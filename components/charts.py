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

    Parametreler
    ------------
    benchmark_series : pd.Series, optional
        Benchmark kiyas serisi (index df ile ayni hizada, normalize edilmis).
    benchmark_name : str, optional
        Benchmark serisi etiket adi.
    """
    if df.empty or "tarih" not in df.columns or "fiyat" not in df.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["tarih"],
            y=df["fiyat"],
            mode="lines",
            name="Fiyat",
            line=dict(color=DEFAULT_COLOR_PALETTE[0], width=2),
            hovertemplate="%{x|%Y-%m-%d}<br>Fiyat: %{y:.4f}<extra></extra>",
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
                yaxis="y2",
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.6f}<extra></extra>",
            )
        )

        fig.update_layout(
            yaxis2=dict(
                title="Normalize Deger",
                overlaying="y",
                side="right",
                showgrid=False,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

    fig.update_layout(
        title=title,
        xaxis_title="Tarih",
        yaxis_title="Fiyat (TL)",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig
