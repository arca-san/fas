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
    external_stylesheets=[FLATLY_URL, dmc.styles.ALL],
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
                var t = localStorage.getItem('theme-store');
                if (t) {
                    var parsed = JSON.parse(t);
                    var theme = typeof parsed === 'string' ? parsed : 'light';
                    if (theme === 'dark') {
                        document.documentElement.setAttribute('data-bs-theme', 'dark');
                        var links = document.getElementsByTagName('link');
                        for (var i = 0; i < links.length; i++) {
                            if (links[i].href.indexOf('flatly') > -1) {
                                links[i].href = '""" + DARKLY_URL + """';
                            }
                        }
                    }
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
