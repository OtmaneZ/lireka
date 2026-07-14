# Modèles sémantiques Power BI — Lireka

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Document de travail technique — support à l'intégration J2–J3.

---

## Datasets

| Dataset | Workspace | Mode | Refresh | Source |
|---------|-----------|------|---------|--------|
| `Lireka - Profitabilité` | Lireka - Profitabilité | Import | Mensuel | Modèle unifié (`Lireka_Profitabilite.pbip`) |
| `Lireka - Formation` | Lireka - Formation | Import | Statique | Échantillon anonymisé |

---

## Modèle sémantique — Profitabilité (star schema)

### Tables

```
fact_commandes          ← Commandes (grain : 1 ligne / commande)
fact_transport          ← Colis / coûts transport (grain : 1 ligne / colis)
fact_factures_transport ← Factures Colissimo + Chronopost unifiées
fact_lignes             ← Lignes de commande (grain : 1 ligne / article)
dim_date                ← Calendrier
dim_pays                ← Pays de livraison (code_pays, nom_pays, zone_geo, continent)
dim_transporteur        ← 8 transporteurs canoniques
dim_type_commande       ← Types / canaux de vente (source backend)
_Mesures                ← Mesures DAX (table technique, sans données)
```

**Référentiel transporteurs (`dim_transporteur`)** — 8 entrées :

| Transporteur | Statut |
|--------------|--------|
| DHL | Existant (référence) |
| FedEx | Existant (référence) |
| UPS | Existant (référence) |
| La Poste | Nouveau (intégré — Colissimo) |
| Colis Privé | Nouveau (intégré) |
| Chronopost | Nouveau (intégré) |
| Postes Canada | Autre |
| INCONNU | Non identifié |

### Colonnes clés — `dim_pays`

| Colonne | Description |
|---------|-------------|
| `code_pays` | Clé ISO alpha-2 (ex. `FR`, `CA`) ; `??` = « Pays non attribué » |
| `nom_pays` | Libellé affiché |
| `zone_geo` | Zone géographique (ex. « Europe de l'Ouest ») |
| `continent` | Continent (ex. « Europe ») |

Jointure depuis `fact_commandes[code_pays]` (pas `pays_livraison` — colonne absente du modèle).

### Relations

| Relation | De | Vers | Colonnes | Cardinalité |
|----------|----|------|----------|-------------|
| `rel_commandes_date` | fact_commandes | dim_date | date_commande → date | N:1 |
| `rel_commandes_pays` | fact_commandes | dim_pays | **code_pays** → code_pays | N:1 |
| `rel_commandes_type` | fact_commandes | dim_type_commande | type_commande → type_commande | N:1 |
| `rel_transport_commandes` | fact_transport | fact_commandes | order_id → id_commande | N:1 |
| `rel_lignes_commandes` | fact_lignes | fact_commandes | order_id → id_commande | N:1 |
| `rel_transport_transporteur` | fact_transport | dim_transporteur | transporteur → transporteur | N:1 |
| `rel_factures_transporteur` | fact_factures_transport | dim_transporteur | transporteur → transporteur | N:1 |
| `rel_factures_date` | fact_factures_transport | dim_date | date_facture → date | N:1 |
| `rel_factures_colis` | fact_factures_transport | fact_transport | **id_package** → id_package | N:1 |

**Note** : le rapprochement facture ↔ colis passe par `rel_factures_colis` sur `id_package` (résolution par proximité de date dans Power Query). Il n'existe **pas** de relation directe `fact_commandes` ↔ `fact_factures_transport` sur `numero_suivi`.

### Colonne `source_cout` (`fact_transport`)

| Valeur | Signification |
|--------|---------------|
| `reel` | Coût issu d'une facture Colissimo/Chronopost rapprochée |
| `estime` | Coût backend (`shipping_cost_eur`) sans facture transporteur |
| `non_disponible` | Ni facture ni coût backend renseigné |

---

## Mesures DAX principales

Voir le fichier complet : [`mesures-dax.md`](mesures-dax.md)

### Mesures clés

| Mesure | Description |
|--------|-------------|
| `Coût Transport Réel` | `SUM(fact_transport[cout_transport])` |
| `Coût Transport Estimé` | `SUM(fact_commandes[cout_transport_estime])` |
| `Écart Coût Transport` | Réel − Estimé |
| `Taux Écart Coût` | Écart / Estimé |
| `Marge Brute (prov.)` | **Provisoire** — en attente validation Marc |
| `Taux Matching` | % commandes avec au moins un colis `source_cout = "reel"` |
| `Nb Commandes` | `COUNTROWS(fact_commandes)` |
| `Nb Colis` | `COUNTROWS(fact_transport)` |
| `Coût Moyen Colis` | Coût réel / Nb colis |

---

## Rapports

### Profitabilité — livrable contractuel J3 (L04)

| Rapport | Statut | Périmètre devis |
|---------|--------|-----------------|
| Dashboard profitabilité | 🔄 En cours | **1 rapport** — marge brute par **pays** et par **type de commande** (2 axes d'analyse) |

---

## Conventions de design

| Élément | Convention |
|---------|-----------|
| Police | Segoe UI (défaut Power BI) |
| Couleur principale | #1B3A5C (bleu Lireka — à confirmer) |
| Format monétaire | `#,##0.00 €` |
| Format pourcentage | `0.0%` |
| Langue | Français |

---

*Dernière mise à jour : 14/07/2026 — aligné sur `Lireka_Profitabilite.SemanticModel`.*
