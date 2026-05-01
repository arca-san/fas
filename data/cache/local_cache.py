#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yerel disk cache — Parquet tabanlı.
TEFAS gibi yavaş/kısıtlı API'lerden veri tekrar tekrar çekilmesini önler.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd

from config.settings import CACHE_DIR, CACHE_TTL_HOURS
from config.logger import get_logger

logger = get_logger(__name__)


class LocalCache:
    """Parquet dosyaları üzerinden basit TTL cache."""

    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = CACHE_TTL_HOURS):
        self.cache_dir = Path(cache_dir) if cache_dir else Path(CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.parquet"

    def exists(self, key: str) -> bool:
        path = self._path(key)
        if not path.exists():
            return False
        age = (datetime.now().timestamp() - path.stat().st_mtime) / 3600
        return age < self.ttl_hours

    def get(self, key: str) -> pd.DataFrame:
        path = self._path(key)
        logger.debug("Cache okunuyor: %s", path.name)
        return pd.read_parquet(path)

    def set(self, key: str, df: pd.DataFrame) -> None:
        path = self._path(key)
        df.to_parquet(path, index=False)
        logger.debug("Cache yazıldı: %s", path.name)

    def invalidate(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()
            logger.debug("Cache silindi: %s", path.name)
