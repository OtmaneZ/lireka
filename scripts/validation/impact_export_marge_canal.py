#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impact de l'export backend courant sur la marge brute, canal par canal.
LECTURE SEULE sur le modèle. Aucune écriture .tmdl / DAX / M.

Source unique : Power_BI_Datawarehouse/Données_Backend/customer_order.csv
Logique répliquée depuis (lus sur disque) :
  - _Mesures.tmdl  : mesures [Marge Brute], [CA HT Net Annulation],
                     [Coût Achat Total], [Frais Port Encaissés], etc.
  - fact_commandes.tmdl : mapping colonnes + colonne ca_ht_reconstruit (Power Query).
  - expressions.tmdl : stg_taux_moyen_mensuel (taux FX moyen mensuel interne).
  - reconstruction-ca-marketplace.md : logique Bloc 1 (option B).

Chaque chiffre du récapitulatif est issu d'un calcul exécuté sur ce CSV.
"""

import csv
import os
import sys
from collections import defaultdict

csv.field_size_limit(sys.maxsize)

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_ORDER = os.path.join(BASE, "Power_BI_Datawarehouse", "Données_Backend", "customer_order.csv")
OUT_DIR = os.path.join(BASE, "scripts", "validation", "impact_export_marge_out")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Commentaire DAX de [Marge Brute] (cité VERBATIM depuis _Mesures.tmdl, l.262-277)
# ---------------------------------------------------------------------------
DAX_COMMENT = """\
/// MARGE BRUTE — formule confirmée par Marc Bordier (Slack, 13/07/2026 16h09).
/// Revenu = CA hors commandes annulées (règle Marc "CA=0 sur annulation", grain commande).
/// Coûts conservés sur toutes commandes y compris annulées (décision Marc : coût produit
/// + transport si après expédition). Frais de port encaissés exclus sur commandes CANCELLED
/// (1 283 € sur l'entrepôt actuel, audit 15/07/2026). Annulations partielles non ajustées.
/// Revenue (incl. shipping revenue if relevant) - COGS - Inbound transportation costs
/// - Outbound transportation costs - Duties and Taxes - Marketplace commission fees
/// - Shipping supplies - Returns/refunds - Generic costs.
measure 'Marge Brute' =
        [CA HT Net Annulation]
            + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
            - [Coût Achat Total]
            - [Coût Transport Amont]
            - [Coût Transport Outbound (Retenu)]
            - [Douanes Taxes]
            - [Commissions Marketplace]
            - [Fournitures Expédition]
            - [Retours Remboursements]
            - [Coûts Génériques]
