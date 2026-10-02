"""03-supplychain-retail — 02_risk_scenarios.py

Concentration risk (SKU + country) with two costed scenarios:
  A) Dual-source the top-20 SKUs (stated extra landed-cost %)
  B) Country diversification push into top-5 non-UK markets with demand share targets

Outputs: outputs/scenarios.json, outputs/charts/*.png
"""
from pathlib import Path
import json
import sys

import pandas as pd
import matplotlib.pyplot as plt

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import mpl_setup, save_png, save_json   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
mpl_setup()

DUAL_COST = 0.06          # % extra landed cost to dual-source top SKUs (stated)
TARGET_EXPORT_SHARE = 0.30   # move 30% of non-UK-driven revenue growth to top-5 export markets

def main() -> None:
    df = pd.read_csv(PROJECT / "data" / "processed" / "transactions.csv")
    orders = pd.read_csv(PROJECT / "data" / "processed" / "orders.csv")
    rev = float(df.revenue.sum())
    sk = df.groupby("stockcode").revenue.sum()
    sk_pos = sk[sk > 0].sort_values(ascending=False)
    top20 = float(sk_pos.head(20).sum())

    ctry = orders.groupby("country").revenue.sum().sort_values(ascending=False)
    non_uk = ctry.drop(index="United Kingdom", errors="ignore")
    non_uk_total = float(non_uk.sum())
    uk_rev = float(ctry.get("United Kingdom", 0))

    scen_a_cost = top20 * DUAL_COST
    scen_b_base = non_uk_total
    scen_b_gain = TARGET_EXPORT_SHARE * non_uk_total * .25   # modest growth factor (stated)

    scen = {
        "assumptions": {"dual_source_extra_landed_cost": DUAL_COST,
                        "export_growth_factor": 0.25,
                        "export_share_target": TARGET_EXPORT_SHARE},
        "annual_revenue": round(rev, 0),
        "top20_revenue": round(top20, 0),
        "scenario_a_dual_sourcing_cost": round(scen_a_cost, 0),
        "uk_revenue": round(uk_rev, 0),
        "uk_revenue_share": round(uk_rev / rev, 3),
        "non_uk_revenue": round(non_uk_total, 0),
        "scenario_b_export_revenue_gain": round(scen_b_gain, 0),
    }
    save_json(scen, PROJECT / "outputs" / "scenarios.json")

    # basket size distribution
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bins = [0, 50, 150, 400, 1000, 3000, 100000]
    labels = ["<$50", "$50-150", "$150-400", "$400-1k", "$1k-3k", ">$3k"]
    bands = pd.cut(orders.revenue, bins, labels=labels).value_counts().reindex(labels)
    ax.bar(bands.index, bands.values, color="#134e5e")
    ax.set_ylabel("Orders"); ax.set_title("Order value bands — fulfillment complexity rises with basket")
    save_png(fig, PROJECT / "outputs" / "charts" / "order_bands.png")
    print(json.dumps(scen, indent=2))


if __name__ == "__main__":
    main()
