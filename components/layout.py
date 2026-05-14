#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ortak UI bileşenleri — navbar ve sidebar.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc


def create_navbar() -> dbc.Navbar:
    return dbc.Navbar(
        [
            html.Div(
                html.Img(
                    src="/assets/logo.png",
                    style={"height": "100%", "width": "auto", "maxWidth": "none"},
                ),
                style={"height": "100%", "maxWidth": "220px", "overflow": "hidden", "flexShrink": "0"},
            ),
            html.Span(
                "Fon Analiz Sistemi",
                className="text-white fw-semibold ms-2",
                style={"fontSize": "1.1rem"},
            ),
        ],
        color="primary",
        dark=True,
        className="mb-0 px-3 d-flex align-items-center",
        style={"height": "56px"},
    )


def create_sidebar() -> html.Div:
    """Sol yan menü — sayfalar arası gezinme."""
    return html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink("Ana Sayfa", href="/", active="exact"),
                    dbc.NavLink("Portföy Analizi", href="/portfolio", active="exact"),
                    dbc.NavLink("Karşılaştırma", href="/comparison", active="exact"),
                    dbc.NavLink("Rapor", href="/report", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="p-3",
    )
