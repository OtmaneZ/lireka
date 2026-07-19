#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page 11 — Loss analysis : faisabilité d'une colonne marge_brute_commande.

LECTURE SEULE. Aucune modification du modèle (.tmdl / DAX / M).
Chaque chiffre imprimé est issu d'un calcul exécuté sur les CSV.

Sources :
  - Power_BI_Datawarehouse/Données_Backend/customer_order.csv
  - Power_BI_Datawarehouse/Données_Backend/package.csv
  - Formule [Marge Brute] dans _Mesures.tmdl (10 postes)
  - Colonnes / M dans fact_commandes.tmdl, fact_transport.tmdl, expressions.tmdl

Formule DAX répliquée (grain commande) :
  CA HT Net Annulation                          (ca_ht si state <> CANCELLED sinon 0)
  + Frais Port Encaissés hors CANCELLED         (idem)
  - Coût Achat Total
  - Coût Transport Amont
  - Coût Transport Outbound (Retenu)            ← SUM package.shipping_cost_eur
                                                  (proxy backend ; le modèle PBI
                                                   utilise cout_transport_retenu =
                                                   facture si matchée sinon estimé)
  - Douanes Taxes                               ← SUM package.duties_taxes_eur
  - Commissions Marketplace
  - Fournitures Expédition                      ← SUM package.shipping_supply_cost_eur
  - Retours Remboursements
  - Coûts Génériques
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "Power_BI_Datawarehouse" / "Données_Backend"
CO_PATH = BACKEND / "customer_order.csv"
PKG_PATH = BACKEND / "package.csv"
OUT_DIR = Path(__file__).resolve().parent / "page11_marge_commande_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOL_EUR = 0.01  # tolérance bouclage

