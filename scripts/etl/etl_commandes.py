"""
Lireka ETL — Pipeline commandes clients
==========================================
Transforme l'export CSV backend vers le schéma nettoyé pour Power BI.

Usage:
    python scripts/etl/etl_commandes.py --fichier data/raw/commandes/commandes_20260710.csv

Auteur: Otmane Boulahia — ZineInsights
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_SORTIE = [
    "id_commande",
    "date_commande",
    "pays_livraison",
    "type_commande",
    "transporteur",
    "numero_suivi",
    "ca_ht",
    "cout_achat",
    "cout_transport_estime",
    "nombre_articles",
    "poids_total",
    "date_import",
]

COLONNES_OBLIGATOIRES = [
    "id_commande",
    "date_commande",
    "pays_livraison",
    "type_commande",
    "transporteur",
    "numero_suivi",
    "ca_ht",
    "cout_achat",
    "cout_transport_estime",
]

TRANSPORTEURS_VALIDES = {
    "DHL", "FedEx", "UPS", "La Poste", "Colis Privé", "Chronopost",
    "LA POSTE", "COLIS PRIVE", "CHRONOPOST",
}


def nettoyer_numero_suivi(valeur: str) -> str:
    if not valeur:
        return ""
    return valeur.strip().upper()


def normaliser_transporteur(valeur: str) -> str:
    mapping = {
        "LA POSTE": "La Poste",
        "COLIS PRIVE": "Colis Privé",
        "COLIS PRIVÉ": "Colis Privé",
        "CHRONOPOST": "Chronopost",
        "DHL": "DHL",
        "FEDEX": "FedEx",
        "UPS": "UPS",
    }
    return mapping.get(valeur.strip().upper(), valeur.strip())


def valider_ligne(ligne: dict) -> tuple[bool, list[str]]:
    erreurs = []

    for champ in COLONNES_OBLIGATOIRES:
        if not ligne.get(champ) and ligne.get(champ) != 0:
            erreurs.append(f"{champ} manquant")

    for champ in ["ca_ht", "cout_achat", "cout_transport_estime"]:
        try:
            if float(ligne.get(champ, -1)) < 0:
                erreurs.append(f"{champ} negatif")
        except (ValueError, TypeError):
            erreurs.append(f"{champ} invalide")

    return len(erreurs) == 0, erreurs


def transformer_fichier(fichier_source: Path) -> list[dict]:
    lignes_valides = []
    lignes_rejetees = 0
    ids_vus = set()
    date_import = datetime.now().isoformat()

    with open(fichier_source, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_cmd = row.get("id_commande", "").strip()

            if id_cmd in ids_vus:
                print(f"  DOUBLON: {id_cmd} — ligne ignorée (doublon)")
                lignes_rejetees += 1
                continue
            ids_vus.add(id_cmd)

            ligne = {
                "id_commande": id_cmd,
                "date_commande": row.get("date_commande", "").strip(),
                "pays_livraison": row.get("pays_livraison", "").strip().upper(),
                "type_commande": row.get("type_commande", "").strip(),
                "transporteur": normaliser_transporteur(row.get("transporteur", "")),
                "numero_suivi": nettoyer_numero_suivi(row.get("numero_suivi", "")),
                "ca_ht": row.get("ca_ht", ""),
                "cout_achat": row.get("cout_achat", ""),
                "cout_transport_estime": row.get("cout_transport_estime", ""),
                "nombre_articles": row.get("nombre_articles", ""),
                "poids_total": row.get("poids_total", ""),
                "date_import": date_import,
            }

            valide, erreurs = valider_ligne(ligne)
            if valide:
                lignes_valides.append(ligne)
            else:
                lignes_rejetees += 1
                print(f"  REJET: {id_cmd} — {', '.join(erreurs)}")

    print(f"  Résultat: {len(lignes_valides)} valides, {lignes_rejetees} rejetées")
    return lignes_valides


def main():
    parser = argparse.ArgumentParser(description="ETL commandes clients Lireka")
    parser.add_argument("--fichier", required=True, help="Chemin du CSV source")
    parser.add_argument("--sortie", default="data/processed/commandes/commandes_clean.csv", help="Fichier de sortie")
    args = parser.parse_args()

    fichier_source = Path(args.fichier)
    fichier_sortie = Path(args.sortie)

    if not fichier_source.exists():
        print(f"ERREUR: Fichier introuvable — {fichier_source}")
        sys.exit(1)

    print(f"Traitement: {fichier_source.name}")
    lignes = transformer_fichier(fichier_source)

    fichier_sortie.parent.mkdir(parents=True, exist_ok=True)
    with open(fichier_sortie, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_SORTIE)
        writer.writeheader()
        writer.writerows(lignes)

    print(f"\n=== ETL terminé — {len(lignes)} lignes → {fichier_sortie} ===")


if __name__ == "__main__":
    main()
