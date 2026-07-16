# Mesures DAX — Lireka Power BI

> **Référence** : [`../../project/devis.md`](../../project/devis.md)  
> Référentiel des mesures DAX du dashboard profitabilité.  
> **Généré automatiquement** depuis `Lireka_Profitabilite.SemanticModel/definition/tables/_Mesures.tmdl`.  
> Ne pas éditer à la main : régénérer depuis `_Mesures.tmdl` (script one-shot).

> Total : **105 mesures**, dans l'ordre du modèle.

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

> Fix Bloc2 — grain passé de groupe/titre à article physique le 15/07/2026.  
> Ancienne mesure basée sur SUM(quantity_groupe) déduplicable en contrôle si besoin,  
> voir [Nb Articles (contrôle grain groupe)].  

```dax
Nb Articles = COUNTROWS(fact_lignes)
```

*Format* : `#,##0`

---

## Nb Articles (contrôle grain groupe)

> Contrôle Bloc2 — recalcule l'ancien total par somme des quantity_groupe distincts par groupe.  

```dax
Nb Articles (contrôle grain groupe) = SUMX(
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
CA Total HT (grain article, ajusté annulation) = SUMX(
		fact_lignes,
		IF(
			fact_lignes[statut_annulation_ligne] = "NON_ANNULE",
			fact_lignes[customer_price_per_item_eur],
			0
		)
	)
```

*Format* : `#,##0.00 €`

---

## Coût Achat Total (grain article)

> Bloc3 — coût d'achat au grain article. Conservé dans TOUS les cas d'annulation  
> (avant ET après expédition, décision Marc) — contrôle vs [Coût Achat Total] (grain commande).  

```dax
Coût Achat Total (grain article) = SUM(fact_lignes[product_cost_eur])
```

*Format* : `#,##0.00 €`

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

*Format* : `#,##0.00 €`

---

## CA Total HT

> Chiffre d'affaires HT (order_amount_eur).  

```dax
CA Total HT = SUM(fact_commandes[ca_ht])
```

*Format* : `#,##0.00 €`

---

## CA Total HT (reconstruit)

> CA HT reconstruit — order_amount_eur natif si présent, sinon order_amount_local / taux mensuel moyen.  
> Variante parallèle à [CA Total HT], sur le même modèle que [Marge Brute] vs [Marge Brute (prov.)].  
> Voir docs/notes-techniques/reconstruction-ca-marketplace.md.  

```dax
CA Total HT (reconstruit) = SUM(fact_commandes[ca_ht_reconstruit])
```

*Format* : `#,##0.00 €`

---

## CA HT Net Annulation

> Bloc3 (grain commande) — CA HT hors commandes annulées.  
> Applique la règle Marc "CA=0 sur annulation" au grain commande.  
> Ne capture PAS les annulations partielles (state <> CANCELLED, ~8 900 cmd,  
> borne CA cf. limite-etf-annulation.md) — limite connue documentée.  

```dax
CA HT Net Annulation = CALCULATE([CA Total HT], fact_commandes[state] <> "CANCELLED")
```

*Format* : `#,##0.00 €`

---

## CA HT Net Annulation (reconstruit)

> Bloc3 (grain commande) — CA HT reconstruit hors commandes annulées.  
> Variante marketplace (Bloc 1) de [CA HT Net Annulation].  

```dax
CA HT Net Annulation (reconstruit) = CALCULATE([CA Total HT (reconstruit)], fact_commandes[state] <> "CANCELLED")
```

*Format* : `#,##0.00 €`

---

## CA Commandes Annulation Partielle

> Bloc3 (grain commande) — transparence : CA porté par les commandes en annulation  
> partielle (state <> CANCELLED mais ≥1 article CANCELLED). Non ajusté faute de prix ligne.  
> Identification via rel_lignes_commandes (pas de colonne calculée fact_commandes).  

