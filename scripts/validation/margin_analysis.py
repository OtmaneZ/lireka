"""Analyse marge brute Lireka — fill rate + recalcul vs gross_profit_eur.

Tâche 1 : fill rate (%null, %zero) par colonne sur fichier réel complet, + cohérence
          entre variantes (customer_order vs item/package) au grain commande.
Tâche 2 : recalcul de la marge ligne à ligne au grain customer_order avec la formule
          validée par Marc, comparaison à gross_profit_eur (natif), et isolation de
          poste par poste quand un écart systématique apparaît.

AUCUNE modification des fichiers de données. Lecture seule.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"
BACKEND = ROOT / "Données_Backend"
CO = BACKEND / "customer_order.csv"
ITEM = BACKEND / "customer_order_item.csv"
PKG = BACKEND / "package.csv"

# ---------------------------------------------------------------------------
# Colonnes par poste (fichier, colonne). Les variantes secondaires sont au grain
# item/package et devront être agrégées par order_id pour toute comparaison.
# ---------------------------------------------------------------------------
POSTS = {
    "Revenue":                 [(CO, "order_amount_eur")],
    "Shipping revenue":        [(CO, "shipping_fee_eur")],
    "COGS":                    [(CO, "product_cost_eur"), (ITEM, "product_cost_eur")],
    "Transport inbound":       [(CO, "inbound_transportation_cost_eur"), (ITEM, "freight_in_cost_eur")],
    "Transport outbound":      [(CO, "total_shipping_cost_to_delivery_country_eur"),
                                (ITEM, "shipping_cost_to_delivery_country_eur"),
                                (PKG, "shipping_cost_eur")],
    "Duties/taxes":            [(CO, "duties_and_taxes_eur"), (PKG, "duties_taxes_eur")],
    "Commissions marketplace": [(CO, "marketplace_fees_eur")],
    "Fournitures expédition":  [(CO, "total_shipping_supplies_eur"),
                                (ITEM, "shipping_supplies_cost_eur"),
                                (PKG, "shipping_supply_cost_eur")],
}

# Postes présents dans customer_order mais ABSENTS de la formule de Marc — testés en Tâche 2.
EXTRA_CO = ["returns_and_refunds_eur", "total_generic_costs_eur"]


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


# ===========================================================================
# TÂCHE 1 — FILL RATE
# ===========================================================================
def fill_rate_for_column(path: Path, col: str) -> dict:
    total = 0
    n_null = 0
    n_zero = 0
    n_neg = 0
    s_sum = 0.0
    for chunk in pd.read_csv(path, usecols=[col], chunksize=200_000, low_memory=False):
        v = num(chunk[col])
        total += len(v)
        n_null += int(v.isna().sum())
        n_zero += int((v == 0).sum())
        n_neg += int((v < 0).sum())
        s_sum += float(v.fillna(0).sum())
    return {
        "file": path.name,
        "column": col,
        "rows": total,
        "pct_null": round(100 * n_null / total, 3) if total else None,
        "pct_zero": round(100 * n_zero / total, 3) if total else None,
        "pct_null_or_zero": round(100 * (n_null + n_zero) / total, 3) if total else None,
        "pct_negative": round(100 * n_neg / total, 3) if total else None,
        "sum_eur": round(s_sum, 2),
    }


def task1_fill_rate() -> dict:
    out = {}
    for post, variants in POSTS.items():
        out[post] = [fill_rate_for_column(p, c) for p, c in variants]
    # postes hors formule (contexte pour la tâche 2)
    out["_hors_formule (customer_order)"] = [fill_rate_for_column(CO, c) for c in EXTRA_CO]
    out["_natif backend (customer_order)"] = [
        fill_rate_for_column(CO, c) for c in ["gross_profit_eur", "contribution_profit_eur"]
    ]
    return out


def agg_by_order(path: Path, col: str) -> pd.DataFrame:
    """Somme d'une colonne item/package par order_id (grain commande)."""
    parts = []
    for chunk in pd.read_csv(path, usecols=["order_id", col], chunksize=200_000, low_memory=False):
        chunk[col] = num(chunk[col])
        parts.append(chunk.groupby("order_id", dropna=True)[col].sum())
    s = pd.concat(parts).groupby(level=0).sum()
    return s.rename(col + "__agg")


