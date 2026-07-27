import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")


def load_and_inspect():
    csv_files = sorted(RAW_DIR.glob("*.csv"))
    dataframes = {}

    for path in csv_files:
        df = pd.read_csv(path)
        dataframes[path.stem] = df

        print("=" * 70)
        print(f"FILE: {path.name}")
        print(f"Shape: {df.shape}")
        print("\nDtypes:")
        print(df.dtypes)
        print("\nHead:")
        print(df.head())
        print()

    return dataframes

def explore_fund_master(dfs: dict):
    fm = dfs["01_fund_master"]
    print("=" * 70)
    print("FUND MASTER — unique values")
    print("\nFund houses:")
    print(fm["fund_house"].unique())
    print("\nCategories:")
    print(fm["category"].unique())
    print("\nSub-categories:")
    print(fm["sub_category"].unique())
    print("\nRisk categories:")
    print(fm["risk_category"].unique())


def validate_amfi_codes(dfs: dict):
    fm_codes = set(dfs["01_fund_master"]["amfi_code"])
    nav_codes = set(dfs["02_nav_history"]["amfi_code"])

    missing_from_nav = fm_codes - nav_codes
    extra_in_nav = nav_codes - fm_codes

    print("=" * 70)
    print("AMFI CODE VALIDATION")
    print(f"fund_master codes: {len(fm_codes)}, nav_history codes: {len(nav_codes)}")
    if missing_from_nav:
        print(f"WARNING: {len(missing_from_nav)} codes in fund_master missing from nav_history: {missing_from_nav}")
    else:
        print("OK: every fund_master code has NAV history")
    if extra_in_nav:
        print(f"NOTE: {len(extra_in_nav)} codes in nav_history not in fund_master: {extra_in_nav}")

if __name__ == "__main__":
    dfs = load_and_inspect()
    print(f"\nLoaded {len(dfs)} datasets: {list(dfs.keys())}")
    explore_fund_master(dfs)
    validate_amfi_codes(dfs)