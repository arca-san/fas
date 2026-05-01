@echo off
chcp 65001 >nul
set "VENV_DIR=.venv"

echo ==========================================
echo   Fon Analiz Sistemi — Başlatma Scripti
echo ==========================================
echo.

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Sanal ortam bulunamadı. Oluşturuluyor...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo HATA: Sanal ortam oluşturulamadı. Python kurulu mu?
        pause
        exit /b 1
    )
)

echo Bağımlılıklar kontrol ediliyor...
call %VENV_DIR%\Scripts\pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo HATA: Bağımlılıklar yüklenemedi.
    pause
    exit /b 1
)

echo Uygulama başlatılıyor...
call %VENV_DIR%\Scripts\python index.py

pause
