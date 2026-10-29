# Projet Lireka : notes de travail (usage interne, non livré au client)

## Environnement de travail d'Otmane

- La VM Windows de Lireka a peu de mémoire vive. Power BI Desktop y est inutilisable pour vérifier le rapport : on ne peut pas **actualiser**, ni voir les données ou les visuels en direct.
- Sur la VM, on peut seulement **ouvrir le `.pbip` et publier** dans le Service. Il n'y a jamais de vérification visuelle à demander dans Desktop sur la VM.
- Les vérifications se font dans le **Service** (app.powerbi.com, espace « LIREKA - Power BI »), après publication et actualisation du modèle (Actualiser maintenant, puis historique d'actualisation).
- Pour vérifier du code ou des chiffres : requêtes DAX dans le Service (« Écrire des requêtes DAX »), ou SQL via le connecteur PostgreSQL de Desktop sur la VM (Obtenir les données > PostgreSQL > Options avancées).
- Ne jamais écrire « vérifie dans Desktop » : écrire « publie, actualise, puis vérifie dans le Service ».

## Séquence de livraison (VM)

1. Télécharger le zip de `main` dans `Téléchargements` (`lireka-main.zip`).
2. `C:\lireka\livrer.ps1 -Message '...'` : livre dans le dépôt Git de la VM (`C:\git\lireka.git`).
3. Dans `C:\lireka\depot` : `git restore .` puis `git pull`. Si `pull` échoue (historique différent), recloner : `git clone C:\git\lireka.git C:\lireka\depot`.
4. Fermer complètement Desktop, ouvrir `Lireka_Profitabilite.pbip`, publier, puis actualiser le modèle dans le Service.
5. `git restore .` après publication (Desktop réécrit des fichiers).

## Règles de travail

- Pousser directement sur `main` (demande d'Otmane du 27/10/2026).
- Contenu destiné au client : aucun tiret cadratin, aucun point médian. Communication avec COEX et Inforeso en anglais.
- Jamais de mot de passe, de clé ni de secret dans le dépôt ou dans un message.
