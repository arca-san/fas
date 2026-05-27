#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portföy optimizasyonu modülü.
Markowitz MVO, efficient frontier, risk parity, rebalancing, backtesting,
Monte Carlo simülasyonu ve hedef bazlı planlama.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize, Bounds, LinearConstraint


TRADING_DAYS = 252


# ── Kovaryans & Getiri ────────────────────────────────────────────────

def compute_daily_returns(fund_dict: dict) -> dict:
    """Her fon için günlük (decimal) getiri serisi döndürür."""
    returns = {}
    for kod, df in fund_dict.items():
        df = df.sort_values("tarih")
        ret = df["fiyat"].pct_change().dropna()
        if len(ret) >= 2:
            returns[kod] = ret
    return returns


def compute_covariance_matrix(fund_dict: dict):
    """Günlük getirilerden yıllıklandırılmış kovaryans matrisi ve fon kodu listesi."""
    daily_ret = compute_daily_returns(fund_dict)
    kodlar = list(daily_ret.keys())
    if len(kodlar) < 2:
        return np.array([[0.0]]), kodlar
    ret_df = pd.DataFrame({k: daily_ret[k] for k in kodlar})
    ret_df = ret_df.dropna()
    cov_daily = ret_df.cov().values
    return cov_daily * TRADING_DAYS, kodlar


def compute_expected_returns(fund_dict: dict):
    """Yıllıklandırılmış beklenen getiri vektörü (geometrik ortalama)."""
    daily_ret = compute_daily_returns(fund_dict)
    kodlar = list(daily_ret.keys())
    rets = []
    for k in kodlar:
        n = len(daily_ret[k])
        if n < 2:
            rets.append(0.0)
        else:
            ann = (1 + daily_ret[k]).prod() ** (TRADING_DAYS / n) - 1
            rets.append(ann)
    return np.array(rets), kodlar


# ── Optimizasyon ───────────────────────────────────────────────────────

def _portfolio_stats(weights, returns, cov):
    """Portföy istatistikleri: beklenen getiri, volatilite, Sharpe."""
    port_ret = np.dot(weights, returns)
    port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
    return port_ret, port_vol


def _make_constraints(n_assets):
    """Ağırlıklar toplamı = 1 ve bounds kısıtları."""
    return LinearConstraint(np.ones(n_assets), 1.0, 1.0)


def _make_bounds(n_assets, min_w=0.0, max_w=1.0):
    """Her varlık için [min_w, max_w] bounds dizisi."""
    return Bounds([min_w] * n_assets, [max_w] * n_assets)


def min_variance_portfolio(cov, min_w=0.0, max_w=1.0):
    """Minimum varyans portföy ağırlıkları."""
    n = len(cov)
    if n < 2:
        return np.array([1.0]) if n == 1 else np.array([])

    def objective(w):
        return np.sqrt(np.dot(w.T, np.dot(cov, w)))

    bounds = _make_bounds(n, min_w, max_w)
    cons = _make_constraints(n)
    x0 = np.ones(n) / n
    res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 1000, "ftol": 1e-12})
    return res.x if res.success else x0


def max_sharpe_portfolio(returns, cov, rf_rate=0.0, min_w=0.0, max_w=1.0):
    """Maksimum Sharpe oranlı portföy ağırlıkları."""
    n = len(cov)
    if n < 2:
        return np.array([1.0]) if n == 1 else np.array([])

    def neg_sharpe(w):
        port_ret, port_vol = _portfolio_stats(w, returns, cov)
        return -(port_ret - rf_rate) / port_vol if port_vol > 0 else 1e9

    bounds = _make_bounds(n, min_w, max_w)
    cons = _make_constraints(n)
    x0 = np.ones(n) / n
    res = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 1000, "ftol": 1e-12})
    return res.x if res.success else x0


