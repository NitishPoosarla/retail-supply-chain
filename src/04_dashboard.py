"""03-supplychain-retail — 04_dashboard.py — single-file supply chain dashboard."""
from pathlib import Path
import json
import sys

import pandas as pd
import plotly.graph_objects as go

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.dashboard import build_dashboard   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"


def main() -> None:
    kpis = json.loads((OUT / "kpis.json").read_text())
    scen = json.loads((OUT / "scenarios.json").read_text())
    mo = pd.read_csv(OUT / "seg_month.csv")
    ctry = pd.read_csv(OUT / "seg_country.csv", index_col=0).head(12)

    fig_mo = go.Figure(go.Bar(x=mo.month, y=mo.revenue, marker_color="#134e5e"))
    fig_mo.update_layout(xaxis_title="Month", yaxis_title="Order revenue")

    fig_ct = go.Figure(go.Bar(y=ctry.index, x=ctry.revenue, orientation="h", marker_color="#0e7490"))
    fig_ct.update_layout(yaxis=dict(title=""))

    # SKU concentration summarized via stored KPI (curve recomputation skipped by design)
    build_dashboard(
        str(PROJECT / "dashboard" / "index.html"),
        title="Order-to-Delivery Intelligence — E-commerce Fulfillment Risk",
        subtitle=("Where is the order pipeline leaking, and which SKUs and markets concentrate risk? "
                  "Built from UCI Online Retail II — 525k transactions, Dec 2009–Dec 2011, public."),
        badges=["Supply chain", "Concentration risk", "Costed hedges", "LLM narration"],
        kpis=[
            {"label": "Orders", "value": f"{kpis['orders']:,}"},
            {"label": "Customers", "value": f"{kpis['customers']:,}"},
            {"label": "Returns (rev share)", "value": f"{kpis['returns_rev_share']:.0%}"},
            {"label": "Top-20 SKU revenue", "value": f"{kpis['top20_sku_revenue_share']:.0%}"},
            {"label": "UK revenue share", "value": f"{scen['uk_revenue_share']:.0%}"},
            {"label": "Dual-source hedge cost", "value": f"${scen['scenario_a_dual_sourcing_cost']:,.0f}"},
        ],
        figures=[
            {"title": "Monthly order pipeline", "sub": "seasonal surges stress fulfillment capacity", "fig": fig_mo},
            {"title": "Revenue by country", "sub": "market concentration & export headroom", "fig": fig_ct},
        ],
        recommendations=[
            "Dual-source the top-20 SKUs — the hedge costs "
            f"${scen['scenario_a_dual_sourcing_cost']:,.0f}/period and removes the largest volume-risk cluster.",
            f"Diversify demand: UK = {scen['uk_revenue_share']:.0%} of revenue; target the top-5 export markets "
            f"for ~${scen['scenario_b_export_revenue_gain']:,.0f} incremental revenue (stated growth factor 25%).",
            f"Attack the returns loop ({kpis['returns_rev_share']:.0%} of revenue re-enters the pipeline) — "
            "returns capacity planning belongs in the same S&OP cadence as forward orders.",
            "Set min-stock alerts on the top-20 SKU list before each seasonal surge month.",
        ],
        footer=("Data: UCI Online Retail II (public, CC-BY). AI narrates verified metrics only. "
                "Scenario assumptions stated in outputs/scenarios.json."),
    )
    print("dashboard written")


if __name__ == "__main__":
    main()
