#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEFAS fon detay sayfasından benchmark bilgilerini çekmeye çalışır.
Başarısız olursa config/benchmark_mapping.py içindeki failsafe mapping kullanılır.

Debug Modu:
-----------
TEFAS_API_DEBUG_BENCHMARK=True environment variable'ı set edilirse,
her benchmark çekim denemesi detaylı loglanır.

Not: TEFAS sitesi bot korumalı (Akamai TSPD) olduğundan doğrudan HTML
scraping mümkün değildir. Bu modül öncelikle mevcut API endpoint'lerini
dener, başarısız olursa kategori bazlı mapping'e düşer.

Araştırılan ve Başarısız Olan Yöntemler:
-----------------------------------------
1. /api/funds/fonEndeksGetir → Empty result
2. /api/funds/fonEndeksleriGetir → Empty result
3. /api/funds/fonBenchmarkGetir → Empty result
4. /api/funds/fonKarsilastirmaGetir → Empty result
5. /api/funds/fonProfilGetir → Empty result
6. /api/funds/fonDetayGetir → Empty result
7. /api/funds/fonEndeksBazliBilgiGetir → Empty result
8. HTML page scraping (/FonAnaliz.aspx?FonKod=XXX) → TSPD challenge (403)
9. Next.js _next/data/ endpointleri → TSPD challenge (403)
10. httpx ile farklı client → Aynı TSPD engeli
11. KAP (kap.org.tr) API → Fon benchmark verisi yok

Olası Çözümler (Gelecek):
--------------------------
- Playwright/Selenium ile browser otomasyonu
- TEFAS yeni API endpoint'i eklenirse
- Manuel benchmark listesi (kullanıcı girişi)
"""

import os
import logging
from typing import Optional

from data.fetchers import _tefas_api
from config.benchmark_mapping import get_fallback_benchmarks

logger = logging.getLogger(__name__)

# Debug modu
DEBUG_MODE = os.environ.get("TEFAS_API_DEBUG_BENCHMARK", "").lower() in ("1", "true", "yes")


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
                "source": "api" | "mapping",
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

        # 1. Önce fon kategorisini al (verilmediyse)
        kategori = fon_kategori
        if kategori is None:
            dbg("Kategori verilmedi, fon_anlik_bilgi'den çekiliyor...")
            kategori = self._get_fund_kategori(fon_kodu)
            dbg(f"Kategori: {kategori or 'BULUNAMADI'}")

        if not kategori:
            kategori = "Bilinmeyen"
            dbg("Kategori bulunamadı, default kullanılacak")

        # 2. API'den benchmark bilgisi çekmeyi dene
        dbg("API endpoint'leri deneniyor...")
        api_result = self._try_api_benchmarks(fon_kodu)
        if api_result:
            dbg(f"API'den benchmark bulundu: {len(api_result)} adet")
            return {
                "benchmarks": api_result,
                "source": "api",
                "message": f"{fon_kodu} benchmarkları TEFAS API'den çekildi.",
                "debug_info": "\n".join(debug_lines) if debug_lines else None,
            }
        else:
            dbg("API endpoint'leri benchmark vermedi")

        # 3. Scraping (şu an kapalı - TSPD koruması)
        dbg("Scraping denenmiyor (TSPD koruması aktif)")

        # 4. Failsafe: Kategori bazlı mapping
        dbg(f"Failsafe mapping kullanılıyor (kategori: {kategori})")
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
            "message": f"{fon_kodu} benchmarkları fon türüne göre atandı ({kategori}).",
            "debug_info": "\n".join(debug_lines) if debug_lines else None,
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

        Aşağıdaki endpoint'ler test edildi ve hiçbiri benchmark verisi döndürmedi:
        - /api/funds/fonEndeksGetir
        - /api/funds/fonEndeksleriGetir
        - /api/funds/fonBenchmarkGetir
        - /api/funds/fonKarsilastirmaGetir
        - /api/funds/fonKarsilastir
        - /api/funds/fonProfilGetir
        - /api/funds/fonDetayGetir
        - /api/funds/fonEndeksBazliBilgiGetir
        - /api/funds/fonKarsilastirmaEndeksleri
        - /api/funds/fonBenchmarkEndeksleri
        - /api/funds/fonEndeksleriGetir

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
