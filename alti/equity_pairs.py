"""A1 US equity pairs: private, licensed EOD research only.

Source: Alpaca stocks/bars adjustment=all, corporate-action-adjusted daily prices.
No trading, paper fills, borrowing assumptions or publication of raw licensed bars.
"""
from __future__ import annotations
import json, math, os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HOST="https://data.alpaca.markets"
PAIR=("KO","PEP")
MIN_FORMATION=180
VALIDATION=50
OOS=40

class A1Error(Exception):
    def __init__(self, code, detail):
        self.code=code
        super().__init__(detail)

def source_readiness(env=None):
    env=env if env is not None else os.environ
    keys=bool(env.get("ALTI_A1_API_KEY") and env.get("ALTI_A1_API_SECRET"))
    rights=env.get("ALTI_A1_DATA_RIGHTS")=="PERSONAL_RESEARCH_CONFIRMED"
    return {"credentials_configured":keys,"personal_research_rights_confirmed":rights,
            "borrow_verified":False,"transaction_costs_verified":False,
            "redistribution_verified":False,
            "trade_enabled":False}

class AlpacaBars:
    def __init__(self,key,secret):
        self.key,self.secret=key,secret
    def get(self,path,params):
        if path!="/v2/stocks/bars":
            raise A1Error("DENIED_ENDPOINT","Only Alpaca historical market bars are permitted")
        qs=urlencode(params)
        req=Request(HOST+path+"?"+qs,headers={
            "APCA-API-KEY-ID":self.key,"APCA-API-SECRET-KEY":self.secret,
            "Accept":"application/json","User-Agent":"ALTI-A1/1.0 research"})
        try:
            with urlopen(req,timeout=18) as res:
                body=res.read(2000001)
                if len(body)>2000000:raise A1Error("OVERSIZE","Market response exceeded size limit")
                return json.loads(body)
        except HTTPError as exc:
            code="RATE_LIMITED" if exc.code==429 else "ACCESS_DENIED" if exc.code in (401,403,451) else "SOURCE_HTTP_ERROR"
            raise A1Error(code,"Market data provider returned HTTP "+str(exc.code)) from exc
        except (URLError,TimeoutError,OSError) as exc:
            raise A1Error("NETWORK_ERROR","Historical source not reachable") from exc
        except (UnicodeError,ValueError) as exc:
            raise A1Error("BAD_PROVIDER_JSON","Invalid historical market data response") from exc

def collect(http,as_of):
    """Reject partial pages, duplicate days and non-matched calendars; never forward-fill."""
    end=as_of.date()
    begin=(as_of-timedelta(days=740)).date()
    params={"symbols":",".join(PAIR),"timeframe":"1Day","start":begin.isoformat(),
            "end":end.isoformat(),"adjustment":"all","feed":"iex","limit":10000}
    rows={symbol:{} for symbol in PAIR}
    token=None; seen_tokens=set()
    for _ in range(15):
        if token: params["page_token"]=token
        response=http.get("/v2/stocks/bars",params)
        if not isinstance(response,dict) or not isinstance(response.get("bars"),dict):
            raise A1Error("INVALID_SCHEMA","Stock bars response is not a dictionary")
        for symbol in PAIR:
            for item in response["bars"].get(symbol,[]):
                if not isinstance(item,dict) or not isinstance(item.get("t"),str):
                    raise A1Error("INVALID_SCHEMA","Timestamp missing")
                day=item["t"][:10]
                try:
                    datetime.strptime(day,"%Y-%m-%d")
                    close=float(item["c"])
                except (TypeError,ValueError,KeyError) as exc:
                    raise A1Error("INVALID_BAR","Invalid date or adjusted closing price") from exc
                if not (math.isfinite(close) and close>0):
                    raise A1Error("INVALID_BAR","Adjusted close is not positive and finite")
                if day>=end.isoformat():continue  # no in-progress bar
                if day in rows[symbol]:
                    raise A1Error("DUPLICATE_DAY","Duplicate session for "+symbol)
                rows[symbol][day]=close
        token=response.get("next_page_token")
        if not token:break
        if not isinstance(token,str) or token in seen_tokens:
            raise A1Error("BAD_PAGINATION","Repeated or invalid page token")
        seen_tokens.add(token)
    else:
        raise A1Error("BAD_PAGINATION","Historical source page cap reached")
    days=sorted(set(rows[PAIR[0]]) & set(rows[PAIR[1]]))
    if len(days)<MIN_FORMATION+VALIDATION+OOS:
        raise A1Error("INSUFFICIENT_MATCHED_DAYS","Need at least 270 common adjusted daily sessions")
    # Guard incomplete provider coverage. A pair with heavily divergent source bars
    # must not be treated as a reliable matching daily history.
    coverage=min(len(rows[PAIR[0]]),len(rows[PAIR[1]]))/max(len(rows[PAIR[0]]),len(rows[PAIR[1]]))
    if coverage<0.95:
        raise A1Error("UNBALANCED_HISTORY","Historical bars have unequal market coverage")
    return days,[rows[PAIR[0]][day] for day in days],[rows[PAIR[1]][day] for day in days]

