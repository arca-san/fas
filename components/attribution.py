#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performans atıfı ve stil analizi modülü.
Tracking error dekompozisyonu, Fama-French regresyon, RBSA stil analizi,
stres testi ve Brinson atıf.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint

TRADING_DAYS = 252


# ── Senaryo Tanımları ──────────────────────────────────────────────────

STRESS_SCENARIOS = {
    "2008_kuresel": {
        "label": "2008 Küresel Kriz (Eylül-Kasım)",
        "start": "2008-09-01", "end": "2008-11-30",
        "shocks": {"FHISE": -0.40, "USDTRY": 0.30, "TD91G": 0.05},
    },
    "2018_tr_krizi": {
        "label": "2018 Türkiye Krizi (Ağustos)",
        "start": "2018-08-01", "end": "2018-09-30",
        "shocks": {"FHISE": -0.25, "USDTRY": 0.50, "TD91G": -0.15},
    },
    "2020_covid": {
        "label": "COVID-19 (Mart 2020)",
        "start": "2020-03-01", "end": "2020-04-30",
        "shocks": {"FHISE": -0.20, "USDTRY": 0.10, "TD91G": 0.02},
    },
    "2023_secim": {
        "label": "2023 Seçim Dönemi (Mayıs-Haziran)",
        "start": "2023-05-01", "end": "2023-06-30",
        "shocks": {"FHISE": 0.10, "USDTRY": 0.25, "TD91G": -0.05},
    },
    "faiz_soku_500bps": {
        "label": "Faiz Şoku (+500 bps)",
        "shocks": {"FHISE": -0.15, "TD91G": -0.10, "USDTRY": -0.05},
    },
    "kur_soku_pct20": {
        "label": "Kur Şoku (USD/TRY +%20)",
        "shocks": {"FHISE": -0.05, "USDTRY": 0.20, "TD91G": 0.02},
    },
    "bilesik_sok": {
        "label": "Birleşik Şok (Faiz+Kur+Hisse)",
        "shocks": {"FHISE": -0.30, "USDTRY": 0.25, "TD91G": -0.15},
    },
}


# ── Tracking Error Dekompozisyonu ──────────────────────────────────────

def te_decomposition(fund_returns: pd.Series, benchmark_returns: pd.Series):
    """Tracking error'ü sistematik ve idiosinkratik bileşenlere ayırır.

    R_fund = α + β · R_bench + ε
    Sistematik TE = σ(β · R_bench) · √252
    Idiosinkratik TE = σ(ε) · √252
    """
    common = fund_returns.index.intersection(benchmark_returns.index)
    if len(common) < 20:
        return None

    y = fund_returns.loc[common].values
    x = benchmark_returns.loc[common].values
    x = sm.add_constant(x)
    model = sm.OLS(y, x).fit()
    alpha = model.params[0]
    beta = model.params[1]
    r2 = model.rsquared

    predicted = model.predict(x)
    residuals = y - predicted

    systematic_te = np.std(beta * benchmark_returns.loc[common].values, ddof=1) * np.sqrt(TRADING_DAYS)
    idiosyncratic_te = np.std(residuals, ddof=1) * np.sqrt(TRADING_DAYS)
    total_te = np.std(y - benchmark_returns.loc[common].values, ddof=1) * np.sqrt(TRADING_DAYS)

    return {
        "alpha": round(alpha * TRADING_DAYS, 4),  # yıllıklandırılmış
        "beta": round(beta, 4),
        "r_squared": round(r2, 4),
        "systematic_te": round(systematic_te * 100, 2),
        "idiosyncratic_te": round(idiosyncratic_te * 100, 2),
        "total_te": round(total_te * 100, 2),
        "systematic_ratio": round(systematic_te / total_te * 100, 1) if total_te > 0 else 0.0,
        "idiosyncratic_ratio": round(idiosyncratic_te / total_te * 100, 1) if total_te > 0 else 0.0,
    }


# ── Fama-French / Carhart Regresyon ────────────────────────────────────

