"""Stage 2: read-only USDC/USDT cross-venue book screening, NEVER execution."""
from __future__ import annotations
from .adapters import BINANCE, OKX, FeedError, okx_data, positive, utc_ms


def _levels(values):
    if not isinstance(values,list) or not values:
        raise FeedError('INSUFFICIENT_DATA','Orderbook side empty')
    r=[]
    for row in values[:20]:
        if len(row)<2: raise FeedError('INVALID_DATA','Unexpected book level')
        p=positive(row[0],'book price'); q=positive(row[1],'book quantity')
        r.append([p,q])
    return r


def weighted_execution(levels, units):
    remaining=units; paid=0.0
    for p,qty in levels:
        used=min(remaining,qty); paid+=p*used; remaining-=used
        if remaining<=1e-9: break
    return (paid/units) if remaining<=1e-9 else None


def collect(http, now_ms, received_utc):
    base='USDC'; quote='USDT'; units=1000.0
    b=http.get(BINANCE,'/api/v3/depth',{'symbol':'USDCUSDT','limit':20})
    ob=okx_data(http.get(OKX,'/api/v5/market/books',{'instId':'USDC-USDT','sz':20}))
    if not isinstance(b,dict) or len(ob)!=1: raise FeedError('INVALID_DATA','Unexpected book format')
    o=ob[0]; b_bid=_levels(b.get('bids')); b_ask=_levels(b.get('asks'))
    o_bid=_levels(o.get('bids')); o_ask=_levels(o.get('asks'))
    if b_bid[0][0]>=b_ask[0][0] or o_bid[0][0]>=o_ask[0][0]:
        raise FeedError('INVALID_DATA','Crossed book / auction state; fail closed')
    book_age=(now_ms-int(o.get('ts',0)))/1000
    if book_age>15 or book_age<-60:
        raise FeedError('STALE_DATA','OKX book source timestamp is stale')
    routes=[]
    for buy,sell,buy_levels,sell_levels in [
        ('BINANCE','OKX',b_ask,o_bid),('OKX','BINANCE',o_ask,b_bid)]:
        buy_vwap=weighted_execution(buy_levels,units)
        sell_vwap=weighted_execution(sell_levels,units)
        gross_bps=round((sell_vwap/buy_vwap-1)*10000,3) if buy_vwap and sell_vwap else None
        routes.append({'buy_venue':buy,'sell_venue':sell,'base_units':units,
            'buy_vwap':round(buy_vwap,6) if buy_vwap else None,
            'sell_vwap':round(sell_vwap,6) if sell_vwap else None,
            'gross_spread_bps':gross_bps,
            'net_spread_bps':None,'net_pnl':None,'fees_known':False,
            'status':'SCREEN_ONLY' if gross_bps is not None else 'WEAK_BOOK',
            'reason':'Fees, custody transfer, token chain, simultaneous executable access and Binance native quote time unverified'})
    return {'status':'SCREEN_ONLY_TIMESTAMP_UNVERIFIED','data_label':'READ_ONLY_LIVE',
        'base':base,'quote':quote,'not_usd_cash':True,'issuer':'Circle USDC (symbol assumed; withdrawal network NOT VERIFIED)',
        'chain_contract':'UNVERIFIED','peg_assumption':'USDT is not USD cash',
        'binance_source_asof_utc':None,'binance_received_utc':received_utc,
        'okx_book_asof_utc':utc_ms(o['ts']), 'okx_book_age_seconds':round(book_age,1),
        'best_quotes':{
            'BINANCE':{'bid':b_bid[0][0],'ask':b_ask[0][0], 'bid_qty_base':b_bid[0][1], 'ask_qty_base':b_ask[0][1]},
            'OKX':{'bid':o_bid[0][0],'ask':o_ask[0][0], 'bid_qty_base':o_bid[0][1], 'ask_qty_base':o_ask[0][1]}},
        'depth_levels':20, 'screen_notional_base_units':units, 'routes':routes,
        'eligible_for_paper_fill':False,'actionable':False, 'verified_real_pnl':None,
        'source_urls':['https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints',
                       'https://www.okx.com/docs-v5/en/']}