def analyze(days,x,y):
    """Formation estimates never use validation/OOS dates; this is retrospective screen only."""
    if not(len(days)==len(x)==len(y)) or len(days)<MIN_FORMATION+VALIDATION+OOS:
        raise A1Error("INSUFFICIENT_MATCHED_DAYS","Not enough aligned formation/OOS observations")
    try:
        import numpy as np
        from statsmodels.tsa.stattools import coint
    except ImportError as exc:
        raise A1Error("DEPENDENCY_MISSING","Statsmodels/numpy required for Engle-Granger test") from exc
    xa=np.log(np.asarray(x,dtype=float)); ya=np.log(np.asarray(y,dtype=float))
    if not (np.isfinite(xa).all() and np.isfinite(ya).all()):
        raise A1Error("INVALID_DATA","Non-finite values in adjusted log prices")
    # Use the most recent independent windows; early history only adds context.
    n=MIN_FORMATION+VALIDATION+OOS
    days=days[-n:]; xa=xa[-n:]; ya=ya[-n:]
    train_x,train_y=xa[:MIN_FORMATION],ya[:MIN_FORMATION]
    if float(np.std(train_x))<0.000001 or float(np.std(train_y))<0.000001:
        raise A1Error("DEGENERATE_PAIR","Formation prices have negligible variance")
    design=np.column_stack((np.ones(MIN_FORMATION),train_x))
    alpha,beta=np.linalg.lstsq(design,train_y,rcond=None)[0]
    residual=ya-(alpha+beta*xa)
    origin=residual[:MIN_FORMATION]
    sigma=float(np.std(origin,ddof=1))
    if not math.isfinite(sigma) or sigma<0.000001:
        raise A1Error("DEGENERATE_SPREAD","Spread standard deviation invalid")
    z=(residual-float(np.mean(origin)))/sigma
    # Engle-Granger is a formation-only test; no p-value selection on the OOS portion.
    _score,p_value,_critical=coint(train_y,train_x,trend="c",autolag="aic")
    if not math.isfinite(float(p_value)):raise A1Error("INVALID_STAT_TEST","Cointegration test invalid")
    return {"pair":list(PAIR),"market":"US_EQUITIES","currency":"USD",
        "feed":"ALPACA_IEX_EOD","adjustment":"ALL_SPLITS_DIVIDENDS_SPINOFF",
        "matched_sessions":len(days),"formation_sessions":MIN_FORMATION,
        "validation_sessions":VALIDATION,"oos_sessions":OOS,
        "formation_end":days[MIN_FORMATION-1],
        "validation_end":days[MIN_FORMATION+VALIDATION-1],"oos_end":days[-1],
        "formation_coint_p":round(float(p_value),6),
        "formation_cointegration_screen_pass":bool(p_value<0.05),
        "last_oos_z":round(float(z[-1]),3),
        "beta_formation_only":round(float(beta),5),
        "lookahead_note":"Retrospective corporate-action adjustments may use information learned after past sessions; no forward performance inferred",
        "verified_net_pnl":None,"paper_fill":None,"trade_ready":False}

def run_a1(now=None,env=None,http=None):
    now=now or datetime.now(timezone.utc)
    env=env if env is not None else os.environ
    flags=source_readiness(env)
    base={"status":"SOURCE_REQUIRED","data_label":"NOT_CONNECTED",
          "reason":"Alpaca EOD market-data API keys and authorized personal research use not configured",
          "source":"ALPACA_ADJUSTED_DAILY","pair":list(PAIR),
          "source_rights":flags,"actionable":False,"paper_pnl":None,"real_pnl":None,
          "derived_statistics":None}
    if not flags["credentials_configured"] or not flags["personal_research_rights_confirmed"]:
        return base
    try:
        data=collect(http or AlpacaBars(env["ALTI_A1_API_KEY"],env["ALTI_A1_API_SECRET"]),now)
        result=analyze(*data)
        base.update(status="RESEARCH_ONLY",data_label="PRIVATE_RESEARCH",
                    reason="Adjusted daily history checked; borrow, quote, costs, live eligibility and forward evidence unverified")
        # Never publish derived proprietary feed analytics without documented rights.
        if env.get("ALTI_A1_PUBLIC_DERIVED_RIGHTS")=="CONFIRMED":
            base["derived_statistics"]=result
        else:
            base["reason"]+="; public derived-data permission not confirmed"
        base["matched_sessions"]=result["matched_sessions"]
        base["last_eod_session"]=result["oos_end"]
        return base
    except A1Error as exc:
        base.update(status="SOURCE_ERROR",reason=exc.code+": "+str(exc))
        return base
    except (ValueError,TypeError,OverflowError,KeyError) as exc:
        base.update(status="SOURCE_ERROR",reason="INVALID_DATA: "+type(exc).__name__)
        return base
