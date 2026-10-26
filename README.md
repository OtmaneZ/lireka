# Lireka, rapport Power BI de profitabilité

Projet Power BI (format PBIP) du rapport **Lireka_Profitabilite** : chiffre d'affaires, marge brute et coûts par canal, pays, transporteur et commande, à partir de la base analytique Lireka (PostgreSQL, schéma `analytics_views`).

Le projet ne contient aucune donnée : uniquement la définition du modèle et des pages. Les données sont lues dans la base à chaque actualisation.

## Contenu du dépôt

```
lireka/
├── powerbi/
│   ├── Lireka_Profitabilite.pbip            fichier à ouvrir dans Power BI Desktop
│   ├── Lireka_Profitabilite.SemanticModel/  modèle sémantique (tables, relations, mesures)
│   ├── Lireka_Profitabilite.Report/         pages et visuels du rapport
│   └── models/                              référentiel des mesures DAX
├── docs/
│   ├── 04-processus/       chargement des données et actualisation (documentation du processus)
│   ├── 05-formation/       supports de formation
│   ├── 06-exploitation/    serveur Git du VPS : accès, usage, dépannage
│   ├── doc_reunion_4_08/   règles de calcul des KPI publiés et recette chiffrée
│   └── notes-techniques/   limites connues des données source
└── deploiement/vps/        scripts d'administration du serveur Git
```

## Ouvrir le projet

1. **Accès à la base** : le modèle lit PostgreSQL (`analytics`, schéma `analytics_views`) sur le réseau COEX. Il faut le tunnel WireGuard actif sur le poste, ou travailler sur le VPS de la passerelle.
2. **Power BI Desktop** (Windows, 16 Go de RAM conseillés) : ouvrir `powerbi/Lireka_Profitabilite.pbip`. Paramètres (*Transformer les données* > *Gérer les paramètres*) : `PgServer`, `PgDatabase`, `PgSchema`. Au premier *Actualiser*, saisir les identifiants PostgreSQL et approuver les requêtes SQL natives.
3. **Sans accès à la base**, le projet s'ouvre sans données : on peut modifier les pages et les mesures, puis publier ; le Service recharge les données par la passerelle.

## Publier et actualiser

- **Publication** : *Accueil* > *Publier* vers l'espace de travail « LIREKA - Power BI », en remplaçant le modèle existant.
- **Actualisation** : quotidienne à 6:00 (Europe/Paris), par la passerelle Lireka-Gateway installée sur le VPS (tunnel WireGuard vers la base). Détails : [`docs/04-processus/processus-etl-gouvernance.md`](docs/04-processus/processus-etl-gouvernance.md).

## Travailler avec Git

Le dépôt central est sur le VPS de Lireka (`C:\git\lireka.git`), accessible en SSH par clé. Installation, ajout d'une personne et commandes du quotidien : [`docs/06-exploitation/serveur-git-vps.md`](docs/06-exploitation/serveur-git-vps.md).

## Règles de calcul

- Chiffre d'affaires **hors TVA**, frais de port inclus (`order_amount_excl_vat_eur`), hors commandes annulées.
- Marge brute : chiffre d'affaires moins coût d'achat, transport amont, transport sortant, droits et taxes, commissions marketplace et fournitures d'expédition.
- Référentiel complet des mesures : [`powerbi/models/mesures-dax.md`](powerbi/models/mesures-dax.md).
