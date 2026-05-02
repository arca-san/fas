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
                                        html.Hr(),
                                        dbc.Button(
                                            "Analiz Et",
                                            id="analiz-btn",
                                            color="primary",
                                            className="w-100 mt-2",
                                        ),
                                        html.Div(id="analiz-status", className="mt-2 text-info"),
                                        html.Small(
                                            "TEFAS'tan veri aliniyor, bu islem 10-30 saniye surebilir.",
                                            className="text-muted d-block mt-1",
                                            id="tefas-uyari",
                                        ),
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
        seen = set()
        data = []
        for r in results:
            kod = r.get("fonKodu", "")
            if kod and kod not in seen:
                seen.add(kod)
                data.append({
                    "value": kod,
                    "label": f"{kod} - {r.get('fonUnvan', '')}",
                })
        logger.debug("Arama: '%s' -> %s sonuc (dedup: %s)", search_value, len(results), len(data))
        return data
    except Exception as exc:
        logger.warning("Fon arama basarisiz: %s", exc)
        return dash.no_update


@callback(
    Output("fiyat-grafigi", "figure"),
    Output("grafik-alani", "style"),
    Output("analiz-status", "children"),
    Output("tefas-uyari", "style"),
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
        return go.Figure(), {"display": "none"}, "Lutfen en az bir fon secin.", {"display": "none"}

    fon_kodu = fon_kodlari[0]
    fetcher = TefasFetcher()

    try:
        from datetime import datetime
        bas = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        bit = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
        df = fetcher.get_historical_data(fon_kodu, bas, bit)
    except Exception as exc:
        logger.error("Veri cekme hatasi: %s", exc)
        return go.Figure(), {"display": "none"}, f"Veri cekme hatasi: {exc}", {"display": "none"}

    if df.empty:
        return go.Figure(), {"display": "none"}, f"{fon_kodu} icin veri bulunamadi.", {"display": "none"}

    risk_free_daily = None
    benchmark_series = None
    benchmark_name = None
    status_parts = [f"{fon_kodu} getiri grafigi hazir. ({len(df)} gun)"]

    if benchmark == "TLREF":
        try:
            tlref_scraper = TLREFScraper()
            try:
                tlref_all = tlref_scraper.from_zip()
            except Exception:
                tlref_all = tlref_scraper.from_csv()
            tlref_map = dict(zip(tlref_all["date"].dt.date, tlref_all["value"]))

            if "tarih" in df.columns and not df["tarih"].empty:
                carpim = 1.0
                risk_free_cum = []
                onceki_tarih = None
                son_bilinen = None

                for tarih in df["tarih"]:
                    t = tarih.date() if hasattr(tarih, "date") else tarih
                    son_bilinen = tlref_map.get(t, son_bilinen)

                    if son_bilinen is not None:
                        daily_r = TLREFConverter.daily_compound(son_bilinen) / 100.0
                        if onceki_tarih is None:
                            gap = 1
                        else:
                            gap = (t - onceki_tarih).days
                        carpim *= (1.0 + daily_r) ** gap

                    risk_free_cum.append(carpim)
                    onceki_tarih = t

                benchmark_series = pd.Series(
                    risk_free_cum, index=df.index, name="TLREF (Kumulatif)"
                ) * 100.0 - 100.0

            # TLREF'i fon tarih araligina kirp
            tlref_filtre = tlref_all[
                (tlref_all["date"].dt.date >= df["tarih"].iloc[0].date())
                & (tlref_all["date"].dt.date <= df["tarih"].iloc[-1].date())
            ]
            if not tlref_filtre.empty:
                min_t = tlref_filtre["value"].min()
                max_t = tlref_filtre["value"].max()
            else:
                min_t = son_bilinen or 0
                max_t = son_bilinen or 0

            toplam_getiri = (risk_free_cum[-1] - 1.0) * 100.0 if risk_free_cum else 0
            status_parts.append(
                f"TLREF: %{min_t:.2f}~%{max_t:.2f} (Kum: %{toplam_getiri:.1f})"
            )
            benchmark_name = "TLREF (Kumulatif)"
            logger.info(
                "TLREF yuklendi: %s kayit, %s - %s",
                len(tlref_all), tlref_all["date"].iloc[0].date(),
                tlref_all["date"].iloc[-1].date(),
            )
        except Exception as exc:
            logger.warning("TLREF cekilemedi: %s", exc)
            status_parts.append(f"TLREF alinamadi: {exc}")

    fig = create_price_chart(
        df,
        title=f"{fon_kodu} - Getiri Grafigi",
        benchmark_series=benchmark_series,
        benchmark_name=benchmark_name,
    )

    logger.info(
        "Grafik olusturuldu: %s, %s satir, benchmark=%s",
        fon_kodu, len(df), benchmark,
    )
    return fig, {"display": "block"}, " | ".join(status_parts), {"display": "none"}
