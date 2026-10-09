# Mesures DAX — Lireka Power BI

> **Référence** : [`../../docs/01-cadrage/devis.md`](../../docs/01-cadrage/devis.md)  
> Référentiel des mesures DAX du dashboard profitabilité.  
> **Généré automatiquement** depuis `Lireka_Profitabilite.SemanticModel/definition/tables/_Mesures.tmdl`.  
> Ne pas éditer à la main : régénérer depuis `_Mesures.tmdl` (script one-shot).

> Total : **273 mesures**, dans l'ordre du modèle.

---

## Nb Commandes

> Nombre de commandes (grain fact_commandes), périmètre perimetre_volumes = "Oui" :  
> commandes avec CA + commandes annulées (les commandes actives sans montant de vente sont exclues).  

```dax
Nb Commandes =
IF(
    [_Allocation ligne active],
    CALCULATE(DISTINCTCOUNT(fact_lignes[order_id]), KEEPFILTERS(fact_commandes[perimetre_volumes] = "Oui")),
    CALCULATE(COUNTROWS(fact_commandes), KEEPFILTERS(fact_commandes[perimetre_volumes] = "Oui"))
)
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

## _Allocation ligne active

> Vrai si un filtre porte sur la langue du livre ou l'ISBN (fact_lignes) : les mesures socle  
> grain commande sont alors réparties par article (1/n de la commande par article,  
> fact_lignes[nb_articles_commande]). Sinon, agrégation commande directe.  

```dax
_Allocation ligne active = ISFILTERED(fact_lignes[langue_livre]) || ISFILTERED(fact_lignes[isbn])
```

---

## Nb commandes sans CA

> Nombre de commandes sans montant de vente EUR en base (ca_disponible = "Non").  
> Exclues du revenu, des coûts et de la marge.  

```dax
Nb commandes sans CA = CALCULATE(COUNTROWS(fact_commandes), KEEPFILTERS(fact_commandes[ca_disponible] = "Non"))
```

*Format* : `#,##0`

---

## Nb commandes canal non mappé

> Nombre de commandes dont la source n'est rattachée à aucun canal (canal "Other").  
> Ignore le filtre canal de la page : contrôle de la correspondance source -> canal.  

```dax
Nb commandes canal non mappé =
CALCULATE(
    COUNTROWS(fact_commandes),
    REMOVEFILTERS(dim_type_commande),
    dim_type_commande[canal] = "Other"
)
```

*Format* : `#,##0`

---

## _PY incomplet

> Vrai si plus de 5 % des commandes non annulées de la période N-1 n'ont pas de montant de vente  
> (ca_disponible = "Non"). Rend vides les PY / YoY de revenu, de marge, de coûts et de volumes :  
> une comparaison à une période N-1 incomplète surestimerait la croissance.  

```dax
_PY incomplet =
VAR seuil = 0.05
VAR total =
    CALCULATE(
        COUNTROWS(fact_commandes),
        SAMEPERIODLASTYEAR(dim_date[date]),
        KEEPFILTERS(fact_commandes[state] <> "CANCELLED")
    )
VAR sansCA =
    CALCULATE(
        COUNTROWS(fact_commandes),
        SAMEPERIODLASTYEAR(dim_date[date]),
        KEEPFILTERS(fact_commandes[state] <> "CANCELLED"),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Non")
    )
RETURN DIVIDE(sansCA, total) > seuil
```

---

## Avertissement — commandes sans CA

> Bandeau Marketplaces : commandes exclues faute de montant de vente en base ("" si aucune).  

```dax
Avertissement — commandes sans CA =
VAR n = [Nb commandes sans CA]
RETURN
    IF(
        n > 0,
        "Excluded from all figures: " & FORMAT(n, "#,##0", "en-US") & " orders ("
            & FORMAT(DIVIDE(n, CALCULATE(COUNTROWS(fact_commandes), KEEPFILTERS(fact_commandes[state] <> "CANCELLED"))), "0.0%", "en-US")
            & ") with no sales amount in the source data",
        ""
    )
```

---

## Avertissement — données

> Bandeau General View : commandes sans CA + canal non mappé + filtre langue ("" si rien à signaler).  

```dax
Avertissement — données =
VAR a = [Avertissement — commandes sans CA]
VAR m = [Nb commandes canal non mappé]
VAR b = IF(m > 0, FORMAT(m, "#,##0", "en-US") & " orders from unmapped sales channels excluded from all pages", "")
VAR c = [Avertissement — langue]
VAR ab = a & IF(a <> "" && b <> "", "  |  ", "") & b
RETURN ab & IF(ab <> "" && c <> "", "  |  ", "") & c
```

---

## Avertissement — langue

> Texte affiché quand la langue du livre est filtrée : les montants commande sont alors répartis  
> à parts égales entre les livres de chaque commande ([_Allocation ligne active]).  

```dax
Avertissement — langue = IF(ISFILTERED(fact_lignes[langue_livre]), "Language filter: amounts split per book", "")
```

---

## Avertissement — Marketplaces

> Bandeau Marketplaces : commandes sans CA + filtre langue ("" si rien à signaler).  

```dax
Avertissement — Marketplaces =
VAR a = [Avertissement — commandes sans CA]
VAR c = [Avertissement — langue]
RETURN a & IF(a <> "" && c <> "", "  |  ", "") & c
```

---

## Dernière date de données

> Date de la dernière commande avec CA dans le modèle (ignore tous les filtres).  

```dax
Dernière date de données =
CALCULATE(
    MAX(fact_commandes[date_commande]),
    REMOVEFILTERS(),
    fact_commandes[ca_disponible] = "Oui"
)
```

*Format* : `dd/mm/yyyy`

---

## Fraîcheur des données

> Carte de fraîcheur (rail gauche de chaque page) : "Data through 07 Oct 2026",  
> complétée de l'âge des données si elles ont plus d'un jour.  

```dax
Fraîcheur des données =
VAR d = [Dernière date de données]
VAR age = DATEDIFF(d, TODAY(), DAY)
RETURN
    IF(
        ISBLANK(d),
        "No data",
        "Data through " & FORMAT(d, "dd mmm yyyy", "en-US")
            & IF(age > 1, " (" & age & " days ago)", "")
    )
```

---

## Libellé période

> Période affichée (dates min / max du contexte, bornées à la dernière donnée) : "17 Jun 2025 – 16 Jun 2026".  

```dax
Libellé période =
VAR d1 = MIN(dim_date[date])
VAR dmax = [Dernière date de données]
VAR d2 = MIN(MAX(dim_date[date]), dmax)
RETURN
    IF(
        ISBLANK(d1) || d1 > d2,
        "No data",
        FORMAT(d1, "dd mmm yyyy", "en-US") & " – " & FORMAT(d2, "dd mmm yyyy", "en-US")
    )
```

---

## Titre — Profit bridge

> Titre dynamique du waterfall Profit bridge.  

```dax
Titre — Profit bridge = "Gross Profit bridge, " & [Libellé période] & " vs same period prior year"
```

---

## Unités commandées (avec CA)

> Unités commandées des commandes avec CA : dénominateur des ratios par unité.  

```dax
Unités commandées (avec CA) = CALCULATE([Unités commandées], KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
```

*Format* : `#,##0`

---

## Coût Transport Outbound (tous colis)

> Page Transport : coût outbound de tous les colis (vue transporteurs), sans filtre ca_disponible.  

```dax
Coût Transport Outbound (tous colis) = SUM(fact_transport[cout_transport_retenu])
```

*Format* : `€#,##0`

---

## Coût Transport Outbound (tous colis) PY

```dax
Coût Transport Outbound (tous colis) PY = CALCULATE([Coût Transport Outbound (tous colis)], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `€#,##0`

---

## Coût Transport Outbound (tous colis) YoY %

```dax
Coût Transport Outbound (tous colis) YoY % = DIVIDE([Coût Transport Outbound (tous colis)] - [Coût Transport Outbound (tous colis) PY], [Coût Transport Outbound (tous colis) PY])
```

*Format* : `0.0%`

---

## Douanes Taxes (tous colis)

> Page Transport : droits et taxes de tous les colis, sans filtre ca_disponible.  

```dax
Douanes Taxes (tous colis) = SUM(fact_transport[duties_taxes_eur])
```

*Format* : `€#,##0`

---

## Douanes Taxes (tous colis) YoY %

```dax
Douanes Taxes (tous colis) YoY % =
VAR py = CALCULATE([Douanes Taxes (tous colis)], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN DIVIDE([Douanes Taxes (tous colis)] - py, py)
```

*Format* : `0.0%`

---

## Fournitures Expédition (tous colis)

> Page Transport : fournitures d'expédition de tous les colis, sans filtre ca_disponible.  

```dax
Fournitures Expédition (tous colis) = SUM(fact_transport[shipping_supply_cost_eur])
```

*Format* : `€#,##0`

---

## Nb Articles

> Fix Bloc2 — grain passé de groupe/titre à article physique le 15/07/2026.  
> Périmètre perimetre_volumes = "Oui" (même périmètre que [Nb Commandes]).  
> Ancienne mesure basée sur SUM(quantity_groupe) déduplicable en contrôle si besoin,  
> voir [Nb Articles (contrôle grain groupe)].  

```dax
Nb Articles =
CALCULATE(COUNTROWS(fact_lignes), KEEPFILTERS(fact_commandes[perimetre_volumes] = "Oui"))
```

*Format* : `#,##0`

---

## Nb Articles (contrôle grain groupe)

> Contrôle Bloc2 — recalcule l'ancien total par somme des quantity_groupe distincts par groupe.  

```dax
Nb Articles (contrôle grain groupe) =
SUMX(
    VALUES(fact_lignes[item_group_id]),
    CALCULATE(MAX(fact_lignes[quantity_groupe]))
)
```

*Format* : `#,##0`

---

## Nb Articles Annulés

> Granularité Bloc2 — articles dont internal_state = CANCELLED (pas la logique de marge Bloc 3).  

```dax
Nb Articles Annulés = CALCULATE([Nb Articles], fact_lignes[internal_state] = "CANCELLED")
```

*Format* : `#,##0`

---

## CA Total HT (grain article, ajusté annulation)

> Bloc3 — CA HT au grain article, zéro sur les lignes annulées (avant ET après expédition).  
> Remplace fact_commandes[ca_ht] pour la logique de marge Bloc 3 : zéro appliqué au grain  
> article, pas commande, pour gérer les annulations partielles (~8 900 commandes, audit 15/07/2026).  

```dax
CA Total HT (grain article, ajusté annulation) =
CALCULATE(
    SUMX(
        fact_lignes,
        IF(
            fact_lignes[statut_annulation_ligne] = "NON_ANNULE",
            fact_lignes[customer_price_per_item_eur],
            0
        )
    ),
    KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
)
```

*Format* : `€#,##0`

---

## Coût Achat Total (grain article)

