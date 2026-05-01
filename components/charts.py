#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotly grafik fabrikasi — fiyat ve getiri grafikleri.
"""

import plotly.graph_objects as go
import pandas as pd

from config.constants import DEFAULT_COLOR_PALETTE


def create_price_chart(df: pd.DataFrame, title: str = "Fon Fiyat Grafiği") -> go.Figure:
    """Tekil fon fiyat grafiği."""
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

    fig.update_layout(
        title=title,
        xaxis_title="Tarih",
        yaxis_title="Fiyat (TL)",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig
