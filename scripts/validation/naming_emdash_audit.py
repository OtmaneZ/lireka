#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LECTURE SEULE. Aucune écriture.
Analyse de la convention de nommage : em-dash et autres caractères non-ASCII
dans les NOMS de mesures de _Mesures.tmdl, et leur résolution effective
dans le Report (.json) et en références croisées entre mesures.
"""
import os
import re
import glob
import unicodedata
from collections import defaultdict, Counter

BASE = "/root/lireka"
MES = os.path.join(BASE, "powerbi", "Lireka_Profitabilite.SemanticModel",
                   "definition", "tables", "_Mesures.tmdl")
REPORT_DIR = os.path.join(BASE, "powerbi", "Lireka_Profitabilite.Report")
SEM_DIR = os.path.join(BASE, "powerbi", "Lireka_Profitabilite.SemanticModel")

# ---------------------------------------------------------------------------
# 1. Extraction des noms de mesures depuis _Mesures.tmdl
#    Deux formes : measure 'Nom avec espaces' = ...   |  measure Nom = ...
# ---------------------------------------------------------------------------
with open(MES, "r", encoding="utf-8") as f:
    tmdl_text = f.read()

names = []
for m in re.finditer(r"^\s*measure\s+('([^']*)'|([^\s=]+))\s*=", tmdl_text, re.M):
    name = m.group(2) if m.group(2) is not None else m.group(3)
    names.append(name)

ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ()")

def nonascii_chars(s):
    return [c for c in s if c not in ALLOWED]

# map char -> codepoint label
def cp(c):
    return f"U+{ord(c):04X}"

char_names = {
    "\u2014": "EM DASH",
    "\u2013": "EN DASH",
    "\u002D": "HYPHEN-MINUS (ASCII)",
    "\u2019": "RIGHT SINGLE QUOTATION MARK (apostrophe typo)",
    "\u00A0": "NO-BREAK SPACE",
    "\u200B": "ZERO WIDTH SPACE",
}

measures_with_special = []   # (name, [chars])
char_counter = Counter()
for name in names:
    specials = nonascii_chars(name)
    if specials:
        measures_with_special.append((name, specials))
        for c in set(specials):
            char_counter[c] += 1

print("=" * 70)
print("TÂCHE 2 — Inventaire caractères hors [A-Za-z0-9 espace parenthèses]")
print("=" * 70)
print(f"Total mesures détectées dans _Mesures.tmdl : {len(names)}")
print(f"Mesures avec caractère(s) spécial(aux)     : {len(measures_with_special)}")
print()
print("Compte par caractère (nb de mesures contenant au moins 1 occurrence) :")
for c, n in char_counter.most_common():
    label = char_names.get(c, unicodedata.name(c, "?"))
    print(f"  {cp(c)}  {label:<45} : {n} mesures")
print()
print("Détail (nom exact -> caractères) :")
for name, specials in measures_with_special:
    uniq = sorted(set(specials), key=lambda x: ord(x))
    tags = ", ".join(f"{cp(c)}" for c in uniq)
    print(f"  [{tags}]  {name!r}")

# ---------------------------------------------------------------------------
# 3. Références effectives dans le Report (.json / .tmdl du Report) et
#    références croisées entre mesures dans _Mesures.tmdl
# ---------------------------------------------------------------------------
report_files = []
for ext in ("*.json", "*.tmdl"):
    report_files += glob.glob(os.path.join(REPORT_DIR, "**", ext), recursive=True)

report_blobs = {}
for fp in report_files:
    try:
        with open(fp, "r", encoding="utf-8") as f:
            report_blobs[fp] = f.read()
    except Exception as e:
        report_blobs[fp] = ""

# focus sur mesures em-dash
EMDASH = "\u2014"
emdash_measures = [n for n, s in measures_with_special if EMDASH in s]

print()
print("=" * 70)
print("TÂCHE 3 — Résolution effective des mesures em-dash (U+2014)")
print("=" * 70)
print(f"Mesures em-dash dans _Mesures.tmdl : {len(emdash_measures)}")

# citons les 3 mesures nommées dans le ticket + toutes les em-dash
target_names = ["Top Loss — Revenue", "KPI Compact — Revenue",
                "Top Rank Loss — Gross Profit"]

def count_refs_in_report(name):
    hits = []
    for fp, blob in report_blobs.items():
        if name in blob:
            hits.append(os.path.relpath(fp, BASE))
    return hits

def count_xref_in_tmdl(name, self_name):
    # référence croisée dans une AUTRE mesure : [Nom]
    pat = "[" + name + "]"
    return tmdl_text.count(pat)

print()
print("Mesures citées dans le ticket :")
for n in target_names:
    present = n in names
    refs = count_refs_in_report(n)
    xref = tmdl_text.count("[" + n + "]")
    print(f"  {n!r}")
    print(f"     définie dans _Mesures.tmdl : {present}")
    print(f"     référencée dans Report      : {len(refs)} fichier(s)")
    for r in refs[:5]:
        print(f"        - {r}")
    print(f"     référencée [] dans TMDL     : {xref} occurrence(s) (def incluse)")

print()
print("Toutes les mesures em-dash — couverture Report + xref TMDL :")
for n in emdash_measures:
    refs = count_refs_in_report(n)
    xref = tmdl_text.count("[" + n + "]")
    flag = "RÉFÉRENCÉE" if refs else "non trouvée dans Report"
    print(f"  {flag:>24}  refReport={len(refs):<2} xrefTMDL={xref:<2}  {n!r}")

# recherche d'erreurs de résolution partout dans le projet
print()
print("Recherche 'Missing_References' / 'MissingReference' / 'Unresolved' dans tout le projet :")
err_hits = []
for fp in glob.glob(os.path.join(BASE, "powerbi", "**", "*"), recursive=True):
    if not os.path.isfile(fp):
        continue
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            blob = f.read()
    except Exception:
        continue
    for tok in ("Missing_References", "MissingReference", "Unresolved", "unresolved"):
        if tok in blob:
            err_hits.append((os.path.relpath(fp, BASE), tok))
if err_hits:
    for fp, tok in err_hits:
        print(f"  {tok} -> {fp}")
else:
    print("  Aucune occurrence dans powerbi/**")

# ---------------------------------------------------------------------------
# 4. Encodage / BOM
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("TÂCHE 4 — Encodage & BOM (.tmdl SemanticModel + .json/.tmdl Report)")
print("=" * 70)
def check_bom(fp):
    with open(fp, "rb") as f:
        head = f.read(4)
    bom = None
    if head.startswith(b"\xef\xbb\xbf"):
        bom = "UTF-8 BOM"
    elif head.startswith(b"\xff\xfe"):
        bom = "UTF-16 LE BOM"
    elif head.startswith(b"\xfe\xff"):
        bom = "UTF-16 BE BOM"
    # test décodage utf-8
    try:
        with open(fp, "rb") as f:
            f.read().decode("utf-8")
        utf8_ok = True
    except UnicodeDecodeError:
        utf8_ok = False
    return bom, utf8_ok

groups = {
    "SemanticModel .tmdl": glob.glob(os.path.join(SEM_DIR, "**", "*.tmdl"), recursive=True),
    "Report .json": glob.glob(os.path.join(REPORT_DIR, "**", "*.json"), recursive=True),
    "Report .tmdl": glob.glob(os.path.join(REPORT_DIR, "**", "*.tmdl"), recursive=True),
}
for label, files in groups.items():
    boms = Counter()
    utf8_fail = []
    for fp in files:
        bom, ok = check_bom(fp)
        boms[bom or "sans BOM"] += 1
        if not ok:
            utf8_fail.append(os.path.relpath(fp, BASE))
    print(f"  {label:<22} : {len(files)} fichiers | BOM={dict(boms)} | "
          f"non-UTF8={len(utf8_fail)}")
    for fp in utf8_fail[:5]:
        print(f"      NON-UTF8: {fp}")

# ---------------------------------------------------------------------------
# 5. Doublons silencieux : noms qui ne diffèrent que par tiret/apostrophe/espace
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("TÂCHE 5 — Doublons silencieux (diffèrent seulement par tiret/apostrophe/espace)")
print("=" * 70)
def normalize(s):
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2212", "-")
    s = s.replace("\u2019", "'").replace("\u00A0", " ").replace("\u200B", "")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

buckets = defaultdict(list)
for n in names:
    buckets[normalize(n)].append(n)

found_dup = False
for key, group in buckets.items():
    if len(set(group)) > 1:
        found_dup = True
        print(f"  Clé normalisée {key!r} :")
        for g in sorted(set(group)):
            print(f"      {g!r}")
if not found_dup:
    print("  Aucun doublon silencieux détecté.")
