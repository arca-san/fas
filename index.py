import dash
from dash import html, dcc, page_container, clientside_callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from app import app
from components.layout import create_navbar, create_sidebar

app.layout = dmc.MantineProvider(
    dbc.Container(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="analysis-store", storage_type="session"),
            dcc.Store(id="theme-store", data="light", storage_type="local"),
            create_navbar(),
            dbc.Row(
                [
                    dbc.Col(
                        create_sidebar(),
                        xs=0, sm=0, md=2,
                        className="bg-light sidebar d-none d-md-block vh-100",
                        id="sidebar-col",
                    ),
                    dbc.Col(
                        page_container,
                        xs=12, sm=12, md=10,
                        className="p-3 p-md-4",
                        id="page-content",
                    ),
                ],
                className="g-0",
            ),
        ],
        fluid=True,
        className="dbc",
    ),
    id="mantine-provider",
)

clientside_callback(
    """
    function(n_clicks, current) {
        var newTheme = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-bs-theme', newTheme);
        var links = document.getElementsByTagName('link');
        for (var i = 0; i < links.length; i++) {
            var h = links[i].href || '';
            if (h.indexOf('flatly') > -1) links[i].disabled = (newTheme !== 'light');
            if (h.indexOf('darkly') > -1) links[i].disabled = (newTheme !== 'dark');
        }
        var meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.content = newTheme === 'dark' ? '#222' : '#1abc9c';

        var sidebar = document.getElementById('sidebar-col');
        if (sidebar) {
            if (newTheme === 'dark') {
                sidebar.classList.remove('bg-light');
            } else {
                sidebar.classList.add('bg-light');
            }
        }

        var btn = document.getElementById('theme-toggle');
        if (btn) btn.textContent = newTheme === 'dark' ? '☀️' : '🌙';

        var container = document.querySelector('.dbc');
        if (container) container.style.backgroundColor = newTheme === 'dark' ? '#1a1a2e' : '';

        return newTheme;
    }
    """,
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
