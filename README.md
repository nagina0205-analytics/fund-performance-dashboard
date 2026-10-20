# Fund Performance and Exit Scenario Dashboard

LPs ask the same questions every quarter. How is the fund doing? When will we get cash back? What happens if exits slip? This project answers those three questions for three synthetic venture funds, and puts the answers on one web page a non-technical reader can use.

**Live dashboard:** https://nagina-arsalan.github.io/fund-performance-dashboard/

All funds, companies and numbers are made up. `src/generate_cashflows.py` creates them.

## What it calculates

| Metric | Meaning |
| --- | --- |
| Paid-in | Capital called from LPs so far |
| DPI | Distributions / paid-in. Cash actually returned. |
| RVPI | Remaining value (NAV) / paid-in. Value still on paper. |
| TVPI | DPI + RVPI. Total value multiple. |
| Net IRR | Annual return on the dated cash flows, with NAV as a final inflow on the valuation date |
| MOIC | Company value / company cost |

On top of that:

- **Exit scenarios.** Bear (60% of current value, exits 2 years late), Base (current value, on schedule) and Bull (1.8x, a year early). For each, the projected TVPI, IRR and cash coming back each year.
- **Follow-on analysis.** Every company ranked by MOIC, with reserves set aside, and a signal: prioritize follow-on, hold reserves, or review before putting more money in.

## How it works

```
data/*.csv  ->  src/analysis.py (Python, pandas)  ->  docs/data.json  ->  docs/index.html (JavaScript, Chart.js)
```

Python does all the math. The page only reads `data.json` and draws it, so updating the numbers means re-running one script.

## Run it yourself

```
pip install -r requirements.txt
python src/generate_cashflows.py
python src/analysis.py
python -m unittest discover tests -v
```

To view the page locally, run `python -m http.server` inside `docs/` and open http://localhost:8000.

## Tests

The IRR function is checked against cases you can do by hand (doubling money in one year is 100%, 1,000 to 1,100 in a year is 10%), and DPI, RVPI and TVPI are checked on a small fund with known answers.

## What I would add with real data

Pull cash flows from the fund administrator instead of a CSV, add a public market equivalent (PME) comparison, and let the user set their own scenario multiples on the page.
