#!/usr/bin/env python3
"""
Nettoyage architecture mesures (pré-duplication 5 pages).
- Point 1 : factorise la logique couleur YoY (fusion GV couleur / B2C couleur -> Couleur YoY - X partagees).
- Point 2 : convention de nommage (mesures generiques reutilisables sans prefixe de page).

Le script edite SIMULTANEMENT le modele (_Mesures.tmdl) et TOUTES les liaisons
de visuels (report/**/visual.json) pour garder model + report synchro.
Aucune modif de structure de visuel (colonnes, projections) -> pas de regression tableau B2C.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TMDL = ROOT / "powerbi/Lireka_Profitabilite.SemanticModel/definition/tables/_Mesures.tmdl"
REPORT_DIR = ROOT / "powerbi/Lireka_Profitabilite.Report/definition"

# Renommages 1:1 (mesures generiques : on retire le prefixe de page).
RENAMES = {
    # --- compact format (generique, reutilise sur B2C) ---
    "GV KPI \u2014 Ordered units": "KPI Compact \u2014 Ordered units",
    "GV KPI \u2014 Revenue": "KPI Compact \u2014 Revenue",
    "GV KPI \u2014 Gross Profit": "KPI Compact \u2014 Gross Profit",
    "GV KPI \u2014 Gross Margin": "KPI Compact \u2014 Gross Margin",
    # --- sous-titres carte (generique, reutilise sur B2C) ---
    "GV sous-titre \u2014 Unit\u00e9s": "KPI Sous-titre \u2014 Unit\u00e9s",
    "GV sous-titre \u2014 Revenue": "KPI Sous-titre \u2014 Revenue",
    "GV sous-titre \u2014 Gross Profit": "KPI Sous-titre \u2014 Gross Profit",
    "GV sous-titre \u2014 Gross Margin": "KPI Sous-titre \u2014 Gross Margin",
    # --- data labels graphe (generique) ---
    "GV chart label Revenue YoY": "Chart label \u2014 Revenue YoY",
    "GV chart label Gross Profit YoY": "Chart label \u2014 Gross Profit YoY",
    # --- couleur YoY (generique partagee ; les jumelles GV et B2C fusionnent ici) ---
    "GV couleur \u2014 Unit\u00e9s YoY": "Couleur YoY \u2014 Unit\u00e9s",
    "GV couleur \u2014 Revenue YoY": "Couleur YoY \u2014 Revenue",
    "GV couleur \u2014 Gross Profit YoY": "Couleur YoY \u2014 Gross Profit",
    "GV couleur \u2014 Gross Margin YoY": "Couleur YoY \u2014 Gross Margin",
    "GV couleur \u2014 Cancellation YoY": "Couleur YoY \u2014 Cancellation",
    # les doublons B2C pointent sur la meme mesure partagee
    "B2C couleur - Revenue YoY": "Couleur YoY \u2014 Revenue",
    "B2C couleur - Gross Profit YoY": "Couleur YoY \u2014 Gross Profit",
    "B2C couleur - Gross Margin YoY": "Couleur YoY \u2014 Gross Margin",
}

# Blocs de mesures dupliquees a supprimer du modele (leur logique = mesure partagee renommee).
DUP_DEFS_TO_DROP = [
    "B2C couleur - Revenue YoY",
    "B2C couleur - Gross Profit YoY",
    "B2C couleur - Gross Margin YoY",
]


def drop_measure_block(text: str, name: str) -> str:
    """Supprime le bloc `measure 'name' = ...` + sa/ses ligne(s) lineageTag + commentaires ///."""
    lines = text.split("\n")
    out = []
    i = 0
    needle = f"measure '{name}'"
    while i < len(lines):
        if needle in lines[i]:
            # remonter pour retirer les commentaires /// juste au-dessus
            while out and out[-1].strip().startswith("///"):
                out.pop()
            # avancer jusqu'a la fin du bloc (prochaine ligne 'measure ' ou fin d'indent)
            i += 1
            while i < len(lines):
                s = lines[i]
                if s.strip().startswith("measure ") or s.strip().startswith("/// "):
                    break
                if s.strip() == "" and i + 1 < len(lines) and (
                    lines[i + 1].strip().startswith("measure ")
                    or lines[i + 1].strip().startswith("///")
                ):
                    i += 1  # consommer la ligne vide separatrice
                    break
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def apply_renames(text: str) -> str:
    # remplacements longest-first pour eviter les collisions de sous-chaines
    for old in sorted(RENAMES, key=len, reverse=True):
        text = text.replace(old, RENAMES[old])
    return text


def main():
    # 1) Modele
    tmdl = TMDL.read_text(encoding="utf-8")
    for name in DUP_DEFS_TO_DROP:
        tmdl = drop_measure_block(tmdl, name)
    tmdl = apply_renames(tmdl)
    TMDL.write_text(tmdl, encoding="utf-8")
    print(f"[ok] {TMDL.name} mis a jour")

    # 2) Report : toutes les liaisons visuelles
    changed = 0
    for vj in REPORT_DIR.rglob("*.json"):
        original = vj.read_text(encoding="utf-8")
        updated = apply_renames(original)
        if updated != original:
            vj.write_text(updated, encoding="utf-8")
            changed += 1
    print(f"[ok] {changed} fichiers report mis a jour")


if __name__ == "__main__":
    main()
