#!/usr/bin/env python3
"""
Classification + displayFolder + suppressions MORTE sûres pour _Mesures.tmdl.

Ne renomme aucune mesure, ne modifie aucune expression DAX (hors suppressions),
ne touche pas au dossier Report.
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
TMDL = ROOT / "powerbi/Lireka_Profitabilite.SemanticModel/definition/tables/_Mesures.tmdl"
REPORT = ROOT / "powerbi/Lireka_Profitabilite.Report"
OUT_CSV = ROOT / "scripts/validation/measures_classification.csv"

REF_RE = re.compile(r"\[([^\[\]]+)\]")
PROP_RE = re.compile(r'"Property"\s*:\s*"((?:[^"\\]|\\.)*)"')

# Chaîne FX marketplace / revenu reconstruit (suppression conditionnelle — tâche 3).
RECON_CHAIN_CORE = {
    "CA Total HT (reconstruit)",
    "CA HT Net Annulation (reconstruit)",
    "Revenu (reconstruit)",
    "Revenu (reconstruit) PY",
    "Revenu (reconstruit) YoY Δ",
    "Revenu (reconstruit) YoY %",
    "Marge Brute (reconstruit)",
    "Marge Brute (reconstruit) PY",
    "Marge Brute (reconstruit) YoY Δ",
    "Marge Brute (reconstruit) YoY %",
    "Taux Marge Brute (reconstruit)",
    "Taux Marge Brute (reconstruit) PY",
    "Taux Marge Brute (reconstruit) YoY bps",
    "Taux Marge Brute (revenu reconstruit)",
    "Taux Marge Brute (revenu reconstruit) PY",
    "Taux Marge Brute (revenu reconstruit) YoY bps",
    "Revenu (reconstruit, alloué langue)",
    "Revenu (reconstruit, alloué langue) PY",
    "Revenu (reconstruit, alloué ISBN)",
    "B2C Rest GP reconstruit",
    "B2C Rest GP reconstruit PY",
}


def parse_measures(text: str) -> list[dict]:
    lines = text.splitlines()
    measures: list[dict] = []
    i = 0
    n = len(lines)
    while i < n:
        m = re.match(
            r"^\tmeasure (?:'((?:[^']|'')+)'|([A-Za-z_][\w ]*))\s*=(.*)$",
            lines[i],
        )
        if not m:
            i += 1
            continue
        raw = m.group(1) if m.group(1) is not None else m.group(2)
        name = raw.replace("''", "'").strip()
        line_no = i + 1
        # include preceding /// comments in block start for deletion
        comment_start = line_no - 1
        j = i - 1
        while j >= 0 and lines[j].startswith("\t///"):
            comment_start = j
            j -= 1

        body_lines = [lines[i]]
        i += 1
        while i < n:
            s = lines[i]
            if re.match(r"^\tmeasure ", s):
                break
            if s.startswith("\t///"):
                break
            if s.startswith("\tannotation ") or s.startswith("\tpartition ") or s.startswith(
                "\tcolumn "
            ):
                break
            if s == "":
                if i + 1 >= n:
                    i += 1
                    break
                nxt = lines[i + 1]
                if (
                    re.match(r"^\tmeasure ", nxt)
                    or nxt.startswith("\t///")
                    or nxt.startswith("\tannotation ")
                    or nxt.startswith("\tpartition ")
                    or nxt.startswith("\tcolumn ")
                ):
                    i += 1
                    break
            body_lines.append(s)
            i += 1

        eq = body_lines[0].split("=", 1)[1] if "=" in body_lines[0] else ""
        expr_parts = [eq]
        for s in body_lines[1:]:
            st = s.strip()
            if st.startswith(
                ("formatString:", "lineageTag:", "displayFolder:", "isHidden:", "annotation ")
            ):
                continue
            if ":" in st and st.split(":", 1)[0] in {
                "formatString",
                "lineageTag",
                "displayFolder",
                "isHidden",
            }:
                continue
            expr_parts.append(s)

        measures.append(
            {
                "name": name,
                "line": line_no,
                "expr": "\n".join(expr_parts),
                "body_lines": body_lines,
                "comment_start": comment_start,  # 0-based index of first /// or measure line
                "measure_idx": line_no - 1,
            }
        )
    return measures


def report_measure_names(all_names: set[str]) -> set[str]:
    props: set[str] = set()
    for path in REPORT.rglob("visual.json"):
        text = path.read_text(encoding="utf-8")
        for m in PROP_RE.finditer(text):
            props.add(m.group(1))
    return props & all_names


def python_refs(all_names: set[str]) -> set[str]:
    found: set[str] = set()
    skip = {
        "classify_measures.py",
        "classify_and_folder_measures.py",
        "apply_measure_folders.py",
    }
    for path in ROOT.rglob("*.py"):
        if path.name in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for name in all_names:
            if f"[{name}]" in text or f"'{name}'" in text or f'"{name}"' in text:
                found.add(name)
    return found


def build_deps(measures: list[dict], names: set[str]) -> dict[str, set[str]]:
    deps: dict[str, set[str]] = {}
    for m in measures:
        deps[m["name"]] = {r for r in REF_RE.findall(m["expr"]) if r in names}
    return deps


def reverse_deps(deps: dict[str, set[str]]) -> dict[str, set[str]]:
    rev: dict[str, set[str]] = defaultdict(set)
    for src, targets in deps.items():
        for t in targets:
            rev[t].add(src)
    return rev


def closure_from(seeds: set[str], deps: dict[str, set[str]]) -> set[str]:
    """Transitive dependencies (callees) of seeds."""
    needed: set[str] = set()
    stack = list(seeds)
    while stack:
        cur = stack.pop()
        for d in deps.get(cur, ()):
            if d not in needed and d not in seeds:
                needed.add(d)
                stack.append(d)
    return needed


def closure_callers(seeds: set[str], rev: dict[str, set[str]]) -> set[str]:
    """Transitive callers (dependents) of seeds."""
    out: set[str] = set(seeds)
    stack = list(seeds)
    while stack:
        cur = stack.pop()
        for c in rev.get(cur, ()):
            if c not in out:
                out.add(c)
                stack.append(c)
    return out


CONTROLE_NAME_RE = re.compile(
    r"(contr[oô]le|écart|ecart|matching|doublon|manquant|non match|"
    r"non attribu|zero ou null|backend \(réf|vs backend|vs facturé|"
    r"vs estimé|taux matching|taux écart|annulation partielle|"
    r"coût réel\)|coût estimé\)|coût non disponible|facturés|"
    r"coût transport facturé|coût facturé|colis avec facture|"
    r"panier moyen|poids total|ca mois précédent|évolution ca|"
    r"lignes colis|commandes sans colis|colis sans commande|"
    r"grain groupe|avant expédition|après expédition)",
    re.I,
)


def is_controle_seed(name: str) -> bool:
    if CONTROLE_NAME_RE.search(name):
        return True
    if name in {
        "Marge Brute Backend (réf.)",
        "Marge Brute (grain article, prov.)",
        "Coût Achat Total (grain article)",
        "Nb Colis Facturés",
        "Coût Moyen Colis",
        "CA Commandes Annulation Partielle",
        "Commandes Sans Colis",
        "Colis Sans Commande",
        "Nb Articles Annulés Avant Expédition",
        "Nb Articles Annulés Après Expédition",
        "Nb Colis (coût réel)",
        "Nb Colis (coût estimé)",
        "Nb Colis (coût non disponible)",
    }:
        return True
    return False


def is_attente_seed(name: str) -> bool:
    if re.search(r"YoY\s*[Δ%]|YoY\s*bps", name):
        return True
    if name.startswith("Chart label"):
        return True
    # Native revenue / margin rate family reserved for future pages
    # (dashboard currently uses reconstruit variants).
    if name in {
        "Revenu",
        "Revenu PY",
        "Taux Marge Brute",
        "Taux Marge Brute PY",
        "Nb Commandes PY",
        "CA HT Net Annulation PY",
        "Frais Port Encaissés PY",
        "Coût Achat Total PY",
        "Coût Transport Amont PY",
        "Coût Transport Outbound (Retenu) PY",
        "Douanes Taxes PY",
        "Commissions Marketplace PY",
        "Fournitures Expédition PY",
        "Retours Remboursements PY",
        "Coûts Génériques PY",
        "Unités commandées YoY Δ",  # YoY already, but pair mate
    }:
        return True
    if name.endswith(" PY") and "reconstruit" not in name.lower():
        # PY mates of ATTENTE YoY pairs (native), if not already LIVREE/DEP
        return True
    return False


def is_morte_seed(name: str) -> bool:
    if "(prov.)" in name and "grain article" not in name:
        return True
    if name in {
        "Top Keep ISBN — Revenue",  # orphan helper, never wired
        "Revenu (reconstruit, alloué langue)",
        "Revenu (reconstruit, alloué langue) PY",
        "Taux Marge Brute (reconstruit)",
        "Taux Marge Brute (reconstruit) PY",
        "Taux Marge Brute (reconstruit) YoY bps",
        "Marge Brute (reconstruit) YoY Δ",
        "Marge Brute (reconstruit) YoY %",
    }:
        return True
    return False


def classify(
    names: set[str],
    in_report: set[str],
    deps: dict[str, set[str]],
    rev: dict[str, set[str]],
) -> dict[str, str]:
    livree = set(in_report)
    dep_livree = closure_from(livree, deps)

    # CONTROLE seeds among remaining
    remaining = names - livree - dep_livree
    controle_seeds = {n for n in remaining if is_controle_seed(n)}
    # helpers only used for controle (callees of controle seeds, still remaining)
    controle_helpers = closure_from(controle_seeds, deps) & remaining
    controle = (controle_seeds | controle_helpers) - livree - dep_livree

    remaining2 = remaining - controle
    attente_seeds = {n for n in remaining2 if is_attente_seed(n)}
    attente_helpers = closure_from(attente_seeds, deps) & remaining2
    attente = (attente_seeds | attente_helpers) - livree - dep_livree - controle

    remaining3 = remaining2 - attente
    morte = {n for n in remaining3 if is_morte_seed(n)}
    # anything left: if only supports morte/prov chain → MORTE; else CONTROLE-ish counts
    for n in remaining3 - morte:
        if "(prov.)" in n:
            morte.add(n)
        elif is_controle_seed(n) or any(
            k in n.lower() for k in ("nb colis", "coût transport estimé", "coût transport réel")
        ):
            controle.add(n)
        elif "reconstruit" in n.lower():
            morte.add(n)
        else:
            # default: unused infrastructure → MORTE if unused by anything live, else CONTROLE
            callers = rev.get(n, set())
            if not callers:
                if any(k in n for k in ("Sans ", "Manquant", "Doublon", "Écart", "Matching")):
                    controle.add(n)
                else:
                    morte.add(n)
            else:
                # referenced only by non-livree — assign with majority of callers' provisional class
                controle.add(n)

    # Final exclusivity
    cat: dict[str, str] = {}
    for n in names:
        if n in livree:
            cat[n] = "LIVREE"
        elif n in dep_livree:
            cat[n] = "DEPENDANCE"
        elif n in controle:
            cat[n] = "CONTROLE"
        elif n in attente:
            cat[n] = "ATTENTE"
        else:
            cat[n] = "MORTE"
    return cat


def display_folder(name: str, cat: str) -> str:
    if cat == "CONTROLE":
        return "08 Contrôles"
    if cat == "MORTE":
        return "09 Dette technique"

    # Display / Top families first (even if DEPENDANCE helpers for Rest/Rank)
    if name.startswith(
        (
            "GV Display",
            "B2C Display",
            "Mkt Display",
            "B2C Rest",
            "B2C Rank",
            "B2C Sort",
            "B2C Bridge",
            "B2C couleur",
            "B2B Rank",
        )
    ):
        return "06 Display (familles GV / B2C / Mkt)"
    if name.startswith("Top ") or name.startswith("Top"):
        return "07 Top / Loss"

    if cat == "ATTENTE" or re.search(r"YoY| PY$", name) or name.startswith("Chart label"):
        # Keep pure YoY/attente in 05; domain PY still YoY folder
        if re.search(r"YoY| PY$", name) or name.startswith("Chart label"):
            return "05 YoY"

    # KPI published surface
    if name.startswith(
        ("KPI ", "Couleur YoY", "GV Display", "Chart label")
    ) or name in {
        "Nb Commandes",
        "Marge Brute",
        "Unités commandées YoY %",
        "Marge Brute PY",
        "Marge Brute YoY %",
        "Taux Annulation",
        "Taux Annulation YoY bps",
        "Revenu (reconstruit)",
        "Revenu (reconstruit) PY",
        "Revenu (reconstruit) YoY %",
        "Taux Marge Brute (revenu reconstruit)",
        "Taux Marge Brute (revenu reconstruit) YoY bps",
    }:
        if name.startswith(("KPI ", "Couleur YoY")) or name in {
            "Nb Commandes",
            "Unités commandées YoY %",
            "Marge Brute PY",
            "Marge Brute YoY %",
            "Taux Annulation",
            "Taux Annulation YoY bps",
        }:
            return "01 KPI publiés"

    # Domain folders for remaining LIVREE / DEPENDANCE / ATTENTE base
    revenus_kw = (
        "revenu",
        "ca total",
        "ca ht",
        "frais port",
        "panier",
        "commissions marketplace",
    )
    couts_kw = (
        "coût",
        "cout",
        "douanes",
        "fournitures",
        "retours",
        "génériques",
        "generiques",
        "transport",
        "colis",
        "nb articles",
        "nb commandes",
        "unités",
        "unites",
        "poids",
    )
    marge_kw = ("marge", "taux marge", "profit produit", "gross")

    low = name.lower()
    if any(k in low for k in ("yoy",)) or name.endswith(" PY"):
        return "05 YoY"
    if any(k in low for k in marge_kw) and "reconstruit" not in low:
        # margin measures
        if "taux annulation" in low:
            return "01 KPI publiés"
        return "04 Marge"
    if "reconstruit" in low and ("marge" in low or "taux marge" in low):
        return "04 Marge"
    if "reconstruit" in low or any(k in low for k in revenus_kw):
        return "02 Revenus"
    if any(k in low for k in couts_kw):
        return "03 Coûts"
    if any(k in low for k in marge_kw):
        return "04 Marge"
    if name in {"Marge Brute", "Profit Produit Pur"}:
        return "04 Marge"
    if name.startswith("Unités") or name.startswith("Nb "):
        return "03 Coûts" if "colis" in low or "article" in low else "01 KPI publiés"
    return "01 KPI publiés"


def drop_measure_block(lines: list[str], name: str) -> list[str]:
    """Remove measure block + preceding /// comments + trailing blank."""
    out: list[str] = []
    i = 0
    # match both quoted and unquoted
    needles = (f"measure '{name}'", f"measure {name} =", f"measure {name}=")
    while i < len(lines):
        line = lines[i]
        if any(n in line for n in needles) and re.match(r"^\tmeasure ", line):
            # drop preceding /// already pushed
            while out and out[-1].startswith("\t///"):
                out.pop()
            # also drop blank line before comments? keep structure tidy
            while out and out[-1] == "":
                # keep one blank only if previous content exists — pop blanks before measure
                out.pop()
            i += 1
            while i < len(lines):
                s = lines[i]
                if re.match(r"^\tmeasure ", s) or s.startswith("\t///"):
                    break
                if s.startswith("\tannotation ") or s.startswith("\tpartition ") or s.startswith(
                    "\tcolumn "
                ):
                    break
                if s == "" and i + 1 < len(lines) and (
                    re.match(r"^\tmeasure ", lines[i + 1])
                    or lines[i + 1].startswith("\t///")
                    or lines[i + 1].startswith("\tannotation ")
                ):
                    i += 1
                    break
                i += 1
            # ensure a blank separator
            if out and out[-1] != "":
                out.append("")
            continue
        out.append(line)
        i += 1
    # tidy multiple blanks
    tidy: list[str] = []
    for s in out:
        if s == "" and tidy and tidy[-1] == "":
            continue
        tidy.append(s)
    return tidy


