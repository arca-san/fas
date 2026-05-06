#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEFAS fon detay sayfasından benchmark bilgilerini çekmeye çalışır.
Başarısız olursa config/benchmark_mapping.py içindeki failsafe mapping kullanılır.

Not: TEFAS sitesi bot korumalı (Akamai TSPD) olduğundan doğrudan HTML
scraping mümkün değildir. Bu modül öncelikle mevcut API endpoint'lerini
dener, başarısız olursa kategori bazlı mapping'e düşer.
"""

import logging
from typing import Optional

from data.fetchers import _tefas_api
from config.benchmark_mapping import get_fallback_benchmarks

logger = logging.getLogger(__name__)


class TefasBenchmarkScraper:
    """TEFAS fon benchmarklarını çekmeye çalışan scraper."""

    def get_fund_benchmarks(self, fon_kodu: str, fon_kategori: Optional[str] = None) -> dict:
        """Fon benchmarklarını çek.

        Parameters
        ----------
        fon_kodu : str
            TEFAS fon kodu (örn: "MAC", "AAL")
        fon_kategori : str, optional
            Fon kategorisi (örn: "Hisse Senedi Fonu").
            Verilmezse fon_anlik_bilgi'den çekilir.

        Returns
        -------
        dict
            {
                "benchmarks": [{"kod": str, "agirlik": float}, ...],
                "source": "api" | "scraping" | "mapping",
                "message": str,
            }
        """
        fon_kodu = fon_kodu.upper().strip()

        # 1. Önce fon kategorisini al (verilmediyse)
        kategori = fon_kategori
        if kategori is None:
            kategori = self._get_fund_kategori(fon_kodu)

        # 2. API'den benchmark bilgisi çekmeyi dene
        api_result = self._try_api_benchmarks(fon_kodu)
        if api_result:
            return {
                "benchmarks": api_result,
                "source": "api",
                "message": f"{fon_kodu} benchmarkları TEFAS API'den çekildi.",
            }

        # 3. Scraping denenebilir (şu an bot koruması nedeniyle kapalı)
        # scraping_result = self._try_scraping(fon_kodu)
        # if scraping_result:
        #     return {
        #         "benchmarks": scraping_result,
        #         "source": "scraping",
        #         "message": f"{fon_kodu} benchmarkları TEFAS sayfasından çekildi.",
        #     }

        # 4. Failsafe: Kategori bazlı mapping
        mapping = get_fallback_benchmarks(kategori)
        benchmarks = [
            {"kod": kod, "agirlik": agirlik}
            for kod, agirlik in mapping.items()
        ]

        return {
            "benchmarks": benchmarks,
            "source": "mapping",
            "message": f"{fon_kodu} benchmarkları fon türüne göre atandı ({kategori}).",
        }

    def _get_fund_kategori(self, fon_kodu: str) -> Optional[str]:
        """Fon kategorisini fon_anlik_bilgi'den al."""
        try:
            info = _tefas_api.fon_anlik_bilgi(fon_kodu)
            if info:
                return info.get("fonKategori")
        except Exception as exc:
            logger.warning("Fon kategorisi alınamadı (%s): %s", fon_kodu, exc)
        return None

    def _try_api_benchmarks(self, fon_kodu: str) -> Optional[list]:
        """TEFAS API endpoint'lerinden benchmark bilgisi çekmeyi dene.

        Şu an için bilinen endpoint'ler doğrudan benchmark verisi döndürmüyor.
        Gelecekte yeni endpoint'ler eklenirse buraya eklenebilir.
        """
        return None

    def _try_scraping(self, fon_kodu: str) -> Optional[list]:
        """TEFAS fon detay sayfasından benchmark bilgisi çekmeyi dene.

        Not: TEFAS sitesi Akamai TSPD bot koruması kullandığından
        mevcut HTTP session ile HTML scraping mümkün değildir.
        Selenium/Playwright gibi browser otomasyonu gerekebilir.

        Bu metod şu an NotImplementedError döndürür.
        """
        return None
