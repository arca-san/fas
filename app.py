#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash uygulaması giriş noktası.
"""

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from scripts.auto_update import main as auto_update

try:
    auto_update()
except Exception:
    pass

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY, dmc.styles.ALL],
    suppress_callback_exceptions=True,
    title="Fon Analiz Sistemi",
)

app.index_string = """
<!DOCTYPE html>
<html data-bs-theme="light">
    <head>
        {%metas%}
        <script>
        (function() {
            try {
                var t = JSON.parse(localStorage.getItem('theme-store'));
                if (t && (t === 'dark' || t.light)) {
                    var theme = typeof t === 'string' ? t : 'light';
                    document.documentElement.setAttribute('data-bs-theme', theme);
                }
            } catch(e) {}
        })();
        </script>
        <link rel="icon" type="image/png" href="/assets/logo.png">
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body class="dbc">
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

server = app.server