def inject_display_props(body_lines: list[str], folder: str, hidden: bool) -> list[str]:
    """Insert displayFolder / isHidden after formatString or before lineageTag."""
    # strip existing displayFolder / isHidden
    cleaned = [
        s
        for s in body_lines
        if not s.strip().startswith("displayFolder:") and not s.strip().startswith("isHidden:")
    ]
    # Quotes required: folder names contain spaces.
    props = [f'\t\tdisplayFolder: "{folder}"']
    if hidden:
        props.append("\t\tisHidden: true")

    # insert before lineageTag if present, else after formatString, else at end
    out: list[str] = []
    inserted = False
    for s in cleaned:
        if not inserted and s.strip().startswith("lineageTag:"):
            out.extend(props)
            out.append(s)
            inserted = True
            continue
        out.append(s)
    if not inserted:
        # after formatString
        out2: list[str] = []
        for s in out:
            out2.append(s)
            if not inserted and s.strip().startswith("formatString:"):
                out2.extend(props)
                inserted = True
        out = out2
    if not inserted:
        out.extend(props)
    return out


def main(apply: bool = False) -> int:
    text = TMDL.read_text(encoding="utf-8")
    measures = parse_measures(text)
    if len(measures) != 218:
        print(f"ERROR: expected 218 measures, got {len(measures)}", file=sys.stderr)
        return 1

    names = {m["name"] for m in measures}
    by_name = {m["name"]: m for m in measures}
    deps = build_deps(measures, names)
    rev = reverse_deps(deps)
    in_report = report_measure_names(names)
    in_py = python_refs(names)

    cat = classify(names, in_report, deps, rev)

    rows = []
    counts: dict[str, int] = defaultdict(int)
    for m in measures:
        name = m["name"]
        r = {
            "nom": name,
            "ligne": m["line"],
            "categorie": cat[name],
            "ref_report": "oui" if name in in_report else "non",
            "ref_mesure": "oui" if rev.get(name) else "non",
            "ref_python": "oui" if name in in_py else "non",
        }
        rows.append(r)
        counts[cat[name]] += 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["nom", "ligne", "categorie", "ref_report", "ref_mesure", "ref_python"],
        )
        w.writeheader()
        w.writerows(rows)

    print(f"CSV: {OUT_CSV}")
    for k in ("LIVREE", "DEPENDANCE", "CONTROLE", "ATTENTE", "MORTE"):
        print(f"  {k}: {counts[k]}")

    # Reconstruction chain safety
    chain = closure_callers(RECON_CHAIN_CORE & names, rev)
    displayed = sorted(n for n in chain if n in in_report)
    print("\n=== Chaîne reconstruite + dépendants (extrait) ===")
    print(f"  taille chaîne+dépendants: {len(chain)}")
    print(f"  dont affichés Report: {len(displayed)}")
    if displayed:
        print("  → NE PAS SUPPRIMER la chaîne reconstruite (dépendants Report présents).")
        for n in displayed[:15]:
            print(f"    - {n}")
        if len(displayed) > 15:
            print(f"    … +{len(displayed) - 15} autres")

    taux_rev = "Taux Marge Brute (revenu reconstruit)"
    if taux_rev in in_report:
        print(f"\n[{taux_rev}] est dans le Report → NE PAS SUPPRIMER.")

    # MORTE candidates: category MORTE, not in report/python, and either
    # unreferenced or only referenced by other MORTE candidates (iterative).
    morte_names = {r["nom"] for r in rows if r["categorie"] == "MORTE"}
    morte_safe: list[str] = []
    remaining_morte = set(morte_names)
    changed = True
    while changed:
        changed = False
        for n in sorted(remaining_morte):
            if n in in_report or n in in_py:
                continue
            callers = rev.get(n, set())
            if callers and not callers.issubset(set(morte_safe) | remaining_morte):
                # referenced by a non-MORTE survivor
                live_callers = callers - remaining_morte - set(morte_safe)
                if live_callers:
                    continue
            if not callers or callers.issubset(set(morte_safe)):
                morte_safe.append(n)
                remaining_morte.discard(n)
                changed = True
            elif callers.issubset(remaining_morte | set(morte_safe)):
                # only called by other MORTE — defer until leaf deleted; allow if all callers also safe-pending
                if all(
                    (c not in in_report and c not in in_py)
                    for c in callers
                ):
                    # mark leaves first; if this has only MORTE callers, wait
                    if not callers - set(morte_safe):
                        morte_safe.append(n)
                        remaining_morte.discard(n)
                        changed = True
    # Second pass: any MORTE whose callers are all in morte_safe
    changed = True
    while changed:
        changed = False
        for n in sorted(remaining_morte):
            if n in in_report or n in in_py:
                continue
            callers = rev.get(n, set())
            if callers.issubset(set(morte_safe)):
                morte_safe.append(n)
                remaining_morte.discard(n)
                changed = True

    # Si un dépendant de la chaîne reconstruite est au Report : ne supprimer
    # RIEN du cœur de cette chaîne (reprise Display hors périmètre).
    # Les orphelins MORTE qui référencent la chaîne (ex. Top Keep ISBN) restent
    # suppressibles s'ils ne sont pas dans la clôture des mesures Report.
    needed_by_report = in_report | closure_from(in_report, deps)
    if displayed:
        forbidden = (RECON_CHAIN_CORE & names) | needed_by_report
    else:
        forbidden = set(needed_by_report)
    to_delete = [n for n in morte_safe if n not in forbidden]
    if not displayed:
        for n in sorted((RECON_CHAIN_CORE | {taux_rev}) & names):
            if n in forbidden or n in in_py:
                continue
            if n not in to_delete:
                to_delete.append(n)

    print(f"\n=== MORTE suppressibles bruts: {len(morte_safe)} ===")
    for n in morte_safe:
        flag = " [bloqué chaîne reconstruit]" if n in forbidden else ""
        print(f"  - {n}{flag}")
    print(f"\n=== Suppressions effectives: {len(to_delete)} ===")
    for n in to_delete:
        print(f"  - {n}")
    if displayed:
        print(
            f"\n[garde-fou] Chaîne reconstruite non supprimée "
            f"({len(displayed)} dépendants Report)."
        )

    if not apply:
        print("\n(dry-run — relancer avec --apply pour écrire le TMDL)")
        return 0

    # --- APPLY ---
    names_before = [m["name"] for m in measures]
    lines = text.splitlines()

    print(f"\nApplication: suppression de {len(to_delete)} mesure(s) + displayFolder…")
    for n in to_delete:
        lines = drop_measure_block(lines, n)

    new_text = "\n".join(lines)
    if not new_text.endswith("\n"):
        new_text += "\n"

    # 2) Re-parse and inject displayFolder
    measures2 = parse_measures(new_text)
    # rebuild cat for remaining; deleted gone
    remaining_names = {m["name"] for m in measures2}
    # Keep original categories for survivors
    folders = {}
    hidden = {}
    for m in measures2:
        c = cat[m["name"]]
        folders[m["name"]] = display_folder(m["name"], c)
        hidden[m["name"]] = c == "CONTROLE"

    # Rewrite file measure by measure via body replacement
    # Safer: walk lines and rewrite each measure block's properties
    lines = new_text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(
            r"^\tmeasure (?:'((?:[^']|'')+)'|([A-Za-z_][\w ]*))\s*=",
            lines[i],
        )
        if not m:
            out.append(lines[i])
            i += 1
            continue
        raw = m.group(1) if m.group(1) is not None else m.group(2)
        name = raw.replace("''", "'").strip()
        block = [lines[i]]
        i += 1
        while i < len(lines):
            s = lines[i]
            if re.match(r"^\tmeasure ", s) or s.startswith("\t///"):
                break
            if s.startswith("\tannotation ") or s.startswith("\tpartition ") or s.startswith(
                "\tcolumn "
            ):
                break
            if s == "" and i + 1 < len(lines) and (
                re.match(r"^\tmeasure ", lines[i + 1]) or lines[i + 1].startswith("\t///")
            ):
                break
            block.append(s)
            i += 1
        block = inject_display_props(block, folders[name], hidden[name])
        out.extend(block)
        # preserve following blank if any
        if i < len(lines) and lines[i] == "":
            out.append("")
            i += 1

    final = "\n".join(out)
    if not final.endswith("\n"):
        final += "\n"
    TMDL.write_text(final, encoding="utf-8")

    # --- CONTROLES ---
    measures_after = parse_measures(final)
    names_after = [m["name"] for m in measures_after]
    deleted = [n for n in names_before if n not in set(names_after)]

    report_props = report_measure_names(set(names_before) | set(names_after))
    orphans = sorted(report_props - set(names_after))

    missing_folder = []
    flines = final.splitlines()
    for m in measures_after:
        idx = None
        for li, s in enumerate(flines):
            if not s.startswith("\tmeasure "):
                continue
            if f"'{m['name']}'" in s or re.match(
                rf"^\tmeasure {re.escape(m['name'])}\s*=", s
            ):
                idx = li
                break
        chunk = "\n".join(flines[idx : idx + 40]) if idx is not None else ""
        if "displayFolder:" not in chunk:
            missing_folder.append(m["name"])

    surviving_before = [n for n in names_before if n not in set(deleted)]
    names_ok = surviving_before == names_after

    print("\n========== CONTRÔLES FINAUX ==========")
    print(f"1. Références orphelines Report: {len(orphans)}")
    for o in orphans:
        print(f"   ORPHELIN: {o}")
    print(f"2. Mesures avant: {len(names_before)} → après: {len(names_after)}")
    print(f"   Supprimées ({len(deleted)}):")
    for n in deleted:
        print(f"   - {n}")
    print(f"3. Mesures sans displayFolder: {len(missing_folder)}")
    for n in missing_folder:
        print(f"   - {n}")
    print(f"4. Noms inchangés (hors supprimées): {'OUI' if names_ok else 'NON'}")
    if not names_ok:
        sb, sa = set(surviving_before), set(names_after)
        print(f"   only before: {sb - sa}")
        print(f"   only after: {sa - sb}")
        for a, b in zip(surviving_before, names_after):
            if a != b:
                print(f"   order/name drift: {a!r} vs {b!r}")
                break

    # CSV TÂCHE 1 = classification des 218 mesures avant suppression (déjà écrit).
    # Annotate deleted rows for traceability.
    out_deleted = ROOT / "scripts/validation/measures_deleted.csv"
    with out_deleted.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nom", "categorie", "raison"])
        w.writeheader()
        for n in deleted:
            w.writerow(
                {
                    "nom": n,
                    "categorie": cat[n],
                    "raison": "MORTE 3x non (report/mesure/python)",
                }
            )
    print(f"CSV suppressions: {out_deleted}")

    return 0 if not orphans and not missing_folder and names_ok else 1


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    raise SystemExit(main(apply=apply))