# ---------------------------------------------------------------------------
# TÂCHE 1 — Grain documenté (sources modèle, lecture seule)
# ---------------------------------------------------------------------------
# Chaque poste cite : mesure DAX, colonne modèle, table, grain, code M producteur.
GRAIN_POSTES = [
    {
        "poste": "CA HT Net Annulation",
        "mesure": "CA HT Net Annulation = CALCULATE([CA Total HT], fact_commandes[state] <> \"CANCELLED\")",
        "colonne_modele": "fact_commandes[ca_ht]  (filtre state à la mesure)",
        "colonne_csv": "order_amount_eur",
        "table": "fact_commandes",
        "grain": "commande",
        "pre_agregation": "non",
        "code_m": (
            'stg_customer_order : Csv.Document(...\\customer_order.csv) + '
            'TransformColumnTypes({order_amount_eur, type number}); '
            'fact_commandes : RenameColumns({"order_amount_eur","ca_ht"})'
        ),
    },
    {
        "poste": "Frais Port Encaissés (hors CANCELLED)",
        "mesure": "CALCULATE([Frais Port Encaissés], fact_commandes[state] <> \"CANCELLED\")",
        "colonne_modele": "fact_commandes[frais_port_encaisse]",
        "colonne_csv": "shipping_fee_eur",
        "table": "fact_commandes",
        "grain": "commande",
        "pre_agregation": "non",
        "code_m": (
            'stg_customer_order : TransformColumnTypes({shipping_fee_eur, type number}); '
            'fact_commandes : RenameColumns({"shipping_fee_eur","frais_port_encaisse"}). '
            'Le filtre state <> CANCELLED est dans la mesure, pas dans la colonne.'
        ),
    },
    {
        "poste": "Coût Achat Total",
        "mesure": "Coût Achat Total = SUM(fact_commandes[cout_achat])",
        "colonne_modele": "fact_commandes[cout_achat]",
        "colonne_csv": "product_cost_eur",
        "table": "fact_commandes",
        "grain": "commande",
        "pre_agregation": "non",
        "code_m": (
            'stg_customer_order : TransformColumnTypes({product_cost_eur, type number}); '
            'fact_commandes : RenameColumns({"product_cost_eur","cout_achat"})'
        ),
    },
    {
        "poste": "Coût Transport Amont",
        "mesure": "Coût Transport Amont = SUM(fact_commandes[cout_transport_amont])",
        "colonne_modele": "fact_commandes[cout_transport_amont]",
        "colonne_csv": "inbound_transportation_cost_eur",
        "table": "fact_commandes",
        "grain": "commande",
        "pre_agregation": "non",
        "code_m": (
            'fact_commandes : TransformColumnTypes({inbound_transportation_cost_eur, type number}); '
            'RenameColumns({"inbound_transportation_cost_eur","cout_transport_amont"})'
        ),
    },
    {
        "poste": "Coût Transport Outbound (Retenu)",
        "mesure": "Coût Transport Outbound (Retenu) = SUM(fact_transport[cout_transport_retenu])",
        "colonne_modele": "fact_transport[cout_transport_retenu]",
        "colonne_csv": "package.shipping_cost_eur (+ facture si matchée en PBI)",
        "table": "fact_transport",
        "grain": "colis",
        "pre_agregation": "oui",
        "code_m": (
            'stg_package : Csv.Document(...\\package.csv), shipping_cost_eur typé; '
            'fact_transport : RenameColumns({"shipping_cost_eur","cout_transport"}); '
            'NestedJoin factures -> cout_transport_facture; '
            'AddColumn cout_transport_retenu = '
            'if cout_transport_facture <> null then facture else cout_transport'
        ),
    },
    {
        "poste": "Douanes Taxes",
        "mesure": "Douanes Taxes = SUM(fact_transport[duties_taxes_eur])",
        "colonne_modele": "fact_transport[duties_taxes_eur]",
        "colonne_csv": "package.duties_taxes_eur",
        "table": "fact_transport",
        "grain": "colis",
        "pre_agregation": "oui",
        "code_m": (
            'stg_package : TransformColumnTypes({duties_taxes_eur, type number}); '
            'fact_transport : SelectColumns(..., "duties_taxes_eur", ...)'
        ),
    },
    {
        "poste": "Commissions Marketplace",
        "mesure": "Commissions Marketplace = SUM(fact_commandes[commissions_marketplace])",
        "colonne_modele": "fact_commandes[commissions_marketplace]",
        "colonne_csv": "marketplace_fees_eur",
        "table": "fact_commandes",
        "grain": "commande",
        "pre_agregation": "non",
        "code_m": (
            'fact_commandes : TransformColumnTypes({marketplace_fees_eur, type number}); '
            'RenameColumns({"marketplace_fees_eur","commissions_marketplace"})'
        ),
    },
    {
        "poste": "Fournitures Expédition",
        "mesure": "Fournitures Expédition = SUM(fact_transport[shipping_supply_cost_eur])",
        "colonne_modele": "fact_transport[shipping_supply_cost_eur]",
        "colonne_csv": "package.shipping_supply_cost_eur",
        "table": "fact_transport",
        "grain": "colis",
        "pre_agregation": "oui",
        "code_m": (
            'stg_package : TransformColumnTypes({shipping_supply_cost_eur, type number}); '
            'fact_transport : SelectColumns(..., "shipping_supply_cost_eur", ...)'
        ),
    },
    {
        "poste": "Retours Remboursements",
        "mesure": "Retours Remboursements = SUM(fact_commandes[retours_remboursements])",
        "colonne_modele": "fact_commandes[retours_remboursements]",
        "colonne_csv": (
            "customer_order_item.returns_and_refunds_cost_eur "
            "(egal a customer_order.returns_and_refunds_eur au grain commande)"
        ),
        "table": "fact_commandes (via stg_couts_bloc5_commande / item)",
        "grain": "article -> pre-agrege commande dans le modele",
        "pre_agregation": "oui (deja faite dans stg_couts_bloc5_commande)",
        "code_m": (
            'stg_couts_bloc5_commande : Table.Group(stg_Commande_Items, {"order_id"}, '
            '{{"retours_remboursements", each List.Sum(...[returns_and_refunds_cost_eur])}}); '
            'fact_commandes : NestedJoin id_commande=order_id, ReplaceValue null->0'
        ),
    },
    {
        "poste": "Coûts Génériques",
        "mesure": "Coûts Génériques = SUM(fact_commandes[couts_generiques])",
        "colonne_modele": "fact_commandes[couts_generiques]",
        "colonne_csv": (
            "customer_order_item.generic_costs_eur "
            "(egal a customer_order.total_generic_costs_eur au grain commande)"
        ),
        "table": "fact_commandes (via stg_couts_bloc5_commande / item)",
        "grain": "article -> pre-agrege commande dans le modele",
        "pre_agregation": "oui (deja faite dans stg_couts_bloc5_commande)",
        "code_m": (
            'stg_couts_bloc5_commande : Table.Group(..., '
            '{{"couts_generiques", each List.Sum(...[generic_costs_eur])}}); '
            'fact_commandes : NestedJoin + ReplaceValue null->0'
        ),
    },
]


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def money(x: float) -> str:
    return f"{x:,.2f} EUR".replace(",", " ").replace(".", ",")


