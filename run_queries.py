import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/db/bluestock_mf.db")
QUERIES_PATH = Path("sql/queries.sql")


def run_queries():
    conn = sqlite3.connect(DB_PATH)
    text = QUERIES_PATH.read_text()
    blocks = [b.strip() for b in text.split(";") if b.strip()]

    for block in blocks:
        lines = block.strip().splitlines()
        comment_lines = [l for l in lines if l.strip().startswith("--")]
        title = comment_lines[0].lstrip("- ").strip() if comment_lines else "Unnamed Query"

        print("=" * 70)
        print(title)
        try:
            df = pd.read_sql(block + ";", conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"ERROR: {e}")
        print()

    conn.close()


if __name__ == "__main__":
    run_queries()