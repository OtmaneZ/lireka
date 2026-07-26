# Lireka × ZineInsights — Power BI

Mission 4 jours (1 800 € HT) : intégration transporteurs et commandes, jointure par n° de suivi, dashboard profitabilité et formation.

## Périmètre contractuel (devis)

1. Intégration **La Poste**, **Colis Privé**, **Chronopost**
2. Import et structuration du **CSV commandes** backend
3. **Jointure** factures ↔ commandes par numéro de suivi
4. **Dashboards de profitabilité** — marge brute par pays, par type de commande
5. **Formation** des utilisateurs
6. **Documentation du processus**

→ [`docs/01-cadrage/devis.md`](docs/01-cadrage/devis.md) · [`docs/01-cadrage/livrables.md`](docs/01-cadrage/livrables.md)

## Structure du dépôt

```
lireka/
├── docs/
│   ├── 01-cadrage/       devis.md, livrables.md, cadrage
│   ├── 04-processus/     processus-etl-gouvernance.md (L06)
│   └── 05-formation/     programme-formation.md, session-01-bases.md (L05)
├── powerbi/              modèle PBIP + rapport profitabilité L04
├── tools/audit-interne/  scripts de contrôle technique (usage interne)
└── scripts/validation/   scripts de contrôle (usage interne)
```

## Setup local (data analyst)

1. **Données** — copier `Power_BI_Datawarehouse/` depuis SharePoint/Drive à la racine du repo (non versionné).
2. **Power BI** — ouvrir `powerbi/Lireka_Profitabilite.pbip` ; vérifier le paramètre `LocalRootPath` (*Transformer les données* → *Gérer les paramètres*).
3. **Chronopost 2026** — le modèle attend `Dashboards_transporteurs/CHRONOPOST Dashboard PowerBI/2026_CHRONOPOST_V2.csv`.
4. **Python** (scripts de contrôle) :

```powershell
cd c:\dev\projets\lireka
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Override optionnel de l'entrepôt : `$env:LIREKA_DWH = "chemin\vers\Power_BI_Datawarehouse"`.
