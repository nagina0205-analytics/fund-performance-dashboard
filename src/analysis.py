"""Fund performance and exit scenario analysis.

Reads data/fund_cashflows.csv and data/portfolio_companies.csv, then writes
docs/data.json, which the dashboard (docs/index.html) reads.

Metrics:
  Paid-in capital (PIC) = total capital called
  DPI  = distributions / paid-in           (cash actually returned)
  RVPI = remaining value (NAV) / paid-in   (value still on paper)
  TVPI = DPI + RVPI                        (total value multiple)
  MOIC = company value / company cost      (per company)
  IRR  = discount rate where the net present value of all cash flows,
         with NAV treated as a final inflow on the valuation date, equals zero
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
VALUATION_DATE = date(2026, 9, 30)

# Exit scenarios: multiple applied to current value, and years of delay
SCENARIOS = {
    "Bear": {"value_multiple": 0.6, "delay_years": 2},
    "Base": {"value_multiple": 1.0, "delay_years": 0},
    "Bull": {"value_multiple": 1.8, "delay_years": -1},
}


def xirr(cashflows):
    """IRR for irregular dates using bisection. cashflows = list of (date, amount)."""
    if not cashflows or all(a >= 0 for _, a in cashflows) or all(a <= 0 for _, a in cashflows):
        return None
    t0 = min(d for d, _ in cashflows)

    def npv(rate):
        return sum(a / (1 + rate) ** ((d - t0).days / 365.25) for d, a in cashflows)

    lo, hi = -0.99, 10.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 4)


def fund_metrics(flows, companies):
    rows = []
    for fund, f in flows.groupby("fund"):
        paid_in = -f.loc[f["amount_usd"] < 0, "amount_usd"].sum()
        distributed = f.loc[f["amount_usd"] > 0, "amount_usd"].sum()
        nav = companies.loc[companies["fund"] == fund, "current_value_usd"].sum()
        cf = [(d.date(), a) for d, a in zip(f["date"], f["amount_usd"])] + [(VALUATION_DATE, nav)]
        rows.append({
            "fund": fund,
            "paid_in_usd": round(paid_in, 2),
            "distributed_usd": round(distributed, 2),
            "nav_usd": round(nav, 2),
            "dpi": round(distributed / paid_in, 2),
            "rvpi": round(nav / paid_in, 2),
            "tvpi": round((distributed + nav) / paid_in, 2),
            "irr": xirr(cf),
        })
    return pd.DataFrame(rows)


def exit_scenarios(flows, companies):
    """Project TVPI, IRR and liquidity by year under each scenario."""
    out = []
    for fund, f in flows.groupby("fund"):
        paid_in = -f.loc[f["amount_usd"] < 0, "amount_usd"].sum()
        distributed = f.loc[f["amount_usd"] > 0, "amount_usd"].sum()
        base_cf = [(d.date(), a) for d, a in zip(f["date"], f["amount_usd"])]
        comp = companies[companies["fund"] == fund]
        for name, s in SCENARIOS.items():
            exits = comp.assign(
                exit_year=(comp["expected_exit_year"] + s["delay_years"]).clip(lower=2027),
                proceeds=comp["current_value_usd"] * s["value_multiple"],
            )
            by_year = exits.groupby("exit_year")["proceeds"].sum()
            cf = base_cf + [(date(int(y), 6, 30), p) for y, p in by_year.items()]
            out.append({
                "fund": fund,
                "scenario": name,
                "projected_tvpi": round((distributed + exits["proceeds"].sum()) / paid_in, 2),
                "projected_irr": xirr(cf),
                "liquidity_by_year": {str(int(y)): round(p, 2) for y, p in by_year.items()},
            })
    return out


def follow_on_analysis(companies):
    """Rank companies for follow-on capital by current MOIC, and show reserves at stake."""
    c = companies.copy()
    c["moic"] = (c["current_value_usd"] / c["invested_usd"]).round(2)
    c["signal"] = pd.cut(c["moic"], bins=[-1, 0.8, 1.5, 1000],
                         labels=["Review before follow-on", "Hold reserves", "Prioritize follow-on"])
    c["signal"] = c["signal"].astype(str)
    return c.sort_values("moic", ascending=False)


def main():
    flows = pd.read_csv(DATA / "fund_cashflows.csv", parse_dates=["date"])
    companies = pd.read_csv(DATA / "portfolio_companies.csv")

    metrics = fund_metrics(flows, companies)
    scenarios = exit_scenarios(flows, companies)
    follow_on = follow_on_analysis(companies)

    DOCS.mkdir(exist_ok=True)
    payload = {
        "valuation_date": VALUATION_DATE.isoformat(),
        "funds": metrics.to_dict(orient="records"),
        "scenarios": scenarios,
        "companies": follow_on.to_dict(orient="records"),
    }
    (DOCS / "data.json").write_text(json.dumps(payload, indent=2))

    print(metrics.to_string(index=False))
    print(f"\nWrote {DOCS / 'data.json'}")


if __name__ == "__main__":
    main()