def min_variance_for_return(returns, cov, target_return, min_w=0.0, max_w=1.0):
    """Belirli bir hedef getiri için minimum varyans portföyü."""
    n = len(cov)
    if n < 2:
        return np.array([1.0]) if n == 1 else np.array([])

    def objective(w):
        return np.sqrt(np.dot(w.T, np.dot(cov, w)))

    bounds = _make_bounds(n, min_w, max_w)
    cons = [
        _make_constraints(n),
        LinearConstraint(returns, target_return, target_return),
    ]
    x0 = np.ones(n) / n
    res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 1000, "ftol": 1e-12})
    return res.x if res.success else x0


def efficient_frontier_points(returns, cov, rf_rate=0.0, n_points=50, min_w=0.0, max_w=1.0):
    """Efficient frontier üzerinde n_points adet (vol, ret, weights) noktası."""
    n = len(cov)
    if n < 2:
        return []

    # Min var portföyü (en sol uç)
    w_min = min_variance_portfolio(cov, min_w, max_w)
    r_min, vol_min = _portfolio_stats(w_min, returns, cov)

    # Max getiri portföyü (en sağ üst uç)
    idx_max = np.argmax(returns)
    w_max_ret = np.zeros(n)
    w_max_ret[idx_max] = min(max_w, 1.0)
    if w_max_ret[idx_max] < 1.0:
        remaining = 1.0 - w_max_ret[idx_max]
        others = [i for i in range(n) if i != idx_max]
        w_max_ret[others] = remaining / len(others)
    r_max, _ = _portfolio_stats(w_max_ret, returns, cov)

    # n_points hedef getiri için min varyans portföyleri
    target_returns = np.linspace(r_min, r_max, n_points)
    points = []
    for tr in target_returns:
        w = min_variance_for_return(returns, cov, tr, min_w, max_w)
        pr, pv = _portfolio_stats(w, returns, cov)
        # Sharpe filtresi: sadece aynı getiride en düşük volatiliteli noktalar
        if (points and pr <= points[-1][1] + 1e-6) or not points:
            points.append((pv, pr, w))
        elif pr > points[-1][1]:
            points.append((pv, pr, w))
    return points


