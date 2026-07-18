# Audit complet — Lireka_Profitabilite
Date : 2026-07-18 · Auditeur : Cursor · Périmètre : repo complet sur disque

> Méthode : chaque constat est tagué `[CONFIRMÉ]` (preuve fichier/CSV) ou `[HYPOTHÈSE]` (runtime Desktop / DAX Studio / VertiPaq requis). Aucune correction n’a été appliquée pendant cet audit.

---

## 0. Synthèse exécutive

Le livrable technique sur disque est **substantiel et globalement cohérent** (star schema attendu, 8 pages V1 présentes, bindings mesures/colonnes sans rupture détectée, chrome aligné, `SharePointSiteURL` correct). Il n’est **pas prêt pour une signature client sans réserve** : validation métier absente (L01–L06 restent ⬜), gaps mockup bloqués par des données tiers (customer name / Title / Author), documentation process et notes techniques **contredites par les CSV actuels**, et dette de gouvernance DAX (218 mesures sans display folders, ~64 orphelines, docs/formats partiels).

| Domaine | BLOQUANT | MAJEUR | MINEUR | INFO | État |
|---------|---------:|-------:|-------:|-----:|------|
| 1. Conformité specs | 2 | 3 | 2 | 2 | critique |
| 2. Modèle de données | 0 | 1 | 2 | 2 | à corriger |
| 3. Mesures DAX | 0 | 3 | 4 | 2 | à corriger |
| 4. Power Query / M | 0 | 2 | 1 | 2 | à corriger |
| 5. Rapport PBIR | 0 | 2 | 1 | 2 | à corriger |
| 6. Performance (statique) | 0 | 2 | 2 | 2 | à corriger |
| 7. Qualité des données | 1 | 2 | 1 | 2 | critique |
| 8. Hygiène du repo | 0 | 3 | 3 | 1 | à corriger |
| 9. Gouvernance | 0 | 2 | 2 | 2 | à corriger |

### Top 5 actions prioritaires (impact livraison client)

1. **Obtenir validation Marc** sur `[Marge Brute]` (9 termes + Bloc 5 retours/génériques) et sur le choix CA natif vs reconstruit dans le numérateur — sans ça, L04 n’est pas accepté. *(dépend Marc)*
2. **Combler les gaps mockup I1/I2/I3** (customer name, Title/Author) ou faire accepter formellement les intérims comme livrable V1. *(dépend Marc / export backend)*
3. **Mettre à jour L06 + notes techniques** (`processus-etl-gouvernance.md` affirme SharePoint ; le modèle lit en `Local` ; docs shipping/CA marketplace obsolètes vs CSV du 2026-07-16). *(interne)*
4. **Recette Desktop slide-par-slide** (waterfalls `_BridgePaysYoY`, Top sellers/loss, KPI FORMAT) + Performance Analyzer sur `Revenu (reconstruit, alloué langue)` et `CA Commandes Annulation Partielle`. *(interne + runtime)*
5. **Ranger le modèle mesures** : display folders, purge/archivage des 64 orphelines de contrôle, aligner `powerbi/models/mesures-dax.md` (annonce 105 mesures vs 218 réelles). *(interne)*

### Dépendances tiers vs actionnable en interne

| Dépend de Marc / backend | Actionnable en interne |
|--------------------------|------------------------|
| Validation formule `[Marge Brute]` + périmètre Bloc 5 | Correction L06 (Local vs SharePoint) |
| Export `customer_name` / `company_name` (I1, I3) | Display folders + purge mesures orphelines |
| Export Title / Author × ISBN (I2) | Recette Desktop + nettoyage docs obsolètes |
| Validation reconstruction CA marketplace (option B) | Alignement registre `livrables.md` (statuts ⬜ vs implémenté) |
| Validation coexistence returns vs product_cost sur CANCELLED | Scripts de contrôle / hygiène `.bak` |
| Session formation L05 (disponibilité équipes) | Mesures manquantes V1 « per unit » / Units shipped (si demandées) |

---

## 1. Conformité specs

### Constats

