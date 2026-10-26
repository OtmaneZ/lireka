# 3. Git et publication

Comment récupérer le projet, le modifier à plusieurs et publier une mise à jour dans le Service Power BI.

---

## 1. Le dépôt Git de Lireka

Le projet est versionné dans un dépôt Git hébergé sur le VPS Windows de Lireka, la machine qui porte aussi la passerelle Power BI.

| Élément | Valeur |
|---|---|
| Serveur | VPS Lireka, `20.19.33.4` |
| Dépôt central | `C:\git\lireka.git` (branche `main`) |
| Accès | SSH, par clé uniquement (aucun mot de passe accepté) |
| Personnes autorisées | membres du groupe Windows local `lireka-git` |
| Adresse de clonage | `<utilisateur>@20.19.33.4:C:/git/lireka.git` |

L'historique est protégé : il est impossible de le réécrire ou de supprimer la branche `main` depuis un poste.

---

## 2. Première installation sur un poste

1. Installer **Git for Windows** (https://git-scm.com/download/win, options par défaut) et **Power BI Desktop**.
2. Créer sa clé SSH dans PowerShell :
   ```powershell
   ssh-keygen -t ed25519 -C "prenom.nom@lireka"
   ```
   Valider l'emplacement proposé. Une phrase secrète est recommandée.
3. Transmettre à l'administrateur du VPS le contenu de `%USERPROFILE%\.ssh\id_ed25519.pub` (clé **publique**, qui peut circuler par e-mail). Le fichier `id_ed25519` sans `.pub` est la clé privée : il ne quitte jamais le poste.
4. Une fois l'accès ouvert (section 6), récupérer le projet :
   ```powershell
   cd $HOME\Documents
   git clone prenom.nom@20.19.33.4:C:/git/lireka.git
   ```
   À la première connexion, vérifier que l'empreinte affichée correspond à celle communiquée par l'administrateur, puis répondre `yes`.

---

## 3. Modifier le rapport

1. **Avant de commencer** : `git pull`, pour partir de la dernière version.
2. Ouvrir `lireka\powerbi\Lireka_Profitabilite.pbip` dans Power BI Desktop.
3. Modifier, puis **Fichier > Enregistrer**. Desktop met à jour les fichiers du dossier `powerbi\`.
4. **Enregistrer la modification dans Git** :
   ```powershell
   git add -A
   git commit -m "Ajout du graphique X sur la page Marketplaces"
   git push
   ```

Les fichiers du dossier `powerbi\` sont gérés par Power BI Desktop : ne pas les modifier à la main.

---

## 4. Publier dans le Service Power BI

1. Dans Power BI Desktop, connecté avec un compte Lireka disposant d'une licence Pro : **Accueil > Publier**.
2. Choisir l'espace de travail **LIREKA - Power BI**, puis **Remplacer** le modèle et le rapport existants.
3. Dans le Service, ouvrir le modèle sémantique **Lireka_Profitabilite** > **Actualiser maintenant**.
4. Contrôler **Historique d'actualisation** : la ligne doit indiquer « Completed », sans avertissement.

La connexion à la passerelle, les identifiants de la base et l'actualisation planifiée de 6:00 sont conservés lors d'un remplacement.

Si le poste n'a pas accès à la base (pas de tunnel WireGuard), le projet s'ouvre sans données : on peut quand même modifier et publier ; c'est le Service qui recharge les données par la passerelle. Ne pas lancer « Actualiser » dans Desktop dans ce cas.

---

## 5. Travailler à plusieurs

| Règle | Pourquoi |
|---|---|
| Une seule personne modifie le rapport à la fois ; prévenir l'équipe avant de commencer | Deux modifications simultanées des mêmes pages sont difficiles à fusionner |
| `git pull` avant de commencer, `git push` dès la modification terminée | Chacun travaille sur la dernière version |
| Des commits courts, avec un message qui dit ce qui a changé | L'historique reste lisible et réversible |
| Publier dans le Service seulement ce qui a été poussé dans Git | Le Service et le dépôt restent identiques |
| En cas de refus de `git push` : `git pull`, rouvrir dans Desktop pour vérifier, puis `git push` | Quelqu'un a publié entre-temps |

Pour construire ses propres analyses **sans modifier le rapport commun** : dans Power BI Desktop, **Obtenir les données > Modèles sémantiques Power BI > Lireka_Profitabilite**. On travaille alors dans un fichier à part, connecté en direct au modèle publié.

---

## 6. Administration du serveur Git (VPS)

Dans une session Bureau à distance administrateur, PowerShell en administrateur, depuis le dossier `deploiement\vps` du projet.

**Donner accès à une personne** (avec le contenu de sa clé publique) :
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Ajouter-UtilisateurGit.ps1 -Utilisateur prenom.nom -NomComplet 'Prénom Nom' -ClePublique '<contenu du .pub>'
```
Le script crée un compte Windows local non administrateur, l'ajoute au groupe `lireka-git` et enregistre sa clé. Pour remplacer une clé, relancer la même commande.

**Retirer un accès** :
```powershell
Remove-LocalGroupMember -Group lireka-git -Member prenom.nom
Remove-Item C:\ProgramData\ssh\cles_git\prenom.nom.pub
```

**Réinstaller ou réparer le serveur** : `.\Installer-ServeurGit.ps1` (relançable sans risque).

**Accès depuis l'extérieur** : le port TCP 22 doit être ouvert en entrée dans le groupe de sécurité réseau Azure de la VM (Inforeso). Contrôle depuis un poste : `Test-NetConnection 20.19.33.4 -Port 22`.

---

## 7. Dépannage

| Message | Cause et solution |
|---|---|
| `Permission denied (publickey)` | Clé non enregistrée, ou nom d'utilisateur erroné dans l'adresse de clonage. |
| `Connection timed out` | Port 22 fermé côté Azure : voir section 6. |
| `git-upload-pack` ou `git-receive-pack` n'est pas reconnu | Sur le VPS : `Restart-Service sshd`. Si le message persiste, redémarrer le VPS en dehors de l'actualisation de 6:00, puis vérifier que le tunnel WireGuard et la passerelle sont repartis. |
| `detected dubious ownership` | Relancer `Installer-ServeurGit.ps1` sur le VPS. |
| Actualisation en échec dans le Service | Voir [4-passation.md](4-passation.md), section Exploitation. |
