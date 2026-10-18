"""USDC/USDT public two-venue depth observation; never an executable arbitrage signal.
First try Binance SPOT + OKX; if spot blocked, use Kraken + OKX, never
the Binance futures host for a spot endpoint. No credentials, no orders.
"""
from __future__ import annotations
from .adapters import BINANCE_SPOT, KRAKEN, OKX, FeedError, okx_data, positive, utc_ms


def _levels(values):
    if not isinstance(values,list) or not values:
        raise FeedError('INSUFFICIENT_DATA','Book side empty')
    rows=[]
    for row in values[:20]:
        if not isinstance(row,(list,tuple)) or len(row)<2:
            raise FeedError('INVALID_DATA','Malformed book row')
        rows.append([positive(row[0],'book price'),positive(row[1],'book quantity')])
    return rows


def weighted_execution(levels, units):
    remaining=float(units); paid=0.
    for price,qty in levels:
        used=min(remaining,qty);paid+=used*price;remaining-=used
        if remaining<=1e-9:break
    return paid/units if remaining<=1e-9 else None


def _book(bids,asks):
    bid=_levels(bids);ask=_levels(asks)
    if bid[0][0]>=ask[0][0]:
        raise FeedError('INVALID_DATA','Crossed / inverted order book')
    if any(bid[i][0]<bid[i+1][0] for i in range(len(bid)-1)) or any(
      ask[i][0]>ask[i+1][0] for i in range(len(ask)-1)):
        raise FeedError('INVALID_DATA','Unsorted order book')
    return {'bid':bid,'ask':ask}


def kraken_book(http):
    pairs=http.get(KRAKEN,'/0/public/AssetPairs',{'pair':'USDCUSDT'})
    if not isinstance(pairs,dict) or pairs.get('error') or not isinstance(pairs.get('result'),dict):
        raise FeedError('PROVIDER_API_ERROR','Kraken spot instrument metadata missing')
    options=[k for k,v in pairs['result'].items() if isinstance(v,dict) and
             v.get('base')=='USDC' and v.get('quote')=='USDT' and v.get('status') in (None,'online')]
    if len(options)!=1:
        raise FeedError('INSTRUMENT_MISMATCH','Kraken USDC/USDT pair not confirmed')
    raw=http.get(KRAKEN,'/0/public/Depth',{'pair':'USDCUSDT','count':20})
    if not isinstance(raw,dict) or raw.get('error') or not isinstance(raw.get('result'),dict):
        raise FeedError('PROVIDER_API_ERROR','Kraken orderbook missing')
    book=raw['result'].get(options[0])
    if not isinstance(book,dict):
        raise FeedError('INSTRUMENT_MISMATCH','Kraken depth pair differs from metadata')
    return _book(book.get('bids'),book.get('asks'))


def collect(http,now_ms,received_utc):
    units=1000.
    ob=okx_data(http.get(OKX,'/api/v5/market/books',{'instId':'USDC-USDT','sz':20}))
    if len(ob)!=1 or ob[0].get('instId') not in (None,'USDC-USDT'):
        raise FeedError('INSTRUMENT_MISMATCH','OKX USDC-USDT book not uniquely identified')
    okx=ob[0]
    oks=(now_ms-int(okx.get('ts',0)))/1000
    if oks>15 or oks < -60:
        raise FeedError('STALE_DATA','OKX source orderbook timestamp is stale')
    books={'OKX':_book(okx.get('bids'),okx.get('asks'))}
    issues=[]
    try:
        b=http.get(BINANCE_SPOT,'/api/v3/depth',{'symbol':'USDCUSDT','limit':20})
        if not isinstance(b,dict):raise FeedError('INVALID_DATA','Binance depth schema invalid')
        books['BINANCE']=_book(b.get('bids'),b.get('asks'))
    except FeedError as exc:
        issues.append({'venue':'BINANCE','status':exc.code})
        try:books['KRAKEN']=kraken_book(http)
        except FeedError as fallback:
            issues.append({'venue':'KRAKEN','status':fallback.code})
            raise FeedError('SECOND_VENUE_UNAVAILABLE','Binance spot unavailable and Kraken fallback failed') from fallback

    other=next(x for x in books if x!='OKX')
    routes=[]
    for buy,sell in [('OKX',other),(other,'OKX')]:
        b=weighted_execution(books[buy]['ask'],units)
        s=weighted_execution(books[sell]['bid'],units)
        gross=round((s/b-1)*10000,3) if b and s else None
        routes.append({'buy_venue':buy,'sell_venue':sell,'base_units':units,
          'buy_vwap':round(b,6) if b else None,'sell_vwap':round(s,6) if s else None,
          'gross_spread_bps':gross,'net_spread_bps':None,'net_pnl':None,
          'fees_known':False,'status':'SCREEN_ONLY' if gross is not None else 'WEAK_BOOK',
          'reason':'No verified fees, simultaneous executable quotes, custody or transfer route'})
    return {'status':'SCREEN_ONLY_TIMESTAMP_UNVERIFIED','data_label':'READ_ONLY_LIVE',
      'base':'USDC','quote':'USDT','not_usd_cash':True,
      'venues':list(books),'fallback_used':other=='KRAKEN',
      'binance_source_asof_utc':None,'secondary_source_asof_utc':None,
      'binance_received_utc':received_utc,'received_at_utc':received_utc,
      'okx_book_asof_utc':utc_ms(okx['ts']), 'okx_book_age_seconds':round(oks,2),
      'best_quotes':{v:{'bid':x['bid'][0][0],'ask':x['ask'][0][0],
             'bid_qty_base':x['bid'][0][1],'ask_qty_base':x['ask'][0][1]}
             for v,x in books.items()},
      'depth_levels':20,'screen_notional_base_units':units,
      'routes':routes,'provider_warnings':issues,
      'eligible_for_paper_fill':False,'actionable':False,
      'verified_real_pnl':None,'source_urls':[
       'https://www.okx.com/docs-v5/en/',
       'https://docs.kraken.com/api/docs/rest-api/get-order-book/',
       'https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints']}
