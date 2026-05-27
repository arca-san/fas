#!/usr/bin/env python3
"""
Makroekonomik veri çekme modülü.
TCMB EVDS API'si için iskelet + mevcut TTUFE endeksi üzerinden TÜFE vekili.

Planlanan:
- TCMB EVDS: faiz oranı, döviz kuru, enflasyon (API key gerekli)
- TÜİK: TÜFE, ÜFE, GSYH
- Yahoo Finance: CDS spreads

Şu anda TTUFE (BIST-KYD TÜFE endeksi) mevcut KydFetcher üzerinden kullanılabiliyor.
"""

import os
import logging
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# TCMB EVDS API Key (opsiyonel — .env'den)
EVDS_API_KEY = os.environ.get("FAS_EVDS_API_KEY", "")

# TCMB EVDS seri kodları
EVDS_SERIES = {
    "policy_rate": "TP.FAIZ.01",         # Politika faizi (haftalık repo)
    "usd_try": "TP.DK.USD.A",             # USD/TRY döviz kuru (günlük)
    "eur_try": "TP.DK.EUR.A",             # EUR/TRY döviz kuru
    "cpi_monthly": "TP.TUFE.01",          # TÜFE aylık değişim
    "gdp_yearly": "TP.GSYIH.01",          # GSYH yıllık
}


def get_tufe_via_kyd(start: date, end: date):
    """TTUFE (BIST-KYD TÜFE endeksi) üzerinden enflasyon vekili.

    Not: TTUFE bir endekstir, TÜİK TÜFE'si değildir. Trend için yeterlidir.
    """
    try:
        from config.benchmarks import get_benchmark_data
        df = get_benchmark_data("TTUFE", start, end)
        if df.empty:
            return pd.Series(dtype=float)
        s = df.set_index("tarih")["fiyat"].astype(float)
        return s.pct_change().dropna()
    except Exception as exc:
        logger.warning("TTUFE alınamadı: %s", exc)
        return pd.Series(dtype=float)


def get_evds_series(series_key: str, start: date, end: date):
    """TCMB EVDS API'den zaman serisi çek. (API key gerekir)"""
    if not EVDS_API_KEY:
        logger.debug("EVDS API key tanımlı değil, seri alınamadı: %s", series_key)
        return pd.Series(dtype=float)

    series_code = EVDS_SERIES.get(series_key)
    if not series_code:
        return pd.Series(dtype=float)

    try:
        url = ("https://evds2.tcmb.gov.tr/service/evds/series="
               f"{series_code}&startDate={start.isoformat()}&endDate={end.isoformat()}"
               "&type=json")
        headers = {"key": EVDS_API_KEY}
        resp = requests.get(url, headers=headers, timeout=30)
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return pd.Series(dtype=float)
        df = pd.DataFrame(items)
        date_col = [c for c in df.columns if "Tarih" in c or "Date" in c][0]
        val_col = [c for c in df.columns if c != date_col][0]
        df[date_col] = pd.to_datetime(df[date_col])
        df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
        return df.set_index(date_col)[val_col].dropna()
    except Exception as exc:
        logger.warning("EVDS serisi alınamadı (%s): %s", series_key, exc)
        return pd.Series(dtype=float)


def get_policy_rate(start: date, end: date):
    """TCMB politika faizi."""
    return get_evds_series("policy_rate", start, end)


def get_cpi_evds(start: date, end: date):
    """TCMB EVDS TÜFE serisi."""
    return get_evds_series("cpi_monthly", start, end)
