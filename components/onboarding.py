#!/usr/bin/env python3
"""
Onboarding — ilk kullanım için 3 adımlı tanıtım modal'ı.
"""

from dash import html, dcc, clientside_callback
import dash_bootstrap_components as dbc
from dash import callback, Output, Input, State, dash


def make_onboarding_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("FAS'a Hoş Geldiniz!"), close_button=False),
            dbc.ModalBody([
                html.Div(id="onboarding-step", children=[
                    html.H5("👋 1. Adım — Fon Seçimi"),
                    html.P("Ana sayfadaki 'Fon kodu veya ünvanı yazın' kutusuna "
                           "bir fon kodu yazın (örn: MAC, TI2, NJR)."),
                    html.P("Birden çok fon seçip karşılaştırabilir, yanlarındaki "
                           "% input'ları ile ağırlıklandırabilirsiniz."),
                    html.H5("⚙️ 2. Adım — Analiz", className="mt-3"),
                    html.P("Benchmark seçin, tarih aralığı belirleyin ve "
                           "'Analiz Et' butonuna tıklayın."),
                    html.H5("📊 3. Adım — Sonuçlar", className="mt-3"),
                    html.P("Grafikler, metrik tablosu, korelasyon matrisi ve "
                           "portföy dağılımını inceleyin."),
                ]),
                html.Small("Bu pencere sadece ilk kullanımda gösterilir. "
                           "Sağ üstteki butondan tekrar açabilirsiniz.",
                           className="text-muted d-block mt-2"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Başla!", id="onb-close", color="primary", className="w-100"),
            ]),
        ],
        id="onboarding-modal",
        is_open=False,
        size="lg",
        backdrop="static",
    )


# Onboarding açma/kapama callback
@callback(
    Output("onboarding-modal", "is_open", allow_duplicate=True),
    Input("onb-open", "n_clicks"),
    Input("onb-close", "n_clicks"),
    State("onboarding-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_onboarding(open_clicks, close_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    btn_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if btn_id == "onb-open":
        return True
    if btn_id == "onb-close":
        return False
    return is_open


# İlk açılışta localStorage flag'ine göre göster
clientside_callback(
    """
    function() {
        try {
            var done = sessionStorage.getItem('fas-onboarding-done');
            if (done !== '1') {
                sessionStorage.setItem('fas-onboarding-done', '1');
                return true;
            }
        } catch(e) {}
        return false;
    }
    """,
    Output("onboarding-modal", "is_open", allow_duplicate=True),
    Input("onboarding-modal", "id"),
    prevent_initial_call=True,
)
