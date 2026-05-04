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
from data.fetchers.kyd_fetcher import KydFetcher
from components.charts import create_price_chart
from config.logger import get_logger
from config.benchmarks import benchmark_options as kyd_benchmark_options
from config.benchmarks import benchmark_koda_gore
from config.settings import CALENDAR_ALIGN_METHOD
from tlref_scraper import TLREFScraper, TLREFConverter
import plotly.graph_objects as go

logger = get_logger(__name__)
dash.register_page(__name__, path="/")

# Benchmark seçenekleri
_TLREF_OPTION = {"label": "TLREF (Risksiz Getiri)", "value": "TLREF"}

_BENCHMARK_OPTIONS = [_TLREF_OPTION] + kyd_benchmark_options()

# Varsayılan tarih aralığı: son 1 yıl
_DEFAULT_END = date.today()
_DEFAULT_START = _DEFAULT_END - timedelta(days=365)

layout = dbc.Container(
    [
        html.Div(id="grafik-alani", style={"display": "none"}, children=[
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("Getiri Grafiği", className="card-title"),
                            dcc.Loading(
                                id="loading-chart",
                                type="default",
                                children=dcc.Graph(id="fiyat-grafigi", config={"displayModeBar": True}),
                            ),
                        ]
                    )
                ],
                className="mb-3",
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
                                        html.H5("Fon", className="card-title"),
                                        dmc.MultiSelect(
                                            id="fon-select",
                                            label="Fon kodu veya ünvanı yazın",
                                            placeholder="En az 2 karakter...",
                                            searchable=True,
                                            clearable=True,
                                            debounce=400,
                                            data=[],
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
                                        html.H5("Benchmark(lar)", className="card-title"),
                                        dmc.MultiSelect(
                                            id="benchmark-dropdown",
                                            data=_BENCHMARK_OPTIONS,
                                            placeholder="Benchmark seçin...",
                                            clearable=True,
                                        ),
                                    ]
                                )
                            ],
                            className="mb-3",
                        ),
                    ],
                    xs=12, md=6,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H5("Tarih", className="card-title"),
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
                                        dbc.Button(
                                            "Analiz Et",
                                            id="analiz-btn",
                                            color="primary",
                                            className="w-100",
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
                    xs=12, md=6,
                ),
            ]
        ),
    ],
    fluid=True,
)


