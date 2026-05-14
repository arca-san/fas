#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fon kategorisine göre benchmark mapping (failsafe).
TEFAS sayfasından benchmark bilgisi çekilemediğinde kullanılır.

Benchmark kodları BIST-KYD endeksleridir (config/benchmarks.py).
"""

# Fon kategorisi → benchmark ağırlıkları
# Her mapping toplamı 1.0 olmalıdır.
FON_KATEGORI_BENCHMARK_MAPPING = {
    # Hisse ağırlıklı fonlar
    "Hisse Senedi Fonu": {"FHISE": 1.0},
    "Hisse Senedi Yoğun Fon": {"FHISE": 0.85, "TD91G": 0.15},
    
    # Karma/değişken fonlar
    "Karma Fon": {"FHISE": 0.6, "TD91G": 0.4},
    "Değişken Fon": {"FHISE": 0.5, "TD91G": 0.5},
    
    # Sabit getiri fonları
    "Borçlanma Araçları Fonu": {"TD91G": 1.0},
    "Borçlanma Araçları Yoğun Fon": {"TD91G": 1.0},
    
    # Para piyasası
    "Para Piyasası Fonu": {"TD91G": 1.0},
    
    # Kıymetli madenler
    "Kıymetli Madenler Fonu": {"ATKAP": 1.0},
    "Altın Fonu": {"ATKAP": 1.0},
    "Gümüş Fonu": {"ATKAP": 0.7, "FHISE": 0.3},
    "Emtia Fonu": {"ATKAP": 0.8, "FHISE": 0.2},
    
    # Katılım fonları
    "Katılım Fonu": {"FHISE": 0.5, "TD91G": 0.5},
    "Katılım Hisse Fonu": {"FHISE": 1.0},
    "Katılım Para Piyasası Fonu": {"TD91G": 1.0},
    
    # Fon sepeti
    "Fon Sepeti Fonu": {"FHISE": 0.4, "TD91G": 0.6},
    "Fon Sepeti Dengeli Fon": {"FHISE": 0.5, "TD91G": 0.5},
    "Fon Sepeti Agresif Fon": {"FHISE": 0.8, "TD91G": 0.2},
    "Fon Sepeti Muhafazakar Fon": {"TD91G": 0.8, "FHISE": 0.2},
    
    # Serbest fonlar
    "Serbest Fon": {"FHISE": 0.4, "TD91G": 0.6},
    
    # Gayrimenkul
    "Gayrimenkul Fonu": {"TD91G": 1.0},
    
    # Girişim sermayesi
    "Girişim Sermayesi Fonu": {"FHISE": 1.0},
    
    # Sürdürülebilirlik
    "Sürdürülebilirlik Fonu": {"FHISE": 0.8, "TD91G": 0.2},
    
    # Yabancı fonlar
    "Yabancı Hisse Senedi Fonu": {"FHISE": 0.5, "TD91G": 0.5},
    "Yabancı Fon Sepeti Fonu": {"FHISE": 0.4, "TD91G": 0.6},
}

# Bilinmeyen kategoriler için default mapping
DEFAULT_BENCHMARK_MAPPING = {"FHISE": 0.5, "TD91G": 0.5}


def get_fallback_benchmarks(kategori: str) -> dict[str, float]:
    """Fon kategorisine göre failsafe benchmark ağırlıklarını döndür."""
    if not kategori:
        return DEFAULT_BENCHMARK_MAPPING.copy()
    
    # Tam eşleşme dene
    if kategori in FON_KATEGORI_BENCHMARK_MAPPING:
        return FON_KATEGORI_BENCHMARK_MAPPING[kategori].copy()
    
    # Kısmi eşleşme dene (büyük/küçük harf duyarsız)
    kategori_lower = kategori.lower()
    for cat, mapping in FON_KATEGORI_BENCHMARK_MAPPING.items():
        if cat.lower() in kategori_lower or kategori_lower in cat.lower():
            return mapping.copy()
    
    # Anahtar kelime bazlı eşleşme
    keyword_mapping = [
        (["hisse", "stock", "equity"], {"FHISE": 1.0}),
        (["altın", "gold", "kıymetli maden", "emtia"], {"ATKAP": 1.0}),
        (["para piyasası", "para piyasasi", "money market", "likit"], {"TD91G": 1.0}),
        (["borçlanma", "borclanma", "fixed income", "tahvil", "bono"], {"TD91G": 1.0}),
        (["karma", "balanced", "değişken", "degisken"], {"FHISE": 0.6, "TD91G": 0.4}),
        (["fon sepeti", "fund of funds"], {"FHISE": 0.4, "TD91G": 0.6}),
        (["katılım", "participation", "faizsiz"], {"FHISE": 0.5, "TD91G": 0.5}),
        (["gayrimenkul", "real estate"], {"TD91G": 1.0}),
        (["serbest", "flexible"], {"FHISE": 0.4, "TD91G": 0.6}),
    ]
    
    for keywords, mapping in keyword_mapping:
        if any(kw in kategori_lower for kw in keywords):
            return mapping.copy()
    
    return DEFAULT_BENCHMARK_MAPPING.copy()
