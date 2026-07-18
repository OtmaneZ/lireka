# Outils d'audit interne — ZineInsights

Ce dossier contient des scripts de contrôle qualité et de validation technique utilisés par ZineInsights pendant la mission Lireka.

**Statut : usage interne, non contractuel.**

Ces scripts ne sont pas un livrable du devis (voir `docs/01-cadrage/devis.md`). Ils servent de preuve et de contrôle pour les livrables suivants :
- Intégration des transporteurs (devis #1)
- Jointure factures ↔ commandes (devis #3)
- Dashboard profitabilité (devis #4)

Fichiers :
- `impl_checks.py` — réplique la logique Power Query (jointure facture↔colis, dédup récaps) en pandas, contrôle avant/après
- `transport_source_checks.py` — simule le flag source_cout et les mesures de matching transport
- `key_cleanup_audit.py` — audit des clés/tracking_id dupliqués et chevauchements récaps
- `inspect_pbix.py` — inspection des .pbix existants (tables, mesures, sources M)
