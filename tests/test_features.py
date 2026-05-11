import pandas as pd

from src.features import (
    calculate_momentum,
    calculate_composite_momentum,
    calculate_moving_average,
    calculate_trend_signal,
    calculate_drawdown,
)


def test_calculate_momentum_known_values():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")

    prices = pd.DataFrame(
        {
            "SPY": [100.0, 110.0, 121.0, 133.1],
        },
        index=dates,
    )

    momentum = calculate_momentum(prices, window=1)

    expected = pd.DataFrame(
        {
            "SPY": [float("nan"), 0.10, 0.10, 0.10],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(momentum, expected)


def test_calculate_composite_momentum_known_values():
    dates = pd.date_range("2020-01-31", periods=13, freq="ME")

    prices = pd.DataFrame(
        {
            "SPY": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
            ],
        },
        index=dates,
    )

    composite = calculate_composite_momentum(
        prices,
        weights={
            3: 0.25,
            6: 0.25,
            12: 0.50,
        },
    )

    last_date = dates[-1]

    m3 = prices["SPY"].pct_change(3).loc[last_date]
    m6 = prices["SPY"].pct_change(6).loc[last_date]
    m12 = prices["SPY"].pct_change(12).loc[last_date]

    expected_last_value = 0.25 * m3 + 0.25 * m6 + 0.50 * m12

    assert composite.loc[last_date, "SPY"] == expected_last_value

    # Composite momentum should be NaN before the 12-month component exists.
    assert composite["SPY"].iloc[:12].isna().all()


def test_calculate_moving_average_known_values():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")

    prices = pd.DataFrame(
        {
            "SPY": [100.0, 110.0, 120.0, 130.0],
        },
        index=dates,
    )

    moving_average = calculate_moving_average(prices, window=2)

    expected = pd.DataFrame(
        {
            "SPY": [float("nan"), 105.0, 115.0, 125.0],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(moving_average, expected)


def test_calculate_trend_signal_known_values():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")

    prices = pd.DataFrame(
        {
            "SPY": [100.0, 110.0, 90.0, 130.0],
        },
        index=dates,
    )

    trend = calculate_trend_signal(prices, window=2)

    expected = pd.DataFrame(
        {
            # MA values:
            # Jan: NaN
            # Feb: 105, price 110 > 105 => 1
            # Mar: 100, price 90 > 100 => 0
            # Apr: 110, price 130 > 110 => 1
            "SPY": [float("nan"), 1.0, 0.0, 1.0],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(trend, expected)


def test_calculate_drawdown_known_values():
    dates = pd.date_range("2020-01-31", periods=5, freq="ME")

    prices = pd.DataFrame(
        {
            "SPY": [100.0, 120.0, 90.0, 150.0, 75.0],
        },
        index=dates,
    )

    drawdown = calculate_drawdown(prices)

    expected = pd.DataFrame(
        {
            "SPY": [
                0.0,
                0.0,
                -0.25,  # 90 / 120 - 1
                0.0,
                -0.50,  # 75 / 150 - 1
            ],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(drawdown, expected)