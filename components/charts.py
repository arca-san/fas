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
    title: str = "Fon Fiyat Grafigi",
    benchmark_series: pd.Series = None,
    benchmark_name: str = None,
) -> go.Figure:
    """Tekil fon fiyat grafigi.

    Tum seriler normalize edilir (baslangic = 100) ve ayni sol Y
    ekseninde gosterilir.

    Parametreler
    ------------
    benchmark_series : pd.Series, optional
        Benchmark kiyas serisi (index df ile ayni hizada, normalize edilmis).
    benchmark_name : str, optional
        Benchmark serisi etiket adi.
    """
    if df.empty or "tarih" not in df.columns or "fiyat" not in df.columns:
        return go.Figure()

    bas_fiyat = df["fiyat"].iloc[0]
    normalized_price = df["fiyat"] / bas_fiyat * 100.0

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["tarih"],
            y=normalized_price,
            mode="lines",
            name="Fon (Normalize)",
            line=dict(color=DEFAULT_COLOR_PALETTE[0], width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>Deger: %{y:.2f}<extra></extra>",
        )
    )

    if benchmark_series is not None and benchmark_name:
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
        yaxis_title="Normalize Deger (Baslangic=100)",
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