- [BLOQUANT][CONFIRMÉ] **Registre contractuel L01–L06 entièrement non validé** — `docs/01-cadrage/livrables.md` lignes 22–27 : tous les statuts sont `⬜`, colonne « Validé par » vide. Preuve d’implémentation technique ≠ acceptation client.
- [BLOQUANT][CONFIRMÉ] **Gaps mockup V1 bloqués par données absentes (I1/I2/I3)** — `docs/notes-techniques/INTERIM-LLM-finance-dashboard-data-gaps.md` ; confirmé CSV : aucune colonne customer/company name dans `customer_order.csv` (header audité) ; `fact_lignes.tmdl` a `isbn` sans Title/Author.
- [MAJEUR][CONFIRMÉ] **Pages mockup V1 — statut vs repo** (ids `pages.json` + `page.json` `displayName`) :

  | Vue mockup | Page PBI | Statut | Écart vs mockup |
  |------------|----------|--------|-----------------|
  | General View | `7112a69a17fbef2de240` | construite | Grain auto day/week/month DEFERRED (SPEC §5.1) |
  | Website B2C | `8f3e2a1b9c4d5e6f7a8b9c0d1e2f3a` | construite | Alignée KPI + P&L pays |
  | B2C contribution by country | `c7b2c0n7r1b000000000000000000001` | construite | Waterfalls présents ; validation Desktop non prouvable headless |
  | Website B2B | `b2b0a1c2d3e4f50617283a4b5c6d7e89` | partielle | Axe **Country (interim)** au lieu de customer |
  | Marketplaces | `a9f0e1d2c3b4a5061728394a5b6c7d8e` | construite | — |
  | Top sellers | `b0c1d2e3f405162738495a6b7c8d9e0f` | partielle | ISBN sans Title/Author (I2) |
  | Top loss makers | `c0d1e2f3a405162738495a6b7c8d9e10` | partielle | Customer name omis (I3) |
  | Librairie Arthaud | `d0e1f2a3b405162738495a6b7c8d9e20` | construite | Clone structure GV |

- [MAJEUR][CONFIRMÉ] **Indicateurs V1 (`List_of_Data_fields`, lignes 1–25) vs mesures DAX** — inventaire croisé `_Mesures.tmdl` (218 mesures) :

  | # | Indicateur V1 | Couverture DAX | Preuve |
  |---|---------------|----------------|--------|
  | 1 | Units ordered | Oui — `[Unités commandées]` | `_Mesures.tmdl` L485 |
  | 2 | Units shipped | **Absente** | aucun match « expédi » / shipped |
  | 3 | Cancelled units | Oui — `[Nb Articles Annulés]` | L52 |
  | 4 | Cancellation rate | Oui — `[Taux Annulation]` | L777 |
  | 5 | Number of orders | Oui — `[Nb Commandes]` | L7 |
  | 6 | Product revenue | Partiel — via `[CA HT Net Annulation]` (pas de mesure « CA produit » nommée) | L110 |
  | 7 | Shipping revenue | Oui — `[Frais Port Encaissés]` | L217 |
  | 8 | Revenue | Oui — `[Revenu]` / `[Revenu (reconstruit)]` | L491, L680 |
  | 9 | Product cost | Oui — `[Coût Achat Total]` | L146 zone |
  | 10–11 | PPP / PPM | **Absentes** comme mesures nommées (display P&L seulement) | keyword hits vides |
  | 12 | Inbound Freight | Oui — `[Coût Transport Amont]` | L222 |
  | 13 | Shipping cost | Oui — `[Coût Transport Outbound (Retenu)]` | L227 |
  | 14–15 | Shipping / unit & % CA | **Absentes** | keyword « par unité » vide |
  | 16 | D/T | Oui — `[Douanes Taxes]` | L232 |
  | 17–18 | D/T per unit & % | **Absentes** | — |
  | 19 | Marketplace fees | Oui — `[Commissions Marketplace]` | L237 |
  | 20 | Returns and refunds | Oui — `[Retours Remboursements]` | L251 |
  | 21 | Shipping supplies | Oui — `[Fournitures Expédition]` | L242 |
  | 22 | Generic costs | Oui — `[Coûts Génériques]` | L258 |
  | 23–24 | Gross Profit / Margin | Oui — `[Marge Brute]` / `[Taux Marge Brute]` | L277, L293 |
  | 25 | Gross Profit per unit | **Absente** | — |

  **Bilan** : ~16/25 couverts (dédiés ou équivalent clair), **9 manquants** dont Units shipped et tous les « per unit / % » satellites.

