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

from data.fetchers import _tefas_api
from config.logger import get_logger

logger = get_logger(__name__)
dash.register_page(__name__, path="/")

# Benchmark seçenekleri (başlangıçta sabit, ileride dinamik)
_BENCHMARK_OPTIONS = [
    {"label": "BIST 100", "value": "XU100"},
    {"label": "Dolar/TL", "value": "USDTRY"},
    {"label": "Euro/TL", "value": "EURTRY"},
    {"label": "Altın (Gram)", "value": "GLDGR"},
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
                                            "Birden fazla fon seçebilirsiniz.",
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
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    [
                                                        html.Label("Risk-Free Oranı (Yıllık %)"),
                                                        dcc.Input(
                                                            id="risk-free-input",
                                                            type="number",
                                                            value=45.0,
                                                            step=0.1,
                                                            className="form-control",
                                                        ),
                                                    ],
                                                    width=6,
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
    Output("analysis-store", "data"),
    Output("analiz-status", "children"),
    Input("analiz-btn", "n_clicks"),
    State("fon-select", "value"),
    State("benchmark-dropdown", "value"),
    State("tarih-araligi", "start_date"),
    State("tarih-araligi", "end_date"),
    State("getiri-tipi", "value"),
    State("risk-free-input", "value"),
    prevent_initial_call=True,
)
def run_analysis(
    n_clicks,
    fon_kodlari,
    benchmark,
    start_date,
    end_date,
    getiri_tipi,
    risk_free_annual,
):
    logger.debug("Analiz butonu: fon_kodlari=%s", fon_kodlari)
    if not fon_kodlari:
        return {}, "Lütfen en az bir fon seçin."

    # Metadata store'a kaydet (büyük veri disk cache'ten çekilecek)
    store_data = {
        "fon_kodlari": fon_kodlari,
        "benchmark": benchmark,
        "baslangic": start_date,
        "bitis": end_date,
        "getiri_tipi": getiri_tipi,
        "risk_free_yillik": risk_free_annual,
    }

    logger.info("Analiz başlatıldı: %s fon, %s → %s", len(fon_kodlari), start_date, end_date)
    return store_data, f"Analiz hazır! {len(fon_kodlari)} fon seçildi. 'Fon Analizi' sayfasına geçebilirsiniz."
