#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash uygulaması giriş noktası.
"""

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dmc.styles.ALL],
    suppress_callback_exceptions=True,
    title="Fon Analiz Sistemi",
)

server = app.server