def pct(x: float) -> str:
    return f"{100.0 * x:,.2f} pct".replace(",", " ").replace(".", ",")


def load_orders() -> pd.DataFrame:
    cols = [
        "id",
        "state",
        "order_amount_eur",
        "shipping_fee_eur",
        "product_cost_eur",
        "inbound_transportation_cost_eur",
        "marketplace_fees_eur",
        "returns_and_refunds_eur",
        "total_generic_costs_eur",
        "total_shipping_cost_to_delivery_country_eur",
        "duties_and_taxes_eur",
        "total_shipping_supplies_eur",
    ]
    print(f"Lecture {CO_PATH.name}...")
    df = pd.read_csv(CO_PATH, usecols=cols, low_memory=False)
    for c in cols:
        if c not in ("id", "state"):
            df[c] = num(df[c]).fillna(0.0)
    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["state"] = df["state"].astype(str).fillna("")
    return df


def load_package_agg() -> tuple[pd.DataFrame, dict]:
    """Pré-agrège les postes grain colis par order_id. Retourne aussi contrôles unicité."""
    cols = [
        "id",
        "order_id",
        "shipping_cost_eur",
        "shipping_supply_cost_eur",
        "duties_taxes_eur",
    ]
    print(f"Lecture {PKG_PATH.name}...")
    pkg = pd.read_csv(PKG_PATH, usecols=cols, low_memory=False)
    for c in ("shipping_cost_eur", "shipping_supply_cost_eur", "duties_taxes_eur"):
        pkg[c] = num(pkg[c]).fillna(0.0)
    pkg["id"] = pd.to_numeric(pkg["id"], errors="coerce")
    pkg["order_id"] = pd.to_numeric(pkg["order_id"], errors="coerce")

    n_pkg = len(pkg)
    n_pkg_id_dup = int(pkg["id"].duplicated().sum()) if pkg["id"].notna().any() else 0
    n_null_order = int(pkg["order_id"].isna().sum())

    # Agrégation SUM par order_id (clé de jointure vers fact_commandes)
    agg = (
        pkg.dropna(subset=["order_id"])
        .groupby("order_id", as_index=False)
        .agg(
            outbound_pkg=("shipping_cost_eur", "sum"),
            duties_pkg=("duties_taxes_eur", "sum"),
            supplies_pkg=("shipping_supply_cost_eur", "sum"),
            n_colis=("id", "count"),
        )
    )
    agg["order_id"] = agg["order_id"].astype("Int64")
    # Après GroupBy, order_id est unique par construction
    n_agg = len(agg)
    n_agg_dup = int(agg["order_id"].duplicated().sum())

    meta = {
        "n_package_rows": n_pkg,
        "n_package_id_duplicates": n_pkg_id_dup,
        "n_package_null_order_id": n_null_order,
        "n_order_id_apres_groupby": n_agg,
        "n_order_id_dup_apres_groupby": n_agg_dup,
        "cle_apres_groupby_unique": n_agg_dup == 0,
        "sum_shipping_cost_eur": float(pkg["shipping_cost_eur"].sum()),
        "sum_duties_taxes_eur": float(pkg["duties_taxes_eur"].sum()),
        "sum_shipping_supply_cost_eur": float(pkg["shipping_supply_cost_eur"].sum()),
    }
    return agg, meta


