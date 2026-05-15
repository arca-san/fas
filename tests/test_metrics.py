import numpy as np
import pandas as pd

from components.metrics import (
    calculate_fund_metrics,
    calculate_mix_metrics,
    _annual_return,
    _annualized_vol,
    _downside_vol,
    _max_drawdown,
    _value_at_risk,
    _conditional_var,
    _r_squared,
    get_fund_benchmarks,
)
from config.constants import (
    METRIC_SHARPE,
    METRIC_SORTINO,
    METRIC_TOTAL_RETURN,
    METRIC_ANNUALIZED_RETURN,
    METRIC_VOLATILITY,
    METRIC_MAX_DRAWDOWN,
    METRIC_VAR,
    METRIC_CVAR,
    METRIC_BETA,
    METRIC_ALPHA,
    METRIC_INFORMATION_RATIO,
    METRIC_TREYNOR,
)


class TestAnnualReturn:
    def test_zero_returns(self):
        assert _annual_return(pd.Series([])) == 0.0

    def test_constant_returns(self):
        r = pd.Series([0.0] * 10)
        assert _annual_return(r) == 0.0

    def test_positive_return(self):
        r = pd.Series([0.001] * 252)
        result = _annual_return(r)
        assert result > 0

    def test_single_value(self):
        r = pd.Series([0.01])
        result = _annual_return(r)
        expected = (1.01) ** 252 - 1
        assert abs(result - expected) < 1e-6


class TestAnnualizedVol:
    def test_zero_std(self):
        r = pd.Series([0.0] * 10)
        assert _annualized_vol(r) == 0.0

    def test_known_vol(self):
        r = pd.Series([0.01] * 252)
        assert _annualized_vol(r) == 0.0

    def test_random_vol(self):
        np.random.seed(0)
        r = pd.Series(np.random.normal(0, 0.01, 252))
        result = _annualized_vol(r)
        assert result > 0
        assert result * 100 < 50


class TestDownsideVol:
    def test_no_negative(self):
        r = pd.Series([0.01, 0.02, 0.03])
        assert _downside_vol(r) == 0.0

    def test_with_negatives(self):
        r = pd.Series([-0.01, 0.02, -0.02, 0.01])
        result = _downside_vol(r)
        assert result > 0

    def test_empty(self):
        assert _downside_vol(pd.Series([])) == 0.0


class TestMaxDrawdown:
    def test_increasing(self):
        r = pd.Series([0.01] * 100)
        assert _max_drawdown(r) == 0.0

    def test_single_drop(self):
        r = pd.Series([0.0, 0.0, -0.5, 0.1])
        # Cumulative: 1, 1, 0.5, 0.55 => max dd = (0.5 - 1) / 1 = 0.5 = 50%
        result = _max_drawdown(r)
        assert abs(result - 50.0) < 0.01

    def test_no_drawdown(self):
        r = pd.Series([0.05, 0.03, 0.02])
        result = _max_drawdown(r)
        assert result >= 0

    def test_short_series(self):
        assert _max_drawdown(pd.Series([0.01])) == 0.0


class TestValueAtRisk:
    def test_known_distribution(self):
        np.random.seed(0)
        r = pd.Series(np.random.normal(0, 0.02, 1000))
        result = _value_at_risk(r)
        assert result > 0

    def test_short_series(self):
        assert _value_at_risk(pd.Series([0.01])) == 0.0


class TestConditionalVar:
    def test_known_distribution(self):
        np.random.seed(0)
        r = pd.Series(np.random.normal(0, 0.02, 1000))
        result = _conditional_var(r)
        assert result > 0
        assert result > _value_at_risk(r)

    def test_short_series(self):
        assert _conditional_var(pd.Series([0.01])) == 0.0


class TestRSquared:
    def test_perfect_correlation(self):
        np.random.seed(0)
        x = pd.Series(np.random.normal(0, 0.01, 100))
        y = x * 2
        result = _r_squared(x, y)
        assert abs(result - 1.0) < 0.01

    def test_no_correlation(self):
        np.random.seed(0)
        x = pd.Series(np.random.normal(0, 0.01, 100))
        y = pd.Series(np.random.normal(0, 0.01, 100))
        result = _r_squared(x, y)
        assert 0 <= result <= 0.3

    def test_insufficient_data(self):
        x = pd.Series([0.01, 0.02])
        y = pd.Series([0.03, 0.04])
        assert _r_squared(x, y) == 0.0

    def test_empty_intersection(self):
        x = pd.Series([0.01, 0.02], index=[1, 2])
        y = pd.Series([0.03, 0.04], index=[3, 4])
        assert _r_squared(x, y) == 0.0


