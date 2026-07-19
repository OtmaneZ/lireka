#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page 11 - rejeu Python de la logique M ajoutee a fact_commandes.

Replique EXACTE des 4 colonnes Power Query (marge_brute_commande, poste_basculant,
tranche_panier, tranche_panier_ordre) puis compare a
page11_outbound_basculant_out/results.json.

Indicateur de temps = execution Python locale, PAS le refresh Power BI Desktop.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Reutilise la resolution facture / cout retenu du prototype valide.
from page11_outbound_ecart_et_poste_basculant import (  # noqa: E402
    BACKEND,
    CHANNELS_NAMED,
    build_cout_retenu,
    load_invoices,
    norm_suivi,
    resolve_facture_to_package,
)

ROOT = Path(__file__).resolve().parents[2]
REF_JSON = Path(__file__).resolve().parent / "page11_outbound_basculant_out" / "results.json"
OUT_DIR = Path(__file__).resolve().parent / "page11_fact_commandes_colonnes_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Ordre et libelles EN - identiques au M fact_commandes.tmdl
COST_POSTES = [
    ("Cost of goods", "cout_achat"),
    ("Inbound transport", "cout_amont"),
    ("Outbound transport", "outbound"),
    ("Duties and taxes", "douanes"),
    ("Marketplace commissions", "commissions"),
    ("Shipping supplies", "fournitures"),
    ("Returns and refunds", "retours"),
    ("Generic costs", "generiques"),
]
STRUCTUREL = "Structurally loss-making"

# Mapping libelles FR (results.json) -> EN (colonne modele)
FR_TO_EN = {
    "Outbound": "Outbound transport",
    "structurellement deficitaire": "Structurally loss-making",
    "Coût Achat": "Cost of goods",
    "Douanes Taxes": "Duties and taxes",
    "Fournitures Expédition": "Shipping supplies",
    "Coûts Génériques": "Generic costs",
    "Commissions Marketplace": "Marketplace commissions",
    "Transport Amont": "Inbound transport",
    "Retours Remboursements": "Returns and refunds",
}

TRANCHE_EDGES = [0, 15, 20, 30, 40, 70, 90, 200]
TRANCHE_LABELS = [
    "Under 15 EUR",
    "15 to 20 EUR",
    "20 to 30 EUR",
    "30 to 40 EUR",
    "40 to 70 EUR",
    "70 to 90 EUR",
    "90 to 200 EUR",
    "200 EUR and above",
]


def canal(source: str) -> str:
    s = (source or "").strip()
    if s.startswith("AMAZON"):
        return "AMAZON"
    if s in CHANNELS_NAMED:
        return s
    return "AUTRES"


def money(x: float) -> str:
    return f"{x:,.2f} EUR".replace(",", " ").replace(".", ",")


