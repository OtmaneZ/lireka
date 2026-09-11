# Outils d'audit interne — ZineInsights

**Statut : usage interne, non contractuel.**

Ces scripts ne sont pas un livrable du devis (voir `docs/01-cadrage/devis.md`). Ils servent de
preuve et de contrôle pour les livrables suivants :

- Intégration des transporteurs (devis #1)
- Jointure factures ↔ commandes (devis #3)
- Dashboard profitabilité (devis #4)

## Emplacement des scripts

Les scripts vivent dans **`scripts/validation/`** — source unique. Ce dossier ne contenait
qu'une copie divergeant d'une ligne (`sys.path`), retirée le 28/08/2026 pour éviter que les
deux versions dérivent.

| Script | Rôle |
|--------|------|
| `scripts/validation/impl_checks.py` | Réplique la logique Power Query (jointure facture↔colis, dédup récaps) en pandas — contrôle avant/après |
| `scripts/validation/transport_source_checks.py` | Simule le flag `source_cout` et les mesures de matching transport |
| `scripts/validation/key_cleanup_audit.py` | Audit des clés / `tracking_id` dupliqués et chevauchements récaps |
| `scripts/validation/inspect_pbix.py` | Inspection des `.pbix` existants (tables, mesures, sources M) |
| `scripts/validation/audit_qualite_postgres.py` | Audit qualité des vues `analytics_views` (lecture seule) |

Les sorties (`*_out/`) contiennent des données de production et ne sont pas versionnées.
