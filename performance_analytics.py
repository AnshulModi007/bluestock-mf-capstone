import numpy as np
import pandas as pd
from scipy.stats import linregress

RAW = "data/raw"
PROCESSED = "data/processed"
REPORTS = "reports"

RISK_FREE_RATE = 0.065  # approx. India 10yr G-sec, used as Sharpe/Sortino baseline

# fund_master's free-text benchmark names don't all have an exact match in
# 10_benchmark_indices.csv -- the 3 marked "proxy" fall back to the nearest
# available index rather than an exact match. Flagged in the scorecard notes.
BENCHMARK_MAP = {
    "NIFTY 100 TRI": "NIFTY100",
    "BSE 250 SmallCap TRI": "BSE_SMALLCAP",
    "CRISIL Dynamic Gilt Index": "CRISIL_GILT",
    "NIFTY Midcap 150 TRI": "NIFTY_MIDCAP150",
    "CRISIL Short Term Bond Index": "CRISIL_LIQUID",       # proxy, no exact match
    "NIFTY 500 TRI": "NIFTY500",
    "CRISIL Liquid Fund AI Index": "CRISIL_LIQUID",
    "NIFTY 50 TRI": "NIFTY50",
    "NIFTY Midcap 50 TRI": "NIFTY_MIDCAP150",              # proxy, no exact match
    "NIFTY Large Midcap 250 TRI": "NIFTY500",              # proxy, no exact match
}
PROXY_BENCHMARKS = {"NIFTY Midcap 50 TRI", "CRISIL Short Term Bond Index", "NIFTY Large Midcap 250 TRI"}


def compute_return_and_risk_metrics():
    nav = pd.read_csv(f"{PROCESSED}/clean_nav.csv", parse_dates=["date"])
    rows = []
    for code, g in nav.groupby("amfi_code"):
        g = g.sort_values("date")
        daily_ret = g["nav"].pct_change().dropna()

        years = (g["date"].iloc[-1] - g["date"].iloc[0]).days / 365.25
        cagr = (g["nav"].iloc[-1] / g["nav"].iloc[0]) ** (1 / years) - 1
        cumulative_return = g["nav"].iloc[-1] / g["nav"].iloc[0] - 1

        ann_vol = daily_ret.std() * np.sqrt(252)
        downside = daily_ret[daily_ret < 0]
        downside_dev = downside.std() * np.sqrt(252) if len(downside) > 1 else np.nan

        sharpe = (cagr - RISK_FREE_RATE) / ann_vol if ann_vol else np.nan
        sortino = (cagr - RISK_FREE_RATE) / downside_dev if downside_dev else np.nan

        running_max = g["nav"].cummax()
        drawdown = (g["nav"] - running_max) / running_max
        max_dd = drawdown.min() * 100

        rows.append({
            "amfi_code": code,
            "cagr_pct": cagr * 100,
            "cumulative_return_pct": cumulative_return * 100,
            "ann_volatility_pct": ann_vol * 100,
            "sharpe_computed": sharpe,
            "sortino_computed": sortino,
            "max_drawdown_computed_pct": max_dd,
        })

    metrics = pd.DataFrame(rows)
    metrics.to_csv(f"{REPORTS}/computed_performance_metrics.csv", index=False)
    print(f"Computed return/risk metrics for {len(metrics)} funds")
    print(metrics.head())
    return metrics


def compute_alpha_beta(metrics):
    nav = pd.read_csv(f"{PROCESSED}/clean_nav.csv", parse_dates=["date"])
    funds = pd.read_csv(f"{RAW}/01_fund_master.csv")
    bench = pd.read_csv(f"{RAW}/10_benchmark_indices.csv", parse_dates=["date"])
    bench_pivot = bench.pivot(index="date", columns="index_name", values="close_value")
    bench_ret = bench_pivot.pct_change()

    alpha_list, beta_list = [], []
    for code in metrics["amfi_code"]:
        benchmark_name = funds.loc[funds["amfi_code"] == code, "benchmark"].iloc[0]
        index_name = BENCHMARK_MAP.get(benchmark_name)

        fund_ret = nav[nav["amfi_code"] == code].set_index("date")["nav"].pct_change()
        merged = pd.concat([fund_ret, bench_ret[index_name]], axis=1, join="inner").dropna()
        merged.columns = ["fund", "bench"]

        slope, intercept, *_ = linregress(merged["bench"], merged["fund"])
        beta_list.append(slope)
        alpha_list.append(intercept * 252 * 100)  # annualized alpha, %

    metrics["beta_computed"] = beta_list
    metrics["alpha_computed_pct"] = alpha_list
    metrics.to_csv(f"{REPORTS}/computed_performance_metrics.csv", index=False)
    print("Added alpha/beta. Sample:")
    print(metrics[["amfi_code", "alpha_computed_pct", "beta_computed"]].head())
    return metrics


