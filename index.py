#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uygulama layout'u ve sayfa yönlendirme.
Dash Pages (use_pages=True) ile çalışır.
"""

import dash
from dash import html, dcc, page_container
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from app import app
from components.layout import create_navbar, create_sidebar

app.layout = dmc.MantineProvider(
    dbc.Container(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="analysis-store", storage_type="session"),
            create_navbar(),
            dbc.Row(
                [
                    dbc.Col(
                        create_sidebar(),
                        xs=0, sm=0, md=2,
                        className="bg-light sidebar d-none d-md-block vh-100",
                    ),
                    dbc.Col(
                        page_container,
                        xs=12, sm=12, md=10,
                        className="p-3 p-md-4",
                    ),
                ],
                className="g-0",
            ),
        ],
        fluid=True,
        className="dbc",
    )
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
