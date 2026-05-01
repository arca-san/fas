#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rapor — HTML önizleme ve PDF indirme.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/report")

layout = dbc.Container(
    [
        html.H3("Rapor"),
        html.P("Bu sayfa yapım aşamasında. Analiz raporu önizleme ve PDF indirme burada olacak."),
    ],
    fluid=True,
)
