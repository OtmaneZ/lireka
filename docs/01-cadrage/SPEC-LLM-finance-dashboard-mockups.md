---
id: SPEC-LLM-finance-dashboard-mockups
type: implementation-spec
source_of_truth: visual-mockups-in-pdf
source_pdf: docs/01-cadrage/20260716_Finance_dashboard_mockups.pdf
source_date: 2026-07-16
spec_updated: 2026-07-18
visual_evidence: docs/01-cadrage/_mockup_pages/
visual_extract_method: PyMuPDF (fitz) page render → PNG
related:
  - docs/01-cadrage/20260715_List_of_Data_fields_Finance_dashboard.csv
  - docs/notes-techniques/DEFERRED-LLM-powerbi-ui-backlog.md
  - docs/notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md
  - powerbi/Lireka_Profitabilite.Report/
tags:
  - spec
  - mockup
  - finance-dashboard
  - powerbi
  - llm-lookup
  - implement
  - visual-first
---

# SPEC — Finance dashboard mockups (Power BI)

> **LLM LOOKUP** : `SPEC-LLM-finance-dashboard-mockups`  
> **Source de vérité** : les **images** du PDF mockup (pas le texte OCR seul, pas un clone aveugle de General View).  
> **PDF** : [`20260716_Finance_dashboard_mockups.pdf`](20260716_Finance_dashboard_mockups.pdf)  
> **Rendu pages** : [`_mockup_pages/`](_mockup_pages/) (PNG via PyMuPDF)  
> **Champs** : [`20260715_List_of_Data_fields_Finance_dashboard.csv`](20260715_List_of_Data_fields_Finance_dashboard.csv)  
> **UI reportée** : [`../notes-techniques/DEFERRED-LLM-powerbi-ui-backlog.md`](../notes-techniques/DEFERRED-LLM-powerbi-ui-backlog.md)  
> **Intérims données** : [`../notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md`](../notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md)

---

## 0. Règle d’interprétation (obligatoire)

1. En cas de conflit texte OCR ↔ image mockup → **l’image gagne**.
2. Ne **pas** cloner General View sur B2C / B2B / Marketplaces : ces pages sont surtout **KPI + table P&L** (axe différent).
3. Seules **General View** et **Librairie Arthaud** partagent la structure « KPI + 2 charts canal + table canal ».
4. Items **DEFERRED** : ne pas implémenter sans demande explicite.

---

## 1. Périmètre des vues

| # | Vue | Scope | Slide PDF | Image | Contenu principal (mockup) |
|---|-----|-------|-----------|-------|----------------------------|
| 1 | General View | **V1** | 5 | `page_05.png` | KPI + 2 charts canal + table canal |
| 2a | Website B2C | **V1** | 6 | `page_06.png` | KPI + table **P&L by country** |
| 2b | Website B2C — contribution by country | **V1** | 7 | `page_07.png` | KPI + **2 waterfalls YoY bridge** by country |
| 3 | Website B2B | **V1** | 8 | `page_08.png` | KPI + table **P&L by customer** + top 10 orders |
| 4 | Marketplaces | **V1** | 9 | `page_09.png` | KPI + table **P&L by Marketplace** |
| 5 | Top sellers | **V1** | 10 | `page_10.png` | 6 tables (orders + ISBNs × 3 canaux) |
| 6 | Top loss makers | **V1** | 11 | `page_11.png` | 3 tables loss-making + buckets GP |
| 7 | Librairie Arthaud | **V1** | 12 | `page_12.png` | Même structure que General, canal Arthaud only |
| 8 | Inventory | **V2** | intro | — | Hors V1 |
| 9 | Accounts receivables | **V2** | intro | — | Hors V1 |

**Total pages V1** : 8 (Inventory / AR exclus).

---

## 2. Layout global (toutes les vues)

Réf. slide 3 (`page_03.png`) — structure dashboards transporteurs.

| Zone | Contenu |
|------|---------|
| **Gauche** | Logo Lireka + filtres (date, channel, book language) |
| **Centre** | Cartes KPI, charts, tables |
| **Droite** | Dropdown langue UI **FR ↔ EN** |

### Filtres

| Filtre | Spec mockup | Statut |
|--------|-------------|--------|
| Date | Type Google Analytics | **DEFERRED** |
| Channel | Dropdown (scope page souvent figé côté canal) | Partiel |
| Book language | Dropdown | Partiel |
| UI FR / EN | Droite | **DEFERRED** |

---

## 3. Pattern KPI (commun)

4 cartes, valeur + PY + YoY :

| KPI | Exemple mockup | YoY |
|-----|----------------|-----|
| Ordered units | 1.79k · PY 1.23k | % |
| Revenue | €177.9k · PY €120k | % |
| Gross Profit | €30.8k · PY €20k | % |
| Gross Margin | 17.3% · PY 16.8% | **bps** |

