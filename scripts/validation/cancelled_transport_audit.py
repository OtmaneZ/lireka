"""Audit impact CANCELLED sur fact_transport (Tâche 1)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validation"))

from transport_source_checks import (  # noqa: E402
    assign_source_cout,
    build_packages,
    load_invoices,
    resolve_invoices,
)

BACKEND = ROOT / "Power_BI_Datawarehouse" / "Données_Backend"
OUT = Path(__file__).parent / "cancelled_transport_audit_output.json"


def main() -> None:
    pkg = build_packages()
    invoice_ids = resolve_invoices(load_invoices(), pkg)
    pkg["source_cout"] = assign_source_cout(pkg, invoice_ids)

    co = pd.read_csv(BACKEND / "customer_order.csv", usecols=["id", "state"], dtype=str, low_memory=False)
    cancelled_ids = set(co.loc[co["state"].str.upper() == "CANCELLED", "id"].dropna().astype(int))
    pkg["is_cancelled_order"] = pkg["order_id"].astype(int).isin(cancelled_ids)
    cp = pkg[pkg["is_cancelled_order"]]

    nb_cmd = int(len(co))
    nb_colis = int(len(pkg))
    nb_matched = int(pkg.loc[pkg["source_cout"] == "reel", "order_id"].nunique())

    pkg_wo = pkg[~pkg["is_cancelled_order"]]
    nb_colis_wo = int(len(pkg_wo))
    nb_matched_wo = int(pkg_wo.loc[pkg_wo["source_cout"] == "reel", "order_id"].nunique())

    out = {
        "cancelled_packages_count": int(len(cp)),
        "cancelled_distinct_orders": int(cp["order_id"].nunique()),
        "cout_transport_gt0": int((cp["cout_transport"].notna() & (cp["cout_transport"] > 0)).sum()),
        "cout_transport_eq0": int((cp["cout_transport"] == 0).sum()),
        "cout_transport_null": int(cp["cout_transport"].isna().sum()),
        "sum_cout_transport": round(float(cp["cout_transport"].fillna(0).sum()), 2),
        "cancelled_reel_colis": int((cp["source_cout"] == "reel").sum()),
        "nb_colis_current": nb_colis,
        "nb_colis_without_cancelled": nb_colis_wo,
        "nb_colis_delta": nb_colis - nb_colis_wo,
        "nb_commandes_matchees_current": nb_matched,
        "nb_commandes_matchees_without_cancelled_pkgs": nb_matched_wo,
        "taux_matching_current_pct": round(100 * nb_matched / nb_cmd, 4),
        "taux_matching_without_cancelled_pkgs_pct": round(100 * nb_matched_wo / nb_cmd, 4),
        "taux_matching_delta_pp": round(100 * nb_matched / nb_cmd - 100 * nb_matched_wo / nb_cmd, 4),
        "nb_colis_reel_current": int((pkg["source_cout"] == "reel").sum()),
        "nb_colis_reel_without_cancelled": int((pkg_wo["source_cout"] == "reel").sum()),
        "nb_commandes_total": nb_cmd,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
