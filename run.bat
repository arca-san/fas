@echo off
setlocal

set "VENV_DIR=.venv"

echo ==========================================
echo   Fon Analiz Sistemi - Baslatma Scripti
echo ==========================================
echo.

echo Guncelleme kontrol ediliyor...
python scripts\auto_update.py

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Sanal ortam bulunamadi. Olusturuluyor...
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3.12 -m venv %VENV_DIR% 2>nul
        if errorlevel 1 py -3.11 -m venv %VENV_DIR% 2>nul
        if errorlevel 1 py -3.10 -m venv %VENV_DIR% 2>nul
        if errorlevel 1 python -m venv %VENV_DIR%
    ) else (
        python -m venv %VENV_DIR%
    )
    if errorlevel 1 (
        echo HATA: Sanal ortam olusturulamadi. Python 3.10+ kurulu mu?
        pause
        exit /b 1
    )
    %VENV_DIR%\Scripts\python -m pip install --upgrade pip >nul
)

echo Bagimliliklar kontrol ediliyor...
call %VENV_DIR%\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo HATA: Bagimliliklar yuklenemedi.
    pause
    exit /b 1
)

:start_app
echo Uygulama baslatiliyor...
start /B "" "%VENV_DIR%\Scripts\python" index.py

echo Dash hazir olana kadar bekleniyor...
:wait_loop
timeout /t 1 /nobreak >nul
curl -s -o NUL http://127.0.0.1:8050 >nul 2>&1
if errorlevel 1 goto wait_loop

echo Dash hazir! Tarayici aciliyor...
start http://127.0.0.1:8050

pause
endlocal
