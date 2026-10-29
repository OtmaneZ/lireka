# Lireka, rapport Power BI de profitabilité

Projet Power BI (format PBIP) du rapport **Lireka_Profitabilite** : chiffre d'affaires, marge brute et coûts par canal, pays, transporteur et commande, à partir de la base analytique Lireka (PostgreSQL, schéma `analytics_views`).

Le projet ne contient aucune donnée : uniquement la définition du modèle et des pages. Les données sont lues dans la base à chaque actualisation.

## Contenu du dépôt

```
lireka/
├── powerbi/
│   ├── Lireka_Profitabilite.pbip            fichier à ouvrir dans Power BI Desktop
│   ├── Lireka_Profitabilite.SemanticModel/  modèle sémantique (tables, relations, mesures)
│   └── Lireka_Profitabilite.Report/         pages et visuels du rapport
├── docs/
│   ├── 1-guide-du-rapport.md    les pages et les indicateurs
│   ├── 2-donnees-et-calculs.md  sources, chargement, règles de calcul, actualisation
│   ├── 3-git-et-publication.md  récupérer, modifier, publier ; administration du serveur Git
│   ├── 4-passation.md           accès, architecture, exploitation, contacts, points connus
│   ├── 5-formation.md           support de la session de prise en main
│   └── 6-recette.md             compte rendu de recette
└── deploiement/vps/        scripts d'administration du serveur Git
```

## Ouvrir le projet

1. **Accès à la base** : le modèle lit PostgreSQL (`analytics`, schéma `analytics_views`) sur le réseau COEX. Il faut le tunnel WireGuard actif sur le poste, ou travailler sur le VPS de la passerelle.
2. **Power BI Desktop** (Windows, 16 Go de RAM conseillés) : ouvrir `powerbi/Lireka_Profitabilite.pbip`. Paramètres (*Transformer les données* > *Gérer les paramètres*) : `PgServer`, `PgDatabase`, `PgSchema`. Au premier *Actualiser*, saisir les identifiants PostgreSQL et approuver les requêtes SQL natives.
3. **Sans accès à la base**, le projet s'ouvre sans données : on peut modifier les pages et les mesures, puis publier ; le Service recharge les données par la passerelle.

## Publier et actualiser

- **Publication** : *Accueil* > *Publier* vers l'espace de travail « LIREKA - Power BI », en remplaçant le modèle existant.
- **Actualisation** : quotidienne à 8:00 (Europe/Paris), par la passerelle Lireka-Gateway installée sur le VPS (tunnel WireGuard vers la base). Détails : [`docs/2-donnees-et-calculs.md`](docs/2-donnees-et-calculs.md).

## Travailler avec Git

Le dépôt central est sur le VPS de Lireka (`C:\git\lireka.git`), accessible en SSH par clé. Récupérer, modifier, publier et administrer : [`docs/3-git-et-publication.md`](docs/3-git-et-publication.md).

## Règles de calcul

- Chiffre d'affaires **hors TVA**, frais de port inclus (`order_amount_excl_vat_eur`), hors commandes annulées.
- Marge brute : chiffre d'affaires moins coût d'achat, transport amont, transport sortant, droits et taxes, commissions marketplace et fournitures d'expédition.
- Détail des règles : [`docs/2-donnees-et-calculs.md`](docs/2-donnees-et-calculs.md) ; pages et indicateurs : [`docs/1-guide-du-rapport.md`](docs/1-guide-du-rapport.md).
