<#
.SYNOPSIS
    Usage interne ZineInsights. Publie la version client du projet dans le dépôt Git du VPS Lireka.

.DESCRIPTION
    Prend le commit courant (HEAD) du dépôt de travail, n'en garde que les chemins de $Inclus
    (modèle, rapport, documentation client, scripts d'exploitation) et les pousse comme un seul
    nouveau commit sur la branche main du dépôt cible. L'historique de travail, le devis, l'audit
    interne et les scripts d'analyse ne sont jamais publiés.
    Relançable : un fichier retiré de $Inclus ou du dépôt de travail disparaît aussi du dépôt client.

.EXAMPLE
    # Sur le VPS, depuis la copie de travail à jour (git pull) :
    .\tools\livraison\Publier-DepotPropre.ps1 -Message 'Livraison initiale du rapport Lireka Profitabilité'
#>
param(
    [string]$Source = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$Cible = 'C:\git\lireka.git',
    [string]$Message = "Mise à jour du $(Get-Date -Format 'dd/MM/yyyy')",
    [string]$Auteur = 'Otmane Boulahia',
    [string]$Email = 'otmane@zineinsight.com'
)

$ErrorActionPreference = 'Stop'

$Inclus = @(
    'README.md'
    'powerbi/.gitignore'
    'powerbi/Lireka_Profitabilite.pbip'
    'powerbi/Lireka_Profitabilite.Report'
    'powerbi/Lireka_Profitabilite.SemanticModel'
    'powerbi/models'
    'docs/04-processus'
    'docs/05-formation'
    'docs/06-exploitation'
    'docs/doc_reunion_4_08'
    'docs/notes-techniques/dette-technique-bloc5.md'
    'docs/notes-techniques/dette-technique-postes-canada.md'
    'docs/notes-techniques/limite-etf-annulation.md'
    'docs/notes-techniques/limite-shipping-marketplace.md'
    'docs/notes-techniques/reconstruction-ca-marketplace.md'
    'deploiement'
)

function Invoke-Git {
    & git.exe @args
    if ($LASTEXITCODE -ne 0) { throw "git $($args -join ' ') : code $LASTEXITCODE" }
}

$Travail = Join-Path $env:TEMP ('lireka-livraison-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$Archive = "$Travail.zip"
try {
    Invoke-Git clone --quiet $Cible $Travail
    Invoke-Git -C $Travail config core.autocrlf false

    # Copie de travail vidée : son contenu sera exactement celui de l'archive.
    Get-ChildItem $Travail -Force | Where-Object Name -ne '.git' | Remove-Item -Recurse -Force

    Invoke-Git -C $Source -c core.autocrlf=false archive --format=zip -o $Archive HEAD -- @Inclus
    Expand-Archive -Path $Archive -DestinationPath $Travail -Force

    Invoke-Git -C $Travail add -A
    $Changements = & git.exe -C $Travail status --porcelain
    if (-not $Changements) {
        Write-Host 'Aucun changement à publier.'
        return
    }
    $Origine = (& git.exe -C $Source rev-parse --short HEAD)
    Invoke-Git -C $Travail -c "user.name=$Auteur" -c "user.email=$Email" commit --quiet -m $Message
    Invoke-Git -C $Travail push --quiet origin HEAD:main
    Write-Host "Publié dans $Cible (source $Origine) :"
    & git.exe -C $Travail log -1 --stat --format='%h %s'
}
finally {
    Remove-Item $Travail -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $Archive -Force -ErrorAction SilentlyContinue
}
