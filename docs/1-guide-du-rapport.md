# 1. Guide du rapport

Ce guide décrit les 11 pages du rapport **Lireka_Profitabilite** et la signification de chaque indicateur. Les règles de calcul détaillées sont dans [2-donnees-et-calculs.md](2-donnees-et-calculs.md).

Le rapport est en anglais ; les termes affichés sont repris tels quels ci-dessous.

---

## Éléments communs

| Élément | Où | Rôle |
|---|---|---|
| **Filtre « Period »** | volet Filtres, toutes les pages | Période analysée. Par défaut : les 12 derniers mois. Modifiable, par exemple « année civile précédente ». |
| **Slicer « Date »** | rail de gauche, toutes les pages | Affine la période à l'intérieur du filtre « Period ». Synchronisé entre les pages. |
| **Carte « Data through … »** | rail de gauche, toutes les pages | Date de la dernière commande avec montant dans la base. Si les données ont plus d'un jour, leur âge est affiché. |
| **Slicer « Language »** | pages de ventes | Langue du livre. Quand il est utilisé, les montants de chaque commande sont répartis à parts égales entre ses livres ; un bandeau « Language filter: amounts split per book » le signale. |
| **Slicer « Channel »** | General View, Profit bridge, Transport and carriers, Loss analysis | Website B2C, Website B2B, Marketplaces, Librairie Arthaud. |
| **Granularity (Month / Week)** | General View, Librairie Arthaud | Pas de temps des graphiques. |

### Les quatre cartes KPI (haut des pages de synthèse)

| Carte | Définition |
|---|---|
| **Ordered units** | Nombre de livres commandés (une unité par article). |
| **Revenue** | Chiffre d'affaires **hors TVA**, frais de port inclus, hors commandes annulées. |
| **Gross Profit** | Marge brute : Revenue moins coût d'achat, transport amont, transport sortant, droits et taxes, commissions marketplace et fournitures d'expédition. |
| **Gross Margin** | Gross Profit / Revenue. |

Sous chaque carte : la valeur de l'année précédente (**PY**) et la variation (**YoY**, en % ; en points de base, **bps**, pour la marge). La comparaison est laissée vide si plus de 5 % des commandes de la période précédente n'ont pas de montant en base.

---

## Les pages

### General View
Synthèse des trois canaux en ligne (Website B2C, Website B2B, Marketplaces ; Librairie Arthaud a sa propre page).
- Cartes KPI.
- **Revenue by sales channel** et **Gross Profit by sales channel** : évolution mensuelle par canal, avec l'année précédente en courbe.
- Variation N-1 du revenu et de la marge brute par canal.
- **Units, revenue and profitability by sales channel** : commandes, unités, taux d'annulation, revenu, marge brute et taux de marge par canal, avec leurs variations N-1.
- Bandeau : nombre de commandes exclues faute de montant dans la base.

### Website B2C
Ventes du site grand public par **pays de livraison**.
- Cartes KPI.
- **Revenue and profitability by country** : tous les pays de livraison, triés par revenu (défilement dans le tableau). La colonne Sales %, juste après Sales, est la part du revenu de tous les pays : un filtre Pays ne la recalcule pas à 100 %. Filtre Pays sur la page.

### Website B2C Contribution
Contribution de chaque pays à l'évolution du site grand public.
- **Revenue YoY bridge by country** et **Gross Profit YoY bridge by country** : de la valeur de l'année précédente à la valeur actuelle, pays par pays.

### Website B2B
Ventes du site professionnel.
- Cartes KPI.
- **Revenue and profitability by destination country** : tous les pays, triés par revenu, avec la colonne Sales % (part du total, filtre Pays ignoré) et un filtre Pays.
- **Top 10 B2B orders by revenue** : identifiant de commande Lireka, unités, revenu, marge brute.

### Marketplaces
Ventes par place de marché (Amazon par pays, Cultura, Rakuten, Fnac).
- Cartes KPI.
- **Revenue and profitability by marketplace** : revenu, coûts dont commissions, marge brute et variations N-1.

### Top sellers
Les meilleures ventes, par canal (Website B2B, Website B2C, Marketplaces).
- **Top 10 ISBNs by ordered units** : unités et revenu par ISBN. Le revenu d'un ISBN est estimé en répartissant le montant de la commande à parts égales entre ses livres.
- **Top 10 orders** : les dix commandes au revenu le plus élevé.

### Top loss makers
Les dix commandes les plus déficitaires de chaque canal, avec le détail de leurs coûts (coût d'achat, transport amont et sortant, droits et taxes, commissions, fournitures) pour comprendre d'où vient la perte.

### Librairie Arthaud
Même lecture que General View pour la librairie de Grenoble, avec des graphiques **hebdomadaires**.

### Profit bridge
Passage de la marge brute de l'année précédente à celle de la période, poste par poste : variation du revenu, puis de chaque coût. Le total de la cascade est égal à la marge brute de la période.
- Cartes : **Gross Profit per unit**, **Product margin** ((revenu − coût d'achat) / revenu), **Outbound shipping per unit**, **Duties and taxes per unit**.

### Transport and carriers
Coûts d'expédition, tous colis confondus.
- Cartes : nombre de colis, transport sortant, droits et taxes, fournitures.
- **Outbound shipping cost by month** et **Packages and outbound cost by carrier**.
- **Packages and costs by carrier** : colis, poids, coût moyen par colis, transport, droits et taxes, fournitures, variations N-1.
- Le transporteur est déduit du numéro de suivi ; « Unknown » quand le format n'est pas reconnu.

### Loss analysis
Commandes à marge brute négative.
- Cartes : **Total losses**, **Loss-making orders**, **Share of Gross Profit** (pertes / marge brute), **Share of orders**.
- **What tips an order into loss** : pour chaque commande déficitaire, le poste de coût qui la fait basculer en perte (voir la règle dans [2-donnees-et-calculs.md](2-donnees-et-calculs.md)).
- **Gross Margin by basket size** : marge brute et taux de marge par tranche de panier (hors TVA).
- **Loss drivers by channel** : nombre de commandes déficitaires, perte totale et perte moyenne par canal et par poste.

---

## Glossaire

| Terme | Signification |
|---|---|
| COGS | Coût d'achat des livres |
| Inbound freight | Transport amont (du fournisseur jusqu'à l'entrepôt) |
| Outbound shipping | Transport sortant (de l'entrepôt jusqu'au client) |
| Duties and taxes | Droits de douane et taxes à l'import payés par Lireka |
| Marketplace fees | Commissions des places de marché |
| Shipping supplies | Fournitures d'expédition (emballages) |
| Returns and refunds | Retours et remboursements (hors marge brute) |
| Generic costs | Coûts génériques (hors marge brute) |
| PY / YoY / bps | Année précédente / variation sur un an / points de base (1 point de % = 100 bps) |
