window.dash_clientside = Object.assign(window.dash_clientside || {}, {
    clientside: {
        update_home_charts: function(theme, fiyatFig, scatterFig) {
            if (!theme) return [window.dash_clientside.no_update, window.dash_clientside.no_update];
            
            var isDark = theme === 'dark';
            
            function updateFig(fig) {
                if (!fig || !fig.layout) return fig;
                
                fig.layout.template = isDark ? 'plotly_dark' : 'plotly';
                fig.layout.paper_bgcolor = isDark ? '#1e1e1e' : '#ffffff';
                fig.layout.plot_bgcolor = isDark ? '#1e1e1e' : '#ffffff';
                
                fig.layout.font = fig.layout.font || {};
                fig.layout.font.color = isDark ? '#ffffff' : '#212529';
                
                if (fig.layout.title) {
                    if (typeof fig.layout.title === 'string') {
                        fig.layout.title = { text: fig.layout.title };
                    }
                    fig.layout.title.font = fig.layout.title.font || {};
                    fig.layout.title.font.color = isDark ? '#ffffff' : '#212529';
                }
                
                ['xaxis', 'yaxis'].forEach(function(axisKey) {
                    if (fig.layout[axisKey]) {
                        var axis = fig.layout[axisKey];
                        axis.gridcolor = isDark ? '#333333' : '#e9ecef';
                        axis.linecolor = isDark ? '#555555' : '#dee2e6';
                        axis.tickfont = axis.tickfont || {};
                        axis.tickfont.color = isDark ? '#cccccc' : '#495057';
                        if (axis.title) {
                            axis.title.font = axis.title.font || {};
                            axis.title.font.color = isDark ? '#ffffff' : '#212529';
                        }
                    }
                });
                
                if (fig.layout.legend) {
                    fig.layout.legend.font = fig.layout.legend.font || {};
                    fig.layout.legend.font.color = isDark ? '#ffffff' : '#212529';
                }
                
                if (fig.data) {
                    fig.data.forEach(function(trace) {
                        if (trace.line && (trace.name.indexOf('Benchmark Mix') !== -1 || trace.line.color === '#000000' || trace.line.color === '#ffffff')) {
                            trace.line.color = isDark ? '#ffffff' : '#000000';
                        }
                        if (trace.mode && trace.mode.indexOf('text') !== -1) {
                            trace.textfont = trace.textfont || {};
                            trace.textfont.color = isDark ? '#ffffff' : '#000000';
                        }
                    });
                }
                
                return fig;
            }
            
            var newFiyat = fiyatFig ? JSON.parse(JSON.stringify(fiyatFig)) : fiyatFig;
            var newScatter = scatterFig ? JSON.parse(JSON.stringify(scatterFig)) : scatterFig;
            
            return [updateFig(newFiyat), updateFig(newScatter)];
        },
        update_portfolio_charts: function(theme, fiyatFig) {
            if (!theme) return window.dash_clientside.no_update;
            
            var isDark = theme === 'dark';
            
            function updateFig(fig) {
                if (!fig || !fig.layout) return fig;
                
                fig.layout.template = isDark ? 'plotly_dark' : 'plotly';
                fig.layout.paper_bgcolor = isDark ? '#1e1e1e' : '#ffffff';
                fig.layout.plot_bgcolor = isDark ? '#1e1e1e' : '#ffffff';
                
                fig.layout.font = fig.layout.font || {};
                fig.layout.font.color = isDark ? '#ffffff' : '#212529';
                
                if (fig.layout.title) {
                    if (typeof fig.layout.title === 'string') {
                        fig.layout.title = { text: fig.layout.title };
                    }
                    fig.layout.title.font = fig.layout.title.font || {};
                    fig.layout.title.font.color = isDark ? '#ffffff' : '#212529';
                }
                
                ['xaxis', 'yaxis'].forEach(function(axisKey) {
                    if (fig.layout[axisKey]) {
                        var axis = fig.layout[axisKey];
                        axis.gridcolor = isDark ? '#333333' : '#e9ecef';
                        axis.linecolor = isDark ? '#555555' : '#dee2e6';
                        axis.tickfont = axis.tickfont || {};
                        axis.tickfont.color = isDark ? '#cccccc' : '#495057';
                        if (axis.title) {
                            axis.title.font = axis.title.font || {};
                            axis.title.font.color = isDark ? '#ffffff' : '#212529';
                        }
                    }
                });
                
                if (fig.layout.legend) {
                    fig.layout.legend.font = fig.layout.legend.font || {};
                    fig.layout.legend.font.color = isDark ? '#ffffff' : '#212529';
                }
                
                if (fig.data) {
                    fig.data.forEach(function(trace) {
                        if (trace.line && (trace.name.indexOf('Benchmark Mix') !== -1 || trace.line.color === '#000000' || trace.line.color === '#ffffff')) {
                            trace.line.color = isDark ? '#ffffff' : '#000000';
                        }
                    });
                }
                
                return fig;
            }
            
            var newFiyat = fiyatFig ? JSON.parse(JSON.stringify(fiyatFig)) : fiyatFig;
            return updateFig(newFiyat);
        }
    }
});
