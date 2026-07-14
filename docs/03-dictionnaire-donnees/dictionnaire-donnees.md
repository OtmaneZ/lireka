# Dictionnaire de données — Lireka

> **⚠️ Hors périmètre devis** — Document de travail technique décrivant le modèle livré dans  
> `powerbi/Lireka_Profitabilite.pbip`. Le livrable contractuel L06 est  
> [`processus-etl-gouvernance.md`](../04-processus/processus-etl-gouvernance.md).  
> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> **Dernière mise à jour** : 14 juillet 2026

---

## 1. Sources et chargement

Les données ne passent **pas** par un dépôt `data/processed/` intermédiaire.  
Power Query M lit les CSV directement depuis SharePoint (`Power_BI_Datawarehouse/`).

| Table modèle | Fichier SharePoint | Échantillon local (tests) |
|--------------|-------------------|---------------------------|
| `fact_commandes` | `Données_Backend/customer_order.csv` | — |
| `fact_transport` | `Données_Backend/package.csv` | — |
| `fact_factures_transport` | `Dashboards_transporteurs/COLISSIMO …/*.csv`, `…/CHRONOPOST …/*.csv` | `data/samples/transporteurs/*/` |
| `fact_lignes` | `Données_Backend/customer_order_item_group.csv` | — |

Staging partagé (non chargé) : `stg_customer_order`, `stg_factures_transport_resolu` — voir `expressions.tmdl`.

---

## 2. Commandes — `fact_commandes`

**Grain** : une ligne par commande.  
**Source** : `Données_Backend/customer_order.csv` via `stg_customer_order`.

| Colonne modèle | Type | Source CSV (`customer_order.csv`) | Description |
|----------------|------|-----------------------------------|-------------|
| `id_commande` | int64 | `id` | Clé primaire commande |
| `origin_order_id` | text | `origin_order_id` | Identifiant d'origine (marketplace, etc.) |
| `state` | text | `state` | Statut commande (`SHIPPED`, `CANCELLED`, …) |
| `source` | text | `source` | Canal de vente brut (`WEBSITE`, `AMAZON_FR`, …) |
| `type_commande` | text | dérivé de `source` | Axe d'analyse dashboard ; repli `INCONNU` si vide |
| `code_pays` | text | `destination_country` | Code pays ISO **alpha-2** normalisé ; repli `??` si absent |
| `currency` | text | `currency` | Devise d'origine |
| `ca_ht` | decimal | `order_amount_eur` | Chiffre d'affaires HT en EUR |
| `shipping_fee_eur` | decimal | `shipping_fee_eur` | Frais de port facturés au client en EUR |
| `cout_achat` | decimal | `product_cost_eur` | Coût d'achat des livres en EUR |
| `cout_transport_estime` | decimal | `total_shipping_cost_to_delivery_country_eur` | Coût transport estimé backend en EUR |
| `gross_profit_eur` | decimal | `gross_profit_eur` | Marge brute backend — **référence de contrôle** |
| `gross_margin` | decimal | `gross_margin` | Taux de marge brute backend |
| `contribution_profit_eur` | decimal | `contribution_profit_eur` | Marge contributive backend |
| `contribution_margin` | decimal | `contribution_margin` | Taux de marge contributive |
| `date_commande` | date | `origin_created` (tronqué au jour) | Date commande — clé vers `dim_date` |

> **Note** : le numéro de suivi n'est **pas** sur `fact_commandes` ; il est porté par `fact_transport` (grain colis).

---

## 3. Colis — `fact_transport`

**Grain** : une ligne par colis.  
**Source** : `Données_Backend/package.csv`.

| Colonne modèle | Type | Source CSV (`package.csv`) | Description |
|----------------|------|------------------------------|-------------|
| `id_package` | int64 | `id` | Clé primaire colis |
| `order_id` | int64 | `order_id` | FK vers `fact_commandes[id_commande]` |
| `numero_suivi` | text | `tracking_id` | Numéro de suivi nettoyé (TRIM, UPPER) — clé jointure factures |
| `transporteur` | text | inféré | Dérivé de `fnNormaliserTransporteur(tracking_id)` — pas de colonne transporteur en source |
| `poids_kg` | decimal | `weight` | Poids en kg (`weight` grammes ÷ 1000) |
| `cout_transport` | decimal | `shipping_cost_eur` | Coût transport en EUR (estimation backend ou coût saisi) |
| `shipping_supply_cost_eur` | decimal | `shipping_supply_cost_eur` | Coût fourniture expédition |
| `duties_taxes_eur` | decimal | `duties_taxes_eur` | Droits et taxes |
| `source_cout` | text | calculé | `reel` (facture Colissimo/Chronopost rapprochée), `estime`, `non_disponible` |

Jointure factures ↔ colis : table pont `rel_factures_colis` sur `id_package`.

---

## 4. Factures transporteurs — `fact_factures_transport`

