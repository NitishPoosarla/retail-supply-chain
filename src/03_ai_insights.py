"""03-supplychain-retail — 03_ai_insights.py — measured AI supply chain readout."""
from pathlib import Path
import json
import sys

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared import llm   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"


def main() -> None:
    kpis = json.loads((OUT / "kpis.json").read_text())
    scen = json.loads((OUT / "scenarios.json").read_text())
    drivers = {
        "SKU concentration": (f"Top-20 SKUs carry {kpis['top20_sku_revenue_share']:.0%} of revenue "
                              f"({scen['top20_revenue']:,.0f}); a single supplier outage on any of them hits hard."),
        "Market concentration": (f"UK = {scen['uk_revenue_share']:.0%} of revenue; currency & policy shocks "
                                 "are a one-market problem today."),
        "Returns & cancellations": (f"Return/cancel revenue share {kpis['returns_rev_share']:.0%}; "
                                    "returns eat capacity the same as forward orders."),
        "Costed hedges": (f"A) dual-sourcing top SKUs costs {scen['scenario_a_dual_sourcing_cost']:,.0f} extra "
                          f"landed cost/period; B) export push could add ~{scen['scenario_b_export_revenue_gain']:,.0f} "
                          "revenue at the stated growth factor."),
    }
    prompt = f"""You are briefing a supply chain director of a UK online retailer. Use ONLY verified metrics.
Deliver: (1) two-sentence risk picture, (2) ranked actions with costs, (3) KPIs to track.
Metrics: {json.dumps({**kpis, **scen}, indent=1)}"""
    md = llm.write_insights(str(OUT / "insights.md"), "Order pipeline & fulfillment risk", kpis, drivers, prompt)
    print(md[:1000])


if __name__ == "__main__":
    main()