> Bloc3 — coût d'achat au grain article. Aligné sur la décision Marc 25/08/2026 :  
> 0 si la commande (fact_commandes[state]) est CANCELLED ; inchangé sinon  
> (y compris articles CANCELLED d'une commande encore active = annulation partielle).  
> Contrôle vs [Coût Achat Total] (grain commande).  

```dax
Coût Achat Total (grain article) =
VAR cogsActif =
    CALCULATE(
        SUM(fact_lignes[product_cost_eur]),
        KEEPFILTERS(fact_commandes[state] <> "CANCELLED"),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    )
RETURN IF(ISBLANK(cogsActif), 0, cogsActif)
```

*Format* : `€#,##0`

---

## Nb Articles Annulés Avant Expédition

> Bloc3 — articles annulés avant expédition (proxy package_id null).  

```dax
Nb Articles Annulés Avant Expédition = CALCULATE([Nb Articles], fact_lignes[statut_annulation_ligne] = "ANNULE_AVANT_EXPEDITION")
```

*Format* : `#,##0`

---

## Nb Articles Annulés Après Expédition

> Bloc3 — articles annulés après expédition (proxy package_id non-null).  

```dax
Nb Articles Annulés Après Expédition = CALCULATE([Nb Articles], fact_lignes[statut_annulation_ligne] = "ANNULE_APRES_EXPEDITION")
```

*Format* : `#,##0`

---

## Marge Brute (grain article, prov.)

> Bloc3 — marge brute provisoire au grain article (contrôle/comparaison uniquement).  
> Ne remplace pas [Marge Brute] tant que les Blocs 5 (returns/generic costs) ne sont pas  
> intégrés au même grain. Ne pas publier dans le rapport final sans validation Marc.  

```dax
Marge Brute (grain article, prov.) = [CA Total HT (grain article, ajusté annulation)] - [Coût Achat Total (grain article)]
```

*Format* : `€#,##0`

---

## CA Total HT

> Chiffre d'affaires HT (order_amount_eur).  

```dax
CA Total HT =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[ca_ht]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[ca_ht]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## CA Total HT (reconstruit)

> CA HT des commandes avec CA (ca_ht_reconstruit = order_amount_eur depuis la neutralisation du  
> fallback FX du 19/07/2026 ; aucune conversion de devise). Base des mesures publiées « (reconstruit) ».  

```dax
CA Total HT (reconstruit) =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[ca_ht_reconstruit]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[ca_ht_reconstruit]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## CA HT Net Annulation

> Bloc3 (grain commande) — CA HT hors commandes annulées.  
> Applique la règle Marc "CA=0 sur annulation" au grain commande.  
> Ne capture PAS les annulations partielles (state <> CANCELLED, ~8 900 cmd,  
> borne CA cf. limite-etf-annulation.md) — limite connue documentée.  

```dax
CA HT Net Annulation = CALCULATE([CA Total HT], fact_commandes[state] <> "CANCELLED")
```

*Format* : `€#,##0`

---

## CA HT Net Annulation (reconstruit)

> Bloc3 (grain commande) — CA HT reconstruit hors commandes annulées.  

```dax
CA HT Net Annulation (reconstruit) = CALCULATE([CA Total HT (reconstruit)], fact_commandes[state] <> "CANCELLED")
```

*Format* : `€#,##0`

---

## CA Commandes Annulation Partielle

> Bloc3 (grain commande) — transparence : CA porté par les commandes en annulation  
> partielle (state <> CANCELLED mais ≥1 article CANCELLED). Non ajusté faute de prix ligne.  
> Identification via rel_lignes_commandes (pas de colonne calculée fact_commandes).  

```dax
CA Commandes Annulation Partielle =
CALCULATE(
    [CA Total HT],
    FILTER(
        fact_commandes,
        fact_commandes[state] <> "CANCELLED"
            && COUNTROWS(
                FILTER(
                    RELATEDTABLE(fact_lignes),
                    fact_lignes[internal_state] = "CANCELLED"
                )
            ) > 0
            && COUNTROWS(
                FILTER(
                    RELATEDTABLE(fact_lignes),
                    fact_lignes[internal_state] <> "CANCELLED"
                )
            ) > 0
    )
)
```

*Format* : `€#,##0`

---

## Coût Achat Total

> Coût d'achat total des livres (product_cost_eur), net annulation.  
> Décision Marc 25/08/2026 : COGS = 0 (pas BLANK) si state = CANCELLED — la vente  
> n'a pas eu lieu. Commandes actives inchangées (SUM de cout_achat_net).  

```dax
Coût Achat Total =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[cout_achat_net]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[cout_achat_net]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Coût Transport Estimé

> Coût transport estimé par le backend (total_shipping_cost_to_delivery_country_eur).  

```dax
Coût Transport Estimé = SUM(fact_commandes[cout_transport_estime])
```

*Format* : `€#,##0`

---

## Coût Transport Réel

> Coût transport ESTIMÉ par le backend sur les colis (package.shipping_cost_eur) — contrôle.  

```dax
Coût Transport Réel = SUM(fact_transport[cout_transport])
```

*Format* : `€#,##0`

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

*Format* : `€#,##0`

---

## Écart Coût Outbound vs Estimé Backend

> Fix F-05 : écart entre le coût transport RETENU (facturé si dispo, sinon estimé) et  
> l'estimation backend commande. Remplace l'ancien [Écart Coût Transport] qui comparait  
> deux estimations backend (coût colis vs coût commande), sans valeur de pilotage.  

```dax
Écart Coût Outbound vs Estimé Backend = [Coût Transport Outbound (Retenu)] - [Coût Transport Estimé]
```

*Format* : `€#,##0`

---

## Taux Écart Coût

> Fix F-05 : écart coût outbound en % de l'estimé backend.  

```dax
Taux Écart Coût = DIVIDE([Écart Coût Outbound vs Estimé Backend], [Coût Transport Estimé], 0)
```

*Format* : `0.0%`

---

## Coût Moyen Colis

> Coût outbound moyen par colis (facturé si rapproché, sinon estimé) : même base que la colonne Outbound de la page Transport.  

```dax
Coût Moyen Colis =
DIVIDE([Coût Transport Outbound (tous colis)], [Nb Colis])
```

*Format* : `€#,##0.00`

---

## Marge Brute (prov.)

> MARGE BRUTE — FORMULE PROVISOIRE. CA HT - coût d'achat - coût transport réel.  
> Écart constaté le 12/07/2026 entre ce calcul simple et gross_profit_eur existant.  
> À VALIDER avec Marc / finance avant de considérer comme définitive.  

```dax
Marge Brute (prov.) = [CA Total HT] - [Coût Achat Total] - [Coût Transport Réel]
```

*Format* : `€#,##0`

---

## Marge Brute Backend (réf.)

> Marge brute calculée par le backend (gross_profit_eur) — RÉFÉRENCE de contrôle.  

```dax
Marge Brute Backend (réf.) = SUM(fact_commandes[gross_profit_eur])
```

*Format* : `€#,##0`

---

## Écart Marge vs Backend

> Écart entre la marge provisoire et la marge backend (aide à la validation finance).  

```dax
Écart Marge vs Backend = [Marge Brute (prov.)] - [Marge Brute Backend (réf.)]
```

*Format* : `€#,##0`

---

## Frais Port Encaissés

> Fix F-04 : frais de port encaissés par le client (marketplace notamment).  
> Inclus dans le revenu publié (hors CANCELLED) — formule Marc.  

```dax
Frais Port Encaissés =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[frais_port_encaisse]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[frais_port_encaisse]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Coût Transport Amont

> Fix F-04 : coût de transport amont (inbound_transportation_cost_eur).  
> Pas de filtre CANCELLED — décision Marc 25/08/2026 : conserver 100 % quel que  
> soit le statut (marchandise déjà acheminée jusqu'à Grenoble). Un 0 affiché est  
> un 0 source (inbound_transportation_cost_eur = 0 depuis 2022), pas une exclusion.  

```dax
Coût Transport Amont =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[cout_transport_amont]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[cout_transport_amont]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Coût Transport Outbound (Retenu)

> Fix F-02/F-04 : coût transport outbound RETENU (facturé si rapproché, sinon estimé backend).  
> Grain colis (fact_transport). Décision Marc 25/08/2026 : sur CANCELLED, n'inclure  
> que si la commande a quand même été expédiée — déjà le cas : pas de colis = 0 ;  
> colis présent (proxy package_id / 243 cmd CANCELLED avec package) = coût conservé.  
> Pas de filtre state : un filtre CANCELLED exclurait à tort les expédiées-puis-annulées.  

```dax
Coût Transport Outbound (Retenu) =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[cout_transport_retenu_cmd]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE([Coût Transport Outbound (tous colis)], KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Douanes Taxes

> Fix F-04 : douanes et taxes (duties_taxes_eur) — poste "duties and taxes" de la formule Marc.  

```dax
Douanes Taxes =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[duties_taxes_cmd]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE([Douanes Taxes (tous colis)], KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Commissions Marketplace

> Fix F-04 : commissions marketplace (marketplace_fees_eur).  

```dax
Commissions Marketplace =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[commissions_marketplace]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[commissions_marketplace]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Fournitures Expédition

> Fix F-04 : fournitures d'expédition (shipping_supply_cost_eur).  

```dax
Fournitures Expédition =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[fournitures_cmd]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE([Fournitures Expédition (tous colis)], KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Retours Remboursements

> Bloc5 (dette technique) — retours et remboursements (returns_and_refunds_cost_eur,  
> agrégé par commande). Décision Marc 25/08/2026 : inclure uniquement si la commande  
> a été remboursée — proxifié par le montant (pas de flag « refunded » distinct dans  
> le modèle). SUM du champ = 0 si non remboursé, montant réel sinon ; pas de filtre  
> CANCELLED. Double comptage vs COGS sur annulation clos : [Coût Achat Total] = 0  
> si state = CANCELLED. Poste below-the-line pour [Marge Brute (reconstruit)].  

```dax
Retours Remboursements =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[retours_remboursements]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[retours_remboursements]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Coûts Génériques

> Bloc5 (dette technique) — coûts génériques (generic_costs_eur, agrégé par commande).  
> Hors marge brute publiée (below-the-line, profit bridge et tableaux P&L uniquement).  

```dax
Coûts Génériques =
IF(
    [_Allocation ligne active],
    CALCULATE(
        SUMX(fact_lignes, DIVIDE(RELATED(fact_commandes[couts_generiques]), fact_lignes[nb_articles_commande])),
        KEEPFILTERS(fact_commandes[ca_disponible] = "Oui")
    ),
    CALCULATE(SUM(fact_commandes[couts_generiques]), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `€#,##0`

---

## Marge Brute

> CONTRÔLE — marge APRÈS retours et coûts génériques (Bloc 5). Ce n'est PAS la marge publiée :  
> la formule validée par Marc exclut retours et génériques, voir [Marge Brute (reconstruit)].  
> Historique : formule Slack 13/07/2026 16h09 + Bloc 5,  
> COGS sur annulation mis à jour (Marc, 25/08/2026) : [Coût Achat Total] = 0 si  
> state = CANCELLED. Revenu = CA hors commandes annulées. Transport amont conservé  
> 100 %. Outbound via colis (inclus seulement si expédiée). Frais de port encaissés  
> exclus sur CANCELLED. Annulations partielles non ajustées (~8 900 cmd, limite  
> connue — voir docs/notes-techniques/limite-etf-annulation.md).  
> Grain article [Marge Brute (grain article, prov.)] conservé comme contrôle et chemin de  
> bascule si customer_price_per_item_eur devient disponible par ligne.  
> Revenue (incl. shipping revenue if relevant) - COGS - Inbound transportation costs  
> - Outbound transportation costs - Duties and Taxes - Marketplace commission fees  
> - Shipping supplies - Returns/refunds - Generic costs.  
> Retours/remboursements + coûts génériques inclus (Bloc 5, dette technique provisoire —  
> Marc doit revoir total_generic_costs_eur). Double comptage returns vs COGS sur  
> CANCELLED clos (COGS neutralisé). Grain commande.  

```dax
Marge Brute =
[CA HT Net Annulation]
    + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
    - [Coût Achat Total]
    - [Coût Transport Amont]
    - [Coût Transport Outbound (Retenu)]
    - [Douanes Taxes]
    - [Commissions Marketplace]
    - [Fournitures Expédition]
    - [Retours Remboursements]
    - [Coûts Génériques]
```

*Format* : `€#,##0`

---

## Taux Marge Brute

> Fix F-04 / C-01 : taux = Marge Brute / revenu net annulation  
> ([CA HT Net Annulation] + frais port hors CANCELLED) — même périmètre que [Marge Brute].  

```dax
Taux Marge Brute =
DIVIDE(
    [Marge Brute],
    [CA HT Net Annulation]
        + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED"),
    0
)
```

*Format* : `0.0%`

---

## Écart Marge vs Backend (v2)

> Fix F-04 : écart entre la marge conforme Marc et la marge backend (contrôle v2).  

```dax
Écart Marge vs Backend (v2) = [Marge Brute] - [Marge Brute Backend (réf.)]
```

*Format* : `€#,##0`

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
> (fact_factures_transport[id_package] -> fact_transport[id_package]), package_id fourni par  
> le backend (v_carrier_invoice_lines) : plus de rapprochement par numéro de suivi ni par date.  
> Fix F-06 : coût facturé attribué au COLIS via rel_factures_colis. Relation active épinglée explicitement par USERELATIONSHIP plutôt que de  
> compter sur une relation active implicite. Distinct de [Coût Transport Facturé] qui, lui,  
> suit le chemin direct facture -> transporteur/date.  

```dax
Coût Facturé Rapproché =
CALCULATE(
    SUM(fact_factures_transport[cout_transport]),
    USERELATIONSHIP(fact_factures_transport[id_package], fact_transport[id_package])
)
```

*Format* : `€#,##0`

---

## Écart Réel vs Facturé

> Écart entre le coût réel backend et le coût facturé transporteur (contrôle).  
> Fix F-06 : le terme facturé passe par le chemin id_package (via [Coût Facturé Rapproché]),  
> aligné au grain colis avec [Coût Transport Réel].  

```dax
Écart Réel vs Facturé = [Coût Transport Réel] - [Coût Facturé Rapproché]
```

*Format* : `€#,##0`

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
Taux Matching Factures =
DIVIDE([Nb Colis Avec Facture], [Nb Colis])
```

*Format* : `0.0%`

---

## Panier Moyen

> Panier moyen HT par commande.  

```dax
Panier Moyen = DIVIDE([CA Total HT], [Nb Commandes], 0)
```

*Format* : `€#,##0.00`

---

## Poids Total (kg)

> Poids total expédié (kg).  

```dax
Poids Total (kg) = SUM(fact_transport[poids_kg])
```

*Format* : `#,##0`

---

## CA Mois Précédent

> CA HT du mois précédent (time intelligence).  

```dax
CA Mois Précédent = CALCULATE([CA Total HT], DATEADD(dim_date[date], -1, MONTH))
```

*Format* : `€#,##0`

---

## Évolution CA

> Évolution du CA vs mois précédent (%).  

```dax
Évolution CA = DIVIDE([CA Total HT] - [CA Mois Précédent], [CA Mois Précédent], 0)
```

*Format* : `0.0%`

---

## Colis Order ID Manquant

> Colis sans order_id renseigné.  

```dax
Colis Order ID Manquant = CALCULATE([Nb Colis], ISBLANK(fact_transport[order_id]))
```

*Format* : `#,##0`

---

## Commandes Code Pays Non Attribué

> Commandes dont le code pays est "??" (destination_country absent).  

```dax
Commandes Code Pays Non Attribué = CALCULATE([Nb Commandes], fact_commandes[code_pays] = "??")
```

*Format* : `#,##0`

---

## Commandes Sans Colis

> Commandes hors CANCELLED sans aucun colis dans fact_transport .  

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

## Unités commandées

> Bloc 8 — KPI Finance + time intelligence YoY (SAMEPERIODLASTYEAR).  
> Prérequis : dim_date continue depuis 2020. DIVIDE sans 3e arg → BLANK  
> si dénominateur PY nul / absent.  
> Finance KPI — Ordered Units (alias [Nb Articles], grain article / date_commande).  

```dax
Unités commandées = [Nb Articles]
```

*Format* : `#,##0`

---

## Revenu

> Finance KPI — Revenue = CA produit net annulation + frais de port (hors CANCELLED).  
> Aligné sur le dénominateur de [Taux Marge Brute].  

```dax
Revenu =
[CA HT Net Annulation]
    + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
```

*Format* : `€#,##0`

---

## Unités commandées PY

> --- KPI cards : Unités commandées (Ordered Units) ---  

```dax
Unités commandées PY = IF([_PY incomplet], BLANK(), CALCULATE([Unités commandées], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `#,##0`

---

## Unités commandées YoY Δ

```dax
Unités commandées YoY Δ = [Unités commandées] - [Unités commandées PY]
```

*Format* : `#,##0`

---

## Unités commandées YoY %

```dax
Unités commandées YoY % = DIVIDE([Unités commandées] - [Unités commandées PY], [Unités commandées PY])
```

*Format* : `0.0%`

---

## Revenu PY

> --- KPI cards : Revenu (Revenue) ---  

```dax
Revenu PY = IF([_PY incomplet], BLANK(), CALCULATE([Revenu], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Revenu YoY Δ

```dax
Revenu YoY Δ = [Revenu] - [Revenu PY]
```

*Format* : `€#,##0`

---

## Revenu YoY %

```dax
Revenu YoY % = DIVIDE([Revenu] - [Revenu PY], [Revenu PY])
```

*Format* : `0.0%`

---

## Marge Brute PY

> --- KPI cards : Marge Brute (Gross Profit) ---  

```dax
Marge Brute PY = IF([_PY incomplet], BLANK(), CALCULATE([Marge Brute], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Marge Brute YoY Δ

```dax
Marge Brute YoY Δ = [Marge Brute] - [Marge Brute PY]
```

*Format* : `€#,##0`

---

## Marge Brute YoY %

```dax
Marge Brute YoY % =
DIVIDE([Marge Brute] - [Marge Brute PY], ABS([Marge Brute PY]))
```

*Format* : `0.0%`

---

## Taux Marge Brute PY

> --- KPI cards : Taux Marge Brute (Gross Margin %) — YoY en bps, pas en % ---  

```dax
Taux Marge Brute PY = IF([_PY incomplet], BLANK(), CALCULATE([Taux Marge Brute], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `0.0%`

---

## Taux Marge Brute YoY bps

```dax
Taux Marge Brute YoY bps = ([Taux Marge Brute] - [Taux Marge Brute PY]) * 10000
```

*Format* : `#,##0`

---

## Nb Commandes PY

> --- Tableaux détaillés P&L : même logique PY / YoY Δ / YoY % ---  

```dax
Nb Commandes PY = IF([_PY incomplet], BLANK(), CALCULATE([Nb Commandes], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `#,##0`

---

## Nb Commandes YoY Δ

```dax
Nb Commandes YoY Δ = [Nb Commandes] - [Nb Commandes PY]
```

*Format* : `#,##0`

---

## Nb Commandes YoY %

```dax
Nb Commandes YoY % = DIVIDE([Nb Commandes] - [Nb Commandes PY], [Nb Commandes PY])
```

*Format* : `0.0%`

---

## CA HT Net Annulation PY

```dax
CA HT Net Annulation PY = IF([_PY incomplet], BLANK(), CALCULATE([CA HT Net Annulation], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## CA HT Net Annulation YoY Δ

```dax
CA HT Net Annulation YoY Δ = [CA HT Net Annulation] - [CA HT Net Annulation PY]
```

*Format* : `€#,##0`

---

## CA HT Net Annulation YoY %

```dax
CA HT Net Annulation YoY % = DIVIDE([CA HT Net Annulation] - [CA HT Net Annulation PY], [CA HT Net Annulation PY])
```

*Format* : `0.0%`

---

## Frais Port Encaissés PY

```dax
Frais Port Encaissés PY = IF([_PY incomplet], BLANK(), CALCULATE([Frais Port Encaissés], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Frais Port Encaissés YoY Δ

```dax
Frais Port Encaissés YoY Δ = [Frais Port Encaissés] - [Frais Port Encaissés PY]
```

*Format* : `€#,##0`

---

## Frais Port Encaissés YoY %

```dax
Frais Port Encaissés YoY % = DIVIDE([Frais Port Encaissés] - [Frais Port Encaissés PY], [Frais Port Encaissés PY])
```

*Format* : `0.0%`

---

## Coût Achat Total PY

```dax
Coût Achat Total PY = IF([_PY incomplet], BLANK(), CALCULATE([Coût Achat Total], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Coût Achat Total YoY Δ

```dax
Coût Achat Total YoY Δ = [Coût Achat Total] - [Coût Achat Total PY]
```

*Format* : `€#,##0`

---

## Coût Achat Total YoY %

```dax
Coût Achat Total YoY % = DIVIDE([Coût Achat Total] - [Coût Achat Total PY], [Coût Achat Total PY])
```

*Format* : `0.0%`

---

## Coût Transport Amont PY

```dax
Coût Transport Amont PY = IF([_PY incomplet], BLANK(), CALCULATE([Coût Transport Amont], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Coût Transport Amont YoY Δ

```dax
Coût Transport Amont YoY Δ = [Coût Transport Amont] - [Coût Transport Amont PY]
```

*Format* : `€#,##0`

---

## Coût Transport Amont YoY %

```dax
Coût Transport Amont YoY % = DIVIDE([Coût Transport Amont] - [Coût Transport Amont PY], [Coût Transport Amont PY])
```

*Format* : `0.0%`

---

## Coût Transport Outbound (Retenu) PY

```dax
Coût Transport Outbound (Retenu) PY = IF([_PY incomplet], BLANK(), CALCULATE([Coût Transport Outbound (Retenu)], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Coût Transport Outbound (Retenu) YoY Δ

```dax
Coût Transport Outbound (Retenu) YoY Δ = [Coût Transport Outbound (Retenu)] - [Coût Transport Outbound (Retenu) PY]
```

*Format* : `€#,##0`

---

## Coût Transport Outbound (Retenu) YoY %

```dax
Coût Transport Outbound (Retenu) YoY % = DIVIDE([Coût Transport Outbound (Retenu)] - [Coût Transport Outbound (Retenu) PY], [Coût Transport Outbound (Retenu) PY])
```

*Format* : `0.0%`

---

## Douanes Taxes PY

```dax
Douanes Taxes PY = IF([_PY incomplet], BLANK(), CALCULATE([Douanes Taxes], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Douanes Taxes YoY Δ

```dax
Douanes Taxes YoY Δ = [Douanes Taxes] - [Douanes Taxes PY]
```

*Format* : `€#,##0`

---

## Douanes Taxes YoY %

```dax
Douanes Taxes YoY % = DIVIDE([Douanes Taxes] - [Douanes Taxes PY], [Douanes Taxes PY])
```

*Format* : `0.0%`

---

## Commissions Marketplace PY

```dax
Commissions Marketplace PY = IF([_PY incomplet], BLANK(), CALCULATE([Commissions Marketplace], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Commissions Marketplace YoY Δ

```dax
Commissions Marketplace YoY Δ = [Commissions Marketplace] - [Commissions Marketplace PY]
```

*Format* : `€#,##0`

---

## Commissions Marketplace YoY %

```dax
Commissions Marketplace YoY % = DIVIDE([Commissions Marketplace] - [Commissions Marketplace PY], [Commissions Marketplace PY])
```

*Format* : `0.0%`

---

## Fournitures Expédition PY

```dax
Fournitures Expédition PY = IF([_PY incomplet], BLANK(), CALCULATE([Fournitures Expédition], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Fournitures Expédition YoY Δ

```dax
Fournitures Expédition YoY Δ = [Fournitures Expédition] - [Fournitures Expédition PY]
```

*Format* : `€#,##0`

---

## Fournitures Expédition YoY %

```dax
Fournitures Expédition YoY % = DIVIDE([Fournitures Expédition] - [Fournitures Expédition PY], [Fournitures Expédition PY])
```

*Format* : `0.0%`

---

## Retours Remboursements PY

```dax
Retours Remboursements PY = IF([_PY incomplet], BLANK(), CALCULATE([Retours Remboursements], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Retours Remboursements YoY Δ

```dax
Retours Remboursements YoY Δ = [Retours Remboursements] - [Retours Remboursements PY]
```

*Format* : `€#,##0`

---

## Retours Remboursements YoY %

```dax
Retours Remboursements YoY % = DIVIDE([Retours Remboursements] - [Retours Remboursements PY], [Retours Remboursements PY])
```

*Format* : `0.0%`

---

## Coûts Génériques PY

```dax
Coûts Génériques PY = IF([_PY incomplet], BLANK(), CALCULATE([Coûts Génériques], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Coûts Génériques YoY Δ

```dax
Coûts Génériques YoY Δ = [Coûts Génériques] - [Coûts Génériques PY]
```

*Format* : `€#,##0`

---

## Coûts Génériques YoY %

```dax
Coûts Génériques YoY % = DIVIDE([Coûts Génériques] - [Coûts Génériques PY], [Coûts Génériques PY])
```

*Format* : `0.0%`

---

## Revenu (reconstruit)

> Finance KPI — Revenue (reconstruit) = CA HT net annulation reconstruit + frais port hors CANCELLED.  
> Mesure de revenu publiée sur toutes les pages.  

```dax
Revenu (reconstruit) =
[CA HT Net Annulation (reconstruit)]
    + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
```

*Format* : `€#,##0`

---

## Revenu (reconstruit) PY

```dax
Revenu (reconstruit) PY =
IF([_PY incomplet], BLANK(), CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Revenu (reconstruit) YoY Δ

```dax
Revenu (reconstruit) YoY Δ =
IF([_PY incomplet], BLANK(), [Revenu (reconstruit)] - [Revenu (reconstruit) PY])
```

*Format* : `€#,##0`

---

## Revenu (reconstruit) YoY %

```dax
Revenu (reconstruit) YoY % = DIVIDE([Revenu (reconstruit)] - [Revenu (reconstruit) PY], [Revenu (reconstruit) PY])
```

*Format* : `0.0%`

---

## Marge Brute (reconstruit)

> Marge brute publiée — 7 postes contractuels Marc, base CA reconstruit.  
> Revenu (CA reconstruit net annulation + frais de port hors CANCELLED)  
> − COGS (0 si state = CANCELLED, décision Marc 25/08/2026) − transport amont  
> (conservé 100 %, pas de filtre statut) − transport sortant (colis, donc seulement  
> si expédiée) − droits et taxes − commissions marketplace − fournitures d'expédition.  
> Retours / coûts génériques exclus (below-the-line, profit bridge uniquement).  

```dax
Marge Brute (reconstruit) =
[CA HT Net Annulation (reconstruit)]
    + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
    - [Coût Achat Total]
    - [Coût Transport Amont]
    - [Coût Transport Outbound (Retenu)]
    - [Douanes Taxes]
    - [Commissions Marketplace]
    - [Fournitures Expédition]
```

*Format* : `€#,##0`

---

## Marge Brute (reconstruit) PY

```dax
Marge Brute (reconstruit) PY =
IF([_PY incomplet], BLANK(), CALCULATE([Marge Brute (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Marge Brute (reconstruit) YoY Δ

```dax
Marge Brute (reconstruit) YoY Δ =
IF([_PY incomplet], BLANK(), [Marge Brute (reconstruit)] - [Marge Brute (reconstruit) PY])
```

*Format* : `€#,##0`

---

## Marge Brute (reconstruit) YoY %

```dax
Marge Brute (reconstruit) YoY % =
DIVIDE([Marge Brute (reconstruit)] - [Marge Brute (reconstruit) PY], ABS([Marge Brute (reconstruit) PY]))
```

*Format* : `0.0%`

---

## Taux Marge Brute (reconstruit)

```dax
Taux Marge Brute (reconstruit) =
DIVIDE([Marge Brute (reconstruit)], [Revenu (reconstruit)])
```

*Format* : `0.0%`

---

## Taux Marge Brute (reconstruit) PY

```dax
Taux Marge Brute (reconstruit) PY =
IF([_PY incomplet], BLANK(), CALCULATE([Taux Marge Brute (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `0.0%`

---

## Taux Marge Brute (reconstruit) YoY bps

```dax
Taux Marge Brute (reconstruit) YoY bps =
VAR cy = [Taux Marge Brute (reconstruit)]
VAR py = [Taux Marge Brute (reconstruit) PY]
RETURN IF(ISBLANK(cy) || ISBLANK(py), BLANK(), (cy - py) * 10000)
```

*Format* : `#,##0`

---

## Revenu (reconstruit, alloué langue)

> General View — alloue le revenu commande (reconstruit) au prorata des unités par langue livre.  

```dax
Revenu (reconstruit, alloué langue) =
SUMX(
    VALUES(fact_commandes[id_commande]),
    VAR Rev =
        CALCULATE(
            [CA HT Net Annulation (reconstruit)]
                + CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED"),
            ALLEXCEPT(fact_commandes, fact_commandes[id_commande]),
            REMOVEFILTERS(fact_lignes[langue_livre], fact_lignes[canal_ligne], fact_lignes[canal_langue])
        )
    VAR UnitsTotal =
        CALCULATE(
            [Nb Articles],
            ALLEXCEPT(fact_commandes, fact_commandes[id_commande]),
            REMOVEFILTERS(fact_lignes[langue_livre], fact_lignes[canal_ligne], fact_lignes[canal_langue])
        )
    VAR UnitsSlice = CALCULATE([Nb Articles], ALLEXCEPT(fact_commandes, fact_commandes[id_commande]))
    RETURN IF(UnitsTotal = 0, BLANK(), Rev * DIVIDE(UnitsSlice, UnitsTotal))
)
```

*Format* : `€#,##0`

---

## Taux Annulation

> --- KPI cards : Taux Annulation (Cancellation rate) — YoY en bps, pas en % ---  
> Field cadrage n°4 : = Cancelled units / Ordered units (grain article, date_commande).  
> Numérateur [Nb Articles Annulés] (internal_state = CANCELLED), dénominateur  
> [Unités commandées] (périmètre volumes : commandes avec CA et commandes annulées).  

```dax
Taux Annulation =
DIVIDE([Nb Articles Annulés], [Unités commandées])
```

*Format* : `0.0%`

---

## Taux Annulation PY

```dax
Taux Annulation PY = IF([_PY incomplet], BLANK(), CALCULATE([Taux Annulation], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `0.0%`

---

## Taux Annulation YoY bps

```dax
Taux Annulation YoY bps =
VAR cy = [Taux Annulation]
VAR py = [Taux Annulation PY]
RETURN IF(ISBLANK(cy) || ISBLANK(py), BLANK(), (cy - py) * 10000)
```

*Format* : `#,##0`

---

## KPI Sous-titre — Unités

> Bloc 9 — Présentation General View (L04). Sous-titres cartes KPI  
> (valeur PY + YoY compact, flèche ▲/▼) et mesures couleur (vert/rouge)  
> pour le formatage conditionnel des cartes et des colonnes YoY du tableau.  
> Couleurs alignées charte : good #6FA84B / bad #C0504D.  
> Carte General View — sous-titre "PY: 1.23k (▲ +45.2% YoY)" (unités, compact).  

```dax
KPI Sous-titre — Unités =
VAR py = [Unités commandées PY]
VAR yoy = [Unités commandées YoY %]
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR a = ABS(py)
VAR pytxt =
    SWITCH(
        TRUE(),
        a >= 100000, FORMAT(py / 1000, "#,##0", "en-US") & "K",
        a >= 1000, FORMAT(py / 1000, "0.0", "en-US") & "K",
        FORMAT(py, "#,##0", "en-US")
    )
RETURN
    IF(
        ISBLANK(py),
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Revenue

> Carte General View — sous-titre "PY: €120k (▲ +48.3% YoY)" (revenu reconstruit, compact €).  

```dax
KPI Sous-titre — Revenue =
VAR py = [Revenu (reconstruit) PY]
VAR yoy = [Revenu (reconstruit) YoY %]
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR a = ABS(py)
VAR pytxt =
    SWITCH(
        TRUE(),
        a >= 100000, "€" & FORMAT(py / 1000, "#,##0", "en-US") & "K",
        a >= 1000, "€" & FORMAT(py / 1000, "0.0", "en-US") & "K",
        "€" & FORMAT(py, "#,##0", "en-US")
    )
RETURN
    IF(
        ISBLANK(py),
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Gross Profit

> Carte General View — sous-titre "PY: €20k (▲ +52.8% YoY)" (marge brute, compact €).  

```dax
KPI Sous-titre — Gross Profit =
VAR py = [Marge Brute (reconstruit) PY]
VAR yoy = [Marge Brute (reconstruit) YoY %]
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR a = ABS(py)
VAR pytxt =
    SWITCH(
        TRUE(),
        a >= 100000, "€" & FORMAT(py / 1000, "#,##0", "en-US") & "K",
        a >= 1000, "€" & FORMAT(py / 1000, "0.0", "en-US") & "K",
        "€" & FORMAT(py, "#,##0", "en-US")
    )
RETURN
    IF(
        ISBLANK(py),
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Gross Margin

> Carte General View — sous-titre "PY: 16.8% (▲ +500 bps YoY)" (taux marge, delta en bps).  

```dax
KPI Sous-titre — Gross Margin =
VAR py = [Taux Marge Brute (reconstruit) PY]
VAR bps = [Taux Marge Brute (reconstruit) YoY bps]
VAR arrow = IF(bps >= 0, UNICHAR(9650), UNICHAR(9660))
RETURN
    IF(
        ISBLANK(py),
        "PY: n/a",
        "PY: " & FORMAT(py, "0.0%", "en-US") & IF(ISBLANK(bps), "", "   (" & arrow & " " & FORMAT(bps, "+0;-0", "en-US") & " bps YoY)")
    )
```

---

## Couleur YoY — Unités

> Couleur conditionnelle YoY — unités (hausse = vert). Cartes + tableau.  

```dax
Couleur YoY — Unités =
VAR y = [Unités commandées YoY %]
RETURN IF(ISBLANK(y), BLANK(), IF(y >= 0, "#6FA84B", "#C0504D"))
```

---

## Couleur YoY — Revenue

> Couleur conditionnelle YoY — revenu reconstruit (hausse = vert). Cartes + tableau.  

```dax
Couleur YoY — Revenue =
VAR y = [Revenu (reconstruit) YoY %]
RETURN IF(ISBLANK(y), BLANK(), IF(y >= 0, "#6FA84B", "#C0504D"))
```

---

## Couleur YoY — Gross Profit

> Couleur conditionnelle YoY — marge brute (hausse = vert). Cartes + tableau.  

```dax
Couleur YoY — Gross Profit =
VAR y = [Marge Brute (reconstruit) YoY %]
RETURN IF(ISBLANK(y), BLANK(), IF(y >= 0, "#6FA84B", "#C0504D"))
```

---

## Couleur YoY — Gross Margin

> Couleur conditionnelle YoY — taux marge, delta bps. Vert si >= 0 ; rouge si <= -100 bps ; neutre entre.  

```dax
Couleur YoY — Gross Margin =
VAR bps = [Taux Marge Brute (reconstruit) YoY bps]
RETURN
    SWITCH(
        TRUE(),
        NOT ISNUMBER(bps), BLANK(),
        bps >= 0, "#6FA84B",
        bps <= -100, "#C0504D",
        "#1B3A5C"
    )
```

---

## Couleur YoY — Cancellation

> Couleur conditionnelle YoY — taux d'annulation, delta bps. Baisse = vert (inversé).  

```dax
Couleur YoY — Cancellation = IF([Taux Annulation YoY bps] <= 0, "#6FA84B", "#C0504D")
```

---

## Chart label — Revenue YoY

> General View — data label YoY sur graphe Revenue (combo CY/PY).  

```dax
Chart label — Revenue YoY =
VAR y = [Revenu (reconstruit) YoY %]
RETURN
    IF(
        NOT ISNUMBER(y) || ISBLANK([Revenu (reconstruit) PY]),
        BLANK(),
        FORMAT(y, "+0%;-0%", "en-US") & " YoY"
    )
```

---

## Chart label — Gross Profit YoY

> General View — data label YoY sur graphe Gross Profit (combo CY/PY).  

```dax
Chart label — Gross Profit YoY =
VAR y = [Marge Brute (reconstruit) YoY %]
RETURN
    IF(
        NOT ISNUMBER(y) || ISBLANK([Marge Brute (reconstruit) PY]),
        BLANK(),
        FORMAT(y, "+0%;-0%", "en-US") & " YoY"
    )
```

---

## KPI Compact — Ordered units

> General View — KPI card valeur compacte (K adaptatif : 0.0K sous 100K, #,##0K au-delà, comme les étiquettes des graphiques).  
> formatString DAX (,,M / ,"k") ne s'applique pas aux cartes en locale FR.  

```dax
KPI Compact — Ordered units =
VAR v = [Unités commandées]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, FORMAT(v / 1000, "0.0", "en-US") & "K",
            FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Outbound (tous colis)

> Cartes KPI Transport / Loss analysis : valeur compacte (même format que les cartes KPI des autres pages).  

```dax
KPI Compact — Outbound (tous colis) =
VAR v = [Coût Transport Outbound (tous colis)]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Douanes (tous colis)

```dax
KPI Compact — Douanes (tous colis) =
VAR v = [Douanes Taxes (tous colis)]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Fournitures (tous colis)

```dax
KPI Compact — Fournitures (tous colis) =
VAR v = [Fournitures Expédition (tous colis)]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Colis

```dax
KPI Compact — Colis =
VAR v = [Nb Colis]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, FORMAT(v / 1000, "0.0", "en-US") & "K",
            FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Pertes

```dax
KPI Compact — Pertes =
VAR v = [Pertes Totales]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "€0",
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Commandes déficitaires

```dax
KPI Compact — Commandes déficitaires =
VAR v = [Nb Commandes Deficitaires]
RETURN
    SWITCH(
        TRUE(),
        v >= 100000, FORMAT(v / 1000, "#,##0", "en-US") & "K",
        v >= 1000, FORMAT(v / 1000, "0.0", "en-US") & "K",
        FORMAT(v, "#,##0", "en-US")
    )
```

---

## KPI Compact — Revenue

```dax
KPI Compact — Revenue =
VAR v = [Revenu (reconstruit)]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Gross Profit

```dax
KPI Compact — Gross Profit =
VAR v = [Marge Brute (reconstruit)]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        "n/a",
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## KPI Compact — Gross Margin

```dax
KPI Compact — Gross Margin =
VAR r = [Taux Marge Brute (reconstruit)]
RETURN IF(ISBLANK(r), "n/a", FORMAT(r, "0.0%", "en-US"))
```

---

## GV Display — Ordered units

> General View — tableau KPI, formats compacts (texte).  

```dax
GV Display — Ordered units = [KPI Compact — Ordered units]
```

---

## GV Display — Revenue

```dax
GV Display — Revenue =
IF(ISBLANK([Revenu (reconstruit)]), BLANK(), [KPI Compact — Revenue])
```

---

## GV Display — Gross Profit

```dax
GV Display — Gross Profit =
IF(ISBLANK([Marge Brute (reconstruit)]), BLANK(), [KPI Compact — Gross Profit])
```

---

## GV Display — YoY€

```dax
GV Display — YoY€ =
VAR v = [Revenu (reconstruit) YoY Δ]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## Profit Produit Pur

> Bloc 10 — Website B2C (stable) : Display ASCII + Rest via code_pays  

```dax
Profit Produit Pur = [Revenu (reconstruit)] - [Coût Achat Total]
```

*Format* : `€#,##0`

---

## B2C Display - Sales

```dax
B2C Display - Sales =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Revenu (reconstruit)],
        IF(
            Country = "Rest of the world",
            [B2C Rest Sales],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Revenu (reconstruit)], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - COGS

```dax
B2C Display - COGS =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Coût Achat Total],
        IF(
            Country = "Rest of the world",
            [B2C Rest COGS],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Coût Achat Total], BLANK())
        )
    )
VAR sales =
    IF(
        ISBLANK(Country),
        [Revenu (reconstruit)],
        IF(
            Country = "Rest of the world",
            [B2C Rest Sales],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Revenu (reconstruit)], BLANK())
        )
    )
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        FORMAT(ROUND(v, 0), "€#,##0", "en-US") & " (" & FORMAT(DIVIDE(v, sales, 0), "0.0%", "en-US") & ")"
    )
