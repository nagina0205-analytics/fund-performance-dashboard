"""Create synthetic venture fund cash flows and portfolio company marks.

Writes two files to data/:
  - fund_cashflows.csv     LP-level view: capital calls (negative) and distributions (positive) per fund
  - portfolio_companies.csv company-level cost, current mark, stage, expected exit year and reserves

All companies and numbers are fake.
"""
import csv
import random
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
random.seed(42)

FUNDS = {
    "Fund I": {"vintage": 2016, "size": 200_000_000},
    "Fund II": {"vintage": 2019, "size": 350_000_000},
    "Growth Fund I": {"vintage": 2021, "size": 500_000_000},
}
SECTORS = ["Fintech", "AI Infrastructure", "Bio", "Consumer", "Enterprise SaaS", "Crypto", "Healthcare", "Defense Tech"]
STAGES = ["Seed", "Series A", "Series B", "Series C", "Growth"]
NAMES = ["Arcwell", "Brightloom", "Cobaltix", "Driftwave", "Emberline", "Fernvale", "Glintra", "Halcyra",
         "Ironpeak", "Juniper Labs", "Keystride", "Lumora", "Mosaiq", "Nimbusly", "Orbitra", "Pylonix",
         "Quarrel", "Rivetta", "Solace AI", "Tesserae", "Umbrafy", "Veridian", "Waypoint", "Xylo"]


def main():
    DATA.mkdir(exist_ok=True)
    names = NAMES[:]
    random.shuffle(names)
    flows, companies = [], []

    for fund, info in FUNDS.items():
        size, vintage = info["size"], info["vintage"]
        # Capital calls over the first 5 years, about 90% of fund size in total
        call_pct = [0.20, 0.25, 0.20, 0.15, 0.10]
        for i, pct in enumerate(call_pct):
            year = vintage + i
            if year > 2026:
                break
            flows.append({"fund": fund, "date": date(year, 3, 31).isoformat(), "type": "capital_call",
                          "amount_usd": -round(size * pct, 2)})

        # Distributions start around year 5 for older funds
        for year in range(vintage + 5, 2027):
            multiple = {"Fund I": 0.35, "Fund II": 0.12, "Growth Fund I": 0.04}[fund]
            amt = size * multiple * random.uniform(0.6, 1.4)
            flows.append({"fund": fund, "date": date(year, 9, 30).isoformat(), "type": "distribution",
                          "amount_usd": round(amt, 2)})

        # Portfolio companies with current marks
        invested_total = size * sum(call_pct[: max(0, min(5, 2027 - vintage))]) * 0.9
        n = 8
        weights = [random.uniform(0.5, 1.5) for _ in range(n)]
        for w in weights:
            cost = invested_total * w / sum(weights)
            age = 2026 - vintage
            outcome = random.choices([0.0, 0.6, 1.5, 3.0, 8.0], weights=[15, 25, 30, 20, 10])[0]
            mark = cost * (1 + (outcome - 1) * min(1, age / 6))
            companies.append({
                "fund": fund,
                "company": names.pop(),
                "sector": random.choice(SECTORS),
                "stage": random.choice(STAGES),
                "invested_usd": round(cost, 2),
                "current_value_usd": round(max(mark, 0), 2),
                "expected_exit_year": random.randint(2027, 2032),
                "reserve_usd": round(cost * random.uniform(0.0, 0.6), 2),
            })

    write(DATA / "fund_cashflows.csv", flows)
    write(DATA / "portfolio_companies.csv", companies)
    print(f"Wrote {len(flows)} cash flows and {len(companies)} portfolio companies")


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
