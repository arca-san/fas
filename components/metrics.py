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
    METRIC_MAX_DRAWDOWN,
    METRIC_VAR,
    METRIC_CVAR,
    METRIC_SHARPE,
    METRIC_SORTINO,
    METRIC_TREYNOR,
    METRIC_ALPHA,
    METRIC_BETA,
    METRIC_R_SQUARED,
    METRIC_INFORMATION_RATIO,
    METRIC_TOTAL_RETURN,
    METRIC_ANNUALIZED_RETURN,
    METRIC_CALMAR,
    METRIC_STERLING,
    METRIC_UP_CAPTURE,
    METRIC_DOWN_CAPTURE,
    METRIC_BATTING_AVG,
    METRIC_SKEWNESS,
    METRIC_KURTOSIS,
    METRIC_AVG_DRAWDOWN,
    METRIC_DD_DURATION,
    METRIC_RECOVERY_TIME,
    METRIC_ULCER,
    METRIC_OMEGA,
    METRIC_ACTIVE_SHARE,
    METRIC_M2,
)
from config.settings import VAR_CONFIDENCE
from scipy import stats as sp_stats

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


def _max_drawdown(daily_returns: pd.Series) -> float:
    """Maksimum dusus (peak-to-trough) yuzdesini hesapla, pozitif deger."""
    if len(daily_returns) < 2:
        return 0.0
    cum = (1 + daily_returns).cumprod()
    running_max = cum.expanding().max()
    drawdown = (cum - running_max) / running_max
    max_dd = drawdown.min()
    return abs(max_dd) * 100


def _value_at_risk(daily_returns: pd.Series) -> float:
    """Tarihsel Value at Risk (VaR) %95 guven duzeyinde, pozitif yuzde."""
    if len(daily_returns) < 2:
        return 0.0
    var = np.percentile(daily_returns, (1 - VAR_CONFIDENCE) * 100)
    return abs(var) * 100


def _conditional_var(daily_returns: pd.Series) -> float:
    """Tarihsel CVaR (Expected Shortfall) %95, pozitif yuzde."""
    if len(daily_returns) < 2:
        return 0.0
    threshold = np.percentile(daily_returns, (1 - VAR_CONFIDENCE) * 100)
    tail = daily_returns[daily_returns <= threshold]
    if len(tail) == 0:
        return 0.0
    return abs(tail.mean()) * 100


def _r_squared(fund_returns: pd.Series, market_returns: pd.Series) -> float:
    """R² = korelasyon(fon, benchmark)²"""
    common = fund_returns.index.intersection(market_returns.index)
    if len(common) < 3:
        return 0.0
    corr = fund_returns.loc[common].corr(market_returns.loc[common])
    if pd.isna(corr):
        return 0.0
    return round(corr ** 2, 4)


def _calmar_ratio(ann_ret: float, max_dd: float) -> float:
    """Calmar Oranı = Yıllık Getiri / Max Drawdown."""
    return (ann_ret * 100) / max_dd if max_dd > 0 else 0.0


def _sterling_ratio(ann_ret: float, avg_dd: float) -> float:
    """Sterling Oranı = Yıllık Getiri / (Ortalama DD + %10)."""
    return (ann_ret * 100) / (avg_dd + 10) if (avg_dd + 10) > 0 else 0.0


def _up_down_capture(fund_returns: pd.Series, market_returns: pd.Series) -> tuple:
    """Up/Down Capture oranları."""
    common = fund_returns.index.intersection(market_returns.index)
    if len(common) < 5:
        return 0.0, 0.0
    fr = fund_returns.loc[common]
    mr = market_returns.loc[common]
    up_mask = mr > 0
    down_mask = mr < 0
    up_cap = (fr[up_mask].mean() / mr[up_mask].mean() * 100) if up_mask.any() and mr[up_mask].mean() != 0 else 0.0
    down_cap = (fr[down_mask].mean() / mr[down_mask].mean() * 100) if down_mask.any() and mr[down_mask].mean() != 0 else 0.0
    return round(up_cap, 1), round(down_cap, 1)


