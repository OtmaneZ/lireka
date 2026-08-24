# Recette chiffrée — KPI Revenu / Marge Brute / Taux

Projet Lireka Profitabilité · Phase 3 · Établi le 2026-08-04
Objectif : prouver par le chiffre, avant le prochain point client, que le stack KPI publié reproduit la réalité économique que Marc connaît de son activité.

---

## 1. Pourquoi cette recette peut être exécutée sans arbitrage préalable

Marc a donné en call de démarrage les valeurs de référence de son propre P&L 2025. Elles constituent un jeu de test client, plus solide que n'importe quel contrôle interne : si le dashboard les reproduit, il est juste ; s'il ne les reproduit pas, l'écart est chiffré et devient l'ordre du jour du call, pas un débat d'appréciation.

| Référence | Valeur déclarée | Source |
|---|---|---|
| Chiffre d'affaires 2025 | 8,9 M€ | Résumé call, tldv 23:22 |
| dont ventes site direct | 5,6 M€ | Résumé call, tldv 23:22 |
| Taux de marge brute global | ≈ 17 % | Résumé call, tldv 55:48 |
| Taux de marge brute site direct | ≈ 20 % | Résumé call, tldv 59:40 |
| Taux de marge brute marketplace | ≈ 10 % | Résumé call, tldv 59:40 |

**Contrôle de cohérence interne des cibles.** Site direct : 5,6 M€ × 20 % = 1,12 M€ de marge. Cible globale : 8,9 M€ × 17 % = 1,51 M€. Le solde non-website, soit 3,3 M€ de CA, doit donc dégager 0,39 M€, c'est-à-dire environ 11,9 %. C'est cohérent avec un marketplace à 10 % complété par la librairie Arthaud, dont Marc indique que la marge est sensiblement supérieure à celle de Lireka. **Les cibles tiennent entre elles** — elles sont exploitables telles quelles comme critère d'acceptation.

**Réserve à lever en premier.** Il n'est pas établi que les 8,9 M€ incluent Arthaud Grenoble. C'est le contrôle n°0 ci-dessous, et il conditionne l'interprétation de tous les autres.

---

## 2. Périmètre de la recette

Année civile 2025, sur `date_commande`. Découpage par canal : site direct d'un côté, marketplaces de l'autre, Arthaud isolé s'il est présent dans le modèle. Toutes les mesures sont prises **après application du patch** `patch-mesures-tmdl.md` §3.1, §3.2 et §4, et avant le repointage des cartes — l'objectif est de valider les mesures, pas les visuels.

---

## 3. Requêtes DAX Studio

Ouvrir `powerbi/Lireka_Profitabilite.pbip` dans Power BI Desktop, refresh complet, puis connecter DAX Studio au modèle en mémoire.

### R0 — Périmètre des 8,9 M€

```dax
EVALUATE
SUMMARIZECOLUMNS(
    fact_commandes[canal],
    FILTER(
        ALL(dim_date[date]),
        dim_date[date] >= DATE(2025,1,1) && dim_date[date] <= DATE(2025,12,31)
    ),
    "Revenu reconstruit", [Revenu (reconstruit)],
    "Nb commandes",       [Nb Commandes]
)
ORDER BY [Revenu reconstruit] DESC
```

Lire la liste des canaux et leur poids. Déterminer si Arthaud y figure. Somme de la colonne = base de comparaison aux 8,9 M€.

### R1 — Trio KPI global 2025

```dax
DEFINE
    VAR P2025 =
        FILTER(
            ALL(dim_date[date]),
            dim_date[date] >= DATE(2025,1,1) && dim_date[date] <= DATE(2025,12,31)
        )
EVALUATE
ROW(
    "Revenu",              CALCULATE([Revenu (reconstruit)], P2025),
    "Marge Brute",         CALCULATE([Marge Brute (reconstruit)], P2025),
    "Taux Marge",          CALCULATE([Taux Marge Brute (reconstruit)], P2025),
    "Revenu natif",        CALCULATE([Revenu], P2025),
    "% CA reconstruit",    CALCULATE([% CA reconstruit], P2025),
    "Marge apres Bloc 5",  CALCULATE([Marge Brute (reconstruit, après retours & génériques)], P2025),
    "Impact Bloc 5",       CALCULATE([Impact Bloc 5 (retours & génériques)], P2025),
    "Bloc 5 en points",    CALCULATE([Impact Bloc 5 en points de marge], P2025)
)
```

### R2 — Décomposition des 7 postes

```dax
DEFINE
    VAR P2025 =
        FILTER(
            ALL(dim_date[date]),
            dim_date[date] >= DATE(2025,1,1) && dim_date[date] <= DATE(2025,12,31)
        )
EVALUATE
ROW(
    "1 CA net annulation", CALCULATE([CA HT Net Annulation (reconstruit)], P2025),
    "2 Frais port",        CALCULATE(CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED"), P2025),
    "3 COGS",              CALCULATE([Coût Achat Total], P2025),
    "4 Transport amont",   CALCULATE([Coût Transport Amont], P2025),
    "5 Transport outbound",CALCULATE([Coût Transport Outbound (Retenu)], P2025),
    "6 Douanes taxes",     CALCULATE([Douanes Taxes], P2025),
    "7 Commissions mkt",   CALCULATE([Commissions Marketplace], P2025),
    "8 Fournitures",       CALCULATE([Fournitures Expédition], P2025),
    "  Pct transport facture", CALCULATE([% Coût transport facturé (vs estimé)], P2025)
)
```

