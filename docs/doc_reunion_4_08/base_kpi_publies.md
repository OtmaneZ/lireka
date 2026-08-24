# ADR-001 — Base du stack KPI publié et périmètre de la marge brute

Date : 2026-08-04 · Phase 3 (BIEN AVANCÉ) · Statut : **décidé, en attente de recette**

## Contexte

Le client a validé la forme des dashboards mais conteste les chiffres. L'audit de `_Mesures.tmdl` a établi que les cartes KPI publiées mélangent trois périmètres : `KPI Compact — Revenue` affiche le revenu reconstruit, `KPI Compact — Gross Profit` affiche une marge calculée sur CA natif, et `KPI Compact — Gross Margin` divise la marge native par le revenu reconstruit. Un taux dont le numérateur et le dénominateur ne partagent pas le même périmètre n'est pas réconciliable par un contrôleur de gestion.

## Décision A — la base publiée est le CA reconstruit

Les trois KPI publiés (Revenu, Gross Profit, Gross Margin) sont alignés sur `[Revenu (reconstruit)]`, `[Marge Brute (reconstruit)]` et `[Taux Marge Brute (reconstruit)]`.

Motif déterminant : Marc a déclaré en call une marge brute marketplace de +10 %. Sur base native, le CA marketplace en EUR est absent ou nul sur une large part de l'historique alors que les coûts correspondants sont présents. Une base native produit donc une marge marketplace fortement négative et ne peut structurellement pas reproduire la réalité connue du client. L'avantage de traçabilité de la base native ne compense pas cette impossibilité.

Contrepartie assumée : le dénominateur n'est pas réconciliable pièce à pièce avec la comptabilité. Elle est traitée par publication explicite du taux de reconstruction (mesure `% CA reconstruit`), et non masquée. Les mesures natives sont conservées comme contrôles internes, masquées du field list.

## Décision B — le KPI publié applique les 7 postes de la formule client

`Retours Remboursements` et `Coûts Génériques` sont retirés de la mesure de marge publiée. Ils ne figurent pas dans la formule transmise par Marc, qui est le référentiel contractuel de la mission. Leur inclusion représentait environ −0,9 M€ sur un CA d'environ 8,9 M€, soit près de 10 points de taux de marge — cause première et quantifiée du symptôme « marge trop basse » remonté par le client.

Ces deux postes ne disparaissent pas : ils deviennent une ligne de réconciliation visible sous le KPI, via `[Marge Brute (reconstruit, après retours & génériques)]` et `[Impact Bloc 5]`. Traitement P&L standard : marge brute définie contractuellement, postes below-the-line affichés séparément. L'arbitrage sur leur intégration éventuelle reste à Marc, mais ne bloque plus la livraison.

## Conséquences

La mesure hybride `[Taux Marge Brute (revenu reconstruit)]` et ses déclinaisons PY / YoY bps sont supprimées. Les mesures cibles existant déjà dans le modèle mais orphelines, la correction est majoritairement un rebranchement plutôt qu'une réécriture, ce qui limite le risque de régression.

La décision est validée ou infirmée par la recette chiffrée 2025, dont les critères d'acceptation sont les valeurs déclarées par Marc : CA 8,9 M€ dont 5,6 M€ site direct, taux de marge 17 % global, 20 % site direct, 10 % marketplace. Si ces critères échouent après correction, le problème n'est plus le câblage du modèle mais la qualité des données backend, ce qui relève d'un périmètre distinct.

## Documents liés

`patch-mesures-tmdl.md` (modifications à appliquer), `recette-chiffree-kpi.md` (protocole de validation), `docs/audit_complet.md` (audit du 2026-07-18), doc projet « Here is the formula to calculate Gross Margin » (référentiel formule).