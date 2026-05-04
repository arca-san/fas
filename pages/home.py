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
from components.metrics import calculate_fund_metrics, select_fund_benchmark
from config.logger import get_logger
from config.benchmarks import benchmark_options as kyd_benchmark_options
from config.benchmarks import benchmark_koda_gore
from config.settings import CALENDAR_ALIGN_METHOD
from tlref_scraper import TLREFScraper, TLREFConverter
import plotly.graph_objects as go

logger = get_logger(__name__)
dash.register_page(__name__, path="/")

# Tüm fonları bir kez yükle (startup'da)
try:
    _ALL_FUNDS = _tefas_api.get_all_fonlar()
    logger.info("Tum fonlar yuklendi: %s adet", len(_ALL_FUNDS))
    if _ALL_FUNDS:
        logger.info("Ornek veri: %s", _ALL_FUNDS[0])
    # Tekrarlari temizle
    seen = set()
    _ALL_FUNDS_UNIQUE = []
    for f in _ALL_FUNDS:
        kod = f.get("fonKod")
        if kod and kod not in seen:
            seen.add(kod)
            _ALL_FUNDS_UNIQUE.append(f)
    _ALL_FUNDS = _ALL_FUNDS_UNIQUE
    logger.info("Tekrarsiz fon sayisi: %s", len(_ALL_FUNDS))
except Exception as exc:
    logger.warning("Fon listesi yuklenemedi: %s", exc)
    _ALL_FUNDS = []

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
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5("Fon Metrikleri", className="card-title"),
                            html.Div(id="metrik-tablosu"),
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
                                            placeholder="Fon seçin...",
                                            searchable=True,
                                            clearable=True,
                                            data=[
                                                {
                                                    "value": f.get("fonKod", ""),
                                                    "label": f"{f.get('fonKod', '')} - {f.get('unvan', '')}",
                                                }
                                                for f in _ALL_FUNDS if f.get("fonKod")
                                            ],
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


# Kullanıcı yazdıkça otomatik uppercase yap
@callback(
    Output("fon-select", "searchValue"),
    Input("fon-select", "searchValue"),
    prevent_initial_call=True,
)
def uppercase_search(val):
    if val and val != val.upper():
        return val.upper()
    return val


