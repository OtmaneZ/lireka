# AUDIT TECHNIQUE ADVERSARIAL — Repo Lireka × ZineInsights

> Audit externe indépendant, **lecture seule**, réalisé le 14/07/2026.
> Source de vérité contractuelle : `project/devis.md` et `project/livrables.md`.
> Aucune modification de code effectuée dans cette passe. Les volumes cités dans la
> documentation (989 234 / 946 483 / 12,7 % / 83 481 CANCELLED / 382 suivis recyclés)
> sont traités comme des **affirmations de la doc**, non vérifiées sur données réelles.

> **Note de périmètre (ajoutée le 15/07/2026)** : la formule de marge à 7 postes n'est pas
> une extension d'audit — elle a été explicitement communiquée par Marc Bordier
> (Slack, 13/07/2026). Voir `project/perimetre-verrouille.md` pour le périmètre exact.

---

## 1. Verdict exécutif

**Le repo est-il livrable au client en l'état ? → NON.**

1. **L04 non rempli.** La page `Profitabilité L04` n'affiche **aucune marge brute**, ni
   par pays ni par type de commande. Les 3 graphes montrent des **volumes**
   (`Nb Colis`, `Nb Commandes`), pas de la marge. Le critère contractuel central du
   dashboard de profitabilité n'est pas satisfait (`page.json` + 7 visuels — cf. F-01).
2. **Le « coût transport réel » n'est pas le coût facturé.** `[Coût Transport Réel]` somme
   `package.shipping_cost_eur` (estimation backend), pas le montant des factures
   transporteurs. Le montant facturé **n'entre pas** dans `[Marge Brute (prov.)]`. Le
   critère d'acceptation « Coût transport réel utilisé (issu des factures jointes) » de
   `livrables.md` est violé, et le libellé `source_cout = "reel"` est trompeur (F-02, F-03).
3. **Ambiguïté du modèle non résolue + supports de formation faux.** `relationships.tmdl`
   crée deux chemins ambigus vers `dim_transporteur` et `dim_date` : Power BI désactivera
   des relations silencieusement (F-06). Et les supports de formation référencent des
   colonnes inexistantes (`pays_livraison`, `marge_brute` — F-08).

**Nuance** : la marge provisoire est explicitement étiquetée « en attente validation Marc »
partout, ce qui protège partiellement le prestataire — mais ne rend pas L04 conforme.

---

## 2. Conformité contractuelle

| Livrable | Critère d'acceptation (`livrables.md`) | Statut réel | Preuve | Verdict |
|----------|----------------------------------------|-------------|--------|---------|
| L01 | La Poste, Colis Privé, Chronopost intégrés | 8 libellés dans `dim_transporteur`, inférence par motif ; Colis Privé seulement en coût **estimé** | `dim_transporteur.tmdl` (bloc `Source = #table`) ; `expressions.tmdl` `fnNormaliserTransporteur` | ⚠️ PARTIEL |
| L01 | Postes Canada backend intégré (coût estimé) | Présent (`statut_integration = "Autre"`), inféré `Q013…` | `dim_transporteur.tmdl` ; `expressions.tmdl:StartsWith("Q013")` | ✅ CONFORME |
| L01 | ≥ 1 mois de factures importées | Colissimo 2025+2026, Chronopost 2025+2026 | `expressions.tmdl` `stg_factures_transport_resolu` | ⏸️ BLOQUÉ DONNÉES |
| L02 | Export backend importé + schéma documenté | `fact_commandes`, `fact_lignes`, `fact_transport` importés ; schéma dans `docs/03-dictionnaire-donnees` | `fact_commandes.tmdl` partition `m` | ✅ CONFORME |
| L03 | Jointure **par numéro de suivi** opérationnelle | Jointure par `numero_suivi` **puis** désambiguïsation **par date** → clé `id_package` | `expressions.tmdl` `stg_factures_transport_resolu` (`Table.Sort` sur `delta`) | ⚠️ PARTIEL |
| L03 | Taux de matching documenté | `[Taux Matching]` existe mais dénominateur inclut CANCELLED | `_Mesures.tmdl:108` | ⚠️ PARTIEL |
| **L04** | **Marge brute visible par pays** | **Aucun visuel de marge** ; graphes = volumes | 7 `visual.json` de la page — voir F-01 | ❌ **NON CONFORME** |
| **L04** | **Marge brute visible par type de commande** | idem | idem | ❌ **NON CONFORME** |
| **L04** | **Coût transport réel issu des factures jointes** | `[Coût Transport Réel]` = `package.shipping_cost_eur` (backend), pas la facture | `_Mesures.tmdl:83` + `fact_transport.tmdl:55,114` | ❌ **NON CONFORME** |
| L05 | ≥ 1 session formation proposée | Supports présents mais contiennent des colonnes fausses | `docs/05-formation/*` | ⚠️ PARTIEL |
| L06 | Processus import/refresh documenté | `docs/04-processus/processus-etl-gouvernance.md` présent | non ré-audité en détail | ✅ CONFORME (sous réserve F-06) |

