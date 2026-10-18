"""Deterministic source contracts; no invented prices or trading."""
import datetime as dt
import unittest
from alti.adapters import BINANCE_SPOT,OKX,KRAKEN,FeedError
from alti.stablecoin import collect as stable, weighted_execution
from alti.treasury import parse_xml
from alti.basket import collect as basket

NOW=int(dt.datetime(2026,10,18,20,0,tzinfo=dt.timezone.utc).timestamp()*1000)
class KrakenFallback:
    def get(self,host,path,params=None):
        if host==OKX:
            return {'code':'0','data':[{
                'instId':'USDC-USDT','ts':str(NOW-3000),
                'bids':[['0.9991','3000'],['0.9989','1000']],
                'asks':[['1.0001','4000'],['1.0002','900']]
            }]}
        if host==BINANCE_SPOT:raise FeedError('ACCESS_BLOCKED','451')
        if host==KRAKEN and path=='/0/public/AssetPairs':
            return {'error':[],'result':{'USDCUSDT':{
                'base':'USDC','quote':'USDT','status':'online'}}}
        if host==KRAKEN and path=='/0/public/Depth':
            return {'error':[],'result':{'USDCUSDT':{
                'bids':[['1.0002','2000',NOW//1000]],
                'asks':[['1.0004','2000',NOW//1000]]
            }}}
        raise AssertionError((host,path))
class BasketFixture:
    def get(self,host,path,params=None):
        assert host==OKX and path=='/api/v5/market/history-candles'
        begin=NOW-NOW%86400000
        data=[[str(begin-86400000*i),'1','2','1',
               str((30000 if params['instId'].startswith('BTC') else 1000 if params['instId'].startswith('ETH') else 150)*(1-i*.001)),
               '500','500','500','1'] for i in range(1,86)]
        return {'code':'0','data':data}
class Sources(unittest.TestCase):
    def test_kraken_fallback_has_two_real_books_and_no_fake_net(self):
        out=stable(KrakenFallback(),NOW,'2026-10-18T20:00:00Z')
        self.assertTrue(out['fallback_used'])
        self.assertEqual(out['venues'],['OKX','KRAKEN'])
        self.assertEqual(len(out['routes']),2)
        self.assertTrue(all(x['net_pnl'] is None for x in out['routes']))
        self.assertFalse(out['actionable'])
    def test_treasury_official_yields_reference_only(self):
        sample=b'''<?xml version="1.0"?><feed xmlns:m="urn:m"><entry><m:properties>
          <NEW_DATE>2026-10-16T00:00:00Z</NEW_DATE><BC_2YEAR>3.35</BC_2YEAR>
          <BC_10YEAR>4.25</BC_10YEAR><BC_30YEAR>4.58</BC_30YEAR>
        </m:properties></entry></feed>'''
        out=parse_xml(sample,dt.datetime(2026,10,18,20,tzinfo=dt.timezone.utc))
        self.assertAlmostEqual(out['slope_10y_minus_2y_pct_points'],.90)
        self.assertIsNone(out['repo_rate'])
        self.assertFalse(out['trade_ready'])
        with self.assertRaises(FeedError):
            parse_xml(sample,dt.datetime(2026,11,1,tzinfo=dt.timezone.utc))
    def test_basket_inputs_are_real_candles_not_johansen(self):
        out=basket(BasketFixture(),NOW)
        self.assertEqual(out['aligned_closed_days'],80)
        self.assertIsNone(out['johansen_rank'])
        self.assertFalse(out['trade_ready'])
    def test_spot_endpoint_guard(self):
        from alti.adapters import PublicHTTP
        x=PublicHTTP()
        for host,path in [(KRAKEN,'/0/private/Balance'),
                          (BINANCE_SPOT,'/api/v3/order'),
                          (OKX,'/api/v5/trade/order')]:
            with self.assertRaises(FeedError):
                x.get(host,path)
if __name__=='__main__':unittest.main()
