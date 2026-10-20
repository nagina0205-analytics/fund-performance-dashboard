"""Checks the metric math against hand calculated answers.

Run from the project folder:
    python -m unittest discover tests
"""
import sys
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import analysis  # noqa: E402


class XirrTests(unittest.TestCase):
    def test_doubling_in_one_year_is_100_percent(self):
        r = analysis.xirr([(date(2020, 1, 1), -100), (date(2021, 1, 1), 200)])
        self.assertAlmostEqual(r, 1.0, places=2)

    def test_ten_percent(self):
        r = analysis.xirr([(date(2020, 1, 1), -1000), (date(2021, 1, 1), 1100)])
        self.assertAlmostEqual(r, 0.10, places=2)

    def test_no_sign_change_returns_none(self):
        self.assertIsNone(analysis.xirr([(date(2020, 1, 1), -100), (date(2021, 1, 1), -50)]))


class MultipleTests(unittest.TestCase):
    def test_dpi_rvpi_tvpi(self):
        flows = pd.DataFrame({"fund": ["F", "F"],
                              "date": pd.to_datetime(["2020-01-01", "2023-01-01"]),
                              "amount_usd": [-100.0, 50.0]})
        companies = pd.DataFrame({"fund": ["F"], "current_value_usd": [150.0]})
        m = analysis.fund_metrics(flows, companies).iloc[0]
        self.assertEqual(m["dpi"], 0.5)
        self.assertEqual(m["rvpi"], 1.5)
        self.assertEqual(m["tvpi"], 2.0)


if __name__ == "__main__":
    unittest.main()
