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
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo HATA: Sanal ortam olusturulamadi. Python kurulu mu?
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

:: --- GTK / WeasyPrint ---
echo WeasyPrint kontrol ediliyor...

:: once dogrudan dene
%VENV_DIR%\Scripts\python -c "from weasyprint import HTML" >nul 2>&1
if not errorlevel 1 goto :wp_ok

:: .gtk/bin PATH'te var mi?
set "GTK_BIN=%~dp0.gtk\bin"
if exist "%GTK_BIN%\libgobject-2.0-0.dll" (
    set "PATH=%GTK_BIN%;%PATH%"
    %VENV_DIR%\Scripts\python -c "from weasyprint import HTML" >nul 2>&1
    if not errorlevel 1 goto :wp_ok
)

:: indir
echo GTK runtime bulunamadi, indiriliyor (~300MB)...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\install_gtk.ps1"
if errorlevel 1 (
    echo [!] GTK kurulamadi. PDF raporlari kullanilamaz.
    goto :start_app
)

set "PATH=%GTK_BIN%;%PATH%"
%VENV_DIR%\Scripts\python -c "from weasyprint import HTML" >nul 2>&1
if errorlevel 1 (
    echo [!] WeasyPrint hala calismadi. PDF raporlari kullanilamaz.
) else (
    echo WeasyPrint hazir.
)
goto :start_app

:wp_ok
echo WeasyPrint hazir.

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
