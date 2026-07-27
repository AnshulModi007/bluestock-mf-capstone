import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_nav_history() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    before = len(df)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["amfi_code", "date"])
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="first")

    invalid_nav = (df["nav"] <= 0) | df["nav"].isna()
    if invalid_nav.any():
        print(f"WARNING: dropping {invalid_nav.sum()} rows with NAV <= 0 or missing")
        df = df[~invalid_nav]

    filled_frames = []
    gaps_filled = 0
    for code, group in df.groupby("amfi_code"):
        group = group.set_index("date")
        full_range = pd.bdate_range(group.index.min(), group.index.max())
        reindexed = group.reindex(full_range)
        gaps_filled += reindexed["nav"].isna().sum()
        reindexed["nav"] = reindexed["nav"].ffill()
        reindexed["amfi_code"] = code
        reindexed.index.name = "date"
        filled_frames.append(reindexed.reset_index())

    clean = pd.concat(filled_frames, ignore_index=True)
    clean = clean[["amfi_code", "date", "nav"]].sort_values(["amfi_code", "date"])

    print(f"nav_history: {before} raw rows -> {len(clean)} clean rows "
          f"({gaps_filled} weekday holiday gaps forward-filled)")

    out_path = PROCESSED_DIR / "clean_nav.csv"
    clean.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")
    return clean

def clean_investor_transactions() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    before = len(df)

    print("Raw transaction_type values:", df["transaction_type"].unique())
    print("Raw kyc_status values:", df["kyc_status"].unique())

    df["transaction_date"] = pd.to_datetime(df["transaction_date"])

    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    df["transaction_type"] = df["transaction_type"].replace({"Sip": "SIP"})
    bad_types = ~df["transaction_type"].isin({"SIP", "Lumpsum", "Redemption"})
    if bad_types.any():
        print(f"WARNING: {bad_types.sum()} rows with unexpected transaction_type: "
              f"{df.loc[bad_types, 'transaction_type'].unique()}")

    invalid_amount = df["amount_inr"] <= 0
    if invalid_amount.any():
        print(f"WARNING: dropping {invalid_amount.sum()} rows with amount_inr <= 0")
        df = df[~invalid_amount]

    df["kyc_status"] = df["kyc_status"].str.strip().str.title()
    bad_kyc = ~df["kyc_status"].isin({"Verified", "Pending"})
    if bad_kyc.any():
        print(f"WARNING: {bad_kyc.sum()} rows with unexpected kyc_status: "
              f"{df.loc[bad_kyc, 'kyc_status'].unique()}")

    dupes = df.duplicated()
    if dupes.any():
        print(f"WARNING: dropping {dupes.sum()} exact duplicate rows")
        df = df[~dupes]

    print(f"investor_transactions: {before} raw rows -> {len(df)} clean rows")

    out_path = PROCESSED_DIR / "clean_transactions.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")
    return df

def clean_scheme_performance() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    before = len(df)

    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
        "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
        "max_drawdown_pct", "expense_ratio_pct",
    ]

    for col in numeric_cols:
        coerced = pd.to_numeric(df[col], errors="coerce")
        bad = coerced.isna() & df[col].notna()
        if bad.any():
            print(f"WARNING: {bad.sum()} non-numeric values in {col}")
        df[col] = coerced

    negative_sharpe = df[df["sharpe_ratio"] < 0]
    if len(negative_sharpe):
        print(f"FLAG: {len(negative_sharpe)} funds with negative Sharpe ratio:")
        print(negative_sharpe[["amfi_code", "scheme_name", "sharpe_ratio"]].to_string(index=False))
    else:
        print("OK: no funds with negative Sharpe ratio")

    out_of_range = (df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)
    if out_of_range.any():
        print(f"FLAG: {out_of_range.sum()} funds with expense_ratio_pct outside 0.1%-2.5%:")
        print(df.loc[out_of_range, ["amfi_code", "scheme_name", "expense_ratio_pct"]].to_string(index=False))
    else:
        print("OK: all expense ratios within 0.1%-2.5%")

    print(f"scheme_performance: {before} raw rows -> {len(df)} rows (flags only, nothing dropped)")

    out_path = PROCESSED_DIR / "clean_performance.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")
    return df

if __name__ == "__main__":
    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()