def propose_tranches(panier: pd.Series) -> list[float]:
    """Tranches lisibles dérivées des quantiles réels (montants > 0)."""
    pos = panier[panier > 0]
    qs = pos.quantile([0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]).tolist()

    # Arrondis « lisibles » (1 / 5 / 10 / 25 / 50 / 100 selon l'échelle)
    def nice(x: float) -> float:
        if x < 5:
            return round(x * 2) / 2  # 0.5 €
        if x < 20:
            return float(round(x))  # 1 €
        if x < 50:
            return float(5 * round(x / 5))
        if x < 100:
            return float(10 * round(x / 10))
        if x < 250:
            return float(25 * round(x / 25))
        if x < 500:
            return float(50 * round(x / 50))
        return float(100 * round(x / 100))

    edges = [0.0]
    for q in qs:
        e = nice(float(q))
        if e > edges[-1]:
            edges.append(e)
    # borne haute ouverte
    return edges


def label_tranche(lo: float, hi: float | None) -> str:
    if hi is None:
        return f">= {lo:,.0f} EUR".replace(",", " ")
    if lo == 0:
        return f"[0 ; {hi:,.0f} EUR[".replace(",", " ")
    return f"[{lo:,.0f} ; {hi:,.0f} EUR[".replace(",", " ")