---

## 3. Constats

### F-01 — L04 n'affiche aucune marge brute : le dashboard montre des volumes
**Sévérité** : CRITIQUE
**Nature** : Contractuel
**Preuve** :
- `powerbi/Lireka_Profitabilite.Report/definition/pages/7112a69a17fbef2de240/visuals/e5f60718293a4b1c2d3e4/visual.json` → titre `'Commandes par pays'`, mesure `Property: "Nb Commandes"`.
- `.../visuals/f60718293a4b1c2d3e4f5/visual.json` → titre `'Commandes par type'`, mesure `"Nb Commandes"`.
- `.../visuals/a1b2c3d4e5f60718293a4/visual.json` → titre `'Volumes par transporteur'`, mesure `"Nb Colis"`.
- `.../visuals/d4e5f60718293a4b1c2d3/visual.json` → textbox `"Marge Brute — EN ATTENTE VALIDATION MARC"` (aucune donnée).
**Ce qui se passe** : La seule page du rapport (`page.json` → `displayName: "Profitabilité L04"`) contient un bar-chart pays et un bar-chart type-de-commande, mais tous deux tracent un **comptage de commandes**, pas une marge. Aucun visuel du rapport ne référence `[Marge Brute (prov.)]` ni `[Taux Marge Brute (prov.)]`.
**Impact client** : Marc ouvre « le dashboard de profitabilité » et n'y voit aucune profitabilité. Il conclura, à raison, que le livrable central (L04) n'est pas là.
**Correctif proposé** : Une fois la formule de marge arbitrée (F-04), remplacer la mesure `Y` des deux bar-charts pays/type par la mesure de marge validée, et remplacer la textbox par un visuel carte/matrice `pays × type × [Marge]`. En attendant l'arbitrage, brancher `[Marge Brute (prov.)]` avec un bandeau « provisoire ».
**Effort** : S
**Bloque un livrable ?** : L04 — **oui**

---

### F-02 — Le coût facturé n'entre pas dans la marge ; « Coût Transport Réel » = estimation backend
**Sévérité** : CRITIQUE
**Nature** : Contractuel
**Preuve** :
- `_Mesures.tmdl:83` → `measure 'Marge Brute (prov.)' = [CA Total HT] - [Coût Achat Total] - [Coût Transport Réel]`.
- `_Mesures.tmdl` (bloc `Coût Transport Réel`) → `SUM(fact_transport[cout_transport])`.
- `fact_transport.tmdl:114` → `{"shipping_cost_eur", "cout_transport"}` (la colonne `cout_transport` **est** `package.shipping_cost_eur`, jamais remplacée par le montant de la facture).
- `fact_transport.tmdl:3` → commentaire : `cout_transport = shipping_cost_eur (estimation backend...)`.
**Question tranchée** : *le montant facturé (`fact_factures_transport[cout_transport]`) entre-t-il dans la marge brute ?* → **NON.** La marge n'utilise que `fact_transport[cout_transport]` = coût backend. Le montant facturé n'est exploité que dans des mesures de **contrôle croisé** (`[Coût Transport Facturé]`, `[Écart Réel vs Facturé]`), jamais dans la marge.
**Impact client** : Le critère « Coût transport réel utilisé (issu des factures jointes) » n'est pas rempli. Marc croira que sa marge intègre le coût transporteur réel alors qu'elle utilise l'estimation que la mission devait précisément corriger.
**Correctif proposé** : Décision métier requise (F-04). Techniquement : créer une mesure `[Coût Transport Retenu]` qui prend le **coût facturé** quand `source_cout = "reel"` et l'estimé sinon, puis bâtir la marge dessus — mais cela suppose de porter le montant de facture au grain colis (aujourd'hui seule l'**existence** d'une facture est propagée, pas sa **valeur**).
**Effort** : M
**Bloque un livrable ?** : L04 — **oui**

---

