# Cohérence périmètre — journal des corrections (15/07/2026)

> Propagation du verrou `project/perimetre-verrouille.md` (devis + formule Slack 13/07/2026).

| Fichier | Contradiction initiale | Correction appliquée | Vérifié |
|---------|------------------------|----------------------|---------|
| `AUDIT.md` | F-04 « à arbitrer » ; §5 Bloc 0 #1 formule bloquante ; §6 Q1 demande confirmation formule ; Q6 douanes obsolète | Bandeau 15/07 ; F-04 réécrit (actée + implémentée) ; Bloc 0 #1 → shipping revenue ; §6 = 5 questions (Q1 révisée, Q6 supprimée) ; F-01 correctif aligné | ✅ |
| `IMPLEMENTATION.md` | § « Reste en attente » reprenait Q1 formule + Q6 douanes | Section remplacée par les 5 questions à jour ; renvoi `perimetre-verrouille.md` | ✅ |
| `README.md` | « Formule à valider finance » ; pas de lien périmètre | Bandeau + prérequis corrigés ; lien dans « Liens utiles » | ✅ |
| `project/planning.md` | Dépendance « formule bloque J3 » | Bandeau ; dépendance marquée ✅ actée | ✅ |
| `project/risques.md` | R05 formule non validée ; H04 à valider finance | Bandeau ; R05 résolu ; H04 actée | ✅ |
| `project/devis.md` | Pas de renvoi post-signature | Pied de page → `perimetre-verrouille.md` (corps intact) | ✅ |
| `project/livrables.md` | L04 sans définition marge brute | Note L04 → `perimetre-verrouille.md` | ✅ |
| `docs/01-cadrage/checklist-acces-donnees.md` | Q2 formule non cochée | Bandeau ; Q2 ✅ Slack 13/07 | ✅ |
| `docs/01-cadrage/cahier-des-charges.md` | Prérequis formule non validée | Bandeau ; prérequis ✅ actée | ✅ |
| `docs/01-cadrage/inventaire-sources.md` | Checklist formule non cochée | Bandeau ; item ✅ actée | ✅ |
| `communications/emails/02-demande-acces.md` | Demande formule non arbitrée | Note historique ; Q2 corrigée | ✅ |
| `communications/proposition-commerciale.md` | Prérequis formule à valider | Bandeau ; prérequis ✅ actée | ✅ |
| `docs/05-formation/quiz-evaluation.md` | Q3 réponse formule 3 postes sans étiquette | Réponse pédagogique + formule 7 postes + lien périmètre | ✅ |
| `powerbi/models/mesures-dax.md` | `Marge Brute (prov.)` présentée comme principale | Section marge ; `Marge Brute` documentée actée ; prov = contrôle | ✅ |
| `docs/03-dictionnaire-donnees/dictionnaire-donnees.md` | Table et glossaire centrés sur prov | Bandeau ; `Marge Brute` en tête ; prov = contrôle | ✅ |
| `docs/02-architecture/architecture-data.md` | `Marge Brute (prov.)` comme mesure principale | `Marge Brute` référence ; prov = contrôle historique | ✅ |
| `powerbi/models/modeles-semanticques.md` | prov « en attente validation Marc » | `Marge Brute` actée + prov contrôle | ✅ |
| `docs/04-processus/processus-etl-gouvernance.md` | prov provisoire, validation requise | `Marge Brute` référence actée ; prov = contrôle | ✅ |

## Liens `perimetre-verrouille.md` confirmés

| Fichier | Présent |
|---------|---------|
| `README.md` | ✅ |
| `project/devis.md` | ✅ |
| `project/livrables.md` | ✅ |
| `AUDIT.md` | ✅ |
| `IMPLEMENTATION.md` | ✅ |
| `_Mesures.tmdl` | ✅ |

## Occurrences légitimes conservées

- `_Mesures.tmdl` : mesure `Marge Brute (prov.)` + commentaires « FORMULE PROVISOIRE » (mesure de contrôle)
- `AUDIT.md` §1–§3 : constats historiques du 14/07 (bandeau explicite)
- `mesures-dax.md` : sections `Marge Brute (prov.)` étiquetées contrôle/comparaison
