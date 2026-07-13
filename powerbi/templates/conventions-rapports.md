# Conventions Power BI — Lireka

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Règles de nommage et bonnes pratiques — document de travail J2–J3.

---

## Nommage

### Rapports

```
Lireka - {Sujet}
```

Exemples :
- `Lireka - Dashboard DHL` *(existant — référence)*
- `Lireka - Profitabilité` *(livrable contractuel J3)*

> **Hors périmètre devis** (ne pas nommer comme livrable de la mission) : synthèse direction, écarts transport, dashboard marketing, etc.

### Pages

```
{N°} - {Titre descriptif}
```

Exemples :
- `1 - Vue d'ensemble`
- `2 - Par pays`
- `3 - Détail factures`

### Mesures DAX

- Français, PascalCase avec espaces
- Pas de préfixe sauf si ambiguïté
- Exemples : `Marge Brute`, `Coût Transport Réel`, `Taux Matching`

### Colonnes

- snake_case dans les tables de faits
- Exemples : `numero_suivi`, `cout_transport_reel`, `ca_ht`

---

## Structure d'un dashboard transporteur *(référence — existants DHL / FedEx / UPS)*

> La création de dashboards transporteurs dédiés pour La Poste, Colis Privé ou Chronopost est **hors périmètre devis**. Cette section décrit le modèle des rapports existants, utile comme référence de design.

### Page 1 — Vue d'ensemble

| Zone | Visuel | Mesure / Dimension |
|------|--------|-------------------|
| Haut gauche | Carte KPI | Coût Transport Réel |
| Haut centre | Carte KPI | Nb Colis Facturés |
| Haut droite | Carte KPI | Coût Moyen Colis |
| Milieu | Graphique courbes | Coût par mois |
| Bas | Slicers | Date, Pays |

### Page 2 — Par pays

| Zone | Visuel | Mesure / Dimension |
|------|--------|-------------------|
| Gauche | Carte géographique | Coût par pays |
| Droite | Barres horizontales | Top 10 pays |
| Bas | Tableau | Détail par pays |

### Page 3 — Détail factures

| Zone | Visuel | Mesure / Dimension |
|------|--------|-------------------|
| Pleine page | Table | Toutes les colonnes factures |
| Haut | Slicers | Date, Service |

---

## Dashboard profitabilité *(livrable contractuel J3)*

**Périmètre devis** : **un seul** rapport Power BI couvrant la marge brute selon **deux axes d'analyse** :
- par **pays**
- par **type de commande**

Le devis ne fixe **ni le nombre de pages/onglets, ni la disposition des visuels**. La structure (pages, onglets, répartition des visuels) est **au choix du prestataire**, sous réserve que les deux axes soient exploitables par l'utilisateur.

**Mesures et filtres utiles** (non exhaustif) : Marge Brute, Taux Marge, CA Total, Nb Commandes ; slicers Période, Transporteur, Type commande, Pays.

---

## Checklist avant publication

- [ ] Tous les visuels ont un titre
- [ ] Format monétaire en € partout
- [ ] Filtres par défaut : mois en cours ou dernier mois complet
- [ ] Pas de données de test visibles
- [ ] Tooltips configurés sur les KPIs
- [ ] Testé sur 3+ combinaisons de filtres
- [ ] Publié sur le bon workspace
- [ ] Refresh planifié configuré

---

*Conventions ZineInsights — Juillet 2026*
