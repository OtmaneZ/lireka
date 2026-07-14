# IMPLÉMENTATION DES CORRECTIFS NON BLOQUÉS PAR MARC

> Passe d'implémentation des constats `AUDIT.md` actionnables sans nouvel arbitrage ni
> nouvelles données. Chaque changement référence le constat `F-xx` qu'il corrige
> (commit / commentaires de code au format `Fix F-xx: ...`).
> Formule de marge : **confirmée par Marc** (voir `AUDIT.md` §6 Q1, appliquée le 15/07/2026).

## Méthode de vérification (à lire d'abord)

Power BI Desktop n'est pas disponible dans cet environnement Linux : il n'y a donc **pas** eu
de refresh Power BI réel ni d'ouverture du `.pbip`. Les vérifications ont été menées ainsi :

- **Logique M / DAX** : rejouée en Python en répliquant la logique des partitions **sur les
  vraies données** de `Power_BI_Datawarehouse/` (customer_order.csv = 989 234 lignes,
  package.csv, récaps Colissimo/Chronopost). C'est plus strict qu'un test sur `data/samples/`
  (dont le schéma simplifié ne reflète pas les colonnes sources réelles).
- **JSON rapport / thème** : validés par parsing `json.load` + contrôle des `queryRef`.
- **TMDL** : contrôles statiques de cohérence (colonnes déclarées vs référencées) et `grep`
  de symétrie / d'absence de références obsolètes.
- **Scripts Python** : `py_compile` + test de la variable d'environnement.

Ces vérifications ne remplacent pas l'ouverture du modèle dans Power BI Desktop, qui reste
la vérification finale à faire côté client (cf. `AUDIT.md` §4).

---

## Source de légitimité de la formule de marge

La formule à 7 postes implémentée dans les Blocs 1-3 provient d'un message Slack de
Marc Bordier daté du 13/07/2026 16h09, adressé nommément à Otmane Boulahia, précisant
le calcul du « Gross Margin » attendu pour le livrable L04. Ce n'est pas une initiative
du prestataire au-delà du devis — voir `project/perimetre-verrouille.md`.

---

## Tableau récapitulatif

| Bloc | F-xx corrigé(s) | Fichiers modifiés | Vérification effectuée | Résultat |
|------|-----------------|-------------------|------------------------|----------|
| 1 | F-04 | `fact_commandes.tmdl` | Réplication du typage des colonnes `shipping_fee_eur`, `inbound_transportation_cost_eur`, `marketplace_fees_eur` sur les 989 234 lignes réelles | ✅ 0 erreur de type ; colonnes présentes ; valeurs non nulles (12 410 / 73 674 / 630 883 lignes non nulles) |
| 2 | F-02, F-03 | `fact_transport.tmdl`, `_Mesures.tmdl`, `.../visuals/b2c3d4e5f60718293a4b1/visual.json` | Réplication de la résolution facture→colis puis calcul de `cout_transport_retenu` vs `cout_transport` (backend) sur données réelles | ✅ 115 701 colis rapprochés à une facture ; `cout_transport_retenu ≠ cout_transport` sur **100 %** d'entre eux |
| 3 | F-04, F-01 (part.) | `_Mesures.tmdl` | Calcul complet de `[Marge Brute]` (tous postes) sur données réelles | ✅ se calcule sans erreur, valeur non nulle. ⚠️ total fortement négatif car dominé par CANCELLED (F-07, non touché) — **ne pas présenter comme final** |
| 4 | F-01 | `.../visuals/e5f60718293a4b1c2d3e4`, `.../f60718293a4b1c2d3e4f5`, `.../d4e5f60718293a4b1c2d3` (visual.json) | Parsing JSON + contrôle des `queryState` | ✅ 8/8 visuels parsent ; bar-charts pays & type → `_Mesures.Marge Brute` ; textbox → carte `_Mesures.Taux Marge Brute` |
| 5 | F-05 | `_Mesures.tmdl`, `.../visuals/c3d4e5f60718293a4b1c2/visual.json` | Parsing JSON + grep références | ✅ carte référence `Écart Coût Outbound vs Estimé Backend` ; plus aucune ref à l'ancien nom dans le modèle |
| 6 | F-06 | `relationships.tmdl`, `_Mesures.tmdl` | Contrôle : exactement 2 relations `isActive: false` ; existence des colonnes de tous les `USERELATIONSHIP` ; analyse d'unicité des chemins | ✅ 2 seules relations inactives (posées volontairement) ; plus aucun chemin actif ambigu |
| 7 | F-11 | `expressions.tmdl` | Réplication de la distribution nb candidats (0/1/2+) + tie-break + fenêtre sur données réelles | ✅ 115 722 résolues (1 candidat), 399 non résolues (0 candidat) ; branche ≥2 non déclenchée par les données actuelles ; tie-break déterministe (plus petit `id_package`) vérifié en synthétique |
| 8 | F-12 | `expressions.tmdl`, `fact_transport.tmdl` | `grep Text.Upper(Text.Trim` dans les 2 fichiers ; contrôle des usages de `fnNormaliserSuivi` | ✅ **0** occurrence résiduelle ; `fnNormaliserSuivi` appliquée symétriquement des deux côtés (colis + factures) |
| 9 | F-08, F-09, F-10 | `docs/05-formation/session-02-visuels.md`, `session-03-marketing.md`, `quiz-evaluation.md`, `powerbi/models/mesures-dax.md` | grep colonnes fantômes ; régénération auto + comptage | ✅ plus de `pays_livraison`/`marge_brute` ; Q5 corrigée (7 transporteurs + INCONNU) ; `mesures-dax.md` régénéré (46 mesures, dont les 5 manquantes F-10) |
| 10 | F-14, F-17 | `expressions.tmdl`, `.../visuals/0a1b2c3d4e5f60718293b/visual.json` (nouveau), `report.json`, `StaticResources/RegisteredResources/LirekaTheme.json` (nouveau) | Parsing JSON + grep tenant | ✅ slicer date (`dim_date.annee_mois`) ajouté ; thème `LirekaProfitabilite` référencé ; URL tenant en dur remplacée par placeholder |
| 11 | F-19 | `scripts/validation/*.py` (8 fichiers) | `py_compile` + test override `LIREKA_DWH` | ✅ compilent tous ; override + fallback fonctionnels |

