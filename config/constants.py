#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sabit değerler, sütun isimleri, renk paleti ve metrik açıklamaları.
"""

from config.settings import DEFAULT_COLOR_PALETTE

# Tarih & fiyat sütun isimleri (standartlaştırılmış)
COL_DATE = "tarih"
COL_FON_KODU = "fon_kodu"
COL_FON_UNVAN = "fon_unvan"
COL_PRICE = "fiyat"
COL_DAILY_RETURN = "gunluk_getiri"
COL_CUM_RETURN = "kumulatif_getiri"

# Metrik isimleri (rapor & UI için)
METRIC_VOLATILITY = "Volatilite (Yıllık)"
METRIC_DOWNSIDE_VOL = "Aşağı Yönlü Volatilite"
METRIC_MAX_DRAWDOWN = "Maksimum Düşüş"
METRIC_VAR = f"VaR (%{int(0.95*100)})"
METRIC_CVAR = f"CVaR (%{int(0.95*100)})"
METRIC_SHARPE = "Sharpe Oranı"
METRIC_SORTINO = "Sortino Oranı"
METRIC_TREYNOR = "Treynor Oranı"
METRIC_BETA = "Beta"
METRIC_ALPHA = "Alfa"
METRIC_R_SQUARED = "R²"
METRIC_INFORMATION_RATIO = "Enformasyon Oranı"
METRIC_TOTAL_RETURN = "Toplam Getiri"
METRIC_ANNUALIZED_RETURN = "Yıllıklandırılmış Getiri"
METRIC_CALMAR = "Calmar Oranı"
METRIC_STERLING = "Sterling Oranı"
METRIC_UP_CAPTURE = "Up Capture (%)"
METRIC_DOWN_CAPTURE = "Down Capture (%)"
METRIC_BATTING_AVG = "Batting Average (%)"
METRIC_SKEWNESS = "Çarpıklık (Skewness)"
METRIC_KURTOSIS = "Basıklık (Kurtosis)"
METRIC_AVG_DRAWDOWN = "Ortalama Düşüş (%)"
METRIC_DD_DURATION = "DD Süresi (Gün)"
METRIC_RECOVERY_TIME = "Toparlanma Süresi (Gün)"
METRIC_ULCER = "Ulcer Index (%)"
METRIC_OMEGA = "Omega Oranı"
METRIC_ACTIVE_SHARE = "Active Share (%)"
METRIC_M2 = "M² Ölçüsü (%)"

# Metrik açıklamaları (raporlarda kullanılır)
METRIC_DESCRIPTIONS = {
    METRIC_VOLATILITY: "Getirilerin standart sapması, yıllıklandırılmış.",
    METRIC_DOWNSIDE_VOL: "Sadece negatif getirilerin volatilitesi.",
    METRIC_MAX_DRAWDOWN: "Pikten dibeye maksimum düşüş yüzdesi.",
    METRIC_VAR: "Belirli güven düzeyinde beklenen maksimum kayıp.",
    METRIC_CVAR: "VaR'ı aşan kayıpların ortalaması.",
    METRIC_SHARPE: "Risksiz getiri üzerinden birim risk başına fazla getiri.",
    METRIC_SORTINO: "Sharpe'ın sadece negatif volatilite kullanan versiyonu.",
    METRIC_TREYNOR: "Sistematik risk (Beta katsayısı) başına fazla getiri.",
    METRIC_BETA: "Fonun benchmarka göre sistematik risk duyarlılığı.",
    METRIC_ALPHA: "Benchmarka göre ayarlanmış fazla getiri (yetenek göstergesi).",
    METRIC_R_SQUARED: "Fon getirisinin benchmark tarafından açıklanan varyans oranı.",
    METRIC_INFORMATION_RATIO: "Aktif getiri / Tracking error.",
    METRIC_TOTAL_RETURN: "Seçilen dönemdeki toplam getiri.",
    METRIC_ANNUALIZED_RETURN: "Yıllıklandırılmış ortalama getiri.",
    METRIC_CALMAR: "Yıllık getiri / Maksimum düşüş. Drawdown bazlı risk-ayarlı getiri.",
    METRIC_STERLING: "Yıllık getiri / (Ortalama DD + %10). Yumuşatılmış drawdown oranı.",
    METRIC_UP_CAPTURE: "Piyasa yükselirken fonun yakaladığı getiri oranı (%).",
    METRIC_DOWN_CAPTURE: "Piyasa düşerken fonun kaybettiği getiri oranı (%).",
    METRIC_BATTING_AVG: "Fonun benchmark'ı yendiği dönemlerin yüzdesi.",
    METRIC_SKEWNESS: "Getiri dağılımının asimetrisi. Negatif = sola çarpık (kötü).",
    METRIC_KURTOSIS: "Getiri dağılımının kuyruk kalınlığı. >3 = şişman kuyruk.",
    METRIC_AVG_DRAWDOWN: "Tüm düşüşlerin ortalaması.",
    METRIC_DD_DURATION: "Ortalama düşüş süresi (iş günü).",
    METRIC_RECOVERY_TIME: "Düşüşten toparlanma için geçen ortalama süre (iş günü).",
    METRIC_ULCER: "Düşüşlerin kareleri toplamının karekökü. Drawdown şiddeti ölçüsü.",
    METRIC_OMEGA: "Getiri dağılımının tamamını kullanan risk-ödül oranı. >1 iyi.",
    METRIC_ACTIVE_SHARE: "Fon portföyünün benchmark'tan ne kadar farklılaştığı (basit yaklaşım).",
    METRIC_M2: "Riske göre düzeltilmiş getiri. Fon volatilitesini benchmark seviyesine ölçekler.",
}

# Rapor şablonu ayarları
REPORT_LOGO_PATH = None  # İleride eklenebilir
REPORT_TITLE = "Fon Analiz Sistemi Raporu"
REPORT_FOOTER = "FAS © 2026 — Fon Analiz Sistemi"

# Dash DataTable varsayılan stil ayarları
DATATABLE_STYLE = {
    "style_cell": {
        "textAlign": "center",
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "fontSize": "14px",
    },
    "style_header": {
        "backgroundColor": "rgb(230, 230, 230)",
        "fontWeight": "bold",
    },
    "style_data_conditional": [],
}
