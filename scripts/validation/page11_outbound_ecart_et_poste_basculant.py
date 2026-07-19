#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page 11 — ecart outbound (backend vs retenu) + poste basculant.

LECTURE SEULE. Aucune modification du modele.
Chaque chiffre est issu d'un calcul execute.

Tache 1 : replique fact_transport[cout_transport_retenu] (M cite dans le script)
           et mesure l'ecart vs SUM(package.shipping_cost_eur).
Tache 2 : poste basculant des commandes deficitaires (vs mediane canal non-deficitaire).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DWH = ROOT / "Power_BI_Datawarehouse"
BACKEND = DWH / "Données_Backend"
COL_DIR = DWH / "Dashboards_transporteurs" / "COLISSIMO Dashboard PowerBI"
CHR_DIR = DWH / "Dashboards_transporteurs" / "CHRONOPOST Dashboard PowerBI"
OUT_DIR = Path(__file__).resolve().parent / "page11_outbound_basculant_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Fichiers cites par expressions.tmdl / stg_factures_brutes
INVOICE_FILES = [
    COL_DIR / "2025_COLISSIMO_récap.csv",
    COL_DIR / "2026_COLISSIMO_récap_au_30_juin_2026.csv",
    CHR_DIR / "2025_CHRONOPOST_récap.csv",
    CHR_DIR / "2026_CHRONOPOST_V2.csv",
]

FENETRE_TOLERANCE_JOURS = 7  # Fix F-11, expressions.tmdl

# Cite verbatim depuis fact_transport.tmdl (regle de choix)
REGLE_RETENU_M = """
#"Cout retenu ajoute" = Table.AddColumn(
    #"Jointure facture",
    "cout_transport_retenu",
    each if [cout_transport_facture] <> null then [cout_transport_facture] else [cout_transport],
    type nullable number
)
"""
# cout_transport_facture = SUM des lignes facture resolues (id_package <> null)
# par id_package, depuis stg_factures_transport_resolu.

CHANNELS_NAMED = {"WEBSITE", "PRO_WEBSITE", "CULTURA", "RAKUTEN", "FNAC"}
COST_POSTES = [
    ("Coût Achat", "cout_achat"),
    ("Transport Amont", "cout_amont"),
    ("Outbound", "outbound"),
    ("Douanes Taxes", "douanes"),
    ("Commissions Marketplace", "commissions"),
    ("Fournitures Expédition", "fournitures"),
    ("Retours Remboursements", "retours"),
    ("Coûts Génériques", "generiques"),
]
STRUCTUREL = "structurellement deficitaire"


def canal(source: str) -> str:
    s = (source or "").strip()
    if s.startswith("AMAZON"):
        return "AMAZON"
    if s in CHANNELS_NAMED:
        return s
    return "AUTRES"


def norm_suivi(s: pd.Series) -> pd.Series:
    """fnNormaliserSuivi : NBSP -> espace, trim, upper."""
    return (
        s.astype("string")
        .fillna("")
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
        .str.upper()
    )


def money(x: float) -> str:
    return f"{x:,.2f} EUR".replace(",", " ").replace(".", ",")


def pct(x: float) -> str:
    return f"{100.0 * x:,.4f} pct".replace(",", " ").replace(".", ",")


