#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uygulama layout'u ve sayfa yönlendirme.
Dash Pages (use_pages=True) ile çalışır.
"""

import dash
import webbrowser
import threading
from dash import html, dcc, page_container
import dash_bootstrap_components as dbc

from app import app
from components.layout import create_navbar, create_sidebar

app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="analysis-store", storage_type="session"),  # metadata tutar
        create_navbar(),
        dbc.Row(
            [
                dbc.Col(create_sidebar(), width=2, className="bg-light sidebar vh-100"),
                dbc.Col(page_container, width=10, className="p-4"),
            ],
            className="g-0",
        ),
    ],
    fluid=True,
    className="dbc",
)

if __name__ == "__main__":
    url = "http://127.0.0.1:8050"
    # Uygulama başladıktan 1.5 sn sonra tarayıcıyı otomatik aç
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(debug=True, port=8050)
