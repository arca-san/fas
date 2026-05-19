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
