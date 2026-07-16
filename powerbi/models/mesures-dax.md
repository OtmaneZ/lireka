# Mesures DAX — Lireka Power BI

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Référentiel des mesures DAX pour le dashboard profitabilité (L04).  
> Aligné sur le modèle `Lireka_Profitabilite` et la table `_Mesures` (14/07/2026).

---

## Coûts transport

```dax
Coût Transport Réel =
SUM(fact_transport[cout_transport])
```

```dax
Coût Transport Estimé =
SUM(fact_commandes[cout_transport_estime])
```

```dax
Coût Transport Facturé =
SUM(fact_factures_transport[cout_transport])
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

## Marge brute (provisoire — en attente validation Marc)

```dax
CA Total HT =
SUM(fact_commandes[ca_ht])
```

```dax
Coût Achat Total =
SUM(fact_commandes[cout_achat])
```

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

```dax
Nb Colis Facturés =
COUNTROWS(fact_factures_transport)
```

```dax
Nb Articles =
SUM(fact_lignes[quantity])
```

```dax
Panier Moyen =
DIVIDE([CA Total HT], [Nb Commandes], 0)
```

---

## Qualité données / matching

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

```dax
Nb Commandes Non Matchées =
[Nb Commandes] - [Nb Commandes Matchées]
```

```dax
Commandes Sans Colis =
COUNTROWS(
    EXCEPT(
        VALUES(fact_commandes[id_commande]),
        VALUES(fact_transport[order_id])
    )
)
```

```dax
Colis Sans Commande =
COUNTROWS(
    EXCEPT(
        VALUES(fact_transport[order_id]),
        VALUES(fact_commandes[id_commande])
    )
)
```

---

## Par transporteur

Le transporteur est porté par `fact_transport` et `dim_transporteur` (pas de colonne transporteur sur `fact_commandes`).

```dax
Coût Transport par Transporteur =
CALCULATE(
    [Coût Transport Réel],
    ALLEXCEPT(fact_transport, fact_transport[transporteur])
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

```dax
Nb Colis par Transporteur =
CALCULATE(
    [Nb Colis],
    ALLEXCEPT(fact_transport, fact_transport[transporteur])
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
Marge YTD (prov.) =
TOTALYTD([Marge Brute (prov.)], dim_date[date])
```

---

*Mesures à valider avec les données réelles après refresh du modèle.*
