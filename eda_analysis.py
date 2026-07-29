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


if __name__ == "__main__":
    plot_nav_trends()
    plot_aum_growth()
    plot_sip_inflows()
    plot_folio_growth()