@callback(
    Output("fiyat-grafigi", "figure"),
    Output("grafik-alani", "style"),
    Output("analiz-status", "children"),
    Output("tefas-uyari", "style"),
    Output("metrik-tablosu", "children"),
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
    # Lowercase gelen kodları uppercase'e çevir
    fon_kodlari = [k.upper() for k in (fon_kodlari or [])]
    logger.info("FON KODLARI GELEN: %s (type: %s)", fon_kodlari, type(fon_kodlari))
    if not fon_kodlari:
        return go.Figure(), {"display": "none"}, "Lutfen en az bir fon secin.", {"display": "none"}, html.Small("Henüz fon seçilmedi", className="text-muted")

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
        return go.Figure(), {"display": "none"}, " | ".join(hata_list) if hata_list else "Veri bulunamadi.", {"display": "none"}, html.Small("Metrik hesaplanamadi", className="text-muted")

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

                if kyd_df.empty or not fund_dict:
                    status_parts.append(f"{endeks_adi} verisi bos")
                else:
                    first_df = list(fund_dict.values())[0]
                    logger.info("KYD %s: %s kayit, tarih tipi: %s", bm, len(kyd_df), kyd_df["tarih"].dtype)
                    logger.info("FON first_df tarih tipi: %s, ilk: %s", first_df["tarih"].dtype, first_df["tarih"].iloc[0])

                    if "tarih" not in first_df.columns or first_df["tarih"].empty:
                        status_parts.append(f"{endeks_adi} verisi bos")
                    else:
                        kyd_df = kyd_df.sort_values("tarih").reset_index(drop=True)

                        kyd_map = kyd_df.set_index("tarih")["fiyat"]
                        hizali = kyd_map.reindex(first_df["tarih"]).ffill()
                        logger.info("hizali: %s/%s deger, ilk: %s, NaN: %s", 
                            hizali.notna().sum(), len(hizali), hizali.iloc[0], hizali.isna().sum())

                        if hizali.dropna().empty:
                            status_parts.append(f"{endeks_adi} ile ortak gun bulunamadi")
                        else:
                            # İlk fiyatı al ve getiri hesapla
                            ilk_fiyat = float(hizali.dropna().iloc[0])
                            logger.info("ilk_fiyat: %.4f", ilk_fiyat)
                            
                            # Getiri hesapla
                            getiri = (hizali.astype(float) / ilk_fiyat - 1.0) * 100.0
                            
                            # Index'i datetime olarak ayarla
                            benchmark_dict[bm] = pd.Series(
                                getiri.values,
                                index=first_df["tarih"].values,
                                name=endeks_adi,
                            )
                            logger.info("BM dict olustu: %s, len=%s, ilk=%.4f, NaN=%s", 
                                bm, len(benchmark_dict[bm]), benchmark_dict[bm].iloc[0], benchmark_dict[bm].isna().sum())
                            status_parts.append(
                                f"{endeks_adi}: {hizali.notna().sum()} ortak gun"
                            )

                        logger.info(
                            "KYD benchmark yuklendi: %s (%s kayit)", bm, len(kyd_df)
                        )
            except Exception as exc:
                logger.warning("KYD benchmark cekilemedi (%s): %s", bm, exc)
                status_parts.append(f"{bm} alinamadi: {exc}")

    fig = create_price_chart(
        fund_dict=fund_dict,
        benchmark_dict=benchmark_dict,
        title=f"{', '.join(fund_dict.keys())} - Getiri Grafigi",
    )

    # Metrik hesaplama
    metrik_html, tooltip_metrics = _build_metrics_table(fund_dict)

    fig = create_price_chart(
        fund_dict=fund_dict,
        benchmark_dict=benchmark_dict,
        title=f"{', '.join(fund_dict.keys())} - Getiri Grafigi",
        metrics=tooltip_metrics,
    )
    return fig, {"display": "block"}, " | ".join(status_parts), {"display": "none"}, metrik_html


def _build_metrics_table(fund_dict: dict):
    """Fon metriklerini tablo olarak olustur."""
    from config.constants import (
        METRIC_TOTAL_RETURN,
        METRIC_ANNUALIZED_RETURN,
        METRIC_VOLATILITY,
        METRIC_DOWNSIDE_VOL,
        METRIC_SHARPE,
        METRIC_SORTINO,
        METRIC_BETA,
        METRIC_TREYNOR,
        METRIC_ALPHA,
        METRIC_INFORMATION_RATIO,
    )

    # Fon unvanlarini bul
    fon_unvan_map = {}
    for f in _ALL_FUNDS:
        fon_unvan_map[f.get("fonKod", "").upper()] = f.get("unvan", "")

    # Risksiz getiri (TLREF)
    rf_series = None
    try:
        tlref_scraper = TLREFScraper()
        try:
            tlref_all = tlref_scraper.from_zip()
        except Exception:
            tlref_all = tlref_scraper.from_csv()

        first_df = list(fund_dict.values())[0]
        tlref_map = dict(zip(tlref_all["date"].dt.date, tlref_all["value"]))

        carpim = 1.0
        risk_free_daily = []
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
            risk_free_daily.append(carpim)
            onceki_tarih = t

        rf_series = pd.Series(
            [x - 1 for x in risk_free_daily],
            index=first_df.index,
            name="TLREF",
        )
    except Exception as exc:
        logger.warning("TLRF metrik icin alinamadi: %s", exc)

    # Market benchmark (FHISE)
    market_series = None
    try:
        kyd = KydFetcher()
        end = date.today()
        start = end - timedelta(days=365 * 5)
        market_df = kyd.get_historical_data("FHISE", start, end)
        if not market_df.empty:
            market_series = pd.Series(
                market_df["fiyat"].values,
                index=pd.to_datetime(market_df["tarih"]),
                name="FHISE",
            )
    except Exception as exc:
        logger.warning("FHISE metrik icin alinamadi: %s", exc)

    metrics = calculate_fund_metrics(fund_dict, rf_series, market_series)

    if not metrics:
        return html.Small("Metrik hesaplanamadi", className="text-muted"), {}

    metrik_keys = [
        METRIC_TOTAL_RETURN,
        METRIC_ANNUALIZED_RETURN,
        METRIC_VOLATILITY,
        METRIC_DOWNSIDE_VOL,
        METRIC_SHARPE,
        METRIC_SORTINO,
        METRIC_BETA,
        METRIC_TREYNOR,
        METRIC_ALPHA,
        METRIC_INFORMATION_RATIO,
    ]

    # Tablo basliklari
    headers = ["Fon"] + metrik_keys
    rows = []
    for fon_kodu, m in metrics.items():
        unvan = fon_unvan_map.get(fon_kodu.upper(), fon_kodu)
        row = [f"{fon_kodu}"]
        for k in metrik_keys:
            val = m.get(k, "-")
            if val == "-":
                row.append("-")
            else:
                row.append(f"{val}")
        rows.append(row)

    table = dbc.Table(
        [
            html.Thead(html.Tr([html.Th(h) for h in headers])),
            html.Tbody([html.Tr([html.Td(c) for c in r]) for r in rows]),
        ],
        striped=True,
        bordered=True,
        hover=True,
        size="sm",
        responsive=True,
    )
    return table, metrics
