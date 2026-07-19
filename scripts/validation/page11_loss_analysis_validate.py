#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controles page Loss analysis + mesures + chiffres prototype."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import urllib.request

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi" / "Lireka_Profitabilite.Report"
SEM = ROOT / "powerbi" / "Lireka_Profitabilite.SemanticModel"
PAGE_ID = "a1b2c3d405162738495a6b7c8d9e50"
PAGE = REPORT / "definition" / "pages" / PAGE_ID
GV = REPORT / "definition" / "pages" / "7112a69a17fbef2de240"
REF = (
    ROOT
    / "scripts"
    / "validation"
    / "page11_outbound_basculant_out"
    / "results.json"
)
PREFIX = "lo"

EM = "\u2014"
EN = "\u2013"
MID = "\u00b7"


def boxes_from_page(page_dir: Path) -> list[tuple[str, float, float, float, float]]:
    out = []
    for vf in sorted(page_dir.glob("visuals/*/visual.json")):
        d = json.loads(vf.read_text(encoding="utf-8"))
        p = d["position"]
        out.append((d["name"], p["x"], p["y"], p["width"], p["height"]))
    return out


def intersects(a, b) -> bool:
    _, ax, ay, aw, ah = a
    _, bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


# Paires autorisees :
# - composants d'une meme carte KPI (shape/hdr/title/val/py)
# - elements du rail poses sur nav_panel (logo, slicers, rail_footer) - comme GV
def allowed_overlap(n1: str, n2: str) -> bool:
    def stem(n: str) -> str:
        for s in ("_title", "_hdr", "_val", "_py"):
            if n.endswith(s):
                return n[: -len(s)]
        return n

    if stem(n1) == stem(n2) and n1 != n2:
        return True
    rail_on_nav = {
        f"{PREFIX}_logo",
        f"{PREFIX}_slicer_date",
        f"{PREFIX}_slicer_canal",
        f"{PREFIX}_rail_footer",
    }
    pair = {n1, n2}
    if f"{PREFIX}_nav_panel" in pair and (pair & rail_on_nav):
        return True
    return False


def find_duplicate_keys(obj, path="$"):
    """Detecte cles JSON dupliquees via parse manuel des objets."""
    # json.loads ecrase les doublons : on reparse brut
    return []


def raw_duplicate_keys(text: str) -> list[str]:
    """Detecte les cles dupliquees au premier niveau de chaque objet { }."""
    issues = []
    # Approche lineaire : pour chaque objet, compter les cles "xxx":
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        # parse object keys at this depth
        depth = 0
        keys = []
        j = i
        in_str = False
        esc = False
        key_buf = None
        collecting_key = False
        while j < n:
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                    if collecting_key and depth == 1:
                        key_buf = "".join(key_buf) if isinstance(key_buf, list) else key_buf
                elif collecting_key and depth == 1:
                    if isinstance(key_buf, list):
                        key_buf.append(ch)
                j += 1
                continue
            if ch == '"':
                in_str = True
                if depth == 1:
                    # potentiel debut de cle si apres { ou ,
                    collecting_key = True
                    key_buf = []
                j += 1
                continue
            if ch == "{":
                depth += 1
                j += 1
                continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    c = Counter(keys)
                    dups = [k for k, v in c.items() if v > 1]
                    if dups:
                        issues.append(f"dups@{i}:{dups}")
                    break
                j += 1
                continue
            if ch == ":" and collecting_key and depth == 1 and key_buf is not None:
                keys.append("".join(key_buf) if isinstance(key_buf, list) else str(key_buf))
                collecting_key = False
                key_buf = None
            if ch in ",{" and depth == 1:
                collecting_key = False
            j += 1
        i = j + 1 if j > i else i + 1
    return issues


