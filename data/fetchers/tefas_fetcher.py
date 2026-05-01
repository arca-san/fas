#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEFAS Fetcher — AbstractFetcher implementasyonu.
Mevcut _tefas_api.py wrapper'ını sarar; cache, temizleme ve tip dönüşümü yapar.
"""

import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from config.settings import CACHE_DIR, CACHE_TTL_HOURS
from config.logger import get_logger
from data.fetchers.base import AbstractFetcher
from data.fetchers import _tefas_api

logger = get_logger(__name__)


class TefasFetcher(AbstractFetcher):
    """TEFAS veri kaynağı için fetcher."""

    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_hours: int = CACHE_TTL_HOURS):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_hours = cache_ttl_hours

    # ---------------------------------------------------------
    # Cache yardımcıları
    # ---------------------------------------------------------
    def _cache_key(self, symbol: str, start: date, end: date) -> str:
        raw = f"{symbol}_{start.isoformat()}_{end.isoformat()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"tefas_{key}.parquet"

    def _is_cache_valid(self, path: Path) -> bool:
        if not path.exists():
            return False
        age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
        return age_hours < self.cache_ttl_hours

    def _read_cache(self, path: Path) -> pd.DataFrame:
        logger.debug("Cache okunuyor: %s", path.name)
        return pd.read_parquet(path)

    def _write_cache(self, path: Path, df: pd.DataFrame) -> None:
        df.to_parquet(path, index=False)
        logger.debug("Cache yazıldı: %s", path.name)

    # ---------------------------------------------------------
    # AbstractFetcher implementasyonu
    # ---------------------------------------------------------
    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """
        TEFAS'tan tarihsel fiyat verisi çeker.
        Tarih verilmezse son 5 yılı getirir (PERIYOD_5YIL ile).
        """
        symbol = symbol.upper().strip()

        # Tarih yoksa son 5 yıl
        if start_date is None or end_date is None:
            logger.info("Tarih aralığı verilmedi, son 5 yıl çekiliyor: %s", symbol)
            raw = _tefas_api.fon_5y_fiyat(symbol)
            df = self._raw_to_dataframe(raw, symbol)
            return df

        # Cache kontrolü
        cache_key = self._cache_key(symbol, start_date, end_date)
        cache_path = self._cache_path(cache_key)
        if self._is_cache_valid(cache_path):
            return self._read_cache(cache_path)

        # API çağrısı
        logger.info("TEFAS'tan veri çekiliyor: %s (%s → %s)", symbol, start_date, end_date)
        bas = start_date.strftime("%Y%m%d")
        bit = end_date.strftime("%Y%m%d")
        raw = _tefas_api.fonlar_gunluk_detay_aralik(
            fon_tipi="YAT",
            bas_tarih=bas,
            bit_tarih=bit,
            fon_kodu=symbol,
        )
        df = self._raw_to_dataframe(raw, symbol)

        if not df.empty:
            self._write_cache(cache_path, df)
        return df

    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Fon kodu/ünvanı araması."""
        results = _tefas_api.fon_unvan_ara(query)
        return [
            {
                "kod": r.get("fonKodu", ""),
                "unvan": r.get("fonUnvan", ""),
                "tip": r.get("fonTipi", "YAT"),
            }
            for r in results
        ]

    def list_available_symbols(self) -> List[Dict[str, Any]]:
        """Tüm fonları listele."""
        results = _tefas_api.tum_fonlar("YAT")
        return [
            {
                "kod": r.get("fonKodu", ""),
                "unvan": r.get("fonUnvan", ""),
                "kurucu": r.get("kurucu", ""),
            }
            for r in results
        ]

    # ---------------------------------------------------------
    # Özel TEFAS metodları (adaptör katmanı)
    # ---------------------------------------------------------
    def get_portfolio_distribution(self, symbol: str, tarih: Optional[str] = None) -> Dict[str, float]:
        """Tek fonun portföy dağılımını normalize ederek döndürür."""
        symbol = symbol.upper().strip()
        raw = _tefas_api.fon_portfoy_dagilimi(symbol, tarih)
        if not raw:
            return {}
        return _tefas_api.portfoy_dagilimi_normalize(raw)

    # ---------------------------------------------------------
    # İç yardımcılar
    # ---------------------------------------------------------
    @staticmethod
    def _raw_to_dataframe(raw: List[Dict[str, Any]], symbol: str) -> pd.DataFrame:
        if not raw:
            return pd.DataFrame(columns=["tarih", "fon_kodu", "fon_unvan", "fiyat"])

        df = pd.DataFrame(raw)
        # TEFAS 'tarih' sütunu YYYY-MM-DD formatında string
        df["tarih"] = pd.to_datetime(df["tarih"], errors="coerce")
        df = df.dropna(subset=["tarih"])
        df = df.sort_values("tarih")

        # Standart sütun isimleri
        df = df.rename(columns={
            "fonKodu": "fon_kodu",
            "fonUnvan": "fon_unvan",
            "fiyat": "fiyat",
        })
        df["fon_kodu"] = symbol
        return df[["tarih", "fon_kodu", "fon_unvan", "fiyat"]]
