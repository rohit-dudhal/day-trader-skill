"""Unit tests for Indian Market (NSE) adaptations."""

import datetime
import unittest

from _load import load

alerts = load("trader-alerts", "alerts")
entry = load("trader-entry", "entry")
scan = load("trader-scanner", "scan")
exit_mod = load("trader-exit", "exit")
risk = load("trader-risk", "check")
news = load("trader-news", "news")

DT = datetime.datetime


class TestIndianMarket(unittest.TestCase):
    def test_nse_hours(self):
        self.assertEqual(alerts.NSE_OPEN, datetime.time(9, 15))
        self.assertEqual(alerts.NSE_CLOSE, datetime.time(15, 30))
        self.assertEqual(entry.NSE_OPEN, datetime.time(9, 15))
        self.assertEqual(entry.NSE_CLOSE, datetime.time(15, 30))
        self.assertEqual(scan.NSE_OPEN, datetime.time(9, 15))
        self.assertEqual(scan.NSE_CLOSE, datetime.time(15, 30))
        self.assertEqual(exit_mod.NSE_OPEN, datetime.time(9, 15))
        self.assertEqual(exit_mod.NSE_CLOSE, datetime.time(15, 30))
        self.assertEqual(risk.NSE_OPEN, datetime.time(9, 15))
        self.assertEqual(risk.NSE_CLOSE, datetime.time(15, 30))

    def test_ist_timezone(self):
        # IST is UTC + 5:30, with no DST
        utc_time = DT(2026, 11, 16, 3, 45)  # 03:45 UTC
        ist_time = alerts.to_ist(utc_time)
        self.assertEqual(ist_time, DT(2026, 11, 16, 9, 15))  # Market open
        self.assertEqual(alerts.ist_to_utc(ist_time), utc_time)

        utc_close = DT(2026, 11, 16, 10, 0)  # 10:00 UTC
        self.assertEqual(alerts.to_ist(utc_close), DT(2026, 11, 16, 15, 30))  # Market close

    def test_nse_holidays_2026_and_2027(self):
        # Republic Day, Independence Day, Gandhi Jayanti
        for hols in (alerts.NSE_HOLIDAYS, entry.NSE_HOLIDAYS, scan.NSE_HOLIDAYS, exit_mod.NSE_HOLIDAYS, risk.NSE_HOLIDAYS):
            self.assertIn("2026-01-26", hols)  # Republic Day
            self.assertIn("2026-08-15", hols)  # Independence Day
            self.assertIn("2026-10-02", hols)  # Gandhi Jayanti
            self.assertIn("2026-11-09", hols)  # Diwali
            self.assertIn("2027-01-26", hols)
            self.assertIn("2027-08-15", hols)
            self.assertIn("2027-10-02", hols)

    def test_symbol_preservation_for_yahoo(self):
        # .NS and .BO must NOT be converted to -NS
        for sym in ("RELIANCE.NS", "TCS.NS", "BAJAJ-AUTO.NS", "M&M.NS"):
            self.assertIn(sym, alerts.yahoo_url(sym))
            self.assertEqual(entry.yahoo_symbol(sym), sym)
            self.assertEqual(scan.to_yahoo(sym), sym)
            self.assertEqual(news.yahoo_symbol(sym), sym)

        # US symbols with dot like BRK.B should still convert to BRK-B
        self.assertIn("BRK-B", alerts.yahoo_url("BRK.B"))
        self.assertEqual(entry.yahoo_symbol("BRK.B"), "BRK-B")
        self.assertEqual(scan.to_yahoo("BRK.B"), "BRK-B")

    def test_risk_ticker_validation(self):
        # All Nifty 50 style tickers must pass regex
        sample = ["RELIANCE.NS", "TCS.NS", "ADANIPORTS.NS", "BAJAJ-AUTO.NS", "M&M.NS", "HDFCBANK.NS"]
        for s in sample:
            self.assertTrue(bool(risk.TICKER.match(s)), "Failed to match ticker %s" % s)

    def test_flat_by_close_315_in_plan(self):
        # In exit planning for Indian stocks, flat_by should default to 15:15
        dummy_plan = {"symbol": "RELIANCE.NS", "stop": 1200.0, "target": 1300.0}
        rules = alerts.rules_from_plan(dummy_plan)
        flat_by_rule = next(r for r in rules if r.get("label") == "flat by close")
        self.assertEqual(flat_by_rule["at"], "15:15")

    def test_nse_market_status(self):
        # Market open at 09:15 IST (03:45 UTC)
        open_utc = DT(2026, 11, 16, 3, 45)  # 09:15 IST on a Monday
        st = alerts.market_status(open_utc, india=True)
        self.assertTrue(st["open"])
        self.assertEqual(st["opens"], "09:15")
        self.assertEqual(st["closes"], "15:30")

        # Before open at 09:14 IST (03:44 UTC)
        pre_utc = DT(2026, 11, 16, 3, 44)
        st_pre = alerts.market_status(pre_utc, india=True)
        self.assertFalse(st_pre["open"])
        self.assertEqual(st_pre["reason"], "before the open")

        # After close at 15:30 IST (10:00 UTC)
        post_utc = DT(2026, 11, 16, 10, 0)
        st_post = alerts.market_status(post_utc, india=True)
        self.assertFalse(st_post["open"])
        self.assertEqual(st_post["reason"], "after the close")


if __name__ == "__main__":
    unittest.main()
