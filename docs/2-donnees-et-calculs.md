# 2. Données et calculs

Ce document décrit d'où viennent les données, comment elles sont chargées et comment chaque indicateur est calculé. Il constitue la documentation du processus prévue au devis.

État au 26/10/2026.

---

## 1. Source des données

Toutes les données sont lues dans la base PostgreSQL analytique de Lireka, maintenue par COEX :

| Élément | Valeur |
|---|---|
| Serveur | `10.111.119.1:5432`, réseau COEX, joignable uniquement par le tunnel WireGuard |
| Base | `analytics` |
| Schéma | `analytics_views` |
| Compte de lecture | `liber_power_bi` (lecture seule ; mot de passe détenu par COEX et Lireka, jamais écrit dans le projet) |
| Mise à jour de la base | synchronisation COEX quotidienne à partir de 2:00 |

| Vue | Contenu utilisé |
|---|---|
| `customer_order` | Commandes : montants TTC et HT, état, canal, pays, date, coûts par commande |
| `customer_order_item` | Articles : langue, état, retours, coûts génériques |
| `customer_order_item_group` | ISBN et prix |
| `package` | Colis : coût de transport, droits et taxes, fournitures, numéro de suivi |
| `v_carrier_invoice_lines` | Lignes de factures transporteurs, rattachées au colis par COEX |

Le projet Power BI ne contient aucune donnée : il ne stocke que la définition des requêtes, du modèle et des pages.

---

## 2. Chargement (Power Query)

Mode **Import**. Les jointures et agrégations sont calculées par PostgreSQL (requêtes SQL natives) ; la passerelle ne reçoit que le résultat.

Paramètres (*Transformer les données* > *Gérer les paramètres*) : `PgServer`, `PgDatabase`, `PgSchema`.

| Table du modèle | Grain | Contenu |
|---|---|---|
| `fact_commandes` | commande | Revenu, coûts, marge, état, canal, pays, date |
| `fact_lignes` | article | Langue du livre, ISBN, état de l'article |
| `fact_transport` | colis | Coût de transport retenu, droits et taxes, fournitures, transporteur |
| `fact_factures_transport` | ligne de facture | Contrôles transporteurs |
| `dim_date` | jour | Calendrier de 2020 à la fin de l'année suivant la dernière commande |
| `dim_pays`, `dim_type_commande`, `dim_isbn`, `dim_transporteur` | | Axes d'analyse |
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
- **Commandes avec montant** : seules les commandes dont le montant hors TVA est supérieur à 0 entrent dans le revenu, les coûts et la marge. Selon COEX (26/10/2026), les commandes sans montant sont toutes des commandes annulées. Leur nombre est affiché en bandeau.
- **Commandes annulées** (`CANCELLED`) : revenu et coût d'achat à 0 (décision du 25/08/2026). Le transport amont est conservé ; le transport sortant, les droits et les fournitures ne comptent que si un colis a été expédié.

### Revenue
`order_amount_excl_vat_eur` : prix payé par le client, **hors TVA**, frais de port inclus, hors commandes annulées.

### Gross Profit (marge brute)

| Poste | Source |
|---|---|
| Revenue | `customer_order.order_amount_excl_vat_eur` |
| − Coût d'achat | `customer_order.product_cost_eur` |
| − Transport amont | `customer_order.inbound_transportation_cost_eur` (factures transporteurs depuis le 01/01/2025) |
| − Transport sortant | par colis : montant facturé par le transporteur s'il existe, sinon coût enregistré sur le colis |
| − Droits et taxes | `package.duties_taxes_eur` |
| − Commissions marketplace | `customer_order.marketplace_fees_eur` |
| − Fournitures d'expédition | `package.shipping_supply_cost_eur` |

**Hors marge brute** : retours et remboursements, coûts génériques. Ils sont disponibles dans le modèle et affichés à part dans les tableaux. **Frais de paiement** : disponibles en base (`payment_cost_eur`), pas encore intégrés (décision en attente, voir [4-passation.md](4-passation.md)).

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
Une commande peut contenir des livres de plusieurs langues. Quand on filtre sur la langue ou l'ISBN, les montants de la commande (revenu, coûts, marge) sont répartis **à parts égales** entre ses articles.

### Loss analysis
- **Commande déficitaire** : marge brute de la commande inférieure à 0.
- **Poste basculant** : pour chaque poste de coût, on compare le coût de la commande au coût « normal » de son canal (médiane du ratio coût / revenu des commandes non déficitaires des 12 derniers mois). Le poste retenu est celui dont l'excès explique le plus la perte et qui, ramené à la normale, rendrait la commande positive. Sinon : « Structurally loss-making ».
- **Tranches de panier** : sur le montant hors TVA de la commande.

---

## 4. Actualisation

| Étape | Heure (Paris) |
|---|---|
| Synchronisation de la base par COEX | à partir de 2:00 |
| Actualisation du modèle dans le Service Power BI, par la passerelle Lireka-Gateway (VPS, tunnel WireGuard) | 6:00 |

Contrôle : *modèle sémantique* > *Historique d'actualisation*. Les échecs du 20/10 et du 23/10/2026 venaient d'une synchronisation COEX anormalement longue ; COEX a corrigé le problème le 26/10/2026.

---

## 5. Écarts connus avec le tableau de profitabilité du backoffice

Au 26/10/2026, le tableau de profitabilité du backoffice utilise des **coûts estimés**, alors que la base analytique (et donc Power BI) utilise les **coûts réels** (factures transporteurs, coûts d'achat fournisseurs). COEX aligne le backoffice sur ces mêmes valeurs. Les décisions de définition encore ouvertes sont listées dans [4-passation.md](4-passation.md).
