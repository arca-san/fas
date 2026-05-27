#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotly grafik fabrikasi — fiyat ve getiri grafikleri.
"""

import plotly.graph_objects as go
import pandas as pd

from config.constants import DEFAULT_COLOR_PALETTE, METRIC_SHARPE, METRIC_VOLATILITY


def create_price_chart(
    fund_dict: dict,
    benchmark_dict: dict = None,
    title: str = "Fon Getiri Grafiği",
    metrics: dict = None,
    mix_benchmark: dict = None,
    correlations: dict = None,
    theme: str = "light",
) -> go.Figure:
    """Fon ve benchmark(lar) kumulatif getiri grafigi.

    Tum fonlar ayni grafikte cizilir (düz cizgi, ayri renk).
    Tum benchmarklar ayni grafikte cizilir (kesikli cizgi, gri).
    Mix benchmark varsa kalın siyah çizgi ile gösterilir.

    Parametreler
    ------------
    fund_dict : dict
        {"FON_KODU": df, ...} seklinde fon verileri.
        df'lerde "tarih" ve "fiyat" sutunlari olmali.
    benchmark_dict : dict, optional
        {"BENCHMARK_KODU": pd.Series, ...} seklinde benchmark serileri.
        Seriler yuzde getiri (%0 baslangicli) olmali.
    mix_benchmark : dict, optional
        {"name": str, "series": pd.Series} seklinde mix benchmark.
        name: "Mix (FHISE %50 + TD91G %50)" gibi.
        series: yuzde getiri serisi.
    """
    if not fund_dict:
        return go.Figure()

    # Tum fonlarin ortak tarih araligini bul (inner join)
    date_sets = []
    for kod, df in fund_dict.items():
        if df.empty or "tarih" not in df.columns or "fiyat" not in df.columns:
            continue
        mask = df["tarih"].notna()
        date_sets.append(set(df.loc[mask, "tarih"]))

    if not date_sets:
        return go.Figure()

    ortak_tarihler = set.intersection(*date_sets) if len(date_sets) > 1 else date_sets[0]
    if not ortak_tarihler:
        return go.Figure()

    ortak_tarihler = sorted(ortak_tarihler)

    # Her fon icin ayri trace, dongusel renk
    fig = go.Figure()
    palet = DEFAULT_COLOR_PALETTE

    for i, (kod, df) in enumerate(fund_dict.items()):
        # Sadece ortak tarihleri tut
        df_ortak = df[df["tarih"].isin(ortak_tarihler)].sort_values("tarih")
        if df_ortak.empty:
            continue

        # Sifir olmayan fiyatla başla
        mask = df_ortak["fiyat"].gt(0)
        if not mask.any():
            continue
        df_ortak = df_ortak.loc[mask.idxmax():].reset_index(drop=True)
        if df_ortak.empty:
            continue

        bas_fiyat = df_ortak["fiyat"].iloc[0]
        cum_return = (df_ortak["fiyat"] / bas_fiyat - 1.0) * 100.0
        color = palet[i % len(palet)]

        m = metrics.get(kod, {}) if metrics else {}
        sharpe_str = f"{m.get(METRIC_SHARPE, 0):.3f}" if m else "N/A"
        vol_str = f"{m.get(METRIC_VOLATILITY, 0):.2f}" if m else "N/A"
        corr_val = correlations.get(kod) if correlations else None
        corr_str = f"{corr_val:.4f}" if corr_val is not None else "N/A"

        fig.add_trace(
            go.Scatter(
                x=df_ortak["tarih"],
                y=cum_return,
                mode="lines",
                name=kod,
                line=dict(color=color, width=2),
                hovertext=f"Sharpe: {sharpe_str}<br>Volatilite: {vol_str}%<br>BM Korelasyon: {corr_str}",
                hoverinfo="x+y+text+name",
            )
        )

# Benchmark(lar): fonlarla aynı tarih aralığında çiz
    import logging
    logger = logging.getLogger(__name__)
    
    bm_colors = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3"]
    
    if benchmark_dict:
        logger.debug("=== CHARTS BENCHMARK DICT: %s ===", list(benchmark_dict.keys()))
        for i, (bm_kod, bm_series) in enumerate(benchmark_dict.items()):
            logger.debug("BM %s: len=%s, ilk degerler=%s", bm_kod, len(bm_series), bm_series[:5].tolist())
            
            if bm_series is None or bm_series.empty:
                continue
            
            # Forward fill ile NaN'ları doldur
            bm_filled = bm_series.ffill()
            if bm_filled.dropna().empty:
                logger.debug("BM %s: ffill sonrasi bos", bm_kod)
                continue
            
            # İlk geçerli değer (her zaman 0 olmalı, çünkü normalize ettik)
            first_val = 1.0  # Normalize ettiğimiz için her zaman 1.0
            
            # Tarihleri al
            tarihler = list(ortak_tarihler)
            bm_values = bm_filled.reindex(pd.DatetimeIndex(tarihler)).ffill().values
            
            logger.debug("BM reindex: len=%s, ilk=%s", len(bm_values), bm_values[:5])
            
            fig.add_trace(
                go.Scatter(
                    x=tarihler,
                    y=bm_values,
                    mode="lines",
                    name=bm_kod,
                    line=dict(color=bm_colors[i % len(bm_colors)], width=2, dash="dash"),
                    hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra></extra>",
                )
            )

    # Mix benchmark: kalın siyah (gece modunda beyaz) çizgi
    if mix_benchmark and mix_benchmark.get("series") is not None:
        mix_series = mix_benchmark["series"]
        mix_name = mix_benchmark.get("name", "Mix Benchmark")
        
        if not mix_series.empty:
            mix_filled = mix_series.ffill()
            tarihler = list(ortak_tarihler)
            mix_values = mix_filled.reindex(pd.DatetimeIndex(tarihler)).ffill().values
            
            mix_color = "#ffffff" if theme == "dark" else "#000000"
            fig.add_trace(
                go.Scatter(
                    x=tarihler,
                    y=mix_values,
                    mode="lines",
                    name=mix_name,
                    line=dict(color=mix_color, width=3, dash="dot"),
                    hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra></extra>",
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title="Tarih",
        yaxis_title="Getiri (%)",
        hovermode="x unified",
        template="plotly_dark" if theme == "dark" else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig


def create_risk_return_scatter(
    metrics: dict,
    title: str = "Risk-Getiri Saçılım Grafiği",
    theme: str = "light",
) -> go.Figure:
    """Risk (volatilite) ve getiri ekseninde fon konumlarini goster.

    Parameters
    ----------
    metrics : dict
        {"FON_KODU": {metric_name: value, ...}, ...}
        Her metrik dict'inde METRIC_VOLATILITY ve METRIC_ANNUALIZED_RETURN olmali.
    """
    from config.constants import METRIC_VOLATILITY, METRIC_ANNUALIZED_RETURN

    fig = go.Figure()

    text_positions = ["top center", "bottom center", "middle right", "middle left", "top left", "top right", "bottom left", "bottom right"]
    is_dark = theme == "dark"
    text_color = "#ffffff" if is_dark else "#212529"
    border_color = "#ffffff" if is_dark else "#212529"

    for idx, (kod, m) in enumerate(metrics.items()):
        risk = m.get(METRIC_VOLATILITY, None)
        getiri = m.get(METRIC_ANNUALIZED_RETURN, None)
        if risk is None or getiri is None:
            continue
        
        pos = text_positions[idx % len(text_positions)]
        
        fig.add_trace(
            go.Scatter(
                x=[risk],
                y=[getiri],
                mode="markers+text",
                name=kod,
                text=[kod],
                textposition=pos,
                textfont=dict(size=10, family="sans-serif", color=text_color),
                marker=dict(
                    size=14,
                    line=dict(width=1.5, color=border_color),
                    opacity=0.85
                ),
                hovertemplate=f"<b>{kod}</b><br>Risk (Volatilite): {risk:.2f}%<br>Getiri (Yıllık): {getiri:.2f}%<extra></extra>",
            )
        )

    # Referans cizgileri
    fig.update_layout(
        title=title,
        xaxis_title="Risk (Volatilite, %)",
        yaxis_title="Getiri (Yıllık, %)",
        template="plotly_dark" if is_dark else "plotly",
        hovermode="closest",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig


def create_portfolio_distribution_chart(
    distribution: dict,
    title: str = "Fon Portföy Dağılımı",
    theme: str = "light",
) -> go.Figure:
    """Fonun varlık sınıflarına göre dağılımını donut chart ile gösterir."""
    if not distribution:
        fig = go.Figure()
        fig.update_layout(title=title, template="plotly_dark" if theme == "dark" else "plotly")
        fig.add_annotation(text="Veri bulunamadı", showarrow=False, font=dict(size=14))
        return fig

    labels = list(distribution.keys())
    values = list(distribution.values())
    is_dark = theme == "dark"

    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo="label+percent",
            textfont=dict(size=11, color="#ffffff" if is_dark else "#212529"),
            marker=dict(line=dict(color="#1a1a1a" if is_dark else "#ffffff", width=1)),
            hovertemplate="%{label}<br>%{percent:.1%}<br>%{value:.1f}%<extra></extra>",
        )
    ])
    fig.update_layout(
        title=title,
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="v", x=1.05, y=0.5),
    )
    return fig


def create_rolling_sharpe_chart(
    fund_dict: dict,
    rf_daily: pd.Series = None,
    window: int = 63,
    theme: str = "light",
) -> go.Figure:
    """Kayan pencere Sharpe oranı çizgi grafiği (default 63 iş günü ≈ 3 ay)."""
    if not fund_dict:
        return go.Figure()

    is_dark = theme == "dark"
    fig = go.Figure()
    palet = DEFAULT_COLOR_PALETTE

    for i, (kod, df) in enumerate(fund_dict.items()):
        df = df.sort_values("tarih")
        returns = df["fiyat"].pct_change().dropna()
        if len(returns) < window:
            continue

        rf = rf_daily.reindex(returns.index).fillna(0.0) if rf_daily is not None else pd.Series(0, index=returns.index)
        excess = returns - rf

        rolling_sharpe = (excess.rolling(window).mean() / excess.rolling(window).std() * (252 ** 0.5)).dropna()

        if rolling_sharpe.empty:
            continue

        fig.add_trace(go.Scatter(
            x=rolling_sharpe.index,
            y=rolling_sharpe.values,
            mode="lines",
            name=f"{kod} (rolling Sharpe)",
            line=dict(color=palet[i % len(palet)], width=1.5),
            hovertemplate="%{x|%Y-%m-%d}<br>Sharpe: %{y:.3f}<extra></extra>",
        ))

    fig.update_layout(
        title=f"Rolling Sharpe Oranı ({window} Gün)",
        xaxis_title="Tarih",
        yaxis_title="Sharpe Oranı (Yıllık)",
        hovermode="x unified",
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_correlation_heatmap(
    fund_dict: dict,
    title: str = "Fon Korelasyon Matrisi",
    theme: str = "light",
) -> go.Figure:
    """Fonlar arası günlük getiri korelasyon matrisini heatmap ile gösterir."""
    if not fund_dict or len(fund_dict) < 2:
        fig = go.Figure()
        fig.update_layout(title=title)
        fig.add_annotation(text="En az 2 fon seçilmeli", showarrow=False, font=dict(size=14))
        return fig

    is_dark = theme == "dark"
    daily_returns = {}
    for kod, df in fund_dict.items():
        df = df.sort_values("tarih")
        ret = df["fiyat"].pct_change().dropna()
        if not ret.empty:
            daily_returns[kod] = ret

    if len(daily_returns) < 2:
        fig = go.Figure()
        fig.update_layout(title=title)
        fig.add_annotation(text="Yetersiz veri", showarrow=False)
        return fig

    kodlar = list(daily_returns.keys())
    ortak_idx = daily_returns[kodlar[0]].index
    for k in kodlar[1:]:
        ortak_idx = ortak_idx.intersection(daily_returns[k].index)

    ret_df = pd.DataFrame({k: daily_returns[k].reindex(ortak_idx) for k in kodlar})
    corr = ret_df.corr().round(3)
    labels = kodlar

    colorscale = [[0, '#d62728'], [0.5, '#ffffff' if not is_dark else '#1a1a1a'], [1, '#2ca02c']]

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=labels,
        y=labels,
        colorscale=colorscale,
        zmin=-1, zmax=1,
        text=corr.values,
        texttemplate="%{text:.2f}",
        textfont={"size": 11, "color": "#ffffff" if is_dark else "#212529"},
        hovertemplate="%{x} vs %{y}<br>Korelasyon: %{z:.3f}<extra></extra>",
        colorbar=dict(title="r", titleside="right",
                       tickfont=dict(color="#ffffff" if is_dark else "#212529"),
                       titlefont=dict(color="#ffffff" if is_dark else "#212529")),
    ))
    fig.update_layout(
        title=title,
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
    )
    return fig


def create_efficient_frontier_chart(
    frontier_points: list,
    fund_metrics: dict,
    optimal_weights: dict = None,
    optimal_label: str = "Optimal Portföy",
    rf_rate: float = 0.0,
    theme: str = "light",
) -> go.Figure:
    """Efficient frontier + CML + bireysel fon scatter plotu.

    Parameters
    ----------
    frontier_points : list of (vol, ret, weights)
    fund_metrics : {"FON_KODU": {"Volatilite (Yıllık)": 12.3, "Yıllıklandırılmış Getiri": 45.2}, ...}
    optimal_weights : {kod: agirlik} veya None
    """
    is_dark = theme == "dark"
    text_color = "#ffffff" if is_dark else "#212529"
    fig = go.Figure()

    # Efficient frontier eğrisi
    if frontier_points:
        vols = [p[0] * 100 for p in frontier_points]
        rets = [p[1] * 100 for p in frontier_points]
        fig.add_trace(go.Scatter(
            x=vols, y=rets, mode="lines",
            name="Efficient Frontier",
            line=dict(color="#1abc9c" if not is_dark else "#b666d2", width=2),
            hovertemplate="Vol: %{x:.2f}%<br>Ret: %{y:.2f}%<extra></extra>",
        ))

    # Bireysel fonlar
    palet = DEFAULT_COLOR_PALETTE
    idx = 0
    for kod, m in fund_metrics.items():
        vol = m.get("Volatilite (Yıllık)", 0)
        ret = m.get("Yıllıklandırılmış Getiri", 0)
        if vol <= 0:
            continue
        fig.add_trace(go.Scatter(
            x=[vol], y=[ret], mode="markers+text",
            name=kod, text=[kod], textposition="top center",
            textfont=dict(size=10, color=text_color),
            marker=dict(size=10, color=palet[idx % len(palet)],
                       line=dict(width=1, color=text_color)),
            hovertemplate=f"<b>{kod}</b><br>Vol: {vol:.2f}%<br>Ret: {ret:.2f}%<extra></extra>",
        ))
        idx += 1

    # Optimal portföy noktası (max Sharpe veya seçili)
    if optimal_weights:
        opt_ret = 0
        opt_vol = 0
        for kod, w in optimal_weights.items():
            if kod in fund_metrics and w > 0:
                m = fund_metrics[kod]
                opt_ret += w * m.get("Yıllıklandırılmış Getiri", 0)
        if frontier_points and len(frontier_points) > 0:
            # En yakın frontier noktasını bul
            best = min(frontier_points, key=lambda p: abs(p[1] * 100 - opt_ret))
            opt_vol = best[0] * 100
            opt_ret = best[1] * 100
        fig.add_trace(go.Scatter(
            x=[opt_vol], y=[opt_ret], mode="markers",
            name=optimal_label,
            marker=dict(size=16, symbol="star", color="#f39c12",
                       line=dict(width=2, color="#e67e22")),
            hovertemplate=f"<b>{optimal_label}</b><br>Vol: {opt_vol:.2f}%<br>Ret: {opt_ret:.2f}%<extra></extra>",
        ))
        # CML: rf → optimal
        if rf_rate > 0:
            fig.add_trace(go.Scatter(
                x=[0, opt_vol], y=[rf_rate * 100, opt_ret], mode="lines",
                name="CML",
                line=dict(color="#e74c3c" if not is_dark else "#e74c3c", width=1.5, dash="dot"),
                hovertemplate="CML<extra></extra>",
            ))

    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Risk (Volatilite, %)",
        yaxis_title="Getiri (Yıllık, %)",
        template="plotly_dark" if is_dark else "plotly",
        hovermode="closest",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_monte_carlo_chart(
    paths: np.ndarray,
    initial: float = 100000.0,
    theme: str = "light",
) -> go.Figure:
    """Monte Carlo simülasyonu görselleştirme: bireysel izler + medyan + bant."""
    is_dark = theme == "dark"
    n_sim = min(paths.shape[0], 200)

    fig = go.Figure()

    # Bireysel simülasyonlar (ince gri)
    for i in range(n_sim):
        fig.add_trace(go.Scatter(
            y=paths[i], mode="lines",
            line=dict(color="rgba(128,128,128,0.1)" if not is_dark else "rgba(200,200,200,0.06)", width=0.5),
            showlegend=False,
            hovertemplate="Sim %{i}<extra></extra>",
        ))

    # Medyan
    median = np.median(paths, axis=0)
    fig.add_trace(go.Scatter(
        y=median, mode="lines",
        name="Medyan",
        line=dict(color="#1abc9c" if not is_dark else "#b666d2", width=2.5),
        hovertemplate="Medyan: %{y:,.0f}<extra></extra>",
    ))

    # %5 - %95 bant
    p5 = np.percentile(paths, 5, axis=0)
    p95 = np.percentile(paths, 95, axis=0)
    x_fill = list(range(len(p5))) + list(range(len(p95)))[::-1]
    y_fill = list(p5) + list(p95)[::-1]
    fig.add_trace(go.Scatter(
        x=x_fill, y=y_fill, fill="toself",
        fillcolor="rgba(26,188,156,0.15)" if not is_dark else "rgba(182,102,210,0.15)",
        line=dict(width=0), name="%5-%95 Bant",
        hoverinfo="skip",
    ))

    # Başlangıç çizgisi
    fig.add_hline(y=initial, line_dash="dash", line_color="gray",
                  annotation_text="Başlangıç")

    fig.update_layout(
        title="Monte Carlo Projeksiyonu",
        xaxis_title="Gün",
        yaxis_title="Portföy Değeri (TL)",
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_backtest_chart(
    backtest_df: pd.DataFrame,
    theme: str = "light",
) -> go.Figure:
    """Walk-forward backtest: optimize vs equal-weight karşılaştırma."""
    if backtest_df.empty:
        return go.Figure()

    is_dark = theme == "dark"

    opt_cum = (1 + backtest_df["optimize_getiri"]).cumprod()
    eq_cum = (1 + backtest_df["equal_getiri"]).cumprod()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=backtest_df["test_sonu"], y=opt_cum, mode="lines+markers",
        name="Optimize Portföy",
        line=dict(color="#1abc9c" if not is_dark else "#b666d2", width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:.3f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=backtest_df["test_sonu"], y=eq_cum, mode="lines+markers",
        name="Eşit Ağırlıklı",
        line=dict(color="#95a5a6", width=1.5, dash="dash"),
        hovertemplate="%{x|%Y-%m-%d}<br>%{y:.3f}<extra></extra>",
    ))

    fig.update_layout(
        title="Walk-Forward Backtest",
        xaxis_title="Tarih",
        yaxis_title="Kümülatif Getiri (x)",
        template="plotly_dark" if is_dark else "plotly",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_rebalancing_chart(
    rebal_df: pd.DataFrame,
    theme: str = "light",
) -> go.Figure:
    """Rebalancing simülasyonu: portföy değeri ve drift çift eksenli."""
    if rebal_df.empty:
        return go.Figure()
    is_dark = theme == "dark"
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=rebal_df["tarih"], y=rebal_df["portfoy_deger"], mode="lines",
        name="Portföy Değeri",
        line=dict(color="#1abc9c" if not is_dark else "#b666d2", width=2),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=rebal_df["tarih"], y=rebal_df["drift_pct"] * 100, mode="lines",
        name="Drift (%)", line=dict(color="#e74c3c", width=1, dash="dot"),
    ), secondary_y=True)
    fig.update_layout(
        title="Rebalancing — Portföy Değeri & Drift",
        template="plotly_dark" if is_dark else "plotly",
        hovermode="x unified", margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Değer (x)", secondary_y=False)
    fig.update_yaxes(title_text="Drift (%)", secondary_y=True)
    return fig


def create_goal_projection_chart(
    projection: list,
    nominal_son: float,
    reel_son: float,
    theme: str = "light",
) -> go.Figure:
    """Hedef bazlı birikim projeksiyonu."""
    if not projection:
        return go.Figure()
    is_dark = theme == "dark"
    years = [p["yil"] for p in projection]
    nominal = [p["nominal"] for p in projection]
    reel = [p["reel"] for p in projection]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=nominal, name="Nominal Değer",
        marker_color="#1abc9c" if not is_dark else "#b666d2",
    ))
    fig.add_trace(go.Scatter(
        x=years, y=reel, mode="lines+markers",
        name="Reel Değer (Enflasyon Düzeltmeli)",
        line=dict(color="#e74c3c", width=2, dash="dot"),
    ))
    fig.update_layout(
        title=f"Birikim Projeksiyonu — Nominal: {nominal_son:,.0f} TL | Reel: {reel_son:,.0f} TL",
        xaxis_title="Yıl", yaxis_title="Değer (TL)",
        template="plotly_dark" if is_dark else "plotly",
        hovermode="x unified", margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_style_drift_chart(
    drift_df: pd.DataFrame,
    theme: str = "light",
) -> go.Figure:
    """RBSA stil kayması — stacked area chart."""
    if drift_df.empty or len(drift_df.columns) < 2:
        return go.Figure()
    is_dark = theme == "dark"
    fig = go.Figure()
    cols = [c for c in drift_df.columns if c != "tarih"]
    palet = DEFAULT_COLOR_PALETTE
    for i, col in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=drift_df["tarih"], y=drift_df[col], mode="lines",
            name=col, stackgroup="one",
            line=dict(width=0.5, color=palet[i % len(palet)]),
            hovertemplate="%{x|%Y-%m-%d}<br>" + col + ": %{y:.1%}<extra></extra>",
        ))
    fig.update_layout(
        title="Stil Kayması (RBSA Rolling)",
        xaxis_title="Tarih", yaxis_title="Ağırlık",
        template="plotly_dark" if is_dark else "plotly",
        hovermode="x unified", margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_factor_loading_chart(
    ff_result: dict,
    theme: str = "light",
) -> go.Figure:
    """Fama-French faktör yüklemeleri bar chart."""
    if not ff_result or not ff_result.get("betas"):
        return go.Figure()
    is_dark = theme == "dark"
    factors = list(ff_result["betas"].keys())
    loadings = [ff_result["betas"][f] for f in factors]
    t_vals = [ff_result["t_stats"].get(f, 0) for f in factors]
    colors = ["#2ca02c" if abs(t) >= 2 else "#d62728" for t in t_vals]

    fig = go.Figure(data=[go.Bar(
        x=factors, y=loadings, marker_color=colors,
        text=[f"{l:.3f} (t={t:.1f})" for l, t in zip(loadings, t_vals)],
        textposition="outside",
        textfont=dict(color="#ffffff" if is_dark else "#212529"),
    )])
    title_text = f"Faktör Yüklemeleri | Alpha: {ff_result.get('alpha', 0):.4f} | Adj R²: {ff_result.get('adj_r2', 0):.3f}"
    fig.update_layout(
        title=title_text, xaxis_title="Faktör", yaxis_title="Beta",
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig


def create_stress_test_chart(
    stress_results: dict,
    theme: str = "light",
) -> go.Figure:
    """Stres testi sonuçları — yatay bar chart."""
    if not stress_results:
        return go.Figure()
    is_dark = theme == "dark"

    # İlk fon için tüm senaryoları göster
    first_kod = list(stress_results[next(iter(stress_results))].keys())[0]
    scenarios = list(stress_results.keys())
    impacts = [stress_results[s].get(first_kod) for s in scenarios]
    colors = ["#d62728" if v is not None and v < 0 else "#2ca02c" for v in impacts]

    fig = go.Figure(data=[go.Bar(
        y=scenarios, x=impacts, orientation="h",
        marker_color=colors,
        text=[f"%{v:.1f}" if v is not None else "-" for v in impacts],
        textposition="outside",
        textfont=dict(color="#ffffff" if is_dark else "#212529"),
    )])
    fig.update_layout(
        title=f"Stres Testi — {first_kod}",
        xaxis_title="Etki (%)", yaxis_title="Senaryo",
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.add_vline(x=0, line_dash="dash", line_color="gray")
    return fig


def create_volume_chart(
    volume_data: list,
    fon_kodlari: list,
    theme: str = "light",
) -> go.Figure:
    """Fon bazlı işlem hacmi bar chart."""
    if not volume_data:
        return go.Figure()
    is_dark = theme == "dark"
    kod_hacim = {}
    for r in volume_data:
        kod = r.get("fonKodu", "")
        try:
            hacim = float(r.get("islemHacmi", 0) or 0)
            kod_hacim[kod] = hacim
        except (ValueError, TypeError):
            pass
    kodlar = [k for k in fon_kodlari if k in kod_hacim]
    hacimler = [kod_hacim[k] for k in kodlar]
    if not kodlar:
        return go.Figure()
    renkler = ["#2ca02c" if i == 0 else "#1f77b4" for i in range(len(kodlar))]
    fig = go.Figure(data=[go.Bar(
        x=kodlar, y=hacimler, marker_color=renkler,
        text=[f"{h:,.0f} TL" for h in hacimler],
        textposition="outside",
        textfont=dict(color="#ffffff" if is_dark else "#212529"),
    )])
    fig.update_layout(
        title="İşlem Hacmi (Fon Bazlı)",
        xaxis_title="Fon", yaxis_title="Hacim (TL)",
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def create_brinson_chart(
    attribution_result: dict,
    theme: str = "light",
) -> go.Figure:
    """Brinson atıf waterfall/bar chart."""
    if not attribution_result:
        return go.Figure()
    is_dark = theme == "dark"

    effects = ["Allocation", "Selection", "Interaction", "Toplam Aktif"]
    values = [
        attribution_result.get("allocation_effect", 0),
        attribution_result.get("selection_effect", 0),
        attribution_result.get("interaction_effect", 0),
        attribution_result.get("total_active", 0),
    ]
    colors = ["#1abc9c" if v >= 0 else "#d62728" for v in values]

    fig = go.Figure(data=[go.Bar(
        x=effects, y=values, marker_color=colors,
        text=[f"%{v:.3f}" for v in values], textposition="outside",
        textfont=dict(color="#ffffff" if is_dark else "#212529"),
    )])
    fig.update_layout(
        title="Brinson Atıf",
        xaxis_title="Etki", yaxis_title="Katkı (%)",
        template="plotly_dark" if is_dark else "plotly",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    return fig
