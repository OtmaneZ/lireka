---
id: DEFERRED-LLM-powerbi-ui-backlog
status: DEFERRED
do_not_implement_now: true
tags:
  - deferred
  - backlog
  - powerbi
  - ui
  - grain-auto
  - langue-fr-en
  - date-ga
  - mockup-20260716
scope: Lireka_Profitabilite.Report
spec_source: docs/01-cadrage/20260716_Finance_dashboard_mockups.pdf
decision_date: 2026-07-18
decision: leave aside for now — continue V1 pages/KPIs first
---

# DEFERRED — Power BI UI backlog (grain / FR-EN / date GA)

> **LLM LOOKUP KEYS** : `DEFERRED-LLM-powerbi-ui-backlog` · `deferred powerbi ui` · `grain auto` · `ParamLangueUI` · `date Google Analytics` · `ne pas implémenter maintenant`
>
> **Statut** : `DEFERRED` — ne pas brancher / ne pas prioriser tant que les pages V1 (KPIs, charts, tables) ne sont pas avancées.
>
> **Décision** : 18/07/2026 — laisser de côté ; documenter ici pour reprise ultérieure.

---

## Items reportés (mockup Finance dashboard)

| # | Item | Spec mockup | État modèle | État rapport | Action future |
|---|------|-------------|-------------|--------------|---------------|
| D1 | Grain auto axe temps jour / semaine / mois | Revenue by channel/language : day si timeframe &lt; 1 semaine, week si &lt; 1 mois, month sinon | Table field parameter `_ParamAxePeriode` existe | **Non branché** (axe charts figé mois) | Brancher le field param sur les charts ; logique auto selon filtre date |
| D2 | Dropdown langue UI FR / EN (droite) | Language dropdown right-hand side (FR ↔ EN) | Table `_ParamLangueUI` existe (`FR`/`EN`) | **Absent du rapport** | Slicer à droite + libellés KPI/titres dynamiques |
| D3 | Filtre date type Google Analytics | Date filter similar to Google Analytics | `dim_date` + slicer Between | Slicer **Between** classique seulement | Presets (7j, 30j, mois, custom, comparaison) type GA |

---

## Emplacements code (reprendre ici)

| Élément | Chemin |
|---------|--------|
| Field param grain | `powerbi/Lireka_Profitabilite.SemanticModel/definition/tables/_ParamAxePeriode.tmdl` |
| Param FR/EN | `powerbi/Lireka_Profitabilite.SemanticModel/definition/tables/_ParamLangueUI.tmdl` |
| Spec mockup | `docs/01-cadrage/20260716_Finance_dashboard_mockups.pdf` (slides layout + General View) |
| Doc langues (cadrage) | `docs/01-cadrage/20260716_Claude_menu_déroulant_langues_PowerBI.docx` |

### `_ParamAxePeriode` (déjà défini)

- `Jour` → `dim_date[date]`
- `Semaine` → `dim_date[semaine_annee_libelle]`
- `Mois` → `dim_date[nom_mois_annee]`

### `_ParamLangueUI` (déjà défini)

- `FR` / `Français`
- `EN` / `English`
- Déconnecté des faits (paramètre UI uniquement)

---

## Hors périmètre de ce fichier

Tout le reste du backlog V1 (pages B2B, Marketplaces, Top sellers, Top loss, Arthaud, chart revenu×langue, etc.) **n’est pas** reporté ici — seulement les 3 items UI ci-dessus.

---

## Checklist reprise (quand on débloque)

- [ ] D1 — brancher `_ParamAxePeriode` sur charts General View (+ pages canal)
- [ ] D1 — règle auto grain selon durée du filtre date
- [ ] D2 — slicer `_ParamLangueUI` à droite sur toutes les pages
- [ ] D2 — libellés FR/EN dynamiques
- [ ] D3 — remplacer / enrichir le slicer date Between par UX type GA
- [ ] Retirer `DEFERRED` de ce fichier une fois livré
