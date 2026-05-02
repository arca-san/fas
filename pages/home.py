#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ana Sayfa — Fon seçimi, benchmark, tarih aralığı ve analiz parametreleri.
"""

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from datetime import date, timedelta
import pandas as pd

from data.fetchers import _tefas_api
from data.fetchers.tefas_fetcher import TefasFetcher
from components.charts import create_price_chart
from config.logger import get_logger
from config.settings import TLREF_ANNUAL_DAYS
from tlref_scraper import TLREFScraper, TLREFConverter
import plotly.graph_objects as go

logger = get_logger(__name__)
dash.register_page(__name__, path="/")

# Benchmark seçenekleri (başlangıçta sabit, ileride dinamik)
_BENCHMARK_OPTIONS = [
    {"label": "BIST 100", "value": "XU100"},
    {"label": "Dolar/TL", "value": "USDTRY"},
    {"label": "Euro/TL", "value": "EURTRY"},
    {"label": "Altın (Gram)", "value": "GLDGR"},
    {"label": "TLREF (Risksiz Getiri)", "value": "TLREF"},
]

# Varsayılan tarih aralığı: son 1 yıl
_DEFAULT_END = date.today()
_DEFAULT_START = _DEFAULT_END - timedelta(days=365)

layout = dbc.Container(
    [
        html.H2("Fon Analiz Sistemi", className="mb-4"),
        html.P(
            "Analiz etmek istediğiniz fonları, benchmark'ı ve tarih aralığını seçin."
        ),
        html.Div(id="grafik-alani", style={"display": "none"}, children=[
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("Fiyat Grafiği", className="card-title"),
                            dcc.Loading(
                                id="loading-chart",
                                type="default",
                                children=dcc.Graph(id="fiyat-grafigi", config={"displayModeBar": True}),
                            ),
                        ]
                    )
                ],
                className="mb-4 mt-4",
            ),
        ]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Fon Seçimi", className="card-title"),
                                        dmc.MultiSelect(
                                            id="fon-select",
                                            label="Fon kodu veya ünvanı yazın",
                                            placeholder="En az 2 karakter yazın...",
                                            searchable=True,
                                            clearable=True,
                                            debounce=400,
                                            data=[],
                                        ),
                                        html.Small(
                                            "Birden fazla fon seçebilirsiniz. İlk seçili fonun fiyat grafiği çizilecek.",
                                            className="text-muted d-block mt-2",
                                        ),
                                    ]
                                )
                            ],
                            className="mb-3",
                        ),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Benchmark", className="card-title"),
                                        dcc.Dropdown(
                                            id="benchmark-dropdown",
                                            options=_BENCHMARK_OPTIONS,
                                            placeholder="Benchmark seçin...",
                                            clearable=True,
                                        ),
                                    ]
                                )
                            ],
                            className="mb-3",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Tarih Aralığı", className="card-title"),
                                        dcc.DatePickerRange(
                                            id="tarih-araligi",
                                            start_date=_DEFAULT_START,
                                            end_date=_DEFAULT_END,
                                            display_format="YYYY-MM-DD",
                                        ),
                                    ]
                                )
                            ],
                            className="mb-3",
                        ),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Parametreler", className="card-title"),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Label("Getiri Tipi"),
                                                        dcc.RadioItems(
                                                            id="getiri-tipi",
                                                            options=[
                                                                {"label": "Log Getiri", "value": "log"},
                                                                {"label": "Basit Getiri", "value": "simple"},
                                                            ],
                                                            value="log",
                                                            inline=True,
                                                            labelStyle={"margin-right": "15px"},
                                                        ),
                                                    ],
                                                    width=12,
                                                ),
                                            ]
                                        ),
                                        html.Hr(),
                                        dbc.Button(
                                            "Analiz Et",
                                            id="analiz-btn",
                                            color="primary",
                                            className="w-100 mt-2",
                                        ),
                                        html.Div(id="analiz-status", className="mt-2 text-info"),
                                    ]
                                )
                            ]
                        ),
                    ],
                    width=6,
                ),
            ]
        ),
    ],
    fluid=True,
)


@callback(
    Output("fon-select", "data"),
    Input("fon-select", "searchValue"),
    prevent_initial_call=True,
)
def search_funds(search_value):
    """Kullanıcı yazdıkça TEFAS'tan fon ara."""
    if not search_value or len(search_value.strip()) < 2:
        # Bos veya cok kisa arama: mevcut data'yi koru (secili ogeler kaybolmasin)
        return dash.no_update
    try:
        results = _tefas_api.fon_unvan_ara(search_value.strip())
        data = [
            {"value": r.get("fonKodu", ""), "label": f"{r.get('fonKodu', '')} - {r.get('fonUnvan', '')}"}
            for r in results
            if r.get("fonKodu")
        ]
        logger.debug("Arama: '%s' -> %s sonuc", search_value, len(data))
        return data
    except Exception as exc:
        logger.warning("Fon arama basarisiz: %s", exc)
        return dash.no_update


