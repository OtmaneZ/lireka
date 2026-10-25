#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Installe le serveur Git du VPS Lireka.

.DESCRIPTION
    - Git for Windows (installation machine)
    - OpenSSH Server : démarrage automatique, connexion par clé uniquement
    - Shell SSH par défaut : Windows PowerShell (nécessaire aux commandes Git distantes)
    - Groupe local "lireka-git" : ses membres lisent et écrivent dans le dépôt
    - Dépôt central C:\git\lireka.git (branche main, historique protégé)
    Le script peut être relancé sans risque : chaque étape vérifie l'existant.

.PARAMETER ClePubliqueAdmin
    Contenu du fichier .pub de l'administrateur qui exécute le script (facultatif).
    Ajouté à C:\ProgramData\ssh\administrators_authorized_keys.

.EXAMPLE
    .\Installer-ServeurGit.ps1 -ClePubliqueAdmin (Get-Content "$HOME\.ssh\id_ed25519.pub")
#>
param(
    [string]$ClePubliqueAdmin = '',
    [string]$RacineDepots = 'C:\git',
    [string]$NomDepot = 'lireka.git',
    [string]$Groupe = 'lireka-git'
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$GitCmd = 'C:\Program Files\Git\cmd'
$GitBin = 'C:\Program Files\Git\mingw64\bin'
$GitExe = Join-Path $GitCmd 'git.exe'
$DossierSsh = 'C:\ProgramData\ssh'
$ConfigSsh = Join-Path $DossierSsh 'sshd_config'
$DossierCles = Join-Path $DossierSsh 'cles_git'
$Marqueur = '# --- Lireka : serveur Git ---'
# SID plutôt que noms : fonctionne quelle que soit la langue de Windows.
$SidAdmins = '*S-1-5-32-544'
$SidSystem = '*S-1-5-18'

function Etape([string]$Texte) { Write-Host "`n== $Texte" -ForegroundColor Cyan }

function Invoke-Git {
    & $GitExe @args
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') : code $LASTEXITCODE" }
}

# 1. Git for Windows
Etape 'Git for Windows'
if (-not (Test-Path $GitExe)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Git.Git -e --source winget --scope machine --silent --accept-package-agreements --accept-source-agreements
    }
    else {
        $Version = Invoke-RestMethod 'https://api.github.com/repos/git-for-windows/git/releases/latest' -Headers @{ 'User-Agent' = 'lireka-setup' }
        $Paquet = $Version.assets | Where-Object { $_.name -match '^Git-[\d.]+-64-bit\.exe$' } | Select-Object -First 1
        if (-not $Paquet) { throw 'Installateur Git for Windows introuvable dans la dernière version publiée.' }
        $Installateur = Join-Path $env:TEMP $Paquet.name
        Invoke-WebRequest $Paquet.browser_download_url -OutFile $Installateur -UseBasicParsing
        Start-Process $Installateur -ArgumentList '/VERYSILENT', '/NORESTART', '/NOCANCEL', '/SP-' -Wait
    }
}
if (-not (Test-Path $GitExe)) { throw "Git introuvable après installation : $GitExe" }
Write-Host (& $GitExe --version)

# git-upload-pack et git-receive-pack (mingw64\bin) doivent être dans le PATH machine :
# ce sont les programmes que le client Git lance sur le serveur via SSH.
$CheminMachine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
foreach ($Dossier in $GitCmd, $GitBin) {
    if (($CheminMachine -split ';') -notcontains $Dossier) {
        $CheminMachine = $CheminMachine.TrimEnd(';') + ";$Dossier"
    }
}
[Environment]::SetEnvironmentVariable('Path', $CheminMachine, 'Machine')
$env:Path = $CheminMachine

# 2. OpenSSH Server
Etape 'OpenSSH Server'
$Capacite = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*' | Select-Object -First 1
if ($Capacite -and $Capacite.State -ne 'Installed') {
    Add-WindowsCapability -Online -Name $Capacite.Name | Out-Null
}
if (-not (Get-Service sshd -ErrorAction SilentlyContinue)) { throw 'Service sshd absent après installation.' }
Set-Service sshd -StartupType Automatic
Start-Service sshd   # premier démarrage : génère sshd_config et les clés d'hôte

