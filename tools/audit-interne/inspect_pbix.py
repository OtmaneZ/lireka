"""Inspecte les .pbix du datawarehouse : tables, mesures, sources M."""
from __future__ import annotations

import os

import json
import re
import zipfile
from pathlib import Path

# Fix F-19 : racine de l'entrepôt paramétrable via la variable d'environnement LIREKA_DWH.
ROOT = Path(os.environ.get("LIREKA_DWH", Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"))


def extract_strings(blob: bytes, min_len: int = 4) -> list[str]:
    text = blob.decode("utf-8", errors="ignore")
    found = re.findall(r"[A-Za-z0-9_./\\:-]{%d,}" % min_len, text)
    out, seen = [], set()
    for s in found:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def inspect_pbix(path: Path) -> dict:
    info: dict = {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "size_mb": round(path.stat().st_size / 1024 / 1024, 2)}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        info["internal_files"] = names

        if "DataMashup" in names:
            strings = extract_strings(z.read("DataMashup"))
            keys = ("csv", "customer", "order", "amount", "revenue", "profit", "margin",
                    "facture", "transport", "package", "lireka", "sharepoint", "donn",
                    "colissimo", "chronopost", "dhl", "fedex", "ups")
            info["datamashup_keywords"] = [s for s in strings if any(k in s.lower() for k in keys)][:60]

        if "Metadata" in names:
            meta = z.read("Metadata").decode("utf-16-le", errors="ignore")
            info["metadata_excerpt"] = meta[:400].replace("\n", " ")

        # Format récent : binaire DataModel (pas DataModelSchema JSON)
        if "DataModel" in names:
            dm = z.read("DataModel")
            text = dm.decode("utf-16-le", errors="ignore") + dm.decode("utf-8", errors="ignore")
            text += dm.decode("latin-1", errors="ignore")
            table_names = list(dict.fromkeys(re.findall(r"\b([A-Za-z][A-Za-z0-9 _-]{2,40})\b", text)))
            # filtre bruit : garder noms plausibles de tables/mesures
            plausible = [t for t in table_names if any(k in t.lower() for k in (
                "fact", "dim", "table", "facture", "invoice", "shipment", "colis", "dhl",
                "ups", "fedex", "transport", "date", "mesure", "cost", "coût", "total", "lireka"
            ))]
            info["datamodel_strings"] = plausible[:30]
            measure_hits = list(dict.fromkeys(re.findall(
                r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 '().%-]{4,60})\s*=", text
            )))
            info["measure_like"] = [m.strip() for m in measure_hits if any(k in m.lower() for k in (
                "coût", "cout", "cost", "total", "montant", "factur", "transport", "ht", "ca", "marge"
            ))][:25]
            source_hits = list(dict.fromkeys(re.findall(
                r"([A-Za-z0-9_ ./\\:-]{8,80}\.(?:csv|xlsx))", text, flags=re.I
            )))
            info["source_files"] = source_hits[:20]
            keyword_hits = {}
            for pat in ("customer_order", "order_amount", "gross_profit", "package", "LYSIR", "FedEx", "Colissimo", "Chronopost"):
                m = re.findall(pat + r".{0,30}", text, flags=re.I)
                if m:
                    keyword_hits[pat] = list(dict.fromkeys(m))[:5]
            info["keyword_hits"] = keyword_hits

        if "DataModelSchema" in names:
            dm = json.loads(z.read("DataModelSchema"))
            tables = dm.get("model", {}).get("tables", [])
            info["tables"] = [t.get("name") for t in tables]
            measures = []
            columns_of_interest = []
            for t in tables:
                for m in t.get("measures", []):
                    measures.append({
                        "table": t.get("name"),
                        "name": m.get("name"),
                        "expression": (m.get("expression") or "")[:200],
                    })
                for c in t.get("columns", []):
                    cn = (c.get("name") or "").lower()
                    if any(k in cn for k in ("ca", "amount", "revenue", "profit", "margin", "cout", "cost", "ht")):
                        columns_of_interest.append(f"{t.get('name')}.{c.get('name')}")
            info["measures"] = measures
            info["columns_of_interest"] = columns_of_interest[:40]

    return info


def main() -> None:
    pbix_files = sorted(ROOT.rglob("*.pbix"))
    print(f"PBIX trouvés: {len(pbix_files)}\n")
    for p in pbix_files:
        rel = p.relative_to(ROOT)
        print("=" * 80)
        print(rel)
        try:
            info = inspect_pbix(p)
            print(f"  Taille: {info['size_mb']} MB")
            if info.get("tables"):
                print("  Tables:", ", ".join(info["tables"]))
            if info.get("columns_of_interest"):
                print("  Colonnes CA/coût:", ", ".join(info["columns_of_interest"][:20]))
            if info.get("measures"):
                print("  Mesures:")
                for m in info["measures"][:20]:
                    print(f"    [{m['table']}] {m['name']} = {m['expression']}")
                if len(info["measures"]) > 20:
                    print(f"    ... +{len(info['measures']) - 20} mesures")
            if info.get("datamashup_keywords"):
                print("  Sources M (extraits):", ", ".join(info["datamashup_keywords"][:25]))
            if info.get("source_files"):
                print("  Fichiers source:", ", ".join(info["source_files"][:10]))
            if info.get("datamodel_strings"):
                print("  Noms modèle (extraits):", ", ".join(info["datamodel_strings"][:15]))
            if info.get("measure_like"):
                print("  Mesures (extraits):", " | ".join(info["measure_like"][:12]))
            if info.get("keyword_hits"):
                print("  Mots-clés CA/commande:", info["keyword_hits"])
        except Exception as e:
            print(f"  ERREUR: {e}")


if __name__ == "__main__":
    main()