---

## Détail par bloc

### Bloc 1 — Import des colonnes manquantes (F-04)
- `fact_commandes` : ajout des colonnes `cout_transport_amont` (`inbound_transportation_cost_eur`)
  et `commissions_marketplace` (`marketplace_fees_eur`) ; renommage
  `shipping_fee_eur → frais_port_encaisse` (pour la mesure `[Frais Port Encaissés]`).
  `duties_taxes_eur` et `shipping_supply_cost_eur` étaient déjà exposés dans `fact_transport`.
- **Vérif** : les 3 colonnes source parsent en nombre sans erreur sur 989 234 lignes.

### Bloc 2 — Coût Transport Retenu (F-02, F-03)
- `fact_transport` : la jointure facture porte désormais le **montant facturé**
  (`cout_transport_facture`, somme des lignes rapprochées) ; ajout de `cout_transport_retenu`
  = facturé si disponible, sinon estimé backend. `cout_transport` (estimé) est **conservé**
  pour les mesures de contrôle.
- Modalités `source_cout` renommées (F-03) : `reel → facture_rapprochee`,
  `estime → backend_seul`, `non_disponible → aucun`. Références mises à jour dans
  `_Mesures.tmdl` et le titre du donut.
- **Vérif** : sur données réelles, `cout_transport_retenu` diffère de l'estimé sur 100 % des
  115 701 colis rapprochés — la valeur facturée entre bien désormais dans le coût outbound.

### Bloc 3 — Mesure de marge conforme à la formule Marc (F-04, F-01)
- Ajout de `[Frais Port Encaissés]`, `[Coût Transport Amont]`,
  `[Coût Transport Outbound (Retenu)]`, `[Douanes Taxes]`, `[Commissions Marketplace]`,
  `[Fournitures Expédition]`, `[Marge Brute]`, `[Taux Marge Brute]`,
  `[Écart Marge vs Backend (v2)]`.
- Les mesures provisoires (`Marge Brute (prov.)`, `Marge Brute Backend (réf.)`,
  `Écart Marge vs Backend`) sont **conservées** pour comparaison.
- `// TODO Marc` : périmètre `if relevant` du shipping revenue non tranché — la mesure
  `[Frais Port Encaissés]` reste inconditionnelle.
- **Vérif** : `[Marge Brute]` = −20 539 252,79 € sur données réelles (se calcule sans erreur).
  Ce total est **dominé par l'inclusion des CANCELLED** (F-07, hors périmètre de cette passe)
  et par les retours ; il n'est **pas** un chiffre à présenter au client tel quel.

### Bloc 4 — Câblage de la marge sur L04 (F-01)
- Bar-charts « par pays » et « par type » : mesure `Y` → `_Mesures.Marge Brute`, titres mis à jour.
- Textbox jaune « EN ATTENTE VALIDATION MARC » → carte `_Mesures.Taux Marge Brute` avec
  sous-titre « Formule confirmée le 15/07/2026 — shipping revenue: périmètre en attente ».
- Volumes par transporteur et donut **conservés** (contrôle qualité).

### Bloc 5 — Écart coût transport (F-05)
- `[Écart Coût Transport]` (comparait deux estimations backend) remplacé par
  `[Écart Coût Outbound vs Estimé Backend]` = `[Coût Transport Outbound (Retenu)] − [Coût Transport Estimé]`.
- Carte `c3d4…` : mesure + titre mis à jour.

### Bloc 6 — Relations (F-06)
- Cardinalités (`many`/`one`), `crossFilteringBehavior: singleDirection` et `isActive`
  déclarés explicitement sur **chaque** relation.
- `rel_factures_transporteur` et `rel_factures_date` → `isActive: false` (désambiguïsation).
- `[Coût Transport Facturé]` : `USERELATIONSHIP` sur les relations directes facture→transporteur
  et facture→date + `CROSSFILTER(... None)` sur `id_package` pour éviter toute ambiguïté.