def _batting_average(fund_returns: pd.Series, market_returns: pd.Series) -> float:
    """Benchmark'ı yendiği dönemlerin yüzdesi."""
    common = fund_returns.index.intersection(market_returns.index)
    if len(common) < 5:
        return 0.0
    fr = fund_returns.loc[common]
    mr = market_returns.loc[common]
    wins = (fr > mr).sum()
    return round(wins / len(common) * 100, 1)


def _burke_ratio(ann_ret: float, rf_annual: float, prices: pd.Series) -> float:
    """Burke Oranı = (R_p - R_f) / sqrt(Σ DD_i² / n)"""
    if len(prices) < 2:
        return 0.0
    cum = prices / prices.iloc[0]
    running_max = cum.expanding().max()
    dd = (cum - running_max) / running_max
    dd_squared_sum = (dd[dd < 0] ** 2).sum()
    n = len(dd[dd < 0])
    if n == 0:
        return 0.0
    burke_denom = np.sqrt(dd_squared_sum / n)
    return (ann_ret - rf_annual) / burke_denom if burke_denom > 0 else 0.0


def _drawdown_analysis(prices: pd.Series) -> dict:
    """Detaylı drawdown analizi: ortalama, süre, toparlanma, Ulcer Index."""
    if len(prices) < 2:
        return {"avg_dd": 0.0, "dd_duration": 0, "recovery": 0, "ulcer": 0.0}
    cum = prices / prices.iloc[0]
    running_max = cum.expanding().max()
    dd_series = (cum - running_max) / running_max
    dd_periods = []
    in_dd = False
    dd_start = 0
    dd_values = []
    for i, dd in enumerate(dd_series):
        if dd < 0 and not in_dd:
            in_dd = True
            dd_start = i
        elif dd >= 0 and in_dd:
            in_dd = False
            dd_periods.append((i - dd_start, dd_series.iloc[dd_start:i].min()))
        if dd < 0:
            dd_values.append(dd)
    if in_dd:
        dd_periods.append((len(dd_series) - dd_start, dd_series.iloc[dd_start:].min()))
    avg_dd = abs(np.mean([abs(v) for _, v in dd_periods])) * 100 if dd_periods else 0.0
    avg_duration = np.mean([d for d, _ in dd_periods]) if dd_periods else 0
    ulcer = np.sqrt(np.mean(np.array([v ** 2 for v in dd_values]))) * 100 if dd_values else 0.0
    recovery = avg_duration  # basit yaklaşım
    return {"avg_dd": round(avg_dd, 2), "dd_duration": int(avg_duration), "recovery": int(recovery), "ulcer": round(ulcer, 2)}


def _omega_ratio(daily_returns: pd.Series, threshold: float = 0.0) -> float:
    """Omega Oranı = E[max(R-threshold, 0)] / E[max(threshold-R, 0)]."""
    if len(daily_returns) < 2:
        return 0.0
    gains = daily_returns[daily_returns > threshold].mean() if (daily_returns > threshold).any() else 0.0
    losses = abs(daily_returns[daily_returns < threshold].mean()) if (daily_returns < threshold).any() else 0.0
    return round(gains / losses, 3) if losses > 0 else 0.0


def _m2_measure(ann_ret: float, vol: float, market_vol: float, rf_annual: float) -> float:
    """M² = Rf + (Sharpe * Market_Vol). Riske göre düzeltilmiş getiri."""
    sharpe = (ann_ret - rf_annual) / vol if vol > 0 else 0.0
    return round((rf_annual + sharpe * market_vol) * 100, 2)