- [MAJEUR][CONFIRMÉ] **L06 documente un mode SharePoint actif alors que le modèle est en Local** — `docs/04-processus/processus-etl-gouvernance.md` L34–37 (« lus directement depuis SharePoint ») vs `expressions.tmdl` L10–19 (`SourceMode = "Local"`, `File.Contents(LocalRootPath…)`).
- [MINEUR][CONFIRMÉ] **UI DEFERRED partiellement matérialisée** — tables `_ParamLangueUI`, `_ParamAxePeriode` référencées dans `model.tmdl` L25–26 alors que SPEC marque FR↔EN / grain auto comme DEFERRED.
- [MINEUR][CONFIRMÉ] **Scope creep documentaire / tooling hors devis** (présents, non rattachés à L01–L06 ni au mockup comme livrable client) :
  - `tools/audit-interne/` (doublon partiel de `scripts/validation/`)
  - `docs/01-cadrage/audit-dashboards-existants.md`, notes techniques multiples (utiles en interne, hors « dictionnaire / architecture » exclus du devis mais proches)
  - scripts générateurs de pages (`build_general_view.py`, `build_website_b2c.py`) — tooling interne OK s’ils ne sont pas présentés comme livrables
  - `Power_BI_Datawarehouse/Dashboards_transporteurs/` et `Formation_Power_BI/` = données client, pas livrables ZineInsights (hors périmètre devis confirmé)
- [INFO][CONFIRMÉ] **L04 « 1 rapport, 2 axes »** : le rapport livre 8 pages mockup (plus large que le minimum devis) — acceptable si le mockup client est la référence d’acceptation ; à clarifier avec Marc.
- [INFO][CONFIRMÉ] **L05** : programme session unique documenté (`docs/05-formation/programme-formation.md`) — pas de preuve de session tenue ; statut registre ⬜ cohérent.

### État : critique

---

## 2. Modèle de données

### Constats

- [INFO][CONFIRMÉ] **Cartographie tables** (`definition/tables/*.tmdl` + `model.tmdl`) — modèle attendu présent :

  | Table | Rôle | Notes |
  |-------|------|-------|
  | `fact_commandes` | fact | 21 colonnes, import M |
  | `fact_lignes` | fact | 14 colonnes |
  | `fact_transport` | fact | 11 colonnes |
  | `fact_factures_transport` | fact | 12 colonnes |
  | `dim_date` | dimension date | `dataCategory: Time`, `isKey` sur `date` |
  | `dim_pays` | dimension | |
  | `dim_transporteur` | dimension | |
  | `dim_type_commande` | dimension | |
  | `_Mesures` | mesures | |
  | `_BridgePaysYoY` | **table calculée** | partition `= calculated` (`_BridgePaysYoY.tmdl` L31–56) |
  | `_ParamLangueUI` / `_ParamAxePeriode` | paramètres UI | |

- [MAJEUR][CONFIRMÉ] **Relation fact↔fact active** `rel_factures_colis` : `fact_factures_transport.id_package` → `fact_transport.id_package` (`relationships.tmdl` L35–37). Pattern de rapprochement assumé ; risque de cardinalité many-to-many si plusieurs lignes facture par colis — **non vérifiable sans profil VertiPaq** → confirmation runtime en annexe C.
- [MINEUR][CONFIRMÉ] **2 relations inactives avec usage `USERELATIONSHIP` documenté** — `rel_factures_transporteur`, `rel_factures_date` (`isActive: false`, L25–33) ; mesures `[Coût Transport Facturé]`, `[Coût Facturé Rapproché]` utilisent `USERELATIONSHIP` (extrait audit + commentaire F-06 L161–165 `_Mesures.tmdl`). Cohérent.
- [MINEUR][CONFIRMÉ] **Pas de relation directe fact_lignes / fact_transport → dim_date ou dim_pays** — filtrage via `fact_commandes` (rels L4–19). Star schema classique, pas de snowflake. Direction : défaut one-direction (aucun `bothDirections` déclaré).
- [INFO][CONFIRMÉ] **`dim_date`** : commentaire L1–5 (`2020-01-01` → `2026-12-31`) ; `dataCategory: Time` ; `UnderlyingDateTimeDataType = Date` (L21). Plage faits CSV `origin_created` min/max recomptée : **2020-01-09 → 2026-07-16** — couverte par le calendrier.
- [INFO][CONFIRMÉ] **Aucune table isolée** parmi facts/dims attendues ; params et `_Mesures` volontairement hors relations. **Aucun RLS** détecté (pas de fichiers roles / permissions).
- [HYPOTHÈSE] Cardinalités exactes many/one et unicité `id_package` côté transport — à confirmer dans Desktop (vue relations) / DAX Studio.

### État : à corriger

---

## 3. Mesures DAX

### Constats

