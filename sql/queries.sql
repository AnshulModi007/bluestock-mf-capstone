-- 1. Top 5 funds by AUM
SELECT df.scheme_name, df.fund_house, fp.aum_crore
FROM fact_performance fp
JOIN dim_fund df ON df.amfi_code = fp.amfi_code
ORDER BY fp.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per fund per month
SELECT amfi_code, strftime('%Y-%m', nav_date) AS month, ROUND(AVG(nav), 2) AS avg_nav
FROM fact_nav
GROUP BY amfi_code, month
ORDER BY amfi_code, month
LIMIT 20;

-- 3. SIP inflow YoY growth
SELECT month, sip_inflow_crore, yoy_growth_pct
FROM fact_sip_industry
ORDER BY month;

-- 4. Transactions by state
SELECT state, COUNT(*) AS num_transactions, SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with expense_ratio < 1%
SELECT scheme_name, fund_house, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct;

-- 6. Top 10 funds by 3-year return
SELECT df.scheme_name, fp.return_3yr_pct, fp.sharpe_ratio
FROM fact_performance fp
JOIN dim_fund df ON df.amfi_code = fp.amfi_code
ORDER BY fp.return_3yr_pct DESC
LIMIT 10;

-- 7. Total AUM by fund category
SELECT df.category, SUM(fp.aum_crore) AS total_aum_crore, COUNT(*) AS num_funds
FROM fact_performance fp
JOIN dim_fund df ON df.amfi_code = fp.amfi_code
GROUP BY df.category
ORDER BY total_aum_crore DESC;

-- 8. Transaction type split by age group
SELECT age_group, transaction_type, COUNT(*) AS num_transactions
FROM fact_transactions
GROUP BY age_group, transaction_type
ORDER BY age_group, transaction_type;

-- 9. Funds underperforming their benchmark (negative alpha)
SELECT df.scheme_name, fp.alpha, fp.return_3yr_pct, fp.benchmark_3yr_pct
FROM fact_performance fp
JOIN dim_fund df ON df.amfi_code = fp.amfi_code
WHERE fp.alpha < 0
ORDER BY fp.alpha;

-- 10. Average sector weight across all equity portfolios
SELECT sector, ROUND(AVG(weight_pct), 2) AS avg_weight_pct, COUNT(DISTINCT amfi_code) AS num_funds
FROM fact_portfolio
GROUP BY sector
ORDER BY avg_weight_pct DESC;