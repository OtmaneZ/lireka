# Mesures DAX — Lireka Power BI

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Référentiel des mesures DAX du dashboard profitabilité.  
> **Généré automatiquement** depuis `Lireka_Profitabilite.SemanticModel/definition/tables/_Mesures.tmdl`.  
> Ne pas éditer à la main : régénérer via le script one-shot (voir pied de page).

> Total : **46 mesures**, dans l'ordre du modèle.

---

## Nb Commandes

> Nombre de commandes (grain fact_commandes).  

```dax
Nb Commandes = COUNTROWS(fact_commandes)
```

*Format* : `#,##0`

---

## Nb Colis

> Nombre de colis (grain fact_transport).  

```dax
Nb Colis = COUNTROWS(fact_transport)
```

*Format* : `#,##0`

---

## Nb Colis (coût réel)

> Colis dont le coût provient d'une facture Colissimo/Chronopost rapprochée.  

```dax
Nb Colis (coût réel) = CALCULATE([Nb Colis], fact_transport[source_cout] = "facture_rapprochee")
```

*Format* : `#,##0`

---

## Nb Colis (coût estimé)

> Colis dont le coût provient du backend (shipping_cost_eur) sans facture transporteur.  

```dax
Nb Colis (coût estimé) = CALCULATE([Nb Colis], fact_transport[source_cout] = "backend_seul")
```

*Format* : `#,##0`

---

## Nb Colis (coût non disponible)

> Colis sans facture ni coût backend renseigné (visibles en volume, exclus du coût).  

```dax
Nb Colis (coût non disponible) = CALCULATE([Nb Colis], fact_transport[source_cout] = "aucun")
```

*Format* : `#,##0`

---

## Nb Colis Facturés

> Nombre de lignes de facture transporteur (Colissimo + Chronopost).  

```dax
Nb Colis Facturés = COUNTROWS(fact_factures_transport)
```

*Format* : `#,##0`

---

## Nb Articles

> Nombre d'articles commandés (somme des quantités).  

```dax
Nb Articles = SUM(fact_lignes[quantity])
```

*Format* : `#,##0`

---

## CA Total HT

> Chiffre d'affaires HT (order_amount_eur).  

```dax
CA Total HT = SUM(fact_commandes[ca_ht])
```

*Format* : `#,##0.00 €`

---

## Coût Achat Total

> Coût d'achat total des livres (product_cost_eur).  

```dax
Coût Achat Total = SUM(fact_commandes[cout_achat])
```

*Format* : `#,##0.00 €`

---

## Coût Transport Estimé

> Coût transport estimé par le backend (total_shipping_cost_to_delivery_country_eur).  

```dax
Coût Transport Estimé = SUM(fact_commandes[cout_transport_estime])
```

*Format* : `#,##0.00 €`

---

## Coût Transport Réel

> Coût transport réel, issu des colis backend (package.shipping_cost_eur).  

```dax
Coût Transport Réel = SUM(fact_transport[cout_transport])
```

*Format* : `#,##0.00 €`

---

## Coût Transport Facturé

> Coût transport facturé par Colissimo/Chronopost (contrôle croisé).  
> Fix F-06 : total facturé attribué au transporteur et à la date de la FACTURE elle-même  
> (chemin direct). Comme rel_factures_transporteur / rel_factures_date sont inactives, on  
> les active explicitement via USERELATIONSHIP et on coupe le chemin indirect (id_package)  
> avec CROSSFILTER pour éviter toute ambiguïté.  

```dax
Coût Transport Facturé =
CALCULATE(
    SUM(fact_factures_transport[cout_transport]),
    USERELATIONSHIP(fact_factures_transport[transporteur], dim_transporteur[transporteur]),
    USERELATIONSHIP(fact_factures_transport[date_facture], dim_date[date]),
    CROSSFILTER(fact_factures_transport[id_package], fact_transport[id_package], None)
)
```

*Format* : `#,##0.00 €`

---

## Écart Coût Outbound vs Estimé Backend

> Fix F-05 : écart entre le coût transport RETENU (facturé si dispo, sinon estimé) et  
> l'estimation backend commande. Remplace l'ancien [Écart Coût Transport] qui comparait  
> deux estimations backend (coût colis vs coût commande), sans valeur de pilotage.  

```dax
Écart Coût Outbound vs Estimé Backend =             [Coût Transport Outbound (Retenu)] - [Coût Transport Estimé]
```

*Format* : `#,##0.00 €`

---

## Taux Écart Coût

> Fix F-05 : écart coût outbound en % de l'estimé backend.  

```dax
Taux Écart Coût = DIVIDE([Écart Coût Outbound vs Estimé Backend], [Coût Transport Estimé], 0)
```

*Format* : `0.0%`

---

## Coût Moyen Colis

> Coût transport réel moyen par colis.  

```dax
Coût Moyen Colis = DIVIDE([Coût Transport Réel], [Nb Colis], 0)
```