### F-03 — `source_cout = "reel"` est un nom trompeur (rapprochement ≠ valeur réelle)
**Sévérité** : MAJEUR
**Nature** : Correction / Documentation
**Preuve** :
- `fact_transport.tmdl:119-122` → `#"Source cout" = ... if Table.RowCount([fact]) > 0 then "reel" else if [cout_transport] = null or [cout_transport] = 0 then "non_disponible" else "estime"`.
- La valeur `cout_transport` reste `shipping_cost_eur` dans **tous** les cas.
**Ce qui se passe** : `"reel"` signale seulement qu'une facture a été **rapprochée** au colis, pas que la **valeur** du coût provient de cette facture. Le donut « Répartition coût (réel / estimé / non dispo) » (`visuals/b2c3d4e5f60718293a4b1`) laisse croire à une valeur facturée.
**Impact client** : Un utilisateur final lit « coût réel » et pense « montant que le transporteur nous a facturé ». C'est faux : c'est toujours l'estimation backend, avec juste une facture existante à côté.
**Correctif proposé** : Renommer les modalités en `"facture_rapprochee"` / `"backend_seul"` / `"aucun"`, ou remplacer réellement la valeur par le montant facturé quand disponible (cf. F-02). Mettre à jour donut, mesures `Nb Colis (coût réel/estimé)` et la doc.
**Effort** : S
**Bloque un livrable ?** : L04 — non (mais aggrave F-02)

---

### F-04 — Formule de marge incomplète vs formule validée par Marc (`margin_analysis.py`)
**Sévérité** : MAJEUR
**Nature** : Correction (décision métier)
**Preuve** :
- Formule Marc (`scripts/validation/margin_analysis.py`, `task2_recalc`) : `revenue + shipping_fee − COGS − inbound − outbound − duties − commissions − supplies`.
- DAX (`_Mesures.tmdl:83`) : `CA HT − Coût Achat − Coût Transport Réel`.

| Poste (formule Marc) | Colonne backend | Présent dans le DAX ? |
|----------------------|-----------------|-----------------------|
| revenue | `order_amount_eur` (`ca_ht`) | ✅ |
| + shipping_fee | `shipping_fee_eur` (chargé, `fact_commandes`) | ❌ (colonne importée mais non utilisée) |
| − COGS | `product_cost_eur` (`cout_achat`) | ✅ |
| − inbound | `inbound_transportation_cost_eur` | ❌ (non importé) |
| − outbound | `total_shipping_cost_to_delivery_country_eur` | ⚠️ remplacé par `package.shipping_cost_eur` |
| − duties | `duties_taxes_eur` (importé dans `fact_transport`) | ❌ (importé mais jamais sommé) |
| − commissions | `marketplace_fees_eur` | ❌ (non importé) |
| − supplies | `shipping_supply_cost_eur` (importé) / `total_shipping_supplies_eur` | ❌ (importé mais jamais sommé) |

**Douanes/taxes** : `duties_taxes_eur` **existe** dans `fact_transport.tmdl` mais n'est référencé par **aucune mesure** (grep sur `_Mesures.tmdl` : 0 occurrence). Enjeu central pour Marc (FedEx Maroc/Tunisie). **Verdict : non exploité.**
**Colonnes référencées / existence** : `ca_ht`, `cout_achat`, `cout_transport_estime`, `gross_profit_eur` existent bien dans `fact_commandes.tmdl` ; `cout_transport` existe dans `fact_transport.tmdl`. **Aucune mesure ne référence de colonne inexistante — pas d'erreur bloquante DAX de ce type.**
**Impact client** : La marge affichée sera fausse pour Marc : ni frais de port encaissés, ni commissions marketplace, ni douanes, ni fournitures. Sur des flux hors-UE, l'omission des douanes surestime fortement la marge.
**Correctif proposé** : Arbitrage Marc sur la formule cible, puis importer les postes manquants (`shipping_fee_eur` déjà là ; ajouter `marketplace_fees_eur`, `inbound_transportation_cost_eur`) et construire une mesure de marge complète. Alternative pragmatique : s'appuyer sur `gross_profit_eur` backend comme référence tant que la formule n'est pas arbitrée.
**Effort** : M
**Bloque un livrable ?** : L04 — **oui** (via F-01/F-02)

---

