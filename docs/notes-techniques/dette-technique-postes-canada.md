# Dette technique — Postes Canada (coût estimé backend)

> **Statut** : intégré au modèle profitabilité le 15/07/2026 (Bloc 6)  
> **Décision** : confirmé Marc — colis backend dans le périmètre, pas de dashboard transporteur dédié  
> **Pattern** : identique à Colis Privé (fallback `shipping_cost_eur`, pas de facture transporteur)

---

## Contexte

Les colis **Postes Canada** sont expédiés via des **AWB FedEx groupés** : le fret international est facturé par FedEx, pas par Postes Canada. Il n'existe **pas de récap facture transporteur Postes Canada** dans l'entrepôt (seuls Colissimo et Chronopost sont rapprochés).

Le modèle intègre néanmoins ces colis au complet pour le pilotage profitabilité, avec un **coût estimé backend** (`package.shipping_cost_eur`).

---

## Identification dans le modèle

| Élément | Implémentation |
|---------|----------------|
| Inférence transporteur | `fnNormaliserTransporteur` — préfixe suivi `Q013` → `"Postes Canada"` |
| Alias textuels | `fnCanonTransporteur` — `"POSTES CANADA"`, `"CANADA POST"` |
| Référentiel | `dim_transporteur` — statut `"Nouveau (intégré)"` |
| Grain | `fact_transport` (une ligne par colis) |

Aucune logique spécifique Postes Canada dans `source_cout` : le fallback générique s'applique (comme Colis Privé).

---

## Logique `source_cout`

Pour chaque colis Postes Canada :

| Condition | `source_cout` | Coût retenu |
|-----------|---------------|-------------|
| Facture Colissimo/Chronopost rapprochée | `facture_rapprochee` | Montant facturé |
| Sinon, `shipping_cost_eur` > 0 | `backend_seul` | Estimation backend |
| Sinon | `aucun` | Exclu du coût |

**Audit entrepôt (15/07/2026)** : 3 788 colis Postes Canada, **100 % `backend_seul`**, **0 % `facture_rapprochee`**. Aucun suivi `Q013` présent dans les factures La Poste/Chronopost — pas de contamination FedEx ni de coût réel attribué par erreur.

---

## Volumes audités (`Données_Backend/package.csv`, 15/07/2026)

| Indicateur | Valeur |
|------------|--------|
| Nb colis Postes Canada | **3 788** (0,40 % du volume total) |
| Préfixe `Q013` | **3 788** (100 %) |
| `shipping_cost_eur` renseigné | **3 788** (100 %) |
| SUM `shipping_cost_eur` | **22 826,44 €** |
| Rattachés à `fact_commandes` | **3 788** (100 %, 0 orphelin) |
| Coût facturé réel | **0 €** |

---

## Limite connue (dette technique)

- Coût **estimé** backend uniquement — pas de rapprochement facture transporteur Postes Canada.
- Les AWB FedEx groupés ne doivent **pas** être reclassés Postes Canada : l'inférence par préfixe `Q013` isole correctement ces colis des colis FedEx (18 chiffres).
- Validation Marc : le périmètre et la qualité de `shipping_cost_eur` backend pour Postes Canada.

---

## Fichiers concernés

| Fichier | Rôle |
|---------|------|
| `definition/expressions.tmdl` | `fnNormaliserTransporteur`, `fnCanonTransporteur` |
| `definition/tables/fact_transport.tmdl` | Inférence + `source_cout` générique |
| `definition/tables/dim_transporteur.tmdl` | Référentiel statut intégration |

---

## Points de validation pour Marc (fin de mission)

- [ ] Confirmer que `shipping_cost_eur` backend est le bon proxy de coût pour Postes Canada
- [ ] Valider l'absence de dashboard/facture transporteur dédié (hors périmètre devis)
- [ ] Confirmer qu'aucun coût FedEx AWB groupé ne doit être ventilé sur les colis `Q013`
