"""Preuves chiffrées avant/après pour l'implémentation des 3 décisions.

Réplique en pandas la logique appliquée dans la couche Power Query M (les CSV bruts
ne sont PAS modifiés). Sert uniquement à produire des comptages vérifiables.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"
BACKEND = ROOT / "Données_Backend"
TRANSP = ROOT / "Dashboards_transporteurs"
COL_DIR = TRANSP / "COLISSIMO Dashboard PowerBI"
CHR_DIR = TRANSP / "CHRONOPOST Dashboard PowerBI"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()[:12]


def read_recap(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, sep=";", dtype=str, encoding="latin-1")


def norm(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.upper()


# ===========================================================================
# TÂCHE 1 — jointure facture <-> colis avec résolution par date
# ===========================================================================
def task1() -> dict:
    pkg = pd.read_csv(BACKEND / "package.csv", usecols=["id", "order_id", "tracking_id"],
                      dtype={"tracking_id": "string"}, low_memory=False)
    co = pd.read_csv(BACKEND / "customer_order.csv", usecols=["id", "origin_created"],
                     dtype={"origin_created": "string"}, low_memory=False)
    co["date_commande"] = pd.to_datetime(co["origin_created"].str.slice(0, 10), errors="coerce")
    pkg = pkg.merge(co[["id", "date_commande"]], left_on="order_id", right_on="id",
                    suffixes=("", "_co"))
    pkg["tk"] = norm(pkg["tracking_id"])

    counts = pkg["tk"].value_counts()
    dup_keys = set(counts[counts > 1].index)
    dups = pkg[pkg["tk"].isin(dup_keys)]

    # --- combien de tracking dupliqués existent réellement côté factures ? ---
    inv_suivi = set()
    for p in COL_DIR.glob("*.csv"):
        df = read_recap(p)
        col = next((c for c in df.columns if "colis" in c.lower()), None)
        if col:
            inv_suivi |= set(norm(df[col]).dropna())
    for p in CHR_DIR.glob("*.csv"):
        if p.name == "2026_CHRONOPOST_récap_au_30_juin_2026.csv":
            continue  # exclu (doublon de V2) — cf. tâche 2
        df = read_recap(p)
        col = next((c for c in df.columns if "colis" in c.lower() or "objet" in c.lower()), None)
        if col:
            inv_suivi |= set(norm(df[col]).dropna())
    dup_in_invoices = sorted(dup_keys & inv_suivi)

    # --- contrôle de la résolution par date sur les 382 paires ---
    def resolve(candidates: pd.DataFrame, probe_date) -> int:
        """Réplique la logique M : renvoie l'id_package du candidat dont la date
        commande est la plus proche de la date facture (probe)."""
        if len(candidates) == 1:
            return int(candidates.iloc[0]["id"])
        d = candidates.copy()
        d["delta"] = (d["date_commande"] - probe_date).abs()
        d = d.sort_values(["delta", "id"])
        return int(d.iloc[0]["id"])

    probes_ok = probes_tot = ties = 0
    for tk, g in dups.groupby("tk"):
        g = g[["id", "order_id", "date_commande"]].dropna(subset=["date_commande"])
        if len(g) < 2:
            continue
        dates = g["date_commande"].tolist()
        if len(set(dates)) < len(dates):
            ties += 1  # dates identiques -> pas départageable par date
        for _, row in g.iterrows():
            probes_tot += 1
            chosen = resolve(g, row["date_commande"])
            if chosen == int(row["id"]):
                probes_ok += 1

    return {
        "paires_tracking_dupliquees": int(len(dup_keys)),
        "tracking_dupliques_presents_dans_factures": len(dup_in_invoices),
        "exemples_dup_dans_factures": dup_in_invoices[:10],
        "jointure_avant (numero_suivi seul)": "1 facture -> N colis (fan-out) pour une clé dupliquée = "
                                              "coût attribué en double / au mauvais colis",
        "controle_resolution_par_date": {
            "probes_total (2 par paire)": probes_tot,
            "probes_resolus_correctement": probes_ok,
            "taux_succes_pct": round(100 * probes_ok / probes_tot, 3) if probes_tot else None,
            "paires_dates_identiques_non_departageables": ties,
        },
    }


# ===========================================================================
# TÂCHE 2 — exclusion fichier Chronopost dupliqué
# ===========================================================================
def valid_rows(p: Path) -> int:
    df = read_recap(p)
    tot = next((c for c in df.columns if c.upper().lstrip("\ufeff").startswith("TOTAL")), None)
    if tot is None:
        return len(df)
    v = pd.to_numeric(df[tot].astype("string").str.replace(",", ".", regex=False), errors="coerce")
    return int(v.notna().sum())


def task2() -> dict:
    files = {p.name: p for p in CHR_DIR.glob("*.csv")}
    f2025 = "2025_CHRONOPOST_récap.csv"
    frecap = "2026_CHRONOPOST_récap_au_30_juin_2026.csv"
    fv2 = "2026_CHRONOPOST_V2.csv"
    hashes = {n: sha256(files[n]) for n in files}
    rows = {n: valid_rows(files[n]) for n in files}

    before_chrono = rows[f2025]                      # code actuel : 2025 uniquement
    after_chrono = rows[f2025] + rows[fv2]           # décision : 2025 + V2
    naive_both_2026 = rows[frecap] + rows[fv2]       # risque si on chargeait les 2 fichiers 2026

    return {
        "hashes_sha256_12": hashes,
        "lignes_valides_par_fichier": rows,
        "identiques_byte_for_byte": (hashes[frecap] == hashes[fv2],
                                     f"{frecap} == {fv2}" if hashes[frecap] == hashes[fv2] else "non"),
        "chargement_AVANT (code actuel = 2025 seul)": {"chronopost_lignes": before_chrono,
                                                       "note": "le récap 2026 n'était PAS chargé (hack temporaire + commentaire erroné)"},
        "risque_double_comptage_2026 (récap + V2)": naive_both_2026,
        "2026_compte_une_seule_fois (V2)": rows[fv2],
        "chargement_APRES (2025 + V2, récap exclu)": {"chronopost_lignes": after_chrono},
    }


# ===========================================================================
# TÂCHE 3 — destination_country nul : exclusion CANCELLED + "Pays non attribué"
# ===========================================================================
def task3() -> dict:
    co = pd.read_csv(BACKEND / "customer_order.csv",
                     usecols=["id", "state", "destination_country"], dtype=str, low_memory=False)
    total = len(co)
    dc = co["destination_country"].astype("string").str.strip()
    is_null = dc.isna() | (dc == "") | (dc.str.lower() == "nan")
    state = co["state"].astype("string").str.strip().str.upper()
    is_cancelled = state.eq("CANCELLED")

    null_total = int(is_null.sum())
    null_cancelled = int((is_null & is_cancelled).sum())
    null_non_cancelled = int((is_null & ~is_cancelled).sum())

    after = co[~is_cancelled]
    dc_after = after["destination_country"].astype("string").str.strip()
    null_after = int((dc_after.isna() | (dc_after == "") | (dc_after.str.lower() == "nan")).sum())

    return {
        "total_commandes": total,
        "commandes_CANCELLED_total": int(is_cancelled.sum()),
        "code_pays_?? AVANT (toutes lignes)": null_total,
        "  dont CANCELLED": null_cancelled,
        "  dont non-CANCELLED (résidu -> 'Pays non attribué')": null_non_cancelled,
        "commandes_conservees_apres_exclusion_CANCELLED": int((~is_cancelled).sum()),
        "code_pays_?? APRES (hors CANCELLED, = résidu marqué 'Pays non attribué')": null_after,
    }


def main() -> None:
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out = {"task1_join_date": task1(), "task2_chronopost_dedup": task2(), "task3_country_null": task3()}
    p = Path(__file__).parent / "impl_checks_output.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nÉcrit dans {p}")


if __name__ == "__main__":
    main()
