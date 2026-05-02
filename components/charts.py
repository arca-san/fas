#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotly grafik fabrikasi — fiyat ve getiri grafikleri.
"""

import plotly.graph_objects as go
import pandas as pd

from config.constants import DEFAULT_COLOR_PALETTE


def create_price_chart(
    df: pd.DataFrame,
    title: str = "Fon Getiri Grafigi",
    benchmark_series: pd.Series = None,
    benchmark_name: str = None,
) -> go.Figure:
    """Fon ve benchmark kumulatif getiri grafigi.

    Tum seriler yuzde getiri olarak gosterilir (baslangic = %0).
    Ayni sol Y ekseninde cizilir.

    Parametreler
    ------------
    benchmark_series : pd.Series, optional
        Benchmark yuzde getiri serisi (index df ile ayni hizada, %0 baslangicli).
    benchmark_name : str, optional
        Benchmark serisi etiket adi.
    """
    if df.empty or "tarih" not in df.columns or "fiyat" not in df.columns:
        return go.Figure()

    # Ilk sifir olmayan fiyata kadar olan satirlari kirp
    mask = df["fiyat"].gt(0)
    if not mask.any():
        return go.Figure()
    ilk_idx = mask.idxmax()
    df = df.loc[ilk_idx:].reset_index(drop=True)
    if df.empty:
        return go.Figure()

    bas_fiyat = df["fiyat"].iloc[0]
    cum_return = (df["fiyat"] / bas_fiyat - 1.0) * 100.0

    # benchmark_series de ayni sekilde kirpilmalı
    if benchmark_series is not None:
        benchmark_series = benchmark_series.loc[ilk_idx:].reset_index(drop=True)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["tarih"],
            y=cum_return,
            mode="lines",
            name="Fon Getirisi",
            line=dict(color=DEFAULT_COLOR_PALETTE[0], width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>Getiri: %{y:.2f}%<extra></extra>",
        )
    )

    if benchmark_series is not None and benchmark_name and not benchmark_series.empty:
        fig.add_trace(
            go.Scatter(
                x=df["tarih"],
                y=benchmark_series,
                mode="lines",
                name=benchmark_name,
                line=dict(color=DEFAULT_COLOR_PALETTE[1], width=2, dash="dot"),
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>",
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