*Format* : `#,##0.00 €`

---

## Mesures de marge

> **Mesure de référence** : `[Marge Brute]` — formule 7 postes **actée** par Marc Bordier
> (Slack, 13/07/2026 16h09). Voir [`project/perimetre-verrouille.md`](../../project/perimetre-verrouille.md).
> `[Marge Brute (prov.)]` est conservée comme mesure de **contrôle/comparaison** historique (3 postes).

## Marge Brute (prov.)

> **Mesure de contrôle/comparaison** — formule historique 3 postes (pré-Slack 13/07).
> Ne pas utiliser comme mesure de référence ; voir `[Marge Brute]` (section ci-dessous, après les postes).

```dax
Marge Brute (prov.) = [CA Total HT] - [Coût Achat Total] - [Coût Transport Réel]
```

*Format* : `#,##0.00 €`

---

## Taux Marge Brute (prov.)

> Taux de marge brute (provisoire) = Marge Brute (prov.) / CA HT.  

```dax
Taux Marge Brute (prov.) = DIVIDE([Marge Brute (prov.)], [CA Total HT], 0)
```

*Format* : `0.0%`

---

## Marge Brute Backend (réf.)

> Marge brute calculée par le backend (gross_profit_eur) — RÉFÉRENCE de contrôle.  

```dax
Marge Brute Backend (réf.) = SUM(fact_commandes[gross_profit_eur])
```

*Format* : `#,##0.00 €`

---

## Écart Marge vs Backend

> Écart entre la marge provisoire (3 postes) et la marge backend (contrôle historique).  

```dax
Écart Marge vs Backend = [Marge Brute (prov.)] - [Marge Brute Backend (réf.)]
```

*Format* : `#,##0.00 €`

---

## Frais Port Encaissés

```dax
Frais Port Encaissés = SUM(fact_commandes[frais_port_encaisse])
```

*Format* : `#,##0.00 €`

---

## Coût Transport Amont

> Fix F-04 : coût de transport amont (inbound_transportation_cost_eur).  

```dax
Coût Transport Amont = SUM(fact_commandes[cout_transport_amont])
```

*Format* : `#,##0.00 €`

---

## Coût Transport Outbound (Retenu)

> Fix F-02/F-04 : coût transport outbound RETENU (facturé si rapproché, sinon estimé backend).  

```dax
Coût Transport Outbound (Retenu) = SUM(fact_transport[cout_transport_retenu])
```

*Format* : `#,##0.00 €`

---

## Douanes Taxes

> Fix F-04 : douanes et taxes (duties_taxes_eur) — poste "duties and taxes" de la formule Marc.  

```dax
Douanes Taxes = SUM(fact_transport[duties_taxes_eur])
```

*Format* : `#,##0.00 €`

---

## Commissions Marketplace

> Fix F-04 : commissions marketplace (marketplace_fees_eur).  

```dax
Commissions Marketplace = SUM(fact_commandes[commissions_marketplace])
```

*Format* : `#,##0.00 €`

---

## Fournitures Expédition

> Fix F-04 : fournitures d'expédition (shipping_supply_cost_eur).  

```dax
Fournitures Expédition = SUM(fact_transport[shipping_supply_cost_eur])
```

*Format* : `#,##0.00 €`

---

## Marge Brute

> MARGE BRUTE — formule confirmée par Marc Bordier (Slack, 13/07/2026 16h09).
> Périmètre verrouillé : voir `project/perimetre-verrouille.md`.
> Shipping revenue inclus par défaut ; « if relevant » non tranché (AUDIT.md §6 Q1).

```dax
Marge Brute =
[CA Total HT] + [Frais Port Encaissés]
    - [Coût Achat Total]
    - [Coût Transport Amont]
    - [Coût Transport Outbound (Retenu)]
    - [Douanes Taxes]
    - [Commissions Marketplace]
    - [Fournitures Expédition]
```

*Format* : `#,##0.00 €`

---

## Taux Marge Brute

> Taux de marge brute = Marge Brute / (CA HT + frais de port encaissés).  

```dax
Taux Marge Brute = DIVIDE([Marge Brute], [CA Total HT] + [Frais Port Encaissés], 0)
```

*Format* : `0.0%`

---

## Écart Marge vs Backend (v2)

> Écart entre la marge actée (7 postes) et la marge backend (contrôle v2).  

```dax
Écart Marge vs Backend (v2) = [Marge Brute] - [Marge Brute Backend (réf.)]
```

*Format* : `#,##0.00 €`

---

## Nb Commandes Matchées

> Nombre de commandes ayant au moins un colis avec facture transporteur rapprochée (source_cout = facture_rapprochee).  

```dax
Nb Commandes Matchées = CALCULATE(DISTINCTCOUNT(fact_transport[order_id]), fact_transport[source_cout] = "facture_rapprochee")
```

*Format* : `#,##0`

---

## Taux Matching

> Taux de matching facture = commandes avec coût réel (facture) / total commandes.  