### F-05 — `[Écart Coût Transport]` compare deux estimations backend, pas facturé vs estimé
**Sévérité** : MAJEUR
**Nature** : Correction
**Preuve** :
- `_Mesures.tmdl:66` → `measure 'Écart Coût Transport' = [Coût Transport Réel] - [Coût Transport Estimé]`.
- `[Coût Transport Réel]` = `SUM(fact_transport[cout_transport])` = `package.shipping_cost_eur`.
- `[Coût Transport Estimé]` = `SUM(fact_commandes[cout_transport_estime])` = `total_shipping_cost_to_delivery_country_eur`.
**Ce qui se passe** : Les deux termes sont des **coûts backend** (deux colonnes différentes, deux grains), pas « facture − estimation ». La carte « Écart coût transport » (`visuals/c3d4e5f60718293a4b1c2`, mesure `Taux Écart Coût`) affiche donc un écart entre deux estimations.
**Impact client** : Marc lit « écart coût transport » et l'interprète comme « ce que je paie réellement vs ce que le backend estime ». En réalité c'est un écart interne backend, sans valeur de pilotage. La comparaison facturé/estimé existe (`[Écart Réel vs Facturé]`) mais n'est pas celle affichée.
**Correctif proposé** : Renommer en `[Écart Estimé Colis vs Estimé Commande]`, ou remplacer le terme « réel » par le coût facturé rapproché (cf. F-02). Corriger le titre de la carte.
**Effort** : S
**Bloque un livrable ?** : L04 — non

---

### F-06 — Relations sans cardinalité ni filtrage : chemins ambigus vers `dim_transporteur` et `dim_date`
**Sévérité** : MAJEUR
**Nature** : Modèle
**Preuve** (`relationships.tmdl`, aucune ligne `cardinality`, `crossFilteringBehavior` ni `isActive`) :
- Vers `dim_transporteur` : `rel_transport_transporteur` (`fact_transport→dim_transporteur`) **et** `rel_factures_transporteur` (`fact_factures_transport→dim_transporteur`) **et** `rel_factures_colis` (`fact_factures_transport→fact_transport`) : `fact_factures_transport` atteint `dim_transporteur` **directement** et **via** `fact_transport`.
- Vers `dim_date` : `rel_factures_date` (`fact_factures_transport→dim_date`) **et** `rel_factures_colis + rel_transport_commandes + rel_commandes_date` : `fact_factures_transport` atteint `dim_date` **directement** et **via** `fact_transport→fact_commandes`.
**Ce qui se passe** : Deux chemins actifs entre les mêmes tables. À l'import, Power BI refuse les chemins ambigus et **désactive silencieusement** une des relations (typiquement `rel_factures_transporteur` et/ou `rel_factures_date`). Les cardinalités non déclarées seront devinées.
**Impact client** : Les mesures filtrées via `fact_factures_transport` (`[Coût Transport Facturé]`, `[Écart Réel vs Facturé]`, doublons) peuvent se propager par un chemin non voulu → chiffres de contrôle faux, sans avertissement visible.
**Vérification à faire** : NON VÉRIFIÉ que le modèle charge sans erreur. Procédure : ouvrir `Lireka_Profitabilite.pbip` dans Power BI Desktop, vérifier dans la vue Modèle quelles relations sont en pointillé (inactives), et déclarer explicitement `fromCardinality`/`toCardinality`, `crossFilteringBehavior` et `isActive` sur chacune.
**Correctif proposé** : Déclarer explicitement chaque relation ; rendre `rel_factures_transporteur` et `rel_factures_date` inactives (`isActive: false`) et forcer le filtrage des factures via `fact_transport` par `USERELATIONSHIP` là où nécessaire.
**Effort** : M
**Bloque un livrable ?** : L04 — potentiellement oui (fiabilité des contrôles)

---

