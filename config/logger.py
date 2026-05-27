#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basit loglama ayarları.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log rotasyonu: 5MB / dosya, 3 yedek
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3


def get_logger(name: str) -> logging.Logger:
    """İsimli logger üretir (eğer daha önce ayarlanmadıysa)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # .env'den debug seviyesi oku
    import os
    debug = os.environ.get("FAS_DEBUG", "").lower() in ("1", "true", "yes")
    level = logging.DEBUG if debug else logging.INFO

    logger.setLevel(level)

    # Konsol handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)

    # Dosya handler (rotating)
    file_handler = RotatingFileHandler(
        LOG_DIR / "fas.log", encoding="utf-8",
        maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    return logger
