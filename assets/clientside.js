(function() {
    /* ── Chart Theme Colors (shared tokens) ─────────────────────────── */
    var CHART = {
        dark: {
            template: 'plotly_dark',
            paper_bgcolor: '#1e1e1e',
            plot_bgcolor: '#1e1e1e',
            font_color: '#ffffff',
            title_color: '#ffffff',
            gridcolor: '#333333',
            linecolor: '#555555',
            tickfont_color: '#cccccc',
            axis_title_color: '#ffffff',
            legend_color: '#ffffff',
            mix_line: '#ffffff',
            bar_text: '#ffffff',
        },
        light: {
            template: 'plotly',
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#ffffff',
            font_color: '#212529',
            title_color: '#212529',
            gridcolor: '#e9ecef',
            linecolor: '#dee2e6',
            tickfont_color: '#495057',
            axis_title_color: '#212529',
            legend_color: '#212529',
            mix_line: '#000000',
            bar_text: '#212529',
        }
    };

    function getTheme(theme) {
        return theme === 'dark' ? CHART.dark : CHART.light;
    }

    function updateLineChart(fig, t) {
        if (!fig || !fig.layout) return fig;

        fig.layout.template = t.template;
        fig.layout.paper_bgcolor = t.paper_bgcolor;
        fig.layout.plot_bgcolor = t.plot_bgcolor;

        fig.layout.font = fig.layout.font || {};
        fig.layout.font.color = t.font_color;

        if (fig.layout.title) {
            if (typeof fig.layout.title === 'string') {
                fig.layout.title = { text: fig.layout.title };
            }
            fig.layout.title.font = fig.layout.title.font || {};
            fig.layout.title.font.color = t.title_color;
        }

        ['xaxis', 'yaxis'].forEach(function(axisKey) {
            if (fig.layout[axisKey]) {
                var axis = fig.layout[axisKey];
                axis.gridcolor = t.gridcolor;
                axis.linecolor = t.linecolor;
                axis.tickfont = axis.tickfont || {};
                axis.tickfont.color = t.tickfont_color;
                if (axis.title) {
                    axis.title.font = axis.title.font || {};
                    axis.title.font.color = t.axis_title_color;
                }
            }
        });

        if (fig.layout.legend) {
            fig.layout.legend.font = fig.layout.legend.font || {};
            fig.layout.legend.font.color = t.legend_color;
        }

        if (fig.data) {
            fig.data.forEach(function(trace) {
                if (trace.line && (trace.name.indexOf('Benchmark Mix') !== -1 || trace.line.color === '#000000' || trace.line.color === '#ffffff')) {
                    trace.line.color = t.mix_line;
                }
                if (trace.mode && trace.mode.indexOf('text') !== -1) {
                    trace.textfont = trace.textfont || {};
                    trace.textfont.color = t.font_color;
                }
            });
        }

        return fig;
    }

    function updateBarChart(fig, t) {
        if (!fig || !fig.layout) return fig;

        fig.layout.template = t.template;
        fig.layout.paper_bgcolor = t.paper_bgcolor;
        fig.layout.plot_bgcolor = t.plot_bgcolor;

        fig.layout.font = fig.layout.font || {};
        fig.layout.font.color = t.font_color;

        if (fig.layout.title) {
            if (typeof fig.layout.title === 'string') {
                fig.layout.title = { text: fig.layout.title };
            }
            fig.layout.title.font = fig.layout.title.font || {};
            fig.layout.title.font.color = t.title_color;
        }

        ['xaxis', 'yaxis'].forEach(function(axisKey) {
            if (fig.layout[axisKey]) {
                var axis = fig.layout[axisKey];
                axis.gridcolor = t.gridcolor;
                axis.linecolor = t.linecolor;
                axis.tickfont = axis.tickfont || {};
                axis.tickfont.color = t.tickfont_color;
                if (axis.title) {
                    axis.title.font = axis.title.font || {};
                    axis.title.font.color = t.axis_title_color;
                }
            }
        });

        if (fig.data) {
            fig.data.forEach(function(trace) {
                if (trace.textfont) {
                    trace.textfont.color = t.bar_text;
                }
            });
        }

        return fig;
    }

    /* ── Exported client-side callbacks ─────────────────────────────── */

    var clientsideFuncs = {
        update_home_charts: function(theme, fiyatFig, scatterFig, portfoyFig, korFig, rollingFig) {
            if (!theme) return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            var t = getTheme(theme);
            var newFiyat = fiyatFig ? JSON.parse(JSON.stringify(fiyatFig)) : fiyatFig;
            var newScatter = scatterFig ? JSON.parse(JSON.stringify(scatterFig)) : scatterFig;
            var newPortfoy = portfoyFig ? JSON.parse(JSON.stringify(portfoyFig)) : portfoyFig;
            var newKor = korFig ? JSON.parse(JSON.stringify(korFig)) : korFig;
            var newRolling = rollingFig ? JSON.parse(JSON.stringify(rollingFig)) : rollingFig;
            return [updateLineChart(newFiyat, t), updateLineChart(newScatter, t), updateLineChart(newPortfoy, t), updateLineChart(newKor, t), updateLineChart(newRolling, t)];
        },
        update_portfolio_charts: function(theme, fiyatFig) {
            if (!theme) return window.dash_clientside.no_update;
            var t = getTheme(theme);
            var newFiyat = fiyatFig ? JSON.parse(JSON.stringify(fiyatFig)) : fiyatFig;
            return updateLineChart(newFiyat, t);
        },
        update_fonbulucu_charts: function(theme, barFig) {
            if (!theme) return window.dash_clientside.no_update;
            var t = getTheme(theme);
            var newBar = barFig ? JSON.parse(JSON.stringify(barFig)) : barFig;
            return updateBarChart(newBar, t);
        },
        update_optimization_charts: function(theme, efFig, pieFig, backtestFig, mcFig, ffFig, driftFig, brinsonFig, stressFig) {
            // ...
            return [updateLineChart(newEf, t), updateLineChart(newPie, t), updateLineChart(newBt, t), updateLineChart(newMc, t), updateLineChart(newFf, t), updateLineChart(newDrift, t), updateLineChart(newBrinson, t), updateLineChart(newStress, t)];
        }
    };

    // ── Keyboard Shortcuts ─────────────────────────────────────────────
    document.addEventListener('keydown', function(e) {
        if (e.altKey === true && !e.shiftKey && !e.ctrlKey) {
            var url = null;
            switch (e.key) {
                case '1': url = '/'; break;
                case '2': url = '/fon-bulucu'; break;
                case '3': url = '/portfolio'; break;
                case '4': url = '/duyurular'; break;
                case 'g': case 'G': url = '/giris'; break;
            }
            if (url) { window.location.href = url; e.preventDefault(); }
        }
    });
    
    // ── ARIA improvements ──────────────────────────────────────────────
    (function() {
        var graphs = document.querySelectorAll('.js-plotly-plot');
        graphs.forEach(function(g, i) {
            g.setAttribute('role', 'img');
            g.setAttribute('aria-label', 'Grafik ' + (i + 1));
        });
        var navs = document.querySelectorAll('.sidebar');
        navs.forEach(function(n) { n.setAttribute('role', 'navigation'); });
        var mains = document.querySelectorAll('#page-content');
        mains.forEach(function(m) { m.setAttribute('role', 'main'); });
    })();

    if (window.dash_clientside) {
        window.dash_clientside.clientside = window.dash_clientside.clientside || {};
        for (var fName in clientsideFuncs) {
            if (clientsideFuncs.hasOwnProperty(fName)) {
                window.dash_clientside.clientside[fName] = clientsideFuncs[fName];
            }
        }
    } else {
        var internalDashClientside = {
            clientside: clientsideFuncs
        };
        Object.defineProperty(window, 'dash_clientside', {
            get: function() {
                return internalDashClientside;
            },
            set: function(val) {
                if (val) {
                    for (var key in val) {
                        if (val.hasOwnProperty(key)) {
                            internalDashClientside[key] = val[key];
                        }
                    }
                }
            },
            configurable: true
        });
    }
})();