```dax
Taux Matching = DIVIDE([Nb Commandes Matchées], [Nb Commandes], 0)
```

*Format* : `0.0%`

---

## Nb Commandes Non Matchées

> Commandes sans aucun colis rapproché à une facture transporteur.  

```dax
Nb Commandes Non Matchées = [Nb Commandes] - [Nb Commandes Matchées]
```

*Format* : `#,##0`

---

## Coût Facturé Rapproché

> Coût facturé (Colissimo/Chronopost) rapproché du colis via la relation rel_factures_colis  
> (fact_factures_transport[id_package] -> fact_transport[id_package]), clé RÉSOLUE PAR DATE  
> dans la partition. Remplace l'ancien TREATAS sur numero_suivi, qui rattachait la facture  
> aux 2 colis d'un numéro de suivi recyclé (382 cas) => surcomptage.  
> Fix F-06 : coût facturé attribué au COLIS via rel_factures_colis (clé id_package résolue  
> par date). Relation active épinglée explicitement par USERELATIONSHIP plutôt que de  
> compter sur une relation active implicite. Distinct de [Coût Transport Facturé] qui, lui,  
> suit le chemin direct facture -> transporteur/date.  

```dax
Coût Facturé Rapproché =
CALCULATE(
    SUM(fact_factures_transport[cout_transport]),
    USERELATIONSHIP(fact_factures_transport[id_package], fact_transport[id_package])
)
```

*Format* : `#,##0.00 €`

---

## Écart Réel vs Facturé

> Écart entre le coût réel backend et le coût facturé transporteur (contrôle).  
> Fix F-06 : le terme facturé passe par le chemin id_package (via [Coût Facturé Rapproché]),  
> aligné au grain colis avec [Coût Transport Réel].  

```dax
Écart Réel vs Facturé = [Coût Transport Réel] - [Coût Facturé Rapproché]
```

*Format* : `#,##0.00 €`

---

## Nb Colis Avec Facture

> Nombre de colis rapprochés à une facture Colissimo/Chronopost (aligné sur source_cout = facture_rapprochee).  

```dax
Nb Colis Avec Facture = [Nb Colis (coût réel)]
```

*Format* : `#,##0`

---

## Taux Matching Factures

> Taux de rapprochement facture = colis avec facture / total colis.  

```dax
Taux Matching Factures = DIVIDE([Nb Colis Avec Facture], [Nb Colis], 0)
```

*Format* : `0.0%`

---

## Panier Moyen

> Panier moyen HT par commande.  

```dax
Panier Moyen = DIVIDE([CA Total HT], [Nb Commandes], 0)
```

*Format* : `#,##0.00 €`

---

## Poids Total (kg)

> Poids total expédié (kg).  

```dax
Poids Total (kg) = SUM(fact_transport[poids_kg])
```

*Format* : `#,##0.000`

---

## Marge YTD (prov.)

> Marge brute provisoire cumulée sur l'année (YTD).  

```dax
Marge YTD (prov.) = TOTALYTD([Marge Brute (prov.)], dim_date[date])
```

*Format* : `#,##0.00 €`

---

## CA Mois Précédent

> CA HT du mois précédent (time intelligence).  

```dax
CA Mois Précédent = CALCULATE([CA Total HT], DATEADD(dim_date[date], -1, MONTH))
```

*Format* : `#,##0.00 €`

---

## Évolution CA

> Évolution du CA vs mois précédent (%).  

```dax
Évolution CA = DIVIDE([CA Total HT] - [CA Mois Précédent], [CA Mois Précédent], 0)
```

*Format* : `0.0%`

---

## Lignes Colis par Facture (hors 1re)

> Chronopost : lignes au-delà de la 1re par numero_facture (grain multi-colis, pas un doublon qualité).  

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

*Format* : `#,##0`

---

## Vrais Doublons (Facture + Suivi)

> Vrais doublons qualité : même numero_facture ET même numero_suivi sur plusieurs lignes.  

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

*Format* : `#,##0`

---

## Doublons Numero Suivi Factures

> Lignes de facture dont numero_suivi apparaît plus d'une fois (surplus hors 1re occurrence).  

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

*Format* : `#,##0`

---

## Commandes Sans Colis

> Commandes hors CANCELLED sans aucun colis dans fact_transport (162 attendu sur entrepôt actuel).  

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

*Format* : `#,##0`

---

## Colis Sans Commande

> Colis dont order_id ne correspond à aucune commande (intégrité référentielle).  

```dax
Colis Sans Commande =
COUNTROWS(
    FILTER(
        fact_transport,
        ISBLANK(RELATED(fact_commandes[id_commande]))
    )
)
```

*Format* : `#,##0`

---

## Lignes Facture Coût Transport Zero ou Null

> Lignes de facture chargées avec cout_transport nul ou absent.  

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

*Format* : `#,##0`

---

*Mesures régénérées automatiquement depuis `_Mesures.tmdl` le 14/07/2026.*
