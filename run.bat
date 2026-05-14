@echo off
chcp 1254 >nul
setlocal

set "VENV_DIR=.venv"

echo Guncellemeler kontrol ediliyor...
powershell -Command "& {
    $repo = 'arca-san/fas'
    $err = $null

    # Branch oku (.git\HEAD dosyasindan)
    $currentBranch = ''
    $headPath = '.git\HEAD'
    if (Test-Path $headPath) {
        $headContent = Get-Content $headPath -Raw -ErrorAction SilentlyContinue
        if ($headContent -match 'ref: refs/heads/(.+?)[\r\n]') {
            $currentBranch = $matches[1]
        }
    }

    # Local main SHA
    $localSha = $null
    $localMainPath = '.git\refs\heads\master'
    if (Test-Path $localMainPath) {
        $localSha = (Get-Content $localMainPath -Raw -ErrorAction SilentlyContinue).Trim()
    }

    # Remote main SHA (GitHub API)
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
}"

echo ==========================================
echo   Fon Analiz Sistemi - Baslatma Scripti
echo ==========================================
echo.

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Sanal ortam bulunamadi. Olusturuluyor...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo HATA: Sanal ortam olusturulamadi. Python kurulu mu?
        pause
        exit /b 1
    )
)

echo Bagimliliklar kontrol ediliyor...
call %VENV_DIR%\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo HATA: Bagimliliklar yuklenemedi.
    pause
    exit /b 1
)

echo Uygulama baslatiliyor...
echo Dash hazir olana kadar bekleniyor...
start /B "" %VENV_DIR%\Scripts\python index.py

:wait_loop
timeout /t 1 /nobreak >nul
curl -s -o NUL http://127.0.0.1:8050 >nul 2>&1
if errorlevel 1 (
    goto wait_loop
)

echo Dash hazir! Tarayici aciliyor...
start http://127.0.0.1:8050

pause
endlocal
