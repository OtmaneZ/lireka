# Lireka × ZineInsights — Power BI

Mission 4 jours (1 800 € HT) : intégration transporteurs et commandes, jointure par n° de suivi, dashboard profitabilité et formation.

## Périmètre contractuel (devis)

1. Intégration **La Poste**, **Colis Privé**, **Chronopost**
2. Import et structuration du **CSV commandes** backend
3. **Jointure** factures ↔ commandes par numéro de suivi
4. **Dashboards de profitabilité** — marge brute par pays, par type de commande
5. **Formation** des utilisateurs
6. **Documentation du processus**

→ [`project/devis.md`](project/devis.md) · [`project/livrables.md`](project/livrables.md)

## Structure du dépôt

```
lireka/
├── project/              devis.md, livrables.md
├── docs/
│   ├── 04-processus/     processus-etl-gouvernance.md (L06)
│   └── 05-formation/     programme-formation.md, session-01-bases.md (L05)
├── powerbi/              modèle PBIP + rapport profitabilité L04
├── scripts/validation/   scripts de contrôle technique
├── data/samples/         échantillons anonymisés
└── templates/            schémas CSV cibles
```
