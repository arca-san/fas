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

FLATLY_URL = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/flatly/bootstrap.min.css"
DARKLY_URL = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css"

app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dmc.styles.ALL],
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
            var theme = 'light';
            try {
                var t = localStorage.getItem('theme-store');
                if (t) {
                    var parsed = JSON.parse(t);
                    theme = typeof parsed === 'string' ? parsed : 'light';
                }
            } catch(e) {}
            document.documentElement.setAttribute('data-bs-theme', theme);
            var cssUrl = theme === 'dark' ? '""" + DARKLY_URL + """' : '""" + FLATLY_URL + """';
            document.write('<link rel="stylesheet" href="' + cssUrl + '">');
        })();
        </script>
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
