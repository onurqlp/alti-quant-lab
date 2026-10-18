"""One UTC idempotent read-only scan, durable audit + atomic public dashboard snapshot.

Run: python -m alti.worker. No private credentials or trading APIs.
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .adapters import PublicHTTP, FeedError, binance_funding, okx_funding, funding_comparison
from .risk import config, portfolio, strategies
from .stablecoin import collect as stablecoin_collect
from .equity_pairs import run_a1
from .treasury import collect as treasury_collect
from .basket import collect as basket_collect
from .eod_public import collect as public_eod_collect

ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/'site'; DATA=ROOT/'data'

def now_utc():
    return datetime.now(timezone.utc)


def asz(dt):
    return dt.isoformat(timespec='seconds').replace('+00:00','Z')


def read_json(path, fallback):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError,ValueError):return fallback


def atomic_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,path)


def storage_commit(report, events):
    DATA.mkdir(parents=True,exist_ok=True)
    audit=DATA/'audit.jsonl'; dedupe=DATA/'scan_index.json'
    idx=read_json(dedupe,{'scan_ids':[]})
    if report['scan_id'] in idx['scan_ids']:
        print('Existing scan ID; no duplicate append:',report['scan_id'])
        return False
    history=read_json(DATA/'recent_observations.json',[])
    history.extend(events)
    cutoff=now_utc()-timedelta(days=config()['retention_days'])
    history=[x for x in history if datetime.fromisoformat(x['time_utc'].replace('Z','+00:00'))>=cutoff]
    history=history[-2500:]
    report['recent_observations']=history[-100:][::-1]
    report['observation_counts']={label:sum(1 for x in history if x['kind']==label) for label in
                                  ('WATCH_ONLY','REJECTED','SOURCE_ERROR','PAPER_NO_FILL')}
    old=read_json(SITE/'report.json',{})
    if report['live_source_count']==0:
        report['last_successful_scan_utc']=old.get('last_successful_scan_utc')
    else:
        report['last_successful_scan_utc']=report['generated_at_utc']
    atomic_json(DATA/'recent_observations.json',history)
    # Append-only audit; single writer GitHub workflow concurrency ensures no racing writers.
    with audit.open('a',encoding='utf-8') as f:
        for e in events:
            f.write(json.dumps(e,ensure_ascii=False,allow_nan=False)+'\n')
        f.flush();os.fsync(f.fileno())
    atomic_json(SITE/'report.json',report)
    idx['scan_ids']=(idx['scan_ids']+[report['scan_id']])[-1200:]
    atomic_json(dedupe,idx)
    return True


def observation(scan, code, kind, reason, venue=None, symbol=None):
    payload='|'.join([scan,code,kind,venue or '',symbol or '',reason])
    return {'id':hashlib.sha256(payload.encode()).hexdigest()[:20],
            'scan_id':scan,'time_utc':asz(now_utc()),'strategy':code,
            'kind':kind,'venue':venue,'symbol':symbol,'reason':reason,
            'paper_fill':'PAPER_NO_FILL','realized_pnl':None,'mode':'READ_ONLY_LIVE' if kind=='WATCH_ONLY' else 'NOT_VERIFIED'}


def build_report(http=None, ts=None):
    dt=ts or now_utc(); time_ms=int(dt.timestamp()*1000)
    scan='alti-'+dt.strftime('%Y%m%dT%H%MZ') # idempotent per UTC minute
    http=http or PublicHTTP()
    items=strategies(); funding=[]; health=[]; errors=[]; events=[]
    for symbol in config()['symbols']:
        paired=[]
        for venue,fn in [('BINANCE',binance_funding),('OKX',okx_funding)]:
            try:
                record=fn(http,symbol,time_ms,asz(dt)); paired.append(record);funding.append(record)
                health.append({'venue':venue,'symbol':symbol,'status':'READ_ONLY_LIVE',
                               'message':'Historical event and contract metadata validated',
                               'received_utc':asz(dt)})
            except (FeedError,KeyError,TypeError,ValueError,OverflowError) as e:
                code=e.code if isinstance(e,FeedError) else 'INVALID_DATA'
                reason=e.detail if isinstance(e,FeedError) else f'Unexpected {type(e).__name__} in provider response'
                err={'venue':venue,'symbol':symbol,'status':code,'message':reason,'received_utc':asz(dt)}
                health.append(err);errors.append(err)
                events.append(observation(scan,'B1','SOURCE_ERROR',f'{code}: {reason}',venue,symbol))
        if len(paired)==2:
            cmp=funding_comparison(paired)
            events.append(observation(scan,'B1','WATCH_ONLY',cmp['reason'],symbol=symbol))
        else:
            events.append(observation(scan,'B1','REJECTED','CROSS_VENUE_MISSING: Only one or zero validated venues',symbol=symbol))
    # Stage 2 is enabled in a read-only screen. No equivalence, route or fill claims.
    stable=None
    try:
        stable=stablecoin_collect(http,time_ms,asz(dt))
        events.append(observation(scan,'B2','WATCH_ONLY','Two-venue USDC/USDT quote screen only: timestamp, fees and transfer access not verified',symbol='USDCUSDT'))
    except (FeedError,KeyError,TypeError,ValueError,OverflowError) as e:
        code=e.code if isinstance(e,FeedError) else 'INVALID_DATA'
        reason=e.detail if isinstance(e,FeedError) else f'Unexpected {type(e).__name__} in orderbook'
        errors.append({'venue':'BINANCE+OKX','symbol':'USDCUSDT','status':code,'message':reason})
        events.append(observation(scan,'B2','SOURCE_ERROR',f'{code}: {reason}',symbol='USDCUSDT'))
    # A3 read-only daily spot inputs, not a statistically validated strategy.
    basket=None
    try:
        basket=basket_collect(http,time_ms)
        events.append(observation(scan,'A3','WATCH_ONLY','Verified spot basket input candles; rank/OOS and borrow missing'))
    except (FeedError,KeyError,TypeError,ValueError,OverflowError) as e:
        errors.append({'venue':'OKX','symbol':'BTC+ETH+SOL','status':getattr(e,'code','INVALID_DATA'),
                       'message':str(e)[:240]})
        events.append(observation(scan,'A3','SOURCE_ERROR',str(e)[:180]))
    # Official Treasury par yields are T0 context only, not dealer repo prices.
    treasury=None
    try:
        treasury=treasury_collect(dt)
        events.append(observation(scan,'T0','WATCH_ONLY','Official Treasury par yield context, no repo quote'))
    except (FeedError,KeyError,TypeError,ValueError,OverflowError) as e:
        errors.append({'venue':'US_TREASURY','symbol':'YIELD_CURVE','status':getattr(e,'code','INVALID_DATA'),
                       'message':str(e)[:240]})
        events.append(observation(scan,'T0','SOURCE_ERROR',str(e)[:180]))
    cmp_by_symbol={}
    for symbol in config()['symbols']:
        p=[x for x in funding if x['symbol']==symbol]
        cmp_by_symbol[symbol]=funding_comparison(p)
    for item in items:
        if item['id']=='B1':
            item['data_label']='READ_ONLY_LIVE' if funding else 'NOT_CONNECTED'
            item['status']='WATCH_ONLY' if funding else 'SOURCE_ERROR'
            item['reason']='Only realized event observations; trading eligibility/hedging/fees remain unverified' if funding else 'No validated exchange market data received'
        if item['id']=='B2':
            item['data_label']='READ_ONLY_LIVE' if stable else 'NOT_CONNECTED'
            item['status']='SCREEN_ONLY' if stable else 'SOURCE_ERROR'
            item['reason']='Two-way observed orderbook; fees and quote simultaneity unverified' if stable else 'No validated two-venue quote screen'
        if item['id']=='A3':
            item['data_label']='READ_ONLY_LIVE' if basket else 'NOT_CONNECTED'
            item['status']='INPUTS_ONLY' if basket else 'SOURCE_ERROR'
            item['reason']='BTC ETH SOL daily inputs available; Johansen/OOS/borrow unverified' if basket else 'OKX basket inputs missing'
        if item['id']=='T0':
            item['data_label']='REFERENCE_ONLY' if treasury else 'NOT_CONNECTED'
            item['status']='REFERENCE_ONLY' if treasury else 'SOURCE_ERROR'
            item['reason']='Treasury par yield curve available; dealer repo and dirty prices missing' if treasury else 'Treasury reference source unavailable'
    a1=run_a1(now=dt)
    for item in items:
        if item['id']=='A1':
            item['status']=a1['status']
            item['data_label']=a1['data_label']
            item['reason']=a1['reason']
            item['formation_window']=180 if a1['status']=='RESEARCH_ONLY' else None
            item['oos_window']=40 if a1['status']=='RESEARCH_ONLY' else None
    # A1/A2 fallback: unofficial public EOD descriptive inputs only.
    # Licensed Alpaca A1 remains the sole vetted adjusted equities path.
    public_eod={}
    for module in ('A1','A2'):
        try:
            research=public_eod_collect(module,dt)
            public_eod[module]=research
            events.append(observation(scan,module,'WATCH_ONLY',
                'Historical matched US price inputs, rights/borrow/NAV not confirmed'))
        except (FeedError,KeyError,TypeError,ValueError,OverflowError) as e:
            errors.append({'venue':'PUBLIC_EOD_UNOFFICIAL','symbol':module,
                           'status':getattr(e,'code','INVALID_DATA'),'message':str(e)[:240]})
            events.append(observation(scan,module,'SOURCE_ERROR',str(e)[:180]))
    for item in items:
        eod=public_eod.get(item['id'])
        if eod and item['id']=='A1' and item['status']!='RESEARCH_ONLY':
            item['status']='INPUTS_ONLY';item['data_label']='PUBLIC_EOD_UNLICENSED'
            item['reason']='Observed vendor-adjusted KO/PEP EOD; rights/borrow and forward validation absent'
        elif eod and item['id']=='A2':
            item['status']='INPUTS_ONLY';item['data_label']='PUBLIC_EOD_UNLICENSED'
            item['reason']='Observed IVV/VOO adjusted EOD; NAV/benchmark/borrow and feed rights not verified'
    live_count=len(funding)+(1 if stable else 0)+(1 if basket else 0)+(1 if treasury else 0)+len(public_eod)
    report={
        'product':'ALTI QUANT RESEARCH LAB','version':'1.0.0','generated_at_utc':asz(dt),
        'scan_id':scan,'last_successful_scan_utc':None,
        'scan_status':'PARTIAL_LIVE' if live_count and errors else 'READ_ONLY_LIVE' if live_count else 'NO_VALID_LIVE_DATA',
        'mode':'READ_ONLY_LIVE' if live_count else 'UNVERIFIED_NO_LIVE_DATA',
        'live_source_count':live_count,'notional_trade_access_verified':False,
        'live_orders_enabled':False,'verified_real_pnl':None,'paper_pnl':None,'synthetic_data_in_report':False,
        'market_hours':{'crypto':'24/7 (scheduled public API snapshots)','equities':'PUBLIC_EOD_INPUTS_ONLY' if public_eod else 'NOT_CONNECTED','bonds_repo':'REFERENCE_ONLY' if treasury else 'NOT_CONNECTED'},
        'portfolio':portfolio(), 'strategies':items, 'funding_records':funding,
        'funding_comparisons':cmp_by_symbol,'stablecoin':stable,'a3_basket':basket,'t0_treasury':treasury,'a1_research':a1,
        'a1_public_eod':public_eod.get('A1'),'a2_public_eod':public_eod.get('A2'),'provider_health':health,
        'errors':errors, 'recent_observations':[],'observation_counts':{},
        'warnings':['Market data is read-only public research, not an executable price/offer.',
                    'Funding differences are not guaranteed cashflows; basis/hedge/fees/borrow/settlement may dominate.',
                    'NO paper fill without a later executable source quote and explicit legal trading access.',
                    'Coin.Live is independent and untouched.'],
        'source_docs':{'binance':'https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History',
                       'okx':'https://www.okx.com/docs-v5/en/'}
    }
    return report,events


def main():
    report, events=build_report()
    did_write=storage_commit(report,events)
    print(json.dumps({'scan_id':report['scan_id'],'status':report['scan_status'],
                      'live_records':report['live_source_count'],'errors':len(report['errors']),
                      'committed':did_write,'live_orders_enabled':False},ensure_ascii=False))

if __name__=='__main__':main()