Contrôle d'identité : `1 + 2 − 3 − 4 − 5 − 6 − 7 − 8` doit égaler exactement la Marge Brute de R1. Tout écart signale une mesure intermédiaire qui applique un filtre implicite non anticipé.

### R3 — Trio KPI par canal

```dax
EVALUATE
SUMMARIZECOLUMNS(
    fact_commandes[canal],
    FILTER(
        ALL(dim_date[date]),
        dim_date[date] >= DATE(2025,1,1) && dim_date[date] <= DATE(2025,12,31)
    ),
    "Revenu",           [Revenu (reconstruit)],
    "Marge Brute",      [Marge Brute (reconstruit)],
    "Taux Marge",       [Taux Marge Brute (reconstruit)],
    "Pct CA reconstruit", [% CA reconstruit],
    "Impact Bloc 5",    [Impact Bloc 5 (retours & génériques)]
)
ORDER BY [Revenu] DESC
```

### R4 — Contre-épreuve base native

```dax
EVALUATE
SUMMARIZECOLUMNS(
    fact_commandes[canal],
    FILTER(
        ALL(dim_date[date]),
        dim_date[date] >= DATE(2025,1,1) && dim_date[date] <= DATE(2025,12,31)
    ),
    "Revenu natif",      [Revenu],
    "Revenu reconstruit",[Revenu (reconstruit)],
    "Taux natif",        [Taux Marge Brute],
    "Taux reconstruit",  [Taux Marge Brute (reconstruit)]
)
```

Cette requête n'est pas un contrôle, c'est une **pièce de défense**. Elle documente pourquoi la base native a été écartée : elle doit montrer un taux marketplace natif très négatif, incompatible avec les 10 % déclarés par Marc. À conserver et à présenter si la méthode de reconstruction est contestée.

---

## 4. Critères d'acceptation

| # | Contrôle | Cible | Tolérance | Verdict |
|---|---|---|---|---|
| A1 | Revenu 2025 global (R1) | 8,9 M€ | ± 3 % | ⬜ |
| A2 | Revenu site direct 2025 (R3) | 5,6 M€ | ± 3 % | ⬜ |
| A3 | Taux de marge global (R1) | 17,0 % | ± 150 bps | ⬜ |
| A4 | Taux de marge site direct (R3) | 20,0 % | ± 200 bps | ⬜ |
| A5 | Taux de marge marketplace (R3) | 10,0 % | ± 200 bps | ⬜ |
| A6 | Identité des 7 postes (R2) | écart nul | < 1 € | ⬜ |
| A7 | Additivité canal (R3) | Σ canaux = total R1 | < 0,1 % | ⬜ |
| A8 | Impact Bloc 5 (R1) | ≈ 0,9 M€ | ordre de grandeur | ⬜ |
| A9 | Marge marketplace native (R4) | fortement négative | qualitatif | ⬜ |
| A10 | % CA reconstruit global (R1) | à mesurer, pas à cibler | — | ⬜ |

A1 à A5 sont les critères bloquants. A6 et A7 sont des contrôles d'intégrité du modèle : leur échec invalide la lecture de tous les autres. A8, A9 et A10 sont documentaires — ils alimentent le dossier de justification, ils ne conditionnent pas le passage.

---

## 5. Lecture des résultats

**A3 passe, A4 et A5 passent.** Le diagnostic était complet et la correction suffit. Le stack peut être repointé (patch §3.3 à §3.6) et le call client devient une présentation, pas une justification.

**A3 passe mais A5 échoue.** La reconstruction du CA marketplace est mal calibrée. Le taux de change moyen mensuel n'est pas le bon estimateur, ou la couverture de reconstruction est partielle. Point technique à traiter avant le call, hors périmètre de ce patch.

**A3 échoue par le bas après retrait du Bloc 5.** Le problème n'est plus le câblage. Deux causes probables à départager : les coûts de transport outbound estimés par le backend sont surévalués par rapport aux factures réelles — le contrôle `% Coût transport facturé` de R2 le montrera —, ou des coûts sont conservés sur des commandes annulées. Dans ce cas la responsabilité bascule côté données backend, ce qui est documenté et hors forfait.

**A3 échoue par le haut.** Le CA reconstruit est surévalué, ou des coûts manquent. Vérifier en priorité que les commissions marketplace sont bien captées sur l'ensemble des canaux.

**A6 ou A7 échouent.** Ne pas interpréter A1 à A5. Une mesure intermédiaire applique un filtre non anticipé ; il faut la corriger avant de reprendre la recette au début.

---

## 6. Restitution

Reporter les résultats dans un classeur `recette_2025.xlsx` à trois onglets : une synthèse reprenant le tableau §4 avec les valeurs obtenues et le verdict, le détail des sorties R0 à R4 collées brutes, et une note d'écart pour chaque critère non passé avec cause identifiée et responsabilité assignée. Ce classeur est la pièce à présenter au call — pas le dashboard.