@callback(
    Output("fiyat-grafigi", "figure"),
    Output("grafik-alani", "style"),
    Output("analiz-status", "children"),
    Input("analiz-btn", "n_clicks"),
    State("fon-select", "value"),
    State("benchmark-dropdown", "value"),
    State("tarih-araligi", "start_date"),
    State("tarih-araligi", "end_date"),
    prevent_initial_call=True,
)
def run_analysis(
    n_clicks,
    fon_kodlari,
    benchmark,
    start_date,
    end_date,
):
    logger.debug("Analiz butonu: fon_kodlari=%s benchmark=%s", fon_kodlari, benchmark)
    if not fon_kodlari:
        return go.Figure(), {"display": "none"}, "Lutfen en az bir fon secin."

    fon_kodu = fon_kodlari[0]
    fetcher = TefasFetcher()

    try:
        from datetime import datetime
        bas = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        bit = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        df = fetcher.get_historical_data(fon_kodu, bas, bit)
    except Exception as exc:
        logger.error("Veri cekme hatasi: %s", exc)
        return go.Figure(), {"display": "none"}, f"Veri cekme hatasi: {exc}"

    if df.empty:
        return go.Figure(), {"display": "none"}, f"{fon_kodu} icin veri bulunamadi."

    risk_free_daily = None
    benchmark_series = None
    benchmark_name = None
    status_parts = [f"{fon_kodu} fiyat grafigi hazir. ({len(df)} gun)"]

    if benchmark == "TLREF":
        try:
            tlref_scraper = TLREFScraper()
            tlref_df = tlref_scraper.from_csv()
            son_tlref = tlref_df["value"].iloc[-1]
            risk_free_daily = TLREFConverter.daily_compound(son_tlref)

            if "tarih" in df.columns and not df["tarih"].empty:
                bas_date = df["tarih"].iloc[0]
                daily_rate = risk_free_daily / 100.0
                gun_sayisi = len(df)
                risk_free_cum = [(1.0 + daily_rate) ** i for i in range(gun_sayisi)]
                benchmark_series = pd.Series(
                    risk_free_cum, index=df.index, name="TLREF (Bilesik)"
                )
                risk_free_pct = risk_free_daily * gun_sayisi

            status_parts.append(
                f"TLREF: %{son_tlref:.2f} (gunluk: %{risk_free_daily:.4f})"
            )
            benchmark_name = "TLREF (Risksiz Getiri)"
            logger.info(
                "TLREF yuklendi: yillik=%s%% gunluk=%s%%",
                son_tlref, risk_free_daily,
            )
        except Exception as exc:
            logger.warning("TLREF cekilemedi: %s", exc)
            status_parts.append(f"TLREF alinamadi: {exc}")

    fig = create_price_chart(
        df,
        title=f"{fon_kodu} - Fiyat Grafigi",
        benchmark_series=benchmark_series,
        benchmark_name=benchmark_name,
    )

    logger.info(
        "Grafik olusturuldu: %s, %s satir, benchmark=%s",
        fon_kodu, len(df), benchmark,
    )
    return fig, {"display": "block"}, " | ".join(status_parts)