def label_tranche(ca_ht: float) -> tuple[str, int]:
    p = 0.0 if pd.isna(ca_ht) else float(ca_ht)
    if p < 15:
        return TRANCHE_LABELS[0], 1
    if p < 20:
        return TRANCHE_LABELS[1], 2
    if p < 30:
        return TRANCHE_LABELS[2], 3
    if p < 40:
        return TRANCHE_LABELS[3], 4
    if p < 70:
        return TRANCHE_LABELS[4], 5
    if p < 90:
        return TRANCHE_LABELS[5], 6
    if p < 200:
        return TRANCHE_LABELS[6], 7
    return TRANCHE_LABELS[7], 8


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    t0 = time.perf_counter()
    timings: dict[str, float] = {}

    print("=" * 72)
    print("REJEU M - fact_commandes colonnes page 11 (cout_transport_retenu)")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. Cout retenu par colis (meme pipeline que le prototype / fact_transport)
    # ------------------------------------------------------------------
    t = time.perf_counter()
    pkg = pd.read_csv(
        BACKEND / "package.csv",
        usecols=[
            "id",
            "order_id",
            "tracking_id",
            "shipping_cost_eur",
            "duties_taxes_eur",
            "shipping_supply_cost_eur",
        ],
        low_memory=False,
    )
    pkg = pkg.rename(columns={"id": "id_package"})
    pkg["id_package"] = pd.to_numeric(pkg["id_package"], errors="coerce").astype("Int64")
    pkg["order_id"] = pd.to_numeric(pkg["order_id"], errors="coerce").astype("Int64")
    for c in ("shipping_cost_eur", "duties_taxes_eur", "shipping_supply_cost_eur"):
        pkg[c] = pd.to_numeric(pkg[c], errors="coerce")
    pkg["numero_suivi"] = norm_suivi(pkg["tracking_id"])

    co_dates = pd.read_csv(
        BACKEND / "customer_order.csv",
        usecols=["id", "origin_created"],
        dtype=str,
        low_memory=False,
    )
    co_dates["id"] = pd.to_numeric(co_dates["id"], errors="coerce").astype("Int64")
    co_dates["date_commande"] = pd.to_datetime(
        co_dates["origin_created"].str.slice(0, 10), errors="coerce"
    )

    inv = load_invoices()
    resolu = resolve_facture_to_package(inv, pkg, co_dates)
    ft = build_cout_retenu(pkg, resolu)
    timings["1_cout_retenu_colis"] = time.perf_counter() - t
    print(f"[temps] 1_cout_retenu_colis     : {timings['1_cout_retenu_colis']:.1f}s")

    # ------------------------------------------------------------------
    # 2. Table.Group equivalent - agregat par order_id
    # ------------------------------------------------------------------
    t = time.perf_counter()
    ft["_out"] = ft["cout_transport_retenu"].fillna(0.0)
    ft["_dut"] = ft["duties_taxes_eur"].fillna(0.0)
    ft["_sup"] = ft["shipping_supply_cost_eur"].fillna(0.0)
    pkg_by_order = (
        ft.groupby("order_id", as_index=False)
        .agg(
            outbound=("_out", "sum"),
            douanes=("_dut", "sum"),
            fournitures=("_sup", "sum"),
        )
    )
    timings["2_group_par_commande"] = time.perf_counter() - t
    print(f"[temps] 2_group_par_commande    : {timings['2_group_par_commande']:.1f}s")

    # ------------------------------------------------------------------
    # 3. Commandes + marge_brute_commande (logique M)
    # ------------------------------------------------------------------
    t = time.perf_counter()
    cols = [
        "id",
        "state",
        "source",
        "order_amount_eur",
        "shipping_fee_eur",
        "product_cost_eur",
        "inbound_transportation_cost_eur",
        "marketplace_fees_eur",
        "returns_and_refunds_eur",
        "total_generic_costs_eur",
    ]
    orders = pd.read_csv(BACKEND / "customer_order.csv", usecols=cols, low_memory=False)
    orders["id"] = pd.to_numeric(orders["id"], errors="coerce").astype("Int64")
    for c in cols:
        if c not in ("id", "state", "source"):
            orders[c] = pd.to_numeric(orders[c], errors="coerce")
    orders["state"] = orders["state"].astype(str).fillna("")
    orders["canal"] = orders["source"].map(lambda x: canal("" if pd.isna(x) else str(x)))

    m = orders.merge(pkg_by_order, how="left", left_on="id", right_on="order_id")
    for c in ("outbound", "douanes", "fournitures"):
        m[c] = m[c].fillna(0.0)

    cancelled = m["state"] == "CANCELLED"
    # if [state] = "CANCELLED" then 0 else [ca_ht]  (null -> 0)
    m["ca_ht_net"] = np.where(cancelled, 0.0, m["order_amount_eur"].fillna(0.0))
    m["frais_port_net"] = np.where(cancelled, 0.0, m["shipping_fee_eur"].fillna(0.0))
    m["cout_achat"] = m["product_cost_eur"].fillna(0.0)
    m["cout_amont"] = m["inbound_transportation_cost_eur"].fillna(0.0)
    m["commissions"] = m["marketplace_fees_eur"].fillna(0.0)
    m["retours"] = m["returns_and_refunds_eur"].fillna(0.0)
    m["generiques"] = m["total_generic_costs_eur"].fillna(0.0)

    m["marge_brute_commande"] = (
        m["ca_ht_net"]
        + m["frais_port_net"]
        - m["cout_achat"]
        - m["cout_amont"]
        - m["outbound"]
        - m["douanes"]
        - m["commissions"]
        - m["fournitures"]
        - m["retours"]
        - m["generiques"]
    )
    timings["3_marge_brute_commande"] = time.perf_counter() - t
    print(f"[temps] 3_marge_brute_commande  : {timings['3_marge_brute_commande']:.1f}s")

    # ------------------------------------------------------------------
    # 4. Poste basculant - deux passes (medianes puis simulation)
    # ------------------------------------------------------------------
    t = time.perf_counter()
    loss_mask = m["marge_brute_commande"] < 0
    ok_mask = m["marge_brute_commande"] >= 0
    loss = m.loc[loss_mask].copy()
    ok = m.loc[ok_mask].copy()

    t_med = time.perf_counter()
    median_ref: dict[tuple[str, str], float] = {}
    for canal_name, g in ok.groupby("canal"):
        g_pos = g[g["ca_ht_net"] > 0]
        for label, col in COST_POSTES:
            if len(g_pos) == 0:
                median_ref[(canal_name, col)] = 0.0
            else:
                ratios = g_pos[col] / g_pos["ca_ht_net"]
                median_ref[(canal_name, col)] = float(ratios.median())
    timings["4a_medianes_canal"] = time.perf_counter() - t_med
    print(f"[temps] 4a_medianes_canal       : {timings['4a_medianes_canal']:.1f}s")

    t_sim = time.perf_counter()
    canals = loss["canal"].to_numpy()
    ca = loss["ca_ht_net"].to_numpy(dtype=float)
    marge0 = loss["marge_brute_commande"].to_numpy(dtype=float)
    n_loss = len(loss)
    n_postes = len(COST_POSTES)
    amelio = np.full((n_loss, n_postes), -np.inf)
    flip = np.zeros((n_loss, n_postes), dtype=bool)

    for j, (label, col) in enumerate(COST_POSTES):
        med_r = np.array([median_ref.get((c, col), 0.0) for c in canals], dtype=float)
        poste_act = loss[col].to_numpy(dtype=float)
        poste_sim = med_r * ca
        new_marge = marge0 + (poste_act - poste_sim)
        ok_flip = new_marge > 0
        flip[:, j] = ok_flip
        amelio[:, j] = np.where(ok_flip, poste_act - poste_sim, -np.inf)

    any_flip = flip.any(axis=1)
    best_j = np.argmax(amelio, axis=1)
    labels = np.array([c[0] for c in COST_POSTES], dtype=object)
    poste_b = np.where(any_flip, labels[best_j], STRUCTUREL)
    timings["4b_simulation_deficitaires"] = time.perf_counter() - t_sim
    print(f"[temps] 4b_simulation_deficitaires : {timings['4b_simulation_deficitaires']:.1f}s")

    m["poste_basculant"] = pd.NA
    m.loc[loss_mask, "poste_basculant"] = poste_b
    timings["4_poste_basculant_total"] = time.perf_counter() - t
    print(f"[temps] 4_poste_basculant_total : {timings['4_poste_basculant_total']:.1f}s")

    # ------------------------------------------------------------------
    # 5. Tranche panier
    # ------------------------------------------------------------------
    t = time.perf_counter()
    tranches = m["order_amount_eur"].map(label_tranche)
    m["tranche_panier"] = tranches.map(lambda x: x[0])
    m["tranche_panier_ordre"] = tranches.map(lambda x: x[1]).astype(int)
    timings["5_tranche_panier"] = time.perf_counter() - t
    print(f"[temps] 5_tranche_panier        : {timings['5_tranche_panier']:.1f}s")

    timings["total"] = time.perf_counter() - t0
    print(f"[temps] TOTAL (indicateur Python, pas refresh PBI) : {timings['total']:.1f}s")

    # ------------------------------------------------------------------
    # Controles chiffres vs results.json
    # ------------------------------------------------------------------
    with open(REF_JSON, encoding="utf-8") as f:
        ref = json.load(f)

    sum_marge = float(m["marge_brute_commande"].sum())
    n_def = int(loss_mask.sum())
    pertes = float(m.loc[loss_mask, "marge_brute_commande"].sum())

    attributed = m.loc[loss_mask, ["id", "marge_brute_commande", "poste_basculant"]].copy()
    assert attributed["poste_basculant"].isna().sum() == 0
    somme_repartie = float(attributed["marge_brute_commande"].sum())

    # Repartition EN
    tl = []
    for label in [c[0] for c in COST_POSTES] + [STRUCTUREL]:
        sub = attributed[attributed["poste_basculant"] == label]
        tl.append(
            {
                "poste_basculant": label,
                "n_commandes": int(len(sub)),
                "somme_pertes_eur": float(sub["marge_brute_commande"].sum()),
            }
        )
    tl.sort(key=lambda r: r["n_commandes"], reverse=True)

    # Tableau comparatif vs reference (FR -> EN)
    ref_rep = ref["tache2"]["repartition"]
    rows_cmp = []
    all_ok = True
    for r in ref_rep:
        en = FR_TO_EN[r["poste_basculant"]]
        mine = next(x for x in tl if x["poste_basculant"] == en)
        dn = mine["n_commandes"] - r["n_commandes"]
        dp = mine["somme_pertes_eur"] - r["somme_pertes_eur"]
        ok_line = dn == 0 and abs(dp) <= 0.01
        if not ok_line:
            all_ok = False
        rows_cmp.append(
            {
                "poste": en,
                "n_ref": r["n_commandes"],
                "n_replay": mine["n_commandes"],
                "delta_n": dn,
                "pertes_ref": r["somme_pertes_eur"],
                "pertes_replay": mine["somme_pertes_eur"],
                "delta_pertes": dp,
                "ok": ok_line,
            }
        )

    ref_marge_retenu = float(ref["tache1"]["marge_globale_retenu_eur"])
    ref_n_def = int(ref["tache2"]["n_deficitaires"])
    ref_pertes = float(ref["tache2"]["pertes_totales_eur"])

    c1 = abs(sum_marge - ref_marge_retenu) <= 0.01
    c2 = n_def == ref_n_def
    c3 = all_ok
    c4 = abs(somme_repartie - pertes) <= 0.01 and int(attributed["poste_basculant"].isna().sum()) == 0

    print("\n" + "=" * 72)
    print("CONTROLES CHIFFRES")
    print("=" * 72)
    print(
        f"1. SUM marge_brute_commande = {money(sum_marge)}"
        f"  (ref retenu {money(ref_marge_retenu)})  "
        f"{'OK' if c1 else 'ECHEC'}  delta={sum_marge - ref_marge_retenu:.4f}"
    )
    print(
        "   Variante implementee : cout_transport_retenu "
        "(aligne sur [Marge Brute] / [Coût Transport Outbound (Retenu)])."
    )
    print(
        f"   Note : 8 594 310,20 = variante backend ; "
        f"8 628 442,68 = SUM cout_transport_retenu (pas la marge)."
    )
    print(f"2. Nb deficitaires = {n_def:,}  (ref {ref_n_def:,})  {'OK' if c2 else 'ECHEC'}".replace(",", " "))
    print(f"3. Repartition poste basculant : {'OK' if c3 else 'ECHEC'}")
    print(
        f"{'poste':<28} {'n_ref':>8} {'n_replay':>8} {'d_n':>6} "
        f"{'pertes_ref':>16} {'pertes_replay':>16} {'ok':>4}"
    )
    for r in rows_cmp:
        print(
            f"{r['poste']:<28} {r['n_ref']:>8} {r['n_replay']:>8} {r['delta_n']:>6} "
            f"{money(r['pertes_ref']):>16} {money(r['pertes_replay']):>16} "
            f"{'OK' if r['ok'] else 'KO':>4}"
        )
    print(
        f"4. Somme pertes repartie = {money(somme_repartie)} "
        f"vs pertes totales {money(pertes)}  "
        f"{'OK' if c4 else 'ECHEC'}  (non classes={int(attributed['poste_basculant'].isna().sum())})"
    )

    # Apercu tranches
    print("\nTranche panier (aperçu) :")
    for lab, ord_ in zip(TRANCHE_LABELS, range(1, 9)):
        n = int((m["tranche_panier"] == lab).sum())
        print(f"  {ord_}. {lab:<22} n={n:>8}")

    results = {
        "variante_outbound": "cout_transport_retenu",
        "sum_marge_brute_commande": sum_marge,
        "ref_marge_globale_retenu_eur": ref_marge_retenu,
        "n_deficitaires": n_def,
        "pertes_totales_eur": pertes,
        "somme_repartie_eur": somme_repartie,
        "repartition": tl,
        "comparaison_ref": rows_cmp,
        "controles": {
            "c1_somme_marge": c1,
            "c2_n_deficitaires": c2,
            "c3_repartition": c3,
            "c4_somme_repartie": c4,
            "all_ok": c1 and c2 and c3 and c4,
        },
        "timings_s": timings,
        "note_temps": (
            "Indicateur d'execution Python locale uniquement ; "
            "ne mesure pas le refresh Power BI Desktop."
        ),
    }
    out_json = OUT_DIR / "results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON : {out_json}")

    if not (c1 and c2 and c3 and c4):
        print("\n*** CONTROLE CHIFFRES ECHOUE - ne pas committer. ***")
        return 1
    print("\nTous les controles chiffres OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
