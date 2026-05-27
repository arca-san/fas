#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
VENV_DIR=".venv"

echo "=========================================="
echo "  Fon Analiz Sistemi - Baslatma Scripti"
echo "=========================================="
echo ""

echo "Guncelleme kontrol ediliyor..."
python3 scripts/auto_update.py || true

if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Sanal ortam bulunamadi. Olusturuluyor..."
    python3 -m venv "$VENV_DIR" 2>/dev/null || python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "HATA: Sanal ortam olusturulamadi. Python 3.10+ kurulu mu?"
        exit 1
    fi
    "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null 2>&1
fi

echo "Bagimliliklar kontrol ediliyor..."
"$VENV_DIR/bin/pip" install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "HATA: Bagimliliklar yuklenemedi."
    exit 1
fi

echo "Uygulama baslatiliyor..."

"$VENV_DIR/bin/python" index.py &
DASH_PID=$!

echo "Dash hazir olana kadar bekleniyor..."
until curl -s -o /dev/null "http://127.0.0.1:8050" 2>/dev/null; do
    sleep 1
done

echo "Dash hazir! Tarayici aciliyor..."
open "http://127.0.0.1:8050"

wait $DASH_PID
