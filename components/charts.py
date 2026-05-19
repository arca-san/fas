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
        logger.warning("=== CHARTS BENCHMARK DICT: %s ===", list(benchmark_dict.keys()))
        for i, (bm_kod, bm_series) in enumerate(benchmark_dict.items()):
            logger.warning("BM %s: len=%s, ilk degerler=%s", bm_kod, len(bm_series), bm_series[:5].tolist())
            
            if bm_series is None or bm_series.empty:
                continue
            
            # Forward fill ile NaN'ları doldur
            bm_filled = bm_series.ffill()
            if bm_filled.dropna().empty:
                logger.warning("BM %s: ffill sonrasi bos", bm_kod)
                continue
            
            # İlk geçerli değer (her zaman 0 olmalı, çünkü normalize ettik)
            first_val = 1.0  # Normalize ettiğimiz için her zaman 1.0
            
            # Tarihleri al
            tarihler = list(ortak_tarihler)
            bm_values = bm_filled.reindex(pd.DatetimeIndex(tarihler)).ffill().values
            
            logger.warning("BM reindex: len=%s, ilk=%s", len(bm_values), bm_values[:5])
            
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

    # Mix benchmark: kalın siyah çizgi
    if mix_benchmark and mix_benchmark.get("series") is not None:
        mix_series = mix_benchmark["series"]
        mix_name = mix_benchmark.get("name", "Mix Benchmark")
        
        if not mix_series.empty:
            mix_filled = mix_series.ffill()
            tarihler = list(ortak_tarihler)
            mix_values = mix_filled.reindex(pd.DatetimeIndex(tarihler)).ffill().values
            
            fig.add_trace(
                go.Scatter(
                    x=tarihler,
                    y=mix_values,
                    mode="lines",
                    name=mix_name,
                    line=dict(color="#000000", width=3, dash="dot"),
                    hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}%<extra></extra>",
                )
            )

    fig.update_layout(
        title=title,
        xaxis_title="Tarih",
        yaxis_title="Getiri (%)",
        hovermode="x unified",
        template="plotly_white",
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

    for kod, m in metrics.items():
        risk = m.get(METRIC_VOLATILITY, None)
        getiri = m.get(METRIC_ANNUALIZED_RETURN, None)
        if risk is None or getiri is None:
            continue
        fig.add_trace(
            go.Scatter(
                x=[risk],
                y=[getiri],
                mode="markers+text",
                name=kod,
                text=[kod],
                textposition="top center",
                marker=dict(size=12, line=dict(width=2, color="DarkSlateGrey")),
                hovertemplate="%{text}<br>Risk: %{x:.2f}%<br>Getiri: %{y:.2f}%<extra></extra>",
            )
        )

    # Referans cizgileri
    fig.update_layout(
        title=title,
        xaxis_title="Risk (Volatilite, %)",
        yaxis_title="Getiri (Yıllık, %)",
        template="plotly_white",
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
