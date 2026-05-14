#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"
VENV_DIR=".venv"

echo "Güncellemeler kontrol ediliyor..."
GITHUB_REPO="arca-san/fas"

# Branch oku (.git/HEAD dosyasından, git komutu yok)
CURRENT_BRANCH=""
if [ -f ".git/HEAD" ]; then
    HEAD_REF=$(cat ".git/HEAD")
    case "$HEAD_REF" in
        "ref: refs/heads/"*) CURRENT_BRANCH=${HEAD_REF#ref: refs/heads/} ;;
    esac
fi

# Local main SHA
LOCAL_MAIN_SHA=""
if [ -f ".git/refs/heads/master" ]; then
    LOCAL_MAIN_SHA=$(cat ".git/refs/heads/master")
fi

# Remote main SHA (GitHub API)
REMOTE_MAIN_SHA=""
if command -v curl &>/dev/null && command -v python3 &>/dev/null; then
    REMOTE_MAIN_SHA=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/branches/master" 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['commit']['sha'])" 2>/dev/null || echo "")
fi

if [ -n "$REMOTE_MAIN_SHA" ] && [ "$REMOTE_MAIN_SHA" != "$LOCAL_MAIN_SHA" ]; then
    if [ "$CURRENT_BRANCH" = "master" ]; then
        if command -v unzip &>/dev/null && command -v rsync &>/dev/null; then
            echo "Güncelleme bulundu. İndiriliyor..."
            TMP_ZIP=$(mktemp)
            curl -sL "https://github.com/$GITHUB_REPO/archive/master.zip" -o "$TMP_ZIP"
            TMP_DIR=$(mktemp -d)
            unzip -q "$TMP_ZIP" -d "$TMP_DIR" 2>/dev/null
            rsync -a --exclude='.venv' --exclude='.git' "$TMP_DIR/fas-master/" . 2>/dev/null
            rm -f "$TMP_ZIP"
            rm -rf "$TMP_DIR"
            echo "Güncelleme tamamlandı."
        else
            echo "Uyarı: unzip veya rsync bulunamadı, güncelleme atlandı."
        fi
    else
        echo "main branch'i güncel (şu an $CURRENT_BRANCH). Otomatik güncelleme atlandı."
    fi
fi

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

# Arka planda Dash'i başlat
"$VENV_DIR/bin/python" index.py &
DASH_PID=$!

# Dash hazır olana kadar bekle
echo "Dash hazır olana kadar bekleniyor..."
until curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8050" 2>/dev/null | grep -q "200"; do
    sleep 1
done

echo "Dash hazır! Tarayıcı açılıyor..."
open "http://127.0.0.1:8050"

# Dash'i beklemeye devam et
wait $DASH_PID