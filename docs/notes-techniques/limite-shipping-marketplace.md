# Limite shipping revenue marketplace — `shipping_fee_eur` vide

> **Statut** : documenté le 15/07/2026 (audit Bloc 4) — **aucune reconstruction implémentée**  
> **Décision** : ZineInsights — hors périmètre Bloc 4  
> **Référence code** : colonne `fact_commandes[frais_port_encaisse]` (rename de `shipping_fee_eur`), mesure `[Frais Port Encaissés]`  
> **Cause racine probable** : même origine que le trou CA marketplace — voir [reconstruction-ca-marketplace.md](./reconstruction-ca-marketplace.md)

---

## Contexte du problème

Sur les canaux marketplace (Amazon toutes zones, Cultura, Rakuten, Fnac), le backend Lireka ne renseigne pas `shipping_fee_eur` : la colonne est systématiquement à **0** sur 100 % des commandes, alors que `shipping_fee_local` porte le montant des frais de port encaissés dans la devise de la place de marché.

À l'inverse, sur WEBSITE, PRO_WEBSITE et ARTHAUD, `shipping_fee_eur` est alimenté pour une fraction significative des commandes payantes (frais de port > 0).

Le modèle Power BI expose `shipping_fee_eur` renommé en `frais_port_encaisse` sans transformation ni reconstruction. La mesure `[Frais Port Encaissés]` = `SUM(fact_commandes[frais_port_encaisse])` reflète donc fidèlement l'export backend — y compris les zéros marketplace.

---

## Symptôme observé (audit Bloc 4)

Snapshot audité : `Power_BI_Datawarehouse/Données_Backend/customer_order.csv` (989 234 lignes, export du 14/07/2026).

### Couverture par canal

| Canal | Nb commandes | `shipping_fee_eur` > 0 | SUM `shipping_fee_eur` | `shipping_fee_local` > 0 | SUM `shipping_fee_local` |
|-------|--------------|------------------------|------------------------|--------------------------|--------------------------|
| **WEBSITE** (WEBSITE + PRO_WEBSITE) | 300 377 | 9 284 (**3,1 %**) | **25 363,44 €** | 41 185 (13,7 %) | 658 337,19 (unités locales) |
| **MARKETPLACE** | 669 997 | **0 (0,0 %)** | **0,00 €** | **509 312 (76,0 %)** | **~3,17 M** (unités locales, devises mixtes) |
| **ARTHAUD** | 18 860 | 3 126 (16,6 %) | **3 558,40 €** | 11 463 (60,8 %) | 7 840,22 (unités locales) |
| **Total entrepôt** | 989 234 | 12 410 (1,3 %) | **28 921,84 €** | — | — |

Sur WEBSITE, le faible taux de commandes avec frais > 0 (3,1 %) reflète surtout la **gratuité du port** sur la majorité des commandes, pas un trou de données : quand `shipping_fee_local` > 0, `shipping_fee_eur` est cohérent.

Sur marketplace, le trou est structurel : **509 312 commandes** (76 % du volume marketplace) ont `shipping_fee_local` > 0 mais `shipping_fee_eur` = 0.

### Détail marketplace par place

| Canal | Nb commandes | `shipping_fee_eur` > 0 | `shipping_fee_local` > 0 |
|-------|--------------|------------------------|--------------------------|
| AMAZON_FR | 379 034 | 0 % | 87,7 % |
| AMAZON_CA | 65 001 | 0 % | 23,7 % |
| CULTURA | 49 005 | 0 % | 96,9 % |
| AMAZON_US | 42 766 | 0 % | 38,1 % |
| AMAZON_DE | 31 954 | 0 % | 62,4 % |
| AMAZON_UK | 30 873 | 0 % | 55,1 % |
| AMAZON_BE | 24 327 | 0 % | 87,7 % |
| RAKUTEN | 25 663 | 0 % | 99,9 % |
| AMAZON_IT | 10 817 | 0 % | 89,2 % |
| AMAZON_ES | 9 352 | 0 % | 37,9 % |
| FNAC | 768 | 0 % | 97,9 % |
| AMAZON_NL | 382 | 0 % | 0 % |
| AMAZON_SE | 55 | 0 % | 0 % |

### Contrôle d'intégrité modèle (Bloc 4)

| Indicateur | Montant |
|------------|---------|
| `SUM(shipping_fee_eur)` brut CSV | **28 921,84 €** |
| `[Frais Port Encaissés]` attendu (rename seul, sans filtre) | **28 921,84 €** |
| Inclus dans `[Marge Brute]` (non-CANCELLED) | **27 638,33 €** |
| Exclu par filtre `CANCELLED` (voulu) | **1 283,51 €** |

Le pipeline Power Query ne filtre ni ne met à zéro conditionnellement `shipping_fee_eur`. L'écart marketplace n'est pas un bug de modèle.

---

## Impact sur les mesures