"""

# ---------------------------------------------------------------------------
# Mapping des 9 postes de la formule -> colonne(s) customer_order.csv (grain commande)
# ---------------------------------------------------------------------------
# Poste (formule Marc)             | Colonne CSV order-grain            | Calculable ?
# 1 Revenue                        | order_amount_eur (state<>CANCELLED)| OUI
# 2 + Shipping revenue             | shipping_fee_eur (state<>CANCELLED)| OUI
# 3 - COGS                         | product_cost_eur (tous états)      | OUI
# 4 - Inbound transportation       | inbound_transportation_cost_eur    | OUI
# 5 - Outbound transportation      | total_shipping_cost_to_delivery_country_eur
#                                    -> ESTIMATION backend order-grain. La mesure DAX
#                                       utilise fact_transport[cout_transport_retenu]
#                                       (facturé si rapproché, sinon estimé) qui exige la
#                                       réconciliation factures/package (fact_factures_transport)
#                                       ABSENTE des 4 CSV backend. Le "retenu" (matché facture)
#                                       n'est PAS reproductible depuis customer_order.csv.
# 6 - Duties and taxes             | duties_and_taxes_eur               | OUI (order-grain ;
#                                       DAX le prend au grain colis fact_transport)
# 7 - Marketplace commission fees  | marketplace_fees_eur               | OUI
# 8 - Shipping supplies            | total_shipping_supplies_eur        | OUI (order-grain ;
#                                       DAX le prend au grain colis fact_transport)
# 9 - Returns / refunds            | returns_and_refunds_eur            | OUI (order-grain ;
#                                       DAX l'agrège depuis customer_order_item)
#10 - Generic costs                | total_generic_costs_eur            | OUI (order-grain ;
#                                       DAX l'agrège depuis customer_order_item)
#
# => Poste NON reproductible exactement : Outbound "retenu" (matché facture).
#    On calcule la marge avec l'ESTIMATION backend order-grain pour ce poste,
#    étiquetée explicitement (colonne dédiée), sans masquer la divergence.

CHANNELS_NAMED = {"WEBSITE", "PRO_WEBSITE", "CULTURA", "RAKUTEN", "FNAC"}


def canal(source):
    s = (source or "").strip()
    if s.startswith("AMAZON"):
        return "AMAZON"
    if s in CHANNELS_NAMED:
        return s
    return "AUTRES"


def fnum(x):
    """Parse un nombre. Retourne (valeur_float_ou_0, statut) statut in {non_nul, nul, vide}."""
    if x is None:
        return 0.0, "vide"
    s = x.strip()
    if s == "":
        return 0.0, "vide"
    try:
        v = float(s)
    except ValueError:
        return 0.0, "vide"
    if v == 0.0:
        return 0.0, "nul"
    return v, "non_nul"


def annee_mois(origin_created):
    if not origin_created:
        return None
    d = origin_created.strip()[:10]  # yyyy-mm-dd
    if len(d) < 7 or d[4] != "-":
        return None
    try:
        y = int(d[0:4]); m = int(d[5:7])
    except ValueError:
        return None
    return y * 100 + m


# ---------------------------------------------------------------------------
# PASSE 1 — stg_taux_moyen_mensuel : moyenne(currency_rate) par (currency, annee_mois)
#           sur toutes les lignes où currency_rate est non nul (expressions.tmdl l.160-186)
# ---------------------------------------------------------------------------
rate_sum = defaultdict(float)
rate_cnt = defaultdict(int)

with open(CSV_ORDER, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        cr = (row.get("currency_rate") or "").strip()
        cur = (row.get("currency") or "").strip()
        am = annee_mois(row.get("origin_created"))
        if cr == "" or cur == "" or am is None:
            continue
        try:
            crv = float(cr)
        except ValueError:
            continue
        rate_sum[(cur, am)] += crv
        rate_cnt[(cur, am)] += 1

taux_moyen = {k: rate_sum[k] / rate_cnt[k] for k in rate_sum}

# ---------------------------------------------------------------------------
# PASSE 2 — remplissage, CA natif/reconstruit, marge, périmètre résiduel
# ---------------------------------------------------------------------------
FIELDS_FILL = ["order_amount_eur", "order_amount_local", "shipping_fee_eur"]
# fill[canal][field][statut] = count
fill = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# agrégats marge par canal
agg = defaultdict(lambda: {
    "n_cmd": 0,
    "ca_natif": 0.0,          # order_amount_eur net annulation
    "ca_reconstruit": 0.0,    # ca_ht_reconstruit net annulation
    "shipping_rev": 0.0,      # shipping_fee_eur hors CANCELLED
    "cogs": 0.0,              # product_cost_eur tous états
    "inbound": 0.0,
    "outbound_est": 0.0,      # total_shipping_cost_to_delivery_country_eur (ESTIMATION)
    "duties": 0.0,
    "mkt_fees": 0.0,
    "supplies": 0.0,
    "returns": 0.0,
    "generic": 0.0,
})

# périmètre résiduel : order_amount_eur vide/nul ET order_amount_local renseigné
resid = defaultdict(lambda: {"n": 0, "ca_local": 0.0})

with open(CSV_ORDER, newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        c = canal(row.get("source"))
        state = (row.get("state") or "").strip()
        cancelled = (state == "CANCELLED")

        # ---- remplissage ----
        for fld in FIELDS_FILL:
            _, st = fnum(row.get(fld))
            fill[c][fld][st] += 1

        eur_v, eur_st = fnum(row.get("order_amount_eur"))
        loc_v, loc_st = fnum(row.get("order_amount_local"))

        # ---- CA reconstruit (logique Bloc 1 / ca_ht_reconstruit) ----
        cur = (row.get("currency") or "").strip()
        am = annee_mois(row.get("origin_created"))
        taux = taux_moyen.get((cur, am))
        if eur_st == "non_nul":
            ca_rec = eur_v
        elif loc_st == "non_nul" and taux not in (None, 0):
            ca_rec = loc_v / taux
        else:
            ca_rec = None  # reconstruction impossible

        a = agg[c]
        a["n_cmd"] += 1
        # Revenu net annulation (CA=0 si CANCELLED)
        if not cancelled:
            a["ca_natif"] += eur_v
            if ca_rec is not None:
                a["ca_reconstruit"] += ca_rec
            a["shipping_rev"] += fnum(row.get("shipping_fee_eur"))[0]
        # Coûts sur tous états
        a["cogs"] += fnum(row.get("product_cost_eur"))[0]
        a["inbound"] += fnum(row.get("inbound_transportation_cost_eur"))[0]
        a["outbound_est"] += fnum(row.get("total_shipping_cost_to_delivery_country_eur"))[0]
        a["duties"] += fnum(row.get("duties_and_taxes_eur"))[0]
        a["mkt_fees"] += fnum(row.get("marketplace_fees_eur"))[0]
        a["supplies"] += fnum(row.get("total_shipping_supplies_eur"))[0]
        a["returns"] += fnum(row.get("returns_and_refunds_eur"))[0]
        a["generic"] += fnum(row.get("total_generic_costs_eur"))[0]

        # ---- périmètre résiduel ----
        if eur_st in ("vide", "nul") and loc_st == "non_nul":
            resid[c]["n"] += 1
            resid[c]["ca_local"] += loc_v


# ---------------------------------------------------------------------------
# Restitution
# ---------------------------------------------------------------------------
CANAL_ORDER = ["WEBSITE", "PRO_WEBSITE", "AMAZON", "CULTURA", "RAKUTEN", "FNAC", "AUTRES"]
canaux = [c for c in CANAL_ORDER if c in agg] + [c for c in agg if c not in CANAL_ORDER]


def cots(a):
    """Somme des postes de coûts (identique base native/reconstruite)."""
    return (a["cogs"] + a["inbound"] + a["outbound_est"] + a["duties"]
            + a["mkt_fees"] + a["supplies"] + a["returns"] + a["generic"])


def marge_native(a):
    return a["ca_natif"] + a["shipping_rev"] - cots(a)


def marge_reconstruite(a):
    return a["ca_reconstruit"] + a["shipping_rev"] - cots(a)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def fmt(x, dec=2):
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


lines = []
lines.append("# Impact de l'export backend courant sur la marge brute — par canal")
lines.append("")
lines.append("Source : `Power_BI_Datawarehouse/Données_Backend/customer_order.csv` (lecture seule).")
lines.append("")

# ---- Commentaire DAX cité ----
lines.append("## Formule [Marge Brute] — commentaire DAX cité (verbatim _Mesures.tmdl)")
lines.append("")
lines.append("```")
lines.append(DAX_COMMENT.rstrip())
lines.append("```")
lines.append("")
lines.append("Poste **non reproductible exactement** depuis les CSV backend : "
             "*Outbound transportation (retenu)* = `fact_transport[cout_transport_retenu]` "
             "(facturé si rapproché, sinon estimé) — la réconciliation factures/colis n'existe "
             "pas dans les 4 CSV. Substitut order-grain **explicite** utilisé ci-dessous : "
             "`total_shipping_cost_to_delivery_country_eur` (estimation backend), étiqueté "
             "`outbound_est`. Postes duties / supplies / returns / generic : pris au grain "
             "commande (colonnes `*_eur` de customer_order.csv) là où la mesure DAX les prend "
             "au grain colis (fact_transport) ou article (customer_order_item).")
lines.append("")

# ---- Table 1 : remplissage ----
lines.append("## Table intermédiaire 1 — Taux de remplissage (canal × champ)")
lines.append("")
fill_headers = ["Canal", "Champ", "N", "% non nul", "% nul", "% vide",
                "n non nul", "n nul", "n vide"]
fill_rows = []
for c in canaux:
    for fld in FIELDS_FILL:
        d = fill[c][fld]
        n = d["non_nul"] + d["nul"] + d["vide"]
        if n == 0:
            continue
        fill_rows.append([
            c, fld, str(n),
            fmt(100 * d["non_nul"] / n, 1) + " %",
            fmt(100 * d["nul"] / n, 1) + " %",
            fmt(100 * d["vide"] / n, 1) + " %",
            str(d["non_nul"]), str(d["nul"]), str(d["vide"]),
        ])
lines.append(md_table(fill_headers, fill_rows))
lines.append("")

# ---- Table 2 : CA natif vs reconstruit ----
lines.append("## Table intermédiaire 2 — CA natif vs reconstruit (canal)")
lines.append("")
ca_headers = ["Canal", "Nb cmd", "CA natif €", "CA reconstruit €",
              "Écart abs €", "Écart %"]
ca_rows = []
for c in canaux:
    a = agg[c]
    ecart = a["ca_reconstruit"] - a["ca_natif"]
    pct = (100 * ecart / a["ca_natif"]) if a["ca_natif"] else 0.0
    ca_rows.append([
        c, str(a["n_cmd"]), fmt(a["ca_natif"]), fmt(a["ca_reconstruit"]),
        fmt(ecart), (fmt(pct, 2) + " %") if a["ca_natif"] else "n/a",
    ])
lines.append(md_table(ca_headers, ca_rows))
lines.append("")

# ---- Table 3 : périmètre résiduel ----
lines.append("## Table intermédiaire 3 — Périmètre résiduel "
             "(order_amount_eur vide/nul ET order_amount_local renseigné)")
lines.append("")
res_headers = ["Canal", "Nb cmd", "CA local (devise locale)"]
res_rows = []
tot_n = 0; tot_loc = 0.0
for c in canaux:
    rr = resid[c]
    if rr["n"] == 0:
        continue
    res_rows.append([c, str(rr["n"]), fmt(rr["ca_local"])])
    tot_n += rr["n"]; tot_loc += rr["ca_local"]
res_rows.append(["**TOTAL**", str(tot_n), fmt(tot_loc)])
lines.append(md_table(res_headers, res_rows))
lines.append("")

# ---- Table récap : canal × métrique ----
lines.append("## Tableau récapitulatif — canal × métrique")
lines.append("")
recap_headers = [
    "Canal", "Nb cmd",
    "CA natif €", "CA reconstruit €", "Écart abs €", "Écart %",
    "Marge brute (base native) €", "Marge brute (base reconstruite) €",
    "Taux marge natif", "Taux marge reconstruit",
]
recap_rows = []
recap_csv = []
for c in canaux:
    a = agg[c]
    ecart = a["ca_reconstruit"] - a["ca_natif"]
    pct = (100 * ecart / a["ca_natif"]) if a["ca_natif"] else None
    mn = marge_native(a)
    mr = marge_reconstruite(a)
    base_n = a["ca_natif"] + a["shipping_rev"]
    base_r = a["ca_reconstruit"] + a["shipping_rev"]
    tn = (mn / base_n) if base_n else None
    tr = (mr / base_r) if base_r else None
    recap_rows.append([
        c, str(a["n_cmd"]),
        fmt(a["ca_natif"]), fmt(a["ca_reconstruit"]), fmt(ecart),
        (fmt(pct, 2) + " %") if pct is not None else "n/a",
        fmt(mn), fmt(mr),
        (fmt(100 * tn, 2) + " %") if tn is not None else "n/a",
        (fmt(100 * tr, 2) + " %") if tr is not None else "n/a",
    ])
    recap_csv.append({
        "canal": c, "nb_cmd": a["n_cmd"],
        "ca_natif_eur": round(a["ca_natif"], 2),
        "ca_reconstruit_eur": round(a["ca_reconstruit"], 2),
        "ecart_abs_eur": round(ecart, 2),
        "ecart_pct": round(pct, 4) if pct is not None else "",
        "marge_brute_native_eur": round(mn, 2),
        "marge_brute_reconstruite_eur": round(mr, 2),
        "taux_marge_natif": round(tn, 6) if tn is not None else "",
        "taux_marge_reconstruit": round(tr, 6) if tr is not None else "",
    })
lines.append(md_table(recap_headers, recap_rows))
lines.append("")

report = "\n".join(lines)
print(report)

# ---- Exports CSV ----
with open(os.path.join(OUT_DIR, "recap_canal_metrique.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(recap_csv[0].keys()))
    w.writeheader(); w.writerows(recap_csv)

with open(os.path.join(OUT_DIR, "remplissage_canal_champ.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["canal", "champ", "n", "n_non_nul", "n_nul", "n_vide",
                "pct_non_nul", "pct_nul", "pct_vide"])
    for c in canaux:
        for fld in FIELDS_FILL:
            d = fill[c][fld]
            n = d["non_nul"] + d["nul"] + d["vide"]
            if n == 0:
                continue
            w.writerow([c, fld, n, d["non_nul"], d["nul"], d["vide"],
                        round(100 * d["non_nul"] / n, 3),
                        round(100 * d["nul"] / n, 3),
                        round(100 * d["vide"] / n, 3)])

with open(os.path.join(OUT_DIR, "ca_natif_vs_reconstruit.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["canal", "nb_cmd", "ca_natif_eur", "ca_reconstruit_eur", "ecart_abs_eur", "ecart_pct"])
    for c in canaux:
        a = agg[c]
        ecart = a["ca_reconstruit"] - a["ca_natif"]
        pct = (100 * ecart / a["ca_natif"]) if a["ca_natif"] else ""
        w.writerow([c, a["n_cmd"], round(a["ca_natif"], 2), round(a["ca_reconstruit"], 2),
                    round(ecart, 2), round(pct, 4) if pct != "" else ""])

with open(os.path.join(OUT_DIR, "perimetre_residuel.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["canal", "nb_cmd", "ca_local_devise_locale"])
    for c in canaux:
        rr = resid[c]
        if rr["n"] == 0:
            continue
        w.writerow([c, rr["n"], round(rr["ca_local"], 2)])
    w.writerow(["TOTAL", tot_n, round(tot_loc, 2)])

print("\n[CSV exportés dans %s]" % OUT_DIR)
