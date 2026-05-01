#!/usr/bin/env bash
set -e

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
"$VENV_DIR/bin/python" index.py
