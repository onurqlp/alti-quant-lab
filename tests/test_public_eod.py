"""A1/A2 descriptive public EOD fallback, deterministic strict regression."""
import datetime as dt
import json
import unittest
from alti.eod_public import collect,get_chart
from alti.adapters import FeedError

NOW=dt.datetime(2026,10,18,20,40,tzinfo=dt.timezone.utc)
START=dt.date(2025,1,1)
def fake(url):
    symbol=url.split('/chart/')[1].split('?')[0]
    seq=[]
    day=START
    while day<=dt.date(2026,10,16):
        if day.weekday()<5:seq.append(day)
        day+=dt.timedelta(days=1)
    ts=[int(dt.datetime.combine(x,dt.time(21),dt.timezone.utc).timestamp()) for x in seq]
    multiplier={'KO':.05,'PEP':.04,'IVV':.2,'VOO':.21}[symbol]
    adj=[round(50+i*multiplier,5) for i in range(len(seq))]
    return json.dumps({'chart':{'error':None,'result':[{
        'meta':{'symbol':symbol,'currency':'USD',
                'exchangeTimezoneName':'America/New_York',
                'instrumentType':'ETF' if symbol in ('IVV','VOO') else 'EQUITY'},
        'timestamp':ts,'indicators':{'quote':[{'close':adj}],
                       'adjclose':[{'adjclose':adj}]}
    }]}}).encode()
class PublicEod(unittest.TestCase):
    def test_two_real_symbol_pairs_are_observation_only(self):
        for code,pair in [('A1',['KO','PEP']),('A2',['IVV','VOO'])]:
            out=collect(code,NOW,fake)
            self.assertEqual(out['pair'],pair)
            self.assertGreater(out['aligned_sessions'],260)
            self.assertEqual(out['last_complete_session'],'2026-10-16')
            self.assertEqual(out['data_label'],'PUBLIC_EOD_UNLICENSED')
            self.assertEqual(set(out['observed_return_20d_percent']),set(pair))
            self.assertFalse(out['trade_ready'])
            self.assertFalse(out['raw_licensed_prices_redistributed'])
            self.assertFalse(out['redistribution_rights_verified'])
            self.assertIsNone(out['forward_pnl'])
            self.assertIsNone(out['paper_fills'])
    def test_symbol_not_allowlisted(self):
        with self.assertRaises(FeedError):get_chart('TSLA',fake)
    def test_no_adjclose_is_rejected_not_reinterpreted_as_raw(self):
        def bad(url):
            obj=json.loads(fake(url))
            obj['chart']['result'][0]['indicators'].pop('adjclose')
            return json.dumps(obj).encode()
        with self.assertRaises(FeedError):collect('A1',NOW,bad)
    def test_nasdaq_raw_eod_fallback_is_explicit_and_never_trade_ready(self):
        def rate_limited(url):
            raise FeedError('PROVIDER_HTTP_ERROR','Yahoo HTTP 429')
        def nasdaq(url):
            import datetime,json
            rows=[];day=dt.date(2025,1,1)
            while day<=dt.date(2026,10,16):
                if day.weekday()<5:
                    rows.append({'date':day.strftime('%m/%d/%Y'),'close':'$101.25'})
                day+=dt.timedelta(days=1)
            return json.dumps({'data':{'tradesTable':{'rows':rows}}}).encode()
        for code in ['A1','A2']:
            r=collect(code,NOW,rate_limited,nasdaq)
            self.assertEqual(r['source'],'NASDAQ_PUBLIC_HISTORY')
            self.assertEqual(r['adjustment_claim'],'UNADJUSTED_OR_MIXED')
            self.assertGreaterEqual(r['aligned_sessions'],260)
            self.assertFalse(r['redistribution_rights_verified'])
            self.assertFalse(r['trade_ready'])
    def test_outdated_eod_fails_closed(self):
        with self.assertRaises(FeedError):collect('A2',NOW+dt.timedelta(days=16),fake)
if __name__=='__main__':unittest.main()
