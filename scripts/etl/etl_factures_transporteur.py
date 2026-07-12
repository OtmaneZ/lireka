"""
Lireka ETL — Pipeline factures transporteurs
=============================================
Transforme les CSV bruts de factures transporteurs vers le schéma unifié.

Usage:
    python scripts/etl/etl_factures_transporteur.py --transporteur la-poste --fichier data/raw/transporteurs/la-poste/la-poste_factures_202606.csv
    python scripts/etl/etl_factures_transporteur.py --transporteur all --dossier data/raw/transporteurs/

Auteur: Otmane Boulahia — ZineInsights
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Mapping des colonnes source → schéma unifié par transporteur
MAPPINGS = {
    "la-poste": {
        "numero_facture": "numero_facture",
        "date_facture": "date_facture",
        "numero_suivi": "numero_suivi",
        "cout_transport": "cout_transport",
        "poids": "poids",
        "pays_destination": "pays_destination",
        "service": "service",
        "devise": "devise",
    },
    "colis-prive": {
        "numero_facture": "numero_facture",
        "date_facture": "date_facture",
        "numero_suivi": "numero_suivi",
        "cout_transport": "cout_transport",
        "poids": "poids",
        "pays_destination": "pays_destination",
        "service": "service",
        "devise": "devise",
    },
    "chronopost": {
        "numero_facture": "numero_facture",
        "date_facture": "date_facture",
        "numero_suivi": "numero_suivi",
        "cout_transport": "cout_transport",
        "poids": "poids",
        "pays_destination": "pays_destination",
        "service": "service",
        "devise": "devise",
    },
}

TRANSPORTEUR_LABELS = {
    "la-poste": "La Poste",
    "colis-prive": "Colis Privé",
    "chronopost": "Chronopost",
    "dhl": "DHL",
    "fedex": "FedEx",
    "ups": "UPS",
}

SCHEMA_UNIFIE = [
    "numero_facture",
    "date_facture",
    "numero_suivi",
    "transporteur",
    "cout_transport",
    "poids",
    "pays_destination",
    "service",
    "devise",
    "date_import",
]


def nettoyer_numero_suivi(valeur: str) -> str:
    """Normalise le numéro de suivi : TRIM + UPPER."""
    if not valeur:
        return ""
    return valeur.strip().upper()


def valider_ligne(ligne: dict, transporteur: str) -> tuple[bool, list[str]]:
    """Valide une ligne selon les règles de qualité."""
    erreurs = []

    if not ligne.get("numero_suivi"):
        erreurs.append("numero_suivi manquant")

    try:
        cout = float(ligne.get("cout_transport", ""))
        if cout < 0:
            erreurs.append("cout_transport negatif")
    except (ValueError, TypeError):
        erreurs.append("cout_transport invalide")

    if not ligne.get("date_facture"):
        erreurs.append("date_facture manquante")

    return len(erreurs) == 0, erreurs


def transformer_fichier(fichier_source: Path, transporteur: str) -> list[dict]:
    """Transforme un fichier CSV brut vers le schéma unifié."""
    mapping = MAPPINGS.get(transporteur)
    if not mapping:
        print(f"ERREUR: Transporteur '{transporteur}' non configuré.")
        sys.exit(1)

    lignes_valides = []
    lignes_rejetees = 0
    date_import = datetime.now().isoformat()

    with open(fichier_source, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ligne = {
                "transporteur": TRANSPORTEUR_LABELS.get(transporteur, transporteur),
                "date_import": date_import,
            }

            for champ_unifie, champ_source in mapping.items():
                valeur = row.get(champ_source, "")
                if champ_unifie == "numero_suivi":
                    valeur = nettoyer_numero_suivi(valeur)
                ligne[champ_unifie] = valeur

            if not ligne.get("devise"):
                ligne["devise"] = "EUR"

            valide, erreurs = valider_ligne(ligne, transporteur)
            if valide:
                lignes_valides.append(ligne)
            else:
                lignes_rejetees += 1
                print(f"  REJET: {ligne.get('numero_facture', '?')} — {', '.join(erreurs)}")

    print(f"  Résultat: {len(lignes_valides)} valides, {lignes_rejetees} rejetées")
    return lignes_valides


def ecrire_fichier_unifie(lignes: list[dict], fichier_sortie: Path):
    """Écrit ou ajoute au fichier unifié."""
    fichier_sortie.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if fichier_sortie.exists() else "w"
    ecrire_header = not fichier_sortie.exists()

    with open(fichier_sortie, mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_UNIFIE)
        if ecrire_header:
            writer.writeheader()
        writer.writerows(lignes)


def main():
    parser = argparse.ArgumentParser(description="ETL factures transporteurs Lireka")
    parser.add_argument("--transporteur", required=True, help="Nom du transporteur (la-poste, colis-prive, chronopost, all)")
    parser.add_argument("--fichier", help="Chemin du fichier CSV source")
    parser.add_argument("--dossier", help="Dossier contenant les CSV (mode batch)")
    parser.add_argument("--sortie", default="data/processed/transporteurs/factures_unifiees.csv", help="Fichier de sortie unifié")
    args = parser.parse_args()

    fichier_sortie = Path(args.sortie)
    total_lignes = 0

    if args.transporteur == "all" and args.dossier:
        dossier = Path(args.dossier)
        for transporteur in MAPPINGS:
            sous_dossier = dossier / transporteur
            if sous_dossier.exists():
                for fichier in sous_dossier.glob("*.csv"):
                    print(f"\nTraitement: {transporteur} — {fichier.name}")
                    lignes = transformer_fichier(fichier, transporteur)
                    ecrire_fichier_unifie(lignes, fichier_sortie)
                    total_lignes += len(lignes)
    elif args.fichier:
        fichier = Path(args.fichier)
        print(f"Traitement: {args.transporteur} — {fichier.name}")
        lignes = transformer_fichier(fichier, args.transporteur)
        ecrire_fichier_unifie(lignes, fichier_sortie)
        total_lignes = len(lignes)
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\n=== ETL terminé — {total_lignes} lignes ajoutées → {fichier_sortie} ===")


if __name__ == "__main__":
    main()
