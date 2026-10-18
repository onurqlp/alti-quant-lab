"""Official exchange public data only. No authenticated or order endpoints.

All funding rates use signed fractions PER SETTLEMENT EVENT: 0.0001 = 0.01%.
Realized/history and indicative/current rates are NEVER conflated.
"""
from __future__ import annotations
import json
import math
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BINANCE = "https://fapi.binance.com"
BINANCE_SPOT = "https://api.binance.com"
KRAKEN = "https://api.kraken.com"
OKX = "https://www.okx.com"
DOCS = {
    "BINANCE": "https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History",
    "OKX": "https://www.okx.com/docs-v5/en/",
}

class FeedError(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code, self.detail = code, str(detail)[:260]


def utc_ms(ms):
    ms = int(ms)
    if ms < 946684800000 or ms > 4102444800000:
        raise FeedError("INVALID_DATA", "Timestamp not in supported epoch-ms range")
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat().replace("+00:00", "Z")


def as_ms(iso):
    return int(datetime.fromisoformat(iso.replace('Z', '+00:00')).timestamp() * 1000)


def rate(value):
    try:
        v = float(value)
    except (TypeError, ValueError) as e:
        raise FeedError("INVALID_DATA", "Missing or nonnumeric funding fraction") from e
    # Extreme event funding fractions are not plausible in our initial scope.
    if not math.isfinite(v) or abs(v) > 0.05:
        raise FeedError("INVALID_DATA", "Funding fraction outside 5% per-event guardrail; verify units")
    return v


def positive(value, name):
    try:
        v = float(value)
    except (ValueError, TypeError) as e:
        raise FeedError("INVALID_DATA", f"{name} not numeric") from e
    if not math.isfinite(v) or v <= 0:
        raise FeedError("INVALID_DATA", f"{name} must be finite and positive")
    return v


class PublicHTTP:
    ALLOW = {BINANCE, BINANCE_SPOT, OKX, KRAKEN}
    def get(self, host, path, params=None):
        allowed=((host==BINANCE and path.startswith('/fapi/')) or
                 (host==BINANCE_SPOT and path in ('/api/v3/depth',)) or
                 (host==OKX and path in ('/api/v5/public/funding-rate','/api/v5/public/funding-rate-history','/api/v5/public/instruments','/api/v5/market/books','/api/v5/market/history-candles')) or
                 (host==KRAKEN and path in ('/0/public/Depth','/0/public/AssetPairs')))
        if not allowed:
            raise FeedError("INVALID_ENDPOINT", "Non-public or unauthorized market endpoint")
        url = host + path + ('?' + urlencode(params) if params else '')
        for attempt in range(2):
            try:
                req = Request(url, headers={'User-Agent': 'ALTIQuantLab/1.0 (public-market-research)', 'Accept': 'application/json'})
                with urlopen(req, timeout=11) as r:
                    body = r.read(1_700_000)
                    if len(body) == 1_700_000:
                        raise FeedError('INVALID_DATA', 'Oversized public feed response')
                    return json.loads(body)
            except HTTPError as e:
                status = e.code
                if status == 451: code = 'ACCESS_BLOCKED'
                elif status in (401, 403): code = 'ACCESS_UNVERIFIED'
                elif status == 429: code = 'RATE_LIMITED'
                else: code = 'PROVIDER_HTTP_ERROR'
                if status >= 500 or status == 429:
                    if attempt == 0: time.sleep(0.4); continue
                raise FeedError(code, f'HTTP {status} from {host}{path}') from e
            except (TimeoutError, URLError, OSError) as e:
                if attempt == 0: time.sleep(0.4); continue
                raise FeedError('NETWORK_ERROR', f'{type(e).__name__}: public endpoint unreachable') from e
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise FeedError('INVALID_DATA', 'Public endpoint returned invalid JSON') from e
        raise FeedError('NETWORK_ERROR', 'Retries exhausted')


def okx_data(obj):
    if not isinstance(obj, dict) or obj.get('code') != '0' or not isinstance(obj.get('data'), list):
        raise FeedError('PROVIDER_API_ERROR', f'OKX API status: {str(obj.get("code"))[:40] if isinstance(obj, dict) else "invalid"}')
    return obj['data']


def _hist(rows, time_name, value_names):
    records=[]
    for r in rows:
        t = int(r[time_name]); raw = next((r[k] for k in value_names if r.get(k) not in (None, '')), None)
        records.append({'time_ms':t, 'event_time_utc':utc_ms(t), 'rate_fraction':rate(raw)})
    records.sort(key=lambda x:x['time_ms'])
    # Deduplicate provider repeated entries and disallow conflicting rates for same event.
    seen={}
    for rec in records:
        old=seen.get(rec['time_ms'])
        if old is not None and old['rate_fraction'] != rec['rate_fraction']:
            raise FeedError('INVALID_DATA', 'Conflicting realized funding for same event')
        seen[rec['time_ms']]=rec
    records=list(seen.values())
    if len(records) < 2:
        raise FeedError('INSUFFICIENT_DATA', 'At least two actual settlement events required')
    return records


def infer_interval(records):
    gaps = [(records[i]['time_ms']-records[i-1]['time_ms'])/3_600_000 for i in range(1,len(records))]
    recent = gaps[-3:]
    if not recent or any(x <= 0 or x > 24 for x in recent):
        raise FeedError('INVALID_DATA','Invalid settlement sequence')
    # Last two or three gaps must agree; do not fabricate standard 8h interval.
    if any(abs(x-recent[-1])>0.03 for x in recent):
        raise FeedError('INTERVAL_CHANGED','Funding schedule changed inside recent observed events')
    return round(recent[-1],3)


def _age(ms, now_ms):
    return round((now_ms-ms)/1000, 1)


def _base_record(exchange, symbol, rows, interval, interval_source, nxt, now_ms, received_utc, metadata, indicative=None):
    last=rows[-1]
    if last['time_ms'] > now_ms + 60_000 or nxt <= last['time_ms']:
        raise FeedError('INVALID_DATA','Settlement timestamp sequence invalid')
    if nxt < now_ms-60_000:
        raise FeedError('STALE_DATA','Next funding timestamp already passed')
    if interval <= 0 or interval > 24:
        raise FeedError('INVALID_DATA','Impossible funding interval')
    if nxt-last['time_ms'] > 24*3_600_000 + 60_000:
        raise FeedError('INVALID_DATA','Next event inconsistent with prior settlement')
    # Only history is realized. Last event age is not the quote age.
    return {'venue':exchange,'symbol':symbol,'instrument_class':'USDT_LINEAR_PERPETUAL',
        'data_label':'READ_ONLY_LIVE','rate_unit':'SIGNED_FRACTION_PER_EVENT',
        'last_realized_rate_fraction':last['rate_fraction'],
        'last_realized_time_utc':last['event_time_utc'],
        'last_settlement_age_hours':round(_age(last['time_ms'],now_ms)/3600,2),
        'interval_hours':interval, 'interval_source':interval_source,
        'next_funding_time_utc':utc_ms(nxt), 'indicative_rate_fraction':indicative,
        'indicative_is_realized':False,
        'daily_observed_run_rate_fraction':round(last['rate_fraction'] * 24 / interval,10),
        'historical_events': [{'time_utc':r['event_time_utc'],'rate_fraction':r['rate_fraction']} for r in rows[-12:]],
        'metadata':metadata, 'received_utc':received_utc,
        'source_url':DOCS[exchange], 'source_read_only':True, 'access_to_trading':'UNVERIFIED'}


def binance_funding(http, symbol, now_ms, received_utc):
    # Each endpoint is publicly documented; no API key, POST, private account, or orders.
    market=http.get(BINANCE,'/fapi/v1/premiumIndex',{'symbol':symbol})
    history=http.get(BINANCE,'/fapi/v1/fundingRate',{'symbol':symbol,'limit':15})
    info=http.get(BINANCE,'/fapi/v1/fundingInfo')
    ex=http.get(BINANCE,'/fapi/v1/exchangeInfo')
    if not isinstance(market,dict) or not isinstance(history,list) or not isinstance(info,list) or not isinstance(ex,dict):
        raise FeedError('INVALID_DATA','Unexpected Binance response types')
    sym=next((x for x in ex.get('symbols',[]) if x.get('symbol')==symbol), None)
    if not sym or sym.get('contractType')!='PERPETUAL' or sym.get('quoteAsset')!='USDT' or sym.get('marginAsset')!='USDT' or sym.get('status')!='TRADING':
        raise FeedError('INSTRUMENT_MISMATCH','Binance contract properties not validated')
    meta={'base':sym.get('baseAsset'),'quote':'USDT','margin':'USDT',
          'contract_multiplier':'1 BASE_UNIT_PER_QUANTITY (USD-M linear)',
          'market_asof_utc':utc_ms(market['time']), 'market_quote_age_seconds':_age(int(market['time']),now_ms),
          'mark_price':positive(market.get('markPrice'),'markPrice'),
          'index_price':positive(market.get('indexPrice'),'indexPrice')}
    if meta['market_quote_age_seconds'] < -60 or meta['market_quote_age_seconds'] > 120:
        raise FeedError('STALE_DATA', 'Binance premiumIndex timestamp is stale or in future')
    rows=_hist(history,'fundingTime',['fundingRate'])
    inferred=infer_interval(rows)
    adj=next((i for i in info if i.get('symbol')==symbol),None)
    interval=float(adj['fundingIntervalHours']) if adj else inferred
    if abs(interval-inferred)>0.03:
        raise FeedError('INTERVAL_CHANGED','Binance adjusted and observed intervals disagree; fail closed')
    if market.get('symbol')!=symbol:
        raise FeedError('INSTRUMENT_MISMATCH','Binance symbol mismatched')
    nxt=int(market['nextFundingTime'])
    # Historical settled funding is confirmed; mark lastFundingRate treated as INDICATIVE only.
    return _base_record('BINANCE',symbol,rows,interval,
        'FUNDING_INFO_AND_HISTORY' if adj else 'VERIFIED_SETTLEMENT_HISTORY',
        nxt,now_ms,received_utc,meta,rate(market.get('lastFundingRate')))


def okx_funding(http, symbol, now_ms, received_utc):
    inst=symbol.replace('USDT','-USDT-SWAP')
    curr=okx_data(http.get(OKX,'/api/v5/public/funding-rate',{'instId':inst}))
    history=okx_data(http.get(OKX,'/api/v5/public/funding-rate-history',{'instId':inst,'limit':15}))
    instruments=okx_data(http.get(OKX,'/api/v5/public/instruments',{'instType':'SWAP','instId':inst}))
    if len(curr)!=1 or len(instruments)!=1:
        raise FeedError('INVALID_DATA','Ambiguous OKX market response')
    c=curr[0]; s=instruments[0]
    if c.get('instId')!=inst or s.get('instId')!=inst or s.get('ctType')!='linear' or s.get('settleCcy')!='USDT' or s.get('quoteCcy') not in (None,'','USDT'):
        raise FeedError('INSTRUMENT_MISMATCH','OKX contract properties not validated')
    if s.get('state') not in ('live',):
        raise FeedError('INSTRUMENT_MISMATCH','OKX instrument not live')
    cval=positive(s.get('ctVal'),'ctVal')
    if s.get('ctValCcy') not in (symbol[:-4],):
        raise FeedError('INSTRUMENT_MISMATCH','OKX contract value denominated in unexpected asset')
    rows=_hist(history,'fundingTime',['realizedRate','fundingRate'])
    inferred=infer_interval(rows)
    nxt=int(c.get('fundingTime') or 0)
    # OKX current endpoint fundingTime is upcoming event; nextFundingTime is subsequent event.
    subsequent=int(c.get('nextFundingTime') or 0)
    if subsequent <= nxt:
        raise FeedError('INVALID_DATA','OKX nextFundingTime must exceed fundingTime')
    coming_interval=(subsequent-nxt)/3_600_000
    if abs(coming_interval-inferred)>0.03:
        raise FeedError('INTERVAL_CHANGED','OKX observed and upcoming intervals disagree')
    meta={'base':symbol[:-4], 'quote':'USDT','margin':'USDT',
          'contract_multiplier':cval,'contract_multiplier_unit':s['ctValCcy'],
          'next_after_upcoming_utc':utc_ms(subsequent),
          'exchange_timestamp_available':False,
          'market_quote_age_seconds':None}
    # OKX public current funding estimate has no guaranteed exchange-asof on this endpoint.
    rec=_base_record('OKX',symbol,rows,inferred,'VERIFIED_SETTLEMENT_HISTORY',nxt,now_ms,received_utc,meta,
                     rate(c.get('fundingRate')))
    return rec


def funding_comparison(records):
    if len(records)!=2:
        return {'status':'NOT_COMPARABLE','reason':'Two validated venues required','run_rate_diff_fraction':None}
    a,b=records
    if a['symbol']!=b['symbol'] or a['instrument_class']!=b['instrument_class'] or a['metadata']['base']!=b['metadata']['base']:
        return {'status':'NOT_COMPARABLE','reason':'Underlying/contract mismatch','run_rate_diff_fraction':None}
    # Different settlement times are NOT the same holding period.
    events_are_aligned=abs(as_ms(a['next_funding_time_utc'])-as_ms(b['next_funding_time_utc']))<=60_000
    diff=a['daily_observed_run_rate_fraction']-b['daily_observed_run_rate_fraction']
    return {'status':'WATCH_ONLY', 'same_next_settlement':events_are_aligned,
            'run_rate_diff_fraction':round(diff,10),
            'source':'LAST_REALIZED_EVENT_NORMALIZED_NOT_FORECAST',
            'reason': ('Settlement events not aligned; informational rate comparison only' if not events_are_aligned else
                       'Aligned clock does not validate executable basis hedge, fees, margins, trading access or funding persistence'),
            'net_expected_pnl':None,'trade_ready':False,'future_funding_estimate':None}