---

## 4. Pattern table P&L (B2C pays / B2B customer / Marketplaces)

Titre type : **Revenue and profitability by {country \| customer \| Marketplace}**  
Sous-titre type : *Data by … — current year, figures in EUR — YoY variations vs prior year*

| Colonne mockup | Notes |
|----------------|-------|
| Axe (Country / Customer / Marketplace) | Dimension de la page |
| Sales (in EUR) | Revenue |
| COGS | Product cost |
| Product profit | Valeur + % |
| Returns and refunds | |
| Inbound freight | |
| Shipping | Outbound |
| Duties and taxes | |
| Shipping supplies | |
| Generic costs | |
| Gross profit | Valeur + % |
| Revenue YoY (%) | |
| Gross Profit YoY (%) | |
| Gross Margin YoY (bps) | |
| TOTAL row | Obligatoire |

---

## 5. Specs par vue (détail mockup)

### 5.1 General View — slide 5 · `page_05.png`

**Filtres** : date, Channel (B2C / B2B / Marketplaces), Book language.  
**Page filter canal** : B2C + B2B + Marketplaces (pas Arthaud / Autre).

| Zone | Spec mockup (image) | Repo (2026-07-18) |
|------|---------------------|-------------------|
| 4 KPI | Oui | OK |
| Chart gauche | **Revenue by sales channel** (temps × canal, PY vs CY) | OK |
| Chart droite | **Gross Profit by sales channel** (temps × canal, PY vs CY) | OK (restauré 2026-07-18) |
| Table | Units / revenue / profitability **by sales channel** | OK |
| Grain axe temps | day / week / month selon timeframe | **DEFERRED** |

**Note texte slide** : *« Revenue by channel and by language… »* — l’**image** montre Revenue canal + **GP canal**. Priorité image. Langue = filtre ; grain auto = deferred.

**Actions** :
- [x] Remettre chart **Gross Profit by sales channel**
- [x] Retirer Revenue by language comme chart principal GV
- [x] KPI + table canal
- [ ] Grain auto → deferred

---

### 5.2 Website B2C — slide 6 · `page_06.png`

**Scope** : Website B2C.  
**Pas de charts GV.**

| Zone | Spec mockup | Repo |
|------|-------------|------|
| 4 KPI | Oui | OK |
| Table | **Revenue and profitability by country** (P&L §4) | OK |
| Charts canal / langue | **Non** (pas dans le mockup) | OK (clone charts retiré) |

**Page** : `8f3e2a1b9c4d5e6f7a8b9c0d1e2f3a` · `Website B2C`

**Actions** :
- [x] Aligner page `Website B2C` sur slide 6 = **KPI + table P&L pays**
- [x] Supprimer clone charts GV (page `a1b2c3…` retirée)

---

### 5.3 Website B2C — contribution by country — slide 7 · `page_07.png`

**Scope** : Website B2C.  
**Pas de table P&L** sur cette page.

| Zone | Spec mockup | Repo |
|------|-------------|------|
| 4 KPI | Oui | OK |
| Chart gauche | **Revenue YoY bridge by country** (waterfall) | OK |
| Chart droite | **Gross Profit YoY bridge by country** (waterfall) | OK |
| Table P&L pays | Non (c’est slide 6) | OK (absente) |

**Page** : `c7b2c0n7r1b000000000000000000001` · `Website B2C — Contribution`  
**Modèle** (approche simple + robuste) :
- `_BridgePaysYoY` (table calculée) : **Prior year + Top 15 pays + Rest of the world** — le Top 15 est **figé au refresh** (`TOPN(15, …, [Revenu (reconstruit)])`). Le waterfall n'affiche QUE ces lignes → **aucun filtre visuel de mesure** (pas de `Keep`/`SortKey`, fragiles).
- Mesures : `B2C Bridge — Revenue` / `Gross Profit` (rendent le delta de chaque ligne présente).
- Tri visuel = colonne statique `_BridgePaysYoY[SortOrder]` (0 = PY, 1..15 = pays, 9999 = Rest).
- Start = PY · pays/Rest = Δ YoY · **Total auto waterfall ≈ Current year** (libellé natif « Total »).

**Actions** :
- [x] Page dédiée : KPI + 2 waterfalls YoY by country
- [x] Ne pas confondre avec la table P&L slide 6
- [x] Top 15 + Rest figés dans la table (pas tous les pays, sans filtre de mesure)
- [ ] Valider rendu Desktop (**refresh modèle obligatoire** pour recalculer `_BridgePaysYoY`)

---

### 5.4 Website B2B — slide 8 · `page_08.png`

