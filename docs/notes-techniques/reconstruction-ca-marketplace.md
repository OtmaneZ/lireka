# Reconstruction du CA marketplace en EUR — option B

> **Statut** : implémenté dans `Lireka_Profitabilite.SemanticModel` le 15/07/2026  
> **Décision** : ZineInsights — à faire valider par Marc Bordier en fin de mission  
> **Référence code** : `stg_taux_moyen_mensuel`, colonne `fact_commandes[ca_ht_reconstruit]`, mesure `[CA Total HT (reconstruit)]`

---

## Contexte du problème

Sur les canaux marketplace (Amazon, Cultura, Rakuten, Fnac), le backend Lireka ne renseigne pas `order_amount_eur` : la colonne est systématiquement vide ou nulle, alors que `order_amount_local` porte le montant HT dans la devise de la place de marché.

À l'inverse, sur WEBSITE et PRO_WEBSITE, `currency_rate` est renseigné (surtout à partir de 2026, où le taux est présent sur 100 % des commandes). Ce taux représente des **unités de devise locale pour 1 EUR** ; la conversion observée est :

`order_amount_eur ≈ order_amount_local / currency_rate`

Les dashboards transporteurs et le modèle de profitabilité existant utilisaient `order_amount_eur` tel quel (`ca_ht`), ce qui excluait de fait le CA marketplace du pilotage.

---

## Méthode choisie (option B — taux interne reconstruit)

Aucune source externe de taux (BCE, API FX, etc.). Reconstruction entièrement interne au modèle Power BI :

### Étape 1 — `stg_taux_moyen_mensuel` (Power Query, non chargé)

Pour chaque couple `(devise, année_mois)` :

```
taux_moyen_mensuel = MOYENNE(currency_rate)
```

Calculé sur **toutes les commandes** où `currency_rate` est non nul (WEBSITE, PRO_WEBSITE et autres canaux confondus), groupées par `currency` et `année_mois` (`AAAAMM` dérivé de `origin_created`).

### Étape 2 — Colonne `ca_ht_reconstruit` dans `fact_commandes`

| Condition | Valeur |
|-----------|--------|
| `order_amount_eur` non null et ≠ 0 | Conserver `order_amount_eur` (natif backend) |
| Sinon, si `order_amount_local` ≠ 0 **et** un `taux_moyen_mensuel` existe pour la devise/mois | `order_amount_local / taux_moyen_mensuel` |
| Sinon | `null` (reconstruction impossible — cas à isoler) |

### Étape 3 — Mesures DAX (pattern parallèle)

Comme pour `[Marge Brute]` vs `[Marge Brute (prov.)]` :

| Mesure existante (inchangée) | Nouvelle mesure |
|------------------------------|-----------------|
| `[CA Total HT]` = `SUM(ca_ht)` | `[CA Total HT (reconstruit)]` = `SUM(ca_ht_reconstruit)` |

`ca_ht` natif est **conservé** pour ne pas casser les mesures de marge et de contrôle existantes.

---

## Hypothèse

Le **taux moyen mensuel** (et non le taux du jour de la commande) est utilisé comme proxy pour les commandes marketplace sans `currency_rate`. Cette approximation suppose que le taux moyen observé sur WEBSITE/PRO_WEBSITE dans le même mois et la même devise est représentatif du taux réel appliqué par Lireka sur les marketplaces.

---

## Limites connues

