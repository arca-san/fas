#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ana Sayfa — Fon seçimi, benchmark, tarih aralığı ve analiz parametreleri.
"""

import dash
from dash import html, dcc, callback, Output, Input, State, MATCH, ALL
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from datetime import date, timedelta
import pandas as pd

from data.fetchers import _tefas_api
from data.fetchers.tefas_fetcher import TefasFetcher
from data.fetchers.kyd_fetcher import KydFetcher
from components.charts import create_price_chart
from components.metrics import calculate_fund_metrics, select_fund_benchmark, calculate_mix_metrics, get_fund_benchmarks
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

# Mix Benchmark Modal
mix_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Mix Benchmark Oluştur")),
        dbc.ModalBody([
            html.P("Benchmarklar için ağırlık atayın (toplam otomatik %100'e normalize edilir):"),
            html.Div(id="mix-benchmark-inputs"),
            html.Hr(),
            html.Div(id="mix-weight-total", className="mt-2 fw-bold"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Oluştur", id="create-mix-btn", color="primary", className="me-2"),
            dbc.Button("İptal", id="cancel-mix-btn", color="secondary"),
        ]),
    ],
    id="mix-modal",
    size="md",
    is_open=False,
)

layout = dbc.Container(
    [
        dcc.Store(id="mix-benchmark-store"),
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
                                        html.Div(
                                            dbc.Button(
                                                "Mix Benchmark Oluştur",
                                                id="open-mix-modal-btn",
                                                color="secondary",
                                                size="sm",
                                                className="mt-2 w-100",
                                            ),
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
        mix_modal,
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
    State("mix-benchmark-store", "data"),
    prevent_initial_call=True,
)
def run_analysis(
    n_clicks,
    fon_kodlari,
    benchmark,
    start_date,
    end_date,
    mix_data,
):
    logger.debug("Analiz butonu: fon_kodlari=%s benchmark=%s", fon_kodlari, benchmark)
    fon_kodlari = [k.upper() for k in (fon_kodlari or [])]
    logger.info("FON KODLARI GELEN: %s (type: %s)", fon_kodlari, type(fon_kodlari))
    if not fon_kodlari:
        return go.Figure(), {"display": "none"}, "Lutfen en az bir fon secin.", {"display": "none"}, html.Small("Henüz fon seçilmedi", className="text-muted")

    from datetime import datetime
    bas = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    bit = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    fetcher = TefasFetcher()
    fund_dict = {}
    fund_kategoriler = {}
    hata_list = []

    for fon_kodu in fon_kodlari:
        try:
            df = fetcher.get_historical_data(fon_kodu, bas, bit)
            if not df.empty:
                fund_dict[fon_kodu] = df
                # Fon kategorisini al
                try:
                    info = _tefas_api.fon_anlik_bilgi(fon_kodu)
                    if info:
                        fund_kategoriler[fon_kodu] = info.get("fonKategori", "")
                except Exception:
                    pass
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

    # Kullanıcı benchmark seçimi yükle
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
                        risk_free_cum, index=first_df["tarih"], name="TLREF"
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
                            ilk_fiyat = float(hizali.dropna().iloc[0])
                            logger.info("ilk_fiyat: %.4f", ilk_fiyat)
                            
                            getiri = (hizali.astype(float) / ilk_fiyat - 1.0) * 100.0
                            
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

    # Fon benchmarklarını yükle (kategoriden) ve karışım hesapla
    fon_benchmark_series = {}
    fon_benchmark_messages = []
    
    for fon_kodu in fund_dict:
        kategori = fund_kategoriler.get(fon_kodu, "")
        bm_result = get_fund_benchmarks(fon_kodu, kategori)
        fon_benchmark_messages.append(bm_result["message"])
        
        benchmarks = bm_result["benchmarks"]
        if benchmarks:
            tarihler = fund_dict[fon_kodu]["tarih"]
            mix_cum = pd.Series(0.0, index=tarihler, dtype=float)
            
            for bm_info in benchmarks:
                bm_kod = bm_info["kod"]
                agirlik = bm_info["agirlik"]
                
                # Benchmark verisini yükle
                if bm_kod not in benchmark_dict:
                    try:
                        kyd = KydFetcher()
                        kyd_df = kyd.get_historical_data(bm_kod, bas, bit)
                        if not kyd_df.empty:
                            kyd_df = kyd_df.sort_values("tarih").reset_index(drop=True)
                            kyd_map = kyd_df.set_index("tarih")["fiyat"]
                            hizali = kyd_map.reindex(tarihler).ffill()
                            
                            if not hizali.dropna().empty:
                                ilk_fiyat = float(hizali.dropna().iloc[0])
                                getiri = (hizali.astype(float) / ilk_fiyat - 1.0) * 100.0
                                benchmark_dict[bm_kod] = pd.Series(
                                    getiri.values,
                                    index=tarihler.values,
                                    name=bm_kod,
                                )
                    except Exception as exc:
                        logger.warning("Fon benchmark yüklenemedi (%s): %s", bm_kod, exc)
                        continue
                
                if bm_kod in benchmark_dict:
                    bm_series = benchmark_dict[bm_kod]
                    bm_aligned = bm_series.reindex(tarihler).ffill()
                    mix_cum += bm_aligned * agirlik
            
            mix_name = f"{fon_kodu} Benchmark Mix"
            fon_benchmark_series[fon_kodu] = mix_cum.rename(mix_name)

    # Kullanıcı mix benchmark hesaplama
    user_mix_series = None
    user_mix_name = None
    if mix_data and mix_data.get("benchmarks"):
        mix_weights = mix_data["benchmarks"]
        user_mix_name = mix_data.get("name", "Mix Benchmark")
        
        first_df = list(fund_dict.values())[0]
        tarihler = first_df["tarih"]
        
        mix_cum = pd.Series(0.0, index=tarihler, dtype=float)
        
        for bm_kod, weight in mix_weights.items():
            if bm_kod in benchmark_dict:
                bm_series = benchmark_dict[bm_kod]
                bm_aligned = bm_series.reindex(tarihler).ffill()
                mix_cum += bm_aligned * weight
        
        user_mix_series = mix_cum.rename(user_mix_name)

    # Metrik hesaplama - fon benchmark mix'lerini de ekle
    all_mix_series = {}
    all_mix_names = {}
    for fon_kodu, series in fon_benchmark_series.items():
        all_mix_series[fon_kodu] = series
        all_mix_names[fon_kodu] = series.name
    if user_mix_series is not None:
        all_mix_series["user_mix"] = user_mix_series
        all_mix_names["user_mix"] = user_mix_name
    
    metrik_html, tooltip_metrics = _build_metrics_table(
        fund_dict, 
        mix_series=all_mix_series.get("user_mix"), 
        mix_name=all_mix_names.get("user_mix"),
        fon_benchmark_series=fon_benchmark_series,
    )

    # Grafik için mix benchmark (kullanıcı mix'i veya ilk fon benchmark'ı)
    chart_mix = None
    if user_mix_series is not None:
        chart_mix = {"name": user_mix_name, "series": user_mix_series}
    elif fon_benchmark_series:
        first_fon = list(fon_benchmark_series.keys())[0]
        chart_mix = {"name": fon_benchmark_series[first_fon].name, "series": fon_benchmark_series[first_fon]}

    fig = create_price_chart(
        fund_dict=fund_dict,
        benchmark_dict=benchmark_dict,
        title=f"{', '.join(fund_dict.keys())} - Getiri Grafigi",
        metrics=tooltip_metrics,
        mix_benchmark=chart_mix,
    )
    return fig, {"display": "block"}, " | ".join(status_parts), {"display": "none"}, metrik_html


def _build_metrics_table(fund_dict: dict, mix_series: pd.Series = None, mix_name: str = None, fon_benchmark_series: dict = None):
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

    # Risksiz getiri - GUNLUK GETIRI olarak (cumulative degil!)
    rf_daily_returns = pd.Series(dtype=float)
    try:
        tlref_scraper = TLREFScraper()
        try:
            tlref_all = tlref_scraper.from_zip()
        except Exception:
            tlref_all = tlref_scraper.from_csv()

        first_df = list(fund_dict.values())[0]
        fon_tarihler = pd.to_datetime(first_df["tarih"])
        min_t, max_t = fon_tarihler.min(), fon_tarihler.max()

        # Fon tarih araligindaki TLREF verileri
        tlref_filtre = tlref_all[
            (tlref_all["date"] >= min_t) & (tlref_all["date"] <= max_t)
        ].copy()

        if not tlref_filtre.empty:
            # Her gun icin gunluk bilesik getiriyi hesapla
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

            # Kumulatif seriyi gunluk getirilere cevir
            cum_series = pd.Series(daily_rf_list, index=fon_tarihler)
            rf_daily_returns = cum_series.pct_change().fillna(0)
    except Exception as exc:
        logger.warning("TLRF metrik icin alinamadi: %s", exc)

    # Market benchmark (FHISE veya altin fonlari icin ATKAP)
    market_prices = pd.Series(dtype=float)
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
        logger.warning("FHISE metrik icin alinamadi: %s", exc)

    metrics = calculate_fund_metrics(fund_dict, rf_daily_returns, market_prices)

    # Mix benchmark metriklerini ekle
    if mix_series is not None and mix_name:
        try:
            mix_metrics = calculate_mix_metrics(mix_series, rf_daily_returns, market_prices, mix_name)
            if mix_metrics:
                metrics[mix_name] = mix_metrics
        except Exception as exc:
            logger.warning("Mix benchmark metrikleri hesaplanamadi: %s", exc)

    if not metrics:
        return html.Small("Metrik hesaplanamadi", className="text-muted"), {}

    # Benchmark bildirimleri
    notifications = []
    if fon_benchmark_series:
        for fon_kodu, series in fon_benchmark_series.items():
            kategori = ""
            for f in _ALL_FUNDS:
                if f.get("fonKod", "").upper() == fon_kodu:
                    try:
                        info = _tefas_api.fon_anlik_bilgi(fon_kodu)
                        if info:
                            kategori = info.get("fonKategori", "")
                    except Exception:
                        pass
                    break
            
            # Benchmark detaylarını çıkar
            bm_details = []
            from config.benchmark_mapping import get_fallback_benchmarks
            mapping = get_fallback_benchmarks(kategori)
            for kod, agirlik in mapping.items():
                bm_info = benchmark_koda_gore(kod)
                ad = bm_info["ad"] if bm_info else kod
                bm_details.append(f"{ad} (%{agirlik*100:.0f})")
            
            notifications.append(
                dbc.Alert(
                    [
                        html.I(className="bi bi-info-circle me-2"),
                        html.Strong(f"{fon_kodu} Benchmark Mix: "),
                        html.Br(),
                        html.Small(" + ".join(bm_details)),
                        html.Br(),
                        html.Small(
                            f"Kaynak: Fon türüne göre atandı ({kategori}). ",
                            className="text-muted",
                        ),
                        html.Small(
                            "TEFAS API benchmark verisi döndürmemektedir.",
                            className="text-warning",
                            style={"cursor": "help", "title": "TEFAS'ın mevcut API endpoint'leri fon benchmark verisi döndürmemektedir. Benchmarklar fon kategorisine göre atanmaktadır."},
                        ),
                    ],
                    color="info",
                    dismissable=True,
                    className="mb-2 py-2",
                    style={"fontSize": "0.9em"},
                )
            )

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
    from config.constants import METRIC_DESCRIPTIONS

    headers = [html.Th("Fon")]
    tooltip_components = []
    for k_idx, mk in enumerate(metrik_keys):
        desc = METRIC_DESCRIPTIONS.get(mk, "")
        header_id = f"metric-header-{k_idx}"
        if desc:
            headers.append(
                html.Th([
                    mk,
                    html.Span("?", id=header_id, className="ms-1 text-muted", style={"cursor": "help", "fontSize": "0.85em"}),
                ])
            )
            tooltip_components.append(dbc.Tooltip(desc, target=header_id, placement="top"))
        else:
            headers.append(html.Th(mk))

    rows = []
    for fon_kodu, m in metrics.items():
        # Mix benchmark icin unvan arama
        if fon_kodu in fon_unvan_map:
            unvan = fon_unvan_map.get(fon_kodu.upper(), fon_kodu)
            row = [f"{fon_kodu}"]
        else:
            # Mix benchmark
            row = [html.Strong(fon_kodu)]
        
        for k in metrik_keys:
            val = m.get(k, "-")
            if val == "-":
                row.append("-")
            else:
                row.append(f"{val}")
        rows.append(row)

    table_container = html.Div(
        notifications + [
            dbc.Table(
                [
                    html.Thead(html.Tr(headers)),
                    html.Tbody([html.Tr([html.Td(c) for c in r]) for r in rows]),
                ],
                striped=True,
                bordered=True,
                hover=True,
                size="sm",
                responsive=True,
            ),
        ] + tooltip_components
    )
    return table_container, metrics


@callback(
    Output("mix-modal", "is_open"),
    Input("open-mix-modal-btn", "n_clicks"),
    Input("cancel-mix-btn", "n_clicks"),
    Input("create-mix-btn", "n_clicks"),
    State("mix-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_mix_modal(open_click, cancel_click, create_click, is_open):
    if dash.callback_context.triggered_id == "open-mix-modal-btn":
        return True
    return False


@callback(
    Output("mix-benchmark-inputs", "children"),
    Input("open-mix-modal-btn", "n_clicks"),
    State("benchmark-dropdown", "value"),
    prevent_initial_call=True,
)
def build_mix_inputs(open_click, selected_benchmarks):
    if not selected_benchmarks or len(selected_benchmarks) < 2:
        return html.P("En az 2 benchmark seçmelisiniz.", className="text-danger")
    
    inputs = []
    for bm in selected_benchmarks:
        bm_info = benchmark_koda_gore(bm)
        label = bm_info["ad"] if bm_info else bm
        inputs.append(
            dbc.Row(
                [
                    dbc.Col(html.Label(label, className="fw-bold"), xs=8),
                    dbc.Col(
                        dbc.Input(
                            id={"type": "mix-weight-input", "index": bm},
                            type="number",
                            placeholder="%",
                            min=0,
                            max=100,
                            step=1,
                            className="w-100",
                        ),
                        xs=4,
                    ),
                ],
                className="mb-2 align-items-center",
            )
        )
    return inputs


@callback(
    Output("mix-weight-total", "children"),
    Input({"type": "mix-weight-input", "index": ALL}, "value"),
    prevent_initial_call=False,
)
def update_weight_total(weight_values):
    total = sum(v for v in weight_values if v is not None)
    return html.Span(f"Toplam: {total:.0f}%", className="text-muted")


@callback(
    Output("mix-benchmark-store", "data"),
    Input("create-mix-btn", "n_clicks"),
    State("benchmark-dropdown", "value"),
    State({"type": "mix-weight-input", "index": ALL}, "value"),
    State({"type": "mix-weight-input", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def create_mix_benchmark(create_click, selected_benchmarks, weight_values, weight_ids):
    if not create_click or not selected_benchmarks:
        return None
    
    weights = {}
    total = 0
    
    for i, input_id in enumerate(weight_ids):
        bm = input_id["index"]
        w = weight_values[i] if i < len(weight_values) else None
        if w is not None and w > 0:
            weights[bm] = w
            total += w
    
    if total == 0:
        return None
    
    normalized = {bm: w / total for bm, w in weights.items()}
    
    mix_parts = []
    for bm, w in normalized.items():
        short_label = bm
        mix_parts.append(f"{short_label} %{w*100:.0f}")
    
    mix_name = f"Mix ({', '.join(mix_parts)})"
    
    return {
        "benchmarks": normalized,
        "name": mix_name,
    }
