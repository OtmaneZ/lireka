# 2. Données et calculs

Ce document décrit d'où viennent les données, comment elles sont chargées et comment chaque indicateur est calculé. Il constitue la documentation du processus prévue au devis.

État au 06/11/2026.

---

## 1. Source des données

Toutes les données sont lues dans la base PostgreSQL analytique de Lireka, maintenue par COEX.

| Élément | Valeur |
|---|---|
| Serveur | `10.111.119.1:5432`, réseau COEX, joignable uniquement par le tunnel WireGuard |
| Base | `analytics` |
| Schéma | `analytics_views` |
| Compte de lecture | `liber_power_bi`, en lecture seule. Le mot de passe est détenu par COEX et Lireka, il n'est jamais écrit dans le projet. |
| Mise à jour de la base | Synchronisation COEX quotidienne à partir de 2:00, terminée vers 6:30 |

| Vue | Contenu utilisé |
|---|---|
| `customer_order` | Commandes : montants TTC et HT, état, canal, pays, date, coûts par commande |
| `customer_order_item` | Articles : langue, état |
| `customer_order_item_group` | ISBN et prix |
| `package` | Colis : coût de transport, droits et taxes, fournitures, numéro de suivi |
| `v_carrier_invoice_lines` | Lignes de factures transporteurs, rattachées au colis par COEX |
| `v_book_titles` | Titre de chaque livre, une ligne par ISBN |

Le projet Power BI ne contient aucune donnée : il ne stocke que la définition des requêtes, du modèle et des pages.

---

## 2. Chargement

Le modèle est en mode **Import**. Les jointures et agrégations sont calculées par PostgreSQL, au moyen de requêtes SQL natives : la passerelle ne reçoit que le résultat.

Paramètres (*Transformer les données* > *Gérer les paramètres*) : `PgServer`, `PgDatabase`, `PgSchema`.

| Table du modèle | Grain | Contenu |
|---|---|---|
| `fact_commandes` | commande | Revenu, coûts, marge, état, canal, pays, date |
| `fact_lignes` | article | Langue du livre, ISBN, état de l'article |
| `fact_transport` | colis | Coût de transport retenu, droits et taxes, fournitures, transporteur |
| `fact_factures_transport` | ligne de facture | Contrôles des factures transporteurs |
| `dim_date` | jour | Calendrier de 2020 à la fin de l'année suivant la dernière commande |
| `dim_isbn` | livre | ISBN et titre |
| `dim_pays`, `dim_type_commande`, `dim_transporteur` | | Axes d'analyse |
| `BridgePnL` | | Lignes de la cascade du Profit bridge |

### Canaux

| Source de la commande | Canal |
|---|---|
| `WEBSITE` | Website B2C |
| `PRO_WEBSITE` | Website B2B |
| `AMAZON_*`, `CULTURA`, `RAKUTEN`, `FNAC` | Marketplaces |
| `ARTHAUD` | Librairie Arthaud |
| autre | Other |

---

## 3. Règles de calcul

### Périmètre

- **Commandes prises en compte** : la base analytique ne contient que les commandes arrivées à un état final (`SHIPPED`, `PICKED` ou `CANCELLED`). Les commandes en préparation apparaissent une fois expédiées : les derniers jours sont donc provisoirement plus bas que dans le backoffice. Choix validé par Lireka le 29/10/2026.
- **Commandes avec montant** : seules les commandes dont le montant hors TVA est supérieur à 0 entrent dans le revenu, les coûts et la marge. Selon COEX, les commandes sans montant sont toutes des commandes annulées. Leur nombre est affiché en bandeau.
- **Commandes annulées** (`CANCELLED`) : revenu et coût d'achat à 0. Le transport amont est conservé. Le transport sortant, les droits et les fournitures ne comptent que si un colis a été expédié.

### Revenue

`order_amount_excl_vat_eur` : prix payé par le client, **hors TVA**, frais de port inclus, hors commandes annulées.

### Gross Profit (marge brute)

| Poste | Source |
|---|---|
| Revenue | `customer_order.order_amount_excl_vat_eur` |
| − Coût d'achat | `customer_order.product_cost_eur` |
| − Transport amont | `customer_order.inbound_transportation_cost_eur`, issu des factures transporteurs depuis le 01/01/2025 |
| − Transport sortant | Par colis : montant facturé par le transporteur s'il existe, sinon coût enregistré sur le colis |
| − Droits et taxes | `package.duties_taxes_eur` |
| − Commissions marketplace | `customer_order.marketplace_fees_eur` |
| − Fournitures d'expédition | `package.shipping_supply_cost_eur` |
| − Retours et remboursements | `customer_order.returns_and_refunds_eur` : remboursements, rétrofacturations et remplacements, hors commandes annulées |

**Hors marge brute :**
- **Coûts génériques** : selon COEX, ils sont à 0 pour toutes les commandes depuis le 01/01/2025. Ils ne sont pas affichés.
- **Frais de paiement** : disponibles en base (`payment_cost_eur`), non intégrés à la marge brute.

### Autres indicateurs

| Indicateur | Calcul |
|---|---|
| Gross Margin | Gross Profit / Revenue |
| Product margin | (Revenue − coût d'achat) / Revenue |
| Ordered units | Nombre d'articles des commandes avec montant et des commandes annulées |
| Cancellation rate | Articles annulés / Ordered units |
| Valeurs « par unité » | Montant / unités des commandes avec montant |
| PY, YoY | Même période un an plus tôt. Laissés vides si plus de 5 % des commandes non annulées de la période précédente n'ont pas de montant. |

### Filtre de langue ou d'ISBN

Une commande peut contenir des livres de plusieurs langues. Quand on filtre sur la langue ou sur l'ISBN, les montants de la commande (revenu, coûts, marge) sont répartis **à parts égales** entre ses articles.

---

## 4. Actualisation

| Étape | Heure (Paris) |
|---|---|
| Synchronisation de la base par COEX | À partir de 2:00, terminée vers 6:30 |
| Actualisation du modèle dans le Service Power BI, par la passerelle Lireka-Gateway (VPS, tunnel WireGuard) | 8:00, durée d'environ 20 minutes |

Contrôle : *modèle sémantique* > *Historique d'actualisation*. La ligne du jour doit indiquer « Terminé ».

Échecs passés, tous corrigés :
- 20/10 et 23/10/2026 : synchronisation COEX anormalement longue, corrigée par COEX le 26/10/2026.
- 01/11/2026 : connexion interrompue pendant la lecture des titres des livres. Corrigé le 03/11/2026 par la vue légère `v_book_titles`, fournie par COEX.

---

## 5. Cohérence avec le backoffice

Depuis le 02/11/2026, le tableau de profitabilité du backoffice utilise les mêmes sources que la base analytique, donc que Power BI : coûts réels, factures transporteurs, annulations déduites du chiffre d'affaires. C'est vrai au niveau global comme au niveau de chaque commande.

Le 03/11/2026, Lireka a comparé Power BI et le backoffice aux comptes du troisième trimestre et a conclu que les données sont fiables (détail dans le document 6, « Compte rendu de recette »).
