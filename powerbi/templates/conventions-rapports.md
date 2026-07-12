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
- `Lireka - Dashboard DHL`
- `Lireka - Marge par Pays`
- `Lireka - Synthèse Direction`

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

## Structure d'un dashboard transporteur

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

## Structure d'un dashboard profitabilité

### Page 1 — Marge par pays

| Zone | Visuel |
|------|--------|
| KPIs | Marge Brute, Taux Marge, CA Total, Nb Commandes |
| Carte | Marge par pays (code couleur) |
| Barres | Top/Bottom 10 pays par marge |
| Slicers | Période, Transporteur, Type commande |

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
