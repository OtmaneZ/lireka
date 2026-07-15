# Limite ETF — proxy package_id pour l'annulation avant/après expédition

> **Statut** : implémenté dans `Lireka_Profitabilite.SemanticModel` le 15/07/2026  
> **Décision** : Marc Bordier (Slack) — logique avant/après expédition ; proxy technique ZineInsights  
> **Référence code** : colonne `fact_lignes[statut_annulation_ligne]`, mesures Bloc 3 dans `_Mesures.tmdl`

---

## Contexte du problème

Le backoffice Lireka distingue les annulations **avant** et **après** expédition via un sous-statut ETF (Early Termination Fee / frais d'annulation), visible uniquement **à l'unité** dans l'interface backoffice. Ce champ **n'existe pas** dans les exports CSV consommés par Power BI (`customer_order_item.csv`, `customer_order_item_group.csv`).

Sans ce discriminant, la logique de marge Bloc 3 (zéro CA ligne + zéro coût transport sortant si avant expédition ; tous coûts conservés si après) ne peut pas être appliquée fidèlement au grain article.

---

## Méthode choisie — proxy `package_id`

Décision actée par Marc Bordier : utiliser la présence ou l'absence de `package_id` sur l'article comme substitut :

| Proxy | Interprétation | Règle métier Marc |
|-------|----------------|-------------------|
| `internal_state = CANCELLED` **et** `package_id` null | Annulé **avant** expédition | CA ligne = 0 ; coût transport sortant = 0 ; coût achat produit conservé |
| `internal_state = CANCELLED` **et** `package_id` non-null | Annulé **après** expédition | CA ligne = 0 ; **tous** les coûts conservés |
| `internal_state <> CANCELLED` | Non annulé | CA et coûts normaux |

Colonne calculée `statut_annulation_ligne` dans `fact_lignes.tmdl` :

```
NON_ANNULE | ANNULE_AVANT_EXPEDITION | ANNULE_APRES_EXPEDITION
```

---

## Résultats audit proxy (15/07/2026)

Source : `Power_BI_Datawarehouse/Données_Backend/` — 100 670 items `CANCELLED`.

| Indicateur | Volume | % |
|------------|--------|---|
| `package_id` null → avant expédition | 100 501 | **99,83 %** |
| `package_id` non-null → après expédition | 169 | **0,17 %** |
| `package_id` non-null existant dans `package.csv` | 169 / 169 | 100 % |
| Dont `shipping_cost_eur` non-nul | 127 / 169 | 75,15 % |

### Cas limites — package avec états mixtes

| Indicateur | Volume |
|------------|--------|
| `package_id` distincts avec > 1 `internal_state` | 428 |
| Packages avec **CANCELLED + autre état** | **10** |
| Items concernés (tous états mixtes) | 3 514 |

**Risque d'erreur estimé** : 10 packages / 946 483 packages totaux = **0,001 %** ; 169 items après-expédition / 100 670 CANCELLED = **0,17 %**. Bien en deçà du seuil d'alerte 2–3 %.

### Exemples de packages mixtes (audit)

| package_id | order_id | États |
|------------|----------|-------|
| 124425 | 131386 | 1 SHIPPED, 1 CANCELLED |
| 144299 | 150515 | 5 SHIPPED, 1 CANCELLED |
| 192004 | 198256 | 9 SHIPPED, 2 CANCELLED |
| 192365 | 198973 | 3 SHIPPED, 2 CANCELLED |
| 243296 | 242892 | 65 SHIPPED, 1 CANCELLED |

**Traitement proposé (non tranché)** : conserver le proxy tel quel (l'article CANCELLED avec `package_id` est classé après expédition même si d'autres articles du même colis sont SHIPPED) ; alternative = reclasser au niveau package si **tous** les items du package sont CANCELLED. À valider avec Marc.

---

## Limite connue — `customer_price_per_item_eur` non renseigné

Audit Bloc 3 (reconstruction CA au grain article) :

| Indicateur | Volume |
|------------|--------|
| Items avec `customer_price_per_item_eur` = 0 | 1 746 664 / 1 847 317 (**94,6 %**) |
| Commandes `ca_ht > 0` dont somme lignes = `ca_ht` (tol. 0,01 €) | 9 021 / 146 796 (**6,15 %**) |
| Commandes sans annulation, `ca_ht > 0`, somme lignes = `ca_ht` | 8 611 / 140 053 (**6,15 %**) |
| Sous-ensemble `ca_adj > 0` (prix ligne renseigné) | match **70,3 %** |

**Cause identifiée** : `customer_price_per_item_eur` n'est pas systématiquement alimenté dans `customer_order_item_group.csv` ; le CA commande (`order_amount_eur`) est porté au niveau commande uniquement. La mesure `[CA Total HT (grain article, ajusté annulation)]` est structurellement correcte mais **sous-estime le CA** tant que les prix ligne ne sont pas exportés.

**Non bloquant pour le proxy annulation** ; bloquant pour remplacer `[CA Total HT]` dans la marge finale.

---

## Décision grain commande (livraison Bloc 3)

> **Statut** : implémenté le 15/07/2026  
> **Décision** : ZineInsights — mesure de référence `[Marge Brute]` au grain **commande**

### Pourquoi le grain commande

`customer_price_per_item_eur` est à **0 sur 94,6 %** des articles : impossible d'appliquer la règle Marc « CA = 0 sur annulation » via le grain article sans sous-estimer massivement le revenu. Le CA fiable est `order_amount_eur` au niveau `customer_order.csv`.

### Règle livrée dans `[Marge Brute]`

| Poste | Traitement grain commande |
|-------|---------------------------|
| CA (`order_amount_eur`) | **Zéro** sur `state = CANCELLED` via `[CA HT Net Annulation]` |
| Frais de port encaissés | **Exclus** sur `state = CANCELLED` (1 283 €, audit 15/07/2026) |
| Coût achat, commissions, transport amont | **Conservés** sur toutes commandes (y compris annulées) |
| Transport sortant (`fact_transport`) | **Inchangé** — commande sans colis = pas de ligne transport (avant expédition) ; avec colis = coût conservé (après expédition) |

### Ce qui n'est pas capturé

| Limite | Volume audité |
|--------|---------------|
| Annulations partielles (`state <> CANCELLED`, ≥1 item `CANCELLED`) | **8 896 commandes** |
| Borne haute CA non ajusté | **428 863 €** (`[CA Commandes Annulation Partielle]`) |

### Couche de contrôle conservée (grain article)

Inchangée — chemin de montée en charge si les prix ligne sont exportés un jour :

- `fact_lignes[statut_annulation_ligne]`
- `[CA Total HT (grain article, ajusté annulation)]`, `[Marge Brute (grain article, prov.)]`, etc.

### Mesures grain commande ajoutées

| Mesure | Rôle |
|--------|------|
| `[CA HT Net Annulation]` | CA HT hors commandes `CANCELLED` |
| `[CA HT Net Annulation (reconstruit)]` | Variante marketplace |
| `[CA Commandes Annulation Partielle]` | Transparence — CA des commandes partiellement annulées |

---

## Coût transport — confirmation niveau item

Sur les 100 501 items CANCELLED avec `package_id` null :

- **0** lien `package_id` → `fact_transport` (attendu).
- 8 889 commandes ont à la fois des items CANCELLED null-pkg **et** d'autres items avec colis (annulation partielle normale) — le coût transport de ces colis ne doit pas être imputé aux items annulés avant expédition (traitement Bloc 3 ultérieur sur la ventilation transport).

---

## Fichiers modifiés

| Fichier | Modification |
|---------|--------------|
| `definition/tables/fact_lignes.tmdl` | Colonne calculée `statut_annulation_ligne` |
| `definition/tables/_Mesures.tmdl` | Mesures Bloc 3 grain article (contrôle) + grain commande (livraison) ; `[Marge Brute]` utilise `[CA HT Net Annulation]` |

Aucun visuel dashboard ajouté.

---

## Points de validation pour Marc (fin de mission)

- [ ] Valider le proxy `package_id` null / non-null comme substitut du sous-statut ETF
- [ ] Trancher sur les 10 packages à états mixtes (classer item par item vs package entier)
- [ ] Confirmer que le coût achat produit est conservé dans **tous** les cas d'annulation
- [ ] Valider l'application grain **commande** de la règle CA=0 (`[Marge Brute]` livrée)
- [ ] Arbitrer sur l'export de `customer_price_per_item_eur` au grain article (bascule future)
- [ ] Décider si `[Marge Brute (grain article, prov.)]` peut un jour remplacer `[Marge Brute]`
