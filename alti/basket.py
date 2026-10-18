"""A3 experimental crypto basket input screen, NOT cointegration or trade.
Uses actual OKX CLOSED 1D spot candles, consistent UTC daily timestamps.
Johansen rank, formation/OOS and borrow remain unavailable.
"""
from __future__ import annotations
import math
from .adapters import OKX,FeedError,okx_data,positive,utc_ms
SYMBOLS=('BTC','ETH','SOL')
def collect(http,now_ms):
    books={}
    for base in SYMBOLS:
        response=okx_data(http.get(OKX,'/api/v5/market/history-candles',{
            'instId':base+'-USDT','bar':'1Dutc','limit':100}))
        bars={}
        for row in response:
            if not isinstance(row,list) or len(row)<9 or str(row[8])!='1':continue
            try:
                when=int(row[0]);close=positive(row[4],'daily close')
            except (ValueError,TypeError,FeedError):continue
            if (when%(86400000)) or when+86400000>now_ms-1000:continue
            if when in bars:raise FeedError('INVALID_DATA','Duplicate daily UTC bar')
            bars[when]=close
        books[base]=bars
    days=sorted(set.intersection(*(set(x.keys()) for x in books.values())))
    if len(days)<50:raise FeedError('INSUFFICIENT_DATA','Need >=50 aligned verified closed UTC daily candles')
    days=days[-80:]
    latest=days[-1]
    if (now_ms-latest)>7*86400000:raise FeedError('STALE_DATA','A3 last daily bar too old')
    # Pure descriptive 20-session returns; no statistical inference or future edge.
    levels={s:books[s][latest] for s in SYMBOLS}
    returns={s:round((books[s][latest]/books[s][days[-21]]-1)*100,4) for s in SYMBOLS}
    if not all(math.isfinite(v) for v in returns.values()):
        raise FeedError('INVALID_DATA','Nonfinite observed returns')
    return {'data_label':'READ_ONLY_LIVE','status':'INPUTS_ONLY',
       'market':'OKX_SPOT','quote':'USDT','symbols':[s+'USDT' for s in SYMBOLS],
       'source_last_closed_day_utc':utc_ms(latest),
       'aligned_closed_days':len(days),'observed_last_close_usdt':levels,
       'observed_return_20d_percent':returns,
       'johansen_rank':None,'cointegrated':None,'formation_oos_validated':False,
       'borrow_verified':False,'fees_verified':False,'trade_ready':False,
       'paper_pnl':None,'real_pnl':None,
       'interpretation':'Real input prices, NO validated basket strategy or arbitrage'}
