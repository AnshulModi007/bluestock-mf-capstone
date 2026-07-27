import sqlite3
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
DB_DIR = Path("data/db")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = Path("sql/schema.sql")


def create_schema():
    if DB_PATH.exists():
        DB_PATH.unlink()  # start fresh so the DB always matches schema.sql exactly

    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.close()
    print(f"Schema created -> {DB_PATH}")


def load_all():
    engine = create_engine(f"sqlite:///{DB_PATH}")

    dim_fund = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    dim_fund.to_sql("dim_fund", engine, if_exists="append", index=False)
    print(f"dim_fund: {len(dim_fund)} rows loaded")

    fact_nav = pd.read_csv(PROCESSED_DIR / "clean_nav.csv")
    fact_nav = fact_nav.rename(columns={"date": "nav_date"})
    fact_nav = fact_nav.sort_values(["amfi_code", "nav_date"])
    fact_nav["daily_return_pct"] = fact_nav.groupby("amfi_code")["nav"].pct_change() * 100
    fact_nav.to_sql("fact_nav", engine, if_exists="append", index=False)
    print(f"fact_nav: {len(fact_nav)} rows loaded")

    fact_tx = pd.read_csv(PROCESSED_DIR / "clean_transactions.csv")
    fact_tx.to_sql("fact_transactions", engine, if_exists="append", index=False)
    print(f"fact_transactions: {len(fact_tx)} rows loaded")

    fact_perf = pd.read_csv(PROCESSED_DIR / "clean_performance.csv")
    perf_cols = [
        "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade",
    ]
    fact_perf = fact_perf[perf_cols]
    fact_perf.to_sql("fact_performance", engine, if_exists="append", index=False)
    print(f"fact_performance: {len(fact_perf)} rows loaded")

    fact_aum = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
    fact_aum = fact_aum.rename(columns={"date": "as_of_date"})
    fact_aum.to_sql("fact_aum", engine, if_exists="append", index=False)
    print(f"fact_aum: {len(fact_aum)} rows loaded")

    fact_sip = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
    fact_sip.to_sql("fact_sip_industry", engine, if_exists="append", index=False)
    print(f"fact_sip_industry: {len(fact_sip)} rows loaded")

    fact_portfolio = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
    fact_portfolio.to_sql("fact_portfolio", engine, if_exists="append", index=False)
    print(f"fact_portfolio: {len(fact_portfolio)} rows loaded")


if __name__ == "__main__":
    create_schema()
    load_all()

    conn = sqlite3.connect(DB_PATH)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("\nTables in database:", [t[0] for t in tables])
    conn.close()
    print("Done. Database ->", DB_PATH)