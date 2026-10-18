"""A1: no credentials = no source claims; holdout; fail-closed; no paper fills."""
import math
import unittest
from datetime import datetime, timezone
from alti.equity_pairs import run_a1, collect, analyze, A1Error, PAIR

class FakeProvider:
    def __init__(self,bars):self.bars=bars
    def get(self,path,params):return {"bars":self.bars,"next_page_token":None}

class PairContracts(unittest.TestCase):
    def test_unconfigured_does_not_contact_venue(self):
        class Bomb:
            def get(self,*args):raise AssertionError("Source called despite unavailable rights")
        a=run_a1(env={},http=Bomb())
        self.assertEqual(a["status"],"SOURCE_REQUIRED")
        self.assertFalse(a["actionable"])
        self.assertIsNone(a["paper_pnl"])
        self.assertFalse(a["source_rights"]["borrow_verified"])

    def test_mismatched_sessions_fail_closed(self):
        from datetime import timedelta
        now=datetime(2026,10,18,tzinfo=timezone.utc)
        bars={"KO":[],"PEP":[]}
        for i in range(280):
            date=(now-timedelta(days=281-i)).strftime("%Y-%m-%d")+"T00:00:00Z"
            bars["KO"].append({"t":date,"c":100+i/10})
            if i<100:bars["PEP"].append({"t":date,"c":90+i/10})
        with self.assertRaises(A1Error):collect(FakeProvider(bars),now)

    def test_stat_screen_has_split_windows_and_no_pnl(self):
        # Synthetic TEST FIXTURE only. Never store it in production report/history.
        from datetime import timedelta
        n=270
        days=[(datetime(2024,1,2,tzinfo=timezone.utc)+timedelta(days=i)).date().isoformat() for i in range(n)]
        xx=[math.exp(4+0.0012*i+0.028*math.sin(i/9)) for i in range(n)]
        yy=[math.exp(0.4+0.87*math.log(xx[i])+0.007*math.sin(i/4)) for i in range(n)]
        a=analyze(days,xx,yy)
        self.assertEqual(a["formation_sessions"],180)
        self.assertEqual(a["validation_sessions"],50)
        self.assertEqual(a["oos_sessions"],40)
        self.assertLess(a["formation_end"],a["validation_end"])
        self.assertLess(a["validation_end"],a["oos_end"])
        self.assertFalse(a["trade_ready"])
        self.assertIsNone(a["verified_net_pnl"])
        self.assertIsNone(a["paper_fill"])

    def test_metadata_never_leaks_without_derived_rights(self):
        from datetime import timedelta
        now=datetime(2026,10,18,tzinfo=timezone.utc)
        bars={"KO":[],"PEP":[]}
        for i in range(310):
            t=(now-timedelta(days=311-i)).strftime("%Y-%m-%d")+"T00:00:00Z"
            bars["KO"].append({"t":t,"c":90+0.03*i+1.2*math.sin(i/12)})
            bars["PEP"].append({"t":t,"c":95+0.03*i+1.2*math.sin(i/12)+0.2*math.sin(i/5)})
        env={"ALTI_A1_API_KEY":"dummy","ALTI_A1_API_SECRET":"dummy",
             "ALTI_A1_DATA_RIGHTS":"PERSONAL_RESEARCH_CONFIRMED"}
        a=run_a1(now=now,env=env,http=FakeProvider(bars))
        self.assertEqual(a["status"],"RESEARCH_ONLY")
        self.assertIsNone(a["derived_statistics"])
        self.assertFalse(a["actionable"])

if __name__=="__main__":unittest.main()
