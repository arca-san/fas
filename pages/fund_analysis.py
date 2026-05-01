#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tekil Fon Analizi — getiri, risk, metrikler ve grafikler.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/fund-analysis")

layout = dbc.Container(
    [
        html.H3("Fon Analizi"),
        html.P("Bu sayfa yapım aşamasında. Seçilen fonların getiri, risk ve metrik grafikleri burada gösterilecek."),
    ],
    fluid=True,
)