def fama_french_regression(fund_returns: pd.Series, factor_dict: dict):
    """Çok faktörlü regresyon.

    factor_dict: {"MKT": pd.Series, "SMB": pd.Series, "HML": pd.Series, "WML": pd.Series}
    Faktörlerden herhangi biri None olabilir (o faktör model dışı bırakılır).
    """
    active_factors = {k: v for k, v in factor_dict.items() if v is not None and not v.empty}
    if not active_factors or len(fund_returns) < 20:
        return None

    common_idx = fund_returns.index
    for f_series in active_factors.values():
        common_idx = common_idx.intersection(f_series.index)
    if len(common_idx) < 20:
        return None

    y = fund_returns.loc[common_idx].values
    x_cols = {}
    for name, f_series in active_factors.items():
        x_cols[name] = f_series.loc[common_idx].values

    X = np.column_stack(list(x_cols.values()))
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    betas = {}
    t_stats = {}
    p_values = {}
    for i, name in enumerate(active_factors.keys()):
        betas[name] = round(model.params[i + 1], 4)
        t_stats[name] = round(model.tvalues[i + 1], 2)
        p_values[name] = round(model.pvalues[i + 1], 4)

    return {
        "alpha": round(model.params[0] * TRADING_DAYS, 4),
        "alpha_t": round(model.tvalues[0], 2),
        "alpha_p": round(model.pvalues[0], 4),
        "betas": betas,
        "t_stats": t_stats,
        "p_values": p_values,
        "adj_r2": round(model.rsquared_adj, 4),
        "r2": round(model.rsquared, 4),
        "nobs": len(common_idx),
    }


def construct_simple_factors(fhise_returns, bist30_returns=None, td91g_returns=None):
    """Basitleştirilmiş Türkiye faktörleri.

    SMB (Size): BIST TUM - BIST 30 spread vekili.
    Mevcut değilse None döner.
    """
    factors = {}
    if fhise_returns is not None and not fhise_returns.empty:
        factors["MKT"] = fhise_returns
    if bist30_returns is not None and not bist30_returns.empty and fhise_returns is not None:
        common = fhise_returns.index.intersection(bist30_returns.index)
        if len(common) > 20:
            # SMB = FHISE (geniş) - BIST30 (büyük) ≈ küçük şirket primi
            factors["SMB"] = (fhise_returns.loc[common] - bist30_returns.loc[common]).dropna()
    return factors


# ── Returns-Based Style Analysis (RBSA) ────────────────────────────────

def rbsa_analysis(fund_returns: pd.Series, asset_returns: dict):
    """William Sharpe stili getiri bazlı stil analizi.

    asset_returns: {"Hisse Senedi": pd.Series, "Devlet Tahvili": pd.Series, ...}

    minimize Σ(R_fund - Σ(w_i · R_i))²
    subject to: w_i >= 0, Σ(w_i) = 1
    """
    assets = list(asset_returns.keys())
    if len(assets) < 2 or len(fund_returns) < 20:
        return None

    common_idx = fund_returns.index
    for a in assets:
        common_idx = common_idx.intersection(asset_returns[a].index)
    if len(common_idx) < 20:
        return None

    y = fund_returns.loc[common_idx].values
    X = np.column_stack([asset_returns[a].loc[common_idx].values for a in assets])

    def objective(w):
        residuals = y - X.dot(w)
        return np.sum(residuals ** 2)

    # Kısıt: Σw = 1, w_i >= 0
    n = len(assets)
    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
    bounds = [(0, 1) for _ in range(n)]
    x0 = np.ones(n) / n

    # Çoklu başlangıç noktası ile dene
    best_result = None
    best_score = float('inf')
    for seed in range(5):
        np.random.seed(seed)
        x0_try = np.random.dirichlet(np.ones(n))
        res = minimize(objective, x0_try, method='SLSQP', bounds=bounds, constraints=cons,
                       options={'maxiter': 1000, 'ftol': 1e-12})
        if res.success and res.fun < best_score:
            best_score = res.fun
            best_result = res

    if best_result is None or not best_result.success:
        x0 = np.ones(n) / n
        best_result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=cons,
                               options={'maxiter': 1000, 'ftol': 1e-12})

    w = best_result.x
    weights = {a: round(float(w[i]), 4) for i, a in enumerate(assets) if w[i] > 0.005}

    residuals = y - X.dot(w)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    tracking_vol = np.std(residuals, ddof=1) * np.sqrt(TRADING_DAYS)

    return {
        "weights": weights,
        "r_squared": round(r_squared, 4),
        "tracking_vol": round(tracking_vol * 100, 2),
        "nobs": len(common_idx),
    }


