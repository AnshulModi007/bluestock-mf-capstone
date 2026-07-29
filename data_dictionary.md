# Bluestock MF Capstone — Data Dictionary

Database: `data/db/bluestock_mf.db` (SQLite, gitignored — rebuild via `python load_dataset.py`)
Schema definition: `sql/schema.sql`

## dim_fund (40 rows) — source: 01_fund_master.csv
| Column | Type | Description |
|---|---|---|
| amfi_code | INTEGER (PK) | AMFI scheme code, opaque numeric ID |
| fund_house | TEXT | AMC name |
| scheme_name | TEXT | Full official scheme name |
| category | TEXT | Equity / Debt |
| sub_category | TEXT | Large Cap / Small Cap / Liquid / Gilt / etc. |
| plan | TEXT | Regular or Direct |
| launch_date | DATE | Fund launch date |
| benchmark | TEXT | Official benchmark index |
| expense_ratio_pct | REAL | Annual expense ratio, % |
| exit_load_pct | REAL | Exit load, % |
| min_sip_amount | INTEGER | Minimum SIP amount, INR |
| min_lumpsum_amount | INTEGER | Minimum lumpsum amount, INR |
| fund_manager | TEXT | Primary fund manager |
| risk_category | TEXT | SEBI riskometer tier (Low/Moderate/Moderately High/High/Very High) |
| sebi_category_code | TEXT | Structured code, e.g. EC01=Large Cap Equity, DC02=Gilt Debt |

## fact_nav (46,000 rows) — source: 02_nav_history.csv, cleaned via data_cleaning.py
| Column | Type | Description |
|---|---|---|
| amfi_code | INTEGER (FK → dim_fund) | Scheme identifier |
| nav_date | DATE | NAV date, forward-filled for weekday holiday gaps (none found) |
| nav | REAL | NAV in INR |
| daily_return_pct | REAL | `pct_change()` of nav within each fund, computed at load time |

## fact_transactions (32,778 rows) — source: 08_investor_transactions.csv, cleaned
| Column | Type | Description |
|---|---|---|
| tx_id | INTEGER (PK, autoincrement) | Synthetic row ID |
| investor_id | TEXT | Investor identifier, INV000001–INV005000 |
| amfi_code | INTEGER (FK → dim_fund) | Fund transacted in |
| transaction_date | DATE | Transaction date |
| transaction_type | TEXT | SIP / Lumpsum / Redemption |
| amount_inr | INTEGER | Transaction amount, INR, validated > 0 |
| state, city, city_tier | TEXT | Investor geography; city_tier is T30/B30 per AMFI classification |
| age_group, gender | TEXT | Demographics |
| annual_income_lakh | REAL | Annual income, INR lakh |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque |
| kyc_status | TEXT | Verified / Pending |

## fact_performance (40 rows) — source: 07_scheme_performance.csv, cleaned
| Column | Type | Description |
|---|---|---|
| amfi_code | INTEGER (PK, FK → dim_fund) | Scheme identifier |
| return_1yr_pct, return_3yr_pct, return_5yr_pct | REAL | Absolute / CAGR returns |
| benchmark_3yr_pct | REAL | Benchmark 3yr CAGR for comparison |
| alpha | REAL | return_3yr − benchmark_3yr. Zero funds are negative in this dataset. |
| beta | REAL | Market sensitivity |
| sharpe_ratio, sortino_ratio | REAL | Risk-adjusted return. No negative Sharpe found. |
| std_dev_ann_pct | REAL | Annualised volatility |
| max_drawdown_pct | REAL | Worst peak-to-trough decline |
| aum_crore | INTEGER | Scheme-level AUM, INR crore |
| expense_ratio_pct | REAL | Duplicated from dim_fund for convenience |
| morningstar_rating | INTEGER | 1–5 stars |
| risk_grade | TEXT | SEBI risk tier |

## fact_aum (90 rows) — source: 03_aum_by_fund_house.csv
| Column | Type | Description |
|---|---|---|
| fund_house | TEXT (PK part) | AMC name |
| as_of_date | DATE (PK part) | Quarter-end date |
| aum_lakh_crore | REAL | AMC-level AUM, INR lakh crore |
| aum_crore | INTEGER | Same value, INR crore (both units kept explicit to avoid confusion) |
| num_schemes | INTEGER | Scheme count for that AMC |

## fact_sip_industry (48 rows) — source: 04_monthly_sip_inflows.csv
| Column | Type | Description |
|---|---|---|
| month | TEXT (PK) | YYYY-MM |
| sip_inflow_crore | INTEGER | Industry-wide SIP inflow, INR crore |
| active_sip_accounts_crore | REAL | Active SIP accounts, crore |
| new_sip_accounts_lakh | REAL | New SIP registrations, lakh |
| sip_aum_lakh_crore | REAL | Total SIP AUM, INR lakh crore |
| yoy_growth_pct | REAL | YoY inflow growth. NULL for 2022 (no prior-year baseline). |

## fact_portfolio (322 rows) — source: 09_portfolio_holdings.csv
| Column | Type | Description |
|---|---|---|
| amfi_code | INTEGER (FK → dim_fund) | Fund holding the stock |
| stock_symbol | TEXT | NSE/BSE ticker |
| stock_name | TEXT | Full stock name |
| sector | TEXT | Sector classification |
| weight_pct | REAL | % of portfolio |
| market_value_cr | REAL | Holding value, INR crore |
| current_price_inr | REAL | Stock price, INR |
| portfolio_date | DATE | As-of date, Dec 2025 |

## Known data-quality notes
- Live NAV fetch (`live_nav_fetch.py`, raw only, not used downstream): none of the 6 tested AMFI codes resolve on mfapi.in to the fund `dim_fund` assigns them — 5 of 6 are a different fund house entirely.
- All three Day 2 cleaning passes (NAV, transactions, performance) found zero anomalies to fix — data was already well-formed.
- `fact_performance.alpha` has zero negative values — every fund beats its benchmark in this dataset.
- **`fact_performance`'s risk/return metrics (sharpe_ratio, sortino_ratio, alpha, beta, max_drawdown_pct) are not mathematically derivable from `fact_nav`.** `performance_analytics.py` independently computes these from raw daily NAV returns and finds no meaningful relationship: correlation between a fund's own NAV returns and its stated benchmark's returns is ~0 for every fund tested (e.g. an ETF explicitly tracking NIFTY 50 shows -0.03 correlation with NIFTY50 over 1,149 trading days, and its rebased value chart visibly diverges from — even moves opposite to — the index; see `reports/10_benchmark_comparison.png`). Separately, all 3 Liquid funds have `sharpe_ratio` numerically identical to `return_3yr_pct` despite very different volatility, indicating the field wasn't computed as a real Sharpe ratio. Conclusion: `fact_performance`'s metrics and `fact_nav`'s daily prices were generated independently (synthetic dataset), not from one consistent underlying price series. Downstream analysis treats `fact_performance` as its own ground truth and does not reconcile it against NAV-derived metrics. Self-computed metrics (CAGR, volatility, computed Sharpe/Sortino/drawdown, all NAV-only — no benchmark dependency) are saved to `reports/computed_performance_metrics.csv`; the side-by-side is in `reports/performance_comparison.csv`.