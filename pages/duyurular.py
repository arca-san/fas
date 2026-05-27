#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEFAS Duyuruları sayfası."""

import dash
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from datetime import date, timedelta

from data.fetchers import _tefas_api
from config.logger import get_logger

logger = get_logger(__name__)
dash.register_page(__name__, path="/duyurular")

layout = dbc.Container([
    html.H3("TEFAS Duyuruları", className="mb-3"),
    dbc.Row([
        dbc.Col([
            dcc.Loading(id="duyuru-loading", type="default", children=html.Div(id="duyuru-listesi")),
        ], xs=12),
    ]),
], fluid=True)


@callback(
    Output("duyuru-listesi", "children"),
    Input("duyuru-loading", "children"),
    prevent_initial_call=False,
)
def load_duyurular(_):
    try:
        duyurular = _tefas_api.duyurular()
        if not duyurular:
            return dbc.Alert("Şu anda TEFAS duyurusu bulunmamaktadır.", color="info")

        cards = []
        for d in duyurular:
            baslik = d.get("baslik") or d.get("title") or d.get("duyuruBaslik", "Duyuru")
            tarih_raw = d.get("tarih") or d.get("date") or d.get("yayinTarihi", "")
            tarih = str(tarih_raw)[:10] if tarih_raw else ""
            icerik = d.get("metin") or d.get("icerik") or d.get("duyuruMetin", "")
            fon_kod = d.get("fonKodu") or d.get("fonKod") or d.get("fon_kodu", "")
            tur = d.get("tur") or d.get("duyuruTuru", "")

            if len(icerik) > 500:
                icerik = icerik[:500] + "..."

            ozet = [
                dbc.CardHeader([
                    html.Strong(baslik, className="me-2"),
                    html.Small(tarih, className="text-muted"),
                    html.Span(tur, className="badge bg-info ms-2", style={"fontSize": "0.7em"}) if tur else None,
                    html.Span(fon_kod, className="badge bg-secondary ms-2", style={"fontSize": "0.7em"}) if fon_kod else None,
                ]),
                dbc.CardBody(html.Small(icerik, className="text-muted") if icerik else html.I("İçerik bulunamadı", className="text-muted")),
            ]
            cards.append(dbc.Card(ozet, className="mb-2"))

        if not cards:
            return dbc.Alert("Gösterilecek duyuru bulunamadı.", color="info")

        return html.Div([
            html.Small(f"Toplam {len(cards)} duyuru | Kaynak: TEFAS.gov.tr", className="text-muted d-block mb-2"),
            *cards,
        ])

    except Exception as exc:
        logger.warning("Duyuru yuklenemedi: %s", exc)
        return dbc.Alert(f"Duyurular alınamadı: {exc}", color="danger")
