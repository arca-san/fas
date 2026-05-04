#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fon metrik hesaplama modulu.
Sharpe, Sortino, Information Ratio, Treynor, Jensen Alpha.
"""

import numpy as np
import pandas as pd

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

TRADING_DAYS = 252


def _annual_return(daily_returns: pd.Series) -> float:
    n = len(daily_returns)
    if n == 0:
        return 0.0
    total = (1 + daily_returns).prod() ** (TRADING_DAYS / n) - 1
    return total


def _annualized_vol(daily_returns: pd.Series) -> float:
    std = daily_returns.std()
    return std * np.sqrt(TRADING_DAYS)


def _downside_vol(daily_returns: pd.Series) -> float:
    neg = daily_returns[daily_returns < 0]
    if len(neg) == 0:
        return 0.0
    return neg.std() * np.sqrt(TRADING_DAYS)


def _beta(fund_returns: pd.Series, market_returns: pd.Series) -> float:
    common = pd.concat([fund_returns, market_returns], axis=1).dropna()
    if len(common) < 2:
        return 0.0
    cov = common.iloc[:, 0].cov(common.iloc[:, 1])
    var = common.iloc[:, 1].var()
    if var == 0:
        return 0.0
    return cov / var


def _treynor(ann_ret: float, rf: float, beta_val: float) -> float:
    if beta_val == 0:
        return 0.0
    return (ann_ret - rf) / beta_val


def _information_ratio(fund_returns: pd.Series, market_returns: pd.Series) -> float:
    common = pd.concat([fund_returns, market_returns], axis=1).dropna()
    if len(common) < 2:
        return 0.0
    excess = common.iloc[:, 0] - common.iloc[:, 1]
    te = excess.std() * np.sqrt(TRADING_DAYS)
    if te == 0:
        return 0.0
    return (excess.mean() * TRADING_DAYS) / te


def calculate_fund_metrics(
    fund_dict: dict,
    risk_free_series: pd.Series = None,
    market_series: pd.Series = None,
) -> dict:
    """Her fon icin metrikleri hesapla.

    Parameters
    ----------
    fund_dict : dict
        {"FON_KODU": df, ...} — df'lerde "tarih" ve "fiyat" sutunlari olmali.
    risk_free_series : pd.Series, optional
        Gunluk risksiz getiri (onluk form, orn. 0.001).
    market_series : pd.Series, optional
        Market benchmark getiri serisi (gunluk, onluk form).

    Returns
    -------
    dict
        {"FON_KODU": {metric_name: value, ...}, ...}
    """
    results = {}

    for kod, df in fund_dict.items():
        if df.empty or "tarih" not in df.columns or "fiyat" not in df.columns:
            continue

        df_sorted = df.sort_values("tarih").reset_index(drop=True)
        prices = df_sorted["fiyat"]
        daily_returns = prices.pct_change().dropna()

        if len(daily_returns) < 2:
            continue

        # Risksiz getiri
        rf_daily = 0.0
        if risk_free_series is not None and not risk_free_series.empty:
            rf_aligned = risk_free_series.reindex(df_sorted.index).ffill().dropna()
            if len(rf_aligned) > 0:
                rf_daily = rf_aligned.mean()

        rf_annual = rf_daily * TRADING_DAYS
        ann_ret = _annual_return(daily_returns)
        vol = _annualized_vol(daily_returns)
        downside = _downside_vol(daily_returns)

        # Sharpe
        sharpe = (ann_ret - rf_annual) / vol if vol > 0 else 0.0

        # Sortino
        sortino = (ann_ret - rf_annual) / downside if downside > 0 else 0.0

        # Beta, Treynor, Jensen, Information Ratio (market benchmark lazim)
        beta_val = 0.0
        treynor = 0.0
        jensen = 0.0
        info_ratio = 0.0

        if market_series is not None and not market_series.empty:
            market_daily = market_series.pct_change().dropna()
            common = pd.DataFrame({"fund": daily_returns, "market": market_daily}).dropna()
            
            if len(common) >= 2:
                beta_val = _beta(common["fund"], common["market"])
                treynor = _treynor(ann_ret, rf_annual, beta_val)
                jensen = ann_ret - (rf_annual + beta_val * (_annual_return(market_daily) - rf_annual))
                info_ratio = _information_ratio(common["fund"], common["market"])

        total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
        n_days = len(daily_returns)
        ann_return_pct = ann_ret * 100

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