- [MAJEUR][CONFIRMÉ] **218 mesures, 0 display folder** — grep `displayFolder` dans `_Mesures.tmdl` : 0 hit ; compteur folders = `{(none): 218}`. Organisation « en vrac » malgré préfixes (`KPI Compact —`, `Couleur YoY —`, `B2C Display -`, `Mkt Display -`, `Top Loss —`).
- [MAJEUR][CONFIRMÉ] **64 mesures orphelines** (ni dans aucun `visual.json`, ni référencées par une autre mesure) — dont contrôles matching/qualité, YoY Δ/% non branchés, `Chart label — *`, `Top Keep ISBN — Revenue`. Liste complète : annexe B.
- [MAJEUR][CONFIRMÉ] **Doublons / parallèles de marge non homogènes** — coexistent `[Marge Brute]`, `[Marge Brute (prov.)]`, `[Marge Brute (reconstruit)]`, `[Marge Brute (grain article, prov.)]`, `[Marge Brute Backend (réf.)]` + écarts. Les variantes « prov. / reconstruit / grain article » sont documentées comme contrôles ; le risque livraison est la **confusion utilisateur** si exposées dans le field list.
- [MINEUR][CONFIRMÉ] **`[Marge Brute]` — 9 termes présents, commentaire à jour** — `_Mesures.tmdl` L262–287 :

  ```
  CA HT Net Annulation
  + Frais Port Encaissés (hors CANCELLED)
  − Coût Achat Total
  − Coût Transport Amont
  − Coût Transport Outbound (Retenu)
  − Douanes Taxes
  − Commissions Marketplace
  − Fournitures Expédition
  − Retours Remboursements
  − Coûts Génériques
  ```

  Aligne les 7 postes + retours + génériques de la liste Marc / CSV fields. **Point d’attention** : le dashboard publie surtout le **revenu reconstruit** dans les KPI cards, alors que `[Marge Brute]` reste sur CA **natif** net annulation (commentaire L273–276) — écart conceptuel à valider avec Marc.
- [MINEUR][CONFIRMÉ] **Time intelligence correcte (dim_date)** — tous les `SAMEPERIODLASTYEAR` / `DATEADD` audités portent sur `dim_date[date]` (ex. L498, L524, L372), pas sur colonnes fact.
- [MINEUR][CONFIRMÉ] **Qualité DAX** : 0 division `/` suspecte hors `DIVIDE` détectée (`SLASH_DIV = 0`) ; 31 mesures avec itérateurs (`SUMX`/`FILTER`/`RANKX`/`TOPN`) ; 22 avec `ALL`/`ALLSELECTED`/`ALLEXCEPT`. Exemple coûteux : `[CA Commandes Annulation Partielle]` (`FILTER(fact_commandes, … COUNTROWS(FILTER(…)))` L123–130) ; `[Revenu (reconstruit, alloué langue)]` (`SUMX(VALUES(fact_commandes[id_commande]), …)` L751+).
- [MINEUR][CONFIRMÉ] **Mesures `FORMAT()`** : 37 mesures texte. Contreparties numériques vivantes pour les KPI Compact / Display (ex. Compact → Unités/Revenu/Marge/Taux). `Couleur YoY — *` et `Chart label — *` n’ont pas de « valeur métier » numérique dédiée (normal pour couleurs/labels).
- [INFO][CONFIRMÉ] **Conventions de nommage post-refactor** : préfixes `KPI Compact —` / `Couleur YoY —` présents ; inconsistances restantes `B2C Display -` (hyphen ASCII) vs tiret cadratin `—`, et vestiges `B2C couleur - cout/profit`.
- [INFO][CONFIRMÉ] **Bindings Report** : 0 `queryRef` mesure cassée ; 0 colonne cassée (croisement `_Mesures` + colonnes TMDL vs tous `visual.json`).
- [HYPOTHÈSE] Exactitude numérique `[Marge Brute]` vs finance Marc — DAX Studio / recette Excel requise.

### État : à corriger

---

## 4. Power Query / M

### Constats

- [MAJEUR][CONFIRMÉ] **`LocalRootPath` machine-spécifique** — `expressions.tmdl` L19 : `C:\Users\Otmane\Documents\lireka\Power_BI_Datawarehouse`. Bloque le refresh chez le client sans changement de paramètre.
- [MAJEUR][CONFIRMÉ] **Contradiction documentation vs paramètres** — SharePoint URL correcte sur disque (`https://lirekacom.sharepoint.com/sites/Lireka`, L5) **mais dormante** ; lecture réelle = `SourceMode = "Local"` (L12) + `File.Contents`. Historique « placeholder écrasé » : **non reproduit** sur l’état actuel (URL saine).
- [MINEUR][CONFIRMÉ] **Staging non chargé** — requêtes `stg_*` et `fn*` sont des `expression` partagées, absentes de `ref table` dans `model.tmdl` : cohérent (non matérialisées comme tables modèle).
- [INFO][CONFIRMÉ] **Null → 0 Bloc 5 en place** — `fact_commandes.tmdl` L279–284 : `Table.ReplaceValue(..., null, 0, … {"retours_remboursements","couts_generiques"})` après jointure gauche.
- [INFO][CONFIRMÉ] **Typage staging customer_order** — `stg_customer_order` applique `Table.TransformColumnTypes` explicite (L132–152) ; pas de `type any` massif détecté sur ce flux.
- [HYPOTHÈSE] Coût des merges (filtre après merge) et colonnes M chargées puis abandonnées — à profiler dans Power Query Diagnostics.