def task1_coherence(co_df: pd.DataFrame) -> dict:
    """Cohérence entre variante customer_order et variante item/package agrégée."""
    checks = {
        "COGS": (ITEM, "product_cost_eur", "product_cost_eur"),
        "Transport inbound": (ITEM, "freight_in_cost_eur", "inbound_transportation_cost_eur"),
        "Transport outbound (item)": (ITEM, "shipping_cost_to_delivery_country_eur",
                                      "total_shipping_cost_to_delivery_country_eur"),
        "Transport outbound (package)": (PKG, "shipping_cost_eur",
                                         "total_shipping_cost_to_delivery_country_eur"),
        "Duties/taxes (package)": (PKG, "duties_taxes_eur", "duties_and_taxes_eur"),
        "Fournitures (item)": (ITEM, "shipping_supplies_cost_eur", "total_shipping_supplies_eur"),
        "Fournitures (package)": (PKG, "shipping_supply_cost_eur", "total_shipping_supplies_eur"),
    }
    res = {}
    for name, (path, agg_col, co_col) in checks.items():
        agg = agg_by_order(path, agg_col)
        m = co_df[["id", co_col]].merge(agg, left_on="id", right_index=True, how="inner")
        a = num(m[co_col])
        b = m[agg_col + "__agg"]
        both = a.notna() & b.notna()
        n_both = int(both.sum())
        diff = (a - b)[both]
        rel = (diff.abs() / a[both].abs().replace(0, np.nan))
        res[name] = {
            "co_column": co_col,
            "agg_source": f"{path.name}[{agg_col}] sommé par order_id",
            "orders_both_present": n_both,
            "co_sum_eur": round(float(a[both].sum()), 2),
            "agg_sum_eur": round(float(b[both].sum()), 2),
            "mean_abs_diff": round(float(diff.abs().mean()), 4) if n_both else None,
            "median_abs_diff": round(float(diff.abs().median()), 4) if n_both else None,
            "max_abs_diff": round(float(diff.abs().max()), 4) if n_both else None,
            "pct_diff_gt_1eur": round(100 * float((diff.abs() > 1).mean()), 3) if n_both else None,
            "pct_diff_gt_1pct_rel": round(100 * float((rel > 0.01).mean()), 3) if n_both else None,
            "corr": round(float(a[both].corr(b[both])), 5) if n_both > 1 else None,
        }
    return res


# ===========================================================================
# TÂCHE 2 — RECALCUL vs gross_profit_eur
# ===========================================================================
def diff_metrics(recalc: pd.Series, backend: pd.Series, mask: pd.Series) -> dict:
    d = (recalc - backend)[mask]
    n = int(mask.sum())
    if n == 0:
        return {"n": 0}
    rel = (d.abs() / backend[mask].abs().replace(0, np.nan))
    return {
        "n": n,
        "mean_signed_diff": round(float(d.mean()), 4),
        "mean_abs_diff": round(float(d.abs().mean()), 4),
        "median_signed_diff": round(float(d.median()), 4),
        "median_abs_diff": round(float(d.abs().median()), 4),
        "max_abs_diff": round(float(d.abs().max()), 4),
        "pct_lines_diff_gt_1eur": round(100 * float((d.abs() > 1).mean()), 3),
        "pct_lines_rel_gt_5pct": round(100 * float((rel > 0.05).mean()), 3),
        "pct_lines_converged_lt_0p01eur": round(100 * float((d.abs() < 0.01).mean()), 3),
    }


