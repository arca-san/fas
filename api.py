#!/usr/bin/env python3
"""
FAS REST API — Flask Blueprint.
Dash ile aynı Flask sunucusu üzerinde çalışır.

Kullanım: app.py içinde:
    from api import api
    app.server.register_blueprint(api)
"""

from flask import Blueprint, request, jsonify
import pandas as pd

api = Blueprint("api", __name__, url_prefix="/api/v1")


@api.route("/funds", methods=["GET"])
def list_funds():
    from data.fetchers import _tefas_api
    fon_tipi = request.args.get("type", "YAT")
    data = _tefas_api.tum_fonlar(fon_tipi)
    return jsonify({"count": len(data), "data": data})


@api.route("/funds/<kod>", methods=["GET"])
def fund_detail(kod):
    from data.fetchers import _tefas_api
    data = _tefas_api.fon_anlik_bilgi(kod.upper())
    if not data:
        return jsonify({"error": "Fon bulunamadı"}), 404
    return jsonify(data)


@api.route("/funds/<kod>/history", methods=["GET"])
def fund_history(kod):
    from datetime import date, timedelta
    from data.fetchers.tefas_fetcher import TefasFetcher
    start = request.args.get("start", (date.today() - timedelta(days=365)).isoformat())
    end = request.args.get("end", date.today().isoformat())
    fetcher = TefasFetcher()
    df = fetcher.get_historical_data(kod.upper(), start, end)
    return jsonify({
        "symbol": kod.upper(), "count": len(df),
        "data": df.to_dict(orient="records"),
    })


@api.route("/benchmarks", methods=["GET"])
def list_benchmarks():
    from config.benchmarks import all_benchmark_options
    return jsonify({"data": all_benchmark_options()})


@api.route("/benchmarks/<kod>/data", methods=["GET"])
def benchmark_data(kod):
    from datetime import date, timedelta, datetime
    from config.benchmarks import get_benchmark_data
    start = request.args.get("start", (date.today() - timedelta(days=365)).isoformat())
    end = request.args.get("end", date.today().isoformat())
    bas = datetime.strptime(start, "%Y-%m-%d").date()
    bit = datetime.strptime(end, "%Y-%m-%d").date()
    df = get_benchmark_data(kod.upper(), bas, bit)
    return jsonify({
        "symbol": kod.upper(), "count": len(df),
        "data": df.to_dict(orient="records") if not df.empty else [],
    })


@api.route("/metrics", methods=["POST"])
def compute_metrics():
    from datetime import date, timedelta
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from data.fetchers.tefas_fetcher import TefasFetcher
    from components.metrics import calculate_fund_metrics
    body = request.json
    if not body or "fund_codes" not in body:
        return jsonify({"error": "fund_codes required"}), 400
    fetcher = TefasFetcher()
    end = date.today()
    start = end - timedelta(days=365)
    fund_dict = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        fs = {ex.submit(fetcher.get_historical_data, k, start, end): k for k in body["fund_codes"]}
        for f in as_completed(fs):
            k = fs[f]
            try:
                df = f.result()
                if not df.empty:
                    fund_dict[k] = df
            except Exception:
                pass
    metrics = calculate_fund_metrics(fund_dict, pd.Series(dtype=float), pd.Series(dtype=float))
    return jsonify({"count": len(metrics), "data": {k: {mk: v for mk, v in m.items()} for k, m in metrics.items()}})


@api.route("/optimize", methods=["POST"])
def run_optimization():
    from datetime import date, timedelta
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from data.fetchers.tefas_fetcher import TefasFetcher
    from components.optimizer import (
        compute_covariance_matrix, compute_expected_returns,
        max_sharpe_portfolio, min_variance_portfolio, risk_parity_portfolio,
    )
    body = request.json
    if not body or "fund_codes" not in body:
        return jsonify({"error": "fund_codes required"}), 400
    method = body.get("method", "sharpe")
    min_w = body.get("min_weight", 0.01)
    max_w = body.get("max_weight", 0.4)
    fetcher = TefasFetcher()
    end = date.today()
    start = end - timedelta(days=365)
    fund_dict = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        fs = {ex.submit(fetcher.get_historical_data, k, start, end): k for k in body["fund_codes"]}
        for f in as_completed(fs):
            k = fs[f]
            try:
                df = f.result()
                if not df.empty:
                    fund_dict[k] = df
            except Exception:
                pass
    cov, kodlar = compute_covariance_matrix(fund_dict)
    rets, _ = compute_expected_returns(fund_dict)
    if method == "minvar":
        w = min_variance_portfolio(cov, min_w, max_w)
    elif method == "riskparity":
        w = risk_parity_portfolio(cov, max_iter=100, min_w=min_w, max_w=max_w)
    else:
        w = max_sharpe_portfolio(rets, cov, 0.45, min_w, max_w)
    return jsonify({"weights": {k: round(float(w[i]), 4) for i, k in enumerate(kodlar)}, "method": method})
