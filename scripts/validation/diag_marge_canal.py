"""Diagnostic BLOQUANT General View — pourquoi Gross Profit / Gross Margin sont négatifs.

LECTURE SEULE. Réplique au grain commande (hors CANCELLED) :
  - CA brut          = order_amount_eur                       (= numérateur de [Marge Brute])
  - CA reconstruit   = order_amount_eur si >0 sinon local/taux (= numérateur de [Marge Brute (reconstruit)])
  - coûts commande   = product + inbound + marketplace_fees + duties + returns/generic (bloc5)
  - marge brute (brut)        = CA brut + shipping_fee - coûts commande
  - marge brute (reconstruit) = CA reconstruit + shipping_fee - coûts commande
Le coût transport outbound (fact_transport) n'est PAS inclus ici (grain colis) : le signe
de la marge marketplace est déjà démontré au grain commande. gross_profit_eur backend fourni en repère.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"
CO = ROOT / "Données_Backend" / "customer_order.csv"
ITEM = ROOT / "Données_Backend" / "customer_order_item.csv"


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


def main() -> None:
    co = pd.read_csv(
        CO,
        usecols=["id", "state", "source", "currency", "currency_rate",
                 "order_amount_eur", "order_amount_local", "origin_created",
                 "product_cost_eur", "marketplace_fees_eur",
                 "inbound_transportation_cost_eur", "duties_and_taxes_eur",
                 "shipping_fee_eur", "gross_profit_eur"],
        dtype={"state": "string", "source": "string", "currency": "string"},
        low_memory=False,
    )
    co["annee_mois"] = co["origin_created"].str.slice(0, 7).str.replace("-", "", regex=False)
    co["annee_mois"] = pd.to_numeric(co["annee_mois"], errors="coerce")
    rate = num(co["currency_rate"])

    # Taux moyen mensuel par (currency, annee_mois) — comme stg_taux_moyen_mensuel
    tx = (
        co.assign(_r=rate)
        .dropna(subset=["currency", "annee_mois", "_r"])
        .groupby(["currency", "annee_mois"])["_r"].mean()
        .rename("taux")
        .reset_index()
    )
    co = co.merge(tx, on=["currency", "annee_mois"], how="left")

    oa = num(co["order_amount_eur"]).fillna(0)
    loc = num(co["order_amount_local"]).fillna(0)
    taux = num(co["taux"])
    ca_reco = np.where(
        oa != 0, oa,
        np.where((loc != 0) & taux.notna() & (taux != 0), loc / taux, 0.0),
    )

    ship = num(co["shipping_fee_eur"]).fillna(0)
    pcost = num(co["product_cost_eur"]).fillna(0)
    inbound = num(co["inbound_transportation_cost_eur"]).fillna(0)
    mkt = num(co["marketplace_fees_eur"]).fillna(0)
    duties = num(co["duties_and_taxes_eur"]).fillna(0)
    gp_backend = num(co["gross_profit_eur"]).fillna(0)

    # coûts Bloc5 (returns + generic) agrégés par order depuis items
    r_sum = np.zeros(len(co))
    g_sum = np.zeros(len(co))
    idx = co.set_index("id")
    acc = None
    for ch in pd.read_csv(
        ITEM, usecols=["order_id", "returns_and_refunds_cost_eur", "generic_costs_eur"],
        chunksize=300_000, low_memory=False,
    ):
        ch["returns_and_refunds_cost_eur"] = num(ch["returns_and_refunds_cost_eur"])
        ch["generic_costs_eur"] = num(ch["generic_costs_eur"])
        g = ch.groupby("order_id")[["returns_and_refunds_cost_eur", "generic_costs_eur"]].sum()
        acc = g if acc is None else acc.add(g, fill_value=0)
    bloc5 = idx.join(acc).reindex(co["id"].values)
    ret = num(bloc5["returns_and_refunds_cost_eur"]).fillna(0).values
    gen = num(bloc5["generic_costs_eur"]).fillna(0).values

    co["_canal"] = co["source"].map(canal)
    hors_cancel = ~co["state"].str.strip().str.upper().eq("CANCELLED")

    couts_cmd = pcost + inbound + mkt + duties + ret + gen
    marge_brut = oa + ship - couts_cmd
    marge_reco = ca_reco + ship - couts_cmd

    df = pd.DataFrame({
        "canal": co["_canal"],
        "hc": hors_cancel,
        "ca_brut": oa,
        "ca_reco": ca_reco,
        "marge_brut": marge_brut,
        "marge_reco": marge_reco,
        "gp_backend": gp_backend,
    })
    d = df[df["hc"]].groupby("canal").agg(
        n=("ca_brut", "size"),
        ca_brut=("ca_brut", "sum"),
        ca_reconstruit=("ca_reco", "sum"),
        marge_brut_num=("marge_brut", "sum"),
        marge_reconstruit_num=("marge_reco", "sum"),
        gp_backend=("gp_backend", "sum"),
    )
    tot = d.sum(numeric_only=True)
    tot.name = "TOTAL"
    d = pd.concat([d, tot.to_frame().T])
    d["taux_marge_brut_%"] = (100 * d["marge_brut_num"] / d["ca_reconstruit"]).round(1)
    d["taux_marge_reco_%"] = (100 * d["marge_reconstruit_num"] / d["ca_reconstruit"]).round(1)
    for c in ["ca_brut", "ca_reconstruit", "marge_brut_num", "marge_reconstruit_num", "gp_backend"]:
        d[c] = (d[c] / 1000).round(1)  # en K€

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print("=== Par canal (hors CANCELLED) — montants en K€ ===")
    print(d.to_string())
    print("\nLecture :")
    print("  ca_brut          = numérateur réel de [Marge Brute]           (order_amount_eur)")
    print("  ca_reconstruit   = numérateur de [Marge Brute (reconstruit)]  (local/taux si eur=0)")
    print("  marge_brut_num   ≈ [Marge Brute] (grain commande, hors coût transport colis)")
    print("  marge_reconstruit_num ≈ [Marge Brute (reconstruit)]")

    out = Path(__file__).parent / "diag_marge_canal_output.json"
    out.write_text(d.to_json(orient="index", force_ascii=False, indent=2), encoding="utf-8")
    print(f"\nÉcrit : {out}")


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