if (-not (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
}

New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell `
    -Value "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force | Out-Null

# 3. Configuration sshd : clé uniquement, clés des utilisateurs Git dans C:\ProgramData\ssh\cles_git\<utilisateur>.pub
Etape 'Configuration sshd'
$Lignes = Get-Content $ConfigSsh
if ($Lignes -notcontains $Marqueur) {
    Copy-Item $ConfigSsh "$ConfigSsh.avant-lireka" -Force
    $Lignes = $Lignes | Where-Object { $_ -notmatch '^\s*(PasswordAuthentication|PubkeyAuthentication)\s' }
    # Les réglages globaux doivent précéder le premier bloc Match.
    $Entete = @($Marqueur, 'PubkeyAuthentication yes', 'PasswordAuthentication no', '')
    $Fin = @('', $Marqueur, "Match Group $Groupe", "       AuthorizedKeysFile __PROGRAMDATA__/ssh/cles_git/%u.pub")
    Set-Content -Path $ConfigSsh -Value ($Entete + $Lignes + $Fin) -Encoding Ascii
}
New-Item -ItemType Directory -Force -Path $DossierCles | Out-Null
icacls $DossierCles /inheritance:r /grant "${SidAdmins}:(OI)(CI)F" /grant "${SidSystem}:(OI)(CI)F" | Out-Null

if ($ClePubliqueAdmin) {
    $FichierAdmin = Join-Path $DossierSsh 'administrators_authorized_keys'
    $Existantes = if (Test-Path $FichierAdmin) { Get-Content $FichierAdmin } else { @() }
    if ($Existantes -notcontains $ClePubliqueAdmin.Trim()) {
        Add-Content -Path $FichierAdmin -Value $ClePubliqueAdmin.Trim() -Encoding Ascii
    }
    icacls $FichierAdmin /inheritance:r /grant "${SidAdmins}:F" /grant "${SidSystem}:F" | Out-Null
}

# 4. Groupe et dépôt central
Etape "Groupe $Groupe et dépôt $NomDepot"
if (-not (Get-LocalGroup -Name $Groupe -ErrorAction SilentlyContinue)) {
    New-LocalGroup -Name $Groupe -Description 'Lecture et écriture du dépôt Git Lireka (SSH)' | Out-Null
}
New-Item -ItemType Directory -Force -Path $RacineDepots | Out-Null
icacls $RacineDepots /grant "${Groupe}:(OI)(CI)M" | Out-Null

$Depot = Join-Path $RacineDepots $NomDepot
if (-not (Test-Path (Join-Path $Depot 'HEAD'))) {
    Invoke-Git init --bare --initial-branch=main $Depot
}
# Historique protégé : pas de réécriture ni de suppression de branche depuis un poste.
Invoke-Git -C $Depot config receive.denyNonFastForwards true
Invoke-Git -C $Depot config receive.denyDeletes true

# Le dépôt appartient aux administrateurs : autoriser explicitement les membres du groupe.
$CheminGit = $Depot -replace '\\', '/'
$Surs = & $GitExe config --system --get-all safe.directory
if ($Surs -notcontains $CheminGit) { Invoke-Git config --system --add safe.directory $CheminGit }

Restart-Service sshd

# 5. Récapitulatif
Etape 'Terminé'
$Empreinte = & "$env:SystemRoot\System32\OpenSSH\ssh-keygen.exe" -lf (Join-Path $DossierSsh 'ssh_host_ed25519_key.pub')
Write-Host "Dépôt central       : $Depot"
Write-Host "Adresse de clonage  : <utilisateur>@<IP du VPS>:$CheminGit"
Write-Host "Empreinte du serveur (à comparer à la première connexion) :"
Write-Host "  $Empreinte"
Write-Host "Ajouter un utilisateur : .\Ajouter-UtilisateurGit.ps1 -Utilisateur <nom> -ClePublique '<contenu du .pub>'"
