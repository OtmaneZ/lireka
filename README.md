# Lireka × ZineInsights — Power BI

Mission 4 jours (1 800 € HT) : intégration transporteurs et commandes, jointure par n° de suivi, dashboard profitabilité et formation.

## Périmètre contractuel (devis)

1. Intégration **La Poste**, **Colis Privé**, **Chronopost**
2. Import et structuration des **commandes** backend (PostgreSQL)
3. **Jointure** factures ↔ commandes par numéro de suivi
4. **Dashboards de profitabilité** — marge brute par pays, par type de commande
5. **Formation** des utilisateurs
6. **Documentation du processus**

→ [`docs/01-cadrage/devis.md`](docs/01-cadrage/devis.md) · [`docs/01-cadrage/livrables.md`](docs/01-cadrage/livrables.md)

## Structure du dépôt

```
lireka/
├── docs/
│   ├── 01-cadrage/         devis, livrables, cadrage, maquettes (historique)
│   ├── 04-processus/       processus-etl-gouvernance.md — référence du chargement et du refresh (L06)
│   ├── 05-formation/       programme et supports de formation (L05)
│   ├── doc_reunion_4_08/   recette chiffrée des KPI, décision sur les KPI publiés
│   └── notes-techniques/   limites et dettes connues des données source
├── powerbi/                modèle PBIP (SemanticModel + Report) ; models/mesures-dax.md = référentiel des mesures
├── scripts/validation/     scripts de contrôle (usage interne)
└── tools/audit-interne/    README de périmètre
```

## Setup local (data analyst)

1. **Accès à la base** — le modèle lit PostgreSQL (`analytics`, schéma `analytics_views`) sur le réseau COex : tunnel WireGuard actif sur le poste (ou travail sur la VM de la passerelle).
2. **Power BI Desktop** (Windows, 16 Go de RAM conseillés) — ouvrir `powerbi/Lireka_Profitabilite.pbip`. Paramètres (*Transformer les données* → *Gérer les paramètres*) : `PgServer`, `PgDatabase`, `PgSchema`. Au premier *Actualiser*, saisir les identifiants PostgreSQL et approuver les requêtes SQL natives.
3. **Publication** — *Accueil* → *Publier* vers l'espace de travail « Lireka Profitabilité », en remplaçant le modèle existant. Le refresh quotidien (6:00, Europe/Paris) passe par la passerelle Lireka-Gateway (VM Azure, tunnel WireGuard). Détails : [`docs/04-processus/processus-etl-gouvernance.md`](docs/04-processus/processus-etl-gouvernance.md).
4. **Python** (scripts de contrôle) — depuis la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PGHOST = "<hôte PostgreSQL>"; $env:PGUSER = "<utilisateur>"; $env:PGPASSWORD = "<mot de passe>"
```
