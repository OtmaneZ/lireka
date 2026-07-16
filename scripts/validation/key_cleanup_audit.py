"""Audit nettoyage des clés avant chargement (lecture seule, aucune écriture sur les CSV bruts).

TÂCHE 1 : dédup tracking_id dans package.csv (groupes complets, strict vs divergent).
TÂCHE 2 : vérification de la dédup fichiers de l'audit initial + chevauchement réel
          numero_facture / numero_suivi entre récaps COLISSIMO et CHRONOPOST.
TÂCHE 3 : lignes destination_country nulles — champs de repli exploitables ?

Aucune règle de résolution / imputation décidée ici : faits chiffrés uniquement.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"
BACKEND = ROOT / "Données_Backend"
TRANSP = ROOT / "Dashboards_transporteurs"
PKG = BACKEND / "package.csv"
CO = BACKEND / "customer_order.csv"

PKG_COLS = ["id", "order_id", "tracking_id", "weight",
            "shipping_cost_eur", "shipping_supply_cost_eur", "duties_taxes_eur"]
BUSINESS_COLS = ["order_id", "weight", "shipping_cost_eur",
                 "shipping_supply_cost_eur", "duties_taxes_eur"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def norm_key(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper()


# ===========================================================================
# TÂCHE 1 — DÉDUP tracking_id (package.csv)
# ===========================================================================
def task1() -> dict:
    df = pd.read_csv(PKG, usecols=PKG_COLS, dtype={"tracking_id": "string"}, low_memory=False)
    df["_tk"] = norm_key(df["tracking_id"])
    valid = df[df["_tk"].notna() & (df["_tk"] != "")]
    counts = valid["_tk"].value_counts()
    dup_keys = counts[counts > 1].index
    dups = valid[valid["_tk"].isin(dup_keys)].copy()

    group_sizes = counts[counts > 1]
    n_groups = int(len(dup_keys))

    strict_excl_id = 0          # identiques sur toutes colonnes métier (id exclu)
    strict_incl_id = 0          # identiques y compris id (attendu 0, id = PK)
    differ_order_id = 0
    differ_weight = 0
    differ_ship = 0
    differ_supply = 0
    differ_duties = 0
    divergent_examples = []

    for tk, g in dups.groupby("_tk"):
        g_sorted = g.sort_values("id")
        biz = g_sorted[BUSINESS_COLS]
        all_incl_id = g_sorted[["id"] + BUSINESS_COLS]
        is_strict_biz = biz.nunique(dropna=False).eq(1).all()
        is_strict_all = all_incl_id.nunique(dropna=False).eq(1).all()
        if is_strict_all:
            strict_incl_id += 1
        if is_strict_biz:
            strict_excl_id += 1
        else:
            if g_sorted["order_id"].nunique(dropna=False) > 1:
                differ_order_id += 1
            if g_sorted["weight"].nunique(dropna=False) > 1:
                differ_weight += 1
            if g_sorted["shipping_cost_eur"].nunique(dropna=False) > 1:
                differ_ship += 1
            if g_sorted["shipping_supply_cost_eur"].nunique(dropna=False) > 1:
                differ_supply += 1
            if g_sorted["duties_taxes_eur"].nunique(dropna=False) > 1:
                differ_duties += 1
            if len(divergent_examples) < 5:
                divergent_examples.append({
                    "tracking_id": tk,
                    "rows": g_sorted[["id"] + PKG_COLS[1:]].to_dict(orient="records"),
                })

    n_divergent = n_groups - strict_excl_id
    return {
        "package_rows": int(len(df)),
        "distinct_tracking_id_non_null": int(valid["_tk"].nunique()),
        "duplicated_tracking_groups": n_groups,
        "group_size_distribution": {str(k): int(v) for k, v in group_sizes.value_counts().sort_index().items()},
        "strict_duplicate_all_cols_incl_id": strict_incl_id,
        "strict_duplicate_business_cols_id_excluded": strict_excl_id,
        "pct_strict_business": round(100 * strict_excl_id / n_groups, 2) if n_groups else None,
        "divergent_groups": n_divergent,
        "pct_divergent": round(100 * n_divergent / n_groups, 2) if n_groups else None,
        "divergence_breakdown (groupes divergents, non exclusifs)": {
            "differ_order_id": differ_order_id,
            "differ_weight": differ_weight,
            "differ_shipping_cost_eur": differ_ship,
            "differ_shipping_supply_cost_eur": differ_supply,
            "differ_duties_taxes_eur": differ_duties,
        },
        "divergent_examples_full (max 5)": divergent_examples,
    }


# ===========================================================================
# TÂCHE 2 — VÉRIFICATION DÉDUP FICHIERS
# ===========================================================================
def read_recap(path: Path) -> pd.DataFrame:
    for enc in ("latin-1", "utf-8"):
        try:
            return pd.read_csv(path, sep=";", dtype=str, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, sep=";", dtype=str, encoding="utf-8", on_bad_lines="skip")


def col_like(cols, *needles) -> str | None:
    for c in cols:
        cl = c.lower().lstrip("\ufeff")
        if all(n in cl for n in needles):
            return c
    return None


def overlap_stats(sets: dict[str, set]) -> dict:
    names = list(sets)
    out = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            inter = sets[a] & sets[b]
            out[f"{a} ∩ {b}"] = {
                "count_a": len(sets[a]),
                "count_b": len(sets[b]),
                "intersection": len(inter),
                "pct_of_a": round(100 * len(inter) / len(sets[a]), 2) if sets[a] else None,
                "pct_of_b": round(100 * len(inter) / len(sets[b]), 2) if sets[b] else None,
            }
    return out


def key_set(df: pd.DataFrame, col: str | None) -> set:
    if col is None:
        return set()
    s = df[col].astype("string").str.strip().str.upper()
    return set(s[s.notna() & (s != "")].tolist())


def task2() -> dict:
    result = {}

    # --- 2a. Nature de la fonction de dédup de l'audit initial ---
    result["dedup_function_review"] = {
        "fichier": "scripts/validation/audit_warehouse.py -> inventory()",
        "hash_contenu_calcule": "OUI (sha256_file, lecture binaire complète 1 Mo/chunk)",
        "compare_periodes_et_lignes": "OUI (csv_analysis: line_count + période min/max)",
        "limite_1": "ne compare QUE les fichiers dont le nom contient 'récap'/'recap' "
                    "(regex de recap_groups) -> les fichiers *_V2.csv sont EXCLUS du groupement",
        "limite_2": "groupe par préfixe année (2025_… vs 2026_… séparés via re.sub(r'_au_.*')) "
                    "-> 2025 et 2026 ne sont jamais comparés entre eux",
        "consequence": "chaque préfixe ne contenait qu'1 fichier -> aucun groupe de taille>1 -> "
                       "duplicates=[] SANS qu'aucune comparaison de contenu n'ait réellement eu lieu",
        "verdict": "fonction capable de comparer le contenu (hash), mais son PÉRIMÈTRE (filtre nom + "
                   "préfixe année) l'a empêchée de comparer les fichiers suspects entre eux",
    }

    # --- 2b. Inventaire réel des fichiers concernés ---
    col_dir = TRANSP / "COLISSIMO Dashboard PowerBI"
    chr_dir = TRANSP / "CHRONOPOST Dashboard PowerBI"
    col_files = {p.name: p for p in col_dir.glob("*.csv")}
    chr_files = {p.name: p for p in chr_dir.glob("*.csv")}
    result["fichiers_presents"] = {
        "COLISSIMO": sorted(col_files),
        "CHRONOPOST": sorted(chr_files),
        "note_COLISSIMO_V2": ("2026_COLISSIMO_V2.csv ABSENT du dossier"
                              if not any("v2" in n.lower() for n in col_files)
                              else "présent"),
    }

    # --- 2c. COLISSIMO : chevauchement N° de colis (pas de colonne facture) ---
    col_res = {}
    col_sets_suivi = {}
    for name, p in col_files.items():
        df = read_recap(p)
        cols = list(df.columns)
        fac = col_like(cols, "factur") or col_like(cols, "n°", "facture")
        suivi = col_like(cols, "colis") or col_like(cols, "suivi") or col_like(cols, "objet")
        col_res[name] = {
            "columns": cols,
            "rows": int(len(df)),
            "colonne_facture": fac,
            "colonne_suivi": suivi,
            "sha256": sha256_file(p),
        }
        col_sets_suivi[name] = key_set(df, suivi)
    result["COLISSIMO"] = {
        "fichiers": col_res,
        "chevauchement_numero_suivi": overlap_stats(col_sets_suivi),
        "chevauchement_numero_facture": "N/A — aucune colonne facture dans les récaps COLISSIMO",
    }

    # --- 2d. CHRONOPOST : chevauchement facture + suivi, + identité byte ---
    chr_res = {}
    sets_fac, sets_suivi = {}, {}
    for name, p in chr_files.items():
        df = read_recap(p)
        cols = list(df.columns)
        fac = col_like(cols, "factur")
        suivi = col_like(cols, "colis") or col_like(cols, "objet") or col_like(cols, "suivi")
        chr_res[name] = {
            "columns": cols,
            "rows": int(len(df)),
            "colonne_facture": fac,
            "colonne_suivi": suivi,
            "sha256": sha256_file(p),
        }
        sets_fac[name] = key_set(df, fac)
        sets_suivi[name] = key_set(df, suivi)
    # identité byte-for-byte
    hashes = {n: chr_res[n]["sha256"] for n in chr_res}
    identical_pairs = []
    ns = list(hashes)
    for i in range(len(ns)):
        for j in range(i + 1, len(ns)):
            if hashes[ns[i]] == hashes[ns[j]]:
                identical_pairs.append([ns[i], ns[j]])
    result["CHRONOPOST"] = {
        "fichiers": chr_res,
        "paires_identiques_byte_for_byte": identical_pairs,
        "chevauchement_numero_facture": overlap_stats(sets_fac),
        "chevauchement_numero_suivi": overlap_stats(sets_suivi),
    }
    return result


# ===========================================================================
# TÂCHE 3 — destination_country nul
# ===========================================================================
def task3() -> dict:
    cols = ["id", "destination_country", "currency", "source",
            "origin_order_id", "state", "origin_created"]
    df = pd.read_csv(CO, usecols=cols, dtype=str, low_memory=False)
    total = len(df)
    dc = df["destination_country"].astype("string").str.strip()
    is_null = dc.isna() | (dc == "") | (dc.str.lower() == "nan")
    nul = df[is_null].copy()
    n = int(len(nul))

    def dist(col: str, top: int = 20) -> dict:
        vc = nul[col].astype("string").str.strip().replace({"": "(vide)"}).fillna("(null)").value_counts()
        return {str(k): int(v) for k, v in vc.head(top).items()}

    # motif pays dans origin_order_id : segment -XX- (2 lettres)
    ooid = nul["origin_order_id"].astype("string").fillna("")
    m = ooid.str.extract(r"-([A-Za-z]{2})-")
    country_from_ooid = m[0].str.upper()
    has_country_code = country_from_ooid.notna()

    # période
    yr = nul["origin_created"].astype("string").str.slice(0, 4)

    # croisement : parmi les null, combien ont AU MOINS un repli exploitable
    cur = nul["currency"].astype("string").str.strip().str.upper()
    src = nul["source"].astype("string").str.strip()
    currency_singlecountry = cur.isin(["USD", "CAD", "GBP", "JPY", "CHF", "AUD"])  # devise ~ 1 pays
    source_has_country = src.str.contains(r"_[A-Z]{2}$", na=False)

    any_fallback = has_country_code | currency_singlecountry | source_has_country

    return {
        "customer_order_rows": total,
        "destination_country_null_count": n,
        "destination_country_null_pct": round(100 * n / total, 3),
        "repartition_currency": dist("currency"),
        "repartition_source": dist("source"),
        "repartition_state": dist("state"),
        "repartition_par_annee": {str(k): int(v) for k, v in yr.value_counts().sort_index().items()},
        "origin_order_id_avec_code_pays (-XX-)": {
            "count": int(has_country_code.sum()),
            "pct_des_null": round(100 * int(has_country_code.sum()) / n, 2) if n else None,
            "top_codes": {str(k): int(v) for k, v in country_from_ooid[has_country_code].value_counts().head(15).items()},
        },
        "currency_mono_pays (USD/CAD/GBP/…)": {
            "count": int(currency_singlecountry.sum()),
            "pct_des_null": round(100 * int(currency_singlecountry.sum()) / n, 2) if n else None,
        },
        "source_avec_suffixe_pays (_XX)": {
            "count": int(source_has_country.sum()),
            "pct_des_null": round(100 * int(source_has_country.sum()) / n, 2) if n else None,
            "top": {str(k): int(v) for k, v in src[source_has_country].value_counts().head(15).items()},
        },
        "au_moins_un_repli_exploitable": {
            "count": int(any_fallback.sum()),
            "pct_des_null": round(100 * int(any_fallback.sum()) / n, 2) if n else None,
        },
        "aucun_repli_exploitable": {
            "count": int((~any_fallback).sum()),
            "pct_des_null": round(100 * int((~any_fallback).sum()) / n, 2) if n else None,
        },
    }


def main() -> None:
    try:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("TÂCHE 1 — dédup tracking_id...")
    t1 = task1()
    print("TÂCHE 2 — vérification dédup fichiers...")
    t2 = task2()
    print("TÂCHE 3 — destination_country nul...")
    t3 = task3()

    out = {"task1_dedup_tracking": t1, "task2_dedup_fichiers": t2, "task3_destination_country_null": t3}
    out_path = Path(__file__).parent / "key_cleanup_output.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nÉcrit dans {out_path}")


if __name__ == "__main__":
    main()
