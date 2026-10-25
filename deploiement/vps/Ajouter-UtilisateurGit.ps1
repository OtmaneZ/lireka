#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Donne à une personne l'accès au dépôt Git Lireka du VPS.

.DESCRIPTION
    - Crée un compte Windows local (non administrateur) s'il n'existe pas.
      Son mot de passe est aléatoire et n'est jamais communiqué : la connexion se fait par clé SSH uniquement.
    - Ajoute le compte au groupe "lireka-git".
    - Enregistre sa clé publique dans C:\ProgramData\ssh\cles_git\<utilisateur>.pub.
    Relancer le script avec une nouvelle clé remplace l'ancienne (perte ou changement de poste).

.EXAMPLE
    .\Ajouter-UtilisateurGit.ps1 -Utilisateur emma.henry -NomComplet 'Emma Henry' -ClePublique 'ssh-ed25519 AAAA... emma@lireka'
#>
param(
    [Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9._-]{1,19}$')][string]$Utilisateur,
    [Parameter(Mandatory)][string]$ClePublique,
    [string]$NomComplet = '',
    [string]$Groupe = 'lireka-git',
    [string]$AdresseServeur = '20.19.33.4'
)

$ErrorActionPreference = 'Stop'
$DossierCles = 'C:\ProgramData\ssh\cles_git'

$ClePublique = $ClePublique.Trim()
if ($ClePublique -notmatch '^(ssh-ed25519|ecdsa-sha2-nistp256|ssh-rsa) [A-Za-z0-9+/=]+( .*)?$') {
    throw 'Clé publique invalide : coller le contenu complet du fichier .pub (une seule ligne).'
}
if (-not (Get-LocalGroup -Name $Groupe -ErrorAction SilentlyContinue)) {
    throw "Groupe $Groupe absent : lancer d'abord Installer-ServeurGit.ps1."
}

if (-not (Get-LocalUser -Name $Utilisateur -ErrorAction SilentlyContinue)) {
    $Octets = New-Object byte[] 24
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($Octets)
    $MotDePasse = ConvertTo-SecureString ([Convert]::ToBase64String($Octets) + 'aA1!') -AsPlainText -Force
    $Compte = @{
        Name                     = $Utilisateur
        Password                 = $MotDePasse
        Description              = 'Compte Git Lireka (SSH, clé uniquement)'
        PasswordNeverExpires     = $true
        UserMayNotChangePassword = $true
    }
    if ($NomComplet) { $Compte.FullName = $NomComplet }
    New-LocalUser @Compte | Out-Null
    Write-Host "Compte créé : $Utilisateur"
}

$Membres = Get-LocalGroupMember -Group $Groupe | ForEach-Object { ($_.Name -split '\\')[-1] }
if ($Membres -notcontains $Utilisateur) { Add-LocalGroupMember -Group $Groupe -Member $Utilisateur }

$FichierCle = Join-Path $DossierCles "$Utilisateur.pub"
Set-Content -Path $FichierCle -Value $ClePublique -Encoding Ascii

Write-Host "`nAccès prêt pour $Utilisateur. Sur son poste :"
Write-Host "  git clone ${Utilisateur}@${AdresseServeur}:C:/git/lireka.git"
