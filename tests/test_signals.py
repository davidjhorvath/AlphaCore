import pandas as pd

from src.signals import calculate_signal_scores, cross_sectional_rank


def test_cross_sectional_rank_higher_is_better():
    dates = pd.date_range("2020-01-31", periods=2, freq="ME")

    feature = pd.DataFrame(
        {
            "SPY": [10.0, 30.0],
            "QQQ": [20.0, 20.0],
            "SHY": [30.0, 10.0],
        },
        index=dates,
    )

    ranked = cross_sectional_rank(
        feature=feature,
        higher_is_better=True,
    )

    expected = pd.DataFrame(
        {
            "SPY": [1 / 3, 1.0],
            "QQQ": [2 / 3, 2 / 3],
            "SHY": [1.0, 1 / 3],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(ranked, expected)


def test_cross_sectional_rank_lower_is_better():
    dates = pd.date_range("2020-01-31", periods=2, freq="ME")

    feature = pd.DataFrame(
        {
            "SPY": [10.0, 30.0],
            "QQQ": [20.0, 20.0],
            "SHY": [30.0, 10.0],
        },
        index=dates,
    )

    ranked = cross_sectional_rank(
        feature=feature,
        higher_is_better=False,
    )

    expected = pd.DataFrame(
        {
            "SPY": [1.0, 1 / 3],
            "QQQ": [2 / 3, 2 / 3],
            "SHY": [1 / 3, 1.0],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(ranked, expected)


def test_cross_sectional_rank_handles_nan_values():
    dates = pd.date_range("2020-01-31", periods=1, freq="ME")

    feature = pd.DataFrame(
        {
            "SPY": [10.0],
            "QQQ": [float("nan")],
            "SHY": [30.0],
        },
        index=dates,
    )

    ranked = cross_sectional_rank(
        feature=feature,
        higher_is_better=True,
    )

    assert ranked.loc[dates[0], "QQQ"] != ranked.loc[dates[0], "QQQ"]
    assert ranked.loc[dates[0], "SPY"] == 0.5
    assert ranked.loc[dates[0], "SHY"] == 1.0


def test_total_score_formula_manual_example():
    """
    Manual test of the AlphaCore v1 scoring formula:

    total_score =
        40% trend
      + 40% momentum_rank
      + 10% volatility_rank
      + 10% drawdown_rank

    This does not call build_signal_scores because that function loads files.
    It tests the formula logic independently.
    """
    dates = pd.date_range("2020-01-31", periods=1, freq="ME")

    trend = pd.DataFrame(
        {
            "SPY": [1.0],
            "QQQ": [1.0],
            "SHY": [0.0],
        },
        index=dates,
    )

    momentum = pd.DataFrame(
        {
            "SPY": [0.30],
            "QQQ": [0.20],
            "SHY": [0.10],
        },
        index=dates,
    )

    volatility = pd.DataFrame(
        {
            "SPY": [0.20],
            "QQQ": [0.30],
            "SHY": [0.10],
        },
        index=dates,
    )

    drawdown = pd.DataFrame(
        {
            "SPY": [-0.10],
            "QQQ": [-0.20],
            "SHY": [0.00],
        },
        index=dates,
    )

    scores = calculate_signal_scores(
        trend=trend,
        momentum=momentum,
        volatility=volatility,
        drawdown=drawdown,
    )

    expected = pd.DataFrame(
        {
            "SPY": [0.40 + 0.40 + 0.10 * (2 / 3) + 0.10 * (2 / 3)],
            "QQQ": [0.40 + 0.40 * (2 / 3) + 0.10 / 3 + 0.10 / 3],
            "SHY": [float("nan")],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(scores["total_score"], expected)


def test_investable_filter_manual_example():
    """
    Investable rule:
    ETF is investable only if trend == 1 and momentum > 0.
    """
    dates = pd.date_range("2020-01-31", periods=1, freq="ME")

    trend = pd.DataFrame(
        {
            "SPY": [1.0],
            "QQQ": [0.0],
            "SHY": [1.0],
        },
        index=dates,
    )

    momentum = pd.DataFrame(
        {
            "SPY": [0.10],
            "QQQ": [0.20],
            "SHY": [-0.01],
        },
        index=dates,
    )

    investable = (trend == 1.0) & (momentum > 0)

    expected = pd.DataFrame(
        {
            "SPY": [True],
            "QQQ": [False],
            "SHY": [False],
        },
        index=dates,
    )

    pd.testing.assert_frame_equal(investable, expected)
