"""03-supplychain-retail — 01_analysis.py

Order pipeline + fulfillment-risk analysis.

Outputs: processed orders, kpis.json, segment tables, charts.
"""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_shared_root = Path(__file__).resolve().parent
while _shared_root != _shared_root.parent and not (_shared_root / "shared").is_dir():
    _shared_root = _shared_root.parent
sys.path.insert(0, str(_shared_root))  # callable from repo root or standalone checkout
from shared.utils import mpl_setup, save_png, save_json   # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "outputs"
mpl_setup()


def main() -> None:
    (PROJECT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(PROJECT / "data" / "raw" / "online_retail_II.xlsx",
                       sheet_name="Year 2010-2011")
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df["invoicedate"] = pd.to_datetime(df["invoicedate"])
    df["revenue"] = df["quantity"] * df["price"]
    df["is_return"] = df["quantity"] < 0
    df["month"] = df["invoicedate"].dt.to_period("M").astype(str)

    orders = (df[~df.is_return]
              .groupby("invoice")
              .agg(items=("stockcode", "nunique"), qty=("quantity", "sum"),
                   revenue=("revenue", "sum"), date=("invoicedate", "min"),
                   country=("country", "first"))
              .reset_index())
    orders = orders[orders.revenue > 0]

    df.to_csv(PROJECT / "data" / "processed" / "transactions.csv", index=False)
    orders.to_csv(PROJECT / "data" / "processed" / "orders.csv", index=False)
    orders["month"] = pd.to_datetime(orders["date"]).dt.to_period("M").astype(str)

    sk = df.groupby("stockcode").agg(revenue=("revenue", "sum"))
    sk_pos = sk[sk.revenue > 0].revenue.sort_values(ascending=False)

    bits = {
        "tx": len(df),
        "orders": int(len(orders)),
        "customers": int(df["customer_id"].nunique()),
        "aov": float(orders.revenue.mean()),
        "returns_rev_share": float(abs(df.loc[df.is_return, "revenue"].sum()) / df.revenue.sum()),
        "cancelled_invoice_share": float((df.invoice.astype(str).str.startswith("C")).mean()),
        "sku_count": int(sk_pos.index.nunique()),
        "top20_sku_revenue_share": float(sk_pos.head(20).sum() / sk_pos.sum()),
        "uk_share_revenue": float(df.assign(ch=df.country.str.strip() == "United Kingdom")
                                  .loc[lambda d: d.ch].revenue.sum()
                                  / df.revenue.sum()),
        "multi_country_orders_share": float((orders.groupby("country").revenue.sum().pipe(
            lambda s: 1 - s.max() / s.sum()))),
        "active_months": int(df.month.nunique()),
    }
    bits = {k: round(v, 4) if isinstance(v, float) else v for k, v in bits.items()}
    save_json(bits, OUT / "kpis.json")

    mo = orders.groupby("month").revenue.sum()
    mo_ts = orders.groupby("month").agg(revenue=("revenue", "sum"),
                                        orders=("invoice", "count"))
    mo_ts.to_csv(OUT / "seg_month.csv")
    ctry = orders.groupby("country").agg(orders=("invoice", "count"),
                                         revenue=("revenue", "sum")).sort_values("revenue", ascending=False)
    ctry.to_csv(OUT / "seg_country.csv")
    honeypot = sk_pos.head(20)

    # charts
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(range(len(mo)), mo.values, marker="o", color="#0e7490")
    ax.set_xticks(range(len(mo)), mo.index.astype(str), rotation=45, ha="right")
    ax.set_ylabel("Order revenue"); ax.set_title("Monthly order pipeline — seasonal surges stress fulfillment")
    save_png(fig, OUT / "charts" / "monthly_pipeline.png")

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    cum = (sk_pos.cumsum() / sk_pos.sum()).reset_index(drop=True)
    ax.plot(cum.values, color="#e2584c")
    ax.set_xlabel("SKU rank"); ax.set_ylabel("Cumulative revenue share")
    ax.set_title(f"SKU concentration: top-20 SKUs = {bits['top20_sku_revenue_share']:.0%} of revenue")
    save_png(fig, OUT / "charts" / "sku_concentration.png")

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    c10 = ctry.head(10)
    ax.barh(c10.index[::-1], c10.revenue[::-1], color="#134e5e")
    ax.set_xlabel("Revenue")
    ax.set_title("Revenue by country — concentration & export risk")
    save_png(fig, OUT / "charts" / "revenue_country.png")
    print(json.dumps(bits, indent=2))


if __name__ == "__main__":
    main()