def _active_share_approx(fund_returns: pd.Series, market_returns: pd.Series) -> float:
    """Active Share yaklaşımı: Tracking Error / (Volatility_fund + Volatility_market)."""
    common = fund_returns.index.intersection(market_returns.index)
    if len(common) < 5:
        return 0.0
    fr = fund_returns.loc[common]
    mr = market_returns.loc[common]
    te = (fr - mr).std(ddof=1) * np.sqrt(TRADING_DAYS)
    total_vol = fr.std(ddof=1) * np.sqrt(TRADING_DAYS) + mr.std(ddof=1) * np.sqrt(TRADING_DAYS)
    return round(min(te / total_vol * 100, 100), 1) if total_vol > 0 else 0.0


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
        if len(daily_returns_dates) != len(tarihler) - 1:
            daily_returns_dates.index = tarihler[-len(daily_returns_dates):]
        else:
            daily_returns_dates.index = tarihler[1:]

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
            market_common = pd.Series(dtype=float)
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

        max_dd = _max_drawdown(daily_returns_dates)
        var_95 = _value_at_risk(daily_returns_dates)
        cvar_95 = _conditional_var(daily_returns_dates)
        r2_val = _r_squared(daily_returns_dates, market_returns)

        # Yeni metrikler
        calmar = _calmar_ratio(ann_ret, max_dd)
        dd_info = _drawdown_analysis(prices)
        sterling = _sterling_ratio(ann_ret, dd_info["avg_dd"])
        up_cap, down_cap = _up_down_capture(daily_returns_dates, market_returns)
        batting = _batting_average(daily_returns_dates, market_returns)
        skew = round(float(sp_stats.skew(daily_returns_dates)), 3)
        kurt = round(float(sp_stats.kurtosis(daily_returns_dates)), 3)
        omega = _omega_ratio(daily_returns_dates)
        burke = _burke_ratio(ann_ret, rf_annual, prices)
        market_vol = _annualized_vol(market_common) if len(common_dates) >= 2 else 0.0
        m2 = _m2_measure(ann_ret, vol, market_vol, rf_annual)
        active_share = _active_share_approx(daily_returns_dates, market_returns)

        results[kod] = {
            METRIC_TOTAL_RETURN: round(total_return, 2),
            METRIC_ANNUALIZED_RETURN: round(ann_return_pct, 2),
            METRIC_VOLATILITY: round(vol * 100, 2),
            METRIC_DOWNSIDE_VOL: round(downside * 100, 2),
            METRIC_MAX_DRAWDOWN: round(max_dd, 2),
            METRIC_VAR: round(var_95, 2),
            METRIC_CVAR: round(cvar_95, 2),
            METRIC_SHARPE: round(sharpe, 3),
            METRIC_SORTINO: round(sortino, 3),
            METRIC_BETA: round(beta_val, 3),
            METRIC_TREYNOR: round(treynor, 3),
            METRIC_ALPHA: round(jensen, 3),
            METRIC_R_SQUARED: r2_val,
            METRIC_INFORMATION_RATIO: round(info_ratio, 3),
            METRIC_CALMAR: round(calmar, 3),
            METRIC_STERLING: round(sterling, 3),
            METRIC_UP_CAPTURE: up_cap,
            METRIC_DOWN_CAPTURE: down_cap,
            METRIC_BATTING_AVG: batting,
            METRIC_SKEWNESS: skew,
            METRIC_KURTOSIS: kurt,
            METRIC_AVG_DRAWDOWN: dd_info["avg_dd"],
            METRIC_DD_DURATION: dd_info["dd_duration"],
            METRIC_RECOVERY_TIME: dd_info["recovery"],
            METRIC_ULCER: dd_info["ulcer"],
            METRIC_OMEGA: omega,
            METRIC_ACTIVE_SHARE: active_share,
            METRIC_M2: m2,
            METRIC_BURKE: round(burke, 3),
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


def calculate_mix_metrics(
    mix_series: pd.Series,
    rf_daily_returns: pd.Series,
    market_prices: pd.Series,
    mix_name: str = "Mix Benchmark",
) -> dict:
    """Mix benchmark icin metrikleri hesapla.

    Parameters
    ----------
    mix_series : pd.Series
        Mix benchmark getiri serisi (yuzde getiri, %0 baslangicli).
        Index tarih olmali.
    rf_daily_returns : pd.Series
        Gunluk risksiz getiri (onluk form, orn. 0.0012 = %0.12).
    market_prices : pd.Series
        Market benchmark fiyat seviyeleri (index degerleri).
    mix_name : str
        Mix benchmark gorunen adi.

    Returns
    -------
    dict
        {metric_name: value, ...}
    """
    if mix_series is None or mix_series.empty:
        return {}

    # Yuzde getiri serisini decimal getiriyi cevir
    mix_returns_pct = mix_series.dropna()
    if len(mix_returns_pct) < 2:
        return {}

    # Toplam getiri (son deger - ilk deger, zaten %0 baslangicli)
    total_return = mix_returns_pct.iloc[-1] - mix_returns_pct.iloc[0]
    
    # % getiri -> decimal (100'e bol)
    mix_decimal = mix_returns_pct / 100.0 + 1  # 1 ekleyerek fiyat seviyesi yap
    
    # Gunluk getirileri hesapla (pct_change)
    mix_daily = mix_decimal.pct_change().dropna()
    
    if len(mix_daily) < 2:
        return {}

    # Risksiz getiri
    rf_daily = rf_daily_returns.mean() if not rf_daily_returns.empty else 0.0
    rf_annual = rf_daily * TRADING_DAYS

    # Yillandirilmis getiri ve volatilite
    ann_ret = _annual_return(mix_daily)
    vol = _annualized_vol(mix_daily)
    downside = _downside_vol(mix_daily)

    # Market getirileri ile align
    market_returns = market_prices.pct_change().dropna()
    market_aligned = market_returns.reindex(mix_daily.index).dropna()
    common_dates = mix_daily.index.intersection(market_aligned.index)
    
    if len(common_dates) < 2:
        beta_val = 0.0
        treynor = 0.0
        jensen = 0.0
        info_ratio = 0.0
    else:
        mix_common = mix_daily.loc[common_dates]
        market_common = market_aligned.loc[common_dates]
        
        cov_fm = mix_common.cov(market_common)
        var_m = market_common.var()
        beta_val = cov_fm / var_m if var_m > 0 else 0.0
        
        if beta_val != 0:
            treynor = (ann_ret - rf_annual) / beta_val
        else:
            treynor = 0.0
        
        market_ann_ret = _annual_return(market_common)
        jensen = ann_ret - (rf_annual + beta_val * (market_ann_ret - rf_annual))
        
        excess = mix_common - market_common
        te = excess.std(ddof=1) * np.sqrt(TRADING_DAYS)
        if te > 0:
            info_ratio = (excess.mean() * TRADING_DAYS) / te
        else:
            info_ratio = 0.0

    max_dd = _max_drawdown(mix_daily)
    var_95 = _value_at_risk(mix_daily)
    cvar_95 = _conditional_var(mix_daily)
    r2_val = _r_squared(mix_daily, market_returns)

    sharpe = (ann_ret - rf_annual) / vol if vol > 0 else 0.0
    sortino = (ann_ret - rf_annual) / downside if downside > 0 else 0.0
    
    ann_return_pct = ann_ret * 100

    return {
        METRIC_TOTAL_RETURN: round(total_return, 2),
        METRIC_ANNUALIZED_RETURN: round(ann_return_pct, 2),
        METRIC_VOLATILITY: round(vol * 100, 2),
        METRIC_DOWNSIDE_VOL: round(downside * 100, 2),
        METRIC_MAX_DRAWDOWN: round(max_dd, 2),
        METRIC_VAR: round(var_95, 2),
        METRIC_CVAR: round(cvar_95, 2),
        METRIC_SHARPE: round(sharpe, 3),
        METRIC_SORTINO: round(sortino, 3),
        METRIC_BETA: round(beta_val, 3),
        METRIC_TREYNOR: round(treynor, 3),
        METRIC_ALPHA: round(jensen, 3),
        METRIC_R_SQUARED: r2_val,
        METRIC_INFORMATION_RATIO: round(info_ratio, 3),
    }


def get_fund_benchmarks(fon_kodu: str, fon_kategori: str = None) -> dict:
    """Fon benchmarklarini al (KAP cache -> KAP scraping -> mapping fallback).

    Parameters
    ----------
    fon_kodu : str
        TEFAS fon kodu (orn: "MAC")
    fon_kategori : str, optional
        Fon kategorisi (orn: "Hisse Senedi Fonu")

    Returns
    -------
    dict
        {
            "benchmarks": [{"kod": str, "agirlik": float}, ...],
            "source": "kap_cache" | "kap_scraping" | "mapping",
            "message": str,
        }
    """
    from data.fetchers.tefas_benchmark_scraper import TefasBenchmarkScraper

    scraper = TefasBenchmarkScraper()
    return scraper.get_fund_benchmarks(fon_kodu, fon_kategori)


# ── Reel Getiri (Enflasyon Düzeltmeli) ────────────────────────────────

def compute_real_return(nominal_returns: pd.Series, inflation_series: pd.Series):
    """Reel getiri hesapla. nominal ve enflasyon serileri TRADING_DAYS üzerinden.

    Returns dict: nominal_yillik, enflasyon_yillik, reel_yillik, reel_kumulatif_pct.
    """
    if nominal_returns.empty or inflation_series.empty:
        return {}

    common = nominal_returns.index.intersection(inflation_series.index)
    if len(common) < 5:
        return {}

    nom = nominal_returns.loc[common]
    inf = inflation_series.loc[common]

    n = len(nom)
    nom_prod = (1 + nom).prod()
    inf_prod = (1 + inf).prod()

    nom_ann = nom_prod ** (TRADING_DAYS / n) - 1
    inf_ann = inf_prod ** (TRADING_DAYS / n) - 1
    reel_ann = (1 + nom_ann) / (1 + inf_ann) - 1

    reel_cum = (nom_prod / inf_prod - 1) * 100

    return {
        "nominal_yillik": round(nom_ann * 100, 2),
        "enflasyon_yillik": round(inf_ann * 100, 2),
        "reel_yillik": round(reel_ann * 100, 2),
        "reel_kumulatif": round(reel_cum, 2),
    }


# ── IRR / MWR ──────────────────────────────────────────────────────────

def compute_irr(cash_flows: list, tol: float = 1e-8, max_iter: int = 1000):
    """IRR (İç Verim Oranı) Newton yöntemi ile.

    cash_flows: list of (date, amount) — amount > 0 = giriş (yatırım),
                amount < 0 = çıkış (çekme/geri ödeme).
    Son öğe: (bugün, terminal_değer) — portföyün güncel değeri (negatif).
    """
    if len(cash_flows) < 2:
        return None

    dates = [cf[0] for cf in cash_flows]
    amounts = [cf[1] for cf in cash_flows]
    base_date = dates[0]

    # Gün farkları, yıl kesri
    years = [(d - base_date).days / 365.0 for d in dates]
    if any(y < 0 for y in years):
        years = [abs((base_date - d).days) / 365.0 for d in dates]

    def npv(rate):
        return sum(a / (1 + rate) ** y for a, y in zip(amounts, years))

    def npv_deriv(rate):
        return sum(-y * a / (1 + rate) ** (y + 1) for a, y in zip(amounts, years))

    rate = 0.1
    for _ in range(max_iter):
        f = npv(rate)
        f_prime = npv_deriv(rate)
        if abs(f_prime) < 1e-12:
            break
        rate_new = rate - f / f_prime
        if abs(rate_new - rate) < tol:
            return round(rate_new * 100, 2)
        rate = rate_new
    return round(rate * 100, 2) if abs(npv(rate)) < 0.01 else None


def estimate_mwr_vs_twr(fund_returns: pd.Series, initial: float = 100000,
                         monthly_add: float = 0, years: int = 1):
    """TWR ve MWR karşılaştırması.

    TWR: geometrik bağlama (nakit akışından bağımsız)
    MWR: IRR ile (nakit akışlarını dikkate alır)
    """
    if fund_returns.empty:
        return {}

    twr = (1 + fund_returns).prod() - 1

    # Nakit akışları: başlangıç (-) + aylık eklemeler (-) + son değer (+)
    n = len(fund_returns)
    total_months = min(years * 12, n // 21)
    cash_flows = [(fund_returns.index[0], -initial)]
    for m in range(1, total_months + 1):
        idx = min(m * 21, n - 1)
        cash_flows.append((fund_returns.index[idx], -monthly_add))

    terminal = initial
    cum_ret = 1.0
    for ret in fund_returns.iloc[:total_months * 21]:
        cum_ret *= (1 + ret)
    terminal_val = initial * cum_ret + monthly_add * ((cum_ret - 1) / (cum_ret ** (1 / total_months) - 1) if total_months > 0 else 0)
    cash_flows.append((fund_returns.index[min(total_months * 21, n - 1)], terminal_val))

    mwr = compute_irr(cash_flows)

    return {
        "twr": round(twr * 100, 2),
        "mwr": round(mwr, 2) if mwr is not None else None,
        "fark": round((twr * 100) - mwr, 2) if mwr is not None else None,
    }
