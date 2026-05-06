#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAP.org.tr benchmark scraper.
Selenium Edge ile KAP fon detay sayfasından benchmark/endeks verilerini çekmeyi dener.
KAP fon detay sayfaları (/tr/fon-bilgileri/genel/{kod}) genellikle hata sayfası
döndürdüğünden, scraper başarısız olursa None döner ve fallback mapping kullanılır.
Sonuçları JSON cache'e yazar (24 saat TTL).
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "benchmarks.json"
CACHE_TTL_HOURS = 24
PAGE_LOAD_TIMEOUT_SEC = 5
RENDER_WAIT_SEC = 2

import os
SKIP_SCRAPING = os.environ.get("KAP_SKIP_SCRAPING", "1").lower() in ("1", "true", "yes")


class KAPScraper:
    """Selenium Edge ile KAP benchmark scraper.

    Not: KAP fon detay sayfaları genellikle 'Bir Hata Oluştu!' sayfası
    döndürdüğünden scraping çoğu zaman başarısız olur. Bu durumda
    None döner ve fallback mapping kullanılır.
    """

    def __init__(self, cache_file: Optional[Path] = None, ttl_hours: int = CACHE_TTL_HOURS):
        self.cache_file = cache_file or CACHE_FILE
        self.ttl_hours = ttl_hours
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def get_cached(self, fund_code: str) -> Optional[list]:
        """Cache'den benchmark verisi al (TTL kontrolü ile)."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        entry = cache.get(fund_code.upper())
        if not entry:
            return None

        fetched_at = datetime.fromisoformat(entry.get("fetched_at", ""))
        if datetime.now() - fetched_at > timedelta(hours=self.ttl_hours):
            logger.info("Cache süresi dolmus (%s), yeniden çekilecek", fund_code)
            return None

        logger.info("Cache'den alindi (%s): %s benchmark", fund_code, len(entry.get("benchmarks", [])))
        return entry.get("benchmarks")

    def save_cache(self, fund_code: str, benchmarks: list):
        """Benchmark verisini cache'e yaz."""
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            cache = {}

        cache[fund_code.upper()] = {
            "benchmarks": benchmarks,
            "fetched_at": datetime.now().isoformat(),
        }

        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        logger.info("Cache'e yazildi (%s): %s benchmark", fund_code, len(benchmarks))

    def scrape_benchmark(self, fund_code: str) -> Optional[list]:
        """KAP sayfasından benchmark verilerini çekmeyi dener.

        KAP fon detay sayfaları genellikle hata döndürdüğünden
        bu metod çoğu zaman None döner.

        Parameters
        ----------
        fund_code : str
            TEFAS fon kodu (örn: "MAC")

        Returns
        -------
        list | None
            [{"kod": str, "agirlik": float, "ad": str}, ...] veya None
        """
        if SKIP_SCRAPING:
            logger.debug("KAP scraping atlandi (KAP_SKIP_SCRAPING=1)")
            return None

        fund_code = fund_code.upper().strip()
        url = f"https://www.kap.org.tr/tr/fon-bilgileri/genel/{fund_code.lower()}"

        driver = None
        try:
            opts = Options()
            opts.add_argument("--headless")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--window-size=1920,1080")
            opts.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Edge(options=opts)
            driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SEC)

            logger.info("KAP sayfasi yükleniyor: %s", url)
            driver.get(url)

            time.sleep(RENDER_WAIT_SEC)

            # Hata sayfası kontrolü
            body = driver.find_element(By.TAG_NAME, "body")
            page_text = body.text
            if "Bir Hata Oluştu" in page_text or "Hata" in page_text:
                logger.warning("KAP hata sayfası döndürdü (%s)", fund_code)
                return None

            # Benchmark/endeks verilerini ara
            benchmarks = self._parse_benchmarks(driver)

            if benchmarks:
                logger.info(
                    "KAP'den benchmark bulundu (%s): %s adet",
                    fund_code,
                    len(benchmarks),
                )
                self.save_cache(fund_code, benchmarks)
                return benchmarks

            logger.warning("KAP sayfasinda benchmark verisi bulunamadi (%s)", fund_code)
            return None

        except Exception as exc:
            logger.error("KAP scraping hatasi (%s): %s", fund_code, exc)
            return None

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _parse_benchmarks(self, driver) -> list:
        """Driver'daki sayfadan benchmark verilerini parse et."""
        benchmarks = []

        # Tablo satırlarını ara
        rows = driver.find_elements(By.CSS_SELECTOR, "tr")

        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    continue

                row_text = " ".join(cell.text for cell in cells).lower()

                if any(kw in row_text for kw in ["endeks", "benchmark", "kıyaslama", "karsilastir", "referans"]):
                    parsed = self._extract_from_row(cells)
                    if parsed:
                        benchmarks.append(parsed)

            except Exception:
                continue

        # Tabloda bulunamadıysa metin içeriğinde ara
        if not benchmarks:
            benchmarks = self._parse_from_text(driver)

        return benchmarks

    def _extract_from_row(self, cells) -> Optional[dict]:
        """Bir tablo satırından benchmark bilgisini çıkar."""
        kod = None
        agirlik = None
        ad = None

        for cell in cells:
            text = cell.text.strip()
            text_lower = text.lower()

            if not kod:
                code_match = re.search(r"\b([A-ZÇĞİÖŞÜ]{2,5})\b", text)
                if code_match:
                    kod = code_match.group(1)

            if agirlik is None:
                pct_match = re.search(r"(\d+\.?\d*)\s*%", text)
                if pct_match:
                    agirlik = float(pct_match.group(1)) / 100.0
                else:
                    decimal_match = re.search(r"\b(0\.\d+)\b", text)
                    if decimal_match:
                        agirlik = float(decimal_match.group(1))

            if not ad and any(kw in text_lower for kw in ["endeks", "benchmark", "kıyaslama"]):
                ad = text

        if kod:
            return {
                "kod": kod,
                "agirlik": agirlik if agirlik is not None else 1.0,
                "ad": ad or kod,
            }
        return None

    def _parse_from_text(self, driver) -> list:
        """Sayfa metninden benchmark verilerini parse et."""
        benchmarks = []
        body = driver.find_element(By.TAG_NAME, "body")
        text = body.text

        pattern = r"([A-ZÇĞİÖŞÜ]{2,5})\s*[:\-]?\s*(\d+\.?\d*)\s*%"
        matches = re.findall(pattern, text)

        if matches:
            total_weight = 0.0
            for kod, pct in matches:
                weight = float(pct) / 100.0
                total_weight += weight
                benchmarks.append({
                    "kod": kod,
                    "agirlik": weight,
                    "ad": kod,
                })

            if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
                for bm in benchmarks:
                    bm["agirlik"] /= total_weight

        return benchmarks