```

---

## B2C Display - Product profit

```dax
B2C Display - Product profit =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Profit Produit Pur],
        IF(
            Country = "Rest of the world",
            [B2C Rest Product profit],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Profit Produit Pur], BLANK())
        )
    )
VAR sales =
    IF(
        ISBLANK(Country),
        [Revenu (reconstruit)],
        IF(
            Country = "Rest of the world",
            [B2C Rest Sales],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Revenu (reconstruit)], BLANK())
        )
    )
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        FORMAT(ROUND(v, 0), "€#,##0", "en-US") & " (" & FORMAT(DIVIDE(v, sales, 0), "0.0%", "en-US") & ")"
    )
```

---

## B2C Display - Gross profit

```dax
B2C Display - Gross profit =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Marge Brute (reconstruit)],
        IF(
            Country = "Rest of the world",
            [B2C Rest GP reconstruit],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Marge Brute (reconstruit)], BLANK())
        )
    )
VAR sales =
    IF(
        ISBLANK(Country),
        [Revenu (reconstruit)],
        IF(
            Country = "Rest of the world",
            [B2C Rest Sales],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Revenu (reconstruit)], BLANK())
        )
    )
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        FORMAT(ROUND(v, 0), "€#,##0", "en-US") & " (" & FORMAT(DIVIDE(v, sales, 0), "0.0%", "en-US") & ")"
    )