class TestCalculateFundMetrics:
    def test_empty_fund_dict(self, sample_rf_series, sample_market_prices):
        result = calculate_fund_metrics({}, sample_rf_series, sample_market_prices)
        assert result == {}

    def test_single_fund(self, sample_fund_dict, sample_rf_series, sample_market_prices):
        result = calculate_fund_metrics(sample_fund_dict, sample_rf_series, sample_market_prices)
        assert "TESTFON" in result
        m = result["TESTFON"]
        assert METRIC_TOTAL_RETURN in m
        assert METRIC_SHARPE in m
        assert METRIC_SORTINO in m
        assert METRIC_VOLATILITY in m
        assert METRIC_MAX_DRAWDOWN in m
        assert METRIC_VAR in m
        assert METRIC_CVAR in m
        assert METRIC_BETA in m
        assert METRIC_ALPHA in m
        assert METRIC_INFORMATION_RATIO in m
        assert METRIC_TREYNOR in m
        assert METRIC_ANNUALIZED_RETURN in m

    def test_metrics_reasonable(self, sample_fund_dict, sample_rf_series, sample_market_prices):
        result = calculate_fund_metrics(sample_fund_dict, sample_rf_series, sample_market_prices)
        m = result["TESTFON"]
        assert isinstance(m[METRIC_TOTAL_RETURN], float)
        assert isinstance(m[METRIC_SHARPE], float)
        assert m[METRIC_VOLATILITY] > 0

    def test_multiple_funds(self, sample_rf_series, sample_market_prices):
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        np.random.seed(1)
        fund_dict = {}
        for kod in ["FONA", "FONB"]:
            prices = 100 * np.exp(np.random.normal(0.0008, 0.015, 100).cumsum())
            fund_dict[kod] = pd.DataFrame({"tarih": dates, "fiyat": prices})
        result = calculate_fund_metrics(fund_dict, sample_rf_series, sample_market_prices)
        assert len(result) == 2

    def test_empty_dataframe(self, sample_rf_series, sample_market_prices):
        fund_dict = {"EMPTY": pd.DataFrame()}
        result = calculate_fund_metrics(fund_dict, sample_rf_series, sample_market_prices)
        assert result == {}

    def test_short_dataframe(self, sample_rf_series, sample_market_prices):
        dates = pd.date_range("2024-01-01", periods=2, freq="B")
        df = pd.DataFrame({"tarih": dates, "fiyat": [100, 101]})
        fund_dict = {"SHORT": df}
        result = calculate_fund_metrics(fund_dict, sample_rf_series, sample_market_prices)
        assert result == {"SHORT": {}} or result == {}


class TestCalculateMixMetrics:
    def test_none_series(self, sample_rf_series, sample_market_prices):
        assert calculate_mix_metrics(None, sample_rf_series, sample_market_prices) == {}

    def test_empty_series(self, sample_rf_series, sample_market_prices):
        assert calculate_mix_metrics(pd.Series([], dtype=float), sample_rf_series, sample_market_prices) == {}

    def test_valid_series(self, sample_rf_series, sample_market_prices):
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        series = pd.Series(np.linspace(0, 10, 100), index=dates)
        result = calculate_mix_metrics(series, sample_rf_series, sample_market_prices, "Test Mix")
        assert result
        assert METRIC_TOTAL_RETURN in result
        assert METRIC_SHARPE in result

    def test_short_series(self, sample_rf_series, sample_market_prices):
        series = pd.Series([0, 1])
        result = calculate_mix_metrics(series, sample_rf_series, sample_market_prices)
        assert result == {}


class TestGetFundBenchmarks:
    def test_returns_dict_with_keys(self):
        result = get_fund_benchmarks("TEST")
        assert "benchmarks" in result
        assert "source" in result
        assert "message" in result

    def test_known_fund(self):
        result = get_fund_benchmarks("MAC")
        assert isinstance(result["benchmarks"], list)


class TestEdgeCases:
    def test_single_fund_no_benchmark(self):
        dates = pd.date_range("2024-01-01", periods=50, freq="B")
        np.random.seed(5)
        prices = 100 * np.exp(np.random.normal(0.001, 0.02, 50).cumsum())
        fund_dict = {"EDGE": pd.DataFrame({"tarih": dates, "fiyat": prices})}
        rf = pd.Series([0.0005] * 50, index=dates)
        market = pd.Series(np.linspace(1000, 1100, 50), index=dates)
        result = calculate_fund_metrics(fund_dict, rf, market)
        assert "EDGE" in result

    def test_all_same_prices(self):
        dates = pd.date_range("2024-01-01", periods=50, freq="B")
        prices = [100] * 50
        fund_dict = {"FLAT": pd.DataFrame({"tarih": dates, "fiyat": prices})}
        rf = pd.Series([0.0005] * 50, index=dates)
        market = pd.Series(np.linspace(1000, 1100, 50), index=dates)
        result = calculate_fund_metrics(fund_dict, rf, market)
        assert "FLAT" in result
        m = result["FLAT"]
        if m:
            assert m[METRIC_TOTAL_RETURN] == 0.0

    def test_missing_columns(self, sample_rf_series, sample_market_prices):
        df = pd.DataFrame({"wrong_col": [1, 2, 3]})
        fund_dict = {"BAD": df}
        result = calculate_fund_metrics(fund_dict, sample_rf_series, sample_market_prices)
        assert result == {}

    def test_negative_prices(self, sample_rf_series, sample_market_prices):
        dates = pd.date_range("2024-01-01", periods=50, freq="B")
        prices = [100] * 25 + [-1] * 25
        fund_dict = {"NEG": pd.DataFrame({"tarih": dates, "fiyat": prices})}
        result = calculate_fund_metrics(fund_dict, sample_rf_series, sample_market_prices)
        assert "NEG" in result