- `[Coût Facturé Rapproché]` : `USERELATIONSHIP` explicite sur le chemin `id_package`
  (grain colis), distinct du total facturé.

### Bloc 7 — Fenêtre de tolérance + tie-break (F-11)
- Paramètre `FenetreToleranceJours = 7` en tête de `stg_factures_transport_resolu`
  (`// TODO Marc` : seuil à valider, défaut conservateur, **jamais présenté comme validé**).
- Branche ≥ 2 candidats : rejet si `delta > FenetreToleranceJours` ; tie-break déterministe
  par `id_package` croissant ; colonne de traçabilité `nb_candidats_resolution`.
- **Vérif** : comportement 0/1 candidat correct sur données réelles ; la branche ≥ 2 n'est pas
  déclenchée par les factures actuelles (aucun suivi facturé ne mappe > 1 colis), mais la
  logique de départage et de fenêtre est en place et vérifiée en synthétique.

### Bloc 8 — Normalisation des clés (F-12)
- Fonction unique `fnNormaliserSuivi` (NBSP U+00A0 + trim + majuscules), appliquée des DEUX
  côtés (colis + factures, variantes Colissimo/Chronopost) et à l'inférence transporteur.
- **Vérif** : `grep Text.Upper(Text.Trim` → 0 occurrence dans `expressions.tmdl` et
  `fact_transport.tmdl`.

### Bloc 9 — Documentation (F-08, F-09, F-10)
- Supports formation : `pays_livraison → nom_pays` (`dim_pays`), `marge_brute → [Marge Brute]`.
- Quiz Q5 : « 7 transporteurs (dont Postes Canada), + modalité INCONNU pour les non identifiés ».
- `mesures-dax.md` régénéré intégralement depuis `_Mesures.tmdl` (46 mesures) avec date en pied.

### Bloc 10 — Finitions rapport (F-14, F-17)
- Slicer `dim_date.annee_mois` ajouté sur L04.
- Thème `LirekaProfitabilite` (palette cohérente) créé et référencé dans `report.json`.
- `SharePointSiteURL` : valeur placeholder documentée (`https://VOTRE-TENANT.sharepoint.com/sites/VOTRE-SITE`).

### Bloc 11 — Hygiène scripts (F-19)
- `scripts/validation/*.py` : racine de l'entrepôt via `os.environ.get("LIREKA_DWH", <fallback>)`.

---

## Reste en attente de Marc

> Reprise **verbatim** des 6 questions de `AUDIT.md` §6 (non reformulées), pour rester
> cohérent avec ce qui a été envoyé au client. Aucune de ces décisions n'a été tranchée à la
> place de Marc dans cette passe (voir « NE PAS TOUCHER »).

1. **Formule de marge** — « Confirmez-vous la marge brute cible =
   *CA + frais de port encaissés − coût d'achat − transport − douanes − commissions marketplace − fournitures* (formule de `margin_analysis.py`) ? »
   *Pourquoi ça bloque* : sans elle, L04 ne peut afficher une marge juste.
   *Sans réponse* : on livre `[Marge Brute (prov.)]` étiquetée provisoire, non conforme.

2. **Coût transport dans la marge** — « La marge doit-elle utiliser le montant **facturé** par le transporteur quand une facture est rapprochée, ou l'estimation backend ? »
   *Pourquoi ça bloque* : détermine si le critère « coût réel issu des factures » est satisfait.
   *Sans réponse* : la marge reste sur l'estimation → critère L04 non rempli.

3. **Statut CANCELLED** — « Les commandes CANCELLED doivent-elles être exclues du CA, des volumes et du taux de matching ? »
   *Pourquoi ça bloque* : gonfle le dénominateur du matching et fausse le CA.
   *Sans réponse* : chiffres ambigus, taux de matching sous-estimé affiché.

4. **Jointure par date** — « Acceptez-vous que les numéros de suivi recyclés soient départagés par proximité de date, avec rejet au-delà de X jours (X = ?) ? »
   *Pourquoi ça bloque* : le devis dit « par numéro de suivi » ; la désambiguïsation par date est un ajout à valider.
   *Sans réponse* : risque de coûts rattachés à la mauvaise commande.

5. **Colis Privé** — « Colis Privé n'a pas de factures détaillées : ses coûts restent en **estimation backend** (`source_cout = "estime"`). Est-ce acceptable pour L01 ? »
   *Pourquoi ça bloque* : définit si L01 est « intégré » ou « partiel » pour ce transporteur.
   *Sans réponse* : ambiguïté sur le niveau d'intégration livré.

6. **Douanes/taxes** — « Souhaitez-vous que `duties_taxes_eur` (colonne présente, aujourd'hui non utilisée) entre dans la marge, notamment pour FedEx Maroc/Tunisie ? »
   *Pourquoi ça bloque* : impacte fortement la marge hors-UE.
   *Sans réponse* : douanes ignorées → marge hors-UE surestimée.
