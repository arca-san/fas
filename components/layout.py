import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_navbar() -> dbc.Navbar:
    return dbc.Navbar(
        [
            # Mobil hamburger menü
            dbc.Button(
                html.I(className="bi bi-list", style={"fontSize": "1.5rem"}),
                id="mobile-menu-btn",
                color="light",
                outline=True,
                className="d-md-none me-2 border-0",
                style={"--bs-btn-color": "white"},
                title="Menüyü aç/kapat",
            ),
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
                [
                    dbc.Button(
                        "❓",
                        id="onb-open",
                        color="light",
                        size="sm",
                        outline=True,
                        className="me-1 border-white",
                        style={"--bs-btn-color": "white", "fontSize": "1.0rem", "padding": "0.2rem 0.4rem"},
                        title="Yardım",
                    ),
                    dbc.Button(
                        "🌙",
                        id="theme-toggle",
                        color="light",
                        size="sm",
                        outline=True,
                        className="border-white",
                        style={"--bs-btn-color": "white", "fontSize": "1.2rem", "padding": "0.2rem 0.5rem"},
                    ),
                ],
                className="ms-auto d-flex align-items-center",
            ),
        ],
        color="primary",
        dark=True,
        className="mb-0 px-3 d-flex align-items-center",
        style={"height": "56px"},
    )


def create_sidebar_nav() -> dbc.Nav:
    """Sadece navigasyon linkleri (offcanvas için)."""
    return dbc.Nav(
        [
            dbc.NavLink("Ana Sayfa", href="/", active="exact"),
            dbc.NavLink("Fon Bulucu", href="/fon-bulucu", active="exact"),
            dbc.NavLink("Portföy Analizi", href="/portfolio", active="exact"),
            dbc.NavLink("Duyurular", href="/duyurular", active="exact"),
        ],
        vertical=True,
        pills=True,
        className="mb-3",
    )


def create_sidebar() -> html.Div:
    return html.Div(
        [
            create_sidebar_nav(),
            html.Hr(className="mb-2"),
            html.Label("Fon Tipi", className="fw-semibold mb-1", style={"fontSize": "0.8rem"}),
            dbc.RadioItems(
                id="fon-tipi-toggle",
                options=[
                    {"label": "Yatırım Fonu (YAT)", "value": "YAT"},
                    {"label": "BES Fonu", "value": "BES"},
                ],
                value="YAT",
                inline=False,
                className="mb-3",
            ),
        ],
        className="p-3",
        **{"role": "navigation", "aria-label": "Ana navigasyon"},
    )