**Scope** : Website B2B.  
**Pas de charts GV.**

| Zone | Spec mockup | Repo |
|------|-------------|------|
| 4 KPI | Oui | OK |
| Table principale | **Revenue and profitability by customer** (P&L §4, axe client) | **INTERIM** — axe `Country (interim)` (= destination country) ; sous-titre explicite gap |
| Table secondaire | **Top 10 B2B orders by revenue** (sous la P&L) | OK (Keep + blanking mesures, y=460) |
| Charts canal / langue | **Non** | OK (retirés) |

**Page** : `b2b0a1c2d3e4f50617283a4b5c6d7e89` · `Website B2B`

**Gap données (bloquant axe client)** : aucun `customer_name` / `company_name` dans `customer_order.csv` ni autres exports backend commandes.  
→ Voir **[INTERIM I1](../notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md)** · Demander à Marc : champ nom client sur l’export commande.  
→ À l’arrivée : swap axe country → client, retirer libellés INTERIM.

Colonnes top 10 orders : Order ID · Ordered units · Revenue · Gross Profit.

**Actions** :
- [x] Layout mockup : KPI + P&L + top 10 dessous
- [x] Retirer charts GV
- [x] Top 10 orders placé
- [x] P&L intérim by country (honnête) en attendant customer name
- [ ] Remplacer par vrai axe customer quand export disponible

---

### 5.5 Marketplaces — slide 9 · `page_09.png`

**Scope** : Marketplaces.  
**Pas de charts GV.** **Pas de Top 15 / Rest** (liste finie de sources).

| Zone | Spec mockup | Repo |
|------|-------------|------|
| 4 KPI | Oui | OK |
| Table | **Revenue and profitability by Marketplace** (Amazon FR, Cultura, Amazon UK, … Rakuten) | OK |

**Page** : `a9f0e1d2c3b4a5061728394a5b6c7d8e` · `Marketplaces`  
**Modèle** :
- Filtre page : `dim_type_commande[canal] = Marketplaces` (AMAZON*, CULTURA, RAKUTEN, FNAC).
- Axe table : `dim_type_commande[libelle]` (ex. Amazon Fr, Cultura…).
- Mesures d’affichage dédiées `Mkt Display - *` (format mockup, **sans** logique Top15 pays — contrairement à `B2C Display`).
- Tri : `[Revenu (reconstruit)]` DESC · TOTAL natif table.

**Actions** :
- [x] Page KPI + table P&L by Marketplace
- [ ] Valider rendu Desktop

---

### 5.6 Top orders & top sellers — slide 10 · `page_10.png`

**6 tables** = 3 canaux (B2C, B2B, Marketplaces) × (Orders / ISBNs).  
**Pas de KPI** — rail + 6 tables (orders gauche · ISBN droite).

**Page** : `b0c1d2e3f405162738495a6b7c8d9e0f` · `Top sellers`

**Top 10 orders** : Order ID · Ordered units · Revenue · Gross Profit  
**Top 10 ISBNs** : ISBN · Title · Author · Ordered units · Revenue

| Besoin données | Statut |
|----------------|--------|
| Title, Author | **INTERIM I2** — tables ISBN sans Title/Author + bannière → [doc](../notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md) |

**Modèle** :
- Top 10 via **blanking mesures** (pattern B2C Display) — PAS filtre Rank/TopN PBIR (fragile).
- Orders : `Top Keep Commande — Revenue` + `Top Unités/Revenu/Marge Commande` (+ Rank blank hors top 10) · filtre canal catégoriel
- ISBN : `TOPN(10, …, Revenue DESC, isbn ASC)` + `KEEPFILTERS` (évite >>10 lignes si égalités Rank DENSE, ex. Marketplaces) · filtre `fact_lignes[canal_ligne]` · revenu = grain article

**Actions** :
- [x] Page + 6 tables (3 orders OK · 3 ISBN intérim I2)
- [ ] Valider rendu Desktop
- [ ] Ajouter Title / Author quand export disponible (clôturer I2)

---

### 5.7 Top loss makers — slide 11 · `page_11.png`

**3 tables** (B2C, B2B, Marketplaces) — top 10 commandes à marge négative.  
**Page** : `c0d1e2f3a405162738495a6b7c8d9e10` · `Top loss makers`

Colonnes mockup : Order ID · Customer name · Ordered units · Revenue · Gross Profit  
+ **détail de chaque bucket** de Gross Profit (postes P&L).

| Besoin données | Statut |
|----------------|--------|
| Customer name | **INTERIM I3** — colonne omise + bannière → [doc](../notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md) |