**Grain** : une ligne par ligne de récap facture.  
**Sources** : récaps CSV français sur SharePoint (`;` séparateur, virgule décimale) — Colissimo (La Poste) et Chronopost.  
Unifiées dans `stg_factures_transport_resolu` (résolution colis par proximité de date).

| Colonne modèle | Type | Source récap | Description |
|----------------|------|--------------|-------------|
| `numero_facture` | text | Chronopost uniquement | Vide pour Colissimo |
| `date_facture` | date | colonne date récap | Clé vers `dim_date` |
| `numero_suivi` | text | numéro de suivi récap | Nettoyé — clé vers `fact_transport` |
| `transporteur` | text | dérivé | `La Poste` (Colissimo) ou `Chronopost` |
| `service` | text | colonne service | Type de prestation |
| `pays_destination` | text | colonne destination | Pays de livraison (préfixe Colissimo) |
| `poids` | decimal | colonne poids | Poids en kg |
| `cout_transport` | decimal | `TOTAL HT` | Coût transport facturé HT en EUR |
| `devise` | text | constante | `EUR` |
| `order_id` | int64 | résolu | Commande rattachée (proximité date) — masqué |
| `id_package` | int64 | résolu | Colis rattaché — masqué |

Colis Privé et Postes Canada : pas de récap facture dans le périmètre ; coût via `fact_transport` (`source_cout = estime`).

---

## 5. Mesures DAX (dashboard profitabilité)

Les indicateurs sont des **mesures** dans `_Mesures`, pas des colonnes calculées sur `fact_commandes`.  
Référentiel complet : [`powerbi/models/mesures-dax.md`](../../powerbi/models/mesures-dax.md).

| Mesure | Formule (résumé) | Description |
|--------|------------------|-------------|
| `Coût Transport Réel` | `SUM(fact_transport[cout_transport])` | Coût au grain colis — **pas** de colonne `cout_transport_reel` sur `fact_commandes` |
| `Coût Transport Estimé` | `SUM(fact_commandes[cout_transport_estime])` | Estimation backend |
| `Marge Brute (prov.)` | `CA - Coût Achat - Coût Transport Réel` | **Provisoire** — validation Marc en attente |
| `Marge Brute Backend (réf.)` | `SUM(fact_commandes[gross_profit_eur])` | Référence de contrôle |

---

## 6. Tables de dimensions

### dim_date

Calendrier généré en M. Colonnes : `date`, `annee`, `trimestre`, `mois`, `nom_mois`, `semaine`, `jour_semaine`.

### dim_pays

Dérivée des codes `destination_country` distincts (via `stg_customer_order`).

| Colonne | Type | Description |
|---------|------|-------------|
| `code_pays` | text | PK — ISO 3166-1 **alpha-2** (`FR`, `DE`, … ; `??` = pays non attribué) |
| `nom_pays` | text | Libellé pays |
| `zone_geo` | text | Zone géographique |
| `continent` | text | Continent |

### dim_transporteur

Référentiel statique (8 transporteurs). Colonnes : `transporteur`, `type_service`, `statut_integration`, `actif`.

| Transporteur | Statut |
|--------------|--------|
| La Poste, Colis Privé, Chronopost | Nouveau (intégré) |
| DHL, FedEx, UPS | Existant (référence) |
| Postes Canada | Autre (colis backend) |

### dim_type_commande

Dérivée des valeurs distinctes de `customer_order.source`.

| Colonne | Type | Description |
|---------|------|-------------|
| `type_commande` | text | PK — valeur `source` normalisée |
| `categorie` | text | Marketplace / B2C direct / B2B / Autre (règle M) |
| `libelle` | text | Libellé affiché |

---

## 7. Échantillons locaux (`data/samples/`)

Fichiers anonymisés pour tests et validation hors SharePoint.  
**Attention** : `data/samples/commandes/commandes_202606.csv` utilise des noms de colonnes **français simplifiés** (`id_commande`, `ca_ht`, …) — schéma cible historique, **pas** le format brut `customer_order.csv`.  
Les échantillons factures (`data/samples/transporteurs/*/`) sont au format unifié simplifié pour `scripts/validation/validate_data.py`.

---

## 8. Glossaire

| Terme | Définition |
|-------|-----------|
| **Marge brute (prov.)** | CA HT − Coût d'achat − Coût transport réel (mesure DAX, en attente validation Marc) |
| **Coût transport estimé** | `total_shipping_cost_to_delivery_country_eur` — estimation backend Lireka |
| **Coût transport réel** | `fact_transport[cout_transport]` au grain colis (facture rapprochée ou coût backend) |
| **Numéro de suivi** | `package.tracking_id` — clé de liaison factures ↔ colis |
| **source_cout** | Origine du coût transport sur un colis : `reel`, `estime`, `non_disponible` |
| **Star schema** | Modèle en étoile : tables de faits au centre, dimensions autour |

---

*Dictionnaire aligné sur le modèle PBIP livré — mis à jour à chaque évolution du `.pbip`.*
