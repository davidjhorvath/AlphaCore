import pandas as pd

from src.backtest import calculate_strategy_returns, calculate_turnover


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
            0.00,  # first month has no previous weights
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