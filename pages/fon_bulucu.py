#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fon Bulucu — kategorideki fonlari dönemsel getiri ve yönetici basari metriklerine
gore karsilastirir.
"""

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

from data.fetchers import _tefas_api
from data.fetchers.tefas_fetcher import TefasFetcher
from components.metrics import calculate_fund_metrics, _max_drawdown
from config.logger import get_logger
from config.constants import (
    METRIC_SHARPE, METRIC_SORTINO, METRIC_ALPHA,
    METRIC_INFORMATION_RATIO, METRIC_TOTAL_RETURN,
    METRIC_ANNUALIZED_RETURN, METRIC_VOLATILITY,
    METRIC_MAX_DRAWDOWN, METRIC_DESCRIPTIONS,
)
from tlref_scraper import TLREFScraper, TLREFConverter

logger = get_logger(__name__)
dash.register_page(__name__, path="/fon-bulucu")

# ── Fon türlerini yükle ────────────────────────────────────────────
try:
    _FON_TURLERI = _tefas_api.fon_tur_listesi()
    logger.info("Fon turleri yuklendi: %s adet", len(_FON_TURLERI))
except Exception as exc:
    logger.warning("Fon turleri yuklenemedi: %s", exc)
    _FON_TURLERI = []

# ── Dönem tanımları ─────────────────────────────────────────────────
PERIOD_FIELD_MAP = {
    "1a": "getiri1a",
    "3a": "getiri3a",
    "6a": "getiri6a",
    "yb": "getiriyb",
    "1y": "getiri1y",
    "3y": "getiri3y",
    "5y": "getiri5y",
}

PERIOD_LABELS = {
    "1a": "1 Ay",
    "3a": "3 Ay",
    "6a": "6 Ay",
    "yb": "Yılbaşından Bu Yana",
    "1y": "1 Yıl",
    "3y": "3 Yıl",
    "5y": "5 Yıl",
}

_DEFAULT_PERIOD = "1y"

# Varsayilan donem (en uzun): 5 yil
def _max_period_days(period_key: str) -> int:
    mapping = {"1a": 30, "3a": 90, "6a": 180, "yb": 0, "1y": 365, "3y": 1095, "5y": 1825}
    return mapping.get(period_key, 365)


# ── Info bar ────────────────────────────────────────────────────────
info_bar = dbc.Alert([
    html.I(className="bi bi-info-circle me-2"),
    "Seçtiğiniz kategoride belirlediğiniz vadede en yüksek getirili fonları, "
    "fon yöneticisi başarı metriklerine (Alpha, Sharpe, Information Ratio) göre karşılaştırın.",
    html.A(
        " Detaylı Bilgi",
        href="/detayli-bilgi",
        className="alert-link ms-1",
        style={"textDecoration": "underline", "cursor": "pointer"},
    ),
], color="info", dismissable=False, className="py-2 mb-3", style={"fontSize": "0.9em"})


# ── Layout ──────────────────────────────────────────────────────────
layout = dbc.Container([
    info_bar,

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Kategori", className="card-title"),
                    dcc.Dropdown(
                        id="fb-kategori",
                        options=[
                            {"label": t["sfonTurAciklama"], "value": t["sfonTuru"]}
                            for t in _FON_TURLERI
                        ],
                        placeholder="Kategori seçin...",
                        clearable=False,
                    ),
                ])
            ], className="h-100 mb-3"),
        ], xs=12, md=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Vade", className="card-title"),
                    dbc.RadioItems(
                        id="fb-vade",
                        options=[
                            {"label": "1 Ay", "value": "1a"},
                            {"label": "3 Ay", "value": "3a"},
                            {"label": "6 Ay", "value": "6a"},
                            {"label": "Yılbaşı", "value": "yb"},
                            {"label": "1 Yıl", "value": "1y"},
                            {"label": "3 Yıl", "value": "3y"},
                            {"label": "5 Yıl", "value": "5y"},
                        ],
                        value=_DEFAULT_PERIOD,
                        inline=True,
                    ),
                ])
            ], className="h-100 mb-3"),
        ], xs=12, md=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Arama", className="card-title"),
                    dbc.Button(
                        "Fonları Bul",
                        id="fb-ara-btn",
                        color="primary",
                        className="w-100",
                        n_clicks=0,
                    ),
                    html.Div(id="fb-durum", className="mt-2 text-info"),
                ])
            ], className="h-100 mb-3"),
        ], xs=12, md=4),
    ], className="align-items-stretch"),

    html.Div(id="fb-sonuclar", style={"display": "none"}, children=[
        dbc.Card([
            dbc.CardBody([
                html.Div(id="fb-tavsiye", className="mb-3"),
                html.Div(id="fb-tablo"),
            ])
        ], className="mb-3"),
        dbc.Card([
            dbc.CardBody([
                html.H5("Getiri Karşılaştırması", className="card-title"),
                dcc.Loading(
                    dcc.Graph(id="fb-grafik", config={"displayModeBar": True}),
                ),
            ])
        ]),
    ]),
], fluid=True)


# ── Callback: arama ─────────────────────────────────────────────────
@callback(
    Output("fb-sonuclar", "style"),
    Output("fb-tablo", "children"),
    Output("fb-grafik", "figure"),
    Output("fb-durum", "children"),
    Output("fb-tavsiye", "children"),
    Input("fb-ara-btn", "n_clicks"),
    State("fb-kategori", "value"),
    State("fb-vade", "value"),
    prevent_initial_call=True,
)
def fonlari_bul(n_clicks, kategori_kod, vade):
    if not kategori_kod:
        return {"display": "none"}, html.Div(), go.Figure(), "Lütfen bir kategori seçin.", html.Div()

    period_field = PERIOD_FIELD_MAP.get(vade, "getiri1y")
    period_label = PERIOD_LABELS.get(vade, vade)

    # 1. Tüm fon getirilerini çek (kategori filtresiyle)
    try:
        fonlar = _tefas_api.fonlar_donemsel_getiri(fon_tipi="YAT", fon_tur_kod=kategori_kod)
    except Exception as exc:
        logger.warning("Fon getirileri cekilemedi: %s", exc)
        return {"display": "none"}, html.Div(), go.Figure(), f"Veri alinamadi: {exc}", html.Div()

    if not fonlar:
        return {"display": "none"}, html.Div(), go.Figure(), "Bu kategoride fon bulunamadi.", html.Div()

    # 2. Getirisi olan fonlari filtrele ve sirala
    fon_list = []
    for f in fonlar:
        val = f.get(period_field)
        if val is not None:
            fon_list.append((f["fonKodu"], f["fonUnvan"], float(val)))
    fon_list.sort(key=lambda x: x[2], reverse=True)

    if not fon_list:
        return {"display": "none"}, html.Div(), go.Figure(), f"Bu vadede ({period_label}) getiri verisi olan fon bulunamadi.", html.Div()

    # En fazla 10 fon
    top_fonlar = fon_list[:10]
    fon_kodlari = [f[0] for f in top_fonlar]

    # 3. Detayli metrikler icin veri cek
    max_days = _max_period_days(vade)
    end_date = date.today()
    if vade == "yb":
        start_date = date(end_date.year, 1, 1)
    else:
        start_date = end_date - timedelta(days=max_days)

    fetcher = TefasFetcher()
    fund_dict = {}
    for kod in fon_kodlari:
        try:
            df = fetcher.get_historical_data(kod, start_date, end_date)
            if not df.empty and len(df) >= 3:
                fund_dict[kod] = df
        except Exception as exc:
            logger.warning("Veri cekme hatasi %s: %s", kod, exc)

    if not fund_dict:
        return {"display": "none"}, html.Div(), go.Figure(), "Fon verileri cekilemedi.", html.Div()

    # Risksiz getiri ve market benchmark
    first_df = list(fund_dict.values())[0]
    rf_daily = _load_rf_for_period(first_df["tarih"])

    # Market (kategoriye gore)
    fon_unvan_map = {}
    for f in fonlar:
        fon_unvan_map[f["fonKodu"]] = f["fonUnvan"]
    market_prices = _load_market_for_category(fon_kodlari, fon_unvan_map)

    # Metrik hesapla
    metrics = calculate_fund_metrics(fund_dict, rf_daily, market_prices)

    if not metrics:
        return {"display": "none"}, html.Div(), go.Figure(), "Metrikler hesaplanamadi.", html.Div()

    # 5. Tabloyu olustur
    table = _build_fon_table(top_fonlar, metrics, period_field, period_label, fon_unvan_map)

    # 6. Grafik
    fig = _build_bar_chart(top_fonlar, period_field, period_label, fon_kodlari)

    # 7. Tavsiye (kullanici karar versin, sadece bilgi)
    tavsiye = html.Div([
        html.H5(f"📊 {len(top_fonlar)} Fon Karşılaştırması", className="mb-2"),
        html.P(
            f"Seçili dönemde ({period_label}) en yüksek getiriden en düşüğe sıralanmıştır. "
            "Fon yöneticisi başarısını değerlendirmek için Alpha, Sharpe ve Information Ratio metriklerine "
            "odaklanmanız önerilir.",
            className="text-muted", style={"fontSize": "0.9em"},
        ),
    ])
    durum = f"Seçilen zaman aralığına ({period_label}) göre en yüksek getiriyi sağlamış {len(top_fonlar)} fon getirildi"

    return {"display": "block"}, table, fig, durum, tavsiye


# ── Helper: fon tablosu ─────────────────────────────────────────────
def _build_fon_table(top_fonlar, metrics, period_field, period_label, fon_unvan_map):
    metric_keys = [
        METRIC_SHARPE, METRIC_ALPHA, METRIC_INFORMATION_RATIO,
        METRIC_SORTINO, METRIC_ANNUALIZED_RETURN,
        METRIC_VOLATILITY, METRIC_MAX_DRAWDOWN,
    ]
    headers = [html.Th("Fon")]
    tooltip_components = []
    for idx, mk in enumerate(metric_keys):
        desc = METRIC_DESCRIPTIONS.get(mk, "")
        header_id = f"fb-hdr-{idx}"
        if desc:
            headers.append(html.Th([
                mk,
                html.Span("?", id=header_id, className="ms-1 text-muted",
                          style={"cursor": "help", "fontSize": "0.85em"}),
            ]))
            tooltip_components.append(dbc.Tooltip(desc, target=header_id, placement="top"))
        else:
            headers.append(html.Th(mk))

    rows = []
    for i, (kod, unvan, getiri) in enumerate(top_fonlar):
        m = metrics.get(kod, {})
        row_style = {"backgroundColor": "#f0fff0"} if i == 0 else {}
        cells = [html.Td(html.Strong(kod) if i == 0 else kod)]
        for mk in metric_keys:
            val = m.get(mk, "-")
            cells.append(html.Td(f"{val}", style={"textAlign": "center"}))
        rows.append(html.Tr(cells, style=row_style))

    return html.Div(
        tooltip_components + [
            dbc.Table(
                [html.Thead(html.Tr(headers)), html.Tbody(rows)],
                striped=True, bordered=True, hover=True, size="sm", responsive=True,
            ),
        ]
    )


# ── Helper: bar chart ───────────────────────────────────────────────
def _build_bar_chart(top_fonlar, period_field, period_label, fon_kodlari):
    kod_list = [f[0] for f in top_fonlar]
    getiri_list = [f[2] for f in top_fonlar]
    renkler = ["#2ca02c" if g > 0 else "#d62728" for g in getiri_list]
    renkler[0] = "#1f77b4"  # en iyi fon ayri renk

    fig = go.Figure(data=[
        go.Bar(
            x=kod_list,
            y=getiri_list,
            marker_color=renkler,
            text=[f"%{g:.2f}" for g in getiri_list],
            textposition="outside",
        )
    ])
    fig.update_layout(
        title=f"Dönemsel Getiri Karşılaştırması ({period_label})",
        xaxis_title="Fon",
        yaxis_title="Getiri (%)",
        template="plotly_white",
        hovermode="x",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


# ── Helper: TLREF ───────────────────────────────────────────────────
def _load_rf_for_period(tarih_series: pd.Series) -> pd.Series:
    try:
        tlref = TLREFScraper()
        try:
            tlref_all = tlref.from_zip()
        except Exception:
            tlref_all = tlref.from_csv()

        fon_tarihler = pd.to_datetime(tarih_series)
        min_t, max_t = fon_tarihler.min(), fon_tarihler.max()
        tlref_filtre = tlref_all[(tlref_all["date"] >= min_t) & (tlref_all["date"] <= max_t)].copy()
        if tlref_filtre.empty:
            return pd.Series(dtype=float)

        tlref_map = dict(zip(tlref_filtre["date"].dt.date, tlref_filtre["value"]))
        daily_list = []
        onceki = None
        carpim = 1.0
        for tarih in fon_tarihler:
            t = tarih.date() if hasattr(tarih, "date") else tarih
            deger = tlref_map.get(t)
            if deger is not None:
                daily_r = TLREFConverter.daily_compound(deger) / 100.0
                gap = 1 if onceki is None else max((t - onceki).days, 1)
                carpim *= (1.0 + daily_r) ** gap
            onceki = t
            daily_list.append(carpim)
        cum = pd.Series(daily_list, index=fon_tarihler)
        return cum.pct_change().fillna(0)
    except Exception as exc:
        logger.warning("TLREF yuklenemedi: %s", exc)
        return pd.Series(dtype=float)


# ── Helper: market benchmark ───────────────────────────────────────
def _load_market_for_category(fon_kodlari: list, fon_unvan_map: dict) -> pd.Series:
    gold_keywords = ["altin", "gumus", "kiymetli maden", "precious metal", "gold", "silver", "emtia"]
    use_atkap = any(
        any(kw in fon_unvan_map.get(k, "").lower() for kw in gold_keywords)
        for k in fon_kodlari
    )
    symbol = "ATKAP" if use_atkap else "FHISE"
    try:
        from config.benchmarks import get_benchmark_data

        end = date.today()
        start = end - timedelta(days=365 * 5)
        df = get_benchmark_data(symbol, start, end)
        if not df.empty:
            return pd.Series(df["fiyat"].values, index=pd.to_datetime(df["tarih"]), name=symbol)
    except Exception as exc:
        logger.warning("Market (%s) yuklenemedi: %s", symbol, exc)
    return pd.Series(dtype=float)