### État : à corriger

---

## 5. Rapport PBIR

### Constats

- [MAJEUR][CONFIRMÉ] **Intérims mockup visibles comme écarts fonctionnels** — B2B axe pays ; Top sellers ISBN sans Title/Author ; Top loss sans customer name (SPEC + INTERIM + absence colonnes).
- [MAJEUR][HYPOTHÈSE] **Rendu Desktop non validé** pour waterfalls Contribution, tables Top sellers/loss, cards FORMAT — SPEC elle-même coche « Valider rendu Desktop ». Headless ne peut pas signer le rendu.
- [MINEUR][CONFIRMÉ] **Filtre date relatif 12 mois en dur sur chaque page** — ex. General View `page.json` L35–105 (`RelativeDate`, −12 mois) **en plus** du slicer date. Comportement voulu probable, mais le slicer ne peut pas élargir au-delà du filtre page.
- [INFO][CONFIRMÉ] **Inventaire pages** : 8 pages dans `pages.json` `pageOrder` = 8 dossiers disque ; **aucune page fantôme** (`Test-Path` `a1b2c3…` = False au moment de l’audit). Ordre = mockup V1.
- [INFO][CONFIRMÉ] **Chrome cohérent** entre pages à KPI : nav `(0,0,220,720)`, logo `(27,8,161,163)`, slicers date/canal/langue positions identiques ; KPI cards positions identiques sur GV/B2C/B2B/Mkt/Contribution/Arthaud. Top sellers / Top loss : pas de KPI (conforme mockup).
- [INFO][CONFIRMÉ] **Pattern RANKX/TOPN/ALLSELECTED dans bindings PBIR** : **0 occurrence** dans les `visual.json` (grep Report) — le pattern qui a cassé Desktop n’est plus dans les bindings ; logique TopN basculée en mesures blanking / table calculée.
- [HYPOTHÈSE] Interactions visuel↔visuel éditées — aucun fichier `visualInteractions` global trouvé ; à vérifier dans Desktop (Format → Interactions).

### État : à corriger

---

## 6. Performance — audit statique

### Constats

- [MAJEUR][CONFIRMÉ] **Volumes faits (CSV actuels)** — `customer_order.csv` **1 008 455** lignes ; `customer_order_item.csv` **1 903 388** ; `package.csv` **965 055**. Table calculée `_BridgePaysYoY` = petit axe (≤17 lignes), ne duplique pas une fact.
- [MAJEUR][CONFIRMÉ] **Mesures potentiellement coûteuses** (statique) : `[CA Commandes Annulation Partielle]` (double `FILTER` sur fact) ; `[Revenu (reconstruit, alloué langue)]` (`SUMX` sur commandes + `ALLEXCEPT`) ; famille `B2C Rest *` / ranks Top ISBN (`TOPN`/`RANKX`/`ALLSELECTED` côté mesure).
- [MINEUR][CONFIRMÉ] **Colonnes candidates poids mort** (non référencées visuels + relations + patterns DAX forts) — extrait : `dim_date` 9 attributs calendrier non utilisés dans le Report ; `fact_commandes[contribution_*]`, `gross_margin` ; `fact_factures_transport[service,pays_destination,poids,devise,nb_candidats_resolution]` ; etc. (liste annexe A). Certaines peuvent servir au diagnostic — pas forcément à supprimer sans revue.
- [MINEUR][CONFIRMÉ] **Datetimes** : `fact_commandes[date_commande]` tronqué au jour en M (`Date.FromText(Text.Start([origin_created],10))`, L222) — bon signal compression. `dim_date[date]` typé dateTime avec annotation Date.
- [INFO][HYPOTHÈSE] Cardinalité réelle VertiPaq (hash, dict size) — **VertiPaq Analyzer** requis.
- [INFO][HYPOTHÈSE] Temps requête KPI/charts — **Performance Analyzer** Desktop requis.
- [INFO][CONFIRMÉ] **Pas de RANKX/TOPN dans bindings Report** (voir §5) — risque Desktop historique mitigé côté PBIR.

