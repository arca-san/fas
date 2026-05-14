$repo = 'arca-san/fas'
$versionFile = Join-Path $PSScriptRoot 'version.txt'
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')

# --- branch oku ---
$headPath = Join-Path $projectRoot '.git\HEAD'
$currentBranch = ''
if (Test-Path $headPath) {
    $headContent = Get-Content $headPath -Raw -ErrorAction SilentlyContinue
    if ($headContent -match 'ref: refs/heads/(.+?)[\r\n]') {
        $currentBranch = $matches[1]
    }
}
$onMaster = ($currentBranch -eq 'master')

# --- local version oku ---
$localSha = ''
if (Test-Path $versionFile) {
    $localSha = (Get-Content $versionFile -Raw -ErrorAction SilentlyContinue).Trim()
}
if (-not $localSha) { $localSha = 'unknown' }

# --- remote SHA'yi GitHub API'den al ---
try {
    $apiUrl = 'https://api.github.com/repos/' + $repo + '/branches/master'
    $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop -TimeoutSec 10
    $remoteSha = $response.commit.sha
} catch {
    Write-Host 'Guncelleme kontrol edilemedi (Internet yok?).'
    exit 0
}

# --- SHA karsilastirmasi ---
if ($remoteSha -eq $localSha) {
    Write-Host 'Guncelleme yok.'
    exit 0
}

# --- sadece master branch'inde guncelleme uygula ---
if (-not $onMaster) {
    Write-Host ('Guncelleme var (su an ' + $currentBranch + ' dalinda). Gecmek icin master dalina gecin.')
    exit 0
}

# --- ata/soy kontrolu ---
if ($localSha -ne 'unknown') {
    git merge-base --is-ancestor $localSha $remoteSha 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Guncelleme yok (yerel dal remote master ile ayni veya ileride).'
        exit 0
    }
}

# --- guncellemeyi uygula ---
Write-Host 'Guncelleme bulundu. Indiriliyor...'

try {
    $zipUrl = 'https://github.com/' + $repo + '/archive/master.zip'
    $zipPath = [System.IO.Path]::GetTempFileName() + '.zip'
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -ErrorAction Stop

    $extractPath = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString()
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -ErrorAction Stop

    $src = Join-Path $extractPath 'fas-master'
    if (-not (Test-Path $src)) {
        throw 'Zip icinde fas-master/ klasoru bulunamadi.'
    }

    $logPath = [System.IO.Path]::GetTempFileName()
    robocopy $src $projectRoot /E /XD .venv .git /NJH /NJS /NP /NDL /R:1 /W:2 > $logPath 2>&1
    $robocopyExit = $LASTEXITCODE
    if ($robocopyExit -ge 8) {
        $logContent = Get-Content $logPath -Raw
        Remove-Item $logPath -Force -ErrorAction SilentlyContinue
        throw "Dosya kopyalama basarisiz (exit: $robocopyExit).`n$logContent"
    }
    Remove-Item $logPath -Force -ErrorAction SilentlyContinue

    # version.txt'yi guncelle
    $remoteSha | Out-File $versionFile -Encoding ASCII -Force

    Write-Host 'Guncelleme tamamlandi.'
} catch {
    Write-Host "GUNCELLEME HATASI: $_"
    exit 1
} finally {
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }
    if (Test-Path $extractPath) { Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue }
}

exit 0
