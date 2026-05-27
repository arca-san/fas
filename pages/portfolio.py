#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portföy Analizi — birden çok dönemde fon metriklerini karşılaştırma.
"""

import dash
from dash import html, dcc, callback, Output, Input, State, ALL, ClientsideFunction
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from data.fetchers import _tefas_api
from data.fetchers.tefas_fetcher import TefasFetcher
from components.metrics import (
    calculate_fund_metrics,
    calculate_mix_metrics,
    get_fund_benchmarks,
)
from components.charts import create_price_chart, create_efficient_frontier_chart, create_portfolio_distribution_chart, create_monte_carlo_chart, create_backtest_chart, create_rebalancing_chart, create_goal_projection_chart, create_style_drift_chart, create_factor_loading_chart, create_stress_test_chart, create_brinson_chart
from components.optimizer import (
    compute_covariance_matrix, compute_expected_returns,
    max_sharpe_portfolio, min_variance_portfolio, risk_parity_portfolio,
    efficient_frontier_points, simulate_rebalancing, walk_forward_backtest,
    monte_carlo_simulation, monte_carlo_stats, goal_based_projection,
)
from components.attribution import (
    te_decomposition, fama_french_regression, construct_simple_factors,
    rbsa_analysis, style_drift_tracking, run_stress_test_batch,
    brinson_attribution,
)
from config.logger import get_logger
from config.benchmarks import benchmark_koda_gore, all_benchmark_options, get_benchmark_data
from config.constants import (
    METRIC_SHARPE,
    METRIC_SORTINO,
    METRIC_TOTAL_RETURN,
    METRIC_ANNUALIZED_RETURN,
    METRIC_VOLATILITY,
    METRIC_MAX_DRAWDOWN,
    METRIC_DOWNSIDE_VOL,
    METRIC_INFORMATION_RATIO,
    METRIC_BETA,
    METRIC_ALPHA,
    METRIC_TREYNOR,
    METRIC_DESCRIPTIONS,
)
from data.dao import save_portfolio, list_portfolios, delete_portfolio
from flask_login import current_user
from tlref_scraper import TLREFScraper, TLREFConverter

logger = get_logger(__name__)
dash.register_page(__name__, path="/portfolio")

# ── Tüm fonları yükle ────────────────────────────────────────────────
try:
    _ALL_FUNDS = _tefas_api.get_all_fonlar()
    logger.info("Tum fonlar yuklendi: %s adet", len(_ALL_FUNDS))
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

_TLREF_OPTION = {"label": "TLREF (Risksiz Getiri)", "value": "TLREF"}
_BENCHMARK_OPTIONS = [_TLREF_OPTION] + all_benchmark_options()

# ── Dönem tanımları ──────────────────────────────────────────────────
PERIOD_DEFS = {
    "1m":  {"label": "1 Ay",                 "days": 30,     "is_ytd": False},
    "3m":  {"label": "3 Ay",                 "days": 90,     "is_ytd": False},
    "6m":  {"label": "6 Ay",                 "days": 180,    "is_ytd": False},
    "ytd": {"label": "Yılbaşından Bu Yana",  "days": None,   "is_ytd": True},
    "1y":  {"label": "1 Yıl",                "days": 365,    "is_ytd": False},
    "3y":  {"label": "3 Yıl",                "days": 1095,   "is_ytd": False},
    "5y":  {"label": "5 Yıl",                "days": 1825,   "is_ytd": False},
}

PERIOD_ORDER = ["1m", "3m", "6m", "ytd", "1y", "3y", "5y"]
_DEFAULT_PERIODS = ["3m", "6m", "1y"]

# Özet tablosunda gösterilecek metrikler
SUMMARY_METRICS_ORDER = [
    METRIC_SHARPE,
    METRIC_TOTAL_RETURN,
    METRIC_ANNUALIZED_RETURN,
    METRIC_VOLATILITY,
    METRIC_MAX_DRAWDOWN,
    METRIC_SORTINO,
    METRIC_INFORMATION_RATIO,
]

# Metrik yönü: True = yüksek iyi, False = düşük iyi
METRIC_DIRECTION = {
    METRIC_SHARPE: True,
    METRIC_SORTINO: True,
    METRIC_TOTAL_RETURN: True,
    METRIC_ANNUALIZED_RETURN: True,
    METRIC_INFORMATION_RATIO: True,
    METRIC_ALPHA: True,
    METRIC_TREYNOR: True,
    METRIC_VOLATILITY: False,
    METRIC_DOWNSIDE_VOL: False,
    METRIC_MAX_DRAWDOWN: False,
    METRIC_BETA: False,
}


def _get_period_dates(period_key: str, end_date: date):
    p = PERIOD_DEFS[period_key]
    if p["is_ytd"]:
        start = date(end_date.year, 1, 1)
    else:
        start = end_date - timedelta(days=p["days"])
    return start, end_date


# ── Mix Benchmark Modal ──────────────────────────────────────────────
mix_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Mix Benchmark Oluştur")),
        dbc.ModalBody([
            html.P("Benchmarklar için ağırlık atayın (toplam otomatik %100'e normalize edilir):"),
            html.Div(id="pf-mix-benchmark-inputs"),
            html.Hr(),
            html.Div(id="pf-mix-weight-total", className="mt-2 fw-bold"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Oluştur", id="pf-create-mix-btn", color="primary", className="me-2"),
            dbc.Button("İptal", id="pf-cancel-mix-btn", color="secondary"),
        ]),
    ],
    id="pf-mix-modal",
    size="md",
    is_open=False,
)


# ── Sayfa Layout ─────────────────────────────────────────────────────
layout = dbc.Container([
    dcc.Store(id="pf-mix-store"),
    dcc.Store(id="pf-results-store"),

    html.H3("Portföy Analizi", className="mb-3"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Portföy", className="card-title"),
                    dmc.MultiSelect(
                        id="pf-fund-select",
                        label="Fon kodu veya ünvanı yazın",
                        placeholder="Fon seçin...",
                        searchable=True,
                        clearable=True,
                        data=[
                            {"value": f.get("fonKod", ""),
                             "label": f"{f.get('fonKod', '')} - {f.get('unvan', '')}"}
                            for f in _ALL_FUNDS if f.get("fonKod")
                        ],
                    ),
                ])
            ], className="h-100 mb-3"),
        ], xs=12, md=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Benchmark(lar)", className="card-title"),
                dmc.MultiSelect(
                    id="pf-benchmark-select",
                    data=_BENCHMARK_OPTIONS,
                    placeholder="Benchmark seçin...",
                    searchable=True,
                    clearable=True,
                ),
                    dbc.Button(
                        "Mix Benchmark Oluştur",
                        id="pf-open-mix-btn",
                        color="secondary",
                        size="sm",
                        className="mt-2 w-100",
                    ),
                ])
            ], className="h-100 mb-3"),
        ], xs=12, md=4),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Dönemler", className="card-title"),
                    dbc.Checklist(
                        id="pf-periods",
                        options=[
                            {"label": "1 Ay", "value": "1m"},
                            {"label": "3 Ay", "value": "3m"},
                            {"label": "6 Ay", "value": "6m"},
                            {"label": "Yılbaşından Bu Yana", "value": "ytd"},
                            {"label": "1 Yıl", "value": "1y"},
                            {"label": "3 Yıl", "value": "3y"},
                            {"label": "5 Yıl", "value": "5y"},
                        ],
                        value=_DEFAULT_PERIODS,
                        inline=True,
                        switch=True,
                    ),
                    dbc.Button(
                        "Analiz Et",
                        id="pf-analiz-btn",
                        color="primary",
                        className="mt-4 w-100",
                    ),
                    html.Div(id="pf-analiz-status", className="mt-2 text-info"),
                    html.Small(
                        "TEFAS'tan veri aliniyor, bu islem 10-30 saniye surebilir.",
                        className="text-muted d-block mt-1",
                    ),
                ])
            ], className="h-100 mb-3"),
        ], xs=12, md=4),
    ], className="align-items-stretch"),

    html.Div(id="pf-portfolio-actions", className="mb-2"),
    # Kayıtlı portföy yükleme (ilk açılışta gizli, sadece giriş yapmış kullanıcılar)

    html.Div(id="pf-results", style={"display": "none"}, children=[
        dbc.Tabs([
            dbc.Tab(
                label="Özet",
                tab_id="pf-tab-ozet",
                children=[
                    html.Div([
                        html.H5("Metrik Karşılaştırma", className="mt-2"),
                        dcc.Dropdown(
                            id="pf-metric-selector",
                            options=[{"label": m, "value": m} for m in SUMMARY_METRICS_ORDER],
                            value=METRIC_SHARPE,
                            clearable=False,
                            className="mb-3",
                            style={"maxWidth": "400px"},
                        ),
                        dcc.Loading(id="loading-pf-summary", type="default", children=html.Div(id="pf-summary-table")),
                    ])
                ],
            ),
            dbc.Tab(
                label="Dönem Detayları",
                tab_id="pf-tab-detay",
                children=[
                    dcc.Loading(id="loading-pf-detail", type="default", children=dbc.Tabs(id="pf-period-detail-tabs")),
                ],
            ),
            dbc.Tab(
                label="Grafik",
                tab_id="pf-tab-chart",
                children=[
                    dcc.Loading(
                        id="pf-loading-chart",
                        type="default",
                        children=dcc.Graph(id="pf-chart", config={"displayModeBar": True}),
                    ),
                ],
            ),
            dbc.Tab(
                label="Optimizasyon",
                tab_id="pf-tab-optimizasyon",
                children=[
                    dbc.Row([
                        dbc.Col([
                            dbc.Card(dbc.CardBody([
                                html.H5("Optimizasyon Ayarları", className="card-title mb-3"),
                                dbc.RadioItems(
                                    id="pf-optim-method",
                                    options=[
                                        {"label": "Max Sharpe", "value": "sharpe"},
                                        {"label": "Min Varyans", "value": "minvar"},
                                        {"label": "Risk Parity (ERC)", "value": "riskparity"},
                                    ],
                                    value="sharpe",
                                    className="mb-3",
                                ),
                                html.Label("Max Tek Fon Ağırlığı (%)", className="fw-semibold"),
                                dbc.Input(id="pf-optim-maxw", type="number", value=40, min=1, max=100, className="mb-2"),
                                html.Label("Min Tek Fon Ağırlığı (%)", className="fw-semibold"),
                                dbc.Input(id="pf-optim-minw", type="number", value=1, min=0, max=50, className="mb-3"),
                                dbc.Button("Optimize Et", id="pf-optim-btn", color="primary", className="w-100"),
                                html.Div(id="pf-optim-status", className="mt-2 text-info"),
                            ])),
                        ], xs=12, md=4),
                        dbc.Col([
                            dcc.Loading(html.Div([
                                html.Div(id="pf-optim-sonuc"),
                                dcc.Graph(id="pf-ef-grafik", config={"displayModeBar": False}),
                                dcc.Graph(id="pf-optim-pie", config={"displayModeBar": False}),
                            ]))
                        ], xs=12, md=8),
                    ]),
                    html.Hr(),
                    html.H5("Rebalancing & Backtest", className="mt-4"),
                    dcc.Loading(html.Div([
                        dcc.Graph(id="pf-backtest-chart", config={"displayModeBar": False}),
                        dcc.Graph(id="pf-mc-chart", config={"displayModeBar": False}),
                        html.Div(id="pf-mc-stats"),
                    ])),
                ],
            ),
            dbc.Tab(
                label="Atıf & Faktör",
                tab_id="pf-tab-attribution",
                children=[
                    dcc.Loading(html.Div([
                        html.Div(id="pf-te-sonuc"),
                        dcc.Graph(id="pf-ff-chart", config={"displayModeBar": False}),
                        dcc.Graph(id="pf-style-drift-chart", config={"displayModeBar": False}),
                        dcc.Graph(id="pf-brinson-chart", config={"displayModeBar": False}),
                    ])),
                ],
            ),
            dbc.Tab(
                label="Stres Testi",
                tab_id="pf-tab-stress",
                children=[
                    dcc.Loading(html.Div([
                        dcc.Graph(id="pf-stress-chart", config={"displayModeBar": False}),
                        html.Div(id="pf-stress-table"),
                    ])),
                ],
            ),
        ], active_tab="pf-tab-ozet"),
    ]),

    mix_modal,
], fluid=True)


# ── Callback: uppercase search ───────────────────────────────────────
@callback(
    Output("pf-fund-select", "searchValue"),
    Input("pf-fund-select", "searchValue"),
    prevent_initial_call=True,
)
def uppercase_search(val):
    if val and val != val.upper():
        return val.upper()
    return val


# ── Callback: mix modal ──────────────────────────────────────────────
@callback(
    Output("pf-mix-modal", "is_open"),
    Input("pf-open-mix-btn", "n_clicks"),
    Input("pf-cancel-mix-btn", "n_clicks"),
    Input("pf-create-mix-btn", "n_clicks"),
    State("pf-mix-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_mix_modal(open_click, cancel_click, create_click, is_open):
    if dash.callback_context.triggered_id == "pf-open-mix-btn":
        return True
    return False


@callback(
    Output("pf-mix-benchmark-inputs", "children"),
    Input("pf-open-mix-btn", "n_clicks"),
    State("pf-benchmark-select", "value"),
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
            dbc.Row([
                dbc.Col(html.Label(label, className="fw-bold"), xs=8),
                dbc.Col(
                    dbc.Input(
                        id={"type": "pf-mix-weight", "index": bm},
                        type="number",
                        placeholder="%",
                        min=0, max=100, step=1,
                        className="w-100",
                    ),
                    xs=4,
                ),
            ], className="mb-2 align-items-center")
        )
    return inputs


@callback(
    Output("pf-mix-weight-total", "children"),
    Input({"type": "pf-mix-weight", "index": ALL}, "value"),
    prevent_initial_call=False,
)
def update_weight_total(weight_values):
    total = sum(v for v in weight_values if v is not None)
    return html.Span(f"Toplam: {total:.0f}%", className="text-muted")


@callback(
    Output("pf-mix-store", "data"),
    Input("pf-create-mix-btn", "n_clicks"),
    State("pf-benchmark-select", "value"),
    State({"type": "pf-mix-weight", "index": ALL}, "value"),
    State({"type": "pf-mix-weight", "index": ALL}, "id"),
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
    mix_parts = [f"{bm} %{w*100:.0f}" for bm, w in normalized.items()]
    return {
        "benchmarks": normalized,
        "name": f"Mix ({', '.join(mix_parts)})",
    }


# ── Helpers: TLREF / Market verisi ───────────────────────────────────
def _load_tlref_daily_returns(tarih_series: pd.Series) -> pd.Series:
    """TLREF verisini yukle ve gunluk bilesik getiri serisi olarak dondur."""
    try:
        tlref_scraper = TLREFScraper()
        try:
            tlref_all = tlref_scraper.from_zip()
        except Exception:
            tlref_all = tlref_scraper.from_csv()

        fon_tarihler = pd.to_datetime(tarih_series)
        min_t, max_t = fon_tarihler.min(), fon_tarihler.max()
        tlref_filtre = tlref_all[
            (tlref_all["date"] >= min_t) & (tlref_all["date"] <= max_t)
        ].copy()

        if tlref_filtre.empty:
            return pd.Series(dtype=float)

        tlref_map = dict(zip(tlref_filtre["date"].dt.date, tlref_filtre["value"]))
        daily_rf_list = []
        onceki_tarih = None
        carpim = 1.0

        for tarih in fon_tarihler:
            t = tarih.date() if hasattr(tarih, "date") else tarih
            deger = tlref_map.get(t)
            if deger is not None:
                daily_r = TLREFConverter.daily_compound(deger) / 100.0
                gap = 1 if onceki_tarih is None else max((t - onceki_tarih).days, 1)
                carpim *= (1.0 + daily_r) ** gap
            onceki_tarih = t
            daily_rf_list.append(carpim)

        cum_series = pd.Series(daily_rf_list, index=fon_tarihler)
        return cum_series.pct_change().fillna(0)
    except Exception as exc:
        logger.warning("TLREF yuklenemedi: %s", exc)
        return pd.Series(dtype=float)


def _load_market_prices(tarih_series: pd.Series, fon_kodlari: list) -> pd.Series:
    """Market benchmark fiyatlarini yukle (altin fonlari icin ATKAP, diger FHISE)."""
    fon_unvan_map = {}
    for f in _ALL_FUNDS:
        fon_unvan_map[f.get("fonKod", "").upper()] = (f.get("unvan", "") or "").lower()

    gold_keywords = ["altin", "gumus", "kiymetli maden", "precious metal", "gold", "silver", "emtia"]
    use_atkap = any(
        any(kw in fon_unvan_map.get(k.upper(), "") for kw in gold_keywords)
        for k in fon_kodlari
    )
    symbol = "ATKAP" if use_atkap else "FHISE"

    try:
        fon_tarihler = pd.to_datetime(tarih_series)
        end = date.today()
        start = end - timedelta(days=365 * 5)
        df = get_benchmark_data(symbol, start, end)
        if not df.empty:
            market_prices = pd.Series(
                df["fiyat"].values,
                index=pd.to_datetime(df["tarih"]),
                name=symbol,
            )
            return market_prices
    except Exception as exc:
        logger.warning("Market (%s) yuklenemedi: %s", symbol, exc)
    return pd.Series(dtype=float)


def _load_benchmark_series(
    bm_kod: str, bas: date, bit: date, ref_tarihler: pd.Series,
) -> pd.Series:
    """Tek bir benchmark serisini yuzde getiri olarak yukle (0 baslangicli)."""
    try:
        df = get_benchmark_data(bm_kod, bas, bit)
        if df.empty:
            return None
        df = df.sort_values("tarih").reset_index(drop=True)
        kyd_map = df.set_index("tarih")["fiyat"]
        hizali = kyd_map.reindex(ref_tarihler).ffill()
        if hizali.dropna().empty:
            return None
        ilk_fiyat = float(hizali.dropna().iloc[0])
        getiri = (hizali.astype(float) / ilk_fiyat - 1.0) * 100.0
        return pd.Series(getiri.values, index=ref_tarihler.values, name=bm_kod)
    except Exception as exc:
        logger.warning("Benchmark yuklenemedi (%s): %s", bm_kod, exc)
        return None


# ── Helper: summary tablosu ──────────────────────────────────────────
def _build_summary_table(results_data: dict, selected_metric: str) -> html.Div:
    """Fonlar × dönemler matrisi, seçilen metrik değeri ile."""
    periods = results_data.get("periods", [])
    fund_codes = results_data.get("fund_codes", [])
    mix_name = results_data.get("mix_name")

    # Sıralı period listesi
    sorted_periods = sorted(periods, key=lambda p: PERIOD_ORDER.index(p["value"]))

    # Kullanici benchmark etiketlerini topla
    user_bm_labels = set()
    for p in sorted_periods:
        for bm_label in p.get("user_benchmark_metrics", {}):
            user_bm_labels.add(bm_label)

    # Tüm satır etiketleri (fonlar + varsa mix + benchmarklar)
    row_labels = list(fund_codes)
    has_mix = mix_name and any(p.get("mix_metrics") for p in sorted_periods)
    if has_mix:
        row_labels.append(mix_name)
    row_labels.extend(sorted(user_bm_labels))

    # Metric değerlerini topla
    values = {}  # {period_value: {fund_code: value}}
    for p in sorted_periods:
        pv = p["value"]
        values[pv] = {}
        for kod in fund_codes:
            m = p["metrics"].get(kod, {})
            values[pv][kod] = m.get(selected_metric, None)
        if has_mix and p.get("mix_metrics"):
            values[pv][mix_name] = p["mix_metrics"].get(selected_metric, None)
        for bm_label, bm_m in p.get("user_benchmark_metrics", {}).items():
            values[pv][bm_label] = bm_m.get(selected_metric, None)

    # Kolon bazında en iyi/en kötü bul
    best_in_col = {}
    worst_in_col = {}
    direction = METRIC_DIRECTION.get(selected_metric, True)
    for p in sorted_periods:
        pv = p["value"]
        vals = [(k, v) for k, v in values[pv].items() if v is not None]
        if vals:
            if direction:
                best_in_col[pv] = max(vals, key=lambda x: x[1])[0]
                worst_in_col[pv] = min(vals, key=lambda x: x[1])[0]
            else:
                best_in_col[pv] = min(vals, key=lambda x: x[1])[0]
                worst_in_col[pv] = max(vals, key=lambda x: x[1])[0]

    headers = [html.Th("Fon / Dönem")]
    for p in sorted_periods:
        headers.append(html.Th(PERIOD_DEFS[p["value"]]["label"], style={"textAlign": "center"}))

    rows = []
    for label in row_labels:
        is_mix = label == mix_name
        is_bm = label in user_bm_labels
        if is_mix:
            label_el = html.Strong(label)
        elif is_bm:
            label_el = html.Span(label, style={"fontStyle": "italic", "color": "#555"})
        else:
            label_el = label
        cells = [label_el]
        for p in sorted_periods:
            pv = p["value"]
            val = values[pv].get(label)
            if val is None:
                cells.append(html.Td("-", style={"textAlign": "center", "color": "#ccc"}))
            else:
                style = {"textAlign": "center"}
                if label == best_in_col.get(pv):
                    style["backgroundColor"] = "#d4edda"
                    style["fontWeight"] = "bold"
                elif label == worst_in_col.get(pv):
                    style["backgroundColor"] = "#f8d7da"
                cells.append(html.Td(f"{val}", style=style))
        rows.append(html.Tr(cells))

    # Alt satır: en iyi fon ismi
    best_row_cells = [html.Strong("En İyi", style={"color": "#155724"})]
    for p in sorted_periods:
        pv = p["value"]
        best = best_in_col.get(pv)
        best_label = f"⭐ {best}" if best else "-"
        best_row_cells.append(html.Td(best_label, style={"textAlign": "center", "color": "#155724", "fontWeight": "bold"}))
    rows.append(html.Tr(best_row_cells))

    desc = METRIC_DESCRIPTIONS.get(selected_metric, "")
    desc_el = html.Small(desc, className="text-muted d-block mb-2") if desc else ""

    return html.Div([
        desc_el,
        dbc.Table(
            [html.Thead(html.Tr(headers)), html.Tbody(rows)],
            striped=True, bordered=True, hover=True, size="sm", responsive=True,
        ),
    ])


# ── Helper: detail tablolari ─────────────────────────────────────────
def _build_detail_tab_content(
    period_data: dict,
    fon_unvan_map: dict,
    fon_benchmark_series: dict,
    fon_benchmark_sources: dict,
) -> html.Div:
    """Bir donem icin detayli metrik tablosu + benchmark uyarilari."""
    metrics = period_data["metrics"]
    mix_metrics = period_data.get("mix_metrics")

    from config.constants import METRIC_DESCRIPTIONS

    metric_keys = [
        METRIC_TOTAL_RETURN, METRIC_ANNUALIZED_RETURN,
        METRIC_VOLATILITY, METRIC_MAX_DRAWDOWN,
        METRIC_SHARPE, METRIC_SORTINO,
        METRIC_BETA, METRIC_INFORMATION_RATIO,
    ]

    headers = [html.Th("Fon")]
    tooltip_components = []
    for k_idx, mk in enumerate(metric_keys):
        desc = METRIC_DESCRIPTIONS.get(mk, "")
        header_id = f"pf-detail-hdr-{period_data['value']}-{k_idx}"
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
    for kod, m in metrics.items():
        unvan = fon_unvan_map.get(kod.upper(), kod)
        row = [unvan]
        for k in metric_keys:
            val = m.get(k, "-")
            row.append(f"{val}" if val != "-" else "-")
        rows.append(html.Tr([html.Td(c) for c in row]))

    # Fon benchmark mix satirlari
    bm_mix_metrics = period_data.get("benchmark_mix_metrics", {})
    for fon_kodu, bm_m in bm_mix_metrics.items():
        row = [html.Span(f"{fon_kodu} BM", style={"fontStyle": "italic", "color": "#555"})]
        for k in metric_keys:
            val = bm_m.get(k, "-")
            row.append(f"{val}" if val != "-" else "-")
        rows.append(html.Tr([html.Td(c) for c in row]))

    # Kullanici mix benchmark varsa satir ekle
    if mix_metrics:
        mix_name = period_data.get("mix_name", "Mix Benchmark")
        row = [html.Strong(mix_name)]
        for k in metric_keys:
            val = mix_metrics.get(k, "-")
            row.append(html.Span(f"{val}", style={"fontWeight": "bold"}) if val != "-" else "-")
        rows.append(html.Tr([html.Td(c) for c in row]))

    # Kullanici secimi benchmark satirlari
    user_benchmark_metrics = period_data.get("user_benchmark_metrics", {})
    for bm_ad, bm_m in user_benchmark_metrics.items():
        row = [html.Span(bm_ad, style={"fontStyle": "italic", "color": "#555"})]
        for k in metric_keys:
            val = bm_m.get(k, "-")
            row.append(f"{val}" if val != "-" else "-")
        rows.append(html.Tr([html.Td(c) for c in row]))

    # Benchmark uyarilari
    notifications = []
    if fon_benchmark_sources:
        for fon_kodu, source in fon_benchmark_sources.items():
            if fon_kodu not in metrics:
                continue
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

            bm_details = []
            from config.benchmark_mapping import get_fallback_benchmarks
            mapping = get_fallback_benchmarks(kategori)
            for kod, agirlik in mapping.items():
                bm_info = benchmark_koda_gore(kod)
                ad = bm_info["ad"] if bm_info else kod
                bm_details.append(f"{ad} (%{agirlik*100:.0f})")

            if source == "kap_cache":
                color = "success"
                source_msg = "KAP.org.tr cache'den okundu."
            elif source == "kap_scraping":
                color = "success"
                source_msg = "KAP.org.tr'den canlı çekildi."
            else:
                color = "info"
                source_msg = f"Fon turune gore atandi ({kategori})."

            notifications.append(
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    html.Strong(f"{fon_kodu} Benchmark Mix: "),
                    html.Br(),
                    html.Small(" + ".join(bm_details)),
                    html.Br(),
                    html.Small(f"Kaynak: {source_msg}", className="text-muted"),
                ], color=color, dismissable=True, className="mb-2 py-2",
                   style={"fontSize": "0.9em"})
            )

    return html.Div(
        notifications + [
            dbc.Table(
                [html.Thead(html.Tr(headers)), html.Tbody(rows)],
                striped=True, bordered=True, hover=True, size="sm", responsive=True,
            ),
        ] + tooltip_components
    )


# ── Helper: fon benchmark mix serileri ───────────────────────────────
def _compute_fund_benchmark_series(
    fund_dict: dict,
    fund_kategoriler: dict,
    bas: date,
    bit: date,
    benchmark_dict: dict,
) -> tuple:
    """Her fon icin benchmark mix serisini hesapla."""
    fon_benchmark_series = {}
    fon_benchmark_sources = {}
    auto_bm_codes = set()

    for fon_kodu in fund_dict:
        kategori = fund_kategoriler.get(fon_kodu, "")
        bm_result = get_fund_benchmarks(fon_kodu, kategori)
        fon_benchmark_sources[fon_kodu] = bm_result["source"]
        benchmarks = bm_result["benchmarks"]

        if not benchmarks:
            continue

        for bm_info in benchmarks:
            auto_bm_codes.add(bm_info["kod"])

        tarihler = fund_dict[fon_kodu]["tarih"]
        mix_cum = pd.Series(0.0, index=tarihler, dtype=float)

        for bm_info in benchmarks:
            bm_kod = bm_info["kod"]
            agirlik = bm_info["agirlik"]

            if bm_kod not in benchmark_dict:
                bm_series = _load_benchmark_series(bm_kod, bas, bit, tarihler)
                if bm_series is not None:
                    benchmark_dict[bm_kod] = bm_series

            if bm_kod in benchmark_dict:
                bm_series = benchmark_dict[bm_kod]
                bm_aligned = bm_series.reindex(tarihler).ffill()
                mix_cum += bm_aligned * agirlik

        mix_name = f"{fon_kodu} Benchmark Mix"
        fon_benchmark_series[fon_kodu] = mix_cum.rename(mix_name)

    return fon_benchmark_series, fon_benchmark_sources, auto_bm_codes


# ── Callback: ana analiz ─────────────────────────────────────────────
@callback(
    Output("pf-results", "style"),
    Output("pf-results-store", "data"),
    Output("pf-period-detail-tabs", "children"),
    Output("pf-chart", "figure"),
    Output("pf-analiz-status", "children"),
    Input("pf-analiz-btn", "n_clicks"),
    State("pf-fund-select", "value"),
    State("pf-benchmark-select", "value"),
    State("pf-periods", "value"),
    State("pf-mix-store", "data"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def run_portfolio_analysis(n_clicks, fon_kodlari, benchmark_values, period_values, mix_data, theme=None):
    fon_kodlari = [k.upper() for k in (fon_kodlari or [])]
    if not fon_kodlari:
        return {"display": "none"}, dash.no_update, [], go.Figure(), "Lutfen en az bir fon secin."

    if not period_values or len(period_values) < 1:
        return {"display": "none"}, dash.no_update, [], go.Figure(), "En az bir dönem seçin."

    try:
        # En uzun donemi bul
        max_days = 0
        for p in period_values:
            defn = PERIOD_DEFS[p]
            if not defn["is_ytd"] and defn["days"] > max_days:
                max_days = defn["days"]

        end_date = date.today()
        ytd_selected = any(PERIOD_DEFS[p]["is_ytd"] for p in period_values)

        if ytd_selected:
            ytd_start = date(end_date.year, 1, 1)
            overall_start = ytd_start
            if max_days > 0:
                from_max = end_date - timedelta(days=max_days)
                overall_start = min(from_max, overall_start)
        else:
            overall_start = end_date - timedelta(days=max_days)

        bas = overall_start
        bit = end_date

        # Fon verilerini paralel cek
        fetcher = TefasFetcher()
        fund_dict = {}
        fund_kategoriler = {}
        hata_list = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetcher.get_historical_data, f, bas, bit): f for f in fon_kodlari}
            for future in as_completed(futures):
                fon_kodu = futures[future]
                try:
                    df = future.result()
                    if not df.empty:
                        fund_dict[fon_kodu] = df
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
            return {"display": "none"}, dash.no_update, [], go.Figure(), \
                   " | ".join(hata_list) if hata_list else "Veri bulunamadi."

        status_parts = [f"{len(fund_dict)} fon, {min(len(d) for d in fund_dict.values())} gun"]

        # Benchmark verilerini yukle
        benchmark_dict = {}
        benchmark_list = benchmark_values or []

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
                                gap = 1 if onceki_tarih is None else (t - onceki_tarih).days
                                carpim *= (1.0 + daily_r) ** gap
                            risk_free_cum.append(carpim)
                            onceki_tarih = t
                        benchmark_dict["TLREF"] = pd.Series(
                            risk_free_cum, index=first_df["tarih"], name="TLREF",
                        ) * 100.0 - 100.0
                    toplam_getiri = (risk_free_cum[-1] - 1.0) * 100.0 if risk_free_cum else 0
                    status_parts.append(f"TLREF: Kum: %{toplam_getiri:.1f}")
                except Exception as exc:
                    logger.warning("TLREF cekilemedi: %s", exc)
                    status_parts.append(f"TLREF alinamadi: {exc}")
            else:
                bm_series = _load_benchmark_series(bm, bas, bit, list(fund_dict.values())[0]["tarih"])
                if bm_series is not None:
                    endeks_bilgi = benchmark_koda_gore(bm)
                    endeks_adi = endeks_bilgi["ad"] if endeks_bilgi else bm
                    bm_series.name = endeks_adi
                    benchmark_dict[bm] = bm_series
                    status_parts.append(f"{endeks_adi}: {bm_series.notna().sum()} ortak gun")

        # Fon benchmark mix serileri
        fon_benchmark_series, fon_benchmark_sources, auto_bm_codes = _compute_fund_benchmark_series(
            fund_dict, fund_kategoriler, bas, bit, benchmark_dict,
        )

        # Eger bir kullanıcı benchmark'ı, herhangi bir fonun benchmark mix'i ile birebir aynıysa (değer bazında)
        # onu benchmark_dict'ten çıkaralım ki grafikte tekrar çizilmesin.
        filtered_benchmark_dict = {}
        for bm_kod, bm_series in benchmark_dict.items():
            is_duplicate = False
            for fon_kodu, mix_series in fon_benchmark_series.items():
                common_idx = bm_series.index.intersection(mix_series.index)
                if len(common_idx) > 0:
                    diff = (bm_series.loc[common_idx] - mix_series.loc[common_idx]).abs().max()
                    if diff < 0.05:  # Yüzde bazında 0.05% fark (birebir aynı)
                        is_duplicate = True
                        logger.info("Benchmark %s, %s fonunun benchmark mix'i ile birebir ayni oldugu icin filtrelendi.", bm_kod, fon_kodu)
                        break
            if not is_duplicate:
                filtered_benchmark_dict[bm_kod] = bm_series
        benchmark_dict = filtered_benchmark_dict

        # Kullanici mix benchmark
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

        # TLREF + Market benchmark (metrik hesaplama icin)
        first_df = list(fund_dict.values())[0]
        rf_daily_returns = _load_tlref_daily_returns(first_df["tarih"])
        market_prices = _load_market_prices(first_df["tarih"], fon_kodlari)

        # Her donem icin metrik hesapla
        periods_data = []
        for p in period_values:
            p_start, p_end = _get_period_dates(p, end_date)
            p_label = PERIOD_DEFS[p]["label"]

            period_fund_dict = {}
            for kod, df in fund_dict.items():
                mask = (pd.to_datetime(df["tarih"]) >= pd.Timestamp(p_start)) & \
                       (pd.to_datetime(df["tarih"]) <= pd.Timestamp(p_end))
                subset = df[mask].copy()
                if len(subset) >= 3:
                    period_fund_dict[kod] = subset

            if not period_fund_dict:
                continue

            idx = pd.to_datetime(list(period_fund_dict.values())[0]["tarih"])
            rf_subset = rf_daily_returns.reindex(idx).fillna(0) if not rf_daily_returns.empty else pd.Series(0, index=idx)

            metrics = calculate_fund_metrics(period_fund_dict, rf_subset, market_prices)

            mix_metrics = None
            if user_mix_series is not None:
                mix_subset_values = user_mix_series.reindex(idx).ffill()
                mix_metrics = calculate_mix_metrics(mix_subset_values, rf_subset, market_prices, user_mix_name)

            # Her fonun benchmark mix'i icin metrik hesapla
            benchmark_mix_metrics = {}
            for fon_kodu, bm_series in fon_benchmark_series.items():
                bm_subset = bm_series.reindex(idx).ffill()
                bm_mix_name = bm_series.name if hasattr(bm_series, 'name') else f"{fon_kodu} BM"
                bm_m = calculate_mix_metrics(bm_subset, rf_subset, market_prices, bm_mix_name)
                if bm_m:
                    benchmark_mix_metrics[fon_kodu] = bm_m

            # Kullanici secimi benchmark metrikleri
            user_benchmark_metrics = {}
            for bm_kod, bm_series in benchmark_dict.items():
                if bm_kod == "TLREF":
                    continue
                bm_subset = bm_series.reindex(idx).ffill()
                if bm_subset.dropna().empty:
                    continue
                endeks_bilgi = benchmark_koda_gore(bm_kod)
                bm_ad = endeks_bilgi["ad"] if endeks_bilgi else bm_kod
                bm_m = calculate_mix_metrics(bm_subset, rf_subset, market_prices, bm_ad)
                if bm_m:
                    user_benchmark_metrics[bm_ad] = bm_m

            periods_data.append({
                "value": p,
                "label": p_label,
                "metrics": metrics,
                "mix_metrics": mix_metrics,
                "mix_name": user_mix_name,
                "benchmark_mix_metrics": benchmark_mix_metrics,
                "user_benchmark_metrics": user_benchmark_metrics,
            })

        # sonuclari hazirla
        fon_unvan_map = {}
        for f in _ALL_FUNDS:
            fon_unvan_map[f.get("fonKod", "").upper()] = f.get("unvan", "")

        results_data = {
            "periods": periods_data,
            "fund_codes": list(fund_dict.keys()),
            "mix_name": user_mix_name,
            "fon_unvan_map": fon_unvan_map,
        }

        # Detail tabs
        detail_tabs = []
        for pd_data in periods_data:
            tab_content = _build_detail_tab_content(
                pd_data, fon_unvan_map, fon_benchmark_series, fon_benchmark_sources,
            )
            detail_tabs.append(
                dbc.Tab(label=pd_data["label"], tab_id=f"pf-period-{pd_data['value']}", children=[tab_content])
            )

        # Chart (en uzun donemde tum fonlar + benchmark + mix)
        chart_mix = None
        if user_mix_series is not None:
            chart_mix = {"name": user_mix_name, "series": user_mix_series}
        elif fon_benchmark_series:
            first_fon = list(fon_benchmark_series.keys())[0]
            chart_mix = {"name": fon_benchmark_series[first_fon].name, "series": fon_benchmark_series[first_fon]}

        tooltip_metrics = {}
        for kod, m in (periods_data[0]["metrics"] if periods_data else {}).items():
            tooltip_metrics[kod] = m

        fig = create_price_chart(
            fund_dict=fund_dict,
            benchmark_dict=benchmark_dict,
            title=f"{', '.join(fund_dict.keys())} - Getiri Grafigi (En Uzun Donem)",
            metrics=tooltip_metrics,
            mix_benchmark=chart_mix,
            theme=theme,
        )

        return {"display": "block"}, results_data, detail_tabs, fig, " | ".join(status_parts)
    except Exception as exc:
        logger.exception("Portföy analizi hatasi")
        return {"display": "none"}, dash.no_update, [], go.Figure(), f"Hata: {exc}"


# ── Callback: ozet tablosu (store degisimi veya metrik secimi) ───────
@callback(
    Output("pf-summary-table", "children"),
    Input("pf-results-store", "data"),
    Input("pf-metric-selector", "value"),
    prevent_initial_call=True,
)
def update_summary_table(results_data, selected_metric):
    if not results_data:
        return html.Small("Veri bulunamadi. Lütfen analiz yapin.", className="text-muted")
    ctx = dash.callback_context
    if ctx.triggered_id == "pf-results-store":
        selected_metric = selected_metric or METRIC_SHARPE
    return _build_summary_table(results_data, selected_metric)


# ── Optimizasyon callback ──────────────────────────────────────────────
@callback(
    Output("pf-ef-grafik", "figure"),
    Output("pf-optim-pie", "figure"),
    Output("pf-optim-sonuc", "children"),
    Output("pf-optim-status", "children"),
    Output("pf-backtest-chart", "figure"),
    Output("pf-mc-chart", "figure"),
    Output("pf-mc-stats", "children"),
    Input("pf-optim-btn", "n_clicks"),
    State("pf-fund-select", "value"),
    State("pf-optim-method", "value"),
    State("pf-optim-maxw", "value"),
    State("pf-optim-minw", "value"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def run_optimization(n_clicks, fon_kodlari, method, max_w_pct, min_w_pct, theme):
    if not fon_kodlari or len(fon_kodlari) < 2:
        return (go.Figure(), go.Figure(), "", "En az 2 fon seçmelisiniz.",
                go.Figure(), go.Figure(), "")
    fon_kodlari = [k.upper() for k in fon_kodlari]
    max_w = max_w_pct / 100.0 if max_w_pct else 0.4
    min_w = min_w_pct / 100.0 if min_w_pct is not None else 0.01

    try:
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=365 * 2)
        fetcher = TefasFetcher()
        fund_dict = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetcher.get_historical_data, f, start, end): f for f in fon_kodlari}
            for future in as_completed(futures):
                f = futures[future]
                try:
                    df = future.result()
                    if not df.empty and len(df) >= 20:
                        fund_dict[f] = df
                except Exception:
                    pass
        if len(fund_dict) < 2:
            return (go.Figure(), go.Figure(), "", "Yeterli veri bulunamadı.",
                    go.Figure(), go.Figure(), "")

        # Kovaryans ve getiri
        cov, kodlar = compute_covariance_matrix(fund_dict)
        rets, _ = compute_expected_returns(fund_dict)
        if len(cov) < 2 or np.isnan(cov).any():
            return (go.Figure(), go.Figure(), "", "Kovaryans matrisi hesaplanamadı.",
                    go.Figure(), go.Figure(), "")
        # Kovaryans düzeltme (pozitif tanımlı değilse)
        try:
            np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            cov = cov + np.eye(len(cov)) * 1e-6

        # TLREF
        rf_annual = 0.45
        try:
            tlref_scraper = TLREFScraper()
            tlref_all = tlref_scraper.from_zip() if True else tlref_scraper.from_csv()
            fon_tarihler = pd.to_datetime(fund_dict[kodlar[0]]["tarih"])
            min_t, max_t = fon_tarihler.min(), fon_tarihler.max()
            tlref_filtre = tlref_all[(tlref_all["date"] >= min_t) & (tlref_all["date"] <= max_t)]
            if not tlref_filtre.empty:
                rf_annual = tlref_filtre["value"].mean() / 100.0
        except Exception:
            pass

        # Optimize et
        if method == "sharpe":
            weights = max_sharpe_portfolio(rets, cov, rf_annual, min_w, max_w)
            method_label = "Max Sharpe"
        elif method == "minvar":
            weights = min_variance_portfolio(cov, min_w, max_w)
            method_label = "Min Varyans"
        else:
            weights = risk_parity_portfolio(cov, max_iter=100, tol=1e-8, min_w=min_w, max_w=max_w)
            method_label = "Risk Parity (ERC)"

        w_dict = {k: round(float(weights[i]), 4) for i, k in enumerate(kodlar) if weights[i] > 0.001}
        n_selected = len(w_dict)
        port_ret = sum(weights[i] * rets[i] for i in range(len(kodlar)))
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
        sharpe = (port_ret - rf_annual) / port_vol if port_vol > 0 else 0

        # Efficient frontier
        frontier = efficient_frontier_points(rets, cov, rf_annual, n_points=50, min_w=min_w, max_w=max_w)

        # Fon metrikleri (scatter için)
        fund_metrics = {}
        for i, k in enumerate(kodlar):
            fund_metrics[k] = {
                "Volatilite (Yıllık)": round(np.sqrt(cov[i, i]) * 100, 2),
                "Yıllıklandırılmış Getiri": round(rets[i] * 100, 2),
            }

        # EF chart
        ef_fig = create_efficient_frontier_chart(
            frontier, fund_metrics, w_dict,
            optimal_label=f"Optimal ({method_label})",
            rf_rate=rf_annual, theme=theme,
        )

        # Optimal weights pie
        pie_fig = create_portfolio_distribution_chart(
            w_dict, title=f"Optimal Ağırlıklar ({method_label})", theme=theme,
        )

        # Özet kartı
        sonuc = dbc.Card(dbc.CardBody([
            html.H5(f"Optimal Portföy — {method_label}", className="card-title"),
            dbc.Table([
                html.Tbody([
                    html.Tr([html.Td("Beklenen Getiri"), html.Td(f"%{port_ret*100:.2f}", className="fw-bold")]),
                    html.Tr([html.Td("Portföy Volatilitesi"), html.Td(f"%{port_vol*100:.2f}")]),
                    html.Tr([html.Td("Sharpe Oranı"), html.Td(f"{sharpe:.3f}")]),
                    html.Tr([html.Td("Seçilen Fon"), html.Td(f"{n_selected}/{len(kodlar)}")]),
                ])
            ], size="sm", bordered=False, className="mb-0"),
        ]), className="mb-3")

        status = f"Optimizasyon tamamlandı: {method_label}, {n_selected} fon"

        # Backtest
        backtest_df = walk_forward_backtest(
            fund_dict, rets, cov, window_years=1, step_months=3,
            method=method, rf_rate=rf_annual, min_w=min_w, max_w=max_w,
        )
        bt_fig = create_backtest_chart(backtest_df, theme=theme)

        # Monte Carlo
        paths, terminal = monte_carlo_simulation(rets, cov, weights, initial=100000, horizon_days=252, n_sim=500)
        mc_fig = create_monte_carlo_chart(paths, initial=100000, theme=theme)
        mc_stats_data = monte_carlo_stats(terminal, confidence=0.95, initial=100000)
        mc_rows = [html.Tr([html.Td(k), html.Td(str(v))]) for k, v in mc_stats_data.items()]
        mc_stats_div = dbc.Card(dbc.CardBody([
            html.H6("Monte Carlo İstatistikleri (1 Yıl)", className="card-title"),
            dbc.Table(html.Tbody(mc_rows), size="sm", bordered=False, className="mb-0"),
        ]), className="mt-2")

        # Rebalancing simülasyonu
        rebal_df = simulate_rebalancing(fund_dict, w_dict, rebalance_freq="monthly", threshold=0.05)
        rebal_chart = create_rebalancing_chart(rebal_df, theme=theme)

        # Hedef bazlı projeksiyon
        goal = goal_based_projection(rets, cov, weights, initial=100000, monthly_add=1000, years=10)
        goal_chart = create_goal_projection_chart(
            goal["projeksiyon"], goal["nominal_son"], goal["reel_son"], theme=theme,
        )

        sonuc_plus = html.Div([
            sonuc,
            html.H6("Rebalancing Simülasyonu", className="mt-3"),
            dcc.Graph(figure=rebal_chart, config={"displayModeBar": False}),
            html.H6("Hedef Bazlı Projeksiyon (10 Yıl)", className="mt-3"),
            dcc.Graph(figure=goal_chart, config={"displayModeBar": False}),
        ])

        return ef_fig, pie_fig, sonuc_plus, status, bt_fig, mc_fig, mc_stats_div

    except Exception as exc:
        logger.warning("Optimizasyon hatasi: %s", exc)
        return (go.Figure(), go.Figure(), "", f"Hata: {exc}",
                go.Figure(), go.Figure(), "")


# ── Atıf & Stres callback ─────────────────────────────────────────────
@callback(
    Output("pf-portfolio-actions", "children"),
    Output("pf-portfolio-actions", "className"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def show_portfolio_actions(pathname):
    if current_user.is_authenticated:
        pfs = list_portfolios(current_user.id) or []
        options = [{"label": p["name"], "value": p["id"]} for p in pfs]
        return html.Div([
            dbc.Button("Portföyü Kaydet", id="pf-save-btn", color="outline-primary", size="sm", className="me-2"),
            dbc.Button("Kayıtlı Yükle", id="pf-load-btn", color="outline-secondary", size="sm", className="me-2"),
            dcc.Dropdown(id="pf-load-select", options=options, placeholder="Portföy seç...",
                        searchable=True, clearable=True, style={"display": "inline-block", "width": "300px", "verticalAlign": "middle"}),
            _make_save_modal(),
        ]), "mb-2"
    return "", "d-none"


def _make_save_modal():
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Portföyü Kaydet")),
        dbc.ModalBody([
            dbc.Input(id="pf-save-name", placeholder="Portföy adı...", className="mb-2"),
        ]),
        dbc.ModalFooter([
            dbc.Button("Kaydet", id="pf-confirm-save", color="primary", className="me-2"),
            dbc.Button("İptal", id="pf-cancel-save", color="secondary"),
        ]),
    ], id="pf-save-modal", size="sm", is_open=False)


@callback(
    Output("pf-save-modal", "is_open"),
    Input("pf-save-btn", "n_clicks"),
    Input("pf-confirm-save", "n_clicks"),
    Input("pf-cancel-save", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_save_modal(save_btn, confirm, cancel):
    if save_btn:
        return True
    return False


@callback(
    Output("pf-portfolio-actions", "children", allow_duplicate=True),
    Input("pf-confirm-save", "n_clicks"),
    State("pf-save-name", "value"),
    State("pf-fund-select", "value"),
    State("portfoy-weight-store", "data"),
    State("fon-tipi-store", "data"),
    prevent_initial_call=True,
)
def confirm_save(n_clicks, name, fund_codes, weights, fon_tipi):
    if not name or not fund_codes or not current_user.is_authenticated:
        return dash.no_update
    save_portfolio(current_user.id, name, fund_codes, weights, fon_tipi or "YAT")
    pfs = list_portfolios(current_user.id) or []
    options = [{"label": p["name"], "value": p["id"]} for p in pfs]
    return html.Div([
        dbc.Button("Portföyü Kaydet", id="pf-save-btn", color="outline-primary", size="sm", className="me-2"),
        dbc.Button("Kayıtlı Yükle", id="pf-load-btn", color="outline-secondary", size="sm", className="me-2"),
        dcc.Dropdown(id="pf-load-select", options=options, placeholder="Portföy seç...",
                    searchable=True, clearable=True, style={"display": "inline-block", "width": "300px", "verticalAlign": "middle"}),
    ]), options


@callback(
    Output("pf-fund-select", "value"),
    Output("fon-tipi-store", "data", allow_duplicate=True),
    Input("pf-load-select", "value"),
    prevent_initial_call=True,
)
def load_portfolio(portfolio_id):
    if not portfolio_id:
        return dash.no_update, dash.no_update
    from data.dao import list_portfolios
    pfs = list_portfolios(current_user.id) if current_user.is_authenticated else []
    pf = next((p for p in pfs if p["id"] == portfolio_id), None)
    if pf:
        return pf["fund_codes"], pf.get("fon_tipi", "YAT")
    return dash.no_update, dash.no_update


@callback(
    Output("pf-te-sonuc", "children"),
    Output("pf-ff-chart", "figure"),
    Output("pf-style-drift-chart", "figure"),
    Output("pf-brinson-chart", "figure"),
    Output("pf-stress-chart", "figure"),
    Output("pf-stress-table", "children"),
    Input("pf-optim-btn", "n_clicks"),
    State("pf-fund-select", "value"),
    State("theme-store", "data"),
    State("fon-tipi-store", "data"),
    prevent_initial_call=True,
)
def run_attribution(n_clicks, fon_kodlari, theme, fon_tipi):
    if not fon_kodlari or len(fon_kodlari) < 1:
        return ("", go.Figure(), go.Figure(), go.Figure(), go.Figure(), "")
    fon_kodlari = [k.upper() for k in fon_kodlari]
    fon_tipi = fon_tipi or "YAT"

    try:
        from datetime import date, timedelta
        end = date.today()
        start = end - timedelta(days=365 * 2)
        fetcher = TefasFetcher()
        fund_dict = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetcher.get_historical_data, f, start, end): f for f in fon_kodlari}
            for future in as_completed(futures):
                f = futures[future]
                try:
                    df = future.result()
                    if not df.empty and len(df) >= 20:
                        fund_dict[f] = df
                except Exception:
                    pass
        if not fund_dict:
            return ("", go.Figure(), go.Figure(), go.Figure(), go.Figure(), "")

        # Benchmark verileri
        from config.benchmarks import get_benchmark_data
        fhise_df = get_benchmark_data("FHISE", start, end)
        td91g_df = get_benchmark_data("TD91G", start, end)
        atkap_df = get_benchmark_data("ATKAP", start, end)
        osabt_df = get_benchmark_data("OSABT", start, end)
        repbr_df = get_benchmark_data("REPBR", start, end)

        def to_ret(df):
            if df.empty:
                return pd.Series(dtype=float)
            s = df.set_index("tarih")["fiyat"]
            return s.pct_change().dropna()

        fhise_ret = to_ret(fhise_df)
        td91g_ret = to_ret(td91g_df)
        atkap_ret = to_ret(atkap_df)
        osabt_ret = to_ret(osabt_df)
        repbr_ret = to_ret(repbr_df)

        first_kod = list(fund_dict.keys())[0]
        fund_df = fund_dict[first_kod].set_index("tarih")["fiyat"]
        fund_ret = fund_df.pct_change().dropna()

        # TE Decomposition
        te_html = ""
        if not fhise_ret.empty:
            te = te_decomposition(fund_ret, fhise_ret)
            if te:
                te_html = dbc.Card(dbc.CardBody([
                    html.H6("Tracking Error Dekompozisyonu", className="card-title"),
                    dbc.Row([
                        dbc.Col(html.Div([
                            html.Small("Toplam TE"), html.H5(f"%{te['total_te']}"),
                        ]), xs=4),
                        dbc.Col(html.Div([
                            html.Small("Sistematik"), html.H5(f"%{te['systematic_te']} ({te['systematic_ratio']}%)"),
                        ]), xs=4),
                        dbc.Col(html.Div([
                            html.Small("İdiosinkratik"), html.H5(f"%{te['idiosyncratic_te']} ({te['idiosyncratic_ratio']}%)"),
                        ]), xs=4),
                    ]),
                    html.Small(f"Beta: {te['beta']:.3f} | Alpha: {te['alpha']:.4f} | R²: {te['r_squared']:.3f}",
                              className="text-muted"),
                ]), className="mb-3")

        # FF Regression
        ff_factors = {"MKT": fhise_ret}
        if not fhise_ret.empty:
            # SMB proxy ekle
            try:
                bist30_df = get_benchmark_data("XU030.IS", start, end)
                if not bist30_df.empty:
                    bist30_ret = bist30_df.set_index("tarih")["fiyat"].pct_change().dropna()
                    common = fhise_ret.index.intersection(bist30_ret.index)
                    if len(common) > 20:
                        ff_factors["SMB"] = (fhise_ret.loc[common] - bist30_ret.loc[common]).dropna()
            except Exception:
                pass
        ff_result = fama_french_regression(fund_ret, ff_factors)
        ff_fig = create_factor_loading_chart(ff_result, theme=theme) if ff_result else go.Figure()

        # RBSA Style Drift
        asset_rets = {}
        for name, s in [("Hisse", fhise_ret), ("Tahvil", td91g_ret), ("Altın", atkap_ret),
                         ("Özel Sektör", osabt_ret), ("Repo", repbr_ret)]:
            if not s.empty:
                asset_rets[name] = s
        drift_df = style_drift_tracking(fund_ret, asset_rets, window=min(252, len(fund_ret) - 1))
        drift_fig = create_style_drift_chart(drift_df, theme=theme) if not drift_df.empty else go.Figure()

        # Brinson (point-in-time)
        brinson_fig = go.Figure()
        try:
            dist = fetcher.get_portfolio_distribution(first_kod, fon_tipi=fon_tipi)
            if dist:
                # Benchmark: fon kategorisine göre mapping
                benchmark_w = {"Hisse Senedi": 60, "Devlet Tahvili": 40}  # default
                asset_rets_pct = {}
                if not fhise_ret.empty:
                    asset_rets_pct["Hisse Senedi"] = (fhise_df.set_index("tarih")["fiyat"].iloc[-1] / fhise_df.set_index("tarih")["fiyat"].iloc[0] - 1) * 100
                if not td91g_ret.empty:
                    asset_rets_pct["Devlet Tahvili"] = (td91g_df.set_index("tarih")["fiyat"].iloc[-1] / td91g_df.set_index("tarih")["fiyat"].iloc[0] - 1) * 100
                br = brinson_attribution(dist, benchmark_w, asset_rets_pct)
                if br:
                    brinson_fig = create_brinson_chart(br, theme=theme)
        except Exception:
            pass

        # Stres Testi
        fund_metrics_simple = {}
        for kod, df in fund_dict.items():
            rets = df.set_index("tarih")["fiyat"].pct_change().dropna()
            if len(rets) > 5:
                fund_metrics_simple[kod] = {"Beta": rets.corr(fhise_ret) if not fhise_ret.empty else 1.0}
        stress_results = run_stress_test_batch(fund_dict, fund_metrics_simple)
        stress_fig = create_stress_test_chart(stress_results, theme=theme)
        stress_table = ""
        if stress_results:
            rows = []
            for kod in fund_dict.keys():
                cells = [html.Td(html.Strong(kod))]
                for scenario_name in stress_results.keys():
                    val = stress_results[scenario_name].get(kod)
                    color = "#d62728" if val is not None and val < 0 else "#2ca02c" if val is not None else "#888"
                    cells.append(html.Td(f"%{val:.1f}" if val is not None else "-",
                                         style={"textAlign": "center", "color": color}))
                rows.append(html.Tr(cells))
            header = [html.Th("Fon")] + [html.Th(s, style={"fontSize": "0.8em"}) for s in stress_results.keys()]
            stress_table = dbc.Card(dbc.CardBody([
                html.H6("Tüm Fonlar — Senaryo Etkileri", className="card-title"),
                dbc.Table([html.Thead(html.Tr(header)), html.Tbody(rows)],
                          striped=True, bordered=True, hover=True, size="sm", responsive=True),
            ]), className="mt-2")

        return te_html, ff_fig, drift_fig, brinson_fig, stress_fig, stress_table

    except Exception as exc:
        logger.warning("Atıf hatasi: %s", exc)
        return (f"Hata: {exc}", go.Figure(), go.Figure(), go.Figure(), go.Figure(), "")


dash.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_portfolio_charts'
    ),
    Output("pf-chart", "figure", allow_duplicate=True),
    Input("theme-store", "data"),
    State("pf-chart", "figure"),
    prevent_initial_call=True,
)

# Optimizasyon chart'ları için clientside theme güncelleme
dash.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_optimization_charts'
    ),
    Output("pf-ef-grafik", "figure", allow_duplicate=True),
    Output("pf-optim-pie", "figure", allow_duplicate=True),
    Output("pf-backtest-chart", "figure", allow_duplicate=True),
    Output("pf-mc-chart", "figure", allow_duplicate=True),
    Output("pf-ff-chart", "figure", allow_duplicate=True),
    Output("pf-style-drift-chart", "figure", allow_duplicate=True),
    Output("pf-brinson-chart", "figure", allow_duplicate=True),
    Output("pf-stress-chart", "figure", allow_duplicate=True),
    Input("theme-store", "data"),
    State("pf-ef-grafik", "figure"),
    State("pf-optim-pie", "figure"),
    State("pf-backtest-chart", "figure"),
    State("pf-mc-chart", "figure"),
    State("pf-ff-chart", "figure"),
    State("pf-style-drift-chart", "figure"),
    State("pf-brinson-chart", "figure"),
    State("pf-stress-chart", "figure"),
    prevent_initial_call=True,
)