### État : à corriger

---

## 7. Qualité des données — blockers connus

> Chiffres **recomptés** le 2026-07-18 depuis `Power_BI_Datawarehouse/Données_Backend/*.csv` (1 008 455 commandes). Les montants des docs 15/07 sont obsolètes.

### Constats

- [BLOQUANT][CONFIRMÉ] **Customer name absent** — header `customer_order.csv` sans `customer_name` / `company_name` / équivalent ; `has_customer_name = False`. Bloque mockup B2B + Top loss (I1/I3). **Dépend Marc.**
- [MAJEUR][CONFIRMÉ] **`order_amount_eur` sur marketplaces — blocker « vide » caduc ; zeros résiduels** — empty = **0 %** sur tous canaux ; marketplaces : **31 554 / 681 017 zeros (4,63 %)**. La doc `reconstruction-ca-marketplace.md` L11 (« systématiquement vide ») est **fausse sur l’export actuel**. La reconstruction reste pertinente pour les zeros / cas locaux.
- [MAJEUR][CONFIRMÉ] **`shipping_fee_eur` marketplace — doc « 100 % à 0 » caduque** — recomptage marketplaces : empty 0 ; **zero 161 790** ; **nonzero 519 227** ; SUM EUR **3 154 680,82 €** ; `shipping_fee_local > 0` = 519 227. La note `limite-shipping-marketplace.md` (snapshot 989 234 cmd, 0 € marketplace) est **obsolète**. Residual : AMAZON_NL/SE encore 100 % ship_eur = 0 ; AMAZON_CA encore majoritairement 0.
- [MINEUR][CONFIRMÉ] **`returns_and_refunds_eur` ≠ « set at 0 »** — SUM commande = **179 975,84 €** ; **535 981** lignes ≠ 0. Spec CSV fields L27 dit « currently set at 0 » — contredit par les données. Aligné grain item : SUM `returns_and_refunds_cost_eur` = **179 975,84 €**.
- [INFO][CONFIRMÉ] **Annulations partielles** — **9 162** commandes (`state <> CANCELLED` avec ≥1 article CANCELLED) ; **84 793** commandes full CANCELLED. Cohérent avec l’ordre de grandeur documenté (~9 130 / ~8 900).
- [INFO][CONFIRMÉ] **Autres contrôles** — `duplicate_order_ids = 0` ; `negative_order_amount = 0` ; `total_generic_costs_eur` SUM = **765 107,18 €** (doc Bloc 5 citait 747 983,55 € au 15/07 — écart dû au nouvel export).
- [HYPOTHÈSE] Encodage / caractères corrompus dans titres (non présents) — N/A tant que Title absent.

### État : critique

---

## 8. Hygiène du repo

### Constats

- [MAJEUR][CONFIRMÉ] **`powerbi/models/mesures-dax.md` obsolète** — annonce « Total : **105 mesures** » (L8) vs **218** dans `_Mesures.tmdl`.
- [MAJEUR][CONFIRMÉ] **Notes techniques contredites par CSV actuels** — `reconstruction-ca-marketplace.md`, `limite-shipping-marketplace.md`, montants `dette-technique-bloc5.md` (924 129 € / −21 749 723 €) basés sur export 15/07 (989 234 cmd) ≠ export courant (1 008 455 cmd ; returns 179 976 € ; generics 765 107 €).
- [MAJEUR][CONFIRMÉ] **`processus-etl-gouvernance.md` (L06) vs réalité Local** — voir §4.
- [MINEUR][CONFIRMÉ] **Fichier mort / backup** — `powerbi/Lireka_Profitabilite.Report/.pbi/localSettings.json.bak` présent sur disque.
- [MINEUR][CONFIRMÉ] **`.gitignore`** — `powerbi/.gitignore` exclut bien `**/.pbi/localSettings.json` et `cache.abf` (`git check-ignore -v` OK). Root ignore `Power_BI_Datawarehouse/**`, sorties `*_output.json`.
- [MINEUR][CONFIRMÉ] **Scripts `scripts/validation/`** : mélange scripts d’audit encore utiles (`pre_dashboard_checks.py`, `ca_reconstruction_audit.py`) et générateurs one-shot (`build_*.py`, `refactor_measures_cleanup.py`). Doublons avec `tools/audit-interne/`. Sorties versionnées malgré ignore partiel : `diag_marge_canal_output.json`, `pre_dashboard_checks_output.json` présents (à vérifier tracking git).
- [INFO][CONFIRMÉ] **`livrables.md` vs SPEC** : SPEC dit pages « OK / Done » ; registre dit ⬜ — contradiction de **statut projet**, pas de code.

