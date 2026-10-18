"""A1/A2 unauthenticated EOD PRICE INPUT exploration only.

Yahoo Finance chart data is an unofficial, non-contractual public endpoint.
No historical bar redistribution, portfolio orders or claims of NAV/borrow access.
This fallback does NOT replace the private licensed Alpaca A1 adapter.
"""
from __future__ import annotations
import datetime as dt
import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from .adapters import FeedError

HOST="https://query1.finance.yahoo.com"
TICKERS={"KO","PEP","IVV","VOO"}
PAIR_BY_MODULE={"A1":("KO","PEP"),"A2":("IVV","VOO")}
MAX_BYTES=1_750_000

def get_chart(symbol,fetcher=None):
    if symbol not in TICKERS:
        raise FeedError("SYMBOL_NOT_ALLOWED","Curated public EOD research symbols only")
    url=HOST+"/v8/finance/chart/"+symbol+"?"+urlencode({
        "range":"2y","interval":"1d","events":"div,splits"})
    if fetcher is None:
        def fetcher(url):
            req=Request(url,headers={
                "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
                "Accept":"application/json"})
            try:
                with urlopen(req,timeout=14) as response:
                    return response.read(MAX_BYTES+1)
            except HTTPError as e:
                raise FeedError("PROVIDER_HTTP_ERROR","Public chart HTTP "+str(e.code)) from e
            except (URLError,OSError,TimeoutError) as e:
                raise FeedError("NETWORK_ERROR","Public chart endpoint unreachable") from e
    data=fetcher(url)
    if not isinstance(data,bytes) or len(data)>MAX_BYTES:
        raise FeedError("INVALID_DATA","Chart source not bytes or too large")
    try:doc=json.loads(data)
    except (UnicodeError,ValueError) as e:raise FeedError("INVALID_DATA","Malformed market JSON") from e
    chart=doc.get("chart") if isinstance(doc,dict) else None
    arr=chart.get("result") if isinstance(chart,dict) else None
    if not isinstance(arr,list) or len(arr)!=1:
        raise FeedError("SOURCE_ERROR","Market source returned no single chart")
    d=arr[0];meta=d.get("meta") or {}
    if meta.get("symbol")!=symbol or meta.get("currency")!="USD" or meta.get("exchangeTimezoneName")!="America/New_York":
        raise FeedError("SOURCE_MISMATCH","Unexpected symbol/currency/exchange zone")
    if meta.get("instrumentType") not in ("EQUITY","ETF"):
        raise FeedError("SOURCE_MISMATCH","Not a confirmed stock / ETF instrument")
    stamps=d.get("timestamp") or []
    adj=(d.get("indicators") or {}).get("adjclose") or []
    quote=(d.get("indicators") or {}).get("quote") or []
    if len(adj)!=1 or len(quote)!=1 or not isinstance(stamps,list):
        raise FeedError("UNADJUSTED_SOURCE","No adjusted close aligned with daily history")
    closes=adj[0].get("adjclose") or []
    raw=quote[0].get("close") or []
    if len(stamps)!=len(closes) or len(raw)!=len(stamps):
        raise FeedError("INVALID_DATA","Daily row lengths mismatch")
    days={}
    for ts,p,r in zip(stamps,closes,raw):
        if not isinstance(ts,int) or not isinstance(p,(int,float)) or not isinstance(r,(int,float)):
            continue
        if not(math.isfinite(p) and math.isfinite(r) and p>0 and r>0):continue
        day=dt.datetime.fromtimestamp(ts,ZoneInfo("America/New_York")).date().isoformat()
        if day in days:raise FeedError("DUPLICATE_DAILY_BAR","Duplicate NY session day")
        days[day]=float(p)
    if len(days)<260:
        raise FeedError("INSUFFICIENT_DATA","Fewer than 260 valid adjusted daily closes")
    return days

def collect(module,now=None,fetcher=None):
    if module not in PAIR_BY_MODULE:
        raise FeedError("NOT_SUPPORTED","Only A1 and A2 observed price-pair inputs")
    now=now or dt.datetime.now(dt.timezone.utc)
    symbols=PAIR_BY_MODULE[module]
    series=[get_chart(symbol,fetcher) for symbol in symbols]
    aligned=sorted(set(series[0]).intersection(series[1]))
    # Ignore NY current calendar day: potentially still in progress or revised.
    latest_day=now.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    aligned=[d for d in aligned if d<latest_day]
    if len(aligned)<260:raise FeedError("INSUFFICIENT_MATCHED_DAYS","Need 260 matching completed daily sessions")
    last=dt.date.fromisoformat(aligned[-1])
    if (now.date()-last).days>7:
        raise FeedError("STALE_DATA","Adjusted EOD sources more than 7 days old")
    # Observations only; never run significance, fit weights, find short borrow or act.
    twenty={symbol:round(100*(s[aligned[-1]]/s[aligned[-21]]-1),4)
            for symbol,s in zip(symbols,series)}
    diff=round(twenty[symbols[0]]-twenty[symbols[1]],4)
    return {"status":"INPUTS_ONLY","data_label":"PUBLIC_EOD_UNLICENSED",
            "source":"YAHOO_CHART_UNOFFICIAL","pair":list(symbols),
            "market":"US_EQUITIES" if module=="A1" else "US_ETF",
            "currency":"USD","adjustment_claim":"VENDOR_ADJCLOSE_UNVERIFIED",
            "last_complete_session":aligned[-1],"aligned_sessions":len(aligned),
            "observed_return_20d_percent":twenty,
            "relative_return_20d_pct_points":diff,
            "raw_licensed_prices_redistributed":False,
            "redistribution_rights_verified":False,
            "trade_ready":False,"borrow_verified":False,"fee_verified":False,
            "etf_nav_verified":False,"cointegration_oos_verified":False,
            "forward_pnl":None,"paper_fills":None,
            "note":"Descriptive vendor-adjusted EOD observation, not issuer NAV or licensed executable quote"}