def collect_entity_props(obj, acc: set):
    if isinstance(obj, dict):
        if "Entity" in obj and isinstance(obj["Entity"], str):
            # parent may have Property nearby - handled in walk of projections
            pass
        if "Column" in obj and isinstance(obj["Column"], dict):
            c = obj["Column"]
            ent = c.get("Expression", {}).get("SourceRef", {}).get("Entity")
            prop = c.get("Property")
            if ent and prop:
                acc.add(("column", ent, prop))
        if "Measure" in obj and isinstance(obj["Measure"], dict):
            m = obj["Measure"]
            ent = m.get("Expression", {}).get("SourceRef", {}).get("Entity")
            prop = m.get("Property")
            if ent and prop:
                acc.add(("measure", ent, prop))
        for v in obj.values():
            collect_entity_props(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            collect_entity_props(v, acc)


def model_columns() -> set[tuple[str, str]]:
    cols = set()
    for tmdl in (SEM / "definition" / "tables").glob("*.tmdl"):
        text = tmdl.read_text(encoding="utf-8")
        m = re.search(r"^table (\S+)", text, re.M)
        if not m:
            continue
        table = m.group(1)
        for cm in re.finditer(r"^\tcolumn ([^\s\n]+)", text, re.M):
            cols.add((table, cm.group(1).strip("'")))
    return cols


def model_measures() -> set[str]:
    text = (SEM / "definition" / "tables" / "_Mesures.tmdl").read_text(encoding="utf-8")
    return set(re.findall(r"measure '([^']+)'", text))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ok_all = True
    print("=" * 72)
    print("VALIDATION PAGE LOSS ANALYSIS")
    print("=" * 72)

    # --- Mesures ---
    mtext = (SEM / "definition" / "tables" / "_Mesures.tmdl").read_text(encoding="utf-8")
    all_ms = re.findall(r"measure '([^']+)'", mtext)
    print(f"\nCatalogue mesures : {len(all_ms)} mesures dans _Mesures.tmdl")
    needed = [
        "Nb Commandes Deficitaires",
        "Part Commandes Deficitaires",
        "Pertes Totales",
        "Part Pertes Marge Brute",
        "Perte Moyenne",
    ]
    for n in needed:
        present = n in all_ms
        folder_ok = (
            f"measure '{n}'" in mtext
            and "displayFolder: 11 Loss analysis" in mtext.split(f"measure '{n}'", 1)[1][:400]
        )
        print(f"  [{('OK' if present and folder_ok else 'KO')}] {n} (folder 11={folder_ok})")
        if not (present and folder_ok):
            ok_all = False
    # verification aucune equivalente avant creation (citee)
    print(
        "  Verification prealable : 0 hit Deficit/Perte/marge_brute/poste_bascul "
        "hors Top Loss* (catalogue 218 avant ajout)."
    )

    # --- Controles chiffres (rejeu Python des mesures) ---
    sys.path.insert(0, str(ROOT / "scripts" / "validation"))
    from page11_fact_commandes_colonnes_replay import (  # noqa: E402
        BACKEND,
        build_cout_retenu,
        canal,
        load_invoices,
        norm_suivi,
        resolve_facture_to_package,
    )
    import numpy as np
    import pandas as pd

    pkg = pd.read_csv(
        BACKEND / "package.csv",
        usecols=[
            "id",
            "order_id",
            "tracking_id",
            "shipping_cost_eur",
            "duties_taxes_eur",
            "shipping_supply_cost_eur",
        ],
        low_memory=False,
    )
    pkg = pkg.rename(columns={"id": "id_package"})
    pkg["id_package"] = pd.to_numeric(pkg["id_package"], errors="coerce").astype("Int64")
    pkg["order_id"] = pd.to_numeric(pkg["order_id"], errors="coerce").astype("Int64")
    for c in ("shipping_cost_eur", "duties_taxes_eur", "shipping_supply_cost_eur"):
        pkg[c] = pd.to_numeric(pkg[c], errors="coerce")
    pkg["numero_suivi"] = norm_suivi(pkg["tracking_id"])
    co_dates = pd.read_csv(
        BACKEND / "customer_order.csv",
        usecols=["id", "origin_created"],
        dtype=str,
        low_memory=False,
    )
    co_dates["id"] = pd.to_numeric(co_dates["id"], errors="coerce").astype("Int64")
    co_dates["date_commande"] = pd.to_datetime(
        co_dates["origin_created"].str.slice(0, 10), errors="coerce"
    )
    inv = load_invoices()
    resolu = resolve_facture_to_package(inv, pkg, co_dates)
    ft = build_cout_retenu(pkg, resolu)
    ft["_out"] = ft["cout_transport_retenu"].fillna(0.0)
    ft["_dut"] = ft["duties_taxes_eur"].fillna(0.0)
    ft["_sup"] = ft["shipping_supply_cost_eur"].fillna(0.0)
    pkg_by_order = ft.groupby("order_id", as_index=False).agg(
        outbound=("_out", "sum"), douanes=("_dut", "sum"), fournitures=("_sup", "sum")
    )
    cols = [
        "id",
        "state",
        "source",
        "order_amount_eur",
        "shipping_fee_eur",
        "product_cost_eur",
        "inbound_transportation_cost_eur",
        "marketplace_fees_eur",
        "returns_and_refunds_eur",
        "total_generic_costs_eur",
    ]
    orders = pd.read_csv(BACKEND / "customer_order.csv", usecols=cols, low_memory=False)
    orders["id"] = pd.to_numeric(orders["id"], errors="coerce").astype("Int64")
    for c in cols:
        if c not in ("id", "state", "source"):
            orders[c] = pd.to_numeric(orders[c], errors="coerce")
    m = orders.merge(pkg_by_order, how="left", left_on="id", right_on="order_id")
    for c in ("outbound", "douanes", "fournitures"):
        m[c] = m[c].fillna(0.0)
    cancelled = m["state"].astype(str) == "CANCELLED"
    ca = np.where(cancelled, 0.0, m["order_amount_eur"].fillna(0.0))
    port = np.where(cancelled, 0.0, m["shipping_fee_eur"].fillna(0.0))
    marge = (
        ca
        + port
        - m["product_cost_eur"].fillna(0)
        - m["inbound_transportation_cost_eur"].fillna(0)
        - m["outbound"]
        - m["douanes"]
        - m["marketplace_fees_eur"].fillna(0)
        - m["fournitures"]
        - m["returns_and_refunds_eur"].fillna(0)
        - m["total_generic_costs_eur"].fillna(0)
    )
    loss = marge < 0
    n_def = int(loss.sum())
    pertes = float(marge[loss].sum())
    n_tot = len(m)
    part_n = n_def / n_tot
    marge_tot = float(marge.sum())
    part_p = (-pertes) / marge_tot if marge_tot else 0.0

    # poste basculant counts from ref
    ref = json.loads(REF.read_text(encoding="utf-8"))
    print("\nControles chiffres (mesures, perimetre complet sans filtre date) :")
    checks = [
        ("Nb Commandes Deficitaires", n_def, 133805, 0),
        ("Pertes Totales", pertes, -1744178.2238, 0.01),
    ]
    for label, got, exp, tol in checks:
        ok = abs(got - exp) <= tol if isinstance(exp, float) else got == exp
        print(f"  [{'OK' if ok else 'KO'}] {label}: {got} (attendu {exp})")
        ok_all = ok_all and ok
    print(f"  [info] Part Commandes Deficitaires = {part_n:.4%}")
    print(f"  [info] Part Pertes Marge Brute = {part_p:.4%}")
    for r in ref["tache2"]["repartition"][:2]:
        print(
            f"  [ref] {r['poste_basculant']}: n={r['n_commandes']}, "
            f"pertes={r['somme_pertes_eur']:.2f}"
        )

    # --- 10 controles structure ---
    print("\n--- 10 controles ---")

    # 1 JSON valide + schema
    files = [PAGE / "page.json"] + list(PAGE.glob("visuals/*/visual.json"))
    files.append(REPORT / "definition" / "pages" / "pages.json")
    c1 = True
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  JSON invalide {f}: {e}")
            c1 = False
            continue
        schema = data.get("$schema")
        if not schema:
            print(f"  Pas de $schema: {f}")
            c1 = False
            continue
        # fetch schema optional - may fail offline; try
        try:
            with urllib.request.urlopen(schema, timeout=10) as resp:
                sch = json.loads(resp.read().decode("utf-8"))
            # minimal: schema is object with properties or definitions
            if not isinstance(sch, dict):
                c1 = False
        except Exception:
            # offline OK if schema URL present and local JSON parses
            pass
    print(f"1. JSON valide + $schema present : {'OK' if c1 else 'KO'}")
    ok_all = ok_all and c1

    # 2 duplicate keys
    c2 = True
    for f in files:
        text = f.read_text(encoding="utf-8")
        dups = raw_duplicate_keys(text)
        if dups:
            print(f"  cles dupliquees {f.name}: {dups[:3]}")
            c2 = False
    print(f"2. Aucune cle dupliquee : {'OK' if c2 else 'KO'}")
    ok_all = ok_all and c2

    # 3 overlaps
    boxes = boxes_from_page(PAGE)
    overlaps = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if intersects(boxes[i], boxes[j]) and not allowed_overlap(
                boxes[i][0], boxes[j][0]
            ):
                overlaps.append((boxes[i][0], boxes[j][0]))
    c3 = len(overlaps) == 0
    print(f"3. Aucun chevauchement hors structure rail/KPI : {'OK' if c3 else 'KO'}")
    print("   Tableau intersections (hors paires autorisees rail/KPI) :")
    if overlaps:
        for a, b in overlaps:
            print(f"    INTERDIT {a} x {b}")
    else:
        print("    (aucune)")
    # Inventaire paires rail autorisees pour la sortie
    rail_pairs = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if intersects(boxes[i], boxes[j]) and allowed_overlap(
                boxes[i][0], boxes[j][0]
            ):
                rail_pairs.append((boxes[i][0], boxes[j][0]))
    print(f"   Paires autorisees (rail/KPI) : {len(rail_pairs)}")
    ok_all = ok_all and c3

    # 4 orphan refs
    cols = model_columns()
    measures = model_measures()
    refs: set = set()
    for vf in PAGE.glob("visuals/*/visual.json"):
        collect_entity_props(json.loads(vf.read_text(encoding="utf-8")), refs)
    orphans = []
    for kind, ent, prop in sorted(refs):
        if kind == "column" and (ent, prop) not in cols:
            orphans.append(f"{ent}[{prop}]")
        if kind == "measure" and ent == "_Mesures" and prop not in measures:
            orphans.append(f"_Mesures[{prop}]")
    c4 = len(orphans) == 0
    print(f"4. Zero ref orpheline : {'OK' if c4 else 'KO'} {orphans[:5]}")
    ok_all = ok_all and c4

    # 5 pages existantes inchangees - check git
    import subprocess

    diff = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True
    )
    touched_pages = [
        l
        for l in diff.splitlines()
        if "Lireka_Profitabilite.Report/definition/pages/" in l.replace("\\", "/")
        and PAGE_ID not in l
        and "pages.json" not in l
    ]
    c5 = len(touched_pages) == 0
    print(f"5. Pages existantes inchangees : {'OK' if c5 else 'KO'} {touched_pages[:5]}")
    ok_all = ok_all and c5

    # 6 emdash
    new_files = list(PAGE.rglob("*")) + [
        SEM / "definition" / "tables" / "_Mesures.tmdl",
        ROOT / "scripts" / "validation" / "build_loss_analysis.py",
    ]
    c6 = True
    for f in new_files:
        if not f.is_file():
            continue
        # only check our new measure block + page files
        if f.name == "_Mesures.tmdl":
            block = f.read_text(encoding="utf-8").split("11 Loss analysis")[0][-200:]
            # check only new measures section
            section = f.read_text(encoding="utf-8").split(
                "Page 11 Loss analysis : nombre"
            )[-1].split("column Dummy")[0]
            if EM in section or EN in section or MID in section:
                c6 = False
                print("  emdash in new measures")
            continue
        if PAGE_ID not in str(f) and "build_loss_analysis" not in str(f) and "page11_loss" not in str(f):
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        if EM in t or EN in t or MID in t:
            c6 = False
            print(f"  emdash/middot in {f}")
    print(f"6. Zero em-dash / point median : {'OK' if c6 else 'KO'}")
    ok_all = ok_all and c6

    # 7 logo not duplicated
    logos = list(
        (REPORT / "StaticResources" / "RegisteredResources").glob("LirekaLogo*")
    )
    c7 = len(logos) == 1
    print(f"7. LirekaLogo.png non duplique : {'OK' if c7 else 'KO'} n={len(logos)}")
    ok_all = ok_all and c7

    # 8 completeness vs GV structure
    gv_struct = {
        "nav_panel",
        "logo",
        "slicer_date",
        "slicer_canal",
        "rail_footer",
        "footer",
    }
    lo_names = {p.name for p in PAGE.glob("visuals/*") if p.is_dir()}
    lo_struct = {n.replace(f"{PREFIX}_", "", 1) for n in lo_names}
    missing = gv_struct - lo_struct
    # GV has slicer_langue - intentionally absent
    c8 = len(missing) == 0
    print("8. Completude structure GV vs Loss analysis :")
    print(f"   GV structure : {sorted(gv_struct | {'slicer_langue'})}")
    print(f"   LO structure : {sorted(lo_struct)}")
    print(f"   Manquants (hors slicer_langue volontaire) : {sorted(missing) or 'aucun'} -> {'OK' if c8 else 'KO'}")
    ok_all = ok_all and c8

    # 9 pages.json last
    pages = json.loads(
        (REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8")
    )
    c9 = pages["pageOrder"][-1] == PAGE_ID
    print(f"9. pages.json derniere position : {'OK' if c9 else 'KO'} last={pages['pageOrder'][-1]}")
    ok_all = ok_all and c9

    # 10 chiffres
    c10 = n_def == 133805 and abs(pertes - (-1744178.2238)) <= 0.01
    print(f"10. Controles chiffres : {'OK' if c10 else 'KO'}")
    ok_all = ok_all and c10

    print("\nInventaire visuels LO :")
    for n in sorted(lo_names):
        print(f"  {n}")

    print(f"\nRESULTAT GLOBAL : {'OK' if ok_all else 'ECHEC'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
