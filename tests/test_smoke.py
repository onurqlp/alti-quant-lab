"""Four high-impact contract checks; no external endpoints or orders."""
from __future__ import annotations
import unittest
from datetime import datetime, timezone
from alti.adapters import (FeedError, rate, BINANCE, OKX, binance_funding,
                           okx_funding, funding_comparison)
from alti.risk import portfolio, strategies
from alti.stablecoin import weighted_execution

NOW=int(datetime(2026,10,17,0,0,tzinfo=timezone.utc).timestamp()*1000)
HOUR=3600000

class FakeHTTP:
    def get(self, host, path, params=None):
        if host==BINANCE:
            if path.endswith('premiumIndex'):
                return dict(symbol='BTCUSDT',time=NOW-1200,markPrice='90000',indexPrice='89970',
                            lastFundingRate='0.00013',nextFundingTime=NOW+4*HOUR)
            if path.endswith('fundingRate'):
                return [dict(symbol='BTCUSDT',fundingTime=NOW-j*HOUR,fundingRate='0.00010')
                        for j in (20,12,4)]
            if path.endswith('fundingInfo'):return []
            if path.endswith('exchangeInfo'):
                return {'symbols':[dict(symbol='BTCUSDT',contractType='PERPETUAL',quoteAsset='USDT',
                          marginAsset='USDT',status='TRADING',baseAsset='BTC')]}
        if host==OKX:
            if path.endswith('/funding-rate'):
                return {'code':'0','data':[dict(instId='BTC-USDT-SWAP',fundingTime=str(NOW+4*HOUR),
                                         nextFundingTime=str(NOW+12*HOUR),fundingRate='-0.00005')]}
            if path.endswith('/funding-rate-history'):
                return {'code':'0','data':[dict(fundingTime=str(NOW-j*HOUR),fundingRate='-0.00004',realizedRate='-0.00004')
                                         for j in (20,12,4)]}
            if path.endswith('/instruments'):
                return {'code':'0','data':[dict(instId='BTC-USDT-SWAP',ctType='linear',ctVal='0.01',
                                                 ctValCcy='BTC',settleCcy='USDT',state='live')]}
        raise AssertionError(f'unexpected source requested: {host}{path}')

class Contracts(unittest.TestCase):
    def test_exactly_six_and_no_real_trading_or_fabricated_pnl(self):
        self.assertEqual([s['id'] for s in strategies()],['A1','A2','A3','B1','B2','T0'])
        self.assertTrue(all(not s['actionable'] for s in strategies()))
        p=portfolio();self.assertIsNone(p['verified_pnl_try'])
        self.assertEqual(p['protected_reserve_try'],60000)
        self.assertEqual(p['paper_hypothesis_risk_limit_try'],375)
        self.assertEqual(p['paper_gross_exposure_limit_try'],30000)
        self.assertEqual(p['live_trading'],'PERMANENTLY_DISABLED_IN_THIS_BUILD')

    def test_funding_realized_and_indicative_never_mixed(self):
        a=binance_funding(FakeHTTP(),'BTCUSDT',NOW,'2026-10-17T00:00:00Z')
        b=okx_funding(FakeHTTP(),'BTCUSDT',NOW,'2026-10-17T00:00:00Z')
        self.assertEqual(a['last_realized_rate_fraction'],0.0001)
        self.assertEqual(a['indicative_rate_fraction'],0.00013)
        self.assertFalse(a['indicative_is_realized'])
        self.assertEqual(b['interval_hours'],8)
        c=funding_comparison([a,b])
        self.assertEqual(c['status'],'WATCH_ONLY')
        self.assertFalse(c['trade_ready'])
        self.assertIsNone(c['net_expected_pnl'])
        self.assertAlmostEqual(c['run_rate_diff_fraction'],0.00042)

    def test_wrong_funding_units_fail_closed(self):
        with self.assertRaises(FeedError):rate('10')
        with self.assertRaises(FeedError):rate('nan')
        with self.assertRaises(FeedError):rate(None)
        a=binance_funding(FakeHTTP(),'BTCUSDT',NOW,'2026-10-17T00:00:00Z')
        a['metadata']['base']='WRONG_ASSET'
        b=okx_funding(FakeHTTP(),'BTCUSDT',NOW,'2026-10-17T00:00:00Z')
        self.assertEqual(funding_comparison([a,b])['status'],'NOT_COMPARABLE')

    def test_stablecoin_depth_without_fill(self):
        self.assertEqual(weighted_execution([[1.0,300],[1.001,800]],1000),1.0007)
        self.assertIsNone(weighted_execution([[1.0,300]],1000))

if __name__=='__main__':unittest.main()
