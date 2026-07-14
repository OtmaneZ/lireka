"""
Lireka — Validation qualité des données
========================================
Contrôle la qualité des fichiers CSV avant import Power BI.

Usage:
    python scripts/validation/validate_data.py --type factures --fichier data/samples/transporteurs/la-poste/la-poste_factures_202606.csv
    python scripts/validation/validate_data.py --type commandes --fichier data/samples/commandes/commandes_202606.csv
    python scripts/validation/validate_data.py --type matching \
        --fichier-factures data/samples/transporteurs/la-poste/la-poste_factures_202606.csv \
        --fichier-commandes data/samples/commandes/commandes_202606.csv

Auteur: Otmane Boulahia — ZineInsights
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path


def valider_factures(fichier: Path) -> dict:
    stats = {"total": 0, "valide": 0, "erreurs": [], "alertes": []}

    with open(fichier, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        suivi_vus = set()

        for i, row in enumerate(reader, start=2):
            stats["total"] += 1
            ok = True

            if not row.get("numero_suivi"):
                stats["erreurs"].append(f"L{i}: numero_suivi manquant")
                ok = False

            try:
                if float(row.get("cout_transport", -1)) < 0:
                    stats["erreurs"].append(f"L{i}: cout_transport negatif")
                    ok = False
            except ValueError:
                stats["erreurs"].append(f"L{i}: cout_transport invalide")
                ok = False

            suivi = row.get("numero_suivi", "")
            if suivi in suivi_vus:
                stats["alertes"].append(f"L{i}: doublon numero_suivi {suivi}")
            suivi_vus.add(suivi)

            if ok:
                stats["valide"] += 1

    return stats


def valider_commandes(fichier: Path) -> dict:
    stats = {"total": 0, "valide": 0, "erreurs": [], "alertes": []}

    with open(fichier, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ids_vus = set()

        for i, row in enumerate(reader, start=2):
            stats["total"] += 1
            ok = True

            for champ in ["id_commande", "ca_ht", "cout_achat", "numero_suivi"]:
                if not row.get(champ):
                    stats["erreurs"].append(f"L{i}: {champ} manquant")
                    ok = False

            id_cmd = row.get("id_commande", "")
            if id_cmd in ids_vus:
                stats["alertes"].append(f"L{i}: doublon id_commande {id_cmd}")
            ids_vus.add(id_cmd)

            if not row.get("numero_suivi"):
                stats["alertes"].append(f"L{i}: numero_suivi vide (non matchable)")

            if ok:
                stats["valide"] += 1

    return stats


def valider_matching(fichier_commandes: Path, fichier_factures: Path) -> dict:
    stats = {"total_commandes": 0, "matchees": 0, "non_matchees": 0, "taux": 0.0}

    suivis_factures = set()
    with open(fichier_factures, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            suivi = row.get("numero_suivi", "").strip().upper()
            if suivi:
                suivis_factures.add(suivi)

    with open(fichier_commandes, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stats["total_commandes"] += 1
            suivi = row.get("numero_suivi", "").strip().upper()
            if suivi in suivis_factures:
                stats["matchees"] += 1
            else:
                stats["non_matchees"] += 1

    if stats["total_commandes"] > 0:
        stats["taux"] = round(stats["matchees"] / stats["total_commandes"] * 100, 1)

    return stats


def afficher_rapport(titre: str, stats: dict):
    print(f"\n{'='*50}")
    print(f"  RAPPORT QUALITÉ — {titre}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")

    if "total" in stats:
        pct = round(stats["valide"] / stats["total"] * 100, 1) if stats["total"] else 0
        print(f"  Lignes totales  : {stats['total']}")
        print(f"  Lignes valides  : {stats['valide']} ({pct}%)")
        print(f"  Erreurs         : {len(stats['erreurs'])}")
        print(f"  Alertes         : {len(stats['alertes'])}")

        if stats["erreurs"]:
            print("\n  ERREURS:")
            for e in stats["erreurs"][:10]:
                print(f"    - {e}")
            if len(stats["erreurs"]) > 10:
                print(f"    ... et {len(stats['erreurs']) - 10} autres")

        if stats["alertes"]:
            print("\n  ALERTES:")
            for a in stats["alertes"][:10]:
                print(f"    - {a}")

        statut = "OK" if not stats["erreurs"] else "ERREUR"
        if stats["alertes"] and statut == "OK":
            statut = "WARNING"

    elif "total_commandes" in stats:
        print(f"  Commandes totales : {stats['total_commandes']}")
        print(f"  Matchées          : {stats['matchees']}")
        print(f"  Non matchées      : {stats['non_matchees']}")
        print(f"  Taux de matching  : {stats['taux']}%")
        statut = "OK" if stats["taux"] >= 85 else "WARNING"

    print(f"\n  STATUT: {statut}")
    print(f"{'='*50}\n")
    return statut


def main():
    parser = argparse.ArgumentParser(description="Validation qualité données Lireka")
    parser.add_argument("--type", required=True, choices=["factures", "commandes", "matching"])
    parser.add_argument("--fichier", help="Fichier à valider")
    parser.add_argument("--fichier-factures", default="data/samples/transporteurs/la-poste/la-poste_factures_202606.csv")
    parser.add_argument("--fichier-commandes", default="data/samples/commandes/commandes_202606.csv")
    args = parser.parse_args()

    if args.type == "factures":
        if not args.fichier:
            print("ERREUR: --fichier requis pour type factures")
            sys.exit(1)
        stats = valider_factures(Path(args.fichier))
        statut = afficher_rapport("FACTURES", stats)

    elif args.type == "commandes":
        if not args.fichier:
            print("ERREUR: --fichier requis pour type commandes")
            sys.exit(1)
        stats = valider_commandes(Path(args.fichier))
        statut = afficher_rapport("COMMANDES", stats)

    elif args.type == "matching":
        stats = valider_matching(
            Path(args.fichier_commandes),
            Path(args.fichier_factures),
        )
        statut = afficher_rapport("MATCHING SUIVI", stats)

    sys.exit(0 if statut == "OK" else 1)


if __name__ == "__main__":
    main()
