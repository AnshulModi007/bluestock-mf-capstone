import pandas as pd
import matplotlib.pyplot as plt

RAW = "data/raw"
PROCESSED = "data/processed"
REPORTS = "reports"

plt.rcParams["figure.figsize"] = (10, 5)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3


def plot_nav_trends():
    nav = pd.read_csv(f"{PROCESSED}/clean_nav.csv", parse_dates=["date"])
    funds = pd.read_csv(f"{RAW}/01_fund_master.csv")

    # one representative fund per category, up to 5 categories
    picks = funds.groupby("category").first().reset_index()[["amfi_code", "category", "scheme_name"]].head(5)

    fig, ax = plt.subplots()
    for _, row in picks.iterrows():
        series = nav[nav["amfi_code"] == row["amfi_code"]]
        if series.empty:
            continue
        ax.plot(series["date"], series["nav"], label=f"{row['category']}")

    ax.set_title("NAV Trend by Fund Category (2022)")
    ax.set_xlabel("Date")
    ax.set_ylabel("NAV (Rs.)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/01_nav_trend.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/01_nav_trend.png")


def plot_aum_growth():
    aum = pd.read_csv(f"{RAW}/03_aum_by_fund_house.csv", parse_dates=["date"])
    industry = aum.groupby("date")["aum_crore"].sum().reset_index()

    fig, ax = plt.subplots()
    ax.bar(industry["date"].dt.strftime("%Y-%m"), industry["aum_crore"] / 1e5)
    ax.set_title("Total Industry AUM Growth")
    ax.set_xlabel("Quarter")
    ax.set_ylabel("AUM (Lakh Crore Rs.)")
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/02_aum_growth.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/02_aum_growth.png")
    print(industry)


def plot_sip_inflows():
    sip = pd.read_csv(f"{RAW}/04_monthly_sip_inflows.csv")

    fig, ax = plt.subplots()
    ax.plot(sip["month"], sip["sip_inflow_crore"], marker="o")
    ax.set_title("Monthly SIP Inflows")
    ax.set_xlabel("Month")
    ax.set_ylabel("SIP Inflow (Crore Rs.)")
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/03_sip_inflows.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/03_sip_inflows.png")


def plot_folio_growth():
    folio = pd.read_csv(f"{RAW}/06_industry_folio_count.csv")

    fig, ax = plt.subplots()
    ax.plot(folio["month"], folio["total_folios_crore"], marker="o", color="darkgreen")
    ax.set_title("Total Investor Folio Growth")
    ax.set_xlabel("Month")
    ax.set_ylabel("Folios (Crore)")
    ax.tick_params(axis="x", rotation=90)
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/04_folio_growth.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/04_folio_growth.png")

    first, last = folio["total_folios_crore"].iloc[0], folio["total_folios_crore"].iloc[-1]
    pct = (last - first) / first * 100
    print(f"Folio growth over period: {first:.2f}cr -> {last:.2f}cr ({pct:+.1f}%)")

def plot_correlation_heatmap():
    import seaborn as sns
    perf = pd.read_csv(f"{RAW}/07_scheme_performance.csv")
    cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "alpha", "beta",
            "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"]
    corr = perf[cols].corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Correlation: Fund Performance Metrics")
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/05_performance_correlation_heatmap.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/05_performance_correlation_heatmap.png")


def plot_demographics():
    tx = pd.read_csv(f"{RAW}/08_investor_transactions.csv")
    pivot = tx.groupby(["age_group", "gender"])["amount_inr"].sum().unstack()

    fig, ax = plt.subplots()
    pivot.plot(kind="bar", ax=ax)
    ax.set_title("Transaction Amount by Age Group and Gender")
    ax.set_xlabel("Age Group")
    ax.set_ylabel("Total Amount (Rs.)")
    ax.legend(title="Gender")
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/06_demographics.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/06_demographics.png")


def plot_geo_distribution():
    tx = pd.read_csv(f"{RAW}/08_investor_transactions.csv")
    by_state = tx.groupby("state")["amount_inr"].sum().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots()
    ax.barh(by_state.index[::-1], by_state.values[::-1] / 1e7)
    ax.set_title("Top 10 States by Transaction Amount")
    ax.set_xlabel("Total Amount (Crore Rs.)")
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/07_geo_distribution.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/07_geo_distribution.png")


def plot_risk_return_correlation():
    perf = pd.read_csv(f"{RAW}/07_scheme_performance.csv")

    fig, ax = plt.subplots()
    for cat, group in perf.groupby("category"):
        ax.scatter(group["std_dev_ann_pct"], group["return_3yr_pct"], label=cat, alpha=0.7)
    ax.set_title("Risk vs. Return (3yr) by Category")
    ax.set_xlabel("Annualized Std Dev (%)")
    ax.set_ylabel("3yr Return (%)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/08_risk_return_correlation.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/08_risk_return_correlation.png")


def plot_sector_donut():
    holdings = pd.read_csv(f"{RAW}/09_portfolio_holdings.csv")
    by_sector = holdings.groupby("sector")["market_value_cr"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots()
    ax.pie(by_sector, labels=by_sector.index, autopct="%1.1f%%",
           wedgeprops=dict(width=0.4), startangle=90)
    ax.set_title("Portfolio Allocation by Sector")
    fig.tight_layout()
    fig.savefig(f"{REPORTS}/09_sector_donut.png", dpi=150)
    plt.close(fig)
    print("Saved -> reports/09_sector_donut.png")


if __name__ == "__main__":
    plot_nav_trends()
    plot_aum_growth()
    plot_sip_inflows()
    plot_folio_growth()
    plot_correlation_heatmap()
    plot_demographics()
    plot_geo_distribution()
    plot_risk_return_correlation()
    plot_sector_donut()