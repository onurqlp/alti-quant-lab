"""Nasdaq public historical end-of-day closing-price fallback.

Not dividend/split adjusted; not proof of redistribution license, NAV, or borrow.
"""
from datetime import datetime,timedelta
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import math,json
from .adapters import FeedError
MAX=1_750_000
def get(symbol,now,fetcher=None):
    if symbol not in ("KO","PEP","IVV","VOO"):
        raise FeedError("SYMBOL_NOT_ALLOWED","A1/A2 curated source symbols")
    url="https://api.nasdaq.com/api/quote/"+symbol+"/historical?"+urlencode({
        "assetclass":"etf" if symbol in ("IVV","VOO") else "stocks",
        "fromdate":(now-timedelta(days=740)).date().isoformat(),
        "todate":now.date().isoformat(),"limit":1500})
    if fetcher is None:
        def fetcher(url):
            req=Request(url,headers={
              "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
              "Accept":"application/json, text/plain, */*",
              "Origin":"https://www.nasdaq.com",
              "Referer":"https://www.nasdaq.com/market-activity/"})
            try:
                with urlopen(req,timeout=12) as response:return response.read(MAX+1)
            except HTTPError as e:
                raise FeedError("PROVIDER_HTTP_ERROR","Nasdaq historical HTTP "+str(e.code)) from e
            except (URLError,OSError,TimeoutError) as e:
                raise FeedError("NETWORK_ERROR","Nasdaq public EOD source unreachable") from e
    body=fetcher(url)
    if not isinstance(body,bytes) or len(body)>MAX:
        raise FeedError("INVALID_DATA","Nasdaq response size invalid")
    try:doc=json.loads(body)
    except (ValueError,UnicodeError) as e:
        raise FeedError("INVALID_DATA","Nasdaq response not JSON") from e
    data=doc.get("data") if isinstance(doc,dict) else None
    table=data.get("tradesTable") if isinstance(data,dict) else None
    rows=table.get("rows") if isinstance(table,dict) else None
    if not isinstance(rows,list) or len(rows)<260:
        raise FeedError("INSUFFICIENT_DATA","Nasdaq EOD response missing matching sessions")
    out={}
    for row in rows:
        if not isinstance(row,dict):continue
        try:
            day=datetime.strptime(row["date"],"%m/%d/%Y").date().isoformat()
            price=float(str(row["close"]).replace("$","").replace(",",""))
        except (ValueError,KeyError,TypeError):continue
        if not math.isfinite(price) or price<=0:continue
        if day in out:raise FeedError("DUPLICATE_DAILY_BAR","Nasdaq repeated EOD session")
        out[day]=price
    if len(out)<260:raise FeedError("INSUFFICIENT_DATA","Nasdaq EOD valid session count too low")
    return out
