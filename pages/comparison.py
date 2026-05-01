#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Çoklu Fon Karşılaştırması.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/comparison")

layout = dbc.Container(
    [
        html.H3("Karşılaştırma"),
        html.P("Bu sayfa yapım aşamasında. Birden fazla fonun risk-getiri karşılaştırması burada olacak."),
    ],
    fluid=True,
)
