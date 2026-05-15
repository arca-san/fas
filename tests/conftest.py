import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def sample_daily_returns():
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    np.random.seed(42)
    returns = np.random.normal(0.0008, 0.015, 252)
    return pd.Series(returns, index=dates)


@pytest.fixture
def sample_fund_dict():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    np.random.seed(42)
    prices = 100 * np.exp(np.random.normal(0.0008, 0.015, 100).cumsum())
    df = pd.DataFrame({"tarih": dates, "fiyat": prices})
    return {"TESTFON": df}


@pytest.fixture
def sample_rf_series():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    return pd.Series(0.0005, index=dates)


@pytest.fixture
def sample_market_prices():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    prices = 1000 * np.exp(np.random.normal(0.0005, 0.01, 100).cumsum())
    return pd.Series(prices, index=dates)