| Mesure | Comportement marketplace |
|--------|------------------------|
| `[Frais Port Encaissés]` | **Sous-évaluée à 0 €** sur tout le marketplace — même symptôme que `[CA Total HT]` avant reconstruction (Bloc 1) |
| `[Marge Brute]` | Le terme `+ CALCULATE([Frais Port Encaissés], state <> "CANCELLED")` est correctement câblé mais n'apporte **aucun revenu port marketplace** tant que `shipping_fee_eur` reste vide |
| `[Taux Marge Brute]` | Dénominateur `[CA Total HT] + [Frais Port Encaissés]` — le shipping marketplace manquant tire mécaniquement le taux vers le haut sur les segments où le CA est présent |

Répartition du shipping revenue EUR actuellement capté :

| Canal | Part du total EUR |
|-------|-------------------|
| WEBSITE | 87,7 % (25 363,44 €) |
| ARTHAUD | 12,3 % (3 558,40 €) |
| MARKETPLACE | **0 %** (0,00 €) |

---

## Lien avec le trou CA marketplace

Voir [reconstruction-ca-marketplace.md](./reconstruction-ca-marketplace.md) — **même cause racine probable** : le backend Lireka ne convertit pas en EUR les montants marketplace (`order_amount_eur`, `shipping_fee_eur`), alors que les champs locaux (`order_amount_local`, `shipping_fee_local`) sont renseignés.

| Champ | Marketplace — champ EUR | Marketplace — champ local |
|-------|-------------------------|---------------------------|
| CA commande | `order_amount_eur` = 0 % | `order_amount_local` variable selon snapshot SharePoint |
| Frais de port | `shipping_fee_eur` = **0 %** | `shipping_fee_local` > 0 sur **76 %** des commandes |

**Différence de traitement dans le modèle** :

| Poste | Reconstruction implémentée ? | Référence |
|-------|------------------------------|-----------|
| CA marketplace | **Oui** — option B (taux moyen mensuel) | `ca_ht_reconstruit`, `[CA Total HT (reconstruit)]` |
| Shipping marketplace | **Non** | Ce document |

---

## Statut et pistes de résolution

**Aucune reconstruction n'est implémentée** pour le shipping revenue marketplace (contrairement au CA, option B du Bloc 1). Décision Bloc 4 : documentation uniquement, pas de modification `.tmdl`.

Pistes futures (hors périmètre actuel) :

1. **Backend** : Michal fournit `shipping_fee_eur` converti côté export `customer_order.csv` (solution préférée — alignement avec la logique finance Lireka).
2. **Modèle Power BI** : étendre la même logique de reconstruction que le CA (option B) à `shipping_fee_local` → colonne `frais_port_encaisse_reconstruit` + mesure parallèle — **uniquement si** la demande métier l'étend explicitement au shipping et après validation Marc.
3. **Snapshot SharePoint** : sur l'export audité, `shipping_fee_local` est renseigné sur marketplace (contrairement à `order_amount_local` qui était à 0 sur ce snapshot). Un refresh avec un export backend à jour améliorerait la **visibilité** du trou local mais ne résoudrait pas l'absence de conversion EUR sans développement supplémentaire.

---

## Limites connues

1. **Pas de conversion EUR marketplace** : ~3,17 M d'unités locales de frais de port non converties (devises mixtes — Amazon US/CAD, Cultura EUR, Rakuten EUR, etc.) — montant EUR réel inconnu sans taux ou champ backend.
2. **Pas de mesure de contrôle parallèle** : contrairement au CA, il n'existe pas de `[Frais Port Encaissés (reconstruit)]` dans le modèle.
3. **Impact limité sur le total actuel** : le shipping revenue capté (28 922 €) est modeste vs le CA ; l'impact marketplace est surtout un **biais de segment** (marge marketplace surestimée en relatif faute de revenu port).
4. **Filtre CANCELLED** : 1 283,51 € de frais port exclus de `[Marge Brute]` sur commandes annulées — comportement voulu, documenté dans `_Mesures.tmdl`, indépendant du trou marketplace.

---

## Fichiers concernés (lecture seule — aucune modification Bloc 4)

| Fichier | Rôle |
|---------|------|
| `definition/expressions.tmdl` | Typage `shipping_fee_eur` dans `stg_customer_order` |
| `definition/tables/fact_commandes.tmdl` | Rename `shipping_fee_eur` → `frais_port_encaisse` |
| `definition/tables/_Mesures.tmdl` | `[Frais Port Encaissés]`, inclusion dans `[Marge Brute]` |

Aucun visuel dashboard ajouté — documentation dans ce fichier uniquement.

---

## Points de validation pour Marc (fin de mission)

- [ ] Confirmer que `shipping_fee_eur` doit être alimenté côté backend pour les marketplaces (comme pour le CA)
- [ ] Arbitrer si une reconstruction option B (taux moyen mensuel sur `shipping_fee_local`) est souhaitée, ou si seul le champ backend converti fait foi
- [ ] Quantifier l'impact EUR réel du shipping marketplace manquant (nécessite conversion officielle ou taux validés)
- [ ] Décider si `[Frais Port Encaissés (reconstruit)]` doit un jour entrer dans la formule `[Marge Brute]`