```

---

## B2C Display - Returns and refunds

```dax
B2C Display - Returns and refunds =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Retours Remboursements],
        IF(
            Country = "Rest of the world",
            [B2C Rest Returns],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Retours Remboursements], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Inbound freight

```dax
B2C Display - Inbound freight =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Coût Transport Amont],
        IF(
            Country = "Rest of the world",
            [B2C Rest Inbound],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Coût Transport Amont], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Shipping

```dax
B2C Display - Shipping =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Coût Transport Outbound (Retenu)],
        IF(
            Country = "Rest of the world",
            [B2C Rest Shipping],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Coût Transport Outbound (Retenu)], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Duties and taxes

```dax
B2C Display - Duties and taxes =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Douanes Taxes],
        IF(
            Country = "Rest of the world",
            [B2C Rest Duties],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Douanes Taxes], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Shipping supplies

```dax
B2C Display - Shipping supplies =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Fournitures Expédition],
        IF(
            Country = "Rest of the world",
            [B2C Rest Supplies],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Fournitures Expédition], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Marketplace fees

```dax
B2C Display - Marketplace fees =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Commissions Marketplace],
        IF(
            Country = "Rest of the world",
            [B2C Rest Commissions],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Commissions Marketplace], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Generic costs

```dax
B2C Display - Generic costs =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR v =
    IF(
        ISBLANK(Country),
        [Coûts Génériques],
        IF(
            Country = "Rest of the world",
            [B2C Rest Generic],
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Coûts Génériques], BLANK())
        )
    )
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## B2C Display - Revenue YoY %

