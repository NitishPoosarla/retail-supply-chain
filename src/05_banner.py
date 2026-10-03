"""03 — banner: white, wide concentration bar, 2x2 fact grid."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

k = json.loads((Path(__file__).resolve().parents[1] / "outputs" / "kpis.json").read_text())

fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)
ax.set_xlim(0, 12); ax.set_ylim(0, 6.75); ax.axis("off")
fig.patch.set_facecolor("white")

ax.text(0.5, 6.05, "One supplier outage, 14% gone.", fontsize=23,
        fontweight="bold", color="#23303f")
ax.text(0.5, 5.42, "The top-20 SKUs of a UK online retailer — and what it costs not to bet on them",
        fontsize=11.5, color="#5c6a78")

# label above the bar; segment labels clear of each other
red_w = 11.0 * k["top20_sku_revenue_share"]
ax.add_patch(plt.Rectangle((0.5, 3.45), 11.0, 1.0, color="#e3e7ec"))
ax.add_patch(plt.Rectangle((0.5, 3.45), red_w, 1.0, color="#c2452d"))
ax.text(0.5, 4.85, f"top-20 SKUs carry {k['top20_sku_revenue_share']:.1%} of revenue",
        fontsize=12, fontweight="bold", color="#23303f")
ax.text(0.5 + red_w + 0.35, 3.95, "everything else", fontsize=11, color="#5c6a78", va="center")

facts = [
    ("541,910", "transactions · 13 months\n(UCI Online Retail II, public)", 0.5, 2.65),
    ("84%", "of revenue is ONE market —\nthe United Kingdom", 6.4, 2.65),
    (f"{k['returns_rev_share']:.1%}", "of revenue value comes back\nas returns", 0.5, 1.25),
    ("+6% landed", "cost to dual-source the top-20\n(written assumption)", 6.4, 1.25),
]
for big, small, x, y in facts:
    ax.text(x, y, big, fontsize=19, fontweight="bold", color="#23303f")
    ax.text(x, y - 0.5, small, fontsize=10, color="#5c6a78", va="center", linespacing=1.4)

ax.text(0.5, 0.25,
        "Hedges priced from the data · dual-sourcing vs an export push to the top-5 non-UK markets (~$123k, stated)",
        fontsize=10, color="#23303f")
fig.savefig(Path(__file__).resolve().parents[1] / "outputs" / "banner.png",
            dpi=100, facecolor=fig.get_facecolor())
print("banner written")
