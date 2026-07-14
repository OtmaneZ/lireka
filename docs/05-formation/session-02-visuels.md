# Session 2 — Création de visuels & filtres

> **⚠️ Hors périmètre devis** — Support optionnel uniquement. Le forfait 4 jours prévoit une session de formation unique (voir `programme-formation.md`).

> **Durée** : 2 heures  
> **Formateur** : Otmane Boulahia — ZineInsights  
> **Prérequis** : Session 1

---

## 1. Power BI Desktop

### Installation

1. Télécharger depuis [powerbi.microsoft.com/desktop](https://powerbi.microsoft.com/desktop/)
2. Installer (Windows uniquement — Mac : utiliser Power BI Service)
3. Se connecter avec le compte Lireka

### Connexion au dataset

1. Ouvrir Power BI Desktop
2. **Obtenir des données** → **Power BI datasets**
3. Sélectionner le workspace **Lireka - Formation** (sandbox)
4. Choisir le dataset de test

> Le workspace "Formation" contient un dataset anonymisé pour s'exercer sans risque.

---

## 2. Créer un visuel — Pas à pas

### Graphique en barres — Top pays par coût transport

1. Dans le volet **Visualisations**, cliquer sur le graphique **Barres empilées**
2. Glisser `pays_livraison` dans **Axe Y**
3. Glisser `Coût Transport Réel` (mesure) dans **Axe X**
4. Trier par coût décroissant (clic sur `...` → Trier)
5. Limiter à Top 10 : Filtre sur le visuel → Top N → 10

### Carte KPI

1. Cliquer sur le visuel **Carte**
2. Glisser `Marge Brute` (mesure) dans **Champs**
3. Ajouter `Taux Marge Brute` comme **Étiquette de détails**

### Tableau

1. Cliquer sur le visuel **Table**
2. Ajouter les colonnes : `id_commande`, `date_commande`, `pays_livraison`, `transporteur`, `ca_ht`, `marge_brute`
3. Trier par `marge_brute` décroissant

---

## 3. Filtres & interactions

### Types de filtres

| Type | Portée | Création |
|------|--------|----------|
| **Slicer** | Page entière | Visuel Slicer + champ |
| **Filtre visuel** | Un seul visuel | Volet Filtres → Filtres sur ce visuel |
| **Filtre page** | Toute la page | Volet Filtres → Filtres sur cette page |
| **Filtre rapport** | Tout le rapport | Volet Filtres → Filtres sur toutes les pages |

### Slicers recommandés pour Lireka

| Slicer | Champ | Type |
|--------|-------|------|
| Période | `dim_date[mois]` | Liste / Timeline |
| Pays | `dim_pays[nom_pays]` | Liste déroulante |
| Transporteur | `dim_transporteur[transporteur]` | Boutons |
| Type commande | `dim_type_commande[libelle]` | Liste |

### Interactions entre visuels

1. Sélectionner un visuel
2. Menu **Format** → **Modifier les interactions**
3. Choisir pour chaque autre visuel : **Filtrer** / **Mettre en surbrillance** / **Aucun**

---

## 4. Exercice pratique

### Énoncé

> Créez une page avec :
> 1. Un **KPI** affichant le coût transport total
> 2. Un **graphique en barres** : Top 10 pays par coût transport
> 3. Un **Slicer** pour filtrer par transporteur
> 4. Un **tableau** listant les 20 commandes avec la plus grande marge brute

### Critères de réussite

- [ ] Les 4 visuels sont présents
- [ ] Le slicer transporteur filtre tous les visuels
- [ ] Le graphique est trié par coût décroissant
- [ ] Le tableau affiche 20 lignes maximum

---

## 5. Publier un rapport

1. **Accueil** → **Publier**
2. Sélectionner le workspace **Lireka - Formation**
3. Attendre la confirmation
4. Ouvrir dans Power BI Service pour vérifier

---

## 6. Bonnes pratiques

| Pratique | Pourquoi |
|----------|----------|
| Nommer clairement les pages et visuels | Facilite la navigation |
| Utiliser les mesures DAX (pas les colonnes) pour les calculs | Cohérence et performance |
| Limiter les visuels à 6-8 par page | Lisibilité |
| Tester sur différents filtres | Vérifier la cohérence |
| Publier sur le workspace Formation d'abord | Éviter les erreurs en production |

---

*Support Session 2 — ZineInsights — Juillet 2026*
