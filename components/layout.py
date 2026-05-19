import dash
from dash import html, dcc
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
            html.Div(
                dbc.Button(
                    [html.I(className="bi bi-sun-fill me-1", id="theme-icon")],
                    id="theme-toggle",
                    color="light",
                    size="sm",
                    outline=True,
                    className="ms-auto text-white border-white",
                    style={"--bs-btn-color": "white"},
                ),
                className="ms-auto d-flex align-items-center",
            ),
        ],
        color="primary",
        dark=True,
        className="mb-0 px-3 d-flex align-items-center",
        style={"height": "56px"},
    )


def create_sidebar() -> html.Div:
    return html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink("Ana Sayfa", href="/", active="exact"),
                    dbc.NavLink("Fon Bulucu", href="/fon-bulucu", active="exact"),
                    dbc.NavLink("Portföy Analizi", href="/portfolio", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="p-3",
    )
