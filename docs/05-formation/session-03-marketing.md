# Session 3 — Cas pratique marketing

> **⚠️ Hors périmètre devis** — Support optionnel uniquement. Le forfait 4 jours prévoit une session de formation unique (voir `programme-formation.md`).

> **Durée** : 2 heures  
> **Formateur** : Otmane Boulahia — ZineInsights  
> **Prérequis** : Sessions 1 & 2

---

## 1. Données utiles pour le marketing

Le dataset commandes Lireka contient des informations précieuses pour le marketing :

| Donnée | Usage marketing |
|--------|----------------|
| `pays_livraison` | Ciblage géographique, expansion marchés |
| `ca_ht` par pays | Priorisation des marchés rentables |
| `type_commande` | Segmentation client B2C / B2B |
| `nombre_articles` | Panier moyen, comportement d'achat |
| `date_commande` | Saisonnalité, tendances |
| `transporteur` | Corrélation service / satisfaction |
| `marge_brute` par segment | ROI par canal / marché |

---

## 2. Cas pratique guidé — "Performance par marché" *(vision future — hors périmètre devis)*

### Objectif

Exemple pédagogique : créer un **dashboard marketing** montrant la performance commerciale par pays sur 6 mois. Ce livrable **n'est pas** inclus dans la mission 4 jours (devis : dashboards supplémentaires marketing exclus).

### Étapes guidées (30 min)

1. **Nouvelle page** : "Performance marchés"
2. **Slicer Timeline** : `date_commande` — derniers 6 mois
3. **Carte géographique** : `pays_livraison` + `CA Total` (mesure)
4. **Graphique courbe** : évolution mensuelle du CA
5. **Graphique barres** : Top 10 pays par nombre de commandes
6. **KPI** : Panier moyen = `CA Total / Nb Commandes`
7. **Tableau** : Détail par pays (CA, nb commandes, panier moyen, marge)

### Résultat attendu

```
┌─────────────────────────────────────────────────┐
│  Performance marchés          [Timeline 6 mois] │
├─────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ CA Total │  │ Commandes│  │ Panier   │      │
│  │ 1,2M€    │  │ 45 230   │  │ moy. 26€ │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│  ┌──────────────────┐ ┌───────────────────┐    │
│  │ Carte géographique│ │ Courbe CA/mois    │    │
│  └──────────────────┘ └───────────────────┘    │
│  ┌─────────────────────────────────────────┐   │
│  │ Top 10 pays par commandes               │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 3. Cas pratique autonome (40 min)

### Consignes

Chaque participant crée **son propre mini-dashboard** (1 page, 4-6 visuels) sur un sujet de son choix :

| Idée de sujet | Visuels suggérés |
|--------------|-----------------|
| Saisonnalité des ventes | Courbe mensuelle, heatmap jour/semaine |
| Performance B2C vs B2B | Barres comparatives, KPIs côte à côte |
| Analyse panier moyen | Histogramme nb articles, tableau par tranche |
| Coûts transport par marché | Carte, barres, KPI écart estimé/réel |
| Top transporteurs par volume | Graphique donut, tableau croisé |

### Contraintes

- Minimum **4 visuels**
- Au moins **1 slicer**
- Utiliser des **mesures** (pas de calculs manuels)
- Publier sur le workspace **Lireka - Formation**

---

## 4. Présentations (10 min)

Chaque participant présente en **3 minutes** :
1. Le sujet choisi et pourquoi
2. Les visuels créés (démo live)
3. Une insight découverte dans les données

---

## 5. Quiz d'évaluation (10 min)

→ Voir `docs/05-formation/quiz-evaluation.md`

---

## 6. Clôture & prochaines étapes

### Ressources pour aller plus loin

| Ressource | Lien |
|-----------|------|
| Documentation Microsoft Power BI | [learn.microsoft.com/power-bi](https://learn.microsoft.com/power-bi/) |
| DAX Guide | [dax.guide](https://dax.guide) |
| Communauté Power BI France | Forums, LinkedIn |
| Support ZineInsights | Otmane Boulahia — [email] |

### Pour devenir autonome

1. **Pratiquer** sur le workspace Formation
2. **Explorer** les dashboards existants
3. **Poser des questions** au référent data Lireka
4. **Itérer** : un visuel par semaine

---

*Support Session 3 — ZineInsights — Juillet 2026*
