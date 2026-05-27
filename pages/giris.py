#!/usr/bin/env python3
"""Giriş sayfası."""

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
from flask_login import current_user
from flask import redirect

from auth import try_login

dash.register_page(__name__, path="/giris")

layout = dbc.Container(
    dbc.Row(
        dbc.Col([
            html.H3("Fon Analiz Sistemi — Giriş", className="text-center mb-4"),
            dbc.Card(dbc.CardBody([
                dbc.Input(id="login-user", placeholder="Kullanıcı adı", className="mb-3"),
                dbc.Input(id="login-pass", type="password", placeholder="Şifre", className="mb-3"),
                dbc.Button("Giriş", id="login-btn", color="primary", className="w-100"),
                html.Div(id="login-status", className="mt-2 text-center"),
                html.Small("Varsayılan: admin / admin", className="text-muted d-block mt-2 text-center"),
            ])),
        ], xs=12, sm=8, md=6, lg=4, className="mt-5"),
        className="justify-content-center",
    ),
    fluid=True,
)


@callback(
    Output("login-status", "children"),
    Input("login-btn", "n_clicks"),
    State("login-user", "value"),
    State("login-pass", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return html.Span("Kullanıcı adı ve şifre gerekli", className="text-danger")
    success, msg = try_login(username, password)
    if success:
        return html.Div([
            html.Span("Giriş başarılı! Yönlendiriliyorsunuz...", className="text-success"),
            dcc.Location(id="login-redirect", href="/", refresh=True),
        ])
    return html.Span(msg, className="text-danger")
