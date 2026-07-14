"""
Analyse exploratoire — Données backend Lireka
==============================================
Rapport console sur les 4 CSV de Power_BI_Datawarehouse/Données_Backend/.

Usage:
    python scripts/validation/analyse_donnees_backend.py
    python scripts/validation/analyse_donnees_backend.py --data-dir "C:/chemin/Données_Backend"
"""

from __future__ import annotations

import os

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Fix F-19 : racine de l'entrepôt paramétrable via la variable d'environnement LIREKA_DWH.
WAREHOUSE_DIR = Path(os.environ.get("LIREKA_DWH", Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"))

DEFAULT_DATA_DIR = WAREHOUSE_DIR / "Données_Backend"

FILES = {
    "customer_order.csv": {
        "chunksize": 100_000,
        "dtype": {
            "id": "Int64",
            "origin_order_id": "string",
            "state": "string",
            "source": "string",
            "destination_country": "string",
            "currency": "string",
        },
    },
    "customer_order_item.csv": {
        "chunksize": 150_000,
        "dtype": {
            "id": "Int64",
            "item_group_id": "Int64",
            "order_id": "Int64",
            "package_id": "Int64",
            "internal_state": "string",
        },
    },
    "customer_order_item_group.csv": {
        "chunksize": 150_000,
        "dtype": {
            "id": "Int64",
            "order_id": "Int64",
            "isbn": "string",
            "group_type": "string",
        },
    },
    "package.csv": {
        "chunksize": 100_000,
        "dtype": {
            "id": "Int64",
            "order_id": "Int64",
            "tracking_id": "string",
        },
    },
}

CARRIER_KEYWORDS = (
    "transporteur",
    "carrier",
    "provider",
    "courier",
    "shipper",
    "delivengo",
)

CARRIER_KEYWORDS_EXCLUDE = (
    "cost",
    "fee",
    "amount",
    "eur",
    "price",
    "rate",
    "margin",
    "profit",
    "tax",
    "weight",
)

CARRIER_COLUMN_CANDIDATES = (
    "transporteur",
    "carrier",
    "provider",
    "shipping_provider",
    "shipping_carrier",
    "delivery_provider",
    "courier",
    "shipper",
    "transport_provider",
)

COLIS_PRIVE_ALIASES = {
    "colis prive",
    "colis privé",
    "colis-prive",
    "colisprive",
    "geopost",
}

POSTES_CANADA_ALIASES = {
    "postes canada",
    "canada post",
    "canadapost",
    "postes canadiennes",
}


def hr(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def sub(title: str) -> None:
    print()
    print(f"--- {title} ---")


def fmt_int(n: int | float) -> str:
    return f"{int(n):,}".replace(",", " ")


def fmt_pct(num: float, den: float) -> str:
    if den == 0:
        return "N/A"
    return f"{100.0 * num / den:.4f}%"


def fmt_num(x: float) -> str:
    if pd.isna(x):
        return "NaN"
    return f"{x:.6f}"


def normalize_carrier_label(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def is_carrier_like_column(name: str) -> bool:
    lower = name.lower()
    if any(ex in lower for ex in CARRIER_KEYWORDS_EXCLUDE):
        return False
    return any(k in lower for k in CARRIER_KEYWORDS)


def find_carrier_column(columns: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in columns}
    for candidate in CARRIER_COLUMN_CANDIDATES:
        if candidate in lower_map:
            return lower_map[candidate]
    for col in columns:
        if is_carrier_like_column(col):
            return col
    return None


def infer_dtype_series(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    return "string/object"


def analyze_schema(data_dir: Path) -> dict[str, dict]:
    """Point 1 — schéma, types, nulls, ligne count."""
    results: dict[str, dict] = {}

    for filename, cfg in FILES.items():
        path = data_dir / filename
        if not path.exists():
            results[filename] = {"error": f"fichier introuvable: {path}"}
            continue

        null_counts: Counter[str] = Counter()
        row_count = 0
        columns: list[str] | None = None
        dtype_samples: dict[str, list] = defaultdict(list)

        reader = pd.read_csv(
            path,
            dtype=cfg.get("dtype"),
            chunksize=cfg["chunksize"],
            low_memory=False,
        )

        for chunk in reader:
            if columns is None:
                columns = list(chunk.columns)
            row_count += len(chunk)
            for col in chunk.columns:
                null_counts[col] += int(chunk[col].isna().sum())
                if len(dtype_samples[col]) < 5:
                    non_null = chunk[col].dropna()
                    if not non_null.empty:
                        dtype_samples[col].append(non_null.iloc[0])

        assert columns is not None
        col_types: dict[str, str] = {}
        for col in columns:
            sample_vals = dtype_samples[col]
            if sample_vals:
                s = pd.Series(sample_vals)
                col_types[col] = infer_dtype_series(s)
            else:
                col_types[col] = "unknown (toutes valeurs nulles)"

        carrier_col = find_carrier_column(columns)

        results[filename] = {
            "path": path,
            "rows": row_count,
            "columns": columns,
            "types": col_types,
            "nulls": dict(null_counts),
            "carrier_column": carrier_col,
        }

    return results


def load_invoice_tracking_sets(warehouse_dir: Path) -> dict[str, set[str]]:
    """Construit des sets de tracking connus depuis les factures disponibles."""
    tracking_sets: dict[str, set[str]] = {}

    colissimo_dir = warehouse_dir / "Dashboards_transporteurs" / "COLISSIMO Dashboard PowerBI"
    for path in sorted(colissimo_dir.glob("*.csv")):
        try:
            df = pd.read_csv(path, sep=";", dtype=str, encoding="latin-1")
        except Exception:
            df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8")
        col = next((c for c in df.columns if "colis" in c.lower()), None)
        if col:
            tracking_sets.setdefault("La Poste", set()).update(
                df[col].dropna().astype(str).str.strip().str.upper()
            )

    chronopost_dir = warehouse_dir / "Dashboards_transporteurs" / "CHRONOPOST Dashboard PowerBI"
    for path in sorted(chronopost_dir.glob("*.csv")):
        try:
            df = pd.read_csv(path, sep=";", dtype=str, encoding="latin-1")
        except Exception:
            df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8")
        col = next((c for c in df.columns if "colis" in c.lower()), None)
        if col:
            tracking_sets.setdefault("Chronopost", set()).update(
                df[col].dropna().astype(str).str.strip().str.upper()
            )

    ups_dir = (
        warehouse_dir
        / "Dashboards_transporteurs"
        / "UPS Dashboard PowerBI"
        / "01_Données"
        / "02_Données_Sources"
    )
    if ups_dir.exists():
        ups_ids: set[str] = set()
        for path in list(ups_dir.glob("*.csv"))[:50]:
            try:
                df = pd.read_csv(path, header=None, dtype=str, nrows=500)
                for val in df.values.ravel():
                    if isinstance(val, str) and val.startswith("1Z"):
                        ups_ids.add(val.strip().upper())
            except Exception:
                continue
        if ups_ids:
            tracking_sets["UPS"] = ups_ids

    return tracking_sets


def infer_carrier_from_tracking(
    tracking_id: object,
    invoice_sets: dict[str, set[str]],
) -> str:
    if tracking_id is None or (isinstance(tracking_id, float) and np.isnan(tracking_id)):
        return "INCONNU (tracking vide)"

    tid = str(tracking_id).strip().upper()
    if not tid:
        return "INCONNU (tracking vide)"

    for carrier, ids in invoice_sets.items():
        if tid in ids:
            return carrier

    if re.match(r"^1Z[A-Z0-9]{16}$", tid):
        return "UPS"
    if re.match(r"^1Z", tid):
        return "UPS"
    if re.match(r"^6A[0-9A-Z]+$", tid):
        return "La Poste"
    if re.match(r"^(XS|XA|XR|XW)[A-Z0-9]+FR$", tid):
        return "Chronopost"
    if re.match(r"^Z8[0-9]+$", tid):
        return "Colis Privé"
    if re.match(r"^1C[0-9]+$", tid):
        return "Colis Privé"
    if re.match(r"^CP[0-9A-Z]+$", tid):
        return "Colis Privé"
    if re.match(r"^Q013[0-9]+$", tid):
        return "Postes Canada"
    if re.match(r"^[0-9]{15,22}$", tid):
        return "FedEx"
    if re.match(r"^[0-9]{10}$", tid) and tid.startswith("4"):
        return "DHL"
    if re.match(r"^[0-9]{8,9}$", tid):
        return "Colis Privé"
    if re.match(r"^[0-9]{12}$", tid):
        return "DHL EXPRESS"
    if re.match(r"^MY[A-Z0-9]+$", tid) or "DELIVENGO" in tid:
        return "My Delivengo"

    return "INCONNU (pattern non reconnu)"


def analyze_carriers(
    data_dir: Path,
    warehouse_dir: Path,
    schema: dict[str, dict],
) -> dict:
    """Points 2, 3, 7 — transporteurs, Colis Privé, Postes Canada."""
    package_info = schema.get("package.csv", {})
    package_path: Path = package_info["path"]
    native_col = package_info.get("carrier_column")

    carrier_counts: Counter[str] = Counter()
    carrier_source = "colonne native"

    colis_prive_total = 0
    colis_prive_cost_filled = 0
    colis_prive_cost_null_or_zero = 0

    postes_canada_total = 0
    total_packages = 0

    invoice_sets = load_invoice_tracking_sets(warehouse_dir)

    cost_col = "shipping_cost_eur"
    usecols = ["tracking_id", cost_col]
    if native_col:
        usecols = [native_col, cost_col]

    dtype = FILES["package.csv"]["dtype"].copy()
    if native_col:
        dtype[native_col] = "string"

    for chunk in pd.read_csv(
        package_path,
        usecols=usecols,
        dtype=dtype,
        chunksize=FILES["package.csv"]["chunksize"],
        low_memory=False,
    ):
        total_packages += len(chunk)

        if native_col:
            labels = chunk[native_col].map(normalize_carrier_label)
        else:
            carrier_source = "inférence via tracking_id (+ factures Colissimo/Chronopost)"
            labels = chunk["tracking_id"].map(
                lambda x: infer_carrier_from_tracking(x, invoice_sets)
            )

        for label, count in labels.value_counts().items():
            carrier_counts[label] += int(count)

        cp_mask = labels.str.lower().map(
            lambda x: any(alias in x for alias in COLIS_PRIVE_ALIASES)
            or x == "colis privé"
        )
        cp_chunk = chunk[cp_mask]
        colis_prive_total += len(cp_chunk)
        if len(cp_chunk) > 0:
            costs = pd.to_numeric(cp_chunk[cost_col], errors="coerce")
            filled = costs.notna() & (costs != 0)
            colis_prive_cost_filled += int(filled.sum())
            colis_prive_cost_null_or_zero += int((~filled).sum())

        pc_mask = labels.str.lower().map(
            lambda x: any(alias in x for alias in POSTES_CANADA_ALIASES)
            or x == "postes canada"
        )
        postes_canada_total += int(pc_mask.sum())

    return {
        "native_column": native_col,
        "carrier_source": carrier_source,
        "carrier_counts": carrier_counts,
        "total_packages": total_packages,
        "colis_prive": {
            "total": colis_prive_total,
            "cost_filled": colis_prive_cost_filled,
            "cost_null_or_zero": colis_prive_cost_null_or_zero,
        },
        "postes_canada": {
            "total": postes_canada_total,
            "pct": 100.0 * postes_canada_total / total_packages if total_packages else 0.0,
        },
        "invoice_sets_sizes": {k: len(v) for k, v in invoice_sets.items()},
    }


def analyze_join(data_dir: Path) -> dict:
    """Point 4 — jointure package.order_id ↔ customer_order.id."""
    order_ids: set[int] = set()
    order_path = data_dir / "customer_order.csv"

    for chunk in pd.read_csv(
        order_path,
        usecols=["id"],
        dtype={"id": "Int64"},
        chunksize=FILES["customer_order.csv"]["chunksize"],
    ):
        order_ids.update(chunk["id"].dropna().astype(int).tolist())

    package_order_ids: set[int] = set()
    orphan_package_orders: Counter[int] = Counter()
    total_packages = 0
    package_ids_per_order: Counter[int] = Counter()

    package_path = data_dir / "package.csv"
    for chunk in pd.read_csv(
        package_path,
        usecols=["order_id"],
        dtype={"order_id": "Int64"},
        chunksize=FILES["package.csv"]["chunksize"],
    ):
        total_packages += len(chunk)
        for oid in chunk["order_id"].dropna().astype(int):
            package_order_ids.add(oid)
            package_ids_per_order[oid] += 1
            if oid not in order_ids:
                orphan_package_orders[oid] += 1

    orders_without_package = order_ids - package_order_ids
    orders_with_package = order_ids & package_order_ids
    multi_package_orders = sum(1 for c in package_ids_per_order.values() if c > 1)

    sample_orphans = list(orphan_package_orders.keys())[:10]
    sample_no_pkg = list(orders_without_package)[:10]

    return {
        "customer_order_count": len(order_ids),
        "package_count": total_packages,
        "distinct_package_order_ids": len(package_order_ids),
        "orphan_package_rows": sum(orphan_package_orders.values()),
        "distinct_orphan_order_ids": len(orphan_package_orders),
        "orders_without_package": len(orders_without_package),
        "orders_with_package": len(orders_with_package),
        "multi_package_orders": multi_package_orders,
        "order_id_type_package": "Int64 (entier nullable pandas)",
        "order_id_type_customer_order": "Int64 (entier nullable pandas)",
        "sample_orphan_order_ids": sample_orphans,
        "sample_orders_without_package": sample_no_pkg,
    }


def analyze_tracking_by_carrier(
    data_dir: Path,
    warehouse_dir: Path,
    schema: dict[str, dict],
) -> dict:
    """Point 5 — formats tracking_id par transporteur."""
    package_info = schema["package.csv"]
    native_col = package_info.get("carrier_column")
    invoice_sets = load_invoice_tracking_sets(warehouse_dir)

    length_by_carrier: dict[str, Counter[int]] = defaultdict(Counter)
    pattern_by_carrier: dict[str, Counter[str]] = defaultdict(Counter)
    samples_by_carrier: dict[str, list[str]] = defaultdict(list)
    empty_tracking = 0
    total = 0

    usecols = ["tracking_id"]
    dtype = {"tracking_id": "string"}
    if native_col:
        usecols.append(native_col)
        dtype[native_col] = "string"

    def classify_pattern(tid: str) -> str:
        t = tid.upper()
        if re.match(r"^6A", t):
            return "6A…"
        if re.match(r"^1Z", t):
            return "1Z…"
        if re.match(r"^Z8", t):
            return "Z8…"
        if re.match(r"^1C", t):
            return "1C…"
        if re.match(r"^[0-9]+$", t):
            return f"NUM({len(t)})"
        return f"OTHER({t[:4]}…)"

    for chunk in pd.read_csv(
        package_info["path"],
        usecols=usecols,
        dtype=dtype,
        chunksize=FILES["package.csv"]["chunksize"],
    ):
        total += len(chunk)
        tracking = chunk["tracking_id"].fillna("").astype(str).str.strip()
        empty_tracking += int((tracking == "").sum())

        if native_col:
            carriers = chunk[native_col].map(normalize_carrier_label).fillna("INCONNU")
        else:
            carriers = tracking.map(lambda x: infer_carrier_from_tracking(x, invoice_sets))

        lengths = tracking.str.len()
        for carrier, length, tid in zip(carriers, lengths, tracking):
            if not tid:
                carrier = "INCONNU (tracking vide)"
            length_by_carrier[carrier][int(length)] += 1
            if tid:
                pat = classify_pattern(tid)
                pattern_by_carrier[carrier][pat] += 1
                if len(samples_by_carrier[carrier]) < 3:
                    samples_by_carrier[carrier].append(tid)

    focus_carriers = ["Colis Privé", "UPS", "La Poste", "Chronopost", "Postes Canada"]
    focus_summary = {}
    for carrier in focus_carriers:
        if carrier in length_by_carrier or carrier in pattern_by_carrier:
            focus_summary[carrier] = {
                "lengths": length_by_carrier[carrier].most_common(5),
                "patterns": pattern_by_carrier[carrier].most_common(5),
                "samples": samples_by_carrier.get(carrier, []),
            }

    return {
        "total": total,
        "empty_tracking": empty_tracking,
        "length_by_carrier_top": {
            c: cnt.most_common(5)
            for c, cnt in sorted(
                length_by_carrier.items(),
                key=lambda x: sum(x[1].values()),
                reverse=True,
            )[:12]
        },
        "pattern_by_carrier_top": {
            c: cnt.most_common(5)
            for c, cnt in sorted(
                pattern_by_carrier.items(),
                key=lambda x: sum(x[1].values()),
                reverse=True,
            )[:12]
        },
        "focus_carriers": focus_summary,
        "inference_used": native_col is None,
    }


def analyze_gross_profit(data_dir: Path, sample_size: int = 1000) -> dict:
    """Point 6 — comparaison formule demandée vs gross_profit_eur."""
    path = data_dir / "customer_order.csv"
    usecols = [
        "id",
        "state",
        "order_amount_eur",
        "product_cost_eur",
        "total_shipping_cost_to_delivery_country_eur",
        "shipping_fee_eur",
        "gross_profit_eur",
        "gross_margin",
    ]

    eligible_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        path,
        usecols=usecols,
        chunksize=FILES["customer_order.csv"]["chunksize"],
        low_memory=False,
    ):
        for col in usecols[2:]:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")
        mask = (
            chunk["gross_profit_eur"].notna()
            & chunk["order_amount_eur"].notna()
            & (chunk["order_amount_eur"] > 0)
        )
        if mask.any():
            eligible_parts.append(chunk.loc[mask, usecols])

    if not eligible_parts:
        return {"error": "aucune ligne éligible avec gross_profit_eur renseigné"}

    eligible = pd.concat(eligible_parts, ignore_index=True)
    if len(eligible) > sample_size:
        sample = eligible.sample(n=sample_size, random_state=42)
    else:
        sample = eligible

    sample = sample.copy()
    sample["calc_user"] = (
        sample["order_amount_eur"]
        - sample["product_cost_eur"].fillna(0)
        - sample["total_shipping_cost_to_delivery_country_eur"].fillna(0)
    )
    sample["diff"] = (sample["calc_user"] - sample["gross_profit_eur"]).abs()
    sample["match_001"] = sample["diff"] <= 0.01

    alt = (
        sample["order_amount_eur"]
        - sample["product_cost_eur"].fillna(0)
        - sample["shipping_fee_eur"].fillna(0)
    )
    alt_diff = (alt - sample["gross_profit_eur"]).abs()

    return {
        "eligible_rows": len(eligible),
        "sample_size": len(sample),
        "matches_user_formula": int(sample["match_001"].sum()),
        "match_rate_user_formula": 100.0 * sample["match_001"].mean(),
        "median_diff_user": float(sample["diff"].median()),
        "mean_diff_user": float(sample["diff"].mean()),
        "max_diff_user": float(sample["diff"].max()),
        "alt_formula": "order_amount_eur - product_cost_eur - shipping_fee_eur",
        "alt_matches_001": int((alt_diff <= 0.01).sum()),
        "alt_match_rate": 100.0 * (alt_diff <= 0.01).mean(),
        "sample_mismatches": sample.loc[~sample["match_001"], [
            "id", "order_amount_eur", "product_cost_eur",
            "total_shipping_cost_to_delivery_country_eur", "gross_profit_eur", "calc_user", "diff",
        ]].head(5).to_dict("records"),
    }


def print_schema_report(schema: dict[str, dict]) -> None:
    hr("1. SCHÉMA DES FICHIERS")
    for filename, info in schema.items():
        sub(filename)
        if "error" in info:
            print(f"  ERREUR: {info['error']}")
            continue
        print(f"  Chemin      : {info['path']}")
        print(f"  Lignes      : {fmt_int(info['rows'])}")
        print(f"  Colonnes ({len(info['columns'])}):")
        for col in info["columns"]:
            nulls = info["nulls"].get(col, 0)
            pct = 100.0 * nulls / info["rows"] if info["rows"] else 0
            print(
                f"    - {col:<45} type={info['types'][col]:<16} "
                f"nulls={fmt_int(nulls)} ({pct:.4f}%)"
            )
        if info["carrier_column"]:
            print(f"  Colonne transporteur détectée : {info['carrier_column']}")
        else:
            print("  Colonne transporteur détectée : aucune")


def print_carrier_report(carrier_info: dict, schema: dict[str, dict]) -> None:
    hr("2. TRANSPORTEURS DANS package.csv")
    native = carrier_info["native_column"]
    if native:
        print(f"Colonne utilisée : '{native}' (native)")
    else:
        print("Aucune colonne transporteur/provider trouvée dans package.csv.")
        print(f"Méthode appliquée : {carrier_info['carrier_source']}")
        print(
            "Sets factures chargés pour matching : "
            + ", ".join(
                f"{k}={fmt_int(v)}"
                for k, v in carrier_info["invoice_sets_sizes"].items()
            )
        )
        other_carrier_cols = []
        for fname, info in schema.items():
            if fname == "package.csv" or "error" in info:
                continue
            if info.get("carrier_column"):
                other_carrier_cols.append(f"{fname} -> {info['carrier_column']}")
        if other_carrier_cols:
            print("Colonnes transporteur trouvées ailleurs :")
            for line in other_carrier_cols:
                print(f"  - {line}")
        else:
            print("Aucune colonne transporteur trouvée dans les 4 fichiers backend.")

    sub("Répartition (triée par volume)")
    total = carrier_info["total_packages"]
    for carrier, count in carrier_info["carrier_counts"].most_common():
        print(f"  {carrier:<35} {fmt_int(count):>12}  ({fmt_pct(count, total)})")

    expected = [
        "DHL",
        "FedEx",
        "UPS",
        "UPS Standard",
        "DHL EXPRESS",
        "Colis Privé",
        "My Delivengo",
        "Chronopost",
        "Postes Canada",
        "La Poste",
    ]
    found = {c.lower() for c in carrier_info["carrier_counts"]}
    missing = [e for e in expected if e.lower() not in found]
    if missing:
        sub("Transporteurs attendus non trouvés tels quels")
        for m in missing:
            print(f"  - {m}")


def print_colis_prive_report(colis_info: dict) -> None:
    hr("3. COLIS PRIVÉ — complétude shipping_cost_eur")
    total = colis_info["total"]
    filled = colis_info["cost_filled"]
    empty = colis_info["cost_null_or_zero"]
    print(f"Lignes Colis Privé (filtrées)     : {fmt_int(total)}")
    print(f"  Coût renseigné (non null, ≠ 0)   : {fmt_int(filled)}  ({fmt_pct(filled, total)})")
    print(f"  Coût null ou 0                  : {fmt_int(empty)}  ({fmt_pct(empty, total)})")
    if total == 0:
        print("  Note : aucune ligne Colis Privé identifiée — vérifier colonne transporteur ou règles d'inférence.")


def print_join_report(join_info: dict) -> None:
    hr("4. CLÉ DE JOINTURE package.order_id ↔ customer_order.id")
    print(f"Lignes package.csv                         : {fmt_int(join_info['package_count'])}")
    print(f"order_id distincts dans package.csv        : {fmt_int(join_info['distinct_package_order_ids'])}")
    print(f"id distincts dans customer_order.csv       : {fmt_int(join_info['customer_order_count'])}")
    print()
    print(f"order_id dans package SANS match dans customer_order.id :")
    print(f"  - lignes package orphelines              : {fmt_int(join_info['orphan_package_rows'])}")
    print(f"  - order_id distincts orphelins           : {fmt_int(join_info['distinct_orphan_order_ids'])}")
    print()
    print(f"id dans customer_order SANS package associé : {fmt_int(join_info['orders_without_package'])}")
    print(f"id dans customer_order AVEC package         : {fmt_int(join_info['orders_with_package'])}")
    print(f"commandes avec plusieurs packages           : {fmt_int(join_info['multi_package_orders'])}")
    print()
    print(f"Type package.order_id        : {join_info['order_id_type_package']}")
    print(f"Type customer_order.id       : {join_info['order_id_type_customer_order']}")
    print("Préfixes/format              : entiers numériques, pas de préfixe texte détecté")
    if join_info["sample_orphan_order_ids"]:
        sub("Exemples order_id orphelins (package sans customer_order)")
        print("  " + ", ".join(str(x) for x in join_info["sample_orphan_order_ids"]))
    if join_info["sample_orders_without_package"]:
        sub("Exemples customer_order.id sans package")
        print("  " + ", ".join(str(x) for x in join_info["sample_orders_without_package"]))


def print_tracking_report(tracking_info: dict) -> None:
    hr("5. TRACKING_ID — formats par transporteur")
    print(f"Total lignes package          : {fmt_int(tracking_info['total'])}")
    print(f"tracking_id vide/null         : {fmt_int(tracking_info['empty_tracking'])}")
    if tracking_info["inference_used"]:
        print("Note : transporteur inféré — patterns ci-dessous sont indicatifs.")

    sub("Longueurs les plus fréquentes (top transporteurs)")
    for carrier, lengths in tracking_info["length_by_carrier_top"].items():
        lens = ", ".join(f"{l}:{fmt_int(n)}" for l, n in lengths)
        print(f"  {carrier:<30} {lens}")

    sub("Patterns dominants (top transporteurs)")
    for carrier, patterns in tracking_info["pattern_by_carrier_top"].items():
        pats = ", ".join(f"{p}:{fmt_int(n)}" for p, n in patterns)
        print(f"  {carrier:<30} {pats}")

    if tracking_info["focus_carriers"]:
        sub("Focus Colis Privé et transporteurs clés")
        for carrier, detail in tracking_info["focus_carriers"].items():
            print(f"  [{carrier}]")
            print(f"    Exemples   : {detail['samples']}")
            print(f"    Longueurs  : {detail['lengths']}")
            print(f"    Patterns   : {detail['patterns']}")


def print_gross_profit_report(gp_info: dict) -> None:
    hr("6. MARGE EXISTANTE — validation formule")
    if "error" in gp_info:
        print(f"  ERREUR: {gp_info['error']}")
        return

    print("Formule testée (demandée) :")
    print("  gross_profit_calc = order_amount_eur - product_cost_eur - total_shipping_cost_to_delivery_country_eur")
    print()
    print(f"Lignes éligibles (gross_profit_eur renseigné, order_amount_eur > 0) : {fmt_int(gp_info['eligible_rows'])}")
    print(f"Échantillon analysé                                               : {fmt_int(gp_info['sample_size'])}")
    print(f"Correspondances à ±0,01 €                                         : {fmt_int(gp_info['matches_user_formula'])} / {fmt_int(gp_info['sample_size'])} ({gp_info['match_rate_user_formula']:.4f}%)")
    print(f"Écart médian                                                      : {gp_info['median_diff_user']:.6f} €")
    print(f"Écart moyen                                                       : {gp_info['mean_diff_user']:.6f} €")
    print(f"Écart max                                                         : {gp_info['max_diff_user']:.6f} €")
    print()
    if gp_info["match_rate_user_formula"] < 50:
        print("Conclusion : la formule demandée NE correspond PAS de façon fiable à gross_profit_eur.")
        print(f"Formule alternative testée : {gp_info['alt_formula']}")
        print(
            f"  Correspondances ±0,01 € : {fmt_int(gp_info['alt_matches_001'])} / {fmt_int(gp_info['sample_size'])} "
            f"({gp_info['alt_match_rate']:.4f}%)"
        )
    else:
        print("Conclusion : la formule demandée correspond globalement à gross_profit_eur.")

    if gp_info["sample_mismatches"]:
        sub("Exemples d'écarts (formule demandée)")
        for row in gp_info["sample_mismatches"]:
            print(
                f"  id={row['id']} | amount={fmt_num(row['order_amount_eur'])} "
                f"prod={fmt_num(row['product_cost_eur'])} "
                f"ship_country={fmt_num(row['total_shipping_cost_to_delivery_country_eur'])} "
                f"gross={fmt_num(row['gross_profit_eur'])} "
                f"calc={fmt_num(row['calc_user'])} "
                f"Δ={fmt_num(row['diff'])}"
            )


def print_postes_canada_report(postes_info: dict, total_packages: int) -> None:
    hr("7. POSTES CANADA — volume global")
    print(f"Lignes package (Postes Canada) : {fmt_int(postes_info['total'])}")
    print(f"Total lignes package.csv       : {fmt_int(total_packages)}")
    print(f"Part du volume total           : {postes_info['pct']:.4f}%")


def main() -> int:
    # Console Windows : éviter les erreurs d'encodage sur caractères accentués
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Analyse exploratoire données backend Lireka")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Dossier contenant les 4 CSV backend",
    )
    parser.add_argument(
        "--warehouse-dir",
        type=Path,
        default=WAREHOUSE_DIR,
        help="Racine Power_BI_Datawarehouse (factures pour matching tracking)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000,
        help="Taille échantillon pour le test marge (point 6)",
    )
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    warehouse_dir = args.warehouse_dir.resolve()

    print()
    print("RAPPORT D'ANALYSE — Données Backend Lireka")
    print(f"Dossier données : {data_dir}")
    print(f"Dossier entrepôt: {warehouse_dir}")

    schema = analyze_schema(data_dir)
    print_schema_report(schema)

    carrier_info = analyze_carriers(data_dir, warehouse_dir, schema)
    print_carrier_report(carrier_info, schema)
    print_colis_prive_report(carrier_info["colis_prive"])

    join_info = analyze_join(data_dir)
    print_join_report(join_info)

    tracking_info = analyze_tracking_by_carrier(data_dir, warehouse_dir, schema)
    print_tracking_report(tracking_info)

    gp_info = analyze_gross_profit(data_dir, sample_size=args.sample_size)
    print_gross_profit_report(gp_info)

    print_postes_canada_report(carrier_info["postes_canada"], carrier_info["total_packages"])

    print()
    print("=" * 72)
    print("FIN DU RAPPORT")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