```dax
CA Commandes Annulation Partielle = CALCULATE(
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
Coût Transport Facturé = CALCULATE(
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
Écart Coût Outbound vs Estimé Backend = [Coût Transport Outbound (Retenu)] - [Coût Transport Estimé]
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

## Marge Brute (prov.)

> MARGE BRUTE — FORMULE PROVISOIRE. CA HT - coût d'achat - coût transport réel.  
> Écart constaté le 12/07/2026 entre ce calcul simple et gross_profit_eur existant.  
> À VALIDER avec Marc / finance avant de considérer comme définitive.  

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

> Écart entre la marge provisoire et la marge backend (aide à la validation finance).  

```dax
Écart Marge vs Backend = [Marge Brute (prov.)] - [Marge Brute Backend (réf.)]
```

*Format* : `#,##0.00 €`

---

## Frais Port Encaissés

> Fix F-04 : frais de port encaissés par le client (marketplace notamment).  
> Périmètre d'inclusion ("if relevant") non tranché — inclus par défaut dans [Marge Brute].  

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

## Retours Remboursements

> Bloc5 (dette technique) — retours et remboursements (returns_and_refunds_cost_eur,  
> agrégé par commande). Provisoire : Marc doit revoir le périmètre de son côté.  
> Risque double comptage à valider avec Marc : sur CANCELLED, product_cost (cout_achat)  
> est conservé ET returns_and_refunds est aussi soustrait — coexistence réelle dans les  
> données (pas d'identité rr≈pc ; ratio médian rr/pc ≈ 2,4 %). Voir dette-technique-bloc5.md.  

```dax
Retours Remboursements = SUM(fact_commandes[retours_remboursements])
```

*Format* : `#,##0.00 €`

---

## Coûts Génériques

> Bloc5 (dette technique) — coûts génériques (generic_costs_eur, agrégé par commande).  
> Provisoire : Marc doit revoir total_generic_costs_eur / la définition de generic costs  
> de son côté avant de figer ce poste dans la marge.  

```dax
Coûts Génériques = SUM(fact_commandes[couts_generiques])
```

*Format* : `#,##0.00 €`

---

## Marge Brute

> MARGE BRUTE — formule confirmée par Marc Bordier (Slack, 13/07/2026 16h09).  
> Revenu = CA hors commandes annulées (règle Marc "CA=0 sur annulation", grain commande).  
> Coûts conservés sur toutes commandes y compris annulées (décision Marc : coût produit  
> + transport si après expédition). Frais de port encaissés exclus sur commandes CANCELLED  
> (1 283 € sur l'entrepôt actuel, audit 15/07/2026). Annulations partielles non ajustées  
> (~8 900 cmd, limite connue — voir docs/notes-techniques/limite-etf-annulation.md).  
> Grain article [Marge Brute (grain article, prov.)] conservé comme contrôle et chemin de  
> bascule si customer_price_per_item_eur devient disponible par ligne.  
> Revenue (incl. shipping revenue if relevant) - COGS - Inbound transportation costs  
> - Outbound transportation costs - Duties and Taxes - Marketplace commission fees  
> - Shipping supplies - Returns/refunds - Generic costs.  
> Retours/remboursements + coûts génériques inclus (Bloc 5, dette technique provisoire —  
> Marc doit revoir total_generic_costs_eur ; valider risque double comptage returns/refunds  
> vs product_cost conservé sur annulation). Grain commande (agrégés par order_id depuis  
> customer_order_item).  

```dax
Marge Brute = [CA HT Net Annulation]
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

*Format* : `#,##0.00 €`

---

## Taux Marge Brute

> Fix F-04 / C-01 : taux = Marge Brute / revenu net annulation  
> ([CA HT Net Annulation] + frais port hors CANCELLED) — même périmètre que [Marge Brute].  

```dax
Taux Marge Brute = DIVIDE(
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
Coût Facturé Rapproché = CALCULATE(
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
Lignes Colis par Facture (hors 1re) = VAR T =
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
Vrais Doublons (Facture + Suivi) = VAR T =
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
Doublons Numero Suivi Factures = VAR T =
		ADDCOLUMNS(
			VALUES(fact_factures_transport[numero_suivi]),
			"Cnt", CALCULATE(COUNTROWS(fact_factures_transport))
		)
	RETURN
		SUMX(FILTER(T, [Cnt] > 1), [Cnt] - 1)
```

*Format* : `#,##0`

---

## Colis Order ID Manquant

> Colis sans order_id renseigné.

```dax
Colis Order ID Manquant =
CALCULATE([Nb Colis], ISBLANK(fact_transport[order_id]))
```

## Colis Numero Suivi Manquant

> Colis sans numero_suivi renseigné.

```dax
Colis Numero Suivi Manquant =
CALCULATE(
    [Nb Colis],
    ISBLANK(fact_transport[numero_suivi]) || fact_transport[numero_suivi] = ""
)
```

## Commandes Code Pays Non Attribué

> Commandes dont le code pays est "??" (destination_country absent).

```dax
Commandes Code Pays Non Attribué =
CALCULATE([Nb Commandes], fact_commandes[code_pays] = "??")
```

## Commandes Sans Colis

> Commandes hors CANCELLED sans aucun colis dans fact_transport (162 attendu sur entrepôt actuel).  

```dax
Commandes Sans Colis = COUNTROWS(
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
Colis Sans Commande = COUNTROWS(
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
Lignes Facture Coût Transport Zero ou Null = COUNTROWS(
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
Revenu = [CA HT Net Annulation]
		+ CALCULATE([Frais Port Encaissés], fact_commandes[state] <> "CANCELLED")
```

*Format* : `#,##0.00 €`

---

## Unités commandées PY

```dax
Unités commandées PY = CALCULATE([Unités commandées], SAMEPERIODLASTYEAR(dim_date[date]))
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

```dax
Revenu PY = CALCULATE([Revenu], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Revenu YoY Δ

```dax
Revenu YoY Δ = [Revenu] - [Revenu PY]
```

*Format* : `#,##0.00 €`

---

## Revenu YoY %

```dax
Revenu YoY % = DIVIDE([Revenu] - [Revenu PY], [Revenu PY])
```

*Format* : `0.0%`

---

## Marge Brute PY

```dax
Marge Brute PY = CALCULATE([Marge Brute], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Marge Brute YoY Δ

```dax
Marge Brute YoY Δ = [Marge Brute] - [Marge Brute PY]
```

*Format* : `#,##0.00 €`

---

## Marge Brute YoY %

```dax
Marge Brute YoY % = DIVIDE([Marge Brute] - [Marge Brute PY], [Marge Brute PY])
```

*Format* : `0.0%`

---

## Taux Marge Brute PY

```dax
Taux Marge Brute PY = CALCULATE([Taux Marge Brute], SAMEPERIODLASTYEAR(dim_date[date]))
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

```dax
Nb Commandes PY = CALCULATE([Nb Commandes], SAMEPERIODLASTYEAR(dim_date[date]))
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
CA HT Net Annulation PY = CALCULATE([CA HT Net Annulation], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## CA HT Net Annulation YoY Δ

```dax
CA HT Net Annulation YoY Δ = [CA HT Net Annulation] - [CA HT Net Annulation PY]
```

*Format* : `#,##0.00 €`

---

## CA HT Net Annulation YoY %

```dax
CA HT Net Annulation YoY % = DIVIDE([CA HT Net Annulation] - [CA HT Net Annulation PY], [CA HT Net Annulation PY])
```

*Format* : `0.0%`

---

## Frais Port Encaissés PY

```dax
Frais Port Encaissés PY = CALCULATE([Frais Port Encaissés], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Frais Port Encaissés YoY Δ

```dax
Frais Port Encaissés YoY Δ = [Frais Port Encaissés] - [Frais Port Encaissés PY]
```

*Format* : `#,##0.00 €`

---

## Frais Port Encaissés YoY %

```dax
Frais Port Encaissés YoY % = DIVIDE([Frais Port Encaissés] - [Frais Port Encaissés PY], [Frais Port Encaissés PY])
```

*Format* : `0.0%`

---

## Coût Achat Total PY

```dax
Coût Achat Total PY = CALCULATE([Coût Achat Total], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Coût Achat Total YoY Δ

```dax
Coût Achat Total YoY Δ = [Coût Achat Total] - [Coût Achat Total PY]
```

*Format* : `#,##0.00 €`

---

## Coût Achat Total YoY %

```dax
Coût Achat Total YoY % = DIVIDE([Coût Achat Total] - [Coût Achat Total PY], [Coût Achat Total PY])
```

*Format* : `0.0%`

---

## Coût Transport Amont PY

```dax
Coût Transport Amont PY = CALCULATE([Coût Transport Amont], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Coût Transport Amont YoY Δ

```dax
Coût Transport Amont YoY Δ = [Coût Transport Amont] - [Coût Transport Amont PY]
```

*Format* : `#,##0.00 €`

---

## Coût Transport Amont YoY %

```dax
Coût Transport Amont YoY % = DIVIDE([Coût Transport Amont] - [Coût Transport Amont PY], [Coût Transport Amont PY])
```

*Format* : `0.0%`

---

## Coût Transport Outbound (Retenu) PY

```dax
Coût Transport Outbound (Retenu) PY = CALCULATE([Coût Transport Outbound (Retenu)], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Coût Transport Outbound (Retenu) YoY Δ

```dax
Coût Transport Outbound (Retenu) YoY Δ = [Coût Transport Outbound (Retenu)] - [Coût Transport Outbound (Retenu) PY]
```

*Format* : `#,##0.00 €`

---

## Coût Transport Outbound (Retenu) YoY %

```dax
Coût Transport Outbound (Retenu) YoY % = DIVIDE([Coût Transport Outbound (Retenu)] - [Coût Transport Outbound (Retenu) PY], [Coût Transport Outbound (Retenu) PY])
```

*Format* : `0.0%`

---

## Douanes Taxes PY

```dax
Douanes Taxes PY = CALCULATE([Douanes Taxes], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Douanes Taxes YoY Δ

```dax
Douanes Taxes YoY Δ = [Douanes Taxes] - [Douanes Taxes PY]
```

*Format* : `#,##0.00 €`

---

## Douanes Taxes YoY %

```dax
Douanes Taxes YoY % = DIVIDE([Douanes Taxes] - [Douanes Taxes PY], [Douanes Taxes PY])
```

*Format* : `0.0%`

---

## Commissions Marketplace PY

```dax
Commissions Marketplace PY = CALCULATE([Commissions Marketplace], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Commissions Marketplace YoY Δ

```dax
Commissions Marketplace YoY Δ = [Commissions Marketplace] - [Commissions Marketplace PY]
```

*Format* : `#,##0.00 €`

---

## Commissions Marketplace YoY %

```dax
Commissions Marketplace YoY % = DIVIDE([Commissions Marketplace] - [Commissions Marketplace PY], [Commissions Marketplace PY])
```

*Format* : `0.0%`

---

## Fournitures Expédition PY

```dax
Fournitures Expédition PY = CALCULATE([Fournitures Expédition], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Fournitures Expédition YoY Δ

```dax
Fournitures Expédition YoY Δ = [Fournitures Expédition] - [Fournitures Expédition PY]
```

*Format* : `#,##0.00 €`

---

## Fournitures Expédition YoY %

```dax
Fournitures Expédition YoY % = DIVIDE([Fournitures Expédition] - [Fournitures Expédition PY], [Fournitures Expédition PY])
```

*Format* : `0.0%`

---

## Retours Remboursements PY

```dax
Retours Remboursements PY = CALCULATE([Retours Remboursements], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Retours Remboursements YoY Δ

```dax
Retours Remboursements YoY Δ = [Retours Remboursements] - [Retours Remboursements PY]
```

*Format* : `#,##0.00 €`

---

## Retours Remboursements YoY %

```dax
Retours Remboursements YoY % = DIVIDE([Retours Remboursements] - [Retours Remboursements PY], [Retours Remboursements PY])
```

*Format* : `0.0%`

---

## Coûts Génériques PY

```dax
Coûts Génériques PY = CALCULATE([Coûts Génériques], SAMEPERIODLASTYEAR(dim_date[date]))
```

*Format* : `#,##0.00 €`

---

## Coûts Génériques YoY Δ

```dax
Coûts Génériques YoY Δ = [Coûts Génériques] - [Coûts Génériques PY]
```

*Format* : `#,##0.00 €`

---

## Coûts Génériques YoY %

```dax
Coûts Génériques YoY % = DIVIDE([Coûts Génériques] - [Coûts Génériques PY], [Coûts Génériques PY])
```

*Format* : `0.0%`

---
