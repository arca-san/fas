@echo off
chcp 1254 >nul
setlocal

set "VENV_DIR=.venv"

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
echo Tarayici http://127.0.0.1:8050 adresinde acilacak...
start http://127.0.0.1:8050
call %VENV_DIR%\Scripts\python index.py

pause
endlocal
