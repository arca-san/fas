@echo off
chcp 1254 >nul
setlocal

set "VENV_DIR=.venv"

echo Guncellemeler kontrol ediliyor...
powershell -ExecutionPolicy Bypass -File scripts\update_check.ps1

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