### F-07 — `[Taux Matching]` divise par un dénominateur incluant les CANCELLED
**Sévérité** : MAJEUR
**Nature** : Correction
**Preuve** :
- `_Mesures.tmdl:108` → `measure 'Taux Matching' = DIVIDE([Nb Commandes Matchées], [Nb Commandes], 0)`.
- `[Nb Commandes]` = `COUNTROWS(fact_commandes)` (aucun filtre d'état).
- `fact_commandes.tmdl` (partition) → commentaire : *« Exclusion CANCELLED retirée le 14/07/2026 … Ne pas réintroduire sans validation »*. La doc affirme 83 481 CANCELLED.
**Ce qui se passe** : Le numérateur ne peut matcher que des commandes expédiées, mais le dénominateur inclut toutes les CANCELLED. Le taux est donc structurellement écrasé.
**Impact client** : Marc verra un taux de matching artificiellement bas (« votre jointure ne marche pas ») alors que le vrai taux sur commandes expédiées est bien supérieur.
**Correctif proposé** : Soit exposer `[Taux Matching (hors CANCELLED)]` avec dénominateur `CALCULATE([Nb Commandes], fact_commandes[state] <> "CANCELLED")`, soit documenter explicitement le périmètre du taux. Décision métier sur le statut CANCELLED requise (F-04-bis).
**Effort** : S
**Bloque un livrable ?** : L03 — non (indicatif non contractuel) mais crédibilité

---

### F-08 — Supports de formation référencent des colonnes inexistantes (`pays_livraison`, `marge_brute`)
**Sévérité** : MAJEUR
**Nature** : Documentation
**Preuve** :
- `docs/05-formation/session-02-visuels.md:35` → `Glisser pays_livraison dans Axe Y` ; ligne 49 → `id_commande, date_commande, pays_livraison, transporteur, ca_ht, marge_brute` ; ligne 50 → `Trier par marge_brute décroissant`.
- `docs/05-formation/session-03-marketing.md:17,23,37` → `pays_livraison`, `marge_brute par segment`.
- Réalité modèle : la colonne pays s'appelle `code_pays`/`dim_pays[nom_pays]` (`fact_commandes.tmdl`), et **il n'existe aucune colonne `marge_brute`** — seulement les mesures `[Marge Brute (prov.)]` / `[Marge Brute Backend (réf.)]`.
- `powerbi/models/modeles-semanticques.md:55` confirme : *« pas `pays_livraison` — colonne absente du modèle »* → contradiction interne à la doc.
**Impact client** : En session, les participants suivent les pas et ne trouvent aucun champ `pays_livraison`/`marge_brute`. La formation échoue en direct devant Marc.
**Correctif proposé** : Remplacer dans les supports `pays_livraison` → `nom_pays` (`dim_pays`) et `marge_brute` → mesure `[Marge Brute (prov.)]`.
**Effort** : S
**Bloque un livrable ?** : L05 — oui (qualité)

---

### F-09 — Quiz : « 6 transporteurs » alors que `dim_transporteur` en contient 8
**Sévérité** : MOYEN
**Nature** : Documentation
**Preuve** :
- `docs/05-formation/quiz-evaluation.md:77` → réponse Q5 : `C) 6 transporteurs au total après la mission`.
- `dim_transporteur.tmdl` (bloc `#table`) : 8 lignes — La Poste, Colis Privé, Chronopost, DHL, FedEx, UPS, **Postes Canada**, INCONNU. Soit 7 transporteurs réels (dont Postes Canada, dans le périmètre selon `livrables.md`) + INCONNU.
**Ce qui se passe** : Le quiz ignore Postes Canada (pourtant confirmé dans le périmètre) et la modalité INCONNU.
**Impact client** : Incohérence visible ; Marc peut douter du sérieux du référentiel.
**Correctif proposé** : Corriger la réponse Q5 (« 7 transporteurs, dont Postes Canada ; INCONNU = résidu non identifié »).
**Effort** : XS
**Bloque un livrable ?** : L05 — non

---

### F-10 — `mesures-dax.md` n'est pas strictement identique à `_Mesures.tmdl`
**Sévérité** : MOYEN
**Nature** : Documentation
**Preuve** : Mesures présentes dans `_Mesures.tmdl` et **absentes** de `powerbi/models/mesures-dax.md` :
- `Nb Articles` (`_Mesures.tmdl` `SUM(fact_lignes[quantity])`)
- `Coût Transport Facturé` (`SUM(fact_factures_transport[cout_transport])`)
- `Coût Facturé Rapproché`
- `Écart Réel vs Facturé`
- `Poids Total (kg)`
**Ce qui se passe** : Le référentiel documentaire prétend en pied de page « Mesures alignées sur `_Mesures.tmdl` — 14/07/2026 » mais omet 5 mesures.
**Impact client** : Documentation partiellement mensongère ; un utilisateur recopiant la doc ne reproduit pas le modèle.
**Correctif proposé** : Régénérer `mesures-dax.md` depuis `_Mesures.tmdl` (idéalement par script) pour garantir l'égalité.
**Effort** : S
**Bloque un livrable ?** : L06 — non (mais qualité doc)

---

### F-11 — Jointure factures↔colis par proximité de date : risque de faux rapprochement
**Sévérité** : MOYEN (→ MAJEUR à confirmer sur données réelles)
**Nature** : Modèle / Correction
**Preuve** (`expressions.tmdl`, `stg_factures_transport_resolu`) :
```
#"Colis resolu" = ... if Table.RowCount(candidats) = 0 then null
    else if Table.RowCount(candidats) = 1 then candidats{0}
    else Table.First(Table.Sort(
        Table.AddColumn(candidats, "delta", each ... Number.Abs(Duration.TotalDays([date_commande] - dfac)) ...),
        {{"delta", Order.Ascending}}))
```
**Algorithme reconstitué** : jointure `numero_suivi` (facture) ↔ `numero_suivi` (colis) ; si 0 candidat → non résolu ; si 1 → retenu ; si ≥ 2 (suivis recyclés, ~382 selon doc) → on retient le colis dont la **date de commande** est la plus proche de la **date de facture** ; **tie-break = `Table.First` après tri = arbitraire** (pas de départage stable). Fenêtre = illimitée (aucun seuil de jours max ; `delta` par défaut 1e9 si date nulle).
**Écart au devis** : Le devis impose la jointure **par numéro de suivi**. Le modèle joint bien par suivi, mais la **désambiguïsation** repose sur une heuristique de date, non contractuelle et faillible sur les suivis recyclés.
**Impact client** : Sur un suivi recyclé, la facture peut être rattachée au mauvais colis (donc mauvaise commande) si les deux commandes ont des dates voisines. Pas de plafond de fenêtre → rapprochements aberrants possibles.
**Correctif proposé** : Ajouter un **seuil de fenêtre** (ex. rejeter si `delta > N` jours) et un tie-break déterministe (`id_package` croissant). Journaliser les cas ≥ 2 candidats.
**Test de non-régression** : voir §4.
**Effort** : M
**Bloque un livrable ?** : L03 — à confirmer sur données réelles

---

### F-12 — Normalisation des clés incomplète (pas de gestion NBSP / zéros de tête / encodage)
**Sévérité** : MOYEN
**Nature** : Correction
**Preuve** :
- Colis : `fact_transport.tmdl` → `Text.Upper(Text.Trim([tracking_id]))`.
- Factures : `expressions.tmdl` → `Text.Upper(Text.Trim(Record.Field(_, suiviCol)))` et `Text.Upper(Text.Trim([#"N° de colis"]))`.
**Ce qui se passe** : `Text.Trim` retire les espaces ASCII mais **pas** les espaces insécables (U+00A0) fréquents dans les exports Excel/CSV FR, ni ne gère les zéros de tête. La normalisation est symétrique (bon point) mais insuffisante.
**Impact client** : Des rapprochements ratés à cause d'un caractère invisible → taux de matching sous-estimé et coûts non rattachés.
**Correctif proposé** : Ajouter `Text.Remove(Text.Replace(x, Character.FromNumber(160), ""), {" "})` ou un nettoyage regex, des deux côtés identiquement.
**Effort** : S
**Bloque un livrable ?** : L03 — non (mais qualité matching)

---

### F-13 — `fnNormaliserTransporteur` : identifiants 10 chiffres classés INCONNU (limite assumée)
**Sévérité** : MOYEN
**Nature** : Correction
**Preuve** : `expressions.tmdl` `fnNormaliserTransporteur` — commentaire : *« identifiants purement numériques à 10 chiffres restent ambigus … classés INCONNU — à valider »* ; branche finale `else "INCONNU"`.
**Ce qui se passe** : Toute la classification transporteur repose sur des motifs de tracking, sans colonne transporteur source. Les couvertures : `1Z`→UPS, `6A`(13)→La Poste, `Q013`→Postes Canada, `XW/XA/XS/XR`(13)→Chronopost, numérique 18→FedEx, 12→DHL, `Z8`/`1C`/numérique 8-9→Colis Privé. **Alignement strict avec les 8 libellés de `dim_transporteur` : OK** (mêmes 8 sorties). Taux d'INCONNU attendu : NON VÉRIFIÉ (dépend des données).
**Impact client** : Un taux d'INCONNU élevé fausserait la répartition par transporteur (axe non contractuel mais visible dans L04).
**Correctif proposé** : Mesurer le taux d'INCONNU sur données réelles (§4) ; documenter les motifs non couverts.
**Effort** : S
**Bloque un livrable ?** : L04 — non

---

### F-14 — Absence de slicer date, de thème et d'interactions configurées sur L04
**Sévérité** : MINEUR
**Nature** : Documentation / Correction
**Preuve** :
- `pages.json` : une seule page ; `page.json` : pas de fond/thème.
- Aucun `theme.json` référencé dans `report.json` (StaticResources non exploités pour un thème).
- Slicers présents : Pays (`visuals/0718293a4b1c2d3e4f506`) et Type (`visuals/18293a4b1c2d3e4f50607`). **Pas de slicer date** malgré `dim_date` et les mesures de time-intelligence (`Marge YTD`, `CA Mois Précédent`).
- Interactions entre visuels : non configurées (aucun `visualInteractions` dans `page.json`).
**Impact client** : Impossible de filtrer par période ; rendu non charté ; accessibilité/ordre de tabulation par défaut (les `tabOrder` sont 1000..8000, non séquentiels métier).
**Correctif proposé** : Ajouter un slicer `dim_date`, un `theme.json`, et définir les interactions.
**Effort** : S
**Bloque un livrable ?** : L04 — non (mais qualité)

---

### F-15 — Performance refresh : CSV 187 Mo, NestedJoin ~950k lignes, staging évalué 2×, pas d'incrémental
**Sévérité** : MOYEN
**Nature** : Performance
**Preuve** :
- `expressions.tmdl` `fnSharePointLireCsv` lit `customer_order.csv` (179 Mo constaté) via `SharePoint.Files` (liste récursive complète).
- `stg_factures_transport_resolu` fait `Table.NestedJoin` colis↔commandes puis factures↔candidats, et est **référencé par 2 tables** (`fact_factures_transport` **et** `fact_transport` via `#"Ids factures"`) → double évaluation probable (pas de mise en cache garantie).
- Aucun `partition` incrémental déclaré (mode `import` simple partout).
**Impact client** : Refresh long/instable dans le Service (timeout SharePoint, mémoire). `SharePoint.Files` liste toute la bibliothèque avant de filtrer.
**Correctif proposé** : Passer à `SharePoint.Contents` ciblé, activer le pliage/staging via dataflow, envisager refresh incrémental sur `date_commande`. NON VÉRIFIÉ en l'absence de refresh réel.
**Effort** : L
**Bloque un livrable ?** : non (mais risque exploitation)

---

### F-16 — `[Commandes Sans Colis]` : RELATEDTABLE dans un FILTER sur ~1M lignes
**Sévérité** : MINEUR
**Nature** : Performance
**Preuve** : `_Mesures.tmdl` → `Commandes Sans Colis = COUNTROWS(FILTER(fact_commandes, ... COUNTROWS(RELATEDTABLE(fact_transport)) = 0))`.
**Impact client** : Mesure de contrôle coûteuse ; à éviter sur un visuel interactif. Acceptable en usage ponctuel.
**Correctif proposé** : Précalculer un flag `a_colis` en colonne à l'ETL.
**Effort** : S
**Bloque un livrable ?** : non

---

### F-17 — URL SharePoint tenant en dur dans `expressions.tmdl`
**Sévérité** : MINEUR
**Nature** : Hygiène
**Preuve** : `expressions.tmdl` → `expression SharePointSiteURL = "https://lirekacom.sharepoint.com/sites/Lireka" meta [...]`.
**Ce qui se passe** : Le paramètre est un vrai domaine tenant client versionné (pas un secret, mais donnée d'environnement en dur). Contrairement au libellé mission « non renseigné », il **est** renseigné.
**Impact client** : Faible ; à externaliser proprement en paramètre d'environnement.
**Correctif proposé** : Laisser la valeur par défaut vide ou en placeholder documenté.
**Effort** : XS
**Bloque un livrable ?** : non

---

### F-18 — Hygiène données : correcte (pas de PII versionnée) — à confirmer
**Sévérité** : MINEUR (constat positif)
**Nature** : Hygiène
**Preuve** :
- `.gitignore` : `Power_BI_Datawarehouse/**`, `data/raw/**`, `data/staging/**`, `data/processed/**`, `*.pbix`, `credentials.json`, `*.pem`, `*.key`, `scripts/validation/*_output.json`.
- `git ls-files | grep "Données_Backend"` → **0 fichier tracké** (les CSV 47–179 Mo ne sont pas dans Git).
- `data/samples/` contient des échantillons (`commandes_202606.csv`, dossiers transporteurs).
**Réserve** : NON VÉRIFIÉ que `data/samples/` est réellement anonymisé (contenu non inspecté ligne à ligne). Procédure : `head` sur les samples + recherche de patterns email/nom réel.
**Correctif proposé** : Documenter la procédure d'anonymisation des samples.
**Effort** : XS
**Bloque un livrable ?** : non

---

### F-19 — Scripts de validation non reproductibles sans l'entrepôt local
**Sévérité** : MINEUR
**Nature** : Hygiène
**Preuve** : `scripts/validation/*.py` → `ROOT = Path(__file__).resolve().parents[2] / "Power_BI_Datawarehouse"` (dossier gitignoré, absent du repo cloné).
**Ce qui se passe** : Les scripts pointent vers un dossier local non versionné (normal vu la taille/PII), donc non exécutables tels quels sur un clone. Chemin **dans** le repo (pas hors repo), mais dépend de données absentes.
**Impact client** : Un tiers ne peut rejouer les audits sans les données — attendu, mais à paramétrer.
**Correctif proposé** : Paramétrer via variable d'environnement `LIREKA_DWH` avec fallback documenté.
**Effort** : S
**Bloque un livrable ?** : non

---

## 4. À rejouer sur données réelles (demain)

| Contrôle | Comment | Seuil OK |
|----------|---------|----------|
| Marge DAX vs `gross_profit_eur` | Ouvrir le modèle, lire `[Écart Marge vs Backend]` au total et par pays/type | Écart expliqué à 100 % par les postes manquants (F-04) ; sinon investiguer |
| Faux rapprochements par date (F-11) | Sur `stg_factures_transport_resolu`, isoler les `numero_suivi` à ≥ 2 candidats et compter les `delta` > 7 j retenus ; script à ajouter dans `scripts/validation/` | 0 rapprochement avec `delta > N` jours (N à fixer avec Marc) |
| Taux de matching honnête (F-07) | Lire `[Taux Matching]` **et** une variante hors CANCELLED | Écart entre les deux documenté ; publier la variante hors CANCELLED |
| Taux d'INCONNU transporteur (F-13) | `[Nb Colis]` filtré `transporteur = "INCONNU"` / `[Nb Colis]` | < 5 % (seuil indicatif à valider) |
| Impact NBSP/zéros (F-12) | Comparer le taux de matching avant/après nettoyage renforcé | Gain nul = pas de problème ; gain > 0 = corriger |
| Chargement & relations (F-06) | Ouvrir `Lireka_Profitabilite.pbip` ; noter les relations inactives en vue Modèle | Aucune relation désactivée non voulue |
| Refresh Service (F-15) | Publier et lancer un refresh planifié | Refresh < timeout, sans erreur mémoire |
| Douanes (F-04) | Somme de `fact_transport[duties_taxes_eur]` par pays hors-UE | Cohérente avec attente Marc (FedEx MA/TN) |

---

## 5. Plan de remédiation ordonné

> **Note de périmètre (15/07/2026)** : la formule de marge à 7 postes a été confirmée par
> Marc Bordier (Slack, 13/07/2026) — elle n'est pas une proposition d'audit. Voir
> `project/perimetre-verrouille.md`. Les points ci-dessous restent ouverts (CANCELLED,
> « if relevant », fenêtre de jointure, Colis Privé).

**Bloc 0 — Décisions à arbitrer par Marc AVANT tout code (métier) :**
1. **Formule de marge** définitive (postes inclus : shipping_fee, commissions, douanes, inbound, fournitures ?). — bloque F-01/F-02/F-04.
2. **Coût transport** : marge sur coût **facturé** (quand dispo) ou **estimé** ? — bloque F-02.
3. **Statut CANCELLED** : inclus ou exclu du périmètre analytique ? — bloque F-07.
4. **Clé de jointure** : accepte-t-il la désambiguïsation par date, avec fenêtre plafonnée ? — bloque F-11.
5. **Périmètre Colis Privé / Postes Canada** : coût estimé suffisant ? — cf. §6.

**Bloc 1 — Corrections techniques (après arbitrage), par dépendance :**
1. (2 h) Implémenter `[Coût Transport Retenu]` = facturé si `reel` sinon estimé (F-02) + renommer `source_cout` (F-03).
2. (3 h) Construire la mesure de marge conforme à la décision Marc, importer postes manquants (F-04).
3. (2 h) Brancher la marge sur les 2 bar-charts pays/type + carte pays×type ; supprimer la textbox (F-01).
4. (2 h) Déclarer cardinalités/`isActive`/`crossFilter` sur toutes les relations ; désactiver les chemins redondants (F-06).
5. (1 h) Corriger `[Écart Coût Transport]` et le titre de carte (F-05).
6. (1 h) `[Taux Matching (hors CANCELLED)]` (F-07).
7. (1 h) Plafond de fenêtre + tie-break déterministe dans la résolution par date (F-11).
8. (0,5 h) Renforcer la normalisation des clés (NBSP) des deux côtés (F-12).

**Bloc 2 — Documentation & formation :**
9. (1 h) Corriger `session-02`, `session-03`, `quiz` (F-08, F-09).
10. (0,5 h) Régénérer `mesures-dax.md` depuis `_Mesures.tmdl` (F-10).
11. (1 h) Ajouter slicer date + `theme.json` + interactions (F-14).

**Bloc 3 — Performance / hygiène (post-livraison) :**
12. (L) Optimiser lecture SharePoint + refresh incrémental (F-15).
13. (0,5 h) Paramétrer chemins scripts (F-19), externaliser `SharePointSiteURL` (F-17).

**Total corrections bloquantes L04 (blocs 1.1→1.6) : ~11 h.**

---

## 6. Questions à poser à Marc (prêtes à envoyer — max 6)

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

---

*Audit produit en lecture seule — aucun fichier du modèle, du rapport ou des scripts n'a été modifié.*
