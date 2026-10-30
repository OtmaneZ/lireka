# Projet Lireka : notes de travail (usage interne, non livré au client)

## Environnement de travail d'Otmane

- La VM Windows de Lireka a peu de mémoire vive. Power BI Desktop y est inutilisable pour vérifier le rapport : on ne peut pas **actualiser**, ni voir les données ou les visuels en direct.
- Sur la VM, on peut seulement **ouvrir le `.pbip` et publier** dans le Service. Il n'y a jamais de vérification visuelle à demander dans Desktop sur la VM.
- Les vérifications se font dans le **Service** (app.powerbi.com, espace « LIREKA - Power BI »), après publication et actualisation du modèle (Actualiser maintenant, puis historique d'actualisation).
- Pour vérifier du code ou des chiffres : requêtes DAX dans le Service (« Écrire des requêtes DAX »).
- Pour interroger la base PostgreSQL (SQL), **ne plus passer par Desktop** (Obtenir les données > PostgreSQL > Options avancées : trop lent). Sur la VM, `psql` est installé et Otmane a une fonction PowerShell `q` : `q "SELECT ..."` exécute la requête directement (SQL entre guillemets doubles, sans guillemet double à l'intérieur ; schéma `analytics_views`). Les requêtes peuvent être chronométrées dans le terminal. Toujours donner les requêtes SQL sous la forme `q "..."`, et pour chronométrer : `Measure-Command { q "..." | Out-Host }`.
- **Définition de `q`** (à recoller dans chaque nouveau terminal PowerShell de la VM : elle n'est pas conservée). Quand Otmane demande d'activer `q`, lui donner ce bloc à coller, sans mot de passe (`psql` le demande, ou il est déjà en variable d'environnement) :
  ```powershell
  function q($sql) { & C:\pgsql\pgsql\bin\psql.exe -h 10.111.119.1 -d analytics -U liber_power_bi -c $sql }
  ```
- Ne jamais écrire « vérifie dans Desktop » : écrire « publie, actualise, puis vérifie dans le Service ».

## Séquence de livraison (VM)

1. Télécharger le zip de `main` dans `Téléchargements` (`lireka-main.zip`).
2. `C:\lireka\livrer.ps1 -Message '...'` : livre dans le dépôt Git de la VM (`C:\git\lireka.git`).
3. Dans `C:\lireka\depot` : `git restore .` puis `git pull`. Si `pull` échoue (historique différent), recloner : `git clone C:\git\lireka.git C:\lireka\depot`.
4. Fermer complètement Desktop, ouvrir `Lireka_Profitabilite.pbip`, publier, puis actualiser le modèle dans le Service.
5. `git restore .` après publication (Desktop réécrit des fichiers).

**Attention : `C:\lireka\livrer.ps1` est une copie.** Quand `tools/livraison/livrer.ps1` change sur `main` (garde-fou ajouté le 30/10/2026), la VM garde l'ancienne version tant qu'on ne la remplace pas. Avant l'étape 2 (le script supprime le zip à la fin), mettre à jour la copie depuis le zip :
```powershell
Expand-Archive $HOME\Downloads\lireka-main.zip C:\lireka\maj -Force
Copy-Item C:\lireka\maj\lireka-main\tools\livraison\livrer.ps1 C:\lireka\livrer.ps1 -Force
Remove-Item C:\lireka\maj -Recurse -Force
Select-String -Path C:\lireka\livrer.ps1 -Pattern 'ChangementsRecuperes' -Quiet
```
La dernière commande doit répondre `True` : c'est bien la version avec le garde-fou.

## Règles de travail

- Pousser directement sur `main` (demande d'Otmane du 27/10/2026).
- Contenu destiné au client : aucun tiret cadratin, aucun point médian. Communication avec COEX et Inforeso en anglais.
- Jamais de mot de passe, de clé ni de secret dans le dépôt ou dans un message.
