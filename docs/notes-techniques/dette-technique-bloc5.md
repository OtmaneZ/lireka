# Dette technique — Bloc 5 (retours/remboursements + coûts génériques)

> **Statut** : implémenté dans `Lireka_Profitabilite.SemanticModel` le 15/07/2026  
> **Décision** : ZineInsights — postes inclus dans `[Marge Brute]` en **dette technique**  
> **Validation Marc** : périmètre `returns_and_refunds_cost_eur` et `total_generic_costs_eur` à revoir côté backend

---

## Contexte

La formule Marc (Slack, 13/07/2026) excluait initialement les retours/remboursements et les coûts génériques. Ces postes existent dans `customer_order_item.csv` (grain article) et sont agrégés par `order_id` pour alimenter `fact_commandes` au grain commande, cohérent avec `[Marge Brute]`.

---

## Source et grain

| Champ source (`customer_order_item`) | Colonne `fact_commandes` | Agrégation |
|--------------------------------------|--------------------------|------------|
| `returns_and_refunds_cost_eur` | `retours_remboursements` | `SUM` par `order_id` |
| `generic_costs_eur` | `couts_generiques` | `SUM` par `order_id` |

- Staging : `stg_couts_bloc5_commande` (`expressions.tmdl`)
- Jointure : gauche sur `id_commande` = `order_id`, null → 0
- Les valeurs sont **par article** (non constantes sur les commandes multi-articles) : la somme par commande est le traitement correct.

Contrôle : `SUM` agrégé = `SUM` brut `customer_order_item` (tolérance 0,01 €). Également aligné à 100 % avec `returns_and_refunds_eur` / `total_generic_costs_eur` au grain commande dans `customer_order.csv`.

---

## Montants audités (entrepôt `Données_Backend/`, 15/07/2026)

| Poste | SUM total | SUM hors CANCELLED | % du CA natif (9,65 M€) |
|-------|-----------|-------------------|-------------------------|
| Retours et remboursements | **176 145,52 €** | 164 645,26 € | 1,83 % |
| Coûts génériques | **747 983,55 €** | 716 160,24 € | 7,75 % |
| **Total Bloc 5** | **924 129,07 €** | 880 805,50 € | 9,58 % |

Impact sur `[Marge Brute]` : **−924 129,07 €** (passage de −20 825 594 € à **−21 749 723 €**).

---

## Dette technique

Ces deux postes sont **provisoires** :

- Marc doit valider le périmètre de `returns_and_refunds_cost_eur`
- Marc doit revoir `total_generic_costs_eur` côté backend (définition comptable)

Le terme CA de `[Marge Brute]` reste le CA natif (non reconstruit marketplace).
Le nettoyage des annulations (CA=0 sur CANCELLED) est traité séparément via
`[CA HT Net Annulation]` — voir [limite-etf-annulation.md](./limite-etf-annulation.md).
Bloc 5 n'ajoute que les 2 postes de coût (retours, génériques), sans toucher au terme CA.

---

## Recoupement `contribution_profit_eur`

Test : `gross_profit_eur − retours − génériques ≈ contribution_profit_eur`

| Indicateur | Valeur |
|------------|--------|
| Match ligne par ligne (±0,01 €) | 46 635 / 989 234 (4,7 %) |
| SUM `gross_profit_eur` | 18 898 244 € |
| SUM `contribution_profit_eur` | 5 499 106 € |
| SUM `gross_profit − retours − génériques` | 17 974 115 € |
| Écart agrégé | 12 475 009 € |

→ La relation n'est **pas** une identité globale sur cet export ; les postes restent intégrés comme coûts additionnels de la formule Marc, pas comme substitut à `contribution_profit_eur`.

---

## Fichiers modifiés

| Fichier | Modification |
|---------|--------------|
| `definition/expressions.tmdl` | `stg_couts_bloc5_commande` |
| `definition/tables/fact_commandes.tmdl` | Colonnes + jointure Power Query |
| `definition/tables/_Mesures.tmdl` | `[Retours Remboursements]`, `[Coûts Génériques]`, `[Marge Brute]` |
| `definition/model.tmdl` | Ordre des requêtes |

---

## Points de validation pour Marc (fin de mission)

- [ ] Valider le périmètre `returns_and_refunds_cost_eur` (retours SAV, remboursements partiels, etc.)
- [ ] Revoir la définition et le calcul de `total_generic_costs_eur` / `generic_costs_eur`
- [ ] Confirmer que l'agrégation `SUM` par commande est le bon grain pour la marge pilotage
- [ ] Arbitrer sur l'écart `contribution_profit_eur` vs formule Marc enrichie Bloc 5
