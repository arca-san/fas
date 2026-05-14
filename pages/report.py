#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapor — HTML önizleme ve PDF indirme.
"""

import base64
import io
import logging
import os
from datetime import date, timedelta, datetime

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
from jinja2 import Environment, FileSystemLoader

# WeasyPrint macOS brew lib path
os.environ.setdefault("DYLD_FALLBACK_LIBRARY_PATH", "/opt/homebrew/lib")
from weasyprint import HTML

from data.fetchers import _tefas_api
from tlref_scraper import TLREFScraper, TLREFConverter
from data.fetchers.tefas_fetcher import TefasFetcher
from data.fetchers.kyd_fetcher import KydFetcher
from components.metrics import calculate_fund_metrics, calculate_mix_metrics, select_fund_benchmark
from config.constants import METRIC_DESCRIPTIONS
from config.logger import get_logger
from config.settings import PROJECT_ROOT
from config.benchmarks import benchmark_options as kyd_benchmark_options
from config.benchmarks import benchmark_koda_gore

logger = get_logger(__name__)
dash.register_page(__name__, path="/report")

TEMPLATE_DIR = PROJECT_ROOT / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

try:
    _ALL_FUNDS = _tefas_api.get_all_fonlar()
    seen = set()
    _ALL_FUNDS_UNIQUE = []
    for f in _ALL_FUNDS:
        kod = f.get("fonKod")
        if kod and kod not in seen:
            seen.add(kod)
            _ALL_FUNDS_UNIQUE.append(f)
    _ALL_FUNDS = _ALL_FUNDS_UNIQUE
except Exception as exc:
    logger.warning("Fon listesi yuklenemedi: %s", exc)
    _ALL_FUNDS = []

_TLREF_OPTION = {"label": "TLREF (Risksiz Getiri)", "value": "TLREF"}
_BENCHMARK_OPTIONS = [_TLREF_OPTION] + kyd_benchmark_options()

_DEFAULT_END = date.today()
_DEFAULT_START = _DEFAULT_END - timedelta(days=365)

layout = dbc.Container(
    [
        html.H3("Rapor", className="mb-3"),
        html.P("Fon analiz raporu oluşturun. HTML önizleme ve PDF indirme seçenekleri mevcuttur.",
               className="text-muted"),
        dbc.Row(
            className="align-items-stretch mb-3",
            children=[
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Fon", className="card-title"),
                            dmc.MultiSelect(
                                id="report-fon-select",
                                label="Fon kodu yazın",
                                placeholder="Fon seçin...",
                                searchable=True,
                                clearable=True,
                                data=[
                                    {"value": f.get("fonKod", ""),
                                     "label": f"{f.get('fonKod', '')} - {f.get('unvan', '')}"}
                                    for f in _ALL_FUNDS if f.get("fonKod")
                                ],
                            ),
                        ]),
                        className="h-100",
                    ),
                ], xs=12, md=4),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Tarih", className="card-title"),
                            dcc.DatePickerRange(
                                id="report-tarih-araligi",
                                start_date=_DEFAULT_START,
                                end_date=_DEFAULT_END,
                                display_format="YYYY-MM-DD",
                            ),
                        ]),
                        className="h-100",
                    ),
                ], xs=12, md=4),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("İşlem", className="card-title"),
                            dbc.Button("Rapor Oluştur", id="report-olustur-btn",
                                       color="primary", className="w-100 mb-2"),
                            html.Div(id="report-status", className="text-info small"),
                        ]),
                        className="h-100",
                    ),
                ], xs=12, md=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Benchmark", className="card-title"),
                            dmc.MultiSelect(
                                id="report-benchmark-select",
                                data=_BENCHMARK_OPTIONS,
                                placeholder="Benchmark seçin (isteğe bağlı)...",
                                clearable=True,
                            ),
                        ]),
                        className="mb-3",
                    ),
                    xs=12,
                ),
            ]
        ),
        dbc.Card(
            dbc.CardBody([
                html.H5("Önizleme", className="card-title"),
                html.Iframe(id="report-preview", style={
                    "width": "100%", "height": "600px", "border": "1px solid #ddd", "borderRadius": "4px"
                }),
                html.Div(id="report-download-area", className="mt-2"),
            ]),
            id="report-preview-card",
            style={"display": "none"},
        ),
    ],
    fluid=True,
)


@callback(
    Output("report-fon-select", "searchValue"),
    Input("report-fon-select", "searchValue"),
    prevent_initial_call=True,
)
def uppercase_search(val):
    if val and val != val.upper():
        return val.upper()
    return val


@callback(
    Output("report-preview", "srcDoc"),
    Output("report-download-area", "children"),
    Output("report-preview-card", "style"),
    Output("report-status", "children"),
    Input("report-olustur-btn", "n_clicks"),
    State("report-fon-select", "value"),
    State("report-benchmark-select", "value"),
    State("report-tarih-araligi", "start_date"),
    State("report-tarih-araligi", "end_date"),
    prevent_initial_call=True,
)
def generate_report(n_clicks, fon_kodlari, benchmark, start_date, end_date):
    fon_kodlari = [k.upper() for k in (fon_kodlari or [])]
    if not fon_kodlari:
        return "", "", {"display": "none"}, "Lütfen en az bir fon seçin."

    bas = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    bit = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    fetcher = TefasFetcher()
    fund_dict = {}
    for fon_kodu in fon_kodlari:
        try:
            df = fetcher.get_historical_data(fon_kodu, bas, bit)
            if not df.empty:
                fund_dict[fon_kodu] = df
        except Exception as exc:
            logger.warning("Veri cekme hatasi %s: %s", fon_kodu, exc)

    if not fund_dict:
        return "", "", {"display": "none"}, "Veri bulunamadı."

    # Risksiz getiri
    rf_daily_returns = pd.Series(dtype=float)
    market_prices = pd.Series(dtype=float)
    try:
        from tlref_scraper import TLREFScraper, TLREFConverter
        tlref_scraper = TLREFScraper()
        try:
            tlref_all = tlref_scraper.from_zip()
        except Exception:
            tlref_all = tlref_scraper.from_csv()
        first_df = list(fund_dict.values())[0]
        fon_tarihler = pd.to_datetime(first_df["tarih"])
        min_t, max_t = fon_tarihler.min(), fon_tarihler.max()
        tlref_filtre = tlref_all[(tlref_all["date"] >= min_t) & (tlref_all["date"] <= max_t)].copy()
        if not tlref_filtre.empty:
            tlref_map = dict(zip(tlref_filtre["date"].dt.date, tlref_filtre["value"]))
            daily_rf_list = []
            onceki_tarih = None
            carpim = 1.0
            for tarih in fon_tarihler:
                t = tarih.date() if hasattr(tarih, "date") else tarih
                deger = tlref_map.get(t)
                if deger is not None:
                    daily_r = TLREFConverter.daily_compound(deger) / 100.0
                    if onceki_tarih is None:
                        gap = 1
                    else:
                        gap = max((t - onceki_tarih).days, 1)
                    carpim *= (1.0 + daily_r) ** gap
                onceki_tarih = t
                daily_rf_list.append(carpim)
            cum_series = pd.Series(daily_rf_list, index=fon_tarihler)
            rf_daily_returns = cum_series.pct_change().fillna(0)
    except Exception as exc:
        logger.warning("TLREF alinamadi: %s", exc)

    try:
        kyd = KydFetcher()
        end = date.today()
        start = end - timedelta(days=365 * 5)
        market_df = kyd.get_historical_data("FHISE", start, end)
        if not market_df.empty:
            market_prices = pd.Series(
                market_df["fiyat"].values,
                index=pd.to_datetime(market_df["tarih"]),
                name="FHISE",
            )
    except Exception as exc:
        logger.warning("FHISE alinamadi: %s", exc)

    metrics = calculate_fund_metrics(fund_dict, rf_daily_returns, market_prices)

    metrik_isimleri = [
        "Toplam Getiri", "Yıllıklandırılmış Getiri", "Volatilite (Yıllık)",
        "Aşağı Yönlü Volatilite", "Maksimum Düşüş (Max Drawdown)",
        "VaR (%95)", "CVaR (%95)", "Sharpe Oranı", "Sortino Oranı",
        "Beta", "Treynor Oranı", "Alpha", "R²", "Information Ratio",
    ]

    # Benchmark verilerini yükle
    benchmark_list = benchmark if benchmark else []
    benchmarks = []
    benchmark_metrics = {}
    for bm in benchmark_list:
        if bm == "TLREF":
            benchmarks.append("TLREF (Risksiz Getiri)")
        else:
            bm_info = benchmark_koda_gore(bm)
            ad = bm_info["ad"] if bm_info else bm
            benchmarks.append(ad)
            try:
                first_df = list(fund_dict.values())[0]
                kyd = KydFetcher()
                kyd_df = kyd.get_historical_data(bm, bas, bit)
                if not kyd_df.empty and "tarih" in first_df.columns:
                    kyd_df = kyd_df.sort_values("tarih").reset_index(drop=True)
                    kyd_map = kyd_df.set_index("tarih")["fiyat"]
                    hizali = kyd_map.reindex(first_df["tarih"]).ffill()
                    if not hizali.dropna().empty:
                        ilk_fiyat = float(hizali.dropna().iloc[0])
                        bm_series = pd.Series(
                            (hizali.astype(float) / ilk_fiyat - 1.0) * 100.0,
                            index=first_df["tarih"].values,
                            name=ad,
                        )
                        bm_metrics = calculate_mix_metrics(bm_series, rf_daily_returns, market_prices, ad)
                        benchmark_metrics[ad] = bm_metrics
            except Exception as exc:
                logger.warning("Benchmark metrik alinamadi %s: %s", bm, exc)

    template = env.get_template("report.html.j2")
    html_content = template.render(
        start_date=bas.isoformat() if bas else "",
        end_date=bit.isoformat() if bit else "",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        fon_kodlari=fon_kodlari,
        benchmarks=benchmarks,
        metrik_isimleri=metrik_isimleri,
        metrikler=metrics,
        benchmark_metrics=benchmark_metrics,
        metrik_aciklamalari=METRIC_DESCRIPTIONS,
    )

    # PDF
    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        download_link = html.A(
            dbc.Button("PDF İndir", color="success", className="w-100"),
            href=f"data:application/pdf;base64,{pdf_b64}",
            download=f"fon_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        )
    except Exception as exc:
        logger.warning("PDF olusturulamadi: %s", exc)
        download_link = html.Span("PDF oluşturulamadı.", className="text-danger")

    return html_content, download_link, {"display": "block"}, f"Rapor oluşturuldu: {len(fund_dict)} fon."
