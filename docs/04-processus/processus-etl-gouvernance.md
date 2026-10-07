# Documentation du processus — modèle profitabilité Lireka

> **Livrable contractuel** : L06 — Documentation du processus  
> **Référence** : [`../01-cadrage/devis.md`](../01-cadrage/devis.md)  
> **Date** : 14 juillet 2026

Ce document décrit **comment le modèle livré se recharge**, tel qu'implémenté dans  
`powerbi/Lireka_Profitabilite.pbip`. Il ne définit pas de processus récurrent, de SLA  
ni de rôles de gouvernance — ces éléments ne figurent pas au devis.

---

## 1. Objet livré

Le devis prévoit l'intégration des données transporteurs et commandes dans Power BI,  
la jointure factures ↔ commandes, un dashboard de profitabilité et la documentation  
du processus. Concrètement :

| Livrable devis | Implémentation |
|----------------|----------------|
| 3 transporteurs intégrés (La Poste, Colis Privé, Chronopost) | Récaps Colissimo + Chronopost → `fact_factures_transport` ; Colis Privé via backend (`fnNormaliserTransporteur`), coût estimé |
| Dataset commandes structuré | `fact_commandes`, `fact_transport`, `fact_lignes` depuis le backend |
| Jointure factures ↔ commandes | Clé métier = n° de suivi ; rapprochement opérationnel facture → colis par `id_package` (proximité de date en Power Query) |
| Dashboard profitabilité | Rapport `Lireka_Profitabilite.Report` |
| Documentation du processus | Ce fichier |

Les colis **Postes Canada** (préfixe suivi `Q013…`) sont intégrés au modèle via  
`package.csv` ; ils n'ont pas de factures transporteur dans les récaps actuels.

---

## 2. Source des données

> Mis à jour le 05/10/2026 : la lecture SharePoint décrite précédemment n'a jamais été activée ; les CSV locaux ont été remplacés par PostgreSQL.

Toutes les données sont lues dans la base PostgreSQL analytique Lireka (`analytics`), via la passerelle **Lireka-Gateway** (VPN COex). Aucun fichier n'est lu par le modèle.

**Paramètres Power Query** (*Transformer les données* → *Gérer les paramètres*) : `PgServer`, `PgDatabase`, `PgSchema` (`analytics_views`).

| Objet PostgreSQL | Usage |
|------------------|-------|
| `analytics_views.customer_order` | Commandes (CA, coûts, pays, canal, date) |
| `analytics_views.customer_order_item` | Articles, coûts retours / génériques |
| `analytics_views.customer_order_item_group` | ISBN, prix |
| `analytics_views.package` | Colis (coût estimé, douanes, fournitures, suivi) |
| `analytics_views.v_carrier_invoice_lines` | Lignes de factures transporteurs rattachées au colis par le backend |

Tout le modèle lit le schéma du paramètre `PgSchema` (`analytics_views`).

---

## 3. Chargement dans le modèle (Power Query M)

Mode : **Import**. Les jointures, agrégations et `DISTINCT` sont calculés par PostgreSQL (requêtes SQL natives via `fnRequeteSql`) ; la passerelle ne reçoit que le résultat.

| Table Power BI | Source | Rôle |
|----------------|--------|------|
| `fact_commandes` | `customer_order` + retours / génériques agrégés depuis `customer_order_item` | Commandes (grain commande) |
| `fact_transport` | `package` + montants `v_carrier_invoice_lines` agrégés par colis | Colis (coût retenu = facturé si disponible, sinon estimé) |
| `fact_lignes` | `customer_order_item` ⋈ `customer_order_item_group` ⋈ `customer_order` | Articles (grain article) |
| `fact_factures_transport` | `v_carrier_invoice_lines` | Lignes de factures |
| `dim_pays`, `dim_type_commande`, `dim_isbn` | `SELECT DISTINCT` en base | Axes d'analyse |
| `dim_date` | générée ; bornée par `DateDerniereCommande` (max `origin_created` des commandes avec CA) | Axe temporel, fenêtre 12 derniers mois |

Le transporteur sur les colis est **inféré du numéro de suivi** (`fnNormaliserTransporteur`).

### Relations principales

- `fact_transport[order_id]` → `fact_commandes[id_commande]` (`rel_transport_commandes`)
- `fact_lignes[order_id]` → `fact_commandes[id_commande]` (`rel_lignes_commandes`)
- `fact_factures_transport[id_package]` → `fact_transport[id_package]` (`rel_factures_colis`)
- `fact_commandes` → `dim_pays`, `dim_type_commande`, `dim_date`
- `fact_transport` → `dim_transporteur`
- Relations directes facture → `dim_transporteur` / `dim_date` : **inactives** (`isActive: false`) ; activables via `USERELATIONSHIP` dans les mesures de contrôle

---

## 4. Refresh du modèle

- **Power BI Desktop** : ouvrir `powerbi/Lireka_Profitabilite.pbip` sur un poste ayant accès à la base (VPN COex), puis *Actualiser*. Au premier refresh, Desktop demande d'approuver les requêtes SQL natives.
- **Power BI Service** : le dataset se rafraîchit via la passerelle Lireka-Gateway (source PostgreSQL configurée dans la passerelle). La fréquence relève du choix Lireka.
- **Période affichée** : la fenêtre « 12 derniers mois » est calée sur la dernière commande avec CA en base, pas sur la date du refresh. La carte « Data through … » de chaque page affiche cette date.

---

## 5. Points de vigilance connus

- **Marge brute publiée** : `[Marge Brute (reconstruit)]` = formule Marc (Revenue − COGS − transport amont
  − transport sortant − droits et taxes − commissions marketplace − fournitures). Retours et coûts génériques
  hors marge brute. `[Marge Brute]` (avec Bloc 5) reste une mesure de contrôle masquée.
- **Commandes sans CA** : `fact_commandes[ca_disponible] = "Non"` si `order_amount_eur` est vide ou nul
  (marketplaces depuis 09/2024, toutes sources sept.-nov. 2024). Ces commandes sont exclues du revenu,
  des coûts et de la marge ; leur nombre est affiché sur General View et Marketplaces.
- **Matching factures** : les lignes de `v_carrier_invoice_lines` rattachées à un colis alimentent le coût
  rapproché (`source_cout = "facture_rapprochee"`). Les colis sans facture mais avec
  coût backend utilisent `source_cout = "backend_seul"` ; sans les deux :
  `source_cout = "aucun"`. Colis Privé et Postes Canada restent en coût estimé backend.
- **Statut CANCELLED** : règle actée (CA=0 et frais de port exclus dans les mesures
  `[CA HT Net Annulation]` / `[Marge Brute]` ; coûts conservés). Les commandes annulées
  restent dans `fact_commandes` — pas de filtre partition.

---

## 6. Fichiers de référence

| Fichier | Contenu |
|---------|---------|
| `powerbi/Lireka_Profitabilite.SemanticModel/definition/expressions.tmdl` | Requêtes M partagées, fonctions SharePoint |
| `powerbi/Lireka_Profitabilite.SemanticModel/definition/relationships.tmdl` | Relations du modèle |
| `powerbi/models/mesures-dax.md` | Référentiel des mesures DAX |

---

*Documentation alignée sur le périmètre contractuel — proposition commerciale juillet 2026.*
