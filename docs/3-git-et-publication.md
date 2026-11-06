# 3. Git et publication

Comment récupérer le projet, le modifier et publier une mise à jour dans le Service Power BI.

État au 06/11/2026.

---

## 1. Le dépôt Git de Lireka

Le projet est conservé dans un dépôt Git hébergé sur le VPS Windows de Lireka, la machine qui porte aussi la passerelle Power BI. Ce dépôt contient la version de référence du rapport.

| Élément | Valeur |
|---|---|
| Serveur | VPS Lireka, `20.19.33.4` |
| Dépôt central | `C:\git\lireka.git`, branche `main` |
| Accès | SSH, par clé uniquement : aucun mot de passe n'est accepté |
| Personnes autorisées | Membres du groupe Windows local `lireka-git` |
| Adresse de clonage | `<compte>@20.19.33.4:C:/git/lireka.git` |
| Empreinte du serveur | `SHA256:eBMqTCmtpfbE5ym8v8/94o5zQl9i0h6ADtGQhMk4zJc` |

L'historique est protégé : il est impossible de le réécrire ou de supprimer la branche `main` depuis un poste.

---

## 2. Première installation sur un poste

1. Installer **Git for Windows** (git-scm.com/download/win, options par défaut) et **Power BI Desktop**.
2. Créer sa clé SSH dans PowerShell, puis valider les questions avec Entrée. La phrase secrète est facultative.
   ```powershell
   ssh-keygen -t ed25519 -C "prenom.nom@lireka.com"
   ```
3. Envoyer à l'administrateur du VPS le contenu du fichier `%USERPROFILE%\.ssh\id_ed25519.pub`. C'est la clé **publique** : elle peut circuler par e-mail ou par Slack. Le fichier `id_ed25519`, sans `.pub`, est la clé privée : il ne quitte jamais le poste.
4. Une fois l'accès ouvert (section 6), récupérer le projet depuis le dossier de son choix :
   ```powershell
   git clone prenom.nom@20.19.33.4:C:/git/lireka.git
   ```
   À la première connexion, répondre `yes` seulement si l'empreinte affichée est celle de la section 1.

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
4. Contrôler l'**Historique d'actualisation** : la ligne doit indiquer « Terminé ».
5. Fermer Desktop, puis lancer `git restore .` : la publication réécrit des fichiers déjà enregistrés dans Git.

La connexion à la passerelle, les identifiants de la base et l'actualisation planifiée de 8:00 sont conservés lors d'un remplacement.

Sans accès à la base (pas de tunnel WireGuard sur le poste), le projet s'ouvre sans données. On peut quand même modifier et publier : c'est le Service qui recharge les données par la passerelle. Dans ce cas, ne pas lancer « Actualiser » dans Desktop. Publier de préférence quand personne ne consulte le rapport, et actualiser dans le Service juste après.

---

## 5. Travailler à plusieurs

| Règle | Pourquoi |
|---|---|
| Une seule personne modifie le rapport à la fois, et prévient les autres avant de commencer | Deux modifications simultanées des mêmes pages sont difficiles à fusionner |
| `git pull` avant de commencer, `git push` dès la modification terminée | Chacun travaille sur la dernière version |
| Des enregistrements courts, avec un message qui dit ce qui a changé | L'historique reste lisible et réversible |
| Publier dans le Service seulement ce qui a été poussé dans Git | Le Service et le dépôt restent identiques |
| Si `git push` est refusé : `git pull`, rouvrir dans Desktop pour vérifier, puis `git push` | Quelqu'un a publié entre-temps |

Pour construire ses propres analyses **sans modifier le rapport commun**, Git n'est pas nécessaire : dans Power BI Desktop, **Obtenir les données > Modèles sémantiques Power BI > Lireka_Profitabilite**. On travaille alors dans un fichier à part, connecté en direct au modèle publié.

---

## 6. Administration du serveur Git

Ces opérations se font sur le VPS, dans une session Bureau à distance administrateur, avec PowerShell en administrateur, depuis le dossier `deploiement\vps` du projet.

**Donner accès à une personne**, avec le contenu de sa clé publique :
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Ajouter-UtilisateurGit.ps1 -Utilisateur prenom.nom -NomComplet 'Prénom Nom' -ClePublique '<contenu du .pub>'
```
Le script crée un compte Windows local non administrateur, l'ajoute au groupe `lireka-git` et enregistre sa clé. Pour remplacer une clé (nouveau poste, clé perdue), relancer la même commande.

**Retirer un accès** :
```powershell
Remove-LocalGroupMember -Group lireka-git -Member prenom.nom
Remove-Item C:\ProgramData\ssh\cles_git\prenom.nom.pub
```

**Réinstaller ou réparer le serveur** : `.\Installer-ServeurGit.ps1`, qui peut être relancé sans risque.

**Accès depuis l'extérieur** : le port TCP 22 est ouvert en entrée dans le groupe de sécurité réseau Azure de la VM depuis le 28/10/2026 (Inforeso). Seules les clés enregistrées donnent accès. Contrôle depuis un poste : `Test-NetConnection 20.19.33.4 -Port 22`.

---

## 7. Dépannage

| Message | Cause et solution |
|---|---|
| `Permission denied (publickey)` | Clé non enregistrée, ou nom de compte erroné dans l'adresse de clonage. |
| `Connection timed out` | Serveur injoignable depuis le réseau du poste, ou port 22 fermé côté Azure : voir section 6. |
| `git-upload-pack` ou `git-receive-pack` n'est pas reconnu | Sur le VPS : `Restart-Service sshd`. Si le message persiste, redémarrer le VPS en dehors de l'actualisation de 8:00, puis vérifier que le tunnel WireGuard et la passerelle sont repartis. |
| `detected dubious ownership` | Relancer `Installer-ServeurGit.ps1` sur le VPS. |
| Actualisation en échec dans le Service | Voir le document 4, « Passation », section Exploitation. |
