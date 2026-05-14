#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
VENV_DIR=".venv"

echo "=========================================="
echo "  Fon Analiz Sistemi — Baslatma Scripti"
echo "=========================================="
echo ""

if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Sanal ortam bulunamadi. Olusturuluyor..."
    python3 -m venv "$VENV_DIR"
fi

echo "Bagimliliklar kontrol ediliyor..."
"$VENV_DIR/bin/pip" install -q -r requirements.txt

echo "Uygulama baslatiliyor..."

# Arka planda Dash'i baslat
"$VENV_DIR/bin/python" index.py &
DASH_PID=$!

# Dash hazir olana kadar bekle
echo "Dash hazir olana kadar bekleniyor..."
until curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8050" 2>/dev/null | grep -q "200"; do
    sleep 1
done

echo "Dash hazir! Tarayici aciliyor..."
open "http://127.0.0.1:8050"

# Dash'i beklemeye devam et
wait $DASH_PID
