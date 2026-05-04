#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotly grafik fabrikasi — fiyat ve getiri grafikleri.
"""

import plotly.graph_objects as go
import pandas as pd

from config.constants import DEFAULT_COLOR_PALETTE


def create_price_chart(
    fund_dict: dict,
    benchmark_dict: dict = None,
    title: str = "Fon Getiri Grafiği",
) -> go.Figure:
    """Fon ve benchmark(lar) kumulatif getiri grafigi.

    Tum fonlar ayni grafikte cizilir (düz cizgi, ayri renk).
    Tum benchmarklar ayni grafikte cizilir (kesikli cizgi, gri).

    Parametreler
    ------------
    fund_dict : dict
        {"FON_KODU": df, ...} seklinde fon verileri.
        df'lerde "tarih" ve "fiyat" sutunlari olmali.
    benchmark_dict : dict, optional
        {"BENCHMARK_KODU": pd.Series, ...} seklinde benchmark serileri.
        Seriler yuzde getiri (%0 baslangicli) olmali.
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

        fig.add_trace(
            go.Scatter(
                x=df_ortak["tarih"],
                y=cum_return,
                mode="lines",
                name=kod,
                line=dict(color=color, width=2),
                hovertemplate="%{x|%Y-%m-%d}<br>%{customdata}: %{y:.2f}%<extra></extra>",
                customdata=[kod] * len(cum_return),
            )
        )

# Benchmark(lar): ortak tarihlerle hizala
    if benchmark_dict:
        for bm_kod, bm_series in benchmark_dict.items():
            if bm_series is None or bm_series.empty:
                continue
            bm_df = pd.DataFrame({"tarih": bm_series.index, "deger": bm_series.values})
            bm_ortak = bm_df[bm_df["tarih"].isin(ortak_tarihler)].sort_values("tarih")
            if not bm_ortak.empty:
                first_val = bm_ortak["deger"].iloc[0]
                if first_val != 0:
                    bm_return = (bm_ortak["deger"] / first_val - 1.0) * 100.0
                else:
                    bm_return = bm_ortak["deger"]
                fig.add_trace(
                    go.Scatter(
                        x=bm_ortak["tarih"],
                        y=bm_return,
                        mode="lines",
                        name=bm_kod,
                        line=dict(color="#666666", width=2, dash="dot"),
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