```dax
B2C Display - Revenue YoY % =
VAR y = [B2C YoY - Revenue %]
RETURN IF(NOT ISNUMBER(y), BLANK(), FORMAT(y, "+0.0%;-0.0%", "en-US"))
```

---

## B2C Display - GP YoY %

```dax
B2C Display - GP YoY % =
VAR y = [B2C YoY - GP %]
RETURN IF(NOT ISNUMBER(y), BLANK(), FORMAT(y, "+0.0%;-0.0%", "en-US"))
```

---

## B2C Display - GM YoY bps

```dax
B2C Display - GM YoY bps =
VAR y = [B2C YoY - GM bps]
RETURN IF(NOT ISNUMBER(y), BLANK(), FORMAT(y, "+0;-0", "en-US") & " bps")
```

---

## B2C YoY - Revenue %

> Valeur numérique de [B2C Display - Revenue YoY %] (Top 15 + Rest of the world) : base des couleurs.  

```dax
B2C YoY - Revenue % =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
RETURN
    IF(
        ISBLANK(Country),
        [Revenu (reconstruit) YoY %],
        IF(
            Country = "Rest of the world",
            DIVIDE([B2C Rest Sales] - [B2C Rest Sales PY], [B2C Rest Sales PY]),
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Revenu (reconstruit) YoY %], BLANK())
        )
    )
```

*Format* : `0.0%`

---

## B2C YoY - GP %

> Valeur numérique de [B2C Display - GP YoY %] (Top 15 + Rest of the world) : base des couleurs.  

```dax
B2C YoY - GP % =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
RETURN
    IF(
        ISBLANK(Country),
        [Marge Brute (reconstruit) YoY %],
        IF(
            Country = "Rest of the world",
            DIVIDE([B2C Rest GP reconstruit] - [B2C Rest GP reconstruit PY], ABS([B2C Rest GP reconstruit PY])),
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Marge Brute (reconstruit) YoY %], BLANK())
        )
    )
```

*Format* : `0.0%`

---

## B2C YoY - GM bps

> Valeur numérique de [B2C Display - GM YoY bps] (Top 15 + Rest of the world) : base des couleurs.  

```dax
B2C YoY - GM bps =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
VAR RateCy = DIVIDE([B2C Rest GP reconstruit], [B2C Rest Sales])
VAR RatePy = DIVIDE([B2C Rest GP reconstruit PY], [B2C Rest Sales PY])
RETURN
    IF(
        ISBLANK(Country),
        [Taux Marge Brute (reconstruit) YoY bps],
        IF(
            Country = "Rest of the world",
            IF(ISBLANK(RateCy) || ISBLANK(RatePy), BLANK(), (RateCy - RatePy) * 10000),
            IF(ISNUMBER(CountryRank) && CountryRank <= 15, [Taux Marge Brute (reconstruit) YoY bps], BLANK())
        )
    )
```

*Format* : `#,##0`

---

## B2C Couleur - Revenue YoY

> Couleur colonne Revenue YoY des tableaux B2C / B2B (même valeur que l'affichage).  

```dax
B2C Couleur - Revenue YoY =
VAR y = [B2C YoY - Revenue %]
RETURN IF(NOT ISNUMBER(y), BLANK(), IF(y >= 0, "#6FA84B", "#C0504D"))
```

---

## B2C Couleur - GP YoY

> Couleur colonne Gross Profit YoY des tableaux B2C / B2B (même valeur que l'affichage).  

```dax
B2C Couleur - GP YoY =
VAR y = [B2C YoY - GP %]
RETURN IF(NOT ISNUMBER(y), BLANK(), IF(y >= 0, "#6FA84B", "#C0504D"))
```

---

## B2C Couleur - GM YoY

> Couleur colonne Gross Margin YoY (bps) des tableaux B2C / B2B : vert >= 0, rouge <= -100, neutre entre.  

```dax
B2C Couleur - GM YoY =
VAR bps = [B2C YoY - GM bps]
RETURN
    SWITCH(
        TRUE(),
        NOT ISNUMBER(bps), BLANK(),
        bps >= 0, "#6FA84B",
        bps <= -100, "#C0504D",
        "#1B3A5C"
    )
```

---

## B2C couleur - cout

```dax
B2C couleur - cout = "#C86B5A"
```

---

## B2C couleur - profit

```dax
B2C couleur - profit =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR v =
    IF(
        Country = "Rest of the world",
        [B2C Rest GP reconstruit],
        [Marge Brute (reconstruit)]
    )
RETURN IF(v >= 0, "#6FA84B", "#C0504D")
```

---

## B2C Sort Key

> Clé de tri tableau B2C (dans Values, isHidden) : Sales desc ; Rest = -1.  
> Top 15 via [B2C Rank] ici seulement — sinon toutes les lignes réapparaissent.  
> Pas de RANKX dans les mesures Display.  

```dax
B2C Sort Key =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR CountryRank = [B2C Rank]
RETURN
    IF(
        Country = "Rest of the world",
        -1,
        IF(
            ISNUMBER(CountryRank) && CountryRank <= 15,
            [Revenu (reconstruit)],
            BLANK()
        )
    )
```

*Format* : `#,##0.00`

---

## B2C Rank

> TOPN + tie-break nom_pays_en (PAS Rank DENSE) ; BLANK hors TopSet (contrat 1-15, pas de rang 16+). 2026-08-29.  

```dax
B2C Rank =
VAR Country = SELECTEDVALUE(dim_pays[nom_pays_en])
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR InTop = CALCULATE(COUNTROWS(dim_pays), KEEPFILTERS(TopSet))
RETURN
    IF(
        OR(ISBLANK(Country), Country = "Rest of the world")
            || ISBLANK(InTop) || InTop = 0,
        BLANK(),
        RANKX(TopSet, [Revenu (reconstruit)], , DESC, DENSE)
    )
```

---

## B2C Rest Sales

```dax
B2C Rest Sales =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Revenu (reconstruit)], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Revenu (reconstruit)], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Sales PY

```dax
B2C Rest Sales PY =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Revenu (reconstruit) PY], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Revenu (reconstruit) PY], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest COGS

```dax
B2C Rest COGS =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Coût Achat Total], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Coût Achat Total], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Product profit

```dax
B2C Rest Product profit =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Profit Produit Pur], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Profit Produit Pur], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Returns

```dax
B2C Rest Returns =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Retours Remboursements], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Retours Remboursements], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Inbound

```dax
B2C Rest Inbound =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Coût Transport Amont], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Coût Transport Amont], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Shipping

```dax
B2C Rest Shipping =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Coût Transport Outbound (Retenu)], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Coût Transport Outbound (Retenu)], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Duties

```dax
B2C Rest Duties =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Douanes Taxes], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Douanes Taxes], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Supplies

```dax
B2C Rest Supplies =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Fournitures Expédition], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Fournitures Expédition], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Commissions

```dax
B2C Rest Commissions =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Commissions Marketplace], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Commissions Marketplace], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Generic

```dax
B2C Rest Generic =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Coûts Génériques], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Coûts Génériques], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Gross profit

```dax
B2C Rest Gross profit =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Marge Brute], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Marge Brute], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest Gross profit PY

```dax
B2C Rest Gross profit PY =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Marge Brute PY], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Marge Brute PY], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest GP reconstruit

```dax
B2C Rest GP reconstruit =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Marge Brute (reconstruit)], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Marge Brute (reconstruit)], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## B2C Rest GP reconstruit PY

```dax
B2C Rest GP reconstruit PY =
VAR TopSet =
    TOPN(
        15,
        FILTER(
            ALLSELECTED(dim_pays[nom_pays_en]),
            dim_pays[nom_pays_en] <> "Rest of the world"
        ),
        [Revenu (reconstruit)],
        DESC,
        dim_pays[nom_pays_en],
        ASC
    )
VAR TopPart =
    CALCULATE([Marge Brute (reconstruit) PY], ALLSELECTED(dim_pays[nom_pays_en]), KEEPFILTERS(TopSet))
VAR Total =
    CALCULATE([Marge Brute (reconstruit) PY], ALLSELECTED(dim_pays[nom_pays_en]))
RETURN Total - TopPart
```

*Format* : `€#,##0`

---

## Revenu (reconstruit, alloué langue) PY

```dax
Revenu (reconstruit, alloué langue) PY = IF([_PY incomplet], BLANK(), CALCULATE([Revenu (reconstruit, alloué langue)], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## B2C Bridge — Revenue

> B2C contribution bridges (slide 7). Axe _BridgePaysYoY = Prior year + Top 15 + Rest.  
> Rest = complement de l'axe fige (Total - somme des 15 pays de l'axe). 2026-08-29.  
> Ce Top 15 (refresh) differe volontairement de celui du tableau P&L (dynamique, via [B2C Rank]).  

```dax
B2C Bridge — Revenue =
IF(
    [_PY incomplet],
    BLANK(),
        VAR k = SELECTEDVALUE(_BridgePaysYoY[Kind])
        VAR label = SELECTEDVALUE(_BridgePaysYoY[Label])
        RETURN
            SWITCH(
                TRUE(),
                k = "Start",
                    CALCULATE(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])), REMOVEFILTERS(_BridgePaysYoY)),
                k = "Rest",
                    CALCULATE(
                        VAR TotalCY = [Revenu (reconstruit)]
                        VAR TotalPY = CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))
                        VAR AxisCY =
                            SUMX(
                                FILTER(_BridgePaysYoY, _BridgePaysYoY[Kind] = "Country"),
                                CALCULATE(
                                    [Revenu (reconstruit)],
                                    TREATAS({ _BridgePaysYoY[Label] }, dim_pays[nom_pays_en])
                                )
                            )
                        VAR AxisPY =
                            SUMX(
                                FILTER(_BridgePaysYoY, _BridgePaysYoY[Kind] = "Country"),
                                CALCULATE(
                                    CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])),
                                    TREATAS({ _BridgePaysYoY[Label] }, dim_pays[nom_pays_en])
                                )
                            )
                        RETURN (TotalCY - AxisCY) - (TotalPY - AxisPY),
                        REMOVEFILTERS(_BridgePaysYoY)
                    ),
                k = "Country",
                    CALCULATE(
                        [Revenu (reconstruit)] - CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])),
                        TREATAS({ label }, dim_pays[nom_pays_en]),
                        REMOVEFILTERS(_BridgePaysYoY)
                    ),
                BLANK()
            )
)
```

*Format* : `€#,##0`

---

## B2C Bridge — Gross Profit

```dax
B2C Bridge — Gross Profit =
IF(
    [_PY incomplet],
    BLANK(),
        VAR k = SELECTEDVALUE(_BridgePaysYoY[Kind])
        VAR label = SELECTEDVALUE(_BridgePaysYoY[Label])
        RETURN
            SWITCH(
                TRUE(),
                k = "Start",
                    CALCULATE(CALCULATE([Marge Brute (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])), REMOVEFILTERS(_BridgePaysYoY)),
                k = "Rest",
                    CALCULATE(
                        VAR TotalCY = [Marge Brute (reconstruit)]
                        VAR TotalPY = CALCULATE([Marge Brute (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))
                        VAR AxisCY =
                            SUMX(
                                FILTER(_BridgePaysYoY, _BridgePaysYoY[Kind] = "Country"),
                                CALCULATE(
                                    [Marge Brute (reconstruit)],
                                    TREATAS({ _BridgePaysYoY[Label] }, dim_pays[nom_pays_en])
                                )
                            )
                        VAR AxisPY =
                            SUMX(
                                FILTER(_BridgePaysYoY, _BridgePaysYoY[Kind] = "Country"),
                                CALCULATE(
                                    CALCULATE([Marge Brute (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])),
                                    TREATAS({ _BridgePaysYoY[Label] }, dim_pays[nom_pays_en])
                                )
                            )
                        RETURN (TotalCY - AxisCY) - (TotalPY - AxisPY),
                        REMOVEFILTERS(_BridgePaysYoY)
                    ),
                k = "Country",
                    CALCULATE(
                        [Marge Brute (reconstruit)] - CALCULATE([Marge Brute (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date])),
                        TREATAS({ label }, dim_pays[nom_pays_en]),
                        REMOVEFILTERS(_BridgePaysYoY)
                    ),
                BLANK()
            )
)
```

*Format* : `€#,##0`

---

## Revenu (reconstruit, alloué ISBN)

> Top sellers ISBN — revenu commande réparti par article (1/n par article, cf. [_Allocation ligne active]).  
> Alias de [Revenu (reconstruit)] : le filtre ISBN déclenche la répartition par article.  

```dax
Revenu (reconstruit, alloué ISBN) =
[Revenu (reconstruit)]
```

*Format* : `€#,##0`

---

## Top Rank ISBN — Revenue

> Top 10 ISBN classés sur les unités commandées (champ toujours rempli) ; customer_price_per_item_eur  
> est vide sur ~95 % des articles. TOPN + tie-break ISBN (PAS Rank DENSE).  

```dax
Top Rank ISBN — Revenue =
VAR TopSet =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_lignes[isbn]),
            NOT ISBLANK([Unités commandées])
        ),
        [Unités commandées],
        DESC,
        fact_lignes[isbn],
        ASC
    )
VAR InTop = CALCULATE(COUNTROWS(fact_lignes), KEEPFILTERS(TopSet))
RETURN
    IF(
        ISBLANK(InTop) || InTop = 0,
        BLANK(),
        RANKX(TopSet, [Unités commandées], , DESC, DENSE)
    )
```

*Format* : `0`

---

## Mkt Display - Sales

> Marketplaces (slide 9) — Display format mockup, SANS logique Top15 pays.  
> Axe table = dim_type_commande[libelle] ; filtre page canal = Marketplaces.  

```dax
Mkt Display - Sales =
VAR v = [Revenu (reconstruit)]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - COGS

```dax
Mkt Display - COGS =
VAR v = [Coût Achat Total]
VAR sales = [Revenu (reconstruit)]
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        FORMAT(ROUND(v, 0), "€#,##0", "en-US") & " (" & FORMAT(DIVIDE(v, sales, 0), "0.0%", "en-US") & ")"
    )
```

---

## Mkt Display - Product profit

```dax
Mkt Display - Product profit =
VAR v = [Profit Produit Pur]
VAR sales = [Revenu (reconstruit)]
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        FORMAT(ROUND(v, 0), "€#,##0", "en-US") & " (" & FORMAT(DIVIDE(v, sales, 0), "0.0%", "en-US") & ")"
    )
```

---

## Mkt Display - Returns and refunds

```dax
Mkt Display - Returns and refunds =
VAR v = [Retours Remboursements]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Inbound freight

```dax
Mkt Display - Inbound freight =
VAR v = [Coût Transport Amont]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Shipping

```dax
Mkt Display - Shipping =
VAR v = [Coût Transport Outbound (Retenu)]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Duties and taxes

```dax
Mkt Display - Duties and taxes =
VAR v = [Douanes Taxes]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Shipping supplies

```dax
Mkt Display - Shipping supplies =
VAR v = [Fournitures Expédition]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Marketplace fees

```dax
Mkt Display - Marketplace fees =
VAR v = [Commissions Marketplace]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Generic costs

```dax
Mkt Display - Generic costs =
VAR v = [Coûts Génériques]
RETURN IF(ISBLANK(v), BLANK(), FORMAT(ROUND(v, 0), "€#,##0", "en-US"))
```

---

## Mkt Display - Gross profit

```dax
Mkt Display - Gross profit =
VAR v = [Marge Brute (reconstruit)]
VAR sales = [Revenu (reconstruit)]
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        FORMAT(ROUND(v, 0), "€#,##0", "en-US") & " (" & FORMAT(DIVIDE(v, sales, 0), "0.0%", "en-US") & ")"
    )
```

---

## Mkt Display - Revenue YoY %

```dax
Mkt Display - Revenue YoY % =
VAR y = [Revenu (reconstruit) YoY %]
RETURN IF(NOT ISNUMBER(y), BLANK(), FORMAT(y, "+0.0%;-0.0%", "en-US"))
```

---

## Mkt Display - GP YoY %

```dax
Mkt Display - GP YoY % =
VAR y = [Marge Brute (reconstruit) YoY %]
RETURN IF(NOT ISNUMBER(y), BLANK(), FORMAT(y, "+0.0%;-0.0%", "en-US"))
```

---

## Mkt Display - GM YoY bps

```dax
Mkt Display - GM YoY bps =
VAR y = [Taux Marge Brute (reconstruit) YoY bps]
RETURN IF(NOT ISNUMBER(y), BLANK(), FORMAT(y, "+0;-0", "en-US") & " bps")
```

---

## Top Unités Commande

> TOPN + tie-break id_commande (pattern Top * ISBN) — le IF(Keep) par ligne faisait  
> passer le total visuel (RANKX sur revenu agrégé → Keep=1 → somme globale).  
> Classement sur la colonne fact_commandes[revenu_commande] (une requête moteur, pas de mesure  
> réévaluée par commande). Filtre langue / ISBN actif : classement sur le revenu alloué (mesure).  

```dax
Top Unités Commande =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[revenu_commande]),
            fact_commandes[revenu_commande],
            DESC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[revenu_commande] > 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            NOT ISBLANK([Revenu (reconstruit)])
        ),
        [Revenu (reconstruit)],
        DESC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Unités commandées], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Unités commandées], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `#,##0`

---

## Top Revenu Commande

```dax
Top Revenu Commande =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[revenu_commande]),
            fact_commandes[revenu_commande],
            DESC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[revenu_commande] > 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            NOT ISBLANK([Revenu (reconstruit)])
        ),
        [Revenu (reconstruit)],
        DESC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Revenu (reconstruit)], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Revenu (reconstruit)], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Marge Commande

```dax
Top Marge Commande =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[revenu_commande]),
            fact_commandes[revenu_commande],
            DESC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[revenu_commande] > 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            NOT ISBLANK([Revenu (reconstruit)])
        ),
        [Revenu (reconstruit)],
        DESC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Marge Brute (reconstruit)], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Marge Brute (reconstruit)], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Unités ISBN

```dax
Top Unités ISBN =
VAR TopSet =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_lignes[isbn]),
            NOT ISBLANK([Unités commandées])
        ),
        [Unités commandées],
        DESC,
        fact_lignes[isbn],
        ASC
    )
RETURN CALCULATE([Unités commandées], KEEPFILTERS(TopSet))
```

*Format* : `#,##0`

---

## Top Revenu ISBN

```dax
Top Revenu ISBN =
VAR TopSet =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_lignes[isbn]),
            NOT ISBLANK([Unités commandées])
        ),
        [Unités commandées],
        DESC,
        fact_lignes[isbn],
        ASC
    )
RETURN CALCULATE([Revenu (reconstruit, alloué ISBN)], KEEPFILTERS(TopSet))
```

*Format* : `€#,##0`

---

## Top Loss — Unités

> TOPN + tie-break id_commande (pattern Top * Commande corrigé) — le IF(Keep) par ligne  
> faisait retomber le total visuel à BLANK (marge agrégée >= 0 hors Top Rank Loss).  
> Classement sur la colonne fact_commandes[marge_brute_commande] (une requête moteur, pas de  
> mesure réévaluée par commande). Filtre langue / ISBN actif : classement sur la marge allouée (mesure).  

```dax
Top Loss — Unités =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Unités commandées], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Unités commandées], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `#,##0`

---

## Top Loss — Revenue

```dax
Top Loss — Revenue =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Revenu (reconstruit)], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Revenu (reconstruit)], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — COGS

```dax
Top Loss — COGS =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Coût Achat Total], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Coût Achat Total], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Inbound

```dax
Top Loss — Inbound =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Coût Transport Amont], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Coût Transport Amont], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Shipping

```dax
Top Loss — Shipping =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Coût Transport Outbound (Retenu)], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Coût Transport Outbound (Retenu)], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Duties

```dax
Top Loss — Duties =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Douanes Taxes], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Douanes Taxes], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Marketplace fees

```dax
Top Loss — Marketplace fees =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Commissions Marketplace], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Commissions Marketplace], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Supplies

```dax
Top Loss — Supplies =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Fournitures Expédition], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Fournitures Expédition], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Returns

```dax
Top Loss — Returns =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Retours Remboursements], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Retours Remboursements], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Generic

```dax
Top Loss — Generic =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Coûts Génériques], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Coûts Génériques], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Top Loss — Gross Profit

```dax
Top Loss — Gross Profit =
VAR TopSetColonne =
    CALCULATETABLE(
        TOPN(
            10,
            SUMMARIZE(fact_commandes, fact_commandes[id_commande], fact_commandes[marge_brute_commande]),
            fact_commandes[marge_brute_commande],
            ASC,
            fact_commandes[id_commande],
            ASC
        ),
        ALLSELECTED(fact_commandes[id_commande]),
        KEEPFILTERS(fact_commandes[marge_brute_commande] < 0)
    )
VAR TopSetAlloue =
    TOPN(
        10,
        FILTER(
            ALLSELECTED(fact_commandes[id_commande]),
            [Marge Brute (reconstruit)] < 0
        ),
        [Marge Brute (reconstruit)],
        ASC,
        fact_commandes[id_commande],
        ASC
    )
RETURN
    IF(
        [_Allocation ligne active],
        CALCULATE([Marge Brute (reconstruit)], KEEPFILTERS(TopSetAlloue)),
        CALCULATE([Marge Brute (reconstruit)], KEEPFILTERS(TopSetColonne))
    )
```

*Format* : `€#,##0`

---

## Frais Port Net Annulation

> Frais de port hors CANCELLED - même périmètre que le revenu publié.  

```dax
Frais Port Net Annulation = CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
```

*Format* : `€#,##0`

---

## Frais Port Net Annulation PY

```dax
Frais Port Net Annulation PY = IF([_PY incomplet], BLANK(), CALCULATE([Frais Port Net Annulation], SAMEPERIODLASTYEAR(dim_date[date])))
```

*Format* : `€#,##0`

---

## Frais Port Net Annulation YoY Δ

```dax
Frais Port Net Annulation YoY Δ = [Frais Port Net Annulation] - [Frais Port Net Annulation PY]
```

*Format* : `€#,##0`

---

## Bridge PnL YoY

> Profit bridge PnL. Axe = GP reconstruit N-1 + variations des postes de la formule de marge brute.  
> MB_PY = [Marge Brute (reconstruit) PY]. CA = YoY du CA reconstruit net annulation.  
> Total waterfall = [Marge Brute (reconstruit)] (retours / génériques hors marge brute, hors axe).  

```dax
Bridge PnL YoY =
IF(
    [_PY incomplet],
    BLANK(),
        VAR poste = SELECTEDVALUE(BridgePnL[Poste])
        VAR signe = SELECTEDVALUE(BridgePnL[Signe])
        RETURN
            SWITCH(
                poste,
                "MB_PY", [Marge Brute (reconstruit) PY],
                "CA", ([Revenu (reconstruit) YoY Δ] - [Frais Port Net Annulation YoY Δ]) * signe,
                "PORT", [Frais Port Net Annulation YoY Δ] * signe,
                "ACHAT", [Coût Achat Total YoY Δ] * signe,
                "AMONT", [Coût Transport Amont YoY Δ] * signe,
                "OUTBOUND", [Coût Transport Outbound (Retenu) YoY Δ] * signe,
                "DOUANES", [Douanes Taxes YoY Δ] * signe,
                "COMMISSIONS", [Commissions Marketplace YoY Δ] * signe,
                "FOURNITURES", [Fournitures Expédition YoY Δ] * signe,
                BLANK()
            )
)
```

*Format* : `€#,##0`

---

## Taux Marge Commerciale

> Field cadrage n°11 : Pure Product Margin (PPM) = PPP / Revenue.  
> Numerateur [Profit Produit Pur] = [Revenu (reconstruit)] - [Coût Achat Total].  
> [Revenu (reconstruit)] : hors CANCELLED. [Coût Achat Total] : net annulation  
> (0 si state = CANCELLED, décision Marc 25/08/2026).  
> Denominateur [Revenu (reconstruit)] : hors CANCELLED (CA HT net annulation + frais de port), commandes avec CA.  
> Perimetre ratio : revenu et COGS tous deux hors vente annulée.  

```dax
Taux Marge Commerciale =
DIVIDE([Profit Produit Pur], [Revenu (reconstruit)])
```

*Format* : `0.0%`

---

## Transport sortant par unité

> Field cadrage n°14 : Shipping cost per unit = Shipping cost / ordered units.  
> Numerateur [Coût Transport Outbound (Retenu)] : grain colis, sans filtre CANCELLED  
> (cout mesure sur colis expedies).  
> Denominateur [Unités commandées (avec CA)] : unités des commandes avec CA.  

```dax
Transport sortant par unité =
DIVIDE([Coût Transport Outbound (Retenu)], [Unités commandées (avec CA)])
```

*Format* : `€#,##0.00`

---

## Taux Transport sortant

> Field cadrage n°15 : Shipping % of revenue = Shipping cost / revenue.  
> Numerateur [Coût Transport Outbound (Retenu)] : grain colis, sans filtre CANCELLED.  
> Denominateur [Revenu (reconstruit)] : hors CANCELLED.  
> Perimetre DIVERGENT : cout brut colis / revenu net annulation, meme traitement  
> des couts que [Marge Brute] / [Taux Marge Brute] (outbound conserve si colis).  
> Variante nette des deux cotes (non retenue) :  
> DIVIDE(CALCULATE([Coût Transport Outbound (Retenu)], fact_commandes[state] <> "CANCELLED"), [Revenu], 0).  
> Choix : formules client via mesures existantes, aligne sur [Taux Marge Brute].  

```dax
Taux Transport sortant =
DIVIDE([Coût Transport Outbound (Retenu)], [Revenu (reconstruit)])
```

*Format* : `0.0%`

---

## Douanes Taxes par unité

> Field cadrage n°17 : D/T per unit = D/T / ordered units.  
> Numerateur [Douanes Taxes] : grain colis, sans filtre CANCELLED.  
> Denominateur [Unités commandées (avec CA)] : unités des commandes avec CA.  

```dax
Douanes Taxes par unité =
DIVIDE([Douanes Taxes], [Unités commandées (avec CA)])
```

*Format* : `€#,##0.00`

---

## Taux Douanes Taxes

> Field cadrage n°18 : D/T percentage of revenue = D/T / revenue.  
> Numerateur [Douanes Taxes] : grain colis, sans filtre CANCELLED.  
> Denominateur [Revenu (reconstruit)] : hors CANCELLED.  
> Perimetre DIVERGENT : meme logique que [Taux Transport sortant] / [Taux Marge Brute].  
> Variante nette des deux cotes (non retenue) :  
> DIVIDE(CALCULATE([Douanes Taxes], fact_commandes[state] <> "CANCELLED"), [Revenu], 0).  
> Choix : formules client via mesures existantes, aligne sur [Taux Marge Brute].  

```dax
Taux Douanes Taxes =
DIVIDE([Douanes Taxes], [Revenu (reconstruit)])
```

*Format* : `0.0%`

---

## Taux Transport sortant (tous colis)

> Page Transport : coût outbound de tous les colis / revenu. Numérateur = valeur de la carte  
> Outbound (tous colis) ; le revenu ne couvre que les commandes avec CA.  

```dax
Taux Transport sortant (tous colis) = DIVIDE([Coût Transport Outbound (tous colis)], [Revenu (reconstruit)])
```

*Format* : `0.0%`

---

## Taux Douanes Taxes (tous colis)

