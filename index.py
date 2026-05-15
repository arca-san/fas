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
            dcc.Store(id="theme-store", storage_type="local"),
            dcc.Store(id="fav-store", storage_type="local"),
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
        var links = document.querySelectorAll('link');
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

        var label = document.getElementById('theme-label');
        if (label) label.textContent = newTheme === 'dark' ? 'Acik' : 'Koyu';

        return newTheme;
    }
    """,
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)

clientside_callback(
    """
    function(saved) {
        if (!saved) return 'light';
        var links = document.querySelectorAll('link');
        for (var i = 0; i < links.length; i++) {
            var h = links[i].href || '';
            if (h.indexOf('flatly') > -1) links[i].disabled = (saved !== 'light');
            if (h.indexOf('darkly') > -1) links[i].disabled = (saved !== 'dark');
        }
        var sidebar = document.getElementById('sidebar-col');
        if (sidebar) {
            if (saved === 'dark') {
                sidebar.classList.remove('bg-light');
            } else {
                sidebar.classList.add('bg-light');
            }
        }
        var label = document.getElementById('theme-label');
        if (label) label.textContent = saved === 'dark' ? 'Acik' : 'Koyu';
        return saved;
    }
    """,
    Output("theme-store", "data", allow_duplicate=True),
    Input("theme-store", "data"),
    prevent_initial_call=True,
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)