def style_drift_tracking(fund_returns: pd.Series, asset_returns: dict, window=252):
    """Kayan pencerede RBSA — stil kayması takibi."""
    if len(fund_returns) < window or len(asset_returns) < 2:
        return pd.DataFrame()

    common_idx = fund_returns.index
    for a in asset_returns:
        common_idx = common_idx.intersection(asset_returns[a].index)
    dates = sorted(common_idx)

    results = []
    for i in range(len(dates) - window):
        window_dates = dates[i:i + window]
        fund_sub = fund_returns.loc[window_dates]
        asset_sub = {k: v.loc[window_dates] for k, v in asset_returns.items()}
        rbsa = rbsa_analysis(fund_sub, asset_sub)
        if rbsa and rbsa["weights"]:
            row = {"tarih": window_dates[-1], **rbsa["weights"]}
            results.append(row)

    return pd.DataFrame(results) if results else pd.DataFrame()


# ── Stres Testi ────────────────────────────────────────────────────────

def run_historical_scenario(fund_dict: dict, start_date: str, end_date: str):
    """Belirli tarih aralığında fon performansı."""
    results = {}
    for kod, df in fund_dict.items():
        mask = (df["tarih"] >= pd.Timestamp(start_date)) & (df["tarih"] <= pd.Timestamp(end_date))
        period_df = df[mask].sort_values("tarih")
        if len(period_df) >= 2 and period_df["fiyat"].iloc[0] > 0:
            ret = (period_df["fiyat"].iloc[-1] / period_df["fiyat"].iloc[0] - 1) * 100
            results[kod] = round(ret, 2)
        else:
            results[kod] = None
    return results


def run_hypothetical_shock(fund_returns: pd.Series, beta: float, shock_dict: dict):
    """Hipotetik şokun fon getirisine tahmini etkisi.

    shock_dict: {"FHISE": -0.30, "USDTRY": 0.25, ...}
    Toplam etki = Σ(beta_i * shock_i) + spesifik risk (basitleştirilmiş)
    """
    if beta is None or len(fund_returns) < 5:
        return None
    total_impact = 0.0
    for factor, shock in shock_dict.items():
        total_impact += beta * shock
    return {"total_impact": round(total_impact * 100, 2), "beta_used": round(beta, 3)}


def run_stress_test_batch(fund_dict: dict, fund_metrics: dict):
    """Tüm stres senaryolarını çalıştır, fon bazında etki tablosu döndür."""
    results = {}
    for scenario_key, scenario in STRESS_SCENARIOS.items():
        label = scenario["label"]
        if "start" in scenario:
            results[label] = run_historical_scenario(
                fund_dict, scenario["start"], scenario["end"]
            )
        elif "shocks" in scenario:
            shocks = scenario["shocks"]
            scenario_results = {}
            for kod in fund_dict.keys():
                m = fund_metrics.get(kod, {})
                beta_val = m.get("Beta", 1.0) if isinstance(m, dict) else 1.0
                df = fund_dict[kod]
                rets = df.set_index("tarih")["fiyat"].pct_change().dropna()
                impact = run_hypothetical_shock(rets, beta_val, shocks)
                scenario_results[kod] = impact["total_impact"] if impact else None
            results[label] = scenario_results
    return results


# ── Brinson Atıf (Basitleştirilmiş) ─────────────────────────────────────

