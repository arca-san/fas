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
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src="/assets/logo.png", height="30px")),
                            dbc.Col(dbc.NavbarBrand("Fon Analiz Sistemi", className="ms-2")),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="/",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            ]
        ),
        color="primary",
        dark=True,
        className="mb-0",
    )


def create_sidebar() -> html.Div:
    """Sol yan menü — sayfalar arası gezinme."""
    return html.Div(
        [
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Ana Sayfa", href="/", active="exact"),
                    dbc.NavLink("Fon Analizi", href="/fund-analysis", active="exact"),
                    dbc.NavLink("Karşılaştırma", href="/comparison", active="exact"),
                    dbc.NavLink("Rapor", href="/report", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="p-3",
    )