def task2_recalc(co: pd.DataFrame) -> dict:
    gp_exists = "gross_profit_eur" in co.columns
    cp_exists = "contribution_profit_eur" in co.columns

    # composants (NaN -> 0 pour la somme, cf. note fill rate)
    rev = num(co["order_amount_eur"]).fillna(0)
    ship_rev = num(co["shipping_fee_eur"]).fillna(0)
    cogs = num(co["product_cost_eur"]).fillna(0)
    inbound = num(co["inbound_transportation_cost_eur"]).fillna(0)
    outbound = num(co["total_shipping_cost_to_delivery_country_eur"]).fillna(0)
    duties = num(co["duties_and_taxes_eur"]).fillna(0)
    commissions = num(co["marketplace_fees_eur"]).fillna(0)
    supplies = num(co["total_shipping_supplies_eur"]).fillna(0)
    returns = num(co["returns_and_refunds_eur"]).fillna(0)
    generic = num(co["total_generic_costs_eur"]).fillna(0)

    gp = num(co["gross_profit_eur"]) if gp_exists else None
    cp = num(co["contribution_profit_eur"]) if cp_exists else None

    # revenu reconstruit depuis backend : gross_profit / gross_margin
    gmargin = num(co["gross_margin"]) if "gross_margin" in co.columns else None
    rev_backend = None
    if gp is not None and gmargin is not None:
        rev_backend = (gp / gmargin.replace(0, np.nan))

    # Formule Marc (grain customer_order)
    formula_full = rev + ship_rev - cogs - inbound - outbound - duties - commissions - supplies

    # masque : lignes où gross_profit_eur est renseigné
    mask_gp = gp.notna() if gp is not None else pd.Series(False, index=co.index)
    mask_cp = cp.notna() if cp is not None else pd.Series(False, index=co.index)

    out = {
        "gross_profit_eur_exists": gp_exists,
        "contribution_profit_eur_exists": cp_exists,
        "note_revenue": (
            "order_amount_eur = 0 sur de nombreuses lignes alors que gross_profit_eur est "
            "renseigné : le backend n'utilise PAS order_amount_eur comme revenu. "
            "Revenu reconstruit = gross_profit_eur / gross_margin pour contrôle."
        ),
    }

    # --- comparaison formule complète vs backend ---
    out["formule_Marc_vs_gross_profit_eur"] = diff_metrics(formula_full, gp, mask_gp) if gp is not None else "N/A"
    if cp is not None:
        out["formule_Marc_vs_contribution_profit_eur"] = diff_metrics(formula_full, cp, mask_cp)

    # --- diagnostic revenu : order_amount_eur vs revenu reconstruit ---
    if rev_backend is not None:
        rb = rev_backend
        m = mask_gp & rb.notna() & np.isfinite(rb)
        gap = (rev - rb)[m]
        out["revenu_order_amount_eur_vs_reconstruit"] = {
            "n": int(m.sum()),
            "pct_order_amount_eur_zero_quand_gp_present": round(
                100 * float(((rev == 0) & m).sum() / max(int(m.sum()), 1)), 3),
            "mean_signed_diff (oa - reconstruit)": round(float(gap.mean()), 4),
            "median_abs_diff": round(float(gap.abs().median()), 4),
            "pct_lignes_ecart_gt_1eur": round(100 * float((gap.abs() > 1).mean()), 3),
        }
        # formule avec revenu reconstruit au lieu de order_amount_eur
        formula_rev_bk = rb.fillna(0) + ship_rev - cogs - inbound - outbound - duties - commissions - supplies
        out["formule_avec_revenu_reconstruit_vs_gross_profit"] = diff_metrics(formula_rev_bk, gp, m)
        if cp is not None:
            out["formule_avec_revenu_reconstruit_vs_contribution"] = diff_metrics(formula_rev_bk, cp, m & mask_cp)

    # --- isolation poste par poste : retirer un poste à la fois ---
    # base = formule complète ; on ajoute le poste (= le retirer de la soustraction)
    components_removable = {
        "sans_COGS": cogs,
        "sans_inbound": inbound,
        "sans_outbound": outbound,
        "sans_duties": duties,
        "sans_commissions": commissions,
        "sans_fournitures": supplies,
        "sans_shipping_revenue": -ship_rev,  # retirer un + revient à soustraire
    }
    iso_gp = {}
    for label, comp in components_removable.items():
        variant = formula_full + comp if not label.startswith("sans_shipping") else formula_full + ship_rev
        # (pour shipping_revenue : le retirer = enlever +ship_rev)
        if label == "sans_shipping_revenue":
            variant = formula_full - ship_rev
        else:
            variant = formula_full + comp
        iso_gp[label] = diff_metrics(variant, gp, mask_gp) if gp is not None else "N/A"
    out["isolation_vs_gross_profit (retrait d'un poste)"] = iso_gp

    # --- ajout des postes hors formule (returns / generic) vs contribution ---
    add_tests = {}
    base = formula_full
    add_tests["formule_moins_returns"] = base - returns
    add_tests["formule_moins_generic"] = base - generic
    add_tests["formule_moins_returns_et_generic"] = base - returns - generic
    if cp is not None:
        out["ajout_postes_hors_formule_vs_contribution_profit"] = {
            k: diff_metrics(v, cp, mask_cp) for k, v in add_tests.items()
        }
    if gp is not None:
        out["ajout_postes_hors_formule_vs_gross_profit"] = {
            k: diff_metrics(v, gp, mask_gp) for k, v in add_tests.items()
        }

    # --- test hypothèse : gross_profit = revenu_reconstruit - COGS seul ---
    if rev_backend is not None and gp is not None:
        m = mask_gp & rev_backend.notna() & np.isfinite(rev_backend)
        gp_hat = (rev_backend.fillna(0) - cogs)
        out["hypothese_gross_profit = revenu_reconstruit - COGS"] = diff_metrics(gp_hat, gp, m)

    # --- confirmation : formule Marc (revenu reconstruit) MOINS returns MOINS generic
    #     doit converger vers contribution_profit_eur ---
    if rev_backend is not None and cp is not None:
        m = mask_cp & rev_backend.notna() & np.isfinite(rev_backend)
        rb0 = rev_backend.fillna(0)
        marc_bk = rb0 + ship_rev - cogs - inbound - outbound - duties - commissions - supplies
        out["confirmation_vs_contribution"] = {
            "formule_Marc(revenu_reconstruit)": diff_metrics(marc_bk, cp, m),
            "formule_Marc - returns": diff_metrics(marc_bk - returns, cp, m),
            "formule_Marc - generic": diff_metrics(marc_bk - generic, cp, m),
            "formule_Marc - returns - generic": diff_metrics(marc_bk - returns - generic, cp, m),
            "formule_Marc - shipping_rev - returns - generic":
                diff_metrics(marc_bk - ship_rev - returns - generic, cp, m),
        }
        # décomposition directe du résidu (formule Marc - contribution)
        resid = (marc_bk - cp)[m]
        expected = (ship_rev + returns + generic)[m]
        gap = (resid - expected)
        out["residu_decompose (Marc - contribution) vs (shipping_rev+returns+generic)"] = {
            "n": int(m.sum()),
            "mean_abs_gap": round(float(gap.abs().mean()), 4),
            "median_abs_gap": round(float(gap.abs().median()), 4),
            "pct_lignes_gap_lt_0p01eur": round(100 * float((gap.abs() < 0.01).mean()), 3),
        }

    return out


