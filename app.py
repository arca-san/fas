#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dash uygulaması giriş noktası.
"""

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from flask import redirect, request
from flask_login import current_user

from database import init_db
from auth import init_auth
from api import api

# .env dosyasını yükle (opsiyonel)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


FLATLY_URL = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/flatly/bootstrap.min.css"

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
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script>
        (function() {
            try {
                var t = sessionStorage.getItem('theme-store');
                if (t) {
                    var theme = JSON.parse(t);
                    theme = typeof theme === 'string' ? theme : 'light';
                    document.documentElement.setAttribute('data-bs-theme', theme);
                }
            } catch(e) {}
        })();
        </script>
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

# Flask oturum anahtarı
from config.settings import SECRET_KEY
server.secret_key = SECRET_KEY

# Veritabanı + Auth başlatma
init_db()
init_auth(server)

# REST API
server.register_blueprint(api)


# Login koruması — giriş yapmamış kullanıcıları /giris sayfasına yönlendir
@server.before_request
def require_login():
    try:
        if request.path.startswith(("/_dash-", "/assets", "/api/", "/_realtime-")):
            return None
        if request.method == "POST":
            return None
        if request.path in ("/giris", "/", ""):
            return None
        if not current_user.is_authenticated:
            return redirect("/giris")
    except Exception:
        pass
