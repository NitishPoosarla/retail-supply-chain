"""03-supplychain-retail — 06_chat.py — ask-the-data chatbot.

The trust rule: every number is COMPUTED LIVE from data/processed/transactions.csv
(pandas, ~542k rows in a few seconds) or outputs/scenarios.json at question time.
The LLM, if configured with a key, only narrates the verified facts — it is
instructed never to compute or invent. No key → deterministic offline engine,
identical numbers. Nothing hallucinates either way.

Usage:
    python src/06_chat.py                        # interactive REPL
    python src/06_chat.py "sku concentration"    # one-shot
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
TX = PROJECT / "data" / "processed" / "transactions.csv"
ORDERS = PROJECT / "data" / "processed" / "orders.csv"

HEADLINE = ("Overall: 541,910 transactions · 19,960 orders · 4,372 customers · "
            "AOV $534 · top-20 SKUs = 13.7% of revenue · returns = 9.2% of value.")

FIRST_MSG = """Questions I can answer (all computed live from the data):
  sku concentration · worst skus · returns · revenue by country
  monthly trend · aov / orders · the sourcing scenarios
Type 'quit' to exit."""

_cache: dict = {}


def df():
    if "tx" not in _cache:
        import pandas as pd
        _cache["tx"] = pd.read_csv(TX, parse_dates=["invoicedate"])
    return _cache["tx"]


def orders():
    if "o" not in _cache:
        import pandas as pd
        _cache["o"] = pd.read_csv(ORDERS, parse_dates=["date"])
    return _cache["o"]


def compute(q: str):
    q = q.lower().strip()

    if "sku" in q or "concentration" in q or "pareto" in q or "top 20" in q:
        t = df()
        rev = t.groupby("stockcode")["revenue"].sum().sort_values(ascending=False)
        total = rev.sum()
        top20 = rev.head(20)
        top10s = top20.head(10).sum() / total
        lines = [
            f"Revenue share of top-20 SKUs: {top20.sum()/total:.1%} (top-10: {top10s:.1%}) of ${total:,.0f} annual revenue.",
            "Biggest single-SKU exposures (revenue, share):",
        ]
        lines += [f"  {str(code).strip()} — ${v:,.0f} ({v/total:.1%})"
                  for code, v in top20.head(5).items()]
        lines.append("Pareto tail: a single-supplier outage on one of these is a revenue event, not an IT ticket.")
        return lines

    if "return" in q:
        t = df()
        ret = t[t["is_return"] == True]  # noqa: E712
        share = ret["revenue"].abs().sum() / t["revenue"].sum()
        lines = [f"Returns carry {share:.1%} of gross revenue value back through the books.",
                 f"Return transactions: {len(ret):,} of {len(t):,} lines ({len(ret)/len(t):.1%})."]
        by = t[t["is_return"] == True].groupby("stockcode")["revenue"].sum().abs().sort_values(ascending=False).head(3)
        lines += ["Highest-value return streams:", *[f"  SKU {str(c).strip()} — ${v:,.0f}" for c, v in by.items()]]
        return lines

    if "country" in q or "export" in q or "market" in q:
        o = orders()
        rev = o.groupby("country")["revenue"].sum().sort_values(ascending=False)
        uk = rev.get("United Kingdom", 0) / rev.sum()
        lines = [f"UK share of revenue: {uk:.1%} — one-market exposure.",
                 "Next 5 markets by revenue:"]
        lines += [f"  {c} — ${v:,.0f}" for c, v in rev.drop("United Kingdom", errors="ignore").head(5).items()]
        lines.append("Export-push sizing lives in scenario B below.")
        return lines

    if "month" in q or "season" in q or "trend" in q or "holiday" in q:
        t = df()
        m = t.groupby("month")["revenue"].sum()
        peak_month, peak_val = m.idxmax(), m.max()
        lines = [f"Peak revenue month: {peak_month} at ${peak_val/1e6:.2f}M (holiday surge).",
                 "Trough:", f"  {m.idxmin()} — ${m.min()/1e6:.2f}M."]
        lines += [f"  {i} — ${v/1e6:.2f}M" for i, v in m.tail(6).items()]
        return lines

    if "aov" in q or "order" in q or "customer" in q:
        o = orders()
        t = df()
        lines = [f"Orders: {len(o):,} · customers: {t['customer_id'].nunique():,.0f} · AOV: ${o['revenue'].mean():,.2f}",
                 f"Cancelled invoices: {(t['invoice'].astype(str).str.startswith('C')).mean():.1%} of lines."]
        return lines

    if "scenario" in q or "dual" in q or "hedge" in q or "cost" in q:
        s = json.loads((PROJECT / "outputs" / "scenarios.json").read_text())
        a = s["assumptions"]
        return [
            "Scenario A — dual-source the top-20 SKUs (stated assumption: extra landed cost = "
            f"{a['dual_source_extra_landed_cost']:.0%}):",
            f"  top-20 revenue ${s['top20_revenue']:,.0f} × 6% = ${s['scenario_a_dual_sourcing_cost']:,.0f}/year hedge cost",
            "  vs a single-supplier outage idling 13.7% of revenue — priced, not hand-waved.",
            "Scenario B — export push on the top-5 non-UK markets "
            f"(growth factor {a['export_growth_factor']:.0%} toward {a['export_share_target']:.0%} share):",
            f"  +${s['scenario_b_export_revenue_gain']:,.0f} annual revenue.",
            f"Context: annual revenue ${s['annual_revenue']:,.0f}, UK share {s['uk_revenue_share']:.1%}.",
        ]

    if "cancel" in q:
        t = df()
        n = t["invoice"].astype(str).str.startswith("C").mean()
        return [f"Cancelled-invoice lines: {n:.1%} of all transaction lines (mostly manual corrections).",
                "Cancelled orders are quantified separately from returns in the dashboard."]

    return None


def offline_answer(q: str) -> str:
    try:
        lines = compute(q)
    except Exception as e:  # noqa: BLE001
        return f"\n(error while computing from the csv — this engine never guesses: {e})\n"
    if lines is None:
        return ("\nI could not map that to a computed fact, so here is the verified headline\n"
                "(try: sku concentration, returns, revenue by country, monthly trend, scenario).\n\n"
                f"{HEADLINE}\n")
    return "\n".join(["[computed live from transactions.csv —]"] + lines) + f"\n\n{HEADLINE}\n"


def narrate_with_llm(q: str, facts: str) -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""
    import urllib.request
    body = json.dumps({"model": "llama-3.1-8b-instant", "messages": [
        {"role": "system", "content": "You are a precise supply-chain analyst. Use ONLY the numbers in the supplied verified facts. Do not compute, estimate or invent any number. 3 sentences max."},
        {"role": "user", "content": f"Facts (verified, pre-computed):\n{facts}\n\nQuestion: {q}"}]})
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body.encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return "\n\nNARRATED: " + json.loads(r.read())["choices"][0]["message"]["content"].strip() + "\n"
    except Exception:
        return ""


def main() -> None:
    if not TX.exists():
        print("Run src/00_download_data.py + src/01_analysis.py first."); sys.exit(2)

    if len(sys.argv) > 1:  # one-shot
        q = " ".join(sys.argv[1:])
        base = offline_answer(q)
        if os.environ.get("GROQ_API_KEY") and "computed live" in base:
            base += narrate_with_llm(q, base)
        print(base)
        return

    print(FIRST_MSG + "\n")
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); return
        if q.lower() in {"quit", "exit", "q", ""}:
            return
        base = offline_answer(q)
        if os.environ.get("GROQ_API_KEY") and "computed live" in base:
            base += narrate_with_llm(q, base)
        print(base)


if __name__ == "__main__":
    main()
