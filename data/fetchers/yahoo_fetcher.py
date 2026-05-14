from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from config.logger import get_logger
from config.yahoo_benchmarks import yahoo_benchmark_koda_gore

logger = get_logger(__name__)


class YahooFetcher:
    def get_historical_data(
        self, symbol: str, start: Optional[date] = None, end: Optional[date] = None
    ) -> pd.DataFrame:
        info = yahoo_benchmark_koda_gore(symbol)
        if info is None:
            logger.warning("Yahoo benchmark bilinmiyor: %s", symbol)
            return pd.DataFrame(columns=["tarih", "fiyat", "endeks_kodu"])

        try:
            start_s = start.isoformat() if start else None
            end_s = end.isoformat() if end else None
            ticker = yf.Ticker(info["kod"])
            df = ticker.history(start=start_s, end=end_s)
        except Exception as exc:
            logger.warning("Yahoo Finance veri hatasi (%s): %s", symbol, exc)
            return pd.DataFrame(columns=["tarih", "fiyat", "endeks_kodu"])

        if df.empty:
            return pd.DataFrame(columns=["tarih", "fiyat", "endeks_kodu"])

        result = pd.DataFrame({
            "tarih": df.index.date if hasattr(df.index, "date") else df.index,
            "fiyat": df["Close"].values,
            "endeks_kodu": symbol,
        })
        result["tarih"] = pd.to_datetime(result["tarih"])
        result = result.sort_values("tarih").reset_index(drop=True)
        return result