@callback(
    Output("fon-select", "data"),
    Output("fon-select", "searchValue"),
    Input("fon-select", "searchValue"),
    prevent_initial_call=True,
)
def search_funds(search_value):
    """Kullanıcı yazdıkça TEFAS'tan fon ara."""
    if not search_value or len(search_value.strip()) < 2:
        return dash.no_update, dash.no_update
    search_up = search_value.strip().upper()
    try:
        results = _tefas_api.fon_unvan_ara(search_up)
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
        logger.debug("Arama: '%s' -> %s sonuc (dedup: %s)", search_up, len(results), len(data))
        return data, search_up
    except Exception as exc:
        logger.warning("Fon arama basarisiz: %s", exc)
        return dash.no_update, dash.no_update


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
    logger.info("FON KODLARI GELEN: %s (type: %s)", fon_kodlari, type(fon_kodlari))
    if not fon_kodlari:
        return go.Figure(), {"display": "none"}, "Lutfen en az bir fon secin.", {"display": "none"}

    from datetime import datetime
    bas = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    bit = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    fetcher = TefasFetcher()
    fund_dict = {}
    hata_list = []

    for fon_kodu in fon_kodlari:
        try:
            df = fetcher.get_historical_data(fon_kodu, bas, bit)
            if not df.empty:
                fund_dict[fon_kodu] = df
            else:
                hata_list.append(f"{fon_kodu}: veri bulunamadi")
        except Exception as exc:
            logger.warning("Veri cekme hatasi %s: %s", fon_kodu, exc)
            hata_list.append(f"{fon_kodu}: {exc}")

    if not fund_dict:
        return go.Figure(), {"display": "none"}, " | ".join(hata_list) if hata_list else "Veri bulunamadi.", {"display": "none"}

    status_parts = [f"{len(fund_dict)} fon, {min(len(d) for d in fund_dict.values())} gun"]

    benchmark_dict = {}

    benchmark_list = benchmark if benchmark else []

    for bm in benchmark_list:
        if bm == "TLREF":
            try:
                tlref_scraper = TLREFScraper()
                try:
                    tlref_all = tlref_scraper.from_zip()
                except Exception:
                    tlref_all = tlref_scraper.from_csv()
                tlref_map = dict(zip(tlref_all["date"].dt.date, tlref_all["value"]))

                first_df = list(fund_dict.values())[0]

                if "tarih" in first_df.columns and not first_df["tarih"].empty:
                    carpim = 1.0
                    risk_free_cum = []
                    onceki_tarih = None
                    son_bilinen = None

                    for tarih in first_df["tarih"]:
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

                    benchmark_dict["TLREF"] = pd.Series(
                        risk_free_cum, index=first_df.index, name="TLREF"
                    ) * 100.0 - 100.0

                tlref_filtre = tlref_all[
                    (tlref_all["date"].dt.date >= first_df["tarih"].iloc[0].date())
                    & (tlref_all["date"].dt.date <= first_df["tarih"].iloc[-1].date())
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
                logger.info(
                    "TLREF yuklendi: %s kayit", len(tlref_all),
                )
            except Exception as exc:
                logger.warning("TLREF cekilemedi: %s", exc)
                status_parts.append(f"TLREF alinamadi: {exc}")

        else:
            try:
                endeks_bilgi = benchmark_koda_gore(bm)
                endeks_adi = endeks_bilgi["ad"] if endeks_bilgi else bm

                kyd = KydFetcher()
                kyd_df = kyd.get_historical_data(bm, bas, bit)

                if not kyd_df.empty and fund_dict:
                    first_df = list(fund_dict.values())[0]
                    if "tarih" in first_df.columns and not first_df["tarih"].empty:
                        kyd_df = kyd_df.sort_values("tarih").reset_index(drop=True)

                        if CALENDAR_ALIGN_METHOD == "inner":
                            ortak = pd.merge(
                                first_df[["tarih"]].assign(_idx=first_df.index),
                                kyd_df[["tarih", "fiyat"]],
                                on="tarih",
                                how="inner",
                            ).sort_values("tarih")
                            if ortak.empty:
                                status_parts.append(f"{endeks_adi} ile ortak gun bulunamadi")
                            else:
                                ilk_fiyat = ortak["fiyat"].iloc[0]
                                benchmark_dict[bm] = pd.Series(
                                    (ortak["fiyat"] / ilk_fiyat - 1.0) * 100.0,
                                    index=ortak["_idx"].values,
                                    name=endeks_adi,
                                )
                                status_parts.append(
                                    f"{endeks_adi}: {len(ortak)} ortak gun"
                                )
                        else:
                            kyd_map = kyd_df.set_index("tarih")["fiyat"]
                            hizali = kyd_map.reindex(first_df["tarih"]).ffill()
                            ilk_fiyat = hizali.iloc[0]
                            benchmark_dict[bm] = pd.Series(
                                (hizali / ilk_fiyat - 1.0) * 100.0,
                                index=first_df.index,
                                name=endeks_adi,
                            )
                            status_parts.append(
                                f"{endeks_adi}: {kyd_df['tarih'].iloc[0].date()}-{kyd_df['tarih'].iloc[-1].date()}"
                            )

                        logger.info(
                            "KYD benchmark yuklendi: %s (%s kayit)", bm, len(kyd_df)
                        )
                    else:
                        status_parts.append(f"{endeks_adi} verisi bos")
            except Exception as exc:
                logger.warning("KYD benchmark cekilemedi (%s): %s", bm, exc)
                status_parts.append(f"{bm} alinamadi: {exc}")

    fig = create_price_chart(
        fund_dict=fund_dict,
        benchmark_dict=benchmark_dict,
        title=f"{', '.join(fund_dict.keys())} - Getiri Grafigi",
    )

    logger.info(
        "Grafik olusturuldu: %s, %s satir, benchmark=%s",
        list(fund_dict.keys()), min(len(d) for d in fund_dict.values()), list(benchmark_dict.keys()),
    )
    return fig, {"display": "block"}, " | ".join(status_parts), {"display": "none"}
