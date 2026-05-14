$repo = 'arca-san/fas'
$err = $null

$currentBranch = ''
$headPath = '.git\HEAD'
if (Test-Path $headPath) {
    $headContent = Get-Content $headPath -Raw -ErrorAction SilentlyContinue
    if ($headContent -match 'ref: refs/heads/(.+?)[\r\n]') {
        $currentBranch = $matches[1]
    }
}

$localSha = $null
$localMainPath = '.git\refs\heads\master'
if (Test-Path $localMainPath) {
    $localSha = (Get-Content $localMainPath -Raw -ErrorAction SilentlyContinue).Trim()
}

try {
    $apiUrl = 'https://api.github.com/repos/' + $repo + '/branches/master'
    $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop
    $remoteSha = $response.commit.sha

    if ($remoteSha -and $remoteSha -ne $localSha) {
        if ($currentBranch -eq 'master') {
            Write-Host 'Guncelleme bulundu. Indiriliyor...'
            $zipUrl = 'https://github.com/' + $repo + '/archive/master.zip'
            $zipPath = [System.IO.Path]::GetTempFileName()
            Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -ErrorAction Stop

            $extractPath = [System.IO.Path]::GetTempPath() + [System.Guid]::NewGuid().ToString()
            Expand-Archive -Path $zipPath -DestinationPath $extractPath -ErrorAction Stop

            $src = Join-Path $extractPath 'fas-master'
            if (Test-Path $src) {
                robocopy $src '.' /E /XD .venv .git /NJH /NJS /NP >nul 2>&1
            }
            Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $extractPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host 'Guncelleme tamamlandi.'
        } else {
            Write-Host ('main branch''i guncel (su an ' + $currentBranch + '). Otomatik guncelleme atlandi.')
        }
    }
} catch {
    $err = $_.Exception.Message
}
