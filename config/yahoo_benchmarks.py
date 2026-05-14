YAHOO_BENCHMARKS = [
    {"kod": "^SP500TR", "ad": "S&P 500 Total Return (USD)", "birim": "USD"},
    {"kod": "^GSPC",    "ad": "S&P 500 (USD)",            "birim": "USD"},
    {"kod": "^IXIC",    "ad": "NASDAQ Composite (USD)",    "birim": "USD"},
    {"kod": "^DJI",     "ad": "Dow Jones Industrial (USD)", "birim": "USD"},
    {"kod": "^NDX",     "ad": "NASDAQ 100 (USD)",          "birim": "USD"},
    {"kod": "^RUTTR",   "ad": "Russell 2000 Total Return (USD)", "birim": "USD"},
    {"kod": "^DJITR",   "ad": "Dow Jones Total Return (USD)",    "birim": "USD"},
    {"kod": "^XCMP",    "ad": "NASDAQ Composite Total Return (USD)", "birim": "USD"},
    {"kod": "XU100.IS", "ad": "BIST 100 (TRY)",            "birim": "TRY"},
    {"kod": "XU030.IS", "ad": "BIST 30 (TRY)",             "birim": "TRY"},
    {"kod": "XUTUM.IS", "ad": "BIST TUM (TRY)",            "birim": "TRY"},
    {"kod": "^FTSE",    "ad": "FTSE 100 (GBP)",            "birim": "GBP"},
    {"kod": "^GDAXI",   "ad": "DAX (EUR)",                 "birim": "EUR"},
    {"kod": "^N225",    "ad": "Nikkei 225 (JPY)",          "birim": "JPY"},
    {"kod": "^HSI",     "ad": "Hang Seng (HKD)",           "birim": "HKD"},
]

_YAHOO_MAP = {e["kod"]: e for e in YAHOO_BENCHMARKS}


def yahoo_benchmark_options():
    return [
        {"label": f"[Yahoo] {e['ad']}", "value": e["kod"]}
        for e in YAHOO_BENCHMARKS
    ]


def yahoo_benchmark_koda_gore(kod: str):
    return _YAHOO_MAP.get(kod)