1. **Couverture temporelle des taux de référence** : `currency_rate` n'est massivement renseigné qu'à partir de 2026 (100 % des commandes 2026 dans l'export audité ; ~3,7 % en 2025). Les commandes marketplace historiques (2020–2024) n'ont souvent **aucun taux mensuel de référence** pour leur devise/mois → reconstruction impossible.
2. **Pas de conversion officielle Lireka** : approximation interne, pas le calcul finance backend.
3. **FNAC** : devise EUR, mais sans taux mensuel EUR de référence sur les périodes concernées → 0 % de récupération dans l'audit.
4. **Marketplace Amazon historique** : fort volume de commandes avec `order_amount_local > 0` mais sans couple devise/mois couvert.
5. **Snapshot SharePoint** : au 15/07/2026, le fichier `Données_Backend/customer_order.csv` de l'entrepôt Power BI avait `order_amount_local = 0` sur toutes les lignes marketplace (données apparemment dénormalisées). L'export backend brut (`data/raw/customer_order.csv`) reflète le comportement attendu avec `order_amount_local` renseigné. **Vérifier la fraîcheur de l'export SharePoint avant refresh Power BI.**

---

## Volumes de commandes concernées

Analyse sur `data/raw/customer_order.csv` (1 007 110 lignes, backend brut représentatif) — logique identique au modèle Power BI.

### Marketplace — avant / après reconstruction

Critère « avant » : commande marketplace avec `order_amount_eur` absent (≤ 0) **et** `order_amount_local > 0`.

| Indicateur | Volume |
|------------|--------|
| Commandes marketplace totales | 680 247 |
| Éligibles à reconstruction (EUR natif absent, local > 0) | **648 718** |
| Récupérées après reconstruction (`ca_ht_reconstruit` > 0) | **74 130** |
| Toujours sans CA (null) | 574 588 |
| **Taux de récupération** | **11,4 %** |

### Par canal (récupérées / éligibles)

| Canal | Récupérées | Éligibles | Taux |
|-------|------------|-----------|------|
| AMAZON_FR | 45 487 | 365 101 | 12,5 % |
| AMAZON_CA | 2 124 | 62 884 | 3,4 % |
| CULTURA | 9 811 | 48 139 | 20,4 % |
| AMAZON_US | 2 872 | 41 503 | 6,9 % |
| AMAZON_DE | 3 093 | 31 475 | 9,8 % |
| AMAZON_UK | 1 706 | 29 731 | 5,7 % |
| RAKUTEN | 4 055 | 26 494 | 15,3 % |
| AMAZON_BE | 2 765 | 22 838 | 12,1 % |
| AMAZON_IT | 1 583 | 10 274 | 15,4 % |
| AMAZON_ES | 634 | 9 087 | 7,0 % |
| FNAC | 0 | 768 | 0 % |
| AMAZON_NL | 0 | 369 | 0 % |
| AMAZON_SE | 0 | 55 | 0 % |

### Par année (récupérées / éligibles)

La récupération est concentrée sur **2025–2026**, seules périodes où des taux de référence mensuels existent (38 couples devise/mois en 2025, 296 en 2026) :

| Année | Récupérées | Éligibles |
|-------|------------|-----------|
| 2020 | 0 | 30 688 |
| 2021 | 0 | 106 724 |
| 2022 | 0 | 97 328 |
| 2023 | 0 | 98 207 |
| 2024 | 0 | 134 730 |
| 2025 | 14 872 | 121 783 |
| 2026 | 59 258 | 59 258 |

Montants agrégés (proxy sur `order_amount_local` avant, EUR reconstruit après) : ~17,2 M unités locales → ~2,0 M EUR récupérés sur les 74 130 commandes.

### Snapshot entrepôt Power BI (`Données_Backend/customer_order.csv`)

Sur le fichier effectivement consommé par le modèle au moment de l'implémentation :

- Commandes marketplace éligibles : **0** (`order_amount_local` à 0 partout sur marketplace)
- Récupérées : **0**

→ Un refresh Power BI sur cet export ne produira un CA marketplace reconstruit **qu'après mise à jour de l'export backend** avec les `order_amount_local` marketplace.

---

## Fichiers modifiés

| Fichier | Modification |
|---------|--------------|
| `definition/expressions.tmdl` | Typage `currency_rate` / `order_amount_local` dans `stg_customer_order` ; nouvelle requête `stg_taux_moyen_mensuel` |
| `definition/tables/fact_commandes.tmdl` | Colonne `ca_ht_reconstruit` + logique Power Query |
| `definition/tables/_Mesures.tmdl` | Mesure `[CA Total HT (reconstruit)]` |
| `definition/model.tmdl` | Ordre des requêtes (`stg_taux_moyen_mensuel`) |

Aucun visuel dashboard ajouté — documentation en commentaires de code et dans ce fichier uniquement.

---

## Points de validation pour Marc (fin de mission)

- [ ] Valider l'approximation « taux moyen mensuel » vs taux du jour
- [ ] Confirmer que `order_amount_local / currency_rate` est bien la formule backend de référence
- [ ] Arbitrer sur l'historique pré-2026 (non récupérable avec l'option B actuelle)
- [ ] Vérifier la fraîcheur de l'export `customer_order.csv` sur SharePoint (locaux marketplace)
- [ ] Décider si `[CA Total HT (reconstruit)]` doit un jour remplacer `[CA Total HT]` dans la formule de marge