### État : à corriger

---

## 9. Gouvernance du modèle

### Constats

- [MAJEUR][CONFIRMÉ] **Documentation mesures partielle** — 122/218 sans bloc `///` immédiatement précédent (ratio doc ≈ **44 %**). Les mesures cœur (`[Marge Brute]`, transport, Bloc 5) sont documentées ; la majorité des YoY/Display/Top ne le sont pas.
- [MAJEUR][CONFIRMÉ] **Aucun display folder** — 218/218 sans `displayFolder` (voir §3).
- [MINEUR][CONFIRMÉ] **Formats** — 48 mesures sans `formatString` : en grande partie mesures `FORMAT()` texte, couleurs hex, ranks (acceptable) ; à distinguer des mesures numériques réellement non formatées.
- [MINEUR][CONFIRMÉ] **Lineage tags** — présents sur mesures/colonnes auditées ; **aucun doublon** détecté dans les tables parsées (`lineage_dupes: []`).
- [INFO][CONFIRMÉ] **RLS** : absente — conforme à l’attendu contractuel (pas de RLS au devis).
- [INFO][CONFIRMÉ] **Tables** : descriptions `///` présentes sur facts/dims principales ; `_BridgePaysYoY` documentée.

### État : à corriger

---

## Recommandations (pas de fix appliqué)

1. Faire valider par Marc la formule `[Marge Brute]` et le couple CA natif (marge) / CA reconstruit (affichage).
2. Traiter I1–I3 comme prérequis mockup ou obtenir acceptation écrite des intérims.
3. Réécrire L06 pour le mode Local actuel + procédure de bascule SharePoint ; corriger les notes shipping/CA avec un snapshot daté.
4. Introduire display folders + archiver/masquer les mesures de contrôle orphelines avant remise.
5. Lancer la checklist runtime Annexe C avant signature.
6. Mettre à jour `livrables.md` seulement **après** validation client (ne pas cocher ✅ unilatéralement).
7. Ajouter les mesures V1 manquantes (Units shipped, per unit, PPP/PPM) **uniquement** si Marc les exige pour l’acceptation V1 (sinon les reporter clairement).

---

## Annexes

### A. Inventaire tables / relations

**Tables chargées** : `fact_commandes`, `fact_lignes`, `fact_transport`, `fact_factures_transport`, `dim_date`, `dim_pays`, `dim_transporteur`, `dim_type_commande`, `_Mesures`, `_BridgePaysYoY`, `_ParamLangueUI`, `_ParamAxePeriode`.

**Relations** (`relationships.tmdl`) :

| Nom | From → To | Active | Filtre |
|-----|-----------|--------|--------|
| rel_transport_commandes | fact_transport.order_id → fact_commandes.id_commande | oui | one-direction (défaut) |
| rel_lignes_commandes | fact_lignes.order_id → fact_commandes.id_commande | oui | défaut |
| rel_commandes_pays | fact_commandes.code_pays → dim_pays.code_pays | oui | défaut |
| rel_commandes_type | fact_commandes.type_commande → dim_type_commande.type_commande | oui | défaut |
| rel_commandes_date | fact_commandes.date_commande → dim_date.date | oui | défaut |
| rel_transport_transporteur | fact_transport.transporteur → dim_transporteur.transporteur | oui | défaut |
| rel_factures_transporteur | fact_factures_transport.transporteur → dim_transporteur.transporteur | **non** | USERELATIONSHIP |
| rel_factures_date | fact_factures_transport.date_facture → dim_date.date | **non** | USERELATIONSHIP |
| rel_factures_colis | fact_factures_transport.id_package → fact_transport.id_package | oui | défaut |

**Colonnes candidates non référencées (statique)** :

- `dim_date` : annee, trimestre, mois, nom_mois, semaine, jour_semaine, num_jour_semaine, semaine_annee_libelle, nom_mois_annee
- `dim_pays` : nom_pays, zone_geo, continent
- `dim_transporteur` : type_service, statut_integration, actif
- `fact_commandes` : origin_order_id, source, currency, gross_margin, contribution_profit_eur, contribution_margin
- `fact_factures_transport` : service, pays_destination, poids, devise, nb_candidats_resolution
- `fact_lignes` : id_article, list_price_eur, group_type, package_id
- `fact_transport` : cout_transport_facture

### B. Inventaire mesures (synthèse)