def compare_with_provided(metrics):
    provided = pd.read_csv(f"{RAW}/07_scheme_performance.csv")
    merged = metrics.merge(
        provided[["amfi_code", "scheme_name", "sharpe_ratio", "sortino_ratio", "alpha", "beta", "max_drawdown_pct"]],
        on="amfi_code",
    )
    merged["sharpe_diff"] = merged["sharpe_computed"] - merged["sharpe_ratio"]
    merged["beta_diff"] = merged["beta_computed"] - merged["beta"]
    merged.to_csv(f"{REPORTS}/performance_comparison.csv", index=False)
    print("Computed vs. provided metrics (sample):")
    print(merged[["scheme_name", "sharpe_computed", "sharpe_ratio", "sharpe_diff",
                   "beta_computed", "beta", "beta_diff"]].head(10))


def build_fund_scorecard():
    perf = pd.read_csv(f"{RAW}/07_scheme_performance.csv")
    perf["rank_sharpe"] = perf["sharpe_ratio"].rank(ascending=False)
    perf["rank_return_3yr"] = perf["return_3yr_pct"].rank(ascending=False)
    perf["rank_drawdown"] = perf["max_drawdown_pct"].rank(ascending=False)  # less negative = better = higher rank
    perf["composite_score"] = perf[["rank_sharpe", "rank_return_3yr", "rank_drawdown"]].mean(axis=1)

    scorecard = perf.sort_values("composite_score")[
        ["amfi_code", "scheme_name", "category", "return_3yr_pct", "sharpe_ratio",
         "max_drawdown_pct", "morningstar_rating", "composite_score"]
    ]
    scorecard.to_csv(f"{REPORTS}/fund_scorecard.csv", index=False)
    print("Top 10 funds by composite score (lower = better):")
    print(scorecard.head(10).to_string(index=False))


def plot_benchmark_comparison():
    import matplotlib.pyplot as plt

    nav = pd.read_csv(f"{PROCESSED}/clean_nav.csv", parse_dates=["date"])
    funds = pd.read_csv(f"{RAW}/01_fund_master.csv")
    bench = pd.read_csv(f"{RAW}/10_benchmark_indices.csv", parse_dates=["date"])

    fund_row = funds[funds["benchmark"] == "NIFTY 50 TRI"].iloc[0]
    code = fund_row["amfi_code"]

    fund_series = nav[nav["amfi_code"] == code].set_index("date")["nav"]
    bench_series = bench[bench["index_name"] == "NIFTY50"].set_index("date")["close_value"]

    common = pd.concat([fund_series, bench_series], axis=1, join="inner")
    common.columns = ["fund", "benchmark"]
    indexed = common / common.iloc[0] * 100  # both series rebased to 100 at start

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(indexed.index, indexed["fund"], label=fund_row["scheme_name"])
    ax.plot(indexed.index, indexed["benchmark"], label="NIFTY50", linestyle="--")
    ax.set_title("Fund vs. Benchmark (rebased to 100)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Indexed Value")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/10_benchmark_comparison.png", dpi=150)
    plt.close(fig)
    print(f"Saved -> reports/10_benchmark_comparison.png (fund: {fund_row['scheme_name']})")


if __name__ == "__main__":
    metrics = compute_return_and_risk_metrics()
    metrics = compute_alpha_beta(metrics)
    compare_with_provided(metrics)
    build_fund_scorecard()
    plot_benchmark_comparison()
