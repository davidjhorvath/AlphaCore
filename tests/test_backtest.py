import pandas as pd

from src.backtest import (
    build_signal_lag_scenarios,
    build_transaction_cost_scenarios,
    calculate_strategy_returns,
    calculate_turnover,
)


def test_calculate_strategy_returns_uses_prior_period_weights():
    """
    Critical anti-look-ahead test.

    Weights at time t must be applied to returns at time t+1,
    not to returns at time t.
    """
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")

    returns = pd.DataFrame(
        {
            "SPY": [0.10, 0.20, 0.30],
            "SHY": [0.01, 0.01, 0.01],
        },
        index=dates,
    )

    weights = pd.DataFrame(
        {
            "SPY": [1.0, 0.0, 0.0],
            "SHY": [0.0, 1.0, 1.0],
        },
        index=dates,
    )

    strategy_returns = calculate_strategy_returns(
        returns=returns,
        weights=weights,
        signal_lag=1,
    )

    expected = pd.Series(
        [
            float("nan"),  # first month has no previous weights
            0.20,  # uses Jan weights: 100% SPY applied to Feb returns
            0.01,  # uses Feb weights: 100% SHY applied to Mar returns
        ],
        index=dates,
    )

    pd.testing.assert_series_equal(
        strategy_returns,
        expected,
        check_names=False,
    )


def test_first_valid_strategy_return_matches_benchmark_sample_start():
    """The signal-lag warm-up month must not become an artificial zero return."""
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    returns = pd.DataFrame(
        {
            "SPY": [float("nan"), 0.20, 0.30],
            "SHY": [float("nan"), 0.01, 0.01],
        },
        index=dates,
    )
    weights = pd.DataFrame(
        {
            "SPY": [1.0, 0.0, 0.0],
            "SHY": [0.0, 1.0, 1.0],
        },
        index=dates,
    )

    strategy_returns = calculate_strategy_returns(
        returns=returns,
        weights=weights,
        signal_lag=1,
    )

    assert strategy_returns.first_valid_index() == returns["SPY"].first_valid_index()


def test_calculate_strategy_returns_signal_lag_zero_uses_same_period_weights():
    """
    signal_lag=0 is not used for real backtests, but this test confirms
    that lagged and unlagged returns are intentionally different.
    """
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")

    returns = pd.DataFrame(
        {
            "SPY": [0.10, 0.20, 0.30],
            "SHY": [0.01, 0.01, 0.01],
        },
        index=dates,
    )

    weights = pd.DataFrame(
        {
            "SPY": [1.0, 0.0, 0.0],
            "SHY": [0.0, 1.0, 1.0],
        },
        index=dates,
    )

    lagged_returns = calculate_strategy_returns(
        returns=returns,
        weights=weights,
        signal_lag=1,
    )

    same_period_returns = calculate_strategy_returns(
        returns=returns,
        weights=weights,
        signal_lag=0,
    )

    assert not lagged_returns.equals(same_period_returns)


def test_calculate_turnover_known_example():
    """
    Test portfolio turnover on a simple known example.
    """
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")

    weights = pd.DataFrame(
        {
            "SPY": [1.0, 0.5, 0.0],
            "SHY": [0.0, 0.5, 1.0],
        },
        index=dates,
    )

    turnover = calculate_turnover(weights)

    expected = pd.Series(
        [
            0.5,  # initial invested portfolio: sum abs weights / 2
            0.5,  # abs changes: 0.5 + 0.5 = 1.0 / 2
            0.5,
        ],
        index=dates,
    )

    pd.testing.assert_series_equal(
        turnover,
        expected,
        check_names=False,
    )


def test_calculate_turnover_charges_first_allocation_after_leading_nan():
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    weights = pd.DataFrame(
        {
            "SPY": [float("nan"), 0.60, 0.50],
            "SHY": [float("nan"), 0.40, 0.50],
        },
        index=dates,
    )

    turnover = calculate_turnover(weights)

    expected = pd.Series([float("nan"), 0.50, 0.10], index=dates)
    pd.testing.assert_series_equal(turnover, expected, check_names=False)


def test_transaction_cost_scenarios_apply_exact_bps_to_same_turnover():
    dates = pd.date_range("2020-01-31", periods=2, freq="ME")
    gross_returns = pd.Series([0.02, 0.01], index=dates)
    turnover = pd.Series([0.50, 1.00], index=dates)

    result = build_transaction_cost_scenarios(
        strategy_returns=gross_returns,
        turnover=turnover,
        cost_bps_levels=(10, 25, 50),
    )

    expected = pd.DataFrame(
        {
            "AlphaCore_net_10bps": [0.0195, 0.0090],
            "AlphaCore_net_25bps": [0.01875, 0.0075],
            "AlphaCore_net_50bps": [0.0175, 0.0050],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(result, expected)
    assert (result["AlphaCore_net_10bps"] >= result["AlphaCore_net_25bps"]).all()
    assert (result["AlphaCore_net_25bps"] >= result["AlphaCore_net_50bps"]).all()


def test_signal_lag_scenarios_use_common_sample_and_equal_initial_cost():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")
    returns = pd.DataFrame(
        {
            "SPY": [0.10, 0.20, 0.30, 0.40],
            "SHY": [0.01, 0.02, 0.03, 0.04],
        },
        index=dates,
    )
    weights = pd.DataFrame(
        {
            "SPY": [1.0, 0.0, 1.0, 0.0],
            "SHY": [0.0, 1.0, 0.0, 1.0],
        },
        index=dates,
    )

    scenarios, turnover = build_signal_lag_scenarios(
        returns=returns,
        weights=weights,
        signal_lags=(1, 2),
        cost_bps=10,
    )

    expected_returns = pd.DataFrame(
        {
            "AlphaCore_net_lag_1m": [0.0295, 0.3990],
            "AlphaCore_net_lag_2m": [0.2995, 0.0390],
        },
        index=dates[2:],
    )
    expected_turnover = pd.DataFrame(
        {
            "AlphaCore_net_lag_1m": [0.5, 1.0],
            "AlphaCore_net_lag_2m": [0.5, 1.0],
        },
        index=dates[2:],
    )

    pd.testing.assert_frame_equal(scenarios, expected_returns)
    pd.testing.assert_frame_equal(turnover, expected_turnover)
