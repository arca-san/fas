#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
VENV_DIR=".venv"

echo "=========================================="
echo "  Fon Analiz Sistemi — Başlatma Scripti"
echo "=========================================="
echo ""

if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Sanal ortam bulunamadı. Oluşturuluyor..."
    python3 -m venv "$VENV_DIR"
fi

echo "Bağımlılıklar kontrol ediliyor..."
"$VENV_DIR/bin/pip" install -q -r requirements.txt

echo "Uygulama başlatılıyor..."
echo "Tarayıcı 5 saniye sonra http://127.0.0.1:8050 adresinde açılacak..."

open "http://127.0.0.1:8050"
"$VENV_DIR/bin/python" index.py