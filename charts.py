"""Step 6: charts.   ./venv/bin/python charts.py -> charts/00_cover.png, 01_monthly.png, 02_stores.png, 03_snap.png, 04_intermittency.png, 05_pareto.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
R = HERE / "results"
INK, DIM, GRID, BG, BLUE, ORANGE, GRAY, GREEN, PURPLE = "#f2f2f0", "#8a8a87", "#1d1d1d", "#0b0b0b", "#3987e5", "#d95926", "#9a9a96", "#3aa876", "#9b7fe8"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG, "text.color": INK,
                     "axes.edgecolor": "#3a3a3a", "axes.labelcolor": DIM, "xtick.color": DIM, "ytick.color": DIM,
                     "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 1,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 11, "axes.titlesize": 13,
                     "axes.titlelocation": "left", "axes.titlepad": 12})
CAT = {"FOODS": BLUE, "HOUSEHOLD": ORANGE, "HOBBIES": GREEN}
STATE = {"CA": BLUE, "TX": ORANGE, "WI": GREEN}


def save(fig, name):
    fig.tight_layout(); fig.savefig(HERE / "charts" / name, dpi=150); plt.close(fig)


def monthly(ax):
    d = pd.read_csv(R / "01a_monthly_revenue.csv"); d = d[d["full_month"]]
    w = d.pivot(index="month", columns="cat_id", values="revenue") / 1e6; x = pd.to_datetime(w.index + "-01")
    ax.stackplot(x, [w[c] for c in ("FOODS", "HOUSEHOLD", "HOBBIES")], colors=[CAT[c] for c in ("FOODS", "HOUSEHOLD", "HOBBIES")], labels=["Foods", "Household", "Hobbies"], alpha=0.95, linewidth=0)
    t = w.sum(axis=1); ax.text(x[0], t.iloc[0] + 0.12, f"${t.iloc[0]:.1f}M", color=INK, fontsize=9, ha="left"); ax.text(x[-1], t.iloc[-1] + 0.12, f"${t.iloc[-1]:.1f}M", color=INK, fontsize=9, ha="right")
    ax.set_ylim(0, 5.2); ax.set_ylabel("revenue a month, $ millions"); ax.grid(axis="x", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper left", ncol=3)
    ax.set_title("Revenue by month and category, 10 stores (complete months)")


def pareto(ax):
    d = pd.read_csv(R / "09a_pareto_curve.csv"); s = pd.read_csv(R / "09b_pareto_summary.csv").set_index("metric")["value"]
    ax.plot([0, 100], [0, 100], color=DIM, linestyle="--", linewidth=1, label="if every item sold the same")
    ax.plot(d["top_pct_of_items"], 100 * d["cumulative_revenue_share"], color=BLUE, linewidth=2.8, label="actual")
    for p, k, dx, dy in ((1, "top_1pct_items_share", 3, -2), (10, "top_10pct_items_share", 3, -2.5), (20, "top_20pct_items_share", 3, -2.5)):
        v = 100 * s[k]; ax.scatter([p], [v], color=ORANGE, s=45, zorder=3); ax.text(p + dx, v + dy, f"top {p}%: {v:.0f}% of revenue", color=INK, fontsize=9)
    ax.set_xlim(0, 100); ax.set_ylim(0, 102); ax.set_xlabel("share of the 3,049 items, best sellers first, %"); ax.set_ylabel("cumulative share of revenue, %")
    ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="lower right"); ax.set_title("Revenue is concentrated, but not 80/20")


def stores(ax):
    d = pd.read_csv(R / "04a_stores.csv").sort_values("revenue"); y = np.arange(len(d))
    ax.barh(y, d["revenue"] / 1e6, color=[STATE[s] for s in d["state_id"]], height=0.72)
    for yi, (r, sh) in enumerate(zip(d["revenue"], d["revenue_share"])):
        ax.text(r / 1e6 + 0.4, yi, f"${r / 1e6:.1f}M  ({100 * sh:.1f}%)", va="center", color=INK, fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels(d["store_id"], fontsize=9.5); ax.set_xlim(0, 40); ax.set_xlabel("revenue, Jan 2011 to May 2016, $ millions"); ax.grid(axis="y", visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=STATE[s], label=l) for s, l in (("CA", "California (4 stores)"), ("TX", "Texas (3)"), ("WI", "Wisconsin (3)"))], frameon=False, labelcolor=INK, fontsize=9, loc="lower right")
    ax.set_title("Revenue by store: one California store is 17% of the total")


def snap(ax):
    d = pd.read_csv(R / "05_snap.csv"); x = np.arange(3); w = 0.26
    for j, (c, lab) in enumerate((("FOODS", "Foods (what SNAP buys)"), ("HOUSEHOLD", "Household"), ("HOBBIES", "Hobbies"))):
        v = [100 * (d[(d["state_id"] == s) & (d["cat_id"] == c)]["matched_ratio"].iloc[0] - 1) for s in ("CA", "TX", "WI")]
        ax.bar(x + (j - 1) * w, v, width=w * 0.92, color=CAT[c], label=lab)
        for xi, vi in zip(x + (j - 1) * w, v):
            ax.text(xi, vi + 0.6, f"+{vi:.1f}%", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(["California", "Texas", "Wisconsin"]); ax.set_ylim(0, 38); ax.set_ylabel("SNAP days vs other days, %")
    ax.grid(axis="x", visible=False); ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper left"); ax.set_title("Sales on SNAP days vs other days (same weekday): foods up, other goods barely move")


def intermittency(ax):
    d = pd.read_csv(R / "08a_intermittency.csv").set_index("cat_id").loc[["ALL", "FOODS", "HOUSEHOLD", "HOBBIES"]]; y = np.arange(4)[::-1]; left = np.zeros(4)
    for col, lab, c in (("share_sold", "sold something", BLUE), ("share_priced_zero", "on sale, sold nothing", ORANGE), ("share_unpriced", "no price yet (not on sale)", GRAY)):
        v = 100 * d[col].to_numpy(); ax.barh(y, v, left=left, color=c, height=0.62, label=lab)
        for yi, vi, li in zip(y, v, left):
            ax.text(li + vi / 2, yi, f"{vi:.0f}%", ha="center", va="center", color=BG if c != BLUE else BG, fontsize=9.5, fontweight="bold")
        left += v
    ax.set_yticks(y); ax.set_yticklabels(["All", "Foods", "Household", "Hobbies"]); ax.set_xlim(0, 100); ax.set_xlabel("share of item x store x day cells, %"); ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, labelcolor=INK, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3); ax.set_title("Most item-days sell nothing, and a fifth are before the item existed")


def main():
    (HERE / "charts").mkdir(exist_ok=True)
    s = pd.read_csv(R / "09b_pareto_summary.csv").set_index("metric")["value"]; q = pd.read_csv(R / "10_data_quality.csv").set_index("metric")["value"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(14, 8), gridspec_kw={"width_ratios": [1.15, 1]})
    monthly(a); pareto(b)
    for ax in (a, b):
        ax.title.set_fontsize(15)
    fig.suptitle(f"10 Walmart stores, 5.3 years: ${q['total_revenue'] / 1e6:.1f}M of sales, {100 * s['top_10pct_items_share']:.0f}% of it from the top 10% of items", x=0.01, ha="left", fontsize=19, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(HERE / "charts" / "00_cover.png", dpi=100); plt.close(fig)
    for fn, f, h in (("01_monthly.png", monthly, 3.8), ("02_stores.png", stores, 4.1), ("03_snap.png", snap, 3.9), ("04_intermittency.png", intermittency, 3.9), ("05_pareto.png", pareto, 4.2)):
        fig, ax = plt.subplots(figsize=(10, h)); f(ax); save(fig, fn)


if __name__ == "__main__":
    main()