def main() -> int:
    # Console Windows cp1252 : forcer UTF-8 si possible
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    co_mtime = datetime.fromtimestamp(CO_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    pkg_mtime = datetime.fromtimestamp(PKG_PATH.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"customer_order.csv mtime = {co_mtime}")
    print(f"package.csv         mtime = {pkg_mtime}")
    print(f"(analyse executee le {datetime.now().strftime('%Y-%m-%d')} - entrepot courant)\n")

    orders = load_orders()
    pkg_agg, pkg_meta = load_package_agg()

    # Unicité côté commandes
    n_orders = len(orders)
    n_id_null = int(orders["id"].isna().sum())
    n_id_dup = int(orders["id"].duplicated().sum())
    assert n_id_dup == 0, f"id_commande non unique: {n_id_dup} doublons"

    # Merge left : commandes ← agrégat colis (clé order_id unique du bon côté)
    merged = orders.merge(
        pkg_agg,
        how="left",
        left_on="id",
        right_on="order_id",
        validate="one_to_one",  # échoue si duplication
        indicator=True,
    )
    for c in ("outbound_pkg", "duties_pkg", "supplies_pkg", "n_colis"):
        merged[c] = merged[c].fillna(0.0)

    n_cmd_sans_colis = int((merged["_merge"] == "left_only").sum())
    n_colis_orphelins = int(pkg_meta["n_order_id_apres_groupby"] - (merged["_merge"] == "both").sum())

    # --- Postes ligne (filtre CANCELLED reproduit au niveau ligne) ---
    cancelled = merged["state"] == "CANCELLED"
    merged["ca_ht_net"] = np.where(cancelled, 0.0, merged["order_amount_eur"])
    merged["frais_port_net"] = np.where(cancelled, 0.0, merged["shipping_fee_eur"])
    merged["cout_achat"] = merged["product_cost_eur"]
    merged["cout_amont"] = merged["inbound_transportation_cost_eur"]
    merged["outbound"] = merged["outbound_pkg"]  # proxy shipping_cost_eur (sans facture)
    merged["douanes"] = merged["duties_pkg"]
    merged["commissions"] = merged["marketplace_fees_eur"]
    merged["fournitures"] = merged["supplies_pkg"]
    merged["retours"] = merged["returns_and_refunds_eur"]
    merged["generiques"] = merged["total_generic_costs_eur"]

    merged["marge_brute_commande"] = (
        merged["ca_ht_net"]
        + merged["frais_port_net"]
        - merged["cout_achat"]
        - merged["cout_amont"]
        - merged["outbound"]
        - merged["douanes"]
        - merged["commissions"]
        - merged["fournitures"]
        - merged["retours"]
        - merged["generiques"]
    )

    # =====================================================================
    # BOUCLAGE : somme par commande == marge globale (mêmes postes)
    # =====================================================================
    postes_globaux = {
        "ca_ht_net": float(merged["ca_ht_net"].sum()),
        "frais_port_net": float(merged["frais_port_net"].sum()),
        "cout_achat": float(merged["cout_achat"].sum()),
        "cout_amont": float(merged["cout_amont"].sum()),
        "outbound": float(merged["outbound"].sum()),
        "douanes": float(merged["douanes"].sum()),
        "commissions": float(merged["commissions"].sum()),
        "fournitures": float(merged["fournitures"].sum()),
        "retours": float(merged["retours"].sum()),
        "generiques": float(merged["generiques"].sum()),
    }
    marge_globale = (
        postes_globaux["ca_ht_net"]
        + postes_globaux["frais_port_net"]
        - postes_globaux["cout_achat"]
        - postes_globaux["cout_amont"]
        - postes_globaux["outbound"]
        - postes_globaux["douanes"]
        - postes_globaux["commissions"]
        - postes_globaux["fournitures"]
        - postes_globaux["retours"]
        - postes_globaux["generiques"]
    )
    somme_marges = float(merged["marge_brute_commande"].sum())
    ecart_bouclage = somme_marges - marge_globale

    # Diagnostic poste par poste si écart (somme ligne vs agrégat global — doit être 0)
    ecarts_poste = {
        k: float(merged[k].sum() - postes_globaux[k]) for k in postes_globaux
    }

    # Contrôle croisé package brut vs merge (orphelins)
    ecart_outbound_pkg = postes_globaux["outbound"] - pkg_meta["sum_shipping_cost_eur"]
    # (négatif si des colis ont un order_id absent de customer_order)

    # =====================================================================
    # TL-1 — commandes déficitaires
    # =====================================================================
    loss = merged[merged["marge_brute_commande"] < 0]
    n_loss = len(loss)
    pertes = float(loss["marge_brute_commande"].sum())  # négatif
    part_cmd = n_loss / n_orders if n_orders else 0.0
    part_marge = (pertes / marge_globale) if marge_globale != 0 else float("nan")

    # =====================================================================
    # TL-2 — poste de coût dominant parmi les déficitaires
    # =====================================================================
    cost_cols = [
        ("Coût Achat", "cout_achat"),
        ("Transport Amont", "cout_amont"),
        ("Outbound", "outbound"),
        ("Douanes Taxes", "douanes"),
        ("Commissions Marketplace", "commissions"),
        ("Fournitures Expédition", "fournitures"),
        ("Retours Remboursements", "retours"),
        ("Coûts Génériques", "generiques"),
    ]
    cost_matrix = loss[[c for _, c in cost_cols]].to_numpy()
    # argmax du coût ; en cas d'égalité, premier poste dans l'ordre ci-dessus
    dominant_idx = np.argmax(cost_matrix, axis=1)
    loss = loss.copy()
    loss["poste_dominant"] = [cost_cols[i][0] for i in dominant_idx]
    loss["cout_dominant_eur"] = cost_matrix[np.arange(len(loss)), dominant_idx]

    tl2_rows = []
    for name, col in cost_cols:
        sub = loss[loss["poste_dominant"] == name]
        tl2_rows.append(
            {
                "poste_dominant": name,
                "n_commandes": int(len(sub)),
                "part_cmd_deficitaires": float(len(sub) / n_loss) if n_loss else 0.0,
                "somme_pertes_eur": float(sub["marge_brute_commande"].sum()),
                "somme_cout_dominant_eur": float(sub[col].sum()),
            }
        )
    tl2_rows.sort(key=lambda r: r["n_commandes"], reverse=True)

    # =====================================================================
    # TL-3 — marge par tranche de panier (distribution réelle)
    # =====================================================================
    # Panier = order_amount_eur brut (montant commande). CA rapporté = ca_ht_net.
    panier = merged["order_amount_eur"]
    edges = propose_tranches(panier)
    # bins: [e0,e1), [e1,e2), ... [e_last, +inf)
    bins = edges + [np.inf]
    labels = [
        label_tranche(bins[i], None if np.isinf(bins[i + 1]) else bins[i + 1])
        for i in range(len(bins) - 1)
    ]
    merged["tranche"] = pd.cut(
        panier, bins=bins, labels=labels, right=False, include_lowest=True
    )

    tl3_rows = []
    quantiles_ref = {
        f"p{int(q*100)}": float(panier[panier > 0].quantile(q))
        for q in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
    }
    for lab in labels:
        sub = merged[merged["tranche"] == lab]
        ca = float(sub["ca_ht_net"].sum())
        mb = float(sub["marge_brute_commande"].sum())
        tl3_rows.append(
            {
                "tranche": lab,
                "n_commandes": int(len(sub)),
                "ca_ht_net_eur": ca,
                "marge_brute_eur": mb,
                "taux_marge": (mb / ca) if ca != 0 else None,
            }
        )

    # =====================================================================
    # TÂCHE 4 — volumétrie / cardinalité
    # =====================================================================
    # Cardinalité exacte (float64) et arrondie au centime (usage métier €)
    n_distinct_exact = int(merged["marge_brute_commande"].nunique(dropna=False))
    n_distinct_centime = int(
        merged["marge_brute_commande"].round(2).nunique(dropna=False)
    )
    # Taille non compressée d'une colonne Double = 8 octets / ligne
    size_uncompressed_bytes = n_orders * 8
    # Estimation VertiPaq simplifiée (dictionnaire + index) :
    #   dict ≈ n_distinct * 8 ; données ≈ n_rows * ceil(log2(n_distinct))/8
    import math

    bits = max(1, math.ceil(math.log2(max(n_distinct_centime, 2))))
    size_vertipaq_est_bytes = n_distinct_centime * 8 + n_orders * bits / 8

    # =====================================================================
    # Sortie structurée
    # =====================================================================
    results = {
        "meta": {
            "customer_order_mtime": co_mtime,
            "package_mtime": pkg_mtime,
            "n_commandes": n_orders,
            "n_id_null": n_id_null,
            "n_id_duplicates": n_id_dup,
            "package_meta": pkg_meta,
            "merge": {
                "validate": "one_to_one (id ↔ order_id agrégé)",
                "n_commandes_sans_colis": n_cmd_sans_colis,
                "n_order_id_package_absents_de_commandes": n_colis_orphelins,
                "ecart_sum_outbound_merge_vs_pkg_brut_eur": ecart_outbound_pkg,
            },
            "note_outbound": (
                "Prototype CSV : outbound = SUM(package.shipping_cost_eur) par order_id. "
                "Le modèle PBI utilise cout_transport_retenu (facture rapprochée si "
                "disponible). Bouclage interne CSV garanti ; écart possible vs [Marge Brute] Desktop."
            ),
        },
        "tache1_grains": GRAIN_POSTES,
        "tache2_faisabilite": {
            "colonne_calculee_faisable": True,
            "reponse_binaire": "OUI",
            "detail_merge": {
                "table_source": "package.csv → agrégat puis merge vers fact_commandes",
                "cle": "fact_commandes[id_commande] = package.order_id (après GroupBy)",
                "agregation": (
                    "Table.Group / groupby SUM : shipping_cost_eur, duties_taxes_eur, "
                    "shipping_supply_cost_eur"
                ),
                "unicite_cote_droit_apres_groupby": pkg_meta["cle_apres_groupby_unique"],
                "unicite_cote_gauche_id_commande": n_id_dup == 0,
                "risque_duplication_lignes": (
                    "Aucun si GroupBy order_id avant NestedJoin LeftOuter. "
                    "Sans GroupBy, jointure N colis → 1 commande multiplierait les lignes "
                    "fact_commandes (interdit)."
                ),
                "bloc5": (
                    "Déjà pré-agrégé dans stg_couts_bloc5_commande (item → order_id) "
                    "et joint à fact_commandes. Pas de merge supplémentaire nécessaire "
                    "si on réutilise retours_remboursements / couts_generiques."
                ),
                "filtre_cancelled_frais_port_et_ca": (
                    "Une colonne calculee ne porte pas CALCULATE(...). "
                    "Reproduire au niveau ligne : "
                    "ca_ht_net = if [state] <> \"CANCELLED\" then [ca_ht] else 0 ; "
                    "frais_port_net = if [state] <> \"CANCELLED\" then [frais_port_encaisse] else 0 ; "
                    "puis marge = ca_ht_net + frais_port_net - couts..."
                ),
                "outbound_retenu_en_pq": (
                    "Pour coller au DAX : pré-agréger fact_transport[cout_transport_retenu] "
                    "(déjà calculé en M avec factures) par order_id, puis merge. "
                    "Ne pas se contenter de total_shipping_cost_to_delivery_country_eur "
                    "de customer_order (estimation order-grain, autre poste)."
                ),
            },
        },
        "bouclage": {
            "marge_globale_eur": marge_globale,
            "somme_marges_par_commande_eur": somme_marges,
            "ecart_eur": ecart_bouclage,
            "bouclage_ok": abs(ecart_bouclage) <= TOL_EUR,
            "postes_globaux_eur": postes_globaux,
            "ecarts_poste_eur": ecarts_poste,
            "poste_responsable_si_ecart": (
                None
                if abs(ecart_bouclage) <= TOL_EUR
                else max(ecarts_poste, key=lambda k: abs(ecarts_poste[k]))
            ),
        },
        "tl1": {
            "n_commandes_marge_negative": n_loss,
            "part_du_total_commandes": part_cmd,
            "somme_pertes_eur": pertes,
            "part_de_la_marge_brute_globale": part_marge,
            "marge_brute_globale_eur": marge_globale,
        },
        "tl2": tl2_rows,
        "tl3": {
            "quantiles_panier_order_amount_eur_gt0": quantiles_ref,
            "bornes_utilisees_eur": edges,
            "tranches": tl3_rows,
        },
        "tache4_volumetrie": {
            "n_commandes": n_orders,
            "n_valeurs_distinctes_marge_float64": n_distinct_exact,
            "n_valeurs_distinctes_marge_arrondi_centime": n_distinct_centime,
            "taille_non_compressee_bytes": size_uncompressed_bytes,
            "taille_non_compressee_mio": round(size_uncompressed_bytes / (1024**2), 3),
            "taille_vertipaq_estimee_bytes": round(size_vertipaq_est_bytes, 1),
            "taille_vertipaq_estimee_mio": round(size_vertipaq_est_bytes / (1024**2), 3),
            "formule_estimation": (
                "dict≈n_distinct_centime*8 + data≈n_rows*ceil(log2(n_distinct))/8"
            ),
        },
    }

    # ---------- Impression ----------
    print("=" * 72)
    print("TÂCHE 1 — Grain de chaque poste")
    print("=" * 72)
    print(
        f"{'poste':<40} {'table':<18} {'grain':<12} {'pré-agrég.':<10}"
    )
    print("-" * 72)
    for g in GRAIN_POSTES:
        print(
            f"{g['poste']:<40} {g['table'].split()[0]:<18} {g['grain']:<12} {g['pre_agregation']:<10}"
        )
        print(f"  colonne modèle : {g['colonne_modele']}")
        print(f"  colonne CSV    : {g['colonne_csv']}")
        print(f"  M              : {g['code_m'][:110]}...")

    print("\n" + "=" * 72)
    print("TÂCHE 2 — Faisabilité colonne calculee")
    print("=" * 72)
    print("Réponse binaire : OUI — on peut ajouter marge_brute_commande en Power Query.")
    d = results["tache2_faisabilite"]["detail_merge"]
    print(f"Merge : {d['table_source']}")
    print(f"Clé   : {d['cle']}")
    print(f"Agg   : {d['agregation']}")
    print(f"Unicité droite après GroupBy : {d['unicite_cote_droit_apres_groupby']}")
    print(f"Unicité gauche id_commande   : {d['unicite_cote_gauche_id_commande']}")
    print(f"Risque duplication : {d['risque_duplication_lignes']}")
    print(f"Filtre CANCELLED   : {d['filtre_cancelled_frais_port_et_ca']}")
    print(f"Outbound retenu    : {d['outbound_retenu_en_pq']}")
    print(f"Commandes sans colis (left_only) : {n_cmd_sans_colis}")
    print(f"order_id package absents de CO   : {n_colis_orphelins}")
    print(f"Écart SUM outbound merge vs pkg  : {money(ecart_outbound_pkg)}")

    print("\n" + "=" * 72)
    print("BOUCLAGE")
    print("=" * 72)
    print(f"Marge brute globale (10 postes)     : {money(marge_globale)}")
    print(f"Somme marges par commande           : {money(somme_marges)}")
    print(f"Écart                               : {money(ecart_bouclage)}")
    print(f"Bouclage OK (|écart| ≤ {TOL_EUR} €) : {results['bouclage']['bouclage_ok']}")
    if not results["bouclage"]["bouclage_ok"]:
        print(f"Poste responsable                   : {results['bouclage']['poste_responsable_si_ecart']}")
    print("\nPostes globaux :")
    for k, v in postes_globaux.items():
        print(f"  {k:<22} {money(v)}")

    print("\n" + "=" * 72)
    print("TL-1 — Volume et poids des commandes déficitaires")
    print("=" * 72)
    print(f"Nb commandes marge < 0     : {n_loss:,}".replace(",", " "))
    print(f"Part du total commandes    : {pct(part_cmd)}")
    print(f"Somme des pertes           : {money(pertes)}")
    print(f"Part de la marge globale   : {pct(part_marge)}")

    print("\n" + "=" * 72)
    print("TL-2 — Poste de coût dominant (commandes déficitaires)")
    print("=" * 72)
    print(
        f"{'poste':<28} {'n_cmd':>10} {'part':>10} {'pertes €':>16} {'coût dom. €':>16}"
    )
    for r in tl2_rows:
        print(
            f"{r['poste_dominant']:<28} {r['n_commandes']:>10} "
            f"{pct(r['part_cmd_deficitaires']):>12} "
            f"{money(r['somme_pertes_eur']):>18} "
            f"{money(r['somme_cout_dominant_eur']):>18}"
        )

    print("\n" + "=" * 72)
    print("TL-3 — Marge par tranche de panier (order_amount_eur)")
    print("=" * 72)
    print("Quantiles panier > 0 :")
    for k, v in quantiles_ref.items():
        print(f"  {k}: {money(v)}")
    print(f"Bornes retenues (€) : {edges}")
    print(
        f"{'tranche':<22} {'n_cmd':>10} {'CA HT net':>16} {'Marge brute':>16} {'Taux':>10}"
    )
    for r in tl3_rows:
        tx = "n/a" if r["taux_marge"] is None else pct(r["taux_marge"])
        print(
            f"{r['tranche']:<22} {r['n_commandes']:>10,} "
            f"{money(r['ca_ht_net_eur']):>16} "
            f"{money(r['marge_brute_eur']):>16} "
            f"{tx:>10}".replace(",", " ")
        )

    print("\n" + "=" * 72)
    print("TÂCHE 4 — Volumétrie / cardinalité")
    print("=" * 72)
    v = results["tache4_volumetrie"]
    print(f"Nb commandes                         : {v['n_commandes']:,}".replace(",", " "))
    print(f"Valeurs distinctes marge (float64)   : {v['n_valeurs_distinctes_marge_float64']:,}".replace(",", " "))
    print(f"Valeurs distinctes marge (centime)   : {v['n_valeurs_distinctes_marge_arrondi_centime']:,}".replace(",", " "))
    print(f"Taille non compressée (8 o × n)      : {v['taille_non_compressee_mio']} Mio")
    print(f"Taille VertiPaq estimée              : {v['taille_vertipaq_estimee_mio']} Mio")
    print(f"Formule                              : {v['formule_estimation']}")

    out_json = OUT_DIR / "results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON écrit : {out_json}")

    out_txt = OUT_DIR / "results.txt"
    # Relire stdout n'est pas trivial ; on écrit un résumé fichier
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results["bouclage"]["bouclage_ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
