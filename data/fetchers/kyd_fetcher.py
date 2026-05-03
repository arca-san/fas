import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import requests

from config.settings import CACHE_DIR, CACHE_TTL_HOURS
from config.logger import get_logger
from config.benchmarks import BIST_KYD_ENDEXLER, benchmark_koda_gore
from data.fetchers.base import AbstractFetcher

logger = get_logger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
BASE_URL = "https://www.borsaistanbul.com"
GRAPHIC_API = f"{BASE_URL}/graphic.php"


class KydFetcher(AbstractFetcher):
    def __init__(self, cache_dir: Optional[Path] = None, cache_ttl_hours: int = CACHE_TTL_HOURS, timeout: int = 30):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_hours = cache_ttl_hours
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.timeout = timeout

    def _cache_key(self, symbol: str) -> str:
        return hashlib.md5(f"kyd_{symbol}".encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"kyd_{key}.parquet"

    def _is_cache_valid(self, path: Path) -> bool:
        if not path.exists():
            return False
        age_hours = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
        return age_hours < self.cache_ttl_hours

    def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        symbol = symbol.upper().strip()

        cache_key = self._cache_key(symbol)
        cache_path = self._cache_path(cache_key)

        if self._is_cache_valid(cache_path):
            df = pd.read_parquet(cache_path)
            logger.debug("KYD cache hit: %s", symbol)
        else:
            df = self._fetch_from_api(symbol)
            if not df.empty:
                df.to_parquet(cache_path, index=False)
                logger.info("KYD cache yazildi: %s (%s kayit)", symbol, len(df))

        if df.empty:
            return df

        if start_date:
            df = df[df["tarih"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["tarih"] <= pd.Timestamp(end_date)]

        return df.reset_index(drop=True)

    def _fetch_from_api(self, symbol: str) -> pd.DataFrame:
        params = {"veriTuru": "endeks-graphic", "indexCode": symbol}
        try:
            resp = self.session.get(GRAPHIC_API, params=params, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.warning("KYD API hatasi (%s): %s", symbol, exc)
            return pd.DataFrame(columns=["tarih", "fiyat", "endeks_kodu"])

        if payload.get("status") != "success":
            logger.warning("KYD API basarisiz (%s): %s", symbol, payload.get("message", ""))
            return pd.DataFrame(columns=["tarih", "fiyat", "endeks_kodu"])

        records = payload.get("data", [])
        if not records:
            logger.warning("KYD API veri yok: %s", symbol)
            return pd.DataFrame(columns=["tarih", "fiyat", "endeks_kodu"])

        rows = []
        for r in records:
            try:
                rows.append({
                    "tarih": datetime.strptime(r["hisTs"], "%Y-%m-%d"),
                    "fiyat": float(r["clval"]),
                    "endeks_kodu": symbol,
                })
            except (ValueError, KeyError):
                continue

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        df = df.sort_values("tarih").reset_index(drop=True)
        df.columns = ["tarih", "fiyat", "endeks_kodu"]

        return df

    def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        query = query.upper().strip()
        results = []
        for e in BIST_KYD_ENDEXLER:
            if query in e["kod"] or query in e["ad"].upper():
                results.append({
                    "kod": e["kod"],
                    "unvan": e["ad"],
                    "tip": f"BIST-KYD {e['grup']}",
                })
        return results

    def list_available_symbols(self) -> List[Dict[str, Any]]:
        return [
            {"kod": e["kod"], "unvan": e["ad"], "tip": f"BIST-KYD {e['grup']}"}
            for e in BIST_KYD_ENDEXLER
        ]