> Page Transport : droits et taxes de tous les colis / revenu (même périmètre que la carte Duties).  

```dax
Taux Douanes Taxes (tous colis) = DIVIDE([Douanes Taxes (tous colis)], [Revenu (reconstruit)])
```

*Format* : `0.0%`

---

## Marge Brute par unité

> Field cadrage n°25 : Gross Profit per unit = marge publiée / ordered units.  

```dax
Marge Brute par unité =
DIVIDE([Marge Brute (reconstruit)], [Unités commandées (avec CA)])
```

*Format* : `€#,##0.00`

---

## Nb Commandes Deficitaires

> Page 11 Loss analysis : nombre de commandes à marge_brute_commande < 0 (7 postes, CA reconstruit).  

```dax
Nb Commandes Deficitaires =
COALESCE(
    CALCULATE(
        COUNTROWS(fact_commandes),
        fact_commandes[marge_brute_commande] < 0
    ),
    0
)
```

*Format* : `#,##0`

---

## Part Commandes Deficitaires

> Page 11 Loss analysis : part des commandes deficitaires dans le total.  

```dax
Part Commandes Deficitaires =
DIVIDE(
    [Nb Commandes Deficitaires],
    CALCULATE(COUNTROWS(fact_commandes), KEEPFILTERS(fact_commandes[ca_disponible] = "Oui"))
)
```

*Format* : `0.0%`

---

## Pertes Totales

> Page 11 Loss analysis : somme des pertes (marge negative), valeur negative.  

```dax
Pertes Totales =
CALCULATE(
    SUM(fact_commandes[marge_brute_commande]),
    fact_commandes[marge_brute_commande] < 0
)
```

*Format* : `€#,##0`

---

## Part Pertes Marge Brute

> Page 11 Loss analysis : |pertes| / marge brute publiée.  

```dax
Part Pertes Marge Brute =
DIVIDE(-COALESCE([Pertes Totales], 0), [Marge Brute (reconstruit)])
```

*Format* : `0.0%`

---

## Perte Moyenne

> Page 11 Loss analysis : perte moyenne par commande deficitaire.  

```dax
Perte Moyenne =
DIVIDE([Pertes Totales], [Nb Commandes Deficitaires])
```

*Format* : `€#,##0.00`

---

## KPI couleur — valeur

> Cartes KPI GP : navy charte si >= 0, rouge si negatif. Pas de vert (identite visuelle).  

```dax
KPI couleur — valeur = IF([Marge Brute (reconstruit)] >= 0, "#1B3A5C", "#C0504D")
```

---

## KPI couleur — Gross Margin

> Cartes KPI Gross Margin : signe du taux affiche, pas du GP (taux vide sans revenu, GP peut etre < 0).  

```dax
KPI couleur — Gross Margin = IF([Taux Marge Brute (reconstruit)] >= 0, "#1B3A5C", "#C0504D")
```

---

## KPI couleur — Marge par unité

> Carte Profit bridge GP/unité : signe de [Marge Brute par unité] (vide sans unités, GP peut etre < 0).  

```dax
KPI couleur — Marge par unité = IF([Marge Brute par unité] >= 0, "#1B3A5C", "#C0504D")
```

---

## KPI couleur — PPM

> Carte Profit bridge PPM : signe de [Taux Marge Commerciale] (PPP/CA, distinct du GP).  

```dax
KPI couleur — PPM = IF([Taux Marge Commerciale] >= 0, "#1B3A5C", "#C0504D")
```

---

## KPI Sous-titre — GP par unité

> Profit bridge — sous-titre carte marge brute par unité (PY + variation).  

```dax
KPI Sous-titre — GP par unité =
VAR cy = [Marge Brute par unité]
VAR py = CALCULATE([Marge Brute par unité], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    "€" & FORMAT(py, "0.00", "en-US")
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — PPM

> Profit bridge — sous-titre carte marge produit (PY + variation en bps).  

```dax
KPI Sous-titre — PPM =
VAR cy = [Taux Marge Commerciale]
VAR py = CALCULATE([Taux Marge Commerciale], SAMEPERIODLASTYEAR(dim_date[date]))
VAR bps = (cy - py) * 10000
VAR arrow = IF(bps >= 0, UNICHAR(9650), UNICHAR(9660))
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & FORMAT(py, "0.0%", "en-US") & IF(ISBLANK(cy), "", "   (" & arrow & " " & FORMAT(bps, "+0;-0", "en-US") & " bps YoY)")
    )
```

---

## KPI Sous-titre — Transport par unité

> Profit bridge — sous-titre carte transport sortant par unité.  

```dax
KPI Sous-titre — Transport par unité =
VAR cy = [Transport sortant par unité]
VAR py = CALCULATE([Transport sortant par unité], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    "€" & FORMAT(py, "0.00", "en-US")
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Douanes par unité

> Profit bridge — sous-titre carte droits et taxes par unité.  

```dax
KPI Sous-titre — Douanes par unité =
VAR cy = [Douanes Taxes par unité]
VAR py = CALCULATE([Douanes Taxes par unité], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    "€" & FORMAT(py, "0.00", "en-US")
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Pertes

> Loss analysis — sous-titre carte pertes totales.  

```dax
KPI Sous-titre — Pertes =
VAR cy = [Pertes Totales]
VAR py = CALCULATE([Pertes Totales], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    SWITCH(
        TRUE(),
        ABS(py) >= 100000, "€" & FORMAT(py / 1000, "#,##0", "en-US") & "K",
        ABS(py) >= 1000, "€" & FORMAT(py / 1000, "0.0", "en-US") & "K",
        "€" & FORMAT(py, "#,##0", "en-US")
    )
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Commandes déficitaires

> Loss analysis — sous-titre carte commandes déficitaires.  

```dax
KPI Sous-titre — Commandes déficitaires =
VAR cy = [Nb Commandes Deficitaires]
VAR py = CALCULATE([Nb Commandes Deficitaires], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    IF(ABS(py) >= 1000, FORMAT(py / 1000, "0.0", "en-US") & "K", FORMAT(py, "#,##0", "en-US"))
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Part pertes

> Loss analysis — sous-titre carte part des pertes dans la marge brute.  

```dax
KPI Sous-titre — Part pertes =
VAR cy = [Part Pertes Marge Brute]
VAR py = CALCULATE([Part Pertes Marge Brute], SAMEPERIODLASTYEAR(dim_date[date]))
VAR bps = (cy - py) * 10000
VAR arrow = IF(bps >= 0, UNICHAR(9650), UNICHAR(9660))
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & FORMAT(py, "0.0%", "en-US") & IF(ISBLANK(cy), "", "   (" & arrow & " " & FORMAT(bps, "+0;-0", "en-US") & " bps YoY)")
    )
```

---

## KPI Sous-titre — Part commandes déficitaires

> Loss analysis — sous-titre carte part des commandes déficitaires.  

```dax
KPI Sous-titre — Part commandes déficitaires =
VAR cy = [Part Commandes Deficitaires]
VAR py = CALCULATE([Part Commandes Deficitaires], SAMEPERIODLASTYEAR(dim_date[date]))
VAR bps = (cy - py) * 10000
VAR arrow = IF(bps >= 0, UNICHAR(9650), UNICHAR(9660))
RETURN
    IF(
        ISBLANK(py) || ISBLANK(CALCULATE([Revenu (reconstruit)], SAMEPERIODLASTYEAR(dim_date[date]))) || [_PY incomplet],
        "PY: n/a",
        "PY: " & FORMAT(py, "0.0%", "en-US") & IF(ISBLANK(cy), "", "   (" & arrow & " " & FORMAT(bps, "+0;-0", "en-US") & " bps YoY)")
    )
```

---

## KPI Sous-titre — Colis

> Transport — sous-titre carte colis.  

```dax
KPI Sous-titre — Colis =
VAR cy = [Nb Colis]
VAR py = CALCULATE([Nb Colis], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    IF(ABS(py) >= 1000, FORMAT(py / 1000, "0.0", "en-US") & "K", FORMAT(py, "#,##0", "en-US"))
RETURN
    IF(
        ISBLANK(py),
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## KPI Sous-titre — Outbound

> Transport — sous-titre carte outbound : coût tous colis en % du revenu, et PY.  

```dax
KPI Sous-titre — Outbound =
VAR r = [Taux Transport sortant (tous colis)]
VAR rpy = CALCULATE([Taux Transport sortant (tous colis)], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN
    IF(
        ISBLANK(r),
        "n/a",
        FORMAT(r, "0.0%", "en-US") & " of revenue" & IF(ISBLANK(rpy) || [_PY incomplet], "", "   (PY " & FORMAT(rpy, "0.0%", "en-US") & ")")
    )
```

---

## KPI Sous-titre — Douanes

> Transport — sous-titre carte droits et taxes : tous colis en % du revenu, et PY.  

```dax
KPI Sous-titre — Douanes =
VAR r = [Taux Douanes Taxes (tous colis)]
VAR rpy = CALCULATE([Taux Douanes Taxes (tous colis)], SAMEPERIODLASTYEAR(dim_date[date]))
RETURN
    IF(
        ISBLANK(r),
        "n/a",
        FORMAT(r, "0.0%", "en-US") & " of revenue" & IF(ISBLANK(rpy) || [_PY incomplet], "", "   (PY " & FORMAT(rpy, "0.0%", "en-US") & ")")
    )
```

---

## KPI Sous-titre — Fournitures

> Transport — sous-titre carte fournitures d'expédition (tous colis).  

```dax
KPI Sous-titre — Fournitures =
VAR cy = [Fournitures Expédition (tous colis)]
VAR py = CALCULATE([Fournitures Expédition (tous colis)], SAMEPERIODLASTYEAR(dim_date[date]))
VAR yoy = DIVIDE(cy - py, ABS(py))
VAR arrow = IF(yoy >= 0, UNICHAR(9650), UNICHAR(9660))
VAR pytxt =
    SWITCH(
        TRUE(),
        ABS(py) >= 100000, "€" & FORMAT(py / 1000, "#,##0", "en-US") & "K",
        ABS(py) >= 1000, "€" & FORMAT(py / 1000, "0.0", "en-US") & "K",
        "€" & FORMAT(py, "#,##0", "en-US")
    )
RETURN
    IF(
        ISBLANK(py),
        "PY: n/a",
        "PY: " & pytxt & IF(ISBLANK(yoy), "", "   (" & arrow & " " & FORMAT(yoy, "+0.0%;-0.0%", "en-US") & " YoY)")
    )
```

---

## GV Chart Label — Revenue

> General View charts — étiquettes totaux empilés (format carte KPI Compact).  
> labelDisplayUnits natif ne permet pas €…k en préfixe ; mesure texte sur totals.  

```dax
GV Chart Label — Revenue =
IF(ISBLANK([Revenu (reconstruit)]), BLANK(), [KPI Compact — Revenue])
```

---

## GV Chart Label — Gross Profit

```dax
GV Chart Label — Gross Profit =
IF(ISBLANK([Marge Brute (reconstruit)]), BLANK(), [KPI Compact — Gross Profit])
```

---

## GV Chart Label — Revenue PY

```dax
GV Chart Label — Revenue PY =
VAR v = [Revenu (reconstruit) PY]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---

## GV Chart Label — Gross Profit PY

```dax
GV Chart Label — Gross Profit PY =
VAR v = [Marge Brute (reconstruit) PY]
VAR a = ABS(v)
RETURN
    IF(
        ISBLANK(v),
        BLANK(),
        SWITCH(
            TRUE(),
            a >= 100000, "€" & FORMAT(v / 1000, "#,##0", "en-US") & "K",
            a >= 1000, "€" & FORMAT(v / 1000, "0.0", "en-US") & "K",
            "€" & FORMAT(v, "#,##0", "en-US")
        )
    )
```

---