def parse_fr_number(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype("string").str.replace("\u00a0", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def load_invoices() -> pd.DataFrame:
    """stg_factures_brutes — fichiers exacts du modele."""
    parts = []

    # Colissimo
    for p in INVOICE_FILES[:2]:
        df = pd.read_csv(p, sep=";", dtype=str, encoding="utf-8")
        df.columns = [c.lstrip("\ufeff") for c in df.columns]
        part = pd.DataFrame(
            {
                "numero_suivi": norm_suivi(df["N° de colis"]),
                "date_facture": pd.to_datetime(df["Date"], dayfirst=True, errors="coerce"),
                "cout_transport": parse_fr_number(df["TOTAL HT"]),
                "source_fichier": p.name,
            }
        )
        parts.append(part)

    # Chronopost 2025
    p = INVOICE_FILES[2]
    df = pd.read_csv(p, sep=";", dtype=str, encoding="utf-8")
    df.columns = [c.lstrip("\ufeff") for c in df.columns]
    parts.append(
        pd.DataFrame(
            {
                "numero_suivi": norm_suivi(df["N° de colis"]),
                "date_facture": pd.to_datetime(df["Date"], dayfirst=True, errors="coerce"),
                "cout_transport": parse_fr_number(df["TOTAL HT"]),
                "source_fichier": p.name,
            }
        )
    )

    # Chronopost 2026 V2
    p = INVOICE_FILES[3]
    df = pd.read_csv(p, sep=";", dtype=str, encoding="utf-8")
    df.columns = [c.lstrip("\ufeff") for c in df.columns]
    parts.append(
        pd.DataFrame(
            {
                "numero_suivi": norm_suivi(df["N° de colis (N° objet)"]),
                "date_facture": pd.to_datetime(df["Date"], dayfirst=True, errors="coerce"),
                "cout_transport": parse_fr_number(df["TOTAL HT"]),
                "source_fichier": p.name,
            }
        )
    )

    inv = pd.concat(parts, ignore_index=True)
    # Lignes valides : cout_transport <> null (M)
    inv = inv[inv["cout_transport"].notna()].copy()
    return inv


def resolve_facture_to_package(inv: pd.DataFrame, pkg: pd.DataFrame, co_dates: pd.DataFrame) -> pd.DataFrame:
    """
    stg_factures_transport_resolu (F-11) :
      - join inner sur numero_suivi (non vide)
      - 1 candidat -> accepte
      - >=2 -> meilleur |date_commande - date_facture|, tie-break id_package ;
               rejette si delta > 7 jours
    Retourne factures avec id_package resolu (nullable).
    """
    colis = pkg[["id_package", "order_id", "numero_suivi"]].copy()
    colis = colis.merge(co_dates, left_on="order_id", right_on="id", how="left")

    inv_ok = inv[(inv["numero_suivi"].notna()) & (inv["numero_suivi"] != "")].copy()
    colis_ok = colis[(colis["numero_suivi"].notna()) & (colis["numero_suivi"] != "")].copy()

    inv_ok = inv_ok.reset_index(drop=True).reset_index().rename(columns={"index": "inv_idx"})
    merged = inv_ok.merge(colis_ok, on="numero_suivi", how="inner")
    if merged.empty:
        inv_ok["id_package"] = pd.NA
        inv_ok["nb_candidats_resolution"] = 0
        return inv_ok

    delta = (merged["date_commande"] - merged["date_facture"]).abs().dt.total_seconds() / 86400.0
    merged["delta"] = delta.fillna(1_000_000_000.0)

    nb = merged.groupby("inv_idx").size().rename("nb_candidats_resolution")
    merged = merged.merge(nb, on="inv_idx", how="left")

    best = merged.sort_values(
        ["inv_idx", "delta", "id_package"], ascending=[True, True, True]
    ).drop_duplicates("inv_idx", keep="first")

    # Regle F-11
    accepted = best["id_package"].where(
        (best["nb_candidats_resolution"] == 1)
        | (best["delta"] <= FENETRE_TOLERANCE_JOURS),
        other=pd.NA,
    )
    resolu = inv_ok[["inv_idx", "numero_suivi", "date_facture", "cout_transport", "source_fichier"]].merge(
        best[["inv_idx", "nb_candidats_resolution"]].assign(id_package=accepted),
        on="inv_idx",
        how="left",
    )
    # Factures sans aucun candidat (pas dans merge) : nb=0, id_package null
    resolu["nb_candidats_resolution"] = resolu["nb_candidats_resolution"].fillna(0).astype(int)
    return resolu


def build_cout_retenu(pkg: pd.DataFrame, factures_resolues: pd.DataFrame) -> pd.DataFrame:
    """
    fact_transport M :
      GroupBy id_package SUM(cout_transport) où id_package <> null
      cout_transport_retenu = facture si non null sinon backend
    """
    matched = factures_resolues[factures_resolues["id_package"].notna()].copy()
    matched["id_package"] = matched["id_package"].astype("Int64")
    fact_by_pkg = (
        matched.groupby("id_package", as_index=False)["cout_transport"]
        .sum()
        .rename(columns={"cout_transport": "cout_transport_facture"})
    )

    out = pkg.merge(fact_by_pkg, on="id_package", how="left")
    # Regle exacte citee
    out["cout_transport_retenu"] = np.where(
        out["cout_transport_facture"].notna(),
        out["cout_transport_facture"],
        out["shipping_cost_eur"],
    )
    out["source_cout"] = np.where(
        out["cout_transport_facture"].notna(),
        "facture_rapprochee",
        np.where(
            out["shipping_cost_eur"].isna() | (out["shipping_cost_eur"] == 0),
            "aucun",
            "backend_seul",
        ),
    )
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print("=" * 72)
    print("TACHE 1 — Ecart outbound backend vs retenu")
    print("=" * 72)
    print("Regle M (fact_transport.tmdl) :")
    print(REGLE_RETENU_M)
    print(
        "Choix exact : si cout_transport_facture <> null alors facture "
        "(SUM des lignes facture resolues sur le colis), sinon shipping_cost_eur backend."
    )
    print(
        f"Resolution facture->colis : stg_factures_transport_resolu, "
        f"fenetre {FENETRE_TOLERANCE_JOURS}j si >=2 candidats."
    )

    print("\nFichiers factures (expressions.tmdl) :")
    absent = []
    for p in INVOICE_FILES:
        ok = p.exists()
        print(f"  [{'OK' if ok else 'ABSENT'}] {p}")
        if not ok:
            absent.append(str(p))
    if absent:
        print("\n*** FICHIERS FACTURES ABSENTS — Tache 1 arretee. Passage a la Tache 2. ***")
        # Tache 2 utilisera outbound = shipping_cost_eur (prototype)
        use_retenu = False
        tache1 = {
            "fichiers_presents": False,
            "fichiers_absents": absent,
            "arretee": True,
        }
        pkg_by_order = None
        outbound_col_note = "shipping_cost_eur (tache 1 arretee)"
    else:
        use_retenu = True
        outbound_col_note = "cout_transport_retenu replique"

        print("\nChargement package + commandes (dates)...")
        pkg = pd.read_csv(
            BACKEND / "package.csv",
            usecols=["id", "order_id", "tracking_id", "shipping_cost_eur", "duties_taxes_eur", "shipping_supply_cost_eur"],
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

        print("Chargement factures...")
        inv = load_invoices()
        print(f"  lignes facture valides : {len(inv):,}".replace(",", " "))

        print("Resolution facture -> colis (F-11)...")
        resolu = resolve_facture_to_package(inv, pkg, co_dates)
        n_resolues = int(resolu["id_package"].notna().sum())
        n_non_resolues = int(resolu["id_package"].isna().sum())
        print(f"  factures resolues (id_package non null) : {n_resolues:,}".replace(",", " "))
        print(f"  factures non resolues                   : {n_non_resolues:,}".replace(",", " "))

        print("Construction cout_transport_retenu...")
        ft = build_cout_retenu(pkg, resolu)

        sum_backend = float(ft["shipping_cost_eur"].fillna(0).sum())
        sum_retenu = float(ft["cout_transport_retenu"].fillna(0).sum())
        ecart_abs = sum_retenu - sum_backend
        ecart_pct = (ecart_abs / sum_backend) if sum_backend != 0 else float("nan")

        n_rapproches = int((ft["source_cout"] == "facture_rapprochee").sum())
        n_backend_seul = int((ft["source_cout"] == "backend_seul").sum())
        n_aucun = int((ft["source_cout"] == "aucun").sum())
        n_colis = len(ft)

        # Sur les colis rapproches : ecart ligne a ligne facture vs backend
        rap = ft[ft["source_cout"] == "facture_rapprochee"]
        delta_rap = float(
            (rap["cout_transport_retenu"].fillna(0) - rap["shipping_cost_eur"].fillna(0)).sum()
        )

        print(f"\nSUM package.shipping_cost_eur     : {money(sum_backend)}")
        print(f"SUM cout_transport_retenu         : {money(sum_retenu)}")
        print(f"Ecart (retenu - backend)          : {money(ecart_abs)} ({pct(ecart_pct)})")
        print(f"Colis facture_rapprochee          : {n_rapproches:,} / {n_colis:,}".replace(",", " "))
        print(f"Colis backend_seul                : {n_backend_seul:,}".replace(",", " "))
        print(f"Colis aucun                       : {n_aucun:,}".replace(",", " "))
        print(f"Ecart concentre sur colis rapproches : {money(delta_rap)}")

        ft["_backend"] = ft["shipping_cost_eur"].fillna(0.0)
        ft["_retenu"] = ft["cout_transport_retenu"].fillna(0.0)
        ft["_duties"] = ft["duties_taxes_eur"].fillna(0.0)
        ft["_supplies"] = ft["shipping_supply_cost_eur"].fillna(0.0)
        ft["_rap"] = (ft["source_cout"] == "facture_rapprochee").astype(int)
        pkg_by_order = (
            ft.groupby("order_id", as_index=False)
            .agg(
                outbound_backend=("_backend", "sum"),
                outbound_retenu=("_retenu", "sum"),
                duties_pkg=("_duties", "sum"),
                supplies_pkg=("_supplies", "sum"),
                n_colis=("id_package", "count"),
                n_colis_rapproches=("_rap", "sum"),
            )
        )

        tache1 = {
            "fichiers_presents": True,
            "arretee": False,
            "regle_m": REGLE_RETENU_M.strip(),
            "fichiers": [str(p) for p in INVOICE_FILES],
            "n_lignes_facture_valides": int(len(inv)),
            "n_factures_resolues": n_resolues,
            "n_factures_non_resolues": n_non_resolues,
            "sum_shipping_cost_eur": sum_backend,
            "sum_cout_transport_retenu": sum_retenu,
            "ecart_absolu_eur": ecart_abs,
            "ecart_pct_vs_backend": ecart_pct,
            "n_colis": n_colis,
            "n_colis_facture_rapprochee": n_rapproches,
            "n_colis_backend_seul": n_backend_seul,
            "n_colis_aucun": n_aucun,
            "ecart_sur_colis_rapproches_eur": delta_rap,
        }

    # ------------------------------------------------------------------
    # Chargement commandes + marge (avec outbound retenu si dispo)
    # ------------------------------------------------------------------
    print("\nChargement customer_order + calcul marge...")
    cols = [
        "id", "state", "source",
        "order_amount_eur", "shipping_fee_eur", "product_cost_eur",
        "inbound_transportation_cost_eur", "marketplace_fees_eur",
        "returns_and_refunds_eur", "total_generic_costs_eur",
    ]
    orders = pd.read_csv(BACKEND / "customer_order.csv", usecols=cols, low_memory=False)
    orders["id"] = pd.to_numeric(orders["id"], errors="coerce").astype("Int64")
    for c in cols:
        if c not in ("id", "state", "source"):
            orders[c] = pd.to_numeric(orders[c], errors="coerce").fillna(0.0)
    orders["state"] = orders["state"].astype(str).fillna("")
    orders["canal"] = orders["source"].map(canal)

    if pkg_by_order is None:
        # Fallback prototype : agregat package backend only
        pkg = pd.read_csv(
            BACKEND / "package.csv",
            usecols=["id", "order_id", "shipping_cost_eur", "duties_taxes_eur", "shipping_supply_cost_eur"],
            low_memory=False,
        )
        for c in ("shipping_cost_eur", "duties_taxes_eur", "shipping_supply_cost_eur"):
            pkg[c] = pd.to_numeric(pkg[c], errors="coerce").fillna(0.0)
        pkg["order_id"] = pd.to_numeric(pkg["order_id"], errors="coerce").astype("Int64")
        pkg_by_order = (
            pkg.groupby("order_id", as_index=False)
            .agg(
                outbound_backend=("shipping_cost_eur", "sum"),
                outbound_retenu=("shipping_cost_eur", "sum"),
                duties_pkg=("duties_taxes_eur", "sum"),
                supplies_pkg=("shipping_supply_cost_eur", "sum"),
            )
        )

    m = orders.merge(pkg_by_order, how="left", left_on="id", right_on="order_id", validate="one_to_one")
    for c in ("outbound_backend", "outbound_retenu", "duties_pkg", "supplies_pkg"):
        if c in m.columns:
            m[c] = m[c].fillna(0.0)
        else:
            m[c] = 0.0

    cancelled = m["state"] == "CANCELLED"
    m["ca_ht_net"] = np.where(cancelled, 0.0, m["order_amount_eur"])
    m["frais_port_net"] = np.where(cancelled, 0.0, m["shipping_fee_eur"])
    m["cout_achat"] = m["product_cost_eur"]
    m["cout_amont"] = m["inbound_transportation_cost_eur"]
    m["douanes"] = m["duties_pkg"]
    m["commissions"] = m["marketplace_fees_eur"]
    m["fournitures"] = m["supplies_pkg"]
    m["retours"] = m["returns_and_refunds_eur"]
    m["generiques"] = m["total_generic_costs_eur"]
    m["revenu"] = m["ca_ht_net"] + m["frais_port_net"]  # denom. taux marge

    def marge_avec(outbound: pd.Series) -> pd.Series:
        return (
            m["ca_ht_net"] + m["frais_port_net"]
            - m["cout_achat"] - m["cout_amont"] - outbound
            - m["douanes"] - m["commissions"] - m["fournitures"]
            - m["retours"] - m["generiques"]
        )

    m["marge_backend"] = marge_avec(m["outbound_backend"])
    m["marge_retenu"] = marge_avec(m["outbound_retenu"])
    m["outbound"] = m["outbound_retenu"] if use_retenu else m["outbound_backend"]
    m["marge"] = m["marge_retenu"] if use_retenu else m["marge_backend"]

    n_loss_backend = int((m["marge_backend"] < 0).sum())
    n_loss_retenu = int((m["marge_retenu"] < 0).sum())
    pertes_backend = float(m.loc[m["marge_backend"] < 0, "marge_backend"].sum())
    pertes_retenu = float(m.loc[m["marge_retenu"] < 0, "marge_retenu"].sum())

    if use_retenu:
        print("\n--- Impact sur les deficitaires (meme perimetre) ---")
        print(f"Nb deficitaires (outbound backend) : {n_loss_backend:,}".replace(",", " "))
        print(f"Nb deficitaires (outbound retenu)  : {n_loss_retenu:,}".replace(",", " "))
        print(f"Delta nb                           : {n_loss_retenu - n_loss_backend:+,}".replace(",", " "))
        print(f"Pertes (backend)                   : {money(pertes_backend)}")
        print(f"Pertes (retenu)                    : {money(pertes_retenu)}")
        print(f"Delta pertes                       : {money(pertes_retenu - pertes_backend)}")
        tache1.update(
            {
                "n_deficitaires_outbound_backend": n_loss_backend,
                "n_deficitaires_outbound_retenu": n_loss_retenu,
                "delta_n_deficitaires": n_loss_retenu - n_loss_backend,
                "pertes_backend_eur": pertes_backend,
                "pertes_retenu_eur": pertes_retenu,
                "delta_pertes_eur": pertes_retenu - pertes_backend,
                "marge_globale_backend_eur": float(m["marge_backend"].sum()),
                "marge_globale_retenu_eur": float(m["marge_retenu"].sum()),
            }
        )

    # ==================================================================
    # TACHE 2 — Poste basculant
    # ==================================================================
    print("\n" + "=" * 72)
    print(f"TACHE 2 — Poste basculant (outbound = {outbound_col_note})")
    print("=" * 72)

    loss_mask = m["marge"] < 0
    ok_mask = m["marge"] >= 0
    loss = m.loc[loss_mask].copy()
    ok = m.loc[ok_mask].copy()

    # Mediane du ratio poste/CA sur non-deficitaires, CA > 0, par canal
    # CA = ca_ht_net (chiffre d'affaires commande net annulation)
    median_ref: dict[tuple[str, str], float] = {}
    for canal_name, g in ok.groupby("canal"):
        g_pos = g[g["ca_ht_net"] > 0]
        for label, col in COST_POSTES:
            if len(g_pos) == 0:
                median_ref[(canal_name, col)] = 0.0
            else:
                ratios = g_pos[col] / g_pos["ca_ht_net"]
                median_ref[(canal_name, col)] = float(ratios.median())

    # Vectorise : pour chaque poste, new_marge = marge + (poste - med_ratio*CA)
    loss_idx = loss.index.to_numpy()
    ca = loss["ca_ht_net"].to_numpy(dtype=float)
    marge0 = loss["marge"].to_numpy(dtype=float)
    canals = loss["canal"].to_numpy()

    # Matrice (n_loss, n_postes) des ameliorations si flip positif, sinon -inf
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
    best_j = np.argmax(amelio, axis=1)  # parmi -inf, argmax ok si au moins un flip
    labels = np.array([c[0] for c in COST_POSTES], dtype=object)
    poste_b = np.where(any_flip, labels[best_j], STRUCTUREL)

    attributed = pd.DataFrame(
        {
            "id": loss["id"].astype(int).to_numpy(),
            "canal": canals,
            "marge": marge0,
            "poste_basculant": poste_b,
        }
    )
    assert len(attributed) == len(loss), "des deficitaires non classes"
    assert attributed["poste_basculant"].isna().sum() == 0

    pertes_total = float(attributed["marge"].sum())

    # Repartition globale
    tl2 = []
    for label in [c[0] for c in COST_POSTES] + [STRUCTUREL]:
        sub = attributed[attributed["poste_basculant"] == label]
        tl2.append(
            {
                "poste_basculant": label,
                "n_commandes": int(len(sub)),
                "part_n": float(len(sub) / len(attributed)) if len(attributed) else 0.0,
                "somme_pertes_eur": float(sub["marge"].sum()),
                "part_pertes": float(sub["marge"].sum() / pertes_total) if pertes_total != 0 else 0.0,
            }
        )
    tl2.sort(key=lambda r: r["n_commandes"], reverse=True)

    somme_repartie = sum(r["somme_pertes_eur"] for r in tl2)
    controle_ok = abs(somme_repartie - pertes_total) <= 0.01
    n_classes = int(len(attributed))
    n_deficit = int(loss_mask.sum())

    print(f"Nb deficitaires analyses : {n_deficit:,}".replace(",", " "))
    print(f"Pertes totales           : {money(pertes_total)}")
    print(f"Somme repartie           : {money(somme_repartie)}")
    print(f"Controle somme OK        : {controle_ok}")
    print(f"Tous classes             : {n_classes == n_deficit}")
    print(
        f"\n{'poste basculant':<32} {'n_cmd':>10} {'part n':>10} {'pertes EUR':>16} {'part pertes':>12}"
    )
    for r in tl2:
        if r["n_commandes"] == 0:
            continue
        print(
            f"{r['poste_basculant']:<32} {r['n_commandes']:>10} "
            f"{pct(r['part_n']):>10} {money(r['somme_pertes_eur']):>16} "
            f"{pct(r['part_pertes']):>12}"
        )

    # Croisement canal x poste
    cross = (
        attributed.groupby(["canal", "poste_basculant"], as_index=False)
        .agg(n_commandes=("id", "count"), somme_pertes_eur=("marge", "sum"))
        .sort_values(["canal", "n_commandes"], ascending=[True, False])
    )
    print("\n--- Croisement canal x poste basculant ---")
    for canal_name, g in cross.groupby("canal"):
        print(f"\n[{canal_name}]")
        for _, r in g.iterrows():
            print(
                f"  {r['poste_basculant']:<30} n={int(r['n_commandes']):>7}  "
                f"pertes={money(float(r['somme_pertes_eur']))}"
            )

    # Mediane de reference (apercu)
    med_preview = []
    for canal_name in sorted({k[0] for k in median_ref}):
        for label, col in COST_POSTES:
            med_preview.append(
                {
                    "canal": canal_name,
                    "poste": label,
                    "mediane_ratio_poste_sur_ca": median_ref[(canal_name, col)],
                    "n_ref_non_def_ca_gt0": int(
                        ((ok["canal"] == canal_name) & (ok["ca_ht_net"] > 0)).sum()
                    ),
                }
            )

    results = {
        "tache1": tache1,
        "tache2": {
            "outbound_utilise": outbound_col_note,
            "n_deficitaires": n_deficit,
            "pertes_totales_eur": pertes_total,
            "somme_repartie_eur": somme_repartie,
            "controle_somme_ok": controle_ok,
            "tous_classes": n_classes == n_deficit,
            "n_non_classes": n_deficit - n_classes,
            "repartition": tl2,
            "croisement_canal": cross.to_dict(orient="records"),
            "medianes_reference": med_preview,
            "definition_ca": "ca_ht_net = order_amount_eur si state<>CANCELLED sinon 0",
            "definition_simulation": (
                "poste_simule = mediane(poste/CA | non-deficitaires meme canal, CA>0) * CA ; "
                "new_marge = marge + (poste_actuel - poste_simule) ; "
                "basculant = poste seul qui donne new_marge>0 avec max amelioration ; "
                "sinon structurellement deficitaire"
            ),
        },
    }

    out_json = OUT_DIR / "results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON : {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
