# 1. Guide du rapport

Ce guide présente les 9 pages du rapport **Lireka_Profitabilite** et la signification de chaque indicateur. Les règles de calcul détaillées sont dans le document 2, « Données et calculs ».

Le rapport est en anglais : les termes affichés sont repris tels quels ci-dessous.

État au 06/11/2026.

---

## Éléments communs

| Élément | Où | Rôle |
|---|---|---|
| **Filtre « Period »** | volet Filtres, toutes les pages | Période analysée. Par défaut : les 12 derniers mois. Modifiable, par exemple « année civile précédente ». |
| **Slicer « Date »** | rail de gauche, toutes les pages | Affine la période à l'intérieur du filtre « Period ». Synchronisé entre les pages. |
| **Carte « Data through »** | rail de gauche, toutes les pages | Date de la dernière commande avec montant dans la base. Si les données ont plus d'un jour, leur âge est affiché. |
| **Slicer « Language »** | pages de ventes | Langue du livre. Quand il est utilisé, les montants de chaque commande sont répartis à parts égales entre ses livres, et un bandeau le signale. |
| **Slicer « Channel »** | General View, Profit bridge | Website B2C, Website B2B, Marketplaces, Librairie Arthaud. |
| **Slicer des pays** | Website B2C, Website B2B | Pays de livraison. |
| **Granularity (Month / Week)** | General View, Librairie Arthaud | Pas de temps des graphiques. Les semaines sont notées « Wk ». |

### Les quatre cartes KPI

Elles figurent en haut des pages de synthèse.

| Carte | Définition |
|---|---|
| **Ordered units** | Nombre de livres commandés (une unité par article). |
| **Revenue** | Chiffre d'affaires **hors TVA**, frais de port inclus, hors commandes annulées. |
| **Gross Profit** | Marge brute : Revenue moins coût d'achat, transport amont, transport sortant, droits et taxes, commissions marketplace, fournitures d'expédition, retours et remboursements. |
| **Gross Margin** | Gross Profit / Revenue. |

Sous chaque carte figurent la valeur de l'année précédente (**PY**) et la variation (**YoY**), en % ou, pour la marge, en points de base (**bps**). La comparaison est laissée vide si plus de 5 % des commandes de la période précédente n'ont pas de montant en base.

### Couleurs

- Les valeurs négatives sont affichées en rouge.
- Dans les tableaux de résultat, le coût d'achat (COGS) est en rouge et la marge produit (Product profit) en vert. Sur la page Marketplaces, tous les coûts sont en rouge.
- Dans les graphiques empilés, les Marketplaces sont placées en bas des barres.

---

## Les pages

### General View
Synthèse des trois canaux en ligne : Website B2C, Website B2B et Marketplaces. Librairie Arthaud a sa propre page.
- Cartes KPI.
- **Revenue by sales channel** et **Gross Profit by sales channel** : évolution par canal, avec l'année précédente en courbe.
- **Units, revenue and profitability by sales channel** : commandes, unités, taux d'annulation, revenu, marge brute et taux de marge par canal, avec leurs variations sur un an.
- Bandeau : nombre de commandes exclues faute de montant dans la base.

### Website B2C
Ventes du site grand public par **pays de livraison**.
- Cartes KPI.
- **Revenue and profitability by country** : tous les pays de livraison, avec leur drapeau, triés par revenu. Le tableau défile.
- La colonne **Sales %**, juste après Sales, donne la part du revenu de tous les pays. Le slicer des pays ne la recalcule pas à 100 %.

### Website B2C Contribution
Contribution de chaque pays à l'évolution du site grand public.
- **Revenue YoY bridge by country** et **Gross Profit YoY bridge by country** : passage de la valeur de l'année précédente à la valeur actuelle, pays par pays.

### Website B2B
Ventes du site professionnel.
- Cartes KPI.
- **Revenue and profitability by destination country** : tous les pays, triés par revenu, avec la colonne Sales % et le slicer des pays.
- **Top 10 B2B orders by revenue** : identifiant de commande, client (Customer), unités, revenu, marge brute.

### Marketplaces
Ventes par place de marché : Amazon par pays, Cultura, Rakuten, Fnac.
- Cartes KPI.
- **Revenue and profitability by marketplace** : revenu, coûts dont commissions, marge brute et variations sur un an.

### Top sellers
Les meilleures ventes de chaque canal : Website B2B, Website B2C, Marketplaces.
- **Top 10 ISBNs by ordered units** : ISBN, titre du livre, unités et revenu. Le revenu d'un livre est estimé en répartissant le montant de la commande à parts égales entre ses livres.
- **Top 10 orders** : les dix commandes au revenu le plus élevé. Pour le Website B2B, le nom du client est affiché.

### Top loss makers
Les dix commandes les plus déficitaires de chaque canal, avec le détail de leurs coûts (coût d'achat, transport amont et sortant, droits et taxes, commissions, fournitures, retours) pour comprendre d'où vient la perte. Pour le Website B2B, le nom du client est affiché.

### Librairie Arthaud
Même lecture que General View, pour la librairie de Grenoble.

### Profit bridge
Passage de la marge brute de l'année précédente à celle de la période, poste par poste : variation du revenu, puis de chaque coût, retours compris. Le total de la cascade est égal à la marge brute de la période.
- Cartes : **Gross Profit per unit**, **Product margin** (revenu moins coût d'achat, rapporté au revenu), **Outbound shipping per unit**, **Duties and taxes per unit**, avec les valeurs de l'année précédente.

---

## Glossaire

| Terme | Signification |
|---|---|
| COGS | Coût d'achat des livres |
| Product profit | Revenu moins coût d'achat |
| Inbound freight | Transport amont, du fournisseur jusqu'à l'entrepôt |
| Outbound shipping | Transport sortant, de l'entrepôt jusqu'au client |
| Duties and taxes | Droits de douane et taxes à l'import payés par Lireka |
| Marketplace fees | Commissions des places de marché |
| Shipping supplies | Fournitures d'expédition (emballages) |
| Returns and refunds | Retours et remboursements, déduits de la marge brute |
| PY | Année précédente |
| YoY | Variation sur un an |
| bps | Points de base : 1 point de % = 100 bps |
