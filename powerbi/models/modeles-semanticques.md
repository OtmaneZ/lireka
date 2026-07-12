# Modèles sémantiques Power BI — Lireka

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Document de travail technique — support à l'intégration J2–J3.

---

## Datasets

| Dataset | Workspace | Mode | Refresh | Source |
|---------|-----------|------|---------|--------|
| `Lireka - Factures Transport` | Lireka - Transport | Import | Mensuel | `factures_unifiees.csv` |
| `Lireka - Commandes` | Lireka - Profitabilité | Import | Hebdomadaire | `commandes_clean.csv` |
| `Lireka - Profitabilité` | Lireka - Profitabilité | Import | Mensuel | Modèle unifié (jointure) |
| `Lireka - Formation` | Lireka - Formation | Import | Statique | Échantillon anonymisé |

---

## Modèle sémantique — Profitabilité (star schema)

### Tables

```
fact_commandes          ← Commandes enrichies (coût réel, marge)
fact_factures_transport ← Factures transporteurs unifiées
dim_date                ← Calendrier
dim_pays                ← Pays de livraison
dim_transporteur        ← 6 transporteurs
dim_type_commande       ← Types B2C, B2B, etc.
```

### Relations

| De | Vers | Colonne | Cardinalité |
|----|------|---------|-------------|
| fact_commandes | dim_date | date_commande → date | N:1 |
| fact_commandes | dim_pays | pays_livraison → code_pays | N:1 |
| fact_commandes | dim_transporteur | transporteur → transporteur | N:1 |
| fact_commandes | dim_type_commande | type_commande → type_commande | N:1 |
| fact_factures_transport | dim_date | date_facture → date | N:1 |
| fact_factures_transport | dim_transporteur | transporteur → transporteur | N:1 |
| fact_commandes | fact_factures_transport | numero_suivi → numero_suivi | N:1 (inactive si besoin) |

---

## Mesures DAX principales

Voir le fichier complet : [`mesures-dax.md`](mesures-dax.md)

### Mesures clés

| Mesure | Description |
|--------|-------------|
| `Coût Transport Réel` | Somme des coûts issus des factures |
| `Coût Transport Estimé` | Somme des estimations backend |
| `Écart Coût Transport` | Réel − Estimé |
| `Marge Brute` | CA HT − Coût achat − Coût transport réel |
| `Taux Marge Brute` | Marge / CA HT |
| `Taux Matching` | % commandes avec coût réel |
| `Nb Commandes` | Nombre de commandes |
| `Coût Moyen Colis` | Coût réel / Nb commandes |

---

## Rapports

### Transporteurs (x6)

| Rapport | Pages | Statut |
|---------|-------|--------|
| Dashboard DHL | 3 | ✅ Existant |
| Dashboard FedEx | 3 | ✅ Existant |
| Dashboard UPS | 3 | ✅ Existant |
| Dashboard La Poste | 3 | ⬜ À créer |
| Dashboard Colis Privé | 3 | ⬜ À créer |
| Dashboard Chronopost | 3 | ⬜ À créer |

**Structure type par dashboard** :
1. **Vue d'ensemble** — KPIs + graphique mensuel
2. **Par pays** — Carte + tableau
3. **Détail factures** — Table filtrable

### Profitabilité

| Rapport | Pages | Statut |
|---------|-------|--------|
| Marge par pays | 2 | ⬜ À créer |
| Marge par type commande | 2 | ⬜ À créer |
| Écarts coûts transport | 2 | ⬜ À créer |
| Synthèse direction | 1 | ⬜ À créer |

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

## Connexion Claude AI

| Élément | Détail |
|---------|--------|
| Statut | ✅ Connecté (existant) |
| Dataset exposé | *À documenter lors de l'audit* |
| Recommandation | Exposer le dataset Profitabilité unifié |

---

*Documentation à compléter au fur et à mesure de la construction.*
