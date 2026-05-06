#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEFAS fon benchmark bilgilerini cekmeye calisir.
Once KAP.org.tr'den Selenium ile cekmeyi dener (cache'li).
Basarisiz olursa config/benchmark_mapping.py icindeki failsafe mapping kullanilir.

Benchmark Cekme Sirasi:
-----------------------
1. KAP cache (24 saat gecerli)
2. KAP scraping (Selenium Edge ile)
3. Kategori bazli failsafe mapping

Debug Modu:
-----------
TEFAS_API_DEBUG_BENCHMARK=True environment variable'i set edilirse,
her benchmark cekim denemesi detayli loglanir.
"""

import os
import logging
from typing import Optional

from data.fetchers import _tefas_api
from config.benchmark_mapping import get_fallback_benchmarks
from scraper.kap_scraper import KAPScraper

logger = logging.getLogger(__name__)

DEBUG_MODE = os.environ.get("TEFAS_API_DEBUG_BENCHMARK", "").lower() in ("1", "true", "yes")


class TefasBenchmarkScraper:
    """Fon benchmarklarini ceken scraper. KAP + cache + mapping fallback."""

    def get_fund_benchmarks(self, fon_kodu: str, fon_kategori: Optional[str] = None) -> dict:
        """Fon benchmarklarini cek.

        Parameters
        ----------
        fon_kodu : str
            TEFAS fon kodu (orn: "MAC", "AAL")
        fon_kategori : str, optional
            Fon kategorisi (orn: "Hisse Senedi Fonu").
            Verilmezse fon_anlik_bilgi'den cekilir.

        Returns
        -------
        dict
            {
                "benchmarks": [{"kod": str, "agirlik": float}, ...],
                "source": "kap_cache" | "kap_scraping" | "mapping",
                "message": str,
                "debug_info": str (sadece debug modunda),
            }
        """
        fon_kodu = fon_kodu.upper().strip()
        debug_lines = []

        def dbg(msg: str):
            if DEBUG_MODE:
                debug_lines.append(msg)
                logger.debug("[BENCHMARK] %s: %s", fon_kodu, msg)

        # 1. Once fon kategorisini al (verilmediyse)
        kategori = fon_kategori
        if kategori is None:
            dbg("Kategori verilmedi, fon_anlik_bilgi'den cekiliyor...")
            kategori = self._get_fund_kategori(fon_kodu)
            dbg(f"Kategori: {kategori or 'BULUNAMADI'}")

        if not kategori:
            kategori = "Bilinmeyen"
            dbg("Kategori bulunamadi, default kullanilacak")

        # 2. KAP cache'den kontrol et
        dbg("KAP cache kontrol ediliyor...")
        kap = KAPScraper()
        cached = kap.get_cached(fon_kodu)
        if cached:
            dbg(f"KAP cache'den bulundu: {len(cached)} benchmark")
            benchmarks = [
                {"kod": bm["kod"], "agirlik": bm["agirlik"]}
                for bm in cached
            ]
            return {
                "benchmarks": benchmarks,
                "source": "kap_cache",
                "message": f"{fon_kodu} benchmarklari KAP cache'den okundu.",
                "debug_info": "\n".join(debug_lines) if debug_lines else None,
            }

        # 3. KAP scraping dene
        dbg("KAP scraping deneniyor...")
        kap_result = kap.scrape_benchmark(fon_kodu)
        if kap_result:
            dbg(f"KAP scraping'den bulundu: {len(kap_result)} benchmark")
            benchmarks = [
                {"kod": bm["kod"], "agirlik": bm["agirlik"]}
                for bm in kap_result
            ]
            return {
                "benchmarks": benchmarks,
                "source": "kap_scraping",
                "message": f"{fon_kodu} benchmarklari KAP.org.tr'den cekildi.",
                "debug_info": "\n".join(debug_lines) if debug_lines else None,
            }

        dbg("KAP scraping basarisiz")

        # 4. Failsafe: Kategori bazli mapping
        dbg(f"Failsafe mapping kullaniliyor (kategori: {kategori})")
        mapping = get_fallback_benchmarks(kategori)
        benchmarks = [
            {"kod": kod, "agirlik": agirlik}
            for kod, agirlik in mapping.items()
        ]
        dbg(f"Mapping sonucu: {len(benchmarks)} benchmark")
        for bm in benchmarks:
            dbg(f"  - {bm['kod']}: %{bm['agirlik']*100:.0f}")

        return {
            "benchmarks": benchmarks,
            "source": "mapping",
            "message": f"{fon_kodu} benchmarklari fon turune gore atandi ({kategori}).",
            "debug_info": "\n".join(debug_lines) if debug_lines else None,
        }

    def _get_fund_kategori(self, fon_kodu: str) -> Optional[str]:
        """Fon kategorisini fon_anlik_bilgi'den al."""
        try:
            info = _tefas_api.fon_anlik_bilgi(fon_kodu)
            if info:
                return info.get("fonKategori")
        except Exception as exc:
            logger.warning("Fon kategorisi alinamadi (%s): %s", fon_kodu, exc)
        return None
