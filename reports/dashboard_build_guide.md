# Power BI Dashboard Build Guide — Day C Task 3

Build in Power BI Desktop. Save the file as `dashboard/bluestock_mf_dashboard.pbix` when done
(already gitignored — .pbix files aren't committed, only the exported PNGs/PDF will be).

## Step 1 — Import data (avoid the SQLite ODBC driver — just import CSVs directly)

`Get Data > Text/CSV`, one at a time, for each of these:

| File | Use |
|---|---|
| `data/raw/01_fund_master.csv` | dim_fund — the hub table |
| `data/processed/clean_nav.csv` | fact_nav |
| `data/processed/clean_transactions.csv` | fact_transactions |
| `data/raw/07_scheme_performance.csv` | fact_performance (canonical metrics) |
| `reports/fund_scorecard.csv` | ranked scorecard for Page 2's table |
| `data/raw/03_aum_by_fund_house.csv` | fact_aum |
| `data/raw/04_monthly_sip_inflows.csv` | fact_sip_industry |
| `data/raw/05_category_inflows.csv` | Page 4 heatmap |
| `data/raw/06_industry_folio_count.csv` | Folio KPI |
| `data/raw/10_benchmark_indices.csv` | benchmark comparison lines |

## Step 2 — Build relationships (Model view)

All on `amfi_code` (1 → many, from `01_fund_master` out to each fact table):
- `01_fund_master[amfi_code]` → `clean_nav[amfi_code]`
- `01_fund_master[amfi_code]` → `clean_transactions[amfi_code]`
- `01_fund_master[amfi_code]` → `07_scheme_performance[amfi_code]`
- `01_fund_master[amfi_code]` → `fund_scorecard[amfi_code]`

`03_aum_by_fund_house`, `04_monthly_sip_inflows`, `05_category_inflows`, `06_industry_folio_count`,
`10_benchmark_indices` stand alone (no fund-level key) — they drive Pages 1 and 4 directly.

## Step 3 — KPI measures (New Measure, paste the DAX)

```dax
Total AUM Tracked (Cr) = CALCULATE(SUM('03_aum_by_fund_house'[aum_crore]), FILTER('03_aum_by_fund_house', '03_aum_by_fund_house'[date] = MAX('03_aum_by_fund_house'[date])))

SIP Inflow Latest (Cr) = CALCULATE(SUM('04_monthly_sip_inflows'[sip_inflow_crore]), FILTER('04_monthly_sip_inflows', '04_monthly_sip_inflows'[month] = MAX('04_monthly_sip_inflows'[month])))

Folios Latest (Cr) = CALCULATE(SUM('06_industry_folio_count'[total_folios_crore]), FILTER('06_industry_folio_count', '06_industry_folio_count'[month] = MAX('06_industry_folio_count'[month])))

Scheme Count = DISTINCTCOUNT('01_fund_master'[amfi_code])
```

## Page 1 — Industry Overview
- 4 Card visuals: `Total AUM Tracked (Cr)`, `SIP Inflow Latest (Cr)`, `Folios Latest (Cr)`, `Scheme Count`.
  Label the AUM card **"AUM — Tracked Fund Houses"**, not "Total Industry AUM" (see note above).
- Line chart: `03_aum_by_fund_house[date]` (X) vs `sum(aum_crore)` (Y), one line per `fund_house` (legend).
- Bar chart: `fund_house` (Y-axis, sorted desc) vs `sum(aum_crore)` — top 10 fund houses.
- Slicers: none required on this page per spec, but add `date` range slicer for interactivity.

## Page 2 — Fund Performance
- Scatter chart: X = `07_scheme_performance[std_dev_ann_pct]`, Y = `return_3yr_pct`, size = `aum_crore`, legend = `category`.
- Table visual: from `fund_scorecard` — columns `scheme_name, category, return_3yr_pct, sharpe_ratio, max_drawdown_pct, morningstar_rating, composite_score`, sorted by `composite_score` ascending.
- Line chart: `clean_nav[date]` (X) vs `nav` (Y) for the fund selected via slicer/table click, plus a second line from `10_benchmark_indices[close_value]` for comparison (use "Edit Interactions" or a bookmark-driven single-fund filter — simplest: add a Fund slicer that filters both visuals).
- Slicers: `fund_house`, `category`, `plan` (all from `01_fund_master`).

## Page 3 — Investor Analytics
- Bar chart (horizontal): `clean_transactions[state]` (Y) vs `sum(amount_inr)` (X).
- Donut chart: `transaction_type` (legend) vs `sum(amount_inr)`.
- Bar chart: `age_group` (X) vs `average(amount_inr)`.
- Line chart: `transaction_date` (X, by month) vs `count(tx_id)` — monthly transaction volume.
- Slicers: `state`, `age_group`, `city_tier`.

## Page 4 — SIP & Market Trends
- Combo chart (dual-axis): `04_monthly_sip_inflows[month]` (X), bar = `sip_inflow_crore`, line = NIFTY50 `close_value` from `10_benchmark_indices` (filtered to `index_name = "NIFTY50"`, one value per month — use month-end).
- Matrix/heatmap: rows = `05_category_inflows[category]`, columns = `month`, values = `net_inflow_crore`, conditional formatting (color scale) on the values.
- Bar chart: top 5 `category` by `sum(net_inflow_crore)` for FY25 (filter `month` to `2024-04`..`2025-03`).
- Card: SIP accounts YoY growth — `active_sip_accounts_crore` latest vs. 12 months prior; simplest as a line chart with a %-change label rather than a single DAX YoY measure.

## Step 4 — Polish + export
- Add at least 2 slicers per page (already covered above).
- Add tooltips (Power BI does this by default per visual — just confirm they show on hover).
- Pick one consistent color theme (View > Themes) — doesn't need to be literal Bluestock branding, just consistent across all 4 pages.
- `File > Export > Export to PDF` → save as `reports/Dashboard.pdf`.
- Screenshot each page individually → save as `reports/dashboard_page1.png` … `dashboard_page4.png`.

Send me a screenshot of each page as you finish it and I'll review before you move to the next one.
