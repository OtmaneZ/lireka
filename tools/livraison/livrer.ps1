<#
.SYNOPSIS
    Usage interne ZineInsights. Livre la version client du projet dans le dépôt Git du VPS Lireka.

.DESCRIPTION
    1. Prend le dernier zip lireka-*.zip du dossier Téléchargements et l'extrait dans C:\lireka\livraison
       (toujours le même dossier, remplacé à chaque livraison).
    2. Remplace le contenu du dépôt C:\git\lireka.git par les seuls chemins listés dans
       tools\livraison\inclus.txt : un élément retiré de la liste disparaît aussi du dépôt client.
    3. Crée un commit et le pousse sur main. Aucun commit si rien n'a changé.
    4. Supprime le dossier extrait et le zip (aussi en cas d'erreur : retélécharger le zip avant de relancer).

.EXAMPLE
    C:\lireka\livrer.ps1 -Message 'Mise a jour de la documentation'
#>
param(
    [string]$Message = "Mise a jour du $(Get-Date -Format 'dd/MM/yyyy')",
    [string]$Cible = 'C:\git\lireka.git',
    [string]$Dossier = 'C:\lireka\livraison'
)

$ErrorActionPreference = 'Stop'
$Git = 'C:\Program Files\Git\cmd\git.exe'

function Invoke-Git {
    & $Git @args
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') : code $LASTEXITCODE" }
}

$Zip = Get-ChildItem "$HOME\Downloads\lireka-*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Zip) { throw "Aucun zip lireka-*.zip dans $HOME\Downloads" }
Write-Host "Zip utilisé : $($Zip.Name) ($($Zip.LastWriteTime))"

Remove-Item $Dossier -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $Zip.FullName -DestinationPath $Dossier
$Source = (Get-ChildItem $Dossier -Directory | Select-Object -First 1).FullName
$Inclus = Get-Content (Join-Path $Source 'tools\livraison\inclus.txt') | Where-Object { $_.Trim() -ne '' }

$Travail = Join-Path $env:TEMP 'lireka-livraison'
Remove-Item $Travail -Recurse -Force -ErrorAction SilentlyContinue
try {
    Invoke-Git clone -q $Cible $Travail
    Invoke-Git -C $Travail config core.autocrlf false
    Get-ChildItem $Travail -Force | Where-Object Name -ne '.git' | Remove-Item -Recurse -Force

    foreach ($Chemin in $Inclus) {
        $Depuis = Join-Path $Source $Chemin
        if (-not (Test-Path $Depuis)) { throw "Absent du zip : $Chemin" }
        $Vers = Join-Path $Travail $Chemin
        New-Item -ItemType Directory -Force -Path (Split-Path $Vers) | Out-Null
        Copy-Item $Depuis $Vers -Recurse -Force
    }

    Invoke-Git -C $Travail add -A
    $Changements = & $Git -C $Travail status --porcelain
    if (-not $Changements) {
        Write-Host 'Aucun changement à livrer.'
    }
    else {
        Write-Host "Changements :"; $Changements | ForEach-Object { Write-Host "  $_" }
        Invoke-Git -C $Travail -c user.name='Otmane Boulahia' -c user.email='otmane@zineinsight.com' commit -q -m $Message
        Invoke-Git -C $Travail push -q origin HEAD:main
    }
    Write-Host "`n--- Dépôt Lireka"
    & $Git -C $Cible log --oneline -5 main
    Write-Host "Fichiers : $((& $Git -C $Cible ls-tree -r --name-only main | Measure-Object).Count)"
}
finally {
    Remove-Item $Travail -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $Dossier -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $Zip.FullName -Force -ErrorAction SilentlyContinue
}