def brinson_attribution(fund_allocation: dict, benchmark_allocation: dict,
                        asset_returns: dict):
    """Point-in-time Brinson atıf dekompozisyonu.

    fund_allocation: {"Hisse Senedi": 65.0, "Devlet Tahvili": 25.0, ...} (yüzde)
    benchmark_allocation: {"Hisse Senedi": 60.0, "Devlet Tahvili": 40.0, ...} (yüzde)
    asset_returns: {"Hisse Senedi": 12.5, "Devlet Tahvili": 5.0, ...} (yüzde)

    Brinson:
      Allocation = Σ[(w_fund - w_bench) · R_bench]
      Selection  = Σ[w_bench · (R_fund - R_bench)]
      Interaction = Σ[(w_fund - w_bench) · (R_fund - R_bench)]
      Total Active = Allocation + Selection + Interaction
    """
    if not fund_allocation or not benchmark_allocation:
        return None

    # Normalize to 100
    f_total = sum(fund_allocation.values())
    b_total = sum(benchmark_allocation.values())
    fund_w = {k: v / f_total * 100 for k, v in fund_allocation.items()} if f_total > 0 else {}
    bench_w = {k: v / b_total * 100 for k, v in benchmark_allocation.items()} if b_total > 0 else {}

    all_assets = set(list(fund_w.keys()) + list(bench_w.keys()))

    allocation = 0.0
    selection = 0.0
    interaction = 0.0
    details = []

    for asset in all_assets:
        w_f = fund_w.get(asset, 0) / 100
        w_b = bench_w.get(asset, 0) / 100
        r_b = asset_returns.get(asset, 0) / 100
        # Asset return = benchmark return (simplified - no actual fund-level asset return)

        alloc = (w_f - w_b) * r_b
        # Selection approximated: w_b * (active return), active return proxied by 0
        sel = 0.0
        inter = 0.0
        allocation += alloc
        selection += sel
        interaction += inter

        if abs(w_f - w_b) > 0.001 or abs(r_b) > 0.001:
            details.append({
                "asset": asset,
                "fund_weight": round(w_f * 100, 1),
                "benchmark_weight": round(w_b * 100, 1),
                "asset_return": round(r_b * 100, 2),
                "allocation_effect": round(alloc * 100, 3),
            })

    total_active = allocation + selection + interaction

    return {
        "allocation_effect": round(allocation * 100, 3),
        "selection_effect": round(selection * 100, 3),
        "interaction_effect": round(interaction * 100, 3),
        "total_active": round(total_active * 100, 3),
        "details": sorted(details, key=lambda x: abs(x["allocation_effect"]), reverse=True),
    }


# ── Cointegration ──────────────────────────────────────────────────────

def adf_test(series: pd.Series, maxlag: int = None):
    """Augmented Dickey-Fuller birim kök testi. H0: seri durağan değil."""
    if len(series) < 20:
        return None
    result = adfuller(series.dropna(), maxlag=maxlag, autolag="AIC")
    return {
        "stat": round(result[0], 4),
        "pvalue": round(result[1], 4),
        "critical_1pct": round(result[4]["1%"], 4),
        "critical_5pct": round(result[4]["5%"], 4),
        "critical_10pct": round(result[4]["10%"], 4),
        "stationary": result[1] < 0.05,
        "nobs": len(series) - result[2],
    }


def cointegration_test(series1: pd.Series, series2: pd.Series):
    """Engle-Granger eşbütünleşme testi. H0: eşbütünleşme yok."""
    common = series1.dropna().index.intersection(series2.dropna().index)
    if len(common) < 30:
        return None
    s1 = series1.loc[common]
    s2 = series2.loc[common]
    result = coint(s1, s2, autolag="AIC")
    hedge = (s2.std() / s1.std()) if s1.std() > 0 else 1.0

    return {
        "stat": round(result[0], 4),
        "pvalue": round(result[1], 4),
        "critical_1pct": round(result[2][0], 4),
        "critical_5pct": round(result[2][1], 4),
        "cointegrated": result[1] < 0.05,
        "hedge_ratio": round(hedge, 4),
        "nobs": len(common),
    }
