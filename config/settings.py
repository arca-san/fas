#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfigürasyon ayarları — teknik borcu önlemek için tüm sabitler burada.
Değiştirmek gerektiğinde sadece bu dosya güncellenir.
"""

from pathlib import Path

# Proje kök dizini
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Veri & cache
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CACHE_TTL_HOURS = 24

# Getiri tanımı (tek merkezde kontrol)
# "log" veya "simple" — tüm hesaplamalar bu sabite göre yönlendirilir.
RETURN_METHOD = "log"

# Risk-free oran varsayılanı (yıllık, ondalık)
# Gerçek veri çekilemezse bu değer kullanılır.
DEFAULT_RISK_FREE_ANNUAL = 0.45

# Risk-free dönüşüm yöntemi
# "compound": (1 + r)^(1/252) - 1  (iş günü bazlı)
# "simple": r / 252
RISK_FREE_DAILY_METHOD = "compound"
ANNUAL_TRADING_DAYS = 252

# Tarih hizalama politikası
# "inner": sadece ortak tarihleri tutar
# "outer": tüm tarihleri tutar, eksik değerleri forward-fill
CALENDAR_ALIGN_METHOD = "inner"

# Frekans dönüşümü
# "D": günlük (ham), "W": haftalık, "M": aylık
DEFAULT_FREQUENCY = "D"

# Grafik & rapor
DEFAULT_COLOR_PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

# TEFAS rate-limit bilgisi (saniye cinsinden min istek aralığı)
TEFAS_MIN_REQUEST_INTERVAL = 10.0

# VaR / CVaR güven aralığı
VAR_CONFIDENCE = 0.95