# ===========================================================================
def main() -> None:
    print("Lecture customer_order.csv (colonnes utiles)...")
    co_cols = [
        "id", "order_amount_eur", "shipping_fee_eur", "marketplace_fees_eur",
        "product_cost_eur", "inbound_transportation_cost_eur", "returns_and_refunds_eur",
        "total_shipping_cost_to_delivery_country_eur", "total_shipping_supplies_eur",
        "duties_and_taxes_eur", "total_generic_costs_eur", "gross_profit_eur",
        "gross_margin", "contribution_profit_eur", "contribution_margin",
    ]
    co = pd.read_csv(CO, usecols=co_cols, low_memory=False)
    print(f"  {len(co):,} lignes customer_order")

    print("Tâche 1 — fill rate...")
    fill = task1_fill_rate()
    print("Tâche 1 — cohérence entre variantes...")
    coherence = task1_coherence(co)
    print("Tâche 2 — recalcul vs gross_profit_eur...")
    recalc = task2_recalc(co)

    result = {
        "customer_order_rows": len(co),
        "task1_fill_rate": fill,
        "task1_coherence_variantes": coherence,
        "task2_recalc": recalc,
    }
    out_path = Path(__file__).parent / "margin_analysis_output.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- console: tableau fill rate ----
    print("\n" + "=" * 78)
    print("TÂCHE 1 — FILL RATE (fichier complet)")
    print("=" * 78)
    hdr = f"{'Poste':<26}{'fichier[colonne]':<48}{'%null':>8}{'%zero':>8}"
    print(hdr)
    print("-" * len(hdr))
    for post, rows in fill.items():
        for r in rows:
            key = f"{r['file']}[{r['column']}]"
            print(f"{post:<26}{key:<48}{r['pct_null']:>8}{r['pct_zero']:>8}")

    print("\n" + "=" * 78)
    print("TÂCHE 1 — COHÉRENCE VARIANTES (grain commande, lignes où les 2 existent)")
    print("=" * 78)
    for name, r in coherence.items():
        print(f"\n{name}:")
        for k, v in r.items():
            print(f"   {k}: {v}")

    print("\n" + "=" * 78)
    print("TÂCHE 2 — RECALCUL vs gross_profit_eur")
    print("=" * 78)
    print(f"gross_profit_eur existe : {recalc['gross_profit_eur_exists']}")
    print(f"contribution_profit_eur existe : {recalc['contribution_profit_eur_exists']}")
    print(json.dumps(recalc, ensure_ascii=False, indent=2))
    print(f"\nRésultats complets écrits dans {out_path}")


if __name__ == "__main__":
    main()