**Modèle** :
- Top 10 via **blanking mesures** (même pattern) — PAS filtre Rank PBIR.
- Rank : `Top Rank Loss — Gross Profit` parmi `Marge Brute < 0` (ASC) · Keep + mesures `Top Loss — *` blankent hors top 10 · filtre canal catégoriel
- Buckets colonnes : Revenue · COGS · Inbound · Shipping · Duties · Marketplace fees · Supplies · Returns · Generic · Gross Profit

**Actions** :
- [x] Page + 3 tables + buckets GP (Customer name intérim I3)
- [ ] Valider rendu Desktop
- [ ] Ajouter Customer name quand export disponible (clôturer I3)

---

### 5.8 Librairie Arthaud — slide 12 · `page_12.png`

**Texte mockup** : *Same as general view, but with just Librairie Arthaud sales channel only.*

| Zone | Spec | Repo |
|------|------|------|
| Structure | Identique General View (KPI + Revenue by channel + GP by channel + table) | OK |
| Scope | Canal `Librairie Arthaud` only | OK |

**Page** : `d0e1f2a3b405162738495a6b7c8d9e20` · `Librairie Arthaud`  
**Modèle** : clone GV · filtre page `dim_type_commande[canal] = Librairie Arthaud` (source `ARTHAUD`).

**Actions** :
- [x] Page clone structure GV + page filter Arthaud
- [ ] Valider rendu Desktop

---

### 5.9 V2 — ne pas livrer en V1

| Vue | Champs CSV |
|-----|------------|
| Inventory | Units in inventory, Gross/Net value, Aged, Unhealthy |
| Accounts receivables | AR, Past due |

---

## 6. État repo vs mockup (snapshot 2026-07-18)

| Mockup | Page PBI | Alignement |
|--------|----------|------------|
| General View | `7112a69a17fbef2de240` | **OK** hors deferred (GP restauré) |
| B2C slide 6 (P&L pays) | `8f3e2a1b9c4d5e6f7a8b9c0d1e2f3a` (`Website B2C`) | **OK** |
| B2C slide 7 (waterfalls) | `c7b2c0n7r1b000000000000000000001` (`Website B2C — Contribution`) | **OK** — valider Desktop |
| B2B | `b2b0a1c2d3e4f50617283a4b5c6d7e89` | **OK intérim** — P&L by country + top 10 ; customer name pending |
| Marketplaces | `a9f0e1d2c3b4a5061728394a5b6c7d8e` | **OK** — valider Desktop |
| Top sellers | `b0c1d2e3f405162738495a6b7c8d9e0f` | **OK intérim I2** — 6 tables ; Title/Author pending |
| Top loss | `c0d1e2f3a405162738495a6b7c8d9e10` | **OK intérim I3** — 3 tables + buckets ; Customer name pending |
| Arthaud | `d0e1f2a3b405162738495a6b7c8d9e20` | **OK** — clone GV, filtre Arthaud only |

---

## 7. Checklist correctifs (ordre)

| # | Action | Priorité |
|---|--------|----------|
| C1 | GV : restaurer chart **Gross Profit by sales channel** | **Done** |
| C2 | B2C : page slide 6 = KPI + P&L country (retirer clone charts) | **Done** |
| C3 | B2C : page slide 7 = KPI + 2 waterfalls YoY by country | **Done** (valider Desktop) |
| C4 | B2B : retirer charts GV ; P&L intérim country + top 10 | **Done** (customer name pending) |
| C5 | Marketplaces : KPI + P&L by Marketplace | **Done** (valider Desktop) |
| C6 | Arthaud : clone structure GV, filtre Arthaud | **Done** (valider Desktop) |
| C7 | Données Title / Author / Customer name | Gaps trackés → [INTERIM doc](../notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md) (I1/I2/I3 actifs) |
| C8 | Top sellers (6) — orders OK + ISBN intérim I2 | **Done** (valider Desktop ; clôturer I2) |
| C8b | Top loss (3) + buckets GP — Customer name intérim I3 | **Done** (valider Desktop ; clôturer I3) |
| C9 | Nav pages + recette slide-par-slide vs `_mockup_pages/` | Fin V1 |
| D1 | Grain auto / FR-EN / date GA | **DEFERRED** |

---

## 8. Contacts (slide 13)

- Marc Bordier — mbordier@lireka.com  
- Emma Henry — ehenry@lireka.com  

---

## 9. Règles agents / LLM

1. Lire **`_mockup_pages/page_XX.png`** avant d’implémenter une vue.  
2. Ne pas déduire le contenu d’une page canal depuis General View.  
3. Ce fichier = spec d’implémentation ; le PDF = artefact client.  
4. Ne pas implémenter **DEFERRED** / V2 sans demande.  
5. Après chaque page : vérifier amont (mockup image) et aval (visuels + page filter + colonnes).