| Métrique | Valeur |
|----------|--------|
| Nombre total | 218 |
| Display folders | 0 |
| Avec `///` doc | ~96 (44 %) |
| Sans `formatString` | 48 (dont FORMAT/couleurs) |
| Orphelines | 64 |
| `FORMAT()` texte | 37 |
| Préfixes principaux | B2C Display (13), Mkt Display (13), Top Loss (11), Couleur YoY (5), KPI Compact (4), … |

**Orphelines (64)** — ni visuel ni autre mesure :

`Nb Colis (coût estimé)`, `Nb Colis (coût non disponible)`, `Nb Colis Facturés`, `Nb Articles (contrôle grain groupe)`, `Nb Articles Annulés Avant Expédition`, `Nb Articles Annulés Après Expédition`, `Marge Brute (grain article, prov.)`, `CA Commandes Annulation Partielle`, `Coût Transport Facturé`, `Taux Écart Coût`, `Coût Moyen Colis`, `Taux Marge Brute (prov.)`, `Écart Marge vs Backend`, `Écart Marge vs Backend (v2)`, `Taux Matching`, `Nb Commandes Non Matchées`, `Écart Réel vs Facturé`, `Taux Matching Factures`, `Panier Moyen`, `Poids Total (kg)`, `Marge YTD (prov.)`, `Évolution CA`, `Lignes Colis par Facture (hors 1re)`, `Vrais Doublons (Facture + Suivi)`, `Doublons Numero Suivi Factures`, `Colis Order ID Manquant`, `Colis Numero Suivi Manquant`, `Commandes Code Pays Non Attribué`, `Commandes Sans Colis`, `Colis Sans Commande`, `Lignes Facture Coût Transport Zero ou Null`, `Unités commandées YoY Δ`, `Revenu YoY Δ`, `Revenu YoY %`, `Taux Marge Brute YoY bps`, `Nb Commandes YoY Δ`, `Nb Commandes YoY %`, `CA HT Net Annulation YoY Δ`, `CA HT Net Annulation YoY %`, `Frais Port Encaissés YoY Δ`, `Frais Port Encaissés YoY %`, `Coût Achat Total YoY Δ`, `Coût Achat Total YoY %`, `Coût Transport Amont YoY Δ`, `Coût Transport Amont YoY %`, `Coût Transport Outbound (Retenu) YoY Δ`, `Coût Transport Outbound (Retenu) YoY %`, `Douanes Taxes YoY Δ`, `Douanes Taxes YoY %`, `Commissions Marketplace YoY Δ`, `Commissions Marketplace YoY %`, `Fournitures Expédition YoY Δ`, `Fournitures Expédition YoY %`, `Retours Remboursements YoY Δ`, `Retours Remboursements YoY %`, `Coûts Génériques YoY Δ`, `Coûts Génériques YoY %`, `Marge Brute (reconstruit) YoY Δ`, `Marge Brute (reconstruit) YoY %`, `Taux Marge Brute (reconstruit) YoY bps`, `Chart label — Revenue YoY`, `Chart label — Gross Profit YoY`, `Revenu (reconstruit, alloué langue) PY`, `Top Keep ISBN — Revenue`.

### C. Commandes de vérification runtime (pour les `[HYPOTHÈSE]`)

| # | Objectif | Outil / commande |
|---|----------|------------------|
| C1 | Valider rendu 8 pages vs `_mockup_pages/page_05`…`page_12` | Power BI Desktop — ouvrir `powerbi/Lireka_Profitabilite.pbip`, refresh, capture |
| C2 | Recalculer `_BridgePaysYoY` après refresh | Desktop — refresh modèle obligatoire (SPEC §5.3) |
| C3 | Perf KPI + charts GV / allocation langue | Desktop → Vue → Performance Analyzer |
| C4 | Cardinalité / taille dict colonnes | VertiPaq Analyzer (VPAX) sur le modèle |
| C5 | `[Marge Brute]` total vs export finance | DAX Studio : `EVALUATE ROW("MB", [_Mesures].[Marge Brute])` avec filtre date métier |
| C6 | Unicité `fact_transport[id_package]` | DAX Studio / SQL-équivalent : `COUNTROWS` vs `DISTINCTCOUNT(id_package)` |
| C7 | Interactions visuels | Desktop — Format → Éditer les interactions |
| C8 | Matching factures taux réel | Desktop — carte `[Taux Matching]` / `[Taux Matching Factures]` sur période facturée |
| C9 | Basculer SourceMode SharePoint chez client | Desktop → Transformer les données → Paramètres : `SourceMode`, `SharePointSiteURL`, `LocalRootPath` |

---

*Fin de l’audit. Aucun fichier modèle/rapport n’a été modifié à des fins de correction.*
