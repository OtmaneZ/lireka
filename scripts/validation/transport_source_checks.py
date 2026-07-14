"""Preuves chiffrées avant/après — flag source_cout + mesures matching transport.

Réplique en pandas la logique M/TMDL (CSV bruts non modifiés).
"""
from __future__ import annotations

import os

import json
from pathlib import Path

import pandas as pd

# Fix F-19 : racine de l'entrepôt paramétrable via la variable d'environnement LIREKA_DWH.
ROOT = Path(os.environ.get("LIREKA_DWH", Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"))
BACKEND = ROOT / "Données_Backend"
COL_DIR = ROOT / "Dashboards_transporteurs" / "COLISSIMO Dashboard PowerBI"
CHR_DIR = ROOT / "Dashboards_transporteurs" / "CHRONOPOST Dashboard PowerBI"


def norm(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper()


def infer_carrier(tid: str) -> str:
    t = str(tid).strip().upper() if pd.notna(tid) else ""
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
        return "DHL"
    if t.startswith("Z8") or t.startswith("1C"):
        return "Colis Privé"
    if t.isdigit() and len(t) in (8, 9):
        return "Colis Privé"
    return "INCONNU"


def read_recap(p: Path) -> pd.DataFrame:
    df = pd.read_csv(p, sep=";", dtype=str, encoding="latin-1")
    df.columns = [c.lstrip("\ufeff") for c in df.columns]
    return df


def col_by_hint(columns: list[str], *hints: str) -> str:
    for h in hints:
        for c in columns:
            if h in c.lower():
                return c
    raise KeyError(f"Aucune colonne pour {hints} dans {columns}")


def load_invoices() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for p in sorted(COL_DIR.glob("*.csv")):
        df = read_recap(p)
        suivi = col_by_hint(list(df.columns), "colis")
        tot = col_by_hint(list(df.columns), "total")
        date_col = col_by_hint(list(df.columns), "date")
        part = pd.DataFrame({
            "numero_suivi": norm(df[suivi]),
            "date_facture": pd.to_datetime(df[date_col], dayfirst=True, errors="coerce"),
            "cout_transport": pd.to_numeric(df[tot].astype("string").str.replace(",", ".", regex=False), errors="coerce"),
        })
        rows.append(part)
    for p in sorted(CHR_DIR.glob("*.csv")):
        if p.name == "2026_CHRONOPOST_récap_au_30_juin_2026.csv":
            continue
        df = read_recap(p)
        suivi = col_by_hint(list(df.columns), "colis", "objet")
        tot = col_by_hint(list(df.columns), "total")
        date_col = col_by_hint(list(df.columns), "date")
        part = pd.DataFrame({
            "numero_suivi": norm(df[suivi]),
            "date_facture": pd.to_datetime(df[date_col], dayfirst=True, errors="coerce"),
            "cout_transport": pd.to_numeric(df[tot].astype("string").str.replace(",", ".", regex=False), errors="coerce"),
        })
        rows.append(part)
    inv = pd.concat(rows, ignore_index=True)
    return inv[inv["cout_transport"].notna()].copy()


def resolve_invoices(inv: pd.DataFrame, pkg: pd.DataFrame) -> set[int]:
    """Résolution facture -> id_package par proximité de date (logique M)."""
    co = pd.read_csv(BACKEND / "customer_order.csv", usecols=["id", "origin_created"], dtype=str, low_memory=False)
    co["date_commande"] = pd.to_datetime(co["origin_created"].str.slice(0, 10), errors="coerce")
    pkg2 = pkg[["id_package", "order_id", "numero_suivi"]].copy()
    pkg2["order_id"] = pkg2["order_id"].astype("Int64")
    co["id"] = pd.to_numeric(co["id"], errors="coerce").astype("Int64")
    colis = pkg2.merge(co[["id", "date_commande"]], left_on="order_id", right_on="id", how="left")

    inv2 = inv.reset_index(drop=True).reset_index().rename(columns={"index": "inv_idx"})
    merged = inv2.merge(colis, on="numero_suivi", how="inner")
    if merged.empty:
        return set()
    merged["delta_days"] = (
        (merged["date_commande"] - merged["date_facture"]).abs().dt.total_seconds() / 86400.0
    )
    merged["delta_days"] = merged["delta_days"].fillna(1_000_000_000.0)
    best = merged.sort_values(["inv_idx", "delta_days", "id_package"]).drop_duplicates("inv_idx", keep="first")
    return set(best["id_package"].dropna().astype(int))


def build_packages() -> pd.DataFrame:
    pkg = pd.read_csv(
        BACKEND / "package.csv",
        usecols=["id", "order_id", "tracking_id", "shipping_cost_eur"],
        dtype={"tracking_id": "string"},
        low_memory=False,
    )
    pkg = pkg.rename(columns={"id": "id_package", "shipping_cost_eur": "cout_transport"})
    pkg["numero_suivi"] = norm(pkg["tracking_id"])
    pkg["transporteur"] = pkg["tracking_id"].map(infer_carrier)
    pkg["cout_transport"] = pd.to_numeric(pkg["cout_transport"], errors="coerce")
    return pkg


def assign_source_cout(pkg: pd.DataFrame, invoice_ids: set[int]) -> pd.Series:
    has_inv = pkg["id_package"].isin(invoice_ids)
    cost_ok = pkg["cout_transport"].notna() & (pkg["cout_transport"] != 0)
    out = pd.Series("estime", index=pkg.index, dtype="string")
    out[has_inv] = "reel"
    out[~has_inv & ~cost_ok] = "non_disponible"
    return out


def task1(pkg: pd.DataFrame, invoice_ids: set[int]) -> dict:
    pkg = pkg.copy()
    pkg["source_cout"] = assign_source_cout(pkg, invoice_ids)
    by_source = pkg["source_cout"].value_counts().to_dict()
    by_carrier = (
        pkg.groupby(["transporteur", "source_cout"], dropna=False)
        .size()
        .unstack(fill_value=0)
        .astype(int)
        .to_dict(orient="index")
    )
    cp = pkg[pkg["transporteur"] == "Colis Privé"]
    pc = pkg[pkg["transporteur"] == "Postes Canada"]
    return {
        "colonne_ajoutee": "fact_transport.source_cout",
        "valeurs": ["reel", "estime", "non_disponible"],
        "repartition_globale": {k: int(v) for k, v in by_source.items()},
        "total_colis": int(len(pkg)),
        "somme_3_categories": int(by_source.get("reel", 0) + by_source.get("estime", 0) + by_source.get("non_disponible", 0)),
        "colis_prive": {
            "total": int(len(cp)),
            "reel": int((cp["source_cout"] == "reel").sum()),
            "estime": int((cp["source_cout"] == "estime").sum()),
            "non_disponible": int((cp["source_cout"] == "non_disponible").sum()),
            "pct_100_estime_ou_non_dispo": round(100 * (cp["source_cout"] != "reel").mean(), 4),
        },
        "postes_canada": {
            "total": int(len(pc)),
            "reel": int((pc["source_cout"] == "reel").sum()),
            "estime": int((pc["source_cout"] == "estime").sum()),
            "non_disponible": int((pc["source_cout"] == "non_disponible").sum()),
        },
        "par_transporteur": by_carrier,
    }


def task2(pkg: pd.DataFrame, invoice_ids: set[int], nb_commandes: int) -> dict:
    pkg = pkg.copy()
    pkg["source_cout"] = assign_source_cout(pkg, invoice_ids)
    cost_ok = pkg["cout_transport"].notna() & (pkg["cout_transport"] != 0)

    avant_cmd_matchees = int(pkg.loc[cost_ok, "order_id"].nunique())
    apres_cmd_matchees = int(pkg.loc[pkg["source_cout"] == "reel", "order_id"].nunique())

    return {
        "mesures_modifiees": [
            "Nb Commandes Matchées",
            "Taux Matching",
            "Nb Colis Avec Facture",
            "Nb Colis (coût réel) [nouveau]",
            "Nb Colis (coût estimé) [nouveau]",
            "Nb Colis (coût non disponible) [nouveau]",
        ],
        "AVANT (cout_transport > 0)": {
            "Nb_Commandes_Matchees": avant_cmd_matchees,
            "Taux_Matching_pct": round(100 * avant_cmd_matchees / nb_commandes, 4),
            "Nb_Colis_avec_cout_backend": int(cost_ok.sum()),
            "note": "Colis Privé avec coût backend comptait comme matché",
        },
        "APRES (source_cout = reel)": {
            "Nb_Commandes_Matchees": apres_cmd_matchees,
            "Taux_Matching_pct": round(100 * apres_cmd_matchees / nb_commandes, 4),
            "Nb_Colis_cout_reel": int((pkg["source_cout"] == "reel").sum()),
            "Nb_Colis_cout_estime": int((pkg["source_cout"] == "estime").sum()),
            "Nb_Colis_cout_non_disponible": int((pkg["source_cout"] == "non_disponible").sum()),
        },
        "delta_commandes_matchees": apres_cmd_matchees - avant_cmd_matchees,
        "nb_commandes_total": nb_commandes,
    }


def task3(pkg: pd.DataFrame, invoice_ids: set[int]) -> dict:
    pkg = pkg.copy()
    pkg["source_cout"] = assign_source_cout(pkg, invoice_ids)
    cp = pkg[pkg["transporteur"] == "Colis Privé"]
    nd = cp[cp["source_cout"] == "non_disponible"]
    return {
        "decision": "coût non disponible (source_cout = non_disponible)",
        "colis_prive_sans_facture_ni_backend": {
            "count": int(len(nd)),
            "attendu_audit": 8209,
            "ecart_vs_audit": int(len(nd)) - 8209,
        },
        "visibles_en_volume": int(len(cp)),
        "exclus_du_cout_transport": int(len(nd)),
        "pct_du_volume_colis_prive": round(100 * len(nd) / len(cp), 4) if len(cp) else 0,
        "exemples_id_package": nd["id_package"].head(5).astype(int).tolist(),
    }


def main() -> None:
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    pkg = build_packages()
    inv = load_invoices()
    invoice_ids = resolve_invoices(inv, pkg)

    co = pd.read_csv(BACKEND / "customer_order.csv", usecols=["id", "state"], dtype=str, low_memory=False)
    nb_cmd = int((co["state"].str.upper() != "CANCELLED").sum())

    out = {
        "task1_flag_source_cout": task1(pkg, invoice_ids),
        "task2_mesures_matching": task2(pkg, invoice_ids, nb_cmd),
        "task3_colis_prive_non_disponible": task3(pkg, invoice_ids),
        "meta": {
            "id_packages_facture_resolus": len(invoice_ids),
            "lignes_factures_valides": len(inv),
        },
    }
    p = Path(__file__).parent / "transport_source_output.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nÉcrit dans {p}")


if __name__ == "__main__":
    main()
