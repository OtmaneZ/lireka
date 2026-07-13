# Mesures DAX — Lireka Power BI

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Référentiel des mesures DAX pour le dashboard profitabilité (J3).  
> Copier-coller dans Power BI Desktop → Modélisation → Nouvelle mesure.

---

## Coûts transport

```dax
Coût Transport Réel =
SUMX(
    fact_commandes,
    COALESCE(fact_commandes[cout_transport_reel], 0)
)
```

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
DIVIDE([Coût Transport Réel], [Nb Commandes], 0)
```

---

## Marge brute

```dax
CA Total HT =
SUM(fact_commandes[ca_ht])
```

```dax
Coût Achat Total =
SUM(fact_commandes[cout_achat])
```

```dax
Marge Brute =
[CA Total HT] - [Coût Achat Total] - [Coût Transport Réel]
```

```dax
Taux Marge Brute =
DIVIDE([Marge Brute], [CA Total HT], 0)
```

```dax
Marge Brute Estimée =
[CA Total HT] - [Coût Achat Total] - [Coût Transport Estimé]
```

```dax
Écart Marge =
[Marge Brute] - [Marge Brute Estimée]
```

---

## Volumes

```dax
Nb Commandes =
COUNTROWS(fact_commandes)
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

## Qualité données

```dax
Nb Commandes Matchées =
COUNTROWS(
    FILTER(fact_commandes, NOT(ISBLANK(fact_commandes[cout_transport_reel])))
)
```

```dax
Taux Matching =
DIVIDE([Nb Commandes Matchées], [Nb Commandes], 0)
```

```dax
Nb Commandes Non Matchées =
[Nb Commandes] - [Nb Commandes Matchées]
```

---

## Par transporteur

```dax
Coût Transport par Transporteur =
CALCULATE(
    [Coût Transport Réel],
    ALLEXCEPT(fact_commandes, fact_commandes[transporteur])
)
```

```dax
Part Transporteur =
DIVIDE(
    [Coût Transport Réel],
    CALCULATE([Coût Transport Réel], ALL(dim_transporteur)),
    0
)
```

---

## Temporelles

```dax
CA Mois Précédent =
CALCULATE(
    [CA Total HT],
    DATEADD(dim_date[date], -1, MONTH)
)
```

```dax
Évolution CA =
DIVIDE([CA Total HT] - [CA Mois Précédent], [CA Mois Précédent], 0)
```

```dax
Marge YTD =
TOTALYTD([Marge Brute], dim_date[date])
```

---

## Colonne calculée — Coût transport réel (lookup)

```dax
cout_transport_reel =
VAR suivi = fact_commandes[numero_suivi]
RETURN
CALCULATE(
    SUM(fact_factures_transport[cout_transport]),
    FILTER(
        fact_factures_transport,
        fact_factures_transport[numero_suivi] = suivi
    )
)
```

---

*Mesures à tester et ajuster après intégration des données réelles.*
