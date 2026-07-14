"""Audit Power_BI_Datawarehouse — données brutes (relançable)."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"
BACKEND = ROOT / "Données_Backend"
PYTHON = Path(r"C:\Users\Otmane\AppData\Local\Programs\Python\Python312\python.exe")


def fmt_dt(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_dates(series: pd.Series) -> pd.Series:
    s = series.dropna().astype(str).str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        d = pd.to_datetime(s, format=fmt, errors="coerce")
        if d.notna().sum() > len(s) * 0.5:
            return d
    return pd.to_datetime(s, errors="coerce", dayfirst=True)


def detect_date_col(cols: list[str]) -> str | None:
    for c in cols:
        cl = c.lower()
        if "date" in cl or cl in ("origin_created", "change_to_final_state_at"):
            return c
    return None


def infer_carrier(tid: object) -> str:
    if tid is None or (isinstance(tid, float) and pd.isna(tid)):
        return "INCONNU"
    t = str(tid).strip().upper()
    if not t:
        return "INCONNU"
    if t.startswith("1Z"):
        return "UPS"
    if len(t) == 13 and t.startswith("6A"):
        return "La Poste"
    if t.startswith("Q013"):
        return "Postes Canada"
    if len(t) == 13 and t[:2] in ("XW", "XA", "XS", "XR"):
        return "Chronopost"
    if t.isdigit() and len(t) == 18:
        return "FedEx"
    if t.isdigit() and len(t) == 12:
        return "DHL EXPRESS"
    if t.startswith("Z8") or t.startswith("1C"):
        return "Colis Privé"
    if t.isdigit() and len(t) in (8, 9):
        return "Colis Privé"
    if t.isdigit() and len(t) == 10:
        return "DHL"
    if "DELIVENGO" in t or t.startswith("MY"):
        return "My Delivengo"
    return "INCONNU"


def inventory() -> tuple[list[dict], dict, list[dict]]:
    all_files: list[dict] = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_file():
            st = p.stat()
            all_files.append(
                {
                    "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                    "size": st.st_size,
                    "mtime": fmt_dt(st.st_mtime),
                }
            )

    csv_analysis: dict = {}
    csv_files = [f for f in all_files if f["path"].lower().endswith(".csv")]

    for cf in csv_files:
        p = ROOT / cf["path"]
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                first = f.readline()
            sep = ";" if first.count(";") > first.count(",") else ","
            with open(p, "rb") as f:
                line_count = sum(1 for _ in f) - 1
            df_head = pd.read_csv(p, sep=sep, nrows=5, encoding="utf-8", on_bad_lines="skip")
            cols = list(df_head.columns)
            date_col = detect_date_col(cols)
            period = None
            if date_col and line_count > 0:
                mins, maxs = [], []
                for chunk in pd.read_csv(
                    p,
                    sep=sep,
                    usecols=[date_col],
                    chunksize=50_000,
                    encoding="utf-8",
                    on_bad_lines="skip",
                    low_memory=False,
                ):
                    d = parse_dates(chunk[date_col])
                    if d.notna().any():
                        mins.append(d.min())
                        maxs.append(d.max())
                if mins:
                    period = {
                        "min": str(min(mins))[:10],
                        "max": str(max(maxs))[:10],
                        "col": date_col,
                    }
            csv_analysis[cf["path"]] = {
                "lines": line_count,
                "columns": cols,
                "sep": sep,
                "period": period,
                "size": cf["size"],
                "mtime": cf["mtime"],
            }
        except Exception as e:
            csv_analysis[cf["path"]] = {"error": str(e), "size": cf["size"], "mtime": cf["mtime"]}

    recap_groups: dict[str, list] = defaultdict(list)
    for cf in csv_files:
        name = Path(cf["path"]).name
        if "récap" in name.lower() or "recap" in name.lower():
            prefix = re.sub(r"_au_.*", "", name, flags=re.I)
            prefix = re.sub(r"\.csv$", "", prefix, flags=re.I)
            recap_groups[prefix].append(cf)

    duplicates: list[dict] = []
    for prefix, files in recap_groups.items():
        if len(files) > 1:
            hashes: dict[str, list] = {}
            for f in files:
                p = ROOT / f["path"]
                h = sha256_file(p)
                hashes.setdefault(h, []).append(f["path"])
            entry = {
                "prefix": prefix,
                "files": [f["path"] for f in files],
                "sha256_groups": hashes,
                "identical_byte_for_byte": len(hashes) == 1,
            }
            periods = []
            for f in files:
                a = csv_analysis.get(f["path"], {})
                if a.get("period"):
                    periods.append((f["path"], a["period"]["min"], a["period"]["max"]))
            entry["periods"] = periods
            duplicates.append(entry)

    return all_files, csv_analysis, duplicates


def grain_analysis() -> dict:
    ids_co: Counter = Counter()
    rows_co = 0
    for chunk in pd.read_csv(
        BACKEND / "customer_order.csv",
        usecols=["id"],
        dtype={"id": "Int64"},
        chunksize=100_000,
    ):
        rows_co += len(chunk)
        for v in chunk["id"].dropna():
            ids_co[int(v)] += 1
    dup_co = {k: v for k, v in ids_co.items() if v > 1}

    ids_pkg: Counter = Counter()
    track_pkg: Counter = Counter()
    rows_pkg = 0
    for chunk in pd.read_csv(
        BACKEND / "package.csv",
        usecols=["id", "tracking_id"],
        dtype={"id": "Int64", "tracking_id": "string"},
        chunksize=100_000,
    ):
        rows_pkg += len(chunk)
        for v in chunk["id"].dropna():
            ids_pkg[int(v)] += 1
        for v in chunk["tracking_id"].dropna().astype(str).str.strip().str.upper():
            if v:
                track_pkg[v] += 1
    dup_id_pkg = {k: v for k, v in ids_pkg.items() if v > 1}
    dup_track = {k: v for k, v in track_pkg.items() if v > 1}

    return {
        "customer_order": {
            "rows": rows_co,
            "distinct_id": len(ids_co),
            "unique": rows_co == len(ids_co),
            "dup_keys_count": len(dup_co),
            "dup_rows_total": sum(v - 1 for v in dup_co.values()),
            "top_dups": sorted(dup_co.items(), key=lambda x: -x[1])[:5],
        },
        "package": {
            "rows": rows_pkg,
            "distinct_id": len(ids_pkg),
            "id_unique": rows_pkg == len(ids_pkg),
            "dup_id_keys": len(dup_id_pkg),
            "dup_id_rows": sum(v - 1 for v in dup_id_pkg.values()),
            "top_dup_ids": sorted(dup_id_pkg.items(), key=lambda x: -x[1])[:5],
            "distinct_tracking_id": len(track_pkg),
            "tracking_unique": rows_pkg == len(track_pkg),
            "dup_tracking_keys": len(dup_track),
            "dup_tracking_rows": sum(v - 1 for v in dup_track.values()),
            "top_dup_tracking": sorted(dup_track.items(), key=lambda x: -x[1])[:5],
        },
    }


def margin_coverage() -> dict:
    co_cols = list(pd.read_csv(BACKEND / "customer_order.csv", nrows=0).columns)
    item_cols = list(pd.read_csv(BACKEND / "customer_order_item.csv", nrows=0).columns)
    pkg_cols = list(pd.read_csv(BACKEND / "package.csv", nrows=0).columns)
    all_file_cols = {
        "customer_order.csv": co_cols,
        "customer_order_item.csv": item_cols,
        "package.csv": pkg_cols,
    }
    posts = {
        "Revenue": [("customer_order.csv", "order_amount_eur")],
        "Shipping revenue": [("customer_order.csv", "shipping_fee_eur")],
        "COGS": [
            ("customer_order.csv", "product_cost_eur"),
            ("customer_order_item.csv", "product_cost_eur"),
        ],
        "Transport inbound": [
            ("customer_order.csv", "inbound_transportation_cost_eur"),
            ("customer_order_item.csv", "freight_in_cost_eur"),
        ],
        "Transport outbound": [
            ("customer_order.csv", "total_shipping_cost_to_delivery_country_eur"),
            ("customer_order_item.csv", "shipping_cost_to_delivery_country_eur"),
            ("package.csv", "shipping_cost_eur"),
        ],
        "Duties/taxes": [
            ("customer_order.csv", "duties_and_taxes_eur"),
            ("package.csv", "duties_taxes_eur"),
        ],
        "Commissions marketplace": [("customer_order.csv", "marketplace_fees_eur")],
        "Fournitures expédition": [
            ("customer_order.csv", "total_shipping_supplies_eur"),
            ("customer_order_item.csv", "shipping_supplies_cost_eur"),
            ("package.csv", "shipping_supply_cost_eur"),
        ],
    }
    out = {}
    for post, candidates in posts.items():
        found = [(f, c) for f, c in candidates if f in all_file_cols and c in all_file_cols[f]]
        out[post] = {"columns": found, "absent": not bool(found)}
    return out


def carrier_analysis() -> dict:
    carrier_counts: Counter = Counter()
    cp_total = cp_cost = cp_zero = 0
    delivengo = 0
    rows_pkg = 0
    for chunk in pd.read_csv(
        BACKEND / "package.csv",
        usecols=["tracking_id", "shipping_cost_eur"],
        dtype={"tracking_id": "string"},
        chunksize=100_000,
    ):
        rows_pkg += len(chunk)
        carriers = chunk["tracking_id"].map(infer_carrier)
        for c, n in carriers.value_counts().items():
            carrier_counts[c] += n
        t = chunk["tracking_id"].fillna("").astype(str).str.upper()
        delivengo += int(t.str.contains("DELIVENGO|MYDELIV").sum())
        cp = chunk[carriers == "Colis Privé"]
        cp_total += len(cp)
        costs = pd.to_numeric(cp["shipping_cost_eur"], errors="coerce")
        cp_cost += int((costs.notna() & (costs != 0)).sum())
        cp_zero += int((costs.isna() | (costs == 0)).sum())

    cp_dir = ROOT / "Dashboards_transporteurs" / "COLIS PRIVE Dashboard Power BI"
    cp_invoice = (
        [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted(cp_dir.rglob("*.csv"))]
        if cp_dir.exists()
        else []
    )

    pc_invoice = [
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in ROOT.rglob("*.csv")
        if "canada" in str(p).lower() or "postes" in str(p).lower()
    ]

    return {
        "counts": dict(carrier_counts.most_common()),
        "total_packages": rows_pkg,
        "mismatches": {
            "DHL EXPRESS (inféré)": carrier_counts.get("DHL EXPRESS", 0),
            "UPS (inféré, pas UPS Standard)": carrier_counts.get("UPS", 0),
            "My Delivengo (pattern DELIVENGO)": delivengo,
            "UPS Standard tel quel": 0,
            "My Delivengo tel quel": 0,
        },
        "colis_prive": {
            "total": cp_total,
            "backend_cost_filled": cp_cost,
            "backend_cost_null_or_zero": cp_zero,
            "invoice_csv_count": len(cp_invoice),
            "invoice_files_sample": cp_invoice[:15],
        },
        "postes_canada": {
            "volume": carrier_counts.get("Postes Canada", 0),
            "pct": round(100 * carrier_counts.get("Postes Canada", 0) / rows_pkg, 4) if rows_pkg else 0,
            "invoice_files": pc_invoice,
        },
    }


def join_analysis() -> dict:
    pkg_tracking: set[str] = set()
    for chunk in pd.read_csv(
        BACKEND / "package.csv",
        usecols=["tracking_id"],
        dtype={"tracking_id": "string"},
        chunksize=100_000,
    ):
        for v in chunk["tracking_id"].dropna().astype(str).str.strip().str.upper():
            if v:
                pkg_tracking.add(v)

    invoice_rows: list[dict] = []
    for subdir in ("COLISSIMO Dashboard PowerBI", "CHRONOPOST Dashboard PowerBI"):
        d = ROOT / "Dashboards_transporteurs" / subdir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.csv")):
            try:
                df = pd.read_csv(p, sep=";", dtype=str, encoding="latin-1")
            except Exception:
                df = pd.read_csv(p, sep=";", dtype=str, encoding="utf-8")
            col = next((c for c in df.columns if "colis" in c.lower()), None)
            cost_col = next((c for c in df.columns if "TOTAL" in c.upper() and "HT" in c.upper()), None)
            if not col:
                continue
            for _, r in df.iterrows():
                t = str(r[col]).strip().upper() if pd.notna(r[col]) else ""
                if t:
                    invoice_rows.append(
                        {
                            "tracking": t,
                            "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                            "cost": r.get(cost_col) if cost_col else None,
                        }
                    )

    matched = [r for r in invoice_rows if r["tracking"] in pkg_tracking]
    unmatched = [r for r in invoice_rows if r["tracking"] not in pkg_tracking]
    inv_tracking = {r["tracking"] for r in invoice_rows}
    pkg_in_inv = sum(1 for t in pkg_tracking if t in inv_tracking)

    return {
        "invoice_lines": len(invoice_rows),
        "invoice_distinct_tracking": len(inv_tracking),
        "invoice_matched_to_package": len(matched),
        "invoice_match_rate_pct": round(100 * len(matched) / len(invoice_rows), 4) if invoice_rows else None,
        "invoice_unmatched_sample": list({r["tracking"] for r in unmatched})[:10],
        "package_distinct_tracking": len(pkg_tracking),
        "package_matched_to_invoice": pkg_in_inv,
        "package_match_rate_pct": round(100 * pkg_in_inv / len(pkg_tracking), 4) if pkg_tracking else None,
        "package_unmatched_sample": [t for t in list(pkg_tracking) if t not in inv_tracking][:10],
    }


def quality_analysis() -> dict:
    q_pkg = {
        "tracking_id_null": 0,
        "tracking_id_empty": 0,
        "order_id_null": 0,
        "shipping_cost_null": 0,
        "shipping_cost_zero": 0,
        "rows": 0,
    }
    for chunk in pd.read_csv(
        BACKEND / "package.csv",
        usecols=["tracking_id", "order_id", "shipping_cost_eur"],
        dtype={"tracking_id": "string", "order_id": "Int64"},
        chunksize=100_000,
    ):
        q_pkg["rows"] += len(chunk)
        q_pkg["tracking_id_null"] += int(chunk["tracking_id"].isna().sum())
        q_pkg["tracking_id_empty"] += int(
            chunk["tracking_id"].fillna("").astype(str).str.strip().eq("").sum()
        )
        q_pkg["order_id_null"] += int(chunk["order_id"].isna().sum())
        costs = pd.to_numeric(chunk["shipping_cost_eur"], errors="coerce")
        q_pkg["shipping_cost_null"] += int(costs.isna().sum())
        q_pkg["shipping_cost_zero"] += int((costs == 0).sum())

    q_co = {"destination_country_null": 0, "destination_country_empty": 0, "rows": 0}
    for chunk in pd.read_csv(
        BACKEND / "customer_order.csv",
        usecols=["destination_country"],
        dtype={"destination_country": "string"},
        chunksize=100_000,
    ):
        q_co["rows"] += len(chunk)
        q_co["destination_country_null"] += int(chunk["destination_country"].isna().sum())
        q_co["destination_country_empty"] += int(
            chunk["destination_country"].fillna("").astype(str).str.strip().eq("").sum()
        )

    join = join_analysis()
    inv_cost_null = sum(1 for r in join.get("_invoice_rows", []))

    return {
        "package.csv": q_pkg,
        "customer_order.csv": q_co,
        "code_pays_proxy": {
            "null_or_empty_destination_country": q_co["destination_country_null"]
            + q_co["destination_country_empty"],
            "note": "code_pays dérivé de destination_country en modèle ; pas de colonne code_pays dans les CSV bruts",
        },
    }


def main() -> None:
    all_files, csv_analysis, duplicates = inventory()
    grain = grain_analysis()
    margin = margin_coverage()
    carriers = carrier_analysis()
    join = join_analysis()
    quality = quality_analysis()

    # invoice cost quality from join files
    invoice_rows = []
    for subdir in ("COLISSIMO Dashboard PowerBI", "CHRONOPOST Dashboard PowerBI"):
        d = ROOT / "Dashboards_transporteurs" / subdir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.csv")):
            try:
                df = pd.read_csv(p, sep=";", dtype=str, encoding="latin-1")
            except Exception:
                df = pd.read_csv(p, sep=";", dtype=str, encoding="utf-8")
            cost_col = next((c for c in df.columns if "TOTAL" in c.upper() and "HT" in c.upper()), None)
            col = next((c for c in df.columns if "colis" in c.lower()), None)
            if not col:
                continue
            for _, r in df.iterrows():
                invoice_rows.append(r.get(cost_col) if cost_col else None)
    inv_null = sum(1 for c in invoice_rows if c is None or str(c).strip() == "")
    inv_zero = 0
    for c in invoice_rows:
        try:
            if float(str(c).replace(",", ".")) == 0:
                inv_zero += 1
        except (ValueError, TypeError):
            pass
    quality["factures_colissimo_chronopost"] = {
        "lines": len(invoice_rows),
        "cost_null_or_empty": inv_null,
        "cost_zero": inv_zero,
    }

    out = {
        "inventory_count": len(all_files),
        "csv_count": sum(1 for f in all_files if f["path"].lower().endswith(".csv")),
        "inventory": all_files,
        "csv_analysis": csv_analysis,
        "duplicates": duplicates,
        "grain": grain,
        "margin_coverage": margin,
        "carriers": carriers,
        "join": join,
        "quality": quality,
    }
    out_path = Path(__file__).parent / "audit_warehouse_output.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
