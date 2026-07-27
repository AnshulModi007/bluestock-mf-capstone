import time
import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
SCHEME_CODE = 125497  # PDF calls this "HDFC Top 100" — verify against meta below

FIVE_SCHEMES = {
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841,
}


def fetch_nav(scheme_code: int, retries: int = 3) -> pd.DataFrame:
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            payload = response.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  attempt {attempt}/{retries} failed ({e.__class__.__name__}), retrying...")
            time.sleep(2)
    else:
        raise RuntimeError(f"Failed to fetch {scheme_code} after {retries} attempts") from last_error

    meta = payload["meta"]
    print(f"scheme_code={scheme_code} -> {meta['fund_house']} | {meta['scheme_name']}")

    df = pd.DataFrame(payload["data"])
    df["scheme_code"] = scheme_code
    df["scheme_name"] = meta["scheme_name"]
    df["fund_house"] = meta["fund_house"]
    return df


def check_against_fund_master(scheme_code: int, api_scheme_name: str):
    fund_master = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    match = fund_master[fund_master["amfi_code"] == scheme_code]
    if match.empty:
        print(f"WARNING: {scheme_code} not found in fund_master.csv at all")
        return
    local_name = match.iloc[0]["scheme_name"]
    if local_name.strip() != api_scheme_name.strip():
        print(f"WARNING: scheme_code {scheme_code} mismatch")
        print(f"  fund_master.csv says: {local_name}")
        print(f"  live mfapi.in says:   {api_scheme_name}")


def fetch_and_save(code: int, label: str = ""):
    try:
        df = fetch_nav(code)
        check_against_fund_master(code, df["scheme_name"].iloc[0])
        out_path = RAW_DIR / f"live_nav_{code}.csv"
        df.to_csv(out_path, index=False)
        print(f"Saved {len(df)} rows -> {out_path} {label}")
    except RuntimeError as e:
        print(f"SKIPPED {code} {label}: {e}")


if __name__ == "__main__":
    fetch_and_save(SCHEME_CODE, "(HDFC Top 100, per brief)")

    print("\nFetching 5 additional schemes...")
    for name, code in FIVE_SCHEMES.items():
        fetch_and_save(code, f"({name})")