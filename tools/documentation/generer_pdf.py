"""Usage interne ZineInsights. Génère les PDF de la documentation client (docs/1 à 6) dans docs/pdf.

Usage : python3 tools/documentation/generer_pdf.py
Dépendances : markdown, pymdown-extensions ; rendu PDF par rendre_pdf.js (Node, Playwright).
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

import markdown

RACINE = Path(__file__).resolve().parents[2]
DOCS = RACINE / "docs"
SORTIE = DOCS / "pdf"
INTERDITS = {"—": "tiret cadratin", "·": "point médian"}

CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
:root { --nuit: #16233f; --nuit-clair: #e8ecf3; --texte: #1f2733; --discret: #5b6573; --filet: #d3d9e2; }
* { box-sizing: border-box; }
html, body { margin: 0; background: #fff; }
body { font-family: "Inter", "Segoe UI", Arial, sans-serif; font-size: 9.8pt; line-height: 1.55; color: var(--texte); }
.entete { border-bottom: 2px solid var(--nuit); padding-bottom: 10px; margin-bottom: 18px; }
.entete .projet { font-size: 8pt; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--nuit); margin: 0 0 6px; }
.entete h1 { font-size: 22pt; font-weight: 700; color: var(--nuit); margin: 0; line-height: 1.15; letter-spacing: -0.01em; }
.entete .meta { font-size: 8.8pt; color: var(--discret); margin: 6px 0 0; }
p { margin: 5px 0 8px; orphans: 3; widows: 3; }
strong { font-weight: 600; color: #111826; }
h2 { background: var(--nuit); color: #fff; font-size: 12pt; font-weight: 600; padding: 7px 12px; border-radius: 3px; margin: 22px 0 10px; break-after: avoid; }
h3 { color: var(--nuit); font-size: 10.8pt; font-weight: 700; margin: 16px 0 5px; padding-left: 9px; border-left: 3px solid var(--nuit); break-after: avoid; }
ul, ol { margin: 4px 0 10px; padding-left: 20px; }
li { margin: 3px 0; }
table { width: 100%; border-collapse: collapse; margin: 6px 0 12px; font-size: 8.9pt; line-height: 1.45; break-inside: avoid; }
thead { display: table-header-group; }
th { background: var(--nuit-clair); color: var(--nuit); font-weight: 600; text-align: left; padding: 6px 8px; border-bottom: 1.5px solid var(--nuit); }
td { padding: 6px 8px; border-bottom: 1px solid var(--filet); vertical-align: top; }
th:first-child, td:first-child { min-width: 36mm; }
tr { break-inside: avoid; }
code { font-family: "JetBrains Mono", Consolas, monospace; font-size: 8.2pt; background: #f1f3f7; border: 1px solid #e1e5ec; border-radius: 3px; padding: 0 3px; }
pre { background: #f5f7fa; border: 1px solid #dfe4eb; border-left: 3px solid var(--nuit); border-radius: 3px; padding: 8px 11px; margin: 6px 0 12px; overflow: hidden; break-inside: avoid; }
pre code { background: none; border: none; padding: 0; font-size: 8.2pt; line-height: 1.5; white-space: pre-wrap; }
hr { display: none; }
"""

PIED = """
<div style="width:100%; font-family: Inter, Arial, sans-serif; font-size:7.5pt; color:#5b6573; padding:0 18mm; display:flex; justify-content:space-between;">
  <span>Projet Power BI Lireka | {titre}</span>
  <span>Page <span class="pageNumber"></span> sur <span class="totalPages"></span></span>
</div>
"""


def preparer(texte):
    """Ajoute une ligne vide avant chaque liste qui suit directement un paragraphe (exigence de Python-Markdown)."""
    lignes = texte.split("\n")
    sortie = []
    for i, ligne in enumerate(lignes):
        debut_liste = re.match(r"^(\s*)([-*]|\d+\.)\s", ligne)
        if debut_liste and i > 0 and sortie and sortie[-1].strip() and not re.match(r"^\s*([-*]|\d+\.)\s", sortie[-1]) and not sortie[-1].startswith(" "):
            sortie.append("")
        sortie.append(ligne)
    return "\n".join(sortie)


def typographie(corps):
    """Espaces insécables à la française, hors blocs de code."""
    morceaux = re.split(r"(<pre>.*?</pre>|<code>.*?</code>)", corps, flags=re.S)
    for i in range(0, len(morceaux), 2):
        m = morceaux[i].replace("« ", "«\u00a0").replace(" »", "\u00a0»")
        m = re.sub(r"\b([Dd]ocument) (\d)", "\\1\u00a0\\2", m)
        m = m.replace("Ci-dessous", "Ci\u2011dessous")
        morceaux[i] = re.sub(r" ([:;?!%])", "\u00a0\\1", m)
    return "".join(morceaux)


def convertir(chemin):
    texte = chemin.read_text(encoding="utf-8")
    for car, nom in INTERDITS.items():
        if car in texte:
            sys.exit(f"{chemin.name} : {nom} interdit dans un document client")
    titre_complet = re.search(r"^# (.+)$", texte, re.M).group(1).strip()
    texte = re.sub(r"^# .+\n", "", texte, count=1, flags=re.M)
    meta = re.search(r"^(État au .+|Version finale .+)$", texte, re.M)
    if meta:
        texte = texte.replace(meta.group(0) + "\n", "", 1)
    numero, titre = titre_complet.split(". ", 1)
    corps = markdown.markdown(preparer(texte), extensions=["tables", "pymdownx.superfences", "sane_lists"])
    corps = typographie(corps)
    meta_html = f"Document {numero} sur 6"
    if meta:
        meta_html += f" &nbsp;|&nbsp; {html.escape(meta.group(1).rstrip('.'))}"
    page = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>{html.escape(titre)}</title>
<style>{CSS}</style></head><body>
<div class="entete"><p class="projet">Projet Power BI Lireka</p><h1>{html.escape(titre)}</h1><p class="meta">{meta_html}</p></div>
{corps}
</body></html>"""
    return numero, titre, page


def main():
    SORTIE.mkdir(exist_ok=True)
    taches = []
    for chemin in sorted(DOCS.glob("[1-6]-*.md")):
        numero, titre, page = convertir(chemin)
        fichier_html = SORTIE / f"{chemin.stem}.html"
        fichier_html.write_text(page, encoding="utf-8")
        taches.append({
            "html": str(fichier_html),
            "pdf": str(SORTIE / f"Lireka Power BI - {numero}. {titre}.pdf"),
            "pied": PIED.format(titre=html.escape(f"{numero}. {titre}")),
        })
    try:
        subprocess.run(["node", str(Path(__file__).with_name("rendre_pdf.js"))], input=json.dumps(taches),
                       text=True, check=True)
    finally:
        for t in taches:
            Path(t["html"]).unlink(missing_ok=True)

if __name__ == "__main__":
    main()
