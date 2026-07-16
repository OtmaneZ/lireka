# Modèles sémantiques Power BI — Lireka

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Document de travail technique — aligné sur `Lireka_Profitabilite` (14/07/2026).

---

## Datasets

| Dataset | Workspace | Mode | Refresh | Source |
|---------|-----------|------|---------|--------|
| `Lireka - Profitabilité` | Lireka - Profitabilité | Import | Hebdomadaire / mensuel | Entrepôt SharePoint `Power_BI_Datawarehouse` |
| `Lireka - Formation` | Lireka - Formation | Import | Statique | Échantillon anonymisé |

---

## Modèle sémantique — Profitabilité (star schema)

### Tables

```
fact_commandes            ← Commandes (customer_order.csv)
fact_transport            ← Colis / coûts transport (package.csv)
fact_factures_transport   ← Factures Colissimo + Chronopost (récaps CSV)
fact_lignes               ← Lignes articles (customer_order_item_group.csv)
dim_date                  ← Calendrier 2022–2026
dim_pays                  ← Pays de livraison (code ISO + zone_geo + continent)
dim_transporteur          ← 8 transporteurs canoniques
dim_type_commande         ← Canaux de vente (source backend)
_Mesures                  ← Mesures DAX (table technique)
```

### Relations

| De | Vers | Colonne | Cardinalité |
|----|------|---------|-------------|
| fact_transport | fact_commandes | order_id → id_commande | N:1 |
| fact_lignes | fact_commandes | order_id → id_commande | N:1 |
| fact_commandes | dim_date | date_commande → date | N:1 |
| fact_commandes | dim_pays | **code_pays** → code_pays | N:1 |
| fact_commandes | dim_type_commande | type_commande → type_commande | N:1 |
| fact_transport | dim_transporteur | transporteur → transporteur | N:1 |
| fact_factures_transport | dim_transporteur | transporteur → transporteur | N:1 |
| fact_factures_transport | dim_date | date_facture → date | N:1 |
| fact_factures_transport | fact_transport | id_package → id_package | N:1 (clé résolue par date) |

**Absent du modèle** : pas de relation directe `fact_commandes` → `dim_transporteur` (le transporteur est au grain colis, table `fact_transport`).

### dim_pays — enrichissement géographique

| Colonne | Description |
|---------|-------------|
| `code_pays` | Code ISO 3166-1 alpha-2 issu de `destination_country` ; `"??"` si absent |
| `nom_pays` | Libellé pays (table de correspondance) |
| `zone_geo` | Zone commerciale (ex. Europe de l'Ouest, DOM-TOM, Amérique du Nord) |
| `continent` | Continent ou regroupement (Europe, Amérique, Afrique, Non attribué, …) |

### dim_transporteur — 8 transporteurs

| Transporteur | Statut intégration |
|--------------|-------------------|
| La Poste | Nouveau (intégré) |
| Colis Privé | Nouveau (intégré) |
| Chronopost | Nouveau (intégré) |
| DHL | Existant (référence) |
| FedEx | Existant (référence) |
| UPS | Existant (référence) |
| Postes Canada | Autre (backend uniquement, pas de CSV facture) |
| INCONNU | Non identifié |

---

## Mesures DAX principales

Voir le fichier complet : [`mesures-dax.md`](mesures-dax.md)

### Mesures clés

| Mesure | Description |
|--------|-------------|
| `Coût Transport Réel` | Somme `fact_transport[cout_transport]` (backend colis) |
| `Coût Transport Estimé` | Somme `fact_commandes[cout_transport_estime]` |
| `Écart Coût Transport` | Réel − Estimé |
| `Marge Brute (prov.)` | CA HT − Coût achat − Coût transport réel *(en attente validation Marc)* |
| `Taux Marge Brute (prov.)` | Marge provisoire / CA HT |
| `Taux Matching` | % commandes avec au moins un colis `source_cout = "reel"` |
| `Nb Commandes` | Nombre de commandes |
| `Nb Colis` | Nombre de colis |
| `Coût Moyen Colis` | Coût réel / Nb colis |

### Colonne calculée fact_transport

| Colonne | Valeurs | Règle |
|---------|---------|-------|
| `source_cout` | `reel` / `estime` / `non_disponible` | Facture rapprochée / coût backend seul / ni l'un ni l'autre |

---

## Rapports

### Profitabilité — livrable contractuel L04

| Rapport | Statut | Périmètre |
|---------|--------|-----------|
| `Lireka_Profitabilite` | 🟡 En cours | Volumes transport, coûts, pays, type commande ; marge en attente validation |

---

## Conventions de design

| Élément | Convention |
|---------|-----------|
| Police | Segoe UI (défaut Power BI) |
| Couleur principale | #1B3A5C (bleu Lireka — à confirmer) |
| Couleur positive | #28A745 (vert) |
| Couleur négative | #DC3545 (rouge) |
| Format monétaire | `#,##0.00 €` |
| Format pourcentage | `0.0%` |
| Langue | Français |

---

*Documentation alignée sur le modèle TMDL `Lireka_Profitabilite.SemanticModel`.*
