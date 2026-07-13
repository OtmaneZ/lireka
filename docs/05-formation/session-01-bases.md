# Session 1 — Bases Power BI & navigation

> **Référence** : [`programme-formation.md`](programme-formation.md) — session unique J4 (1h30–2h, adaptée depuis ce support)  
> **Formateur** : Otmane Boulahia — ZineInsights

---

## 1. Qu'est-ce que Power BI ?

Power BI est l'outil de Microsoft pour visualiser et analyser des données. Lireka l'utilise pour :

- Suivre les **coûts de transport** par transporteur (factures réelles)
- Calculer la **marge brute réelle** par pays et type de commande
- Piloter l'activité avec des **tableaux de bord interactifs**

### Deux interfaces

| Interface | Usage | Accès |
|-----------|-------|-------|
| **Power BI Service** (web) | Consulter les dashboards, partager | navigateur → app.powerbi.com |
| **Power BI Desktop** (logiciel) | Créer/modifier rapports et modèles | Installation locale |

> Pour cette session, nous utilisons **Power BI Service** (le navigateur).

---

## 2. Naviguer dans Power BI Service

### Se connecter

1. Ouvrir [app.powerbi.com](https://app.powerbi.com)
2. Se connecter avec votre compte Lireka
3. Cliquer sur **Workspaces** → **Lireka - Transport** ou **Lireka - Profitabilité**

### L'interface d'un rapport

```
┌─────────────────────────────────────────────────┐
│  [Logo] Lireka - Dashboard DHL        [Filtres] │
├─────────────────────────────────────────────────┤
│  Page 1 │ Page 2 │ Page 3                       │
├─────────┴────────┴──────────────────────────────┤
│                                                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│   │ KPI      │  │ KPI      │  │ KPI      │    │
│   │ Coût     │  │ Nb colis │  │ Coût     │    │
│   │ total    │  │          │  │ moyen    │    │
│   └──────────┘  └──────────┘  └──────────┘    │
│                                                 │
│   ┌─────────────────────────────────────────┐   │
│   │  Graphique évolution mensuelle          │   │
│   └─────────────────────────────────────────┘   │
│                                                 │
│   ┌─────────────────────────────────────────┐   │
│   │  Tableau détail factures                │   │
│   └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Les éléments interactifs

| Élément | Action | Effet |
|---------|--------|-------|
| **Slicer (filtre)** | Cliquer sur une valeur | Filtre tout le rapport |
| **Graphique** | Cliquer sur une barre/segment | Filtre les autres visuels (cross-filter) |
| **Ctrl + clic** | Sélection multiple | Filtre sur plusieurs valeurs |
| **Bouton Reset** | En haut à droite | Remet tous les filtres à zéro |
| **Drill-down** | Flèche sur un axe | Descendre au niveau détail (mois → jour) |

---

## 3. Dashboards transporteurs *(existants — référence)*

> Les dashboards DHL, FedEx et UPS existent déjà. L'intégration La Poste / Colis Privé / Chronopost porte sur les **données** dans le modèle — **pas** la création de dashboards transporteurs dédiés *(hors périmètre devis)*.

### Structure commune (DHL, FedEx, UPS)

Chaque dashboard transporteur contient :

| Page | Contenu |
|------|---------|
| **Vue d'ensemble** | KPIs : coût total, nb colis, coût moyen/colis |
| **Évolution** | Graphique mensuel des coûts |
| **Détail** | Tableau des factures avec numéro de suivi, montant, poids |

### Exercice guidé — Dashboard DHL

1. Ouvrir le dashboard DHL
2. Sélectionner le mois de **juin 2026** dans le filtre date
3. Noter le **coût total** affiché
4. Cliquer sur le pays **Allemagne** dans le graphique
5. Observer comment les KPIs se mettent à jour
6. Remettre les filtres à zéro (Reset)

---

## 4. Dashboard profitabilité *(livrable contractuel J3)*

**Un seul rapport** couvre la marge brute selon **deux axes d'analyse** : par **pays** et par **type de commande**. Le nombre de pages ou la disposition des visuels n'est pas fixé par le devis.

### KPIs principaux

| KPI | Formule | Interprétation |
|-----|---------|----------------|
| **Marge brute** | CA HT − Coût achat − Coût transport réel | Ce que Lireka gagne réellement |
| **Taux de marge** | Marge brute / CA HT | Rentabilité en % |
| **Écart coût transport** | Coût réel − Coût estimé | Sur/sous-estimation backend |
| **Taux de matching** | % commandes liées à une facture | Qualité de la liaison suivi |

### Filtres disponibles

- **Période** : mois, trimestre, année
- **Pays** : par pays de livraison
- **Type de commande** : B2C, B2B, etc.
- **Transporteur** : DHL, FedEx, UPS, La Poste, etc.

### Exercice guidé — Axes pays et type de commande

1. Ouvrir le dashboard Profitabilité
2. Filtrer sur le **T2 2026**
3. Identifier le **pays le plus rentable** (marge brute la plus élevée)
4. Identifier le **pays le moins rentable**
5. Comparer le coût transport **estimé** vs **réel** pour ce pays
6. Changer l'angle d'analyse vers le **type de commande** (B2C, B2B, etc.) et comparer les marges

---

## 5. Exercice pratique

### Énoncé

> Quelle est la **marge brute totale** de Lireka en **juin 2026** pour les commandes livrées en **France** via **DHL** ?

### Étapes

1. Ouvrir le dashboard Profitabilité
2. Filtrer : Date = Juin 2026
3. Filtrer : Pays = France
4. Filtrer : Transporteur = DHL
5. Lire le KPI "Marge brute"
6. Noter le résultat : __________ €

---

## 6. Aide & ressources

| Besoin | Contact / Ressource |
|--------|-------------------|
| Question sur un chiffre | Référent finance Lireka |
| Problème d'accès | Référent technique Lireka |
| Formation complémentaire | Otmane Boulahia — ZineInsights |
| Documentation | `docs/05-formation/` dans le dépôt projet |

---

*Support Session 1 — ZineInsights — Juillet 2026*
