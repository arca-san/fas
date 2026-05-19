#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detayli Bilgi — Fon Bulucu metodoloji ve metrik açıklamaları.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/detayli-bilgi")

layout = dbc.Container([
    html.H3("Detaylı Bilgi", className="mb-3"),
    dbc.Card([
        dbc.CardBody([
            html.H5("Fon Bulucu Nedir?", className="card-title"),
            html.P(
                "Fon Bulucu sayfası, TEFAS'ta yer alan fonları kategorilerine ve belirlediğiniz "
                "vadeye göre filtreleyerek en yüksek getirili 10 fonu listeler. "
                "Bu fonların fon yöneticisi başarısını gösteren metriklerini karşılaştırabilir, "
                "kendi yatırım kararınızı vermenize yardımcı olur."
            ),
            html.Hr(),
            html.H5("Kullanım", className="card-title"),
            html.Ol([
                html.Li("Kategori seçin (ör: Hisse Senedi, Borçlanma Araçları, Karma vb.)"),
                html.Li("Vade seçin (1 Ay - 5 Yıl arası)"),
                html.Li("\"Fonları Bul\" butonuna tıklayın"),
                html.Li("Sıralanan fonları metriklerine göre inceleyin"),
            ]),
            html.Hr(),
            html.H5("Metrik Açıklamaları", className="card-title"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Metrik"),
                    html.Th("Açıklama"),
                    html.Th("Yön"),
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(html.Strong("Sharpe Oranı")),
                        html.Td("Risksiz getiri üzerindeki fazla getirinin birim risk başına değeri. "
                                "Yüksek Sharpe = daha iyi risk-ayarlı getiri."),
                        html.Td("Yüksek iyi"),
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Alfa")),
                        html.Td("Fon yöneticisinin benchmark'a kıyasla yarattığı ek getiri. "
                                "Pozitif Alfa = yönetici piyasanın üzerinde getiri sağlamış."),
                        html.Td("Yüksek iyi"),
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Enformasyon Oranı")),
                        html.Td("Aktif getirinin (fon - benchmark) tutarlılığını ölçer. "
                                "Yüksek IR = yönetici istikrarlı şekilde fazla getiri üretmiş."),
                        html.Td("Yüksek iyi"),
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Sortino Oranı")),
                        html.Td("Sharpe'a benzer, ancak sadece aşağı yönlü volatiliteyi "
                                "risk olarak kabul eder. Yüksek Sortino = daha iyi düşüş koruması."),
                        html.Td("Yüksek iyi"),
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Volatilite (Yıllık)")),
                        html.Td("Getirilerin yıllık standart sapması. Fonun ne kadar "
                                "dalgalandığını gösterir."),
                        html.Td("Düşük iyi"),
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Maksimum Düşüş")),
                        html.Td("Belirli dönemdeki en yüksek değerden en düşük değere "
                                "olan düşüş. Fonun tarihindeki en büyük kaybı gösterir."),
                        html.Td("Düşük iyi"),
                    ]),
                    html.Tr([
                        html.Td(html.Strong("Yıllıklandırılmış Getiri")),
                        html.Td("Seçilen dönemdeki getirinin yıllık bazda ifade edilmiş hali."),
                        html.Td("Yüksek iyi"),
                    ]),
                ]),
            ], striped=True, bordered=True, hover=True, size="sm", responsive=True),
            html.Hr(),
            html.H5("Fon Yöneticisi Başarısını Değerlendirme", className="card-title"),
            html.P(
                "Fon yöneticisinin doğrudan başarısını değerlendirmek için öncelikle "
                "Alfa ve Enformasyon Oranı metriklerine odaklanmanız önerilir:"
            ),
            html.Ul([
                html.Li(html.B("Alfa:"), " Yönetici benchmark'ı geçebilmiş mi?"),
                html.Li(html.B("Enformasyon Oranı:"), " Bu başarı tutarlı mı?"),
                html.Li(html.B("Sharpe:"), " Risk birimi başına getiri ne kadar?"),
                html.Li(html.B("Sortino:"), " Düşüş riskine karşı koruma ne düzeyde?"),
            ]),
            html.P(
                "Tek bir metriğe odaklanmak yerine tüm metrikleri birlikte "
                "değerlendirmeniz daha sağlıklı bir karar vermenizi sağlar.",
                className="text-muted",
            ),
            html.Hr(),
            html.Div([
                html.A("← Fon Bulucu'ya Dön", href="/fon-bulucu", className="btn btn-primary"),
            ]),
        ])
    ]),
], fluid=True, className="py-3")
