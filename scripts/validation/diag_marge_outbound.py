"""Diagnostic: marge marketplace avec outbound — cause du taux vs cible Marc ~10%."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"
CO = ROOT / "Données_Backend" / "customer_order.csv"
PKG = ROOT / "Données_Backend" / "package.csv"
OUT = Path(__file__).with_name("diag_marge_outbound_output.json")


def num(s):
    return pd.to_numeric(s, errors="coerce")


def canal(source: str) -> str:
    s = (source or "").strip().upper()
    if s == "WEBSITE":
        return "Website B2C"
    if s == "PRO_WEBSITE":
        return "Website B2B"
    if s.startswith("AMAZON") or s in ("CULTURA", "RAKUTEN", "FNAC"):
        return "Marketplaces"
    if s == "ARTHAUD":
        return "Librairie Arthaud"
    return "Autre"


def model_rates(co: pd.DataFrame, mask, label: str, verbose: bool = True) -> dict:
    d_all = co.loc[mask]
    d_hc = d_all[d_all["hc"]]
    ca = float(d_hc["order_amount_eur"].sum())
    ship = float(d_hc["shipping_fee_eur"].sum())
    revenu = ca + ship

    posts = {
        "cogs": float(d_all["product_cost_eur"].sum()),
        "inbound": float(d_all["inbound_transportation_cost_eur"].sum()),
        "outbound": float(d_all["outbound"].sum()),
        "duties": float(d_all["duties_pkg"].sum()),
        "mkt_fees": float(d_all["marketplace_fees_eur"].sum()),
        "supplies": float(d_all["supplies"].sum()),
        "returns": float(d_all["returns_and_refunds_eur"].sum()),
        "generics": float(d_all["total_generic_costs_eur"].sum()),
    }
    marge7 = revenu - sum(
        posts[k] for k in ("cogs", "inbound", "outbound", "duties", "mkt_fees", "supplies")
    )
    marge9 = marge7 - posts["returns"] - posts["generics"]
    gp = float(d_hc["gross_profit_eur"].sum())

    def pct(m):
        return round(100 * m / revenu, 2) if revenu else None

    bridge = []
    running = revenu
    for name in (
        "cogs",
        "inbound",
        "outbound",
        "duties",
        "mkt_fees",
        "supplies",
        "returns",
        "generics",
    ):
        val = posts[name]
        running -= val
        bridge.append(
            {
                "poste": name,
                "montant_m": round(val / 1e6, 3),
                "pts": round(100 * val / revenu, 1) if revenu else None,
                "taux_restant_%": round(100 * running / revenu, 2) if revenu else None,
            }
        )

    row = {
        "label": label,
        "n_all": int(len(d_all)),
        "n_hc": int(len(d_hc)),
        "revenu_m": round(revenu / 1e6, 3),
        "taux_7postes_%": pct(marge7),
        "taux_9postes_MargeBrute_%": pct(marge9),
        "taux_backend_gp_vs_revenu_%": pct(gp),
        "posts_m": {k: round(v / 1e6, 3) for k, v in posts.items()},
        "bridge": bridge,
    }
    if verbose:
        print(f"\n=== {label} ===")
        print(
            f"n_all={row['n_all']:,} n_hc={row['n_hc']:,} revenu={row['revenu_m']}M€"
        )
        for b in bridge:
            print(
                f"  - {b['poste']:10} {b['montant_m']:7.3f}M ({b['pts']:5.1f} pts) "
                f"-> {b['taux_restant_%']:5.2f}%"
            )
        print(
            f"  TAUX 7 postes={row['taux_7postes_%']}% | "
            f"9 postes (actuel)={row['taux_9postes_MargeBrute_%']}% | "
            f"backend GP={row['taux_backend_gp_vs_revenu_%']}%"
        )
    return row


def main() -> None:
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("Loading orders...")
    co = pd.read_csv(
        CO,
        usecols=[
            "id",
            "state",
            "source",
            "origin_created",
            "order_amount_eur",
            "shipping_fee_eur",
            "product_cost_eur",
            "marketplace_fees_eur",
            "inbound_transportation_cost_eur",
            "returns_and_refunds_eur",
            "total_generic_costs_eur",
            "gross_profit_eur",
        ],
        dtype={"state": "string", "source": "string"},
        low_memory=False,
    )
    money = [
        "order_amount_eur",
        "shipping_fee_eur",
        "product_cost_eur",
        "marketplace_fees_eur",
        "inbound_transportation_cost_eur",
        "returns_and_refunds_eur",
        "total_generic_costs_eur",
        "gross_profit_eur",
    ]
    for c in money:
        co[c] = num(co[c]).fillna(0)
    co["date"] = pd.to_datetime(
        co["origin_created"].astype(str).str.slice(0, 10), errors="coerce"
    )
    co["canal"] = co["source"].map(canal)
    co["hc"] = ~co["state"].str.strip().str.upper().eq("CANCELLED")

    print("Loading packages...")
    pkg = pd.read_csv(
        PKG,
        usecols=[
            "order_id",
            "shipping_cost_eur",
            "shipping_supply_cost_eur",
            "duties_taxes_eur",
        ],
        low_memory=False,
    )
    for c in ("shipping_cost_eur", "shipping_supply_cost_eur", "duties_taxes_eur"):
        pkg[c] = num(pkg[c]).fillna(0)
    agg = (
        pkg.groupby("order_id")
        .agg(
            outbound=("shipping_cost_eur", "sum"),
            supplies=("shipping_supply_cost_eur", "sum"),
            duties_pkg=("duties_taxes_eur", "sum"),
        )
        .reset_index()
    )
    co = co.merge(agg, left_on="id", right_on="order_id", how="left")
    for c in ("outbound", "supplies", "duties_pkg"):
        co[c] = co[c].fillna(0)

    today = datetime(2026, 8, 4)
    start_12m = today - timedelta(days=365)

    rows = [
        model_rates(co, co["canal"].eq("Marketplaces"), "MKT all time"),
        model_rates(
            co,
            co["canal"].eq("Marketplaces")
            & (co["date"] >= "2025-01-01")
            & (co["date"] <= "2025-12-31"),
            "MKT calendar 2025",
        ),
        model_rates(
            co,
            co["canal"].eq("Marketplaces")
            & (co["date"] >= start_12m)
            & (co["date"] <= today),
            "MKT last 12m (page filter ~)",
        ),
        model_rates(
            co,
            co["canal"].eq("Website B2C")
            & (co["date"] >= "2025-01-01")
            & (co["date"] <= "2025-12-31"),
            "WEB B2C 2025",
        ),
        model_rates(
            co,
            (co["date"] >= "2025-01-01") & (co["date"] <= "2025-12-31"),
            "ALL 2025",
        ),
    ]

    # Zoom: période dont taux9 ≈ 25.3%
    print("\n=== Recherche période dont taux9 ≈ 25.3% (MKT) ===")
    mkt = co[co["canal"].eq("Marketplaces")].copy()
    closest = []
    for months_back in range(1, 25):
        start = today - timedelta(days=30 * months_back)
        mask = (mkt["date"] >= start) & (mkt["date"] <= today)
        r = model_rates(mkt, mask, f"MKT last {months_back}x30d", verbose=False)
        closest.append(
            (
                abs((r["taux_9postes_MargeBrute_%"] or 999) - 25.3),
                months_back,
                r["taux_9postes_MargeBrute_%"],
                r["taux_7postes_%"],
                r["revenu_m"],
            )
        )
    closest.sort()
    print("Top 5 périodes les plus proches de 25.3% (taux9):")
    for dist, mb, t9, t7, rev in closest[:5]:
        print(
            f"  last {mb * 30}d ≈ {mb}m : taux9={t9}% taux7={t7}% rev={rev}M (Δ={dist:.2f})"
        )

    # By marketplace channel 12m
    print("\n=== Par place (MKT last 12m) ===")
    mask12 = (
        (co["date"] >= start_12m)
        & (co["date"] <= today)
        & co["canal"].eq("Marketplaces")
    )
    by_src = []
    for src, g in co.loc[mask12].groupby("source", sort=False):
        r = model_rates(g, g.index.isin(g.index), str(src), verbose=False)
        print(
            f"  {src:12} rev={r['revenu_m']:6.2f}M  "
            f"taux7={r['taux_7postes_%']:6.2f}%  taux9={r['taux_9postes_MargeBrute_%']:6.2f}%  "
            f"outbound={r['posts_m']['outbound']:5.2f}M  fees={r['posts_m']['mkt_fees']:5.2f}M"
        )
        by_src.append(r)

    OUT.write_text(
        json.dumps({"scenarios": rows, "by_source_12m": by_src}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nÉcrit : {OUT}")


if __name__ == "__main__":
    main()
