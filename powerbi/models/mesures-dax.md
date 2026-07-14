# Mesures DAX — Lireka Power BI

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Référentiel des mesures DAX pour le dashboard profitabilité (J3).  
> Copier-coller dans Power BI Desktop → Modélisation → Nouvelle mesure.

---

## Coûts transport

```dax
Coût Transport Réel =
SUM(fact_transport[cout_transport])
```

> **Note** : le coût réel est porté par `fact_transport[cout_transport]` (grain colis).  
> Il n'existe **pas** de colonne `cout_transport_reel` sur `fact_commandes`.

```dax
Coût Transport Estimé =
SUM(fact_commandes[cout_transport_estime])
```

```dax
Écart Coût Transport = [Coût Transport Réel] - [Coût Transport Estimé]
```

```dax
Taux Écart Coût =
DIVIDE([Écart Coût Transport], [Coût Transport Estimé], 0)
```

```dax
Coût Moyen Colis =
DIVIDE([Coût Transport Réel], [Nb Colis], 0)
```

---

## Marge brute — PROVISOIRE (en attente validation Marc)

> **Ne pas utiliser comme formule définitive.**  
> Écart constaté le 12/07/2026 entre ce calcul simple et `gross_profit_eur` backend.  
> Décision métier requise avant branchement sur le rapport L04.

```dax
Marge Brute (prov.) =
[CA Total HT] - [Coût Achat Total] - [Coût Transport Réel]
```

```dax
Taux Marge Brute (prov.) =
DIVIDE([Marge Brute (prov.)], [CA Total HT], 0)
```

```dax
Marge Brute Backend (réf.) =
SUM(fact_commandes[gross_profit_eur])
```

```dax
Écart Marge vs Backend =
[Marge Brute (prov.)] - [Marge Brute Backend (réf.)]
```

```dax
Marge YTD (prov.) =
TOTALYTD([Marge Brute (prov.)], dim_date[date])
```

---

## Volumes

```dax
Nb Commandes =
COUNTROWS(fact_commandes)
```

```dax
Nb Colis =
COUNTROWS(fact_transport)
```

```dax
Nb Colis Facturés =
COUNTROWS(fact_factures_transport)
```

```dax
Panier Moyen =
DIVIDE([CA Total HT], [Nb Commandes], 0)
```

---

## Qualité données — coût transport par source

```dax
Nb Colis (coût réel) =
CALCULATE([Nb Colis], fact_transport[source_cout] = "reel")
```

```dax
Nb Colis (coût estimé) =
CALCULATE([Nb Colis], fact_transport[source_cout] = "estime")
```

```dax
Nb Colis (coût non disponible) =
CALCULATE([Nb Colis], fact_transport[source_cout] = "non_disponible")
```

---

## Qualité données — matching factures

```dax
Nb Commandes Matchées =
CALCULATE(
    DISTINCTCOUNT(fact_transport[order_id]),
    fact_transport[source_cout] = "reel"
)
```

```dax
Taux Matching =
DIVIDE([Nb Commandes Matchées], [Nb Commandes], 0)
```

> **Critère** : une commande est « matchée » si elle possède au moins un colis  
> avec `source_cout = "reel"` (facture Colissimo/Chronopost rapprochée via `id_package`).

```dax
Nb Commandes Non Matchées =
[Nb Commandes] - [Nb Commandes Matchées]
```

```dax
Nb Colis Avec Facture =
[Nb Colis (coût réel)]
```

```dax
Taux Matching Factures =
DIVIDE([Nb Colis Avec Facture], [Nb Colis], 0)
```

---

## Qualité données — intégrité et doublons

```dax
Lignes Colis par Facture (hors 1re) =
VAR T =
    ADDCOLUMNS(
        FILTER(
            VALUES(fact_factures_transport[numero_facture]),
            NOT ISBLANK(fact_factures_transport[numero_facture])
                && fact_factures_transport[numero_facture] <> ""
        ),
        "Cnt", CALCULATE(COUNTROWS(fact_factures_transport))
    )
RETURN
    SUMX(FILTER(T, [Cnt] > 1), [Cnt] - 1)
```

> **Lecture** : surplus de lignes par `numero_facture` (Chronopost multi-colis).  
> Valeur attendue ~3 019 — structure normale, pas un doublon qualité.

```dax
Vrais Doublons (Facture + Suivi) =
VAR T =
    ADDCOLUMNS(
        SUMMARIZE(
            fact_factures_transport,
            fact_factures_transport[numero_facture],
            fact_factures_transport[numero_suivi]
        ),
        "Cnt", CALCULATE(COUNTROWS(fact_factures_transport))
    )
RETURN
    SUMX(FILTER(T, [Cnt] > 1), [Cnt] - 1)
```

> **Lecture** : enregistrements réellement dupliqués sur la clé composite.  
> Valeur attendue sur l'entrepôt actuel : **0**.

```dax
Doublons Numero Suivi Factures =
VAR T =
    ADDCOLUMNS(
        VALUES(fact_factures_transport[numero_suivi]),
        "Cnt", CALCULATE(COUNTROWS(fact_factures_transport))
    )
RETURN
    SUMX(FILTER(T, [Cnt] > 1), [Cnt] - 1)
```

```dax
Commandes Sans Colis =
COUNTROWS(
    FILTER(
        fact_commandes,
        fact_commandes[state] <> "CANCELLED"
            && COUNTROWS(RELATEDTABLE(fact_transport)) = 0
    )
)
```

> **Périmètre** : commandes hors statut `CANCELLED` sans aucun colis dans `fact_transport`.  
> Valeur attendue sur l'entrepôt actuel : **162** (pas 83 402 qui inclut les CANCELLED).

```dax
Colis Sans Commande =
COUNTROWS(
    FILTER(
        fact_transport,
        ISBLANK(RELATED(fact_commandes[id_commande]))
    )
)
```

```dax
Lignes Facture Coût Transport Zero ou Null =
COUNTROWS(
    FILTER(
        fact_factures_transport,
        ISBLANK(fact_factures_transport[cout_transport])
            || fact_factures_transport[cout_transport] = 0
    )
)
```

---

## Temporelles

```dax
CA Total HT =
SUM(fact_commandes[ca_ht])
```

```dax
Coût Achat Total =
SUM(fact_commandes[cout_achat])
```

```dax
CA Mois Précédent =
CALCULATE([CA Total HT], DATEADD(dim_date[date], -1, MONTH))
```

```dax
Évolution CA =
DIVIDE([CA Total HT] - [CA Mois Précédent], [CA Mois Précédent], 0)
```

---

*Mesures alignées sur `_Mesures.tmdl` — 14/07/2026.*
