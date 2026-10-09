# Documentation du processus — modèle profitabilité Lireka

> **Livrable contractuel** : L06 — Documentation du processus  
> **Référence** : [`../01-cadrage/devis.md`](../01-cadrage/devis.md)  
> **Date** : 14 juillet 2026 — mis à jour le 09/10/2026 (source PostgreSQL, refresh planifié)

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
| 3 transporteurs intégrés (La Poste, Colis Privé, Chronopost) | Factures Colissimo + Chronopost (`v_carrier_invoice_lines`) → `fact_factures_transport` ; Colis Privé via backend (`fnNormaliserTransporteur`), coût estimé |
| Dataset commandes structuré | `fact_commandes`, `fact_transport`, `fact_lignes` depuis le backend |
| Jointure factures ↔ commandes | Rattachement facture → colis (`package_id`) et commande (`order_id`) fait par le backend dans `v_carrier_invoice_lines` ; aucun rapprochement côté Power BI |
| Dashboard profitabilité | Rapport `Lireka_Profitabilite.Report` |
| Documentation du processus | Ce fichier |

Les colis **Postes Canada** (préfixe suivi `Q013…`) sont intégrés au modèle via  
`analytics_views.package` ; ils n'ont pas de factures transporteur en base.

---

## 2. Source des données

> Mis à jour le 05/10/2026 : la lecture SharePoint décrite précédemment n'a jamais été activée ; les CSV locaux ont été remplacés par PostgreSQL.

Toutes les données sont lues dans la base PostgreSQL analytique Lireka (`analytics`), via la passerelle **Lireka-Gateway** (passerelle on-premises installée sur une VM Azure, reliée au réseau COex par un tunnel WireGuard). Aucun fichier n'est lu par le modèle.

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
| `fact_commandes` | `customer_order` + retours / génériques agrégés depuis `customer_order_item` + transport retenu, douanes et fournitures agrégés depuis `package` / `v_carrier_invoice_lines` + médianes par canal (Loss analysis) | Commandes (grain commande) |
| `fact_transport` | `package` + montants `v_carrier_invoice_lines` agrégés par colis | Colis (coût retenu = facturé si disponible, sinon estimé) |
| `fact_lignes` | `customer_order_item` ⋈ `customer_order_item_group` ⋈ `customer_order` | Articles (grain article) |
| `fact_factures_transport` | `v_carrier_invoice_lines` | Lignes de factures |
| `dim_pays`, `dim_type_commande`, `dim_isbn` | `SELECT DISTINCT` en base | Axes d'analyse |
| `dim_date` | générée ; bornée par `DateDerniereCommande` (max `origin_created` des commandes avec CA) | Axe temporel |

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

- **Power BI Desktop** : ouvrir `powerbi/Lireka_Profitabilite.pbip` sur un poste ayant accès à la base (tunnel WireGuard actif, au moins 16 Go de RAM), puis *Actualiser*. Au premier refresh, Desktop demande d'approuver les requêtes SQL natives. Si le poste utilise la configuration WireGuard de la VM, couper le tunnel de la VM pendant ce temps et le relancer ensuite (une clé WireGuard ne peut être active que sur une machine).
- **Power BI Service** : le dataset se rafraîchit via la passerelle Lireka-Gateway (source PostgreSQL configurée dans la passerelle). Actualisation planifiée quotidienne à 6:00 (Europe/Paris) ; le tunnel WireGuard de la VM doit être actif. Contrôle : historique d'actualisation du modèle sémantique dans le Service.
- **Période affichée** : un seul filtre de rapport « Period » (date relative, 12 derniers mois par défaut, modifiable dans le volet Filtres, par exemple « année civile précédente »). La base étant alimentée chaque jour, la période est calée sur la date du jour ; la carte « Data through … » de chaque page affiche la date de la dernière commande avec CA.
- **Slicers Date** : chaque page porte un slicer Date synchronisé (groupe `DateSync`) qui affine la période à l'intérieur du filtre « Period ».
- **Langue / ISBN** : quand un filtre porte sur la langue du livre ou l'ISBN, les montants au grain commande sont répartis à parts égales entre les articles de la commande (`[_Allocation ligne active]`, `fact_lignes[nb_articles_commande]`).
- **Comparaisons N-1** : si plus de 5 % des commandes non annulées de la période N-1 n'ont pas de montant de vente, les PY et variations de revenu et de marge sont vides (mesure `[_PY incomplet]`).

---

## 5. Points de vigilance connus

- **Marge brute publiée** : `[Marge Brute (reconstruit)]` = formule Marc (Revenue − COGS − transport amont
  − transport sortant − droits et taxes − commissions marketplace − fournitures). Retours et coûts génériques
  hors marge brute. `[Marge Brute]` (avec Bloc 5) reste une mesure de contrôle masquée.
- **Commandes sans CA** : `fact_commandes[ca_disponible] = "Non"` si `order_amount_eur` est vide ou nul
  en base. Ces commandes sont exclues du revenu,
  des coûts et de la marge ; leur nombre est affiché sur General View et Marketplaces.
- **Matching factures** : les lignes de `v_carrier_invoice_lines` rattachées à un colis alimentent le coût
  rapproché (`source_cout = "facture_rapprochee"`). Les colis sans facture mais avec
  coût backend utilisent `source_cout = "backend_seul"` ; sans les deux :
  `source_cout = "aucun"`. Colis Privé et Postes Canada restent en coût estimé backend.
- **Statut CANCELLED** : règle actée (décision Marc 25/08/2026) : CA, frais de port et coût d'achat à 0 ;
  transport amont conservé ; transport sortant, droits et fournitures portés par les colis (0 si jamais expédiée).
  Les commandes annulées restent dans `fact_commandes` — pas de filtre partition.

---

## 6. Fichiers de référence

| Fichier | Contenu |
|---------|---------|
| `powerbi/Lireka_Profitabilite.SemanticModel/definition/expressions.tmdl` | Paramètres `PgServer` / `PgDatabase` / `PgSchema`, `fnRequeteSql`, `DateDerniereCommande`, fonctions de normalisation, requêtes intermédiaires des factures |
| `powerbi/Lireka_Profitabilite.SemanticModel/definition/relationships.tmdl` | Relations du modèle |
| `powerbi/models/mesures-dax.md` | Référentiel des mesures DAX |

---

*Documentation alignée sur le périmètre contractuel — proposition commerciale juillet 2026.*
