"""Audit : order_amount_eur = 0 sur 85 % des commandes — le CA existe-t-il ailleurs ?

LECTURE SEULE. Aucune modification des CSV bruts, aucune imputation décidée ici.
Produit uniquement des faits chiffrés pour répondre à la question avant de la
poser à Marc.

Tâche 1 : CA au niveau ligne (customer_order_item vs customer_order_item_group).
Tâche 2 : corrélation de order_amount_eur = 0 avec state / source / currency / période
          + reverse depuis gross_profit_eur pour les non-CANCELLED à 0.
Tâche 4 : origin_order_id / source comme discriminant CA transmis vs non transmis.
(Tâche 3 = balayage fichiers, traitée hors script à partir de l'inventaire.)
"""
from __future__ import annotations

import os

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Fix F-19 : racine de l'entrepôt paramétrable via la variable d'environnement LIREKA_DWH.
ROOT = Path(os.environ.get("LIREKA_DWH", Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"))
BACKEND = ROOT / "Données_Backend"
CO = BACKEND / "customer_order.csv"
ITEM = BACKEND / "customer_order_item.csv"
GRP = BACKEND / "customer_order_item_group.csv"


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def conv_metrics(a: pd.Series, b: pd.Series) -> dict:
    """Métriques de convergence entre 2 séries alignées (a vs b), sur index commun non-NaN."""
    m = a.notna() & b.notna()
    n = int(m.sum())
    if n == 0:
        return {"n": 0}
    d = (a - b)[m]
    rel = d.abs() / b[m].abs().replace(0, np.nan)
    return {
        "n": n,
        "sum_a": round(float(a[m].sum()), 2),
        "sum_b": round(float(b[m].sum()), 2),
        "mean_signed_diff (a-b)": round(float(d.mean()), 4),
        "median_abs_diff": round(float(d.abs().median()), 4),
        "max_abs_diff": round(float(d.abs().max()), 2),
        "pct_converge_lt_0p01": round(100 * float((d.abs() < 0.01).mean()), 3),
        "pct_converge_lt_1eur": round(100 * float((d.abs() < 1).mean()), 3),
        "pct_diff_gt_1eur": round(100 * float((d.abs() > 1).mean()), 3),
        "corr": round(float(a[m].corr(b[m])), 5) if n > 1 else None,
    }


# ===========================================================================
# Agrégation des fichiers de lignes par order_id
# ===========================================================================
def agg_item_group() -> tuple[pd.DataFrame, dict]:
    """Somme par commande du CA reconstitué depuis customer_order_item_group.

    rev_customer = Σ customer_price_per_item_eur × quantity  (prix payé client)
    rev_list     = Σ list_price_eur × quantity               (prix catalogue)
    """
    parts = []
    gtype_counts: dict[str, int] = {}
    gtype_rev: dict[str, float] = {}
    n_rows = 0
    n_cp_null = n_cp_zero = n_q_null = 0
    for chunk in pd.read_csv(
        GRP,
        usecols=["order_id", "quantity", "list_price_eur",
                 "customer_price_per_item_eur", "group_type"],
        chunksize=200_000,
        low_memory=False,
    ):
        n_rows += len(chunk)
        q = num(chunk["quantity"])
        cp = num(chunk["customer_price_per_item_eur"])
        lp = num(chunk["list_price_eur"])
        n_cp_null += int(cp.isna().sum())
        n_cp_zero += int((cp == 0).sum())
        n_q_null += int(q.isna().sum())
        chunk["_rev_c"] = cp * q
        chunk["_rev_l"] = lp * q
        parts.append(chunk.groupby("order_id")[["_rev_c", "_rev_l"]].sum())
        gt = chunk["group_type"].astype("string").fillna("(null)")
        for k, v in gt.value_counts().items():
            gtype_counts[k] = gtype_counts.get(k, 0) + int(v)
        for k, v in chunk.groupby(gt)["_rev_c"].sum().items():
            gtype_rev[k] = gtype_rev.get(k, 0.0) + float(v)
    agg = pd.concat(parts).groupby(level=0).sum()
    diag = {
        "item_group_rows": n_rows,
        "distinct_order_id": int(agg.index.nunique()),
        "customer_price_per_item_eur_null": n_cp_null,
        "customer_price_per_item_eur_zero": n_cp_zero,
        "quantity_null": n_q_null,
        "group_type_counts": gtype_counts,
        "group_type_rev_customer_sum": {k: round(v, 2) for k, v in gtype_rev.items()},
    }
    return agg, diag


def scan_item_columns() -> dict:
    """Confirme le contenu de customer_order_item.csv : colonnes de coût uniquement ?"""
    cols = list(pd.read_csv(ITEM, nrows=0).columns)
    sale_like = [c for c in cols if any(k in c.lower()
                 for k in ("price", "amount", "revenue", "sale", "sell", "montant", "prix"))]
    cost_like = [c for c in cols if "cost" in c.lower()]
    return {"columns": cols, "colonnes_prix_vente_detectees": sale_like, "colonnes_cout": cost_like}


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> None:
    print("Lecture customer_order.csv...")
    co = pd.read_csv(
        CO,
        usecols=["id", "state", "source", "currency", "origin_order_id", "origin_created",
                 "order_amount_eur", "order_amount_local", "currency_rate",
                 "product_cost_eur", "gross_profit_eur", "gross_margin",
                 "contribution_profit_eur"],
        dtype={"state": "string", "source": "string", "currency": "string",
               "origin_order_id": "string", "origin_created": "string"},
        low_memory=False,
    )
    n = len(co)
    oa = num(co["order_amount_eur"])
    oa_local = num(co["order_amount_local"])
    gp = num(co["gross_profit_eur"])
    gm = num(co["gross_margin"])
    pc = num(co["product_cost_eur"])
    co["_oa"] = oa
    co["_is_zero"] = oa == 0
    state = co["state"].str.strip().str.upper()
    co["_state"] = state
    is_cancelled = state.eq("CANCELLED")

    out: dict = {"customer_order_rows": n}

    # ---------------------------------------------------------------------
    # CONTEXTE — order_amount_eur / order_amount_local
    # ---------------------------------------------------------------------
    out["contexte_order_amount"] = {
        "order_amount_eur_zero": int((oa == 0).sum()),
        "order_amount_eur_zero_pct": round(100 * float((oa == 0).mean()), 3),
        "order_amount_eur_null": int(oa.isna().sum()),
        "order_amount_local_zero": int((oa_local == 0).sum()),
        "order_amount_local_zero_pct": round(100 * float((oa_local == 0).mean()), 3),
        "les_deux_zero_ensemble": int(((oa == 0) & (oa_local == 0)).sum()),
        "note": "si local et eur sont 0 aux mêmes lignes -> le 0 vient de la source, pas de la conversion",
    }

    # ---------------------------------------------------------------------
    # TÂCHE 1 — CA au niveau ligne
    # ---------------------------------------------------------------------
    print("Tâche 1 — scan colonnes item + agrégation item_group...")
    item_scan = scan_item_columns()
    grp_agg, grp_diag = agg_item_group()

    co_i = co.set_index("id")
    joined = co_i.join(grp_agg, how="left")  # _rev_c, _rev_l par order
    rev_c = joined["_rev_c"]
    rev_l = joined["_rev_l"]
    oa_j = num(joined["order_amount_eur"])
    gp_j = num(joined["gross_profit_eur"])
    gm_j = num(joined["gross_margin"])
    pc_j = num(joined["product_cost_eur"])
    rev_reconstruit = gp_j / gm_j.replace(0, np.nan)  # CA implicite backend

    mask_pos = oa_j > 0
    mask_zero = oa_j == 0

    t1 = {
        "customer_order_item_scan": item_scan,
        "item_group_diag": grp_diag,
        "verif_convergence_sur_order_amount_positif": {
            "rev_customer(item_group) vs order_amount_eur":
                conv_metrics(rev_c[mask_pos], oa_j[mask_pos]),
            "rev_list(item_group) vs order_amount_eur":
                conv_metrics(rev_l[mask_pos], oa_j[mask_pos]),
        },
        "reconstitution_sur_les_lignes_a_zero": {
            "commandes_oa_zero": int(mask_zero.sum()),
            "  dont rev_customer(item_group) renseigne_et_non_nul":
                int(((rev_c > 0) & mask_zero).sum()),
            "  dont rev_customer(item_group) = 0_ou_absent":
                int(((~(rev_c > 0)) & mask_zero).sum()),
            "somme_rev_customer_reconstitue_sur_oa_zero":
                round(float(rev_c[mask_zero].fillna(0).sum()), 2),
            "somme_rev_list_reconstitue_sur_oa_zero":
                round(float(rev_l[mask_zero].fillna(0).sum()), 2),
        },
        "coherence_rev_customer_vs_revenu_reconstruit_gp_sur_gm (toutes lignes)":
            conv_metrics(rev_c, rev_reconstruit),
        "coherence_rev_customer_vs_revenu_reconstruit_sur_oa_zero":
            conv_metrics(rev_c[mask_zero], rev_reconstruit[mask_zero]),
    }
    out["tache1_ca_niveau_ligne"] = t1

    # ---------------------------------------------------------------------
    # TÂCHE 2 — corrélation du nul
    # ---------------------------------------------------------------------
    print("Tâche 2 — corrélation du nul...")
    year = co["origin_created"].str.slice(0, 4)

    def cross_zero(dim: pd.Series, top: int = 25) -> dict:
        g = pd.DataFrame({"dim": dim.fillna("(null)"), "zero": co["_is_zero"]})
        tab = g.groupby("dim")["zero"].agg(["size", "sum"])
        tab["non_zero"] = tab["size"] - tab["sum"]
        tab["pct_zero"] = (100 * tab["sum"] / tab["size"]).round(2)
        tab = tab.sort_values("size", ascending=False).head(top)
        return {
            str(k): {"total": int(r["size"]), "oa_zero": int(r["sum"]),
                     "oa_non_zero": int(r["non_zero"]), "pct_zero": float(r["pct_zero"])}
            for k, r in tab.iterrows()
        }

    # table croisée state × (oa=0 / oa!=0) COMPLÈTE
    state_tab = pd.DataFrame({"state": state.fillna("(null)"), "zero": co["_is_zero"]})
    st = state_tab.groupby("state")["zero"].agg(["size", "sum"])
    st["oa_non_zero"] = st["size"] - st["sum"]
    st["pct_zero"] = (100 * st["sum"] / st["size"]).round(2)
    st = st.sort_values("size", ascending=False)
    state_cross = {
        str(k): {"total": int(r["size"]), "oa_zero": int(r["sum"]),
                 "oa_non_zero": int(r["oa_non_zero"]), "pct_zero": float(r["pct_zero"])}
        for k, r in st.iterrows()
    }

    n_zero = int((oa == 0).sum())
    n_zero_cancelled = int(((oa == 0) & is_cancelled).sum())
    # non-CANCELLED à oa=0 avec gross_profit renseigné et non nul
    mask_nc_zero = (oa == 0) & (~is_cancelled)
    gp_present_nonzero = mask_nc_zero & gp.notna() & (gp != 0)
    ca_reverse_cogs = (gp + pc)  # gross_profit = CA - COGS -> CA = gp + product_cost
    ca_reverse_gm = gp / gm.replace(0, np.nan)

    t2 = {
        "table_croisee_state_x_order_amount": state_cross,
        "recap_cancelled": {
            "order_amount_eur_zero_total": n_zero,
            "  dont CANCELLED": n_zero_cancelled,
            "  dont NON-CANCELLED": n_zero - n_zero_cancelled,
            "pct_des_zero_qui_sont_CANCELLED":
                round(100 * n_zero_cancelled / n_zero, 3) if n_zero else None,
            "total_CANCELLED": int(is_cancelled.sum()),
            "pct_CANCELLED_qui_sont_zero":
                round(100 * n_zero_cancelled / int(is_cancelled.sum()), 3) if int(is_cancelled.sum()) else None,
        },
        "non_cancelled_a_zero": {
            "total": int(mask_nc_zero.sum()),
            "avec_gross_profit_renseigne_et_non_nul": int(gp_present_nonzero.sum()),
            "pct": round(100 * float(gp_present_nonzero.sum()) / max(int(mask_nc_zero.sum()), 1), 3),
            "CA_implicite_reverse (gp + product_cost_eur) somme":
                round(float(ca_reverse_cogs[gp_present_nonzero].fillna(0).sum()), 2),
            "CA_implicite_reverse (gp / gross_margin) somme":
                round(float(ca_reverse_gm[gp_present_nonzero & gm.notna() & (gm != 0)].fillna(0).sum()), 2),
        },
        "repartition_currency (top)": cross_zero(co["currency"]),
        "repartition_source (top)": cross_zero(co["source"]),
        "repartition_annee": cross_zero(year, top=15),
    }
    out["tache2_correlation_du_nul"] = t2

    # ---------------------------------------------------------------------
    # TÂCHE 4 — origin_order_id / source comme piste
    # ---------------------------------------------------------------------
    print("Tâche 4 — origin_order_id / source...")
    ooid = co["origin_order_id"].astype("string").fillna("")
    # préfixe alpha initial (avant premier chiffre/séparateur)
    prefix = ooid.str.extract(r"^([A-Za-z]+)")[0].fillna("(num/vide)")
    has_letters = ooid.str.contains(r"[A-Za-z]", na=False)
    is_pure_num = ooid.str.match(r"^\d+$", na=False)
    is_empty = ooid.eq("")

    def prefix_cross(series: pd.Series, top: int = 25) -> dict:
        g = pd.DataFrame({"p": series, "zero": co["_is_zero"]})
        tab = g.groupby("p")["zero"].agg(["size", "sum"])
        tab["pct_zero"] = (100 * tab["sum"] / tab["size"]).round(2)
        tab = tab.sort_values("size", ascending=False).head(top)
        return {str(k): {"total": int(r["size"]), "oa_zero": int(r["sum"]),
                         "pct_zero": float(r["pct_zero"])} for k, r in tab.iterrows()}

    t4 = {
        "origin_order_id_format": {
            "vide": int(is_empty.sum()),
            "purement_numerique": int(is_pure_num.sum()),
            "contient_lettres": int(has_letters.sum()),
        },
        "prefixe_alpha_x_zero": prefix_cross(prefix),
        "format_x_zero": {
            "purement_numerique": {
                "total": int(is_pure_num.sum()),
                "oa_zero": int((is_pure_num & co["_is_zero"]).sum()),
                "pct_zero": round(100 * float((is_pure_num & co["_is_zero"]).sum()) / max(int(is_pure_num.sum()), 1), 2),
            },
            "contient_lettres": {
                "total": int(has_letters.sum()),
                "oa_zero": int((has_letters & co["_is_zero"]).sum()),
                "pct_zero": round(100 * float((has_letters & co["_is_zero"]).sum()) / max(int(has_letters.sum()), 1), 2),
            },
        },
        "note": "source déjà croisé en tâche 2 (repartition_source) : un canal à 100 % oa_zero "
                "ou 0 % oa_zero indiquerait un problème de transmission par canal.",
    }
    out["tache4_origin_source"] = t4

    out_path = Path(__file__).parent / "ca_reconstruction_output.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nÉcrit dans {out_path}")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
