---
id: INTERIM-LLM-finance-dashboard-data-gaps
type: technical-note
related:
  - docs/01-cadrage/SPEC-LLM-finance-dashboard-mockups.md
  - docs/01-cadrage/20260715_List_of_Data_fields_Finance_dashboard.csv
tags:
  - interim
  - data-gap
  - finance-dashboard
  - powerbi
  - llm-lookup
---

# INTERIM — Gaps données Finance dashboard (Power BI)

> **LLM LOOKUP** : `INTERIM-LLM-finance-dashboard-data-gaps`  
> Inventaire des **intérims honnêtes** livrés faute de champ backend.  
> À la réception des données : retirer libellés INTERIM + swap vers l’axe / colonnes mockup.

---

## Règle

1. Un intérim est **explicite** dans le rapport (sous-titre / libellé colonne / SPEC).
2. On ne invente **pas** Title / Author / Customer name à partir d’autres sources (ex. FedEx ≠ client B2B).
3. Chaque gap a une **sortie** documentée (champ attendu + action rapport).

---

## I1 — Website B2B : P&L by customer

| | |
|--|--|
| **Mockup** | Slide 8 · `page_08.png` — table *Revenue and profitability by customer* |
| **Page** | `b2b0a1c2d3e4f50617283a4b5c6d7e89` · `Website B2B` |
| **Gap** | Aucun `customer_name` / `company_name` dans `customer_order.csv` ni autres exports commandes backend |
| **Intérim livré** | Axe table = **pays destination** (`dim_pays`) · colonne libellée **Country (interim)** · sous-titre explicite gap |
| **Conservé** | Top 10 B2B orders (Order ID · units · Revenue · GP) — OK sans nom client |
| **Demande données** | Champ nom client (ou société) sur l’export commande, relié à `id_commande` |
| **Sortie** | Swap axe country → customer · retirer « (interim) » et sous-titre gap |
| **Statut** | **Actif** (2026-07-18) |

---

## I2 — Top sellers : Title / Author sur Top 10 ISBNs

| | |
|--|--|
| **Mockup** | Slide 10 · `page_10.png` — 3 tables *Top 10 ISBNs by channel* |
| **Page** | `b0c1d2e3f405162738495a6b7c8d9e0f` · `Top sellers` |
| **Gap** | `Title` et `Author` absents du modèle sémantique et des exports lignes (`fact_lignes` a `isbn`, pas titre/auteur) |
| **Intérim livré** | 3 tables ISBN : colonnes **ISBN · Ordered units · Revenue** seulement · titres « (interim) » · bannière rouge **INTERIM I2** · Revenue = CA grain article (`customer_price`, rapide) — pas allocation commande (trop lente) |
| **Conservé / OK sans gap** | 3 tables Top 10 **orders** (Order ID · units · Revenue · GP) × B2C / B2B / Marketplaces |
| **Demande données** | Titre + auteur par ISBN (export catalogue / item group), joinable sur `fact_lignes[isbn]` |
| **Sortie** | Ajouter colonnes Title · Author · retirer libellés INTERIM / bannière |
| **Statut** | **Actif** (2026-07-18) |

---

## I3 — Top loss makers : Customer name

| | |
|--|--|
| **Mockup** | Slide 11 · `page_11.png` |
| **Page** | `c0d1e2f3a405162738495a6b7c8d9e10` · `Top loss makers` |
| **Gap** | Même que I1 — `customer_name` manquant |
| **Intérim livré** | Colonne **Customer name absente** · bannière **INTERIM I3** · Order ID · units · Revenue · buckets GP · Gross Profit OK |
| **Demande données** | Même export nom client que I1 |
| **Sortie** | Ajouter colonne Customer name · retirer bannière INTERIM |
| **Statut** | **Actif** (2026-07-18) |

---

## Suivi

| ID | Page | Gap | Intérim | Sortie bloquée par |
|----|------|-----|---------|-------------------|
| I1 | Website B2B | Customer name | P&L by **country** | Export nom client |
| I2 | Top sellers | Title, Author | Tables ISBN **sans** Title/Author | Export titre/auteur × ISBN |
| I3 | Top loss | Customer name | Colonne omise + bannière | Export nom client |

Quand un gap est comblé : cocher la sortie dans la SPEC (§ page) **et** passer le statut à **Clos** ici.
