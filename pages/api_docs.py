#!/usr/bin/env python3
"""REST API dökümantasyon sayfası."""

import dash
from dash import html
import dash_bootstrap_components as dbc
import json

dash.register_page(__name__, path="/api-docs")

ENDPOINTS = [
    {
        "method": "GET",
        "path": "/api/v1/funds?type=YAT",
        "desc": "Tüm fonları listeler. type=YAT veya BES.",
        "curl": 'curl http://localhost:8050/api/v1/funds',
    },
    {
        "method": "GET",
        "path": "/api/v1/funds/{kod}",
        "desc": "Tek fonun anlık bilgisini döndürür.",
        "curl": "curl http://localhost:8050/api/v1/funds/AAS",
    },
    {
        "method": "GET",
        "path": "/api/v1/funds/{kod}/history?start=&end=",
        "desc": "Fonun tarihsel fiyat verisi. Varsayılan: son 1 yıl.",
        "curl": "curl 'http://localhost:8050/api/v1/funds/AAS/history?start=2025-01-01&end=2025-12-31'",
    },
    {
        "method": "GET",
        "path": "/api/v1/benchmarks",
        "desc": "Tüm benchmark endekslerini listeler (KYD + Yahoo).",
        "curl": "curl http://localhost:8050/api/v1/benchmarks",
    },
    {
        "method": "GET",
        "path": "/api/v1/benchmarks/{kod}/data?start=&end=",
        "desc": "Benchmark endeks verisi.",
        "curl": "curl 'http://localhost:8050/api/v1/benchmarks/FHISE/data?start=2025-01-01&end=2025-12-31'",
    },
    {
        "method": "POST",
        "path": "/api/v1/metrics",
        "desc": "Fon metriklerini hesaplar. Body: {\"fund_codes\": [\"MAC\", \"TI2\"]}.",
        "curl": "curl -X POST http://localhost:8050/api/v1/metrics -H 'Content-Type: application/json' -d '{\"fund_codes\": [\"MAC\", \"TI2\"]}'",
    },
    {
        "method": "POST",
        "path": "/api/v1/optimize",
        "desc": "Portföy optimizasyonu. Body: {\"fund_codes\": [...], \"method\": \"sharpe\"}.",
        "curl": "curl -X POST http://localhost:8050/api/v1/optimize -H 'Content-Type: application/json' -d '{\"fund_codes\": [\"MAC\", \"TI2\"], \"method\": \"sharpe\"}'",
    },
]

def _build_endpoint_card(ep):
    color_map = {"GET": "success", "POST": "warning"}
    return dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col(html.Span(ep["method"], className=f"badge bg-{color_map.get(ep['method'], 'info')} me-2"), xs="auto"),
            dbc.Col(html.Code(ep["path"], className="text-dark"), xs="auto"),
        ], className="align-items-center mb-2"),
        html.P(ep["desc"], className="mb-1 text-muted", style={"fontSize": "0.9em"}),
        dbc.Card(dbc.CardBody(html.Small(ep["curl"], style={"fontSize": "0.8em"})),
                 className="bg-light", style={"fontFamily": "monospace"}),
    ]), className="mb-3")

layout = dbc.Container([
    html.H3("FAS REST API", className="mb-3"),
    html.P("Tüm endpoint'ler Dash uygulaması ile aynı Flask sunucusunda çalışır. "
           "JSON formatında yanıt döndürür.", className="text-muted"),
    html.Hr(),
    *[_build_endpoint_card(e) for e in ENDPOINTS],
    html.Hr(className="mt-4"),
    html.H5("Notlar", className="mb-2"),
    html.Ul([
        html.Li("Tüm GET endpoint'leri auth gerektirmez."),
        html.Li("POST endpoint'leri şu an auth gerektirmez (geliştirme aşamasında)."),
        html.Li("Rate limit: TEFAS API'si dakikada ~6 istekle sınırlıdır."),
        html.Li("Tarih formatı: YYYY-MM-DD."),
    ], className="text-muted"),
], fluid=True)
