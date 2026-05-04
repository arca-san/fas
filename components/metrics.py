#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fon metrik hesaplama modulu.
Sharpe, Sortino, Information Ratio, Treynor, Jensen Alpha.
"""

import numpy as np
import pandas as pd
import logging

from config.constants import (
    METRIC_VOLATILITY,
    METRIC_DOWNSIDE_VOL,
    METRIC_SHARPE,
    METRIC_SORTINO,
    METRIC_TREYNOR,
    METRIC_ALPHA,
    METRIC_BETA,
    METRIC_INFORMATION_RATIO,
    METRIC_TOTAL_RETURN,
    METRIC_ANNUALIZED_RETURN,
)

logger = logging.getLogger(__name__)

TRADING_DAYS = 252


def _annual_return(daily_returns: pd.Series) -> float:
    """Gunluk getirilerden yillandirilmis getiri hesapla (bilesik)."""
    n = len(daily_returns)
    if n == 0:
        return 0.0
    total = (1 + daily_returns).prod() ** (TRADING_DAYS / n) - 1
    return total


def _annualized_vol(daily_returns: pd.Series) -> float:
    """Gunluk getirilerden yillik volatilite hesapla."""
    std = daily_returns.std(ddof=1)
    return std * np.sqrt(TRADING_DAYS)


def _downside_vol(daily_returns: pd.Series) -> float:
    """Asagi yonlu yillik volatilite hesapla."""
    neg = daily_returns[daily_returns < 0]
    if len(neg) == 0:
        return 0.0
    return neg.std(ddof=1) * np.sqrt(TRADING_DAYS)


def calculate_fund_metrics(
    fund_dict: dict,
    rf_daily_returns: pd.Series,
    market_prices: pd.Series,
) -> dict:
    """Her fon icin metrikleri hesapla.

    Parameters
    ----------
    fund_dict : dict
        {"FON_KODU": df, ...} — df'lerde "tarih" ve "fiyat" sutunlari olmali.
    rf_daily_returns : pd.Series
        Gunluk risksiz getiri (onluk form, orn. 0.0012 = %0.12).
        Index tarih olmali, tum fon tarihlerini kapsamali.
    market_prices : pd.Series
        Market benchmark fiyat seviyeleri (index degerleri).
        Index tarih olmali. Fonlarin tarihleriyle ayni olacak sekilde
        reindex edilir.

    Returns
    -------
    dict
        {"FON_KODU": {metric_name: value, ...}, ...}
    """
    results = {}

    # Market getirileri
    market_returns = market_prices.pct_change().dropna()

    # Risksiz getiri yillik
    rf_daily = rf_daily_returns.mean() if not rf_daily_returns.empty else 0.0
    rf_annual = rf_daily * TRADING_DAYS

    for kod, df in fund_dict.items():
        if df.empty or "tarih" not in df.columns or "fiyat" not in df.columns:
            continue

        df_sorted = df.sort_values("tarih").reset_index(drop=True)
        prices = df_sorted["fiyat"]
        tarihler = pd.to_datetime(df_sorted["tarih"])
        daily_returns = prices.pct_change().dropna()
        daily_returns_dates = daily_returns.copy()
        daily_returns_dates.index = tarihler[1:]  # pct_change ilk satiri dusurur

        if len(daily_returns_dates) < 2:
            continue

        # Fon yillandirilmis getiri ve volatilite
        ann_ret = _annual_return(daily_returns_dates)
        vol = _annualized_vol(daily_returns_dates)
        downside = _downside_vol(daily_returns_dates)

        # Market getirileri ile align (tarih bazli)
        market_aligned = market_returns.reindex(daily_returns_dates.index).dropna()
        
        # Common tarihler
        common_dates = daily_returns_dates.index.intersection(market_aligned.index)
        if len(common_dates) < 2:
            beta_val = 0.0
            treynor = 0.0
            jensen = 0.0
            info_ratio = 0.0
        else:
            fund_common = daily_returns_dates.loc[common_dates]
            market_common = market_aligned.loc[common_dates]
            
            # Beta: Cov(fund, market) / Var(market)
            cov_fm = fund_common.cov(market_common)
            var_m = market_common.var()
            beta_val = cov_fm / var_m if var_m > 0 else 0.0
            
            # Treynor: (Rp - Rf) / Beta
            if beta_val != 0:
                treynor = (ann_ret - rf_annual) / beta_val
            else:
                treynor = 0.0
            
            # Jensen Alpha: Rp - [Rf + Beta * (Rm - Rf)]
            market_ann_ret = _annual_return(market_common)
            jensen = ann_ret - (rf_annual + beta_val * (market_ann_ret - rf_annual))
            
            # Information Ratio: (Rp - Rm) / Tracking Error
            excess = fund_common - market_common
            te = excess.std(ddof=1) * np.sqrt(TRADING_DAYS)
            if te > 0:
                info_ratio = (excess.mean() * TRADING_DAYS) / te
            else:
                info_ratio = 0.0

        # Sharpe
        sharpe = (ann_ret - rf_annual) / vol if vol > 0 else 0.0

        # Sortino
        sortino = (ann_ret - rf_annual) / downside if downside > 0 else 0.0

        # Toplam getiri
        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
        ann_return_pct = ann_ret * 100

        logger.info(
            "%s: ret=%.2f%%, vol=%.2f%%, rf_ann=%.4f, sharpe=%.3f, beta=%.3f",
            kod, ann_return_pct, vol * 100, rf_annual, sharpe, beta_val,
        )

        results[kod] = {
            METRIC_TOTAL_RETURN: round(total_return, 2),
            METRIC_ANNUALIZED_RETURN: round(ann_return_pct, 2),
            METRIC_VOLATILITY: round(vol * 100, 2),
            METRIC_DOWNSIDE_VOL: round(downside * 100, 2),
            METRIC_SHARPE: round(sharpe, 3),
            METRIC_SORTINO: round(sortino, 3),
            METRIC_BETA: round(beta_val, 3),
            METRIC_TREYNOR: round(treynor, 3),
            METRIC_ALPHA: round(jensen, 3),
            METRIC_INFORMATION_RATIO: round(info_ratio, 3),
        }

    return results


def select_fund_benchmark(unvan: str, kyd_fetcher) -> pd.Series:
    """Fon turune gore benchmark sec.

    Altin/gumus/kiymetli madenler -> ATKAP (altin kapanis)
    Diger -> FHISE (hisse senedi fon endeksi)

    Returns
    -------
    pd.Series
        Benchmark fiyat serisi (tarih, fiyat)
    """
    unvan_lower = (unvan or "").lower()
    gold_keywords = ["altin", "gumus", "kiymetli maden", "precious metal", "gold", "silver", "emtia"]
    is_gold = any(kw in unvan_lower for kw in gold_keywords)

    if is_gold:
        symbol = "ATKAP"
    else:
        symbol = "FHISE"

    from datetime import date, timedelta
    end = date.today()
    start = end - timedelta(days=365 * 5)

    try:
        df = kyd_fetcher.get_historical_data(symbol, start, end)
        if not df.empty:
            return pd.Series(
                df["fiyat"].values,
                index=pd.to_datetime(df["tarih"]),
                name=symbol,
            )
    except Exception:
        pass

    return None