def risk_parity_portfolio(cov, max_iter=100, tol=1e-8, min_w=0.0, max_w=1.0):
    """Eşit risk katkılı (ERC) portföy — Newton yöntemi."""
    n = len(cov)
    if n < 2:
        return np.array([1.0]) if n == 1 else np.array([])

    # Başlangıç: equal weight
    w = np.ones(n) / n

    # Risk parity: minimize sum of squared differences of risk contributions
    def risk_budget_objective(w):
        sigma = np.sqrt(np.dot(w.T, np.dot(cov, w)))
        if sigma < 1e-12:
            return 1e12
        mrc = np.dot(cov, w) / sigma  # marginal risk contributions
        rc = w * mrc                    # risk contributions
        target_rc = sigma / n           # equal target
        return np.sum((rc - target_rc) ** 2)

    bounds = _make_bounds(n, min_w, max_w)
    cons = _make_constraints(n)
    x0 = w.copy()
    res = minimize(risk_budget_objective, x0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": max_iter, "ftol": tol})
    if res.success:
        return res.x
    return x0


# ── Rebalancing ────────────────────────────────────────────────────────

def simulate_rebalancing(fund_dict, weights, rebalance_freq="monthly",
                         threshold=0.05, cost_bps=10.0):
    """Portföy değeri + drift simülasyonu. Belirli frekansta/eşikte rebalans.

    Returns DataFrame: tarih, portfoy_deger, drift_pct, islem_maliyeti.
    """
    kodlar = list(fund_dict.keys())
    prices = {}
    for k in kodlar:
        df = fund_dict[k].set_index("tarih")["fiyat"]
        prices[k] = df

    common_idx = prices[kodlar[0]].index
    for k in kodlar[1:]:
        common_idx = common_idx.intersection(prices[k].index)
    common_idx = common_idx.sort_values()

    if len(common_idx) < 2:
        return pd.DataFrame()

    weights = np.array([weights.get(k, 0) for k in kodlar])
    weights = weights / weights.sum()

    target_w = dict(zip(kodlar, weights))
    portfoy_val = []
    drift_vals = []
    cost_vals = []
    current_w = weights.copy()
    port_val = 1.0
    last_rebal = common_idx[0]

    for i, dt in enumerate(common_idx):
        if i == 0:
            portfoy_val.append(1.0)
            drift_vals.append(0.0)
            cost_vals.append(0.0)
            continue

        # Her varlığın getirisi
        asset_vals = []
        for j, k in enumerate(kodlar):
            prev_p = prices[k].loc[common_idx[i - 1]]
            curr_p = prices[k].loc[dt]
            ret = (curr_p / prev_p) - 1 if prev_p > 0 else 0
            asset_vals.append(current_w[j] * (1 + ret))

        port_val = sum(asset_vals)
        current_w = np.array(asset_vals) / port_val if port_val > 0 else current_w

        # Rebalans kontrolü
        drift = max(abs(current_w[j] - target_w[k]) for j, k in enumerate(kodlar))
        cost = 0.0
        if should_rebalance(dt, last_rebal, rebalance_freq, drift, threshold):
            turnover = sum(abs(current_w[j] - target_w[k]) for j, k in enumerate(kodlar))
            cost = turnover * cost_bps / 10000.0
            port_val -= cost
            current_w = weights.copy()
            last_rebal = dt

        portfoy_val.append(port_val)
        drift_vals.append(drift)
        cost_vals.append(cost)

    return pd.DataFrame({
        "tarih": common_idx,
        "portfoy_deger": portfoy_val,
        "drift_pct": drift_vals,
        "islem_maliyeti": cost_vals,
    })


def should_rebalance(dt, last_rebal, freq, drift, threshold):
    """Rebalans yapılmalı mı?"""
    if threshold and drift > threshold:
        return True
    if freq == "monthly":
        return (dt.year != last_rebal.year or dt.month != last_rebal.month)
    elif freq == "quarterly":
        return (dt.year != last_rebal.year or
                (dt.month - 1) // 3 != (last_rebal.month - 1) // 3)
    elif freq == "yearly":
        return dt.year != last_rebal.year
    return dt != last_rebal


# ── Backtesting ─────────────────────────────────────────────────────────

def walk_forward_backtest(fund_dict, returns, cov, window_years=1,
                          step_months=3, method="sharpe", rf_rate=0.0,
                          min_w=0.0, max_w=1.0):
    """Walk-forward backtest. Her dönem optimize et, sonraki dönem performansını ölç."""
    kodlar = list(fund_dict.keys())
    if len(kodlar) < 2:
        return pd.DataFrame()

    daily_ret = compute_daily_returns(fund_dict)
    all_dates = sorted(daily_ret[kodlar[0]].index)
    if len(all_dates) < window_years * TRADING_DAYS + 60:
        return pd.DataFrame()

    window = window_years * TRADING_DAYS
    step = step_months * 21

    results = []
    i = 0
    while i + window < len(all_dates):
        train_end = all_dates[i + window - 1]
        test_start = all_dates[i + window]
        test_end_idx = min(i + window + step, len(all_dates) - 1)
        test_end = all_dates[test_end_idx]

        # Eğitim dönemi: kovaryans + getiri
        train_fund = {}
        for k in kodlar:
            mask = (fund_dict[k]["tarih"] >= all_dates[i]) & (fund_dict[k]["tarih"] <= train_end)
            train_fund[k] = fund_dict[k][mask]
        c, kd = compute_covariance_matrix(train_fund)
        r, _ = compute_expected_returns(train_fund)
        if len(c) < 2 or np.isnan(c).any():
            i += step
            continue

        # Optimize et
        if method == "sharpe":
            w = max_sharpe_portfolio(r, c, rf_rate, min_w, max_w)
        elif method == "minvar":
            w = min_variance_portfolio(c, min_w, max_w)
        else:
            w = np.ones(len(kd)) / len(kd)

        # Test dönemi getirisi (eşit ağırlıklı vs optimize)
        test_ret_opt = 0.0
        test_ret_eq = 0.0
        eq_w = 1.0 / len(kd)
        for j, k in enumerate(kd):
            mask = (fund_dict[k]["tarih"] >= test_start) & (fund_dict[k]["tarih"] <= test_end)
            test_prices = fund_dict[k].loc[mask, "fiyat"]
            if len(test_prices) >= 2 and test_prices.iloc[0] > 0:
                f_ret = test_prices.iloc[-1] / test_prices.iloc[0] - 1
                test_ret_opt += w[j] * f_ret
                test_ret_eq += eq_w * f_ret

        results.append({
            "egitim_sonu": train_end,
            "test_baslangic": test_start,
            "test_sonu": test_end,
            "optimize_getiri": test_ret_opt,
            "equal_getiri": test_ret_eq,
            "weights": dict(zip(kd, w.round(3))),
        })
        i += step

    return pd.DataFrame(results)


# ── Hedef Bazlı Planlama ───────────────────────────────────────────────

def goal_based_projection(returns, cov, weights, initial=100000.0,
                          monthly_add=1000.0, years=10, inflation=0.20,
                          rf_rate=0.0):
    """Hedef bazlı birikim projeksiyonu.

    Returns dict: nominal_son, reel_son, aylik_gerekli (hedef için),
                  yillik_projeksiyon list.
    """
    port_ret, port_vol = _portfolio_stats(weights, returns, cov)
    aylik_ret = (1 + port_ret) ** (1 / 12) - 1
    aylik_vol = port_vol / np.sqrt(12)
    aylik_enflasyon = (1 + inflation) ** (1 / 12) - 1

    projeksiyon = []
    nominal = initial
    for ay in range(years * 12):
        nominal = nominal * (1 + aylik_ret) + monthly_add
        reel = nominal / (1 + inflation) ** ((ay + 1) / 12)
        if (ay + 1) % 12 == 0:
            projeksiyon.append({
                "yil": (ay + 1) // 12,
                "nominal": round(nominal, 2),
                "reel": round(reel, 2),
            })

    nominal_son = nominal
    reel_son = nominal_son / (1 + inflation) ** years

    # Hedef için gerekli aylık ek ödeme (basit yaklaşım)
    aylik_gerekli = monthly_add  # placeholder

    return {
        "nominal_son": round(nominal_son, 2),
        "reel_son": round(reel_son, 2),
        "aylik_gerekli": round(aylik_gerekli, 2),
        "projeksiyon": projeksiyon,
    }


# ── Monte Carlo ─────────────────────────────────────────────────────────

def monte_carlo_simulation(returns, cov, weights, initial=100000.0,
                           horizon_days=252, n_sim=5000):
    """Monte Carlo simülasyonu: GBM ile fiyat yolu üretimi.

    Returns: (sim_paths: np.array shape(n_sim, horizon_days+1),
              terminal_values: np.array shape(n_sim,))
    """
    port_ret, port_vol = _portfolio_stats(weights, returns, cov)
    dt = 1 / TRADING_DAYS
    mu = port_ret
    sigma = port_vol

    np.random.seed(42)
    Z = np.random.normal(0, 1, (n_sim, horizon_days))
    log_returns = (mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * Z
    prices = initial * np.exp(np.cumsum(log_returns, axis=1))
    paths = np.hstack([np.full((n_sim, 1), initial), prices])
    terminal = paths[:, -1]
    return paths, terminal


def monte_carlo_stats(terminal_values, confidence=0.95, initial=100000.0):
    """Monte Carlo terminal değer istatistikleri."""
    mean_val = np.mean(terminal_values)
    median_val = np.median(terminal_values)
    std_val = np.std(terminal_values)
    var_ci = np.percentile(terminal_values, (1 - confidence) * 100)
    cvar_ci = terminal_values[terminal_values <= var_ci].mean()
    prob_positive = np.mean(terminal_values > initial)
    prob_double = np.mean(terminal_values >= 2 * initial)

    return {
        "ortalama": round(mean_val, 2),
        "medyan": round(median_val, 2),
        "std": round(std_val, 2),
        f"VaR ({int(confidence*100)}%)": round(abs(var_ci - initial), 2),
        f"CVaR ({int(confidence*100)}%)": round(abs(cvar_ci - initial), 2),
        "Pozitif Getiri Olasiligi": round(prob_positive * 100, 1),
        "2x Getiri Olasiligi": round(prob_double * 100, 1),
    }
