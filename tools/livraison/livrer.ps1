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

    Garde-fou : si quelqu'un a poussé sur le dépôt de la VM depuis la dernière livraison, le script s'arrête
    sans rien modifier (le zip est conservé), car la livraison effacerait ces changements. Il affiche les
    commits concernés et la commande pour les exporter. Une fois ces changements repris dans GitHub et
    le zip retéléchargé, relancer avec -ChangementsRecuperes.

.EXAMPLE
    C:\lireka\livrer.ps1 -Message 'Mise a jour de la documentation'

.EXAMPLE
    C:\lireka\livrer.ps1 -Message 'Reprise des changements d''Emma' -ChangementsRecuperes
#>
param(
    [string]$Message = "Mise a jour du $(Get-Date -Format 'dd/MM/yyyy')",
    [string]$Cible = 'C:\git\lireka.git',
    [string]$Dossier = 'C:\lireka\livraison',
    [switch]$ChangementsRecuperes
)

$ErrorActionPreference = 'Stop'
$Git = 'C:\Program Files\Git\cmd\git.exe'
# Auteur des commits de livraison : tout commit d'un autre auteur vient d'un poste (Emma, etc.).
$Livreur = 'otmane@zineinsight.com'
$ConserverZip = $false

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

    # Garde-fou : commits poussés depuis un poste après la dernière livraison.
    $Derniere = & $Git -C $Travail log -1 --format=%H "--author=$Livreur" HEAD
    if (-not $Derniere) { throw "Aucune livraison précédente trouvée dans $Cible (auteur $Livreur)." }
    $Recents = @(& $Git -C $Travail log --format='%h  %ad  %an  %s' '--date=format:%d/%m/%Y %H:%M' "$Derniere..HEAD")
    if ($Recents.Count -gt 0) {
        Write-Host "`nCommits poussés sur le dépôt depuis la dernière livraison :" -ForegroundColor Yellow
        $Recents | ForEach-Object { Write-Host "  $_" }
        if (-not $ChangementsRecuperes) {
            $ConserverZip = $true
            $Court = $Derniere.Substring(0, 7)
            Write-Host "`nLa livraison effacerait ces changements : rien n'a été modifié, le zip est conservé." -ForegroundColor Yellow
            Write-Host 'Les exporter (un fichier .patch par commit) et les envoyer pour reprise dans GitHub :'
            Write-Host "  & '$Git' -C $Cible format-patch -o C:\lireka\recuperation $Court..main"
            Write-Host 'Puis retélécharger le zip de main et relancer avec -ChangementsRecuperes.'
            throw 'Livraison arrêtée : changements non repris dans GitHub.'
        }
        Write-Host '-ChangementsRecuperes : ces changements doivent figurer dans le zip, la livraison continue.'
    }

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
    if (-not $ConserverZip) { Remove-Item $Zip.FullName -Force -ErrorAction SilentlyContinue }
}
