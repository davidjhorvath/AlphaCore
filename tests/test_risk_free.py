import numpy as np
import pandas as pd

from src.data_loader import (
    align_risk_free_to_monthly,
    annual_yield_percent_to_monthly_return,
)
from src.performance import (
    alpha_vs_benchmark,
    performance_summary,
    relative_metrics_summary,
    rolling_sharpe,
    sharpe_ratio,
    sortino_ratio,
)


DATES = pd.DatetimeIndex(
    ["2020-01-31", "2020-02-29", "2020-03-31", "2020-04-30"]
)


def test_cmt_yield_percentage_converts_to_monthly_proxy():
    annual_yield = pd.Series([0.0, 12.0])

    result = annual_yield_percent_to_monthly_return(annual_yield)

    expected = pd.Series([0.0, (1 + 0.12 / 2) ** (1 / 6) - 1])
    pd.testing.assert_series_equal(result, expected)


def test_monthly_alignment_uses_previous_month_last_available_yield():
    daily_yields = pd.Series(
        [1.0, 2.0, 3.0, 4.0],
        index=pd.to_datetime(
            ["2020-01-15", "2020-01-31", "2020-02-03", "2020-02-28"]
        ),
        name="DGS3MO",
    )

    result = align_risk_free_to_monthly(daily_yields)

    expected_index = pd.DatetimeIndex(
        ["2020-02-29", "2020-03-31"], name="Date"
    )
    expected_values = annual_yield_percent_to_monthly_return(
        pd.Series([2.0, 4.0])
    ).to_numpy()
    expected = pd.DataFrame(
        {"risk_free_return": expected_values}, index=expected_index
    )
    pd.testing.assert_frame_equal(result, expected)


def test_sharpe_uses_time_varying_risk_free_returns():
    returns = pd.Series([0.02, 0.01, -0.01, 0.03], index=DATES)
    risk_free = pd.Series([0.001, 0.002, 0.003, 0.004], index=DATES)
    excess = returns - risk_free

    expected = excess.mean() / excess.std() * np.sqrt(12)

    assert np.isclose(sharpe_ratio(returns, risk_free), expected)


def test_sortino_uses_time_varying_risk_free_returns():
    returns = pd.Series([0.02, -0.01, -0.03, 0.01], index=DATES)
    risk_free = pd.Series([0.001, 0.002, 0.003, 0.004], index=DATES)
    excess = returns - risk_free
    shortfall = np.minimum(excess, 0.0)

    expected = excess.mean() / np.sqrt(np.mean(shortfall ** 2)) * np.sqrt(12)

    assert np.isclose(sortino_ratio(returns, risk_free), expected)


def test_alpha_uses_capm_excess_returns():
    benchmark_excess = pd.Series([0.01, -0.02, 0.03, -0.01], index=DATES)
    risk_free = pd.Series([0.001, 0.002, 0.003, 0.004], index=DATES)
    monthly_alpha = 0.002
    beta = 0.5
    benchmark = benchmark_excess + risk_free
    strategy = monthly_alpha + beta * benchmark_excess + risk_free

    result = alpha_vs_benchmark(
        strategy,
        benchmark,
        risk_free_rate=risk_free,
    )

    assert np.isclose(result, monthly_alpha * 12)


def test_relative_summary_beta_matches_capm_excess_return_beta():
    benchmark_excess = pd.Series([0.01, -0.02, 0.03, -0.01], index=DATES)
    risk_free = pd.Series([0.001, 0.002, 0.003, 0.004], index=DATES)
    expected_beta = 0.5
    benchmark = benchmark_excess + risk_free
    strategy = 0.002 + expected_beta * benchmark_excess + risk_free
    returns = pd.DataFrame({"AlphaCore_net": strategy, "SPY": benchmark})

    summary = relative_metrics_summary(
        returns,
        strategy_columns=["AlphaCore_net"],
        benchmark="SPY",
        risk_free_returns=risk_free,
    )

    assert np.isclose(summary.loc["AlphaCore_net", "beta"], expected_beta)
    assert np.isclose(summary.loc["AlphaCore_net", "alpha_annualized"], 0.002 * 12)


def test_rolling_sharpe_uses_time_varying_risk_free_returns():
    returns = pd.Series([0.02, 0.01, -0.01, 0.03], index=DATES)
    risk_free = pd.Series([0.001, 0.002, 0.003, 0.004], index=DATES)
    excess = returns - risk_free

    result = rolling_sharpe(returns, window=3, risk_free_rate=risk_free)
    expected = (
        excess.rolling(3).mean() / excess.rolling(3).std() * np.sqrt(12)
    )

    pd.testing.assert_series_equal(result, expected)


def test_rolling_sharpe_requires_consecutive_calendar_months():
    dates_with_gap = pd.DatetimeIndex(
        ["2020-01-31", "2020-03-31", "2020-04-30"]
    )
    returns = pd.Series([0.02, -0.01, 0.03], index=dates_with_gap)
    risk_free = pd.Series([0.001, 0.003, 0.004], index=dates_with_gap)

    result = rolling_sharpe(returns, window=3, risk_free_rate=risk_free)

    assert result.isna().all()


def test_risk_free_alignment_drops_only_missing_dates():
    returns = pd.Series([0.02, 0.01, -0.01, 0.03], index=DATES)
    risk_free = pd.Series(
        [0.001, 0.003, 0.004],
        index=DATES.delete(1),
    )
    excess = returns.loc[risk_free.index] - risk_free

    expected = excess.mean() / excess.std() * np.sqrt(12)

    assert np.isclose(sharpe_ratio(returns, risk_free), expected)


def test_performance_summary_reports_risk_adjusted_observation_count():
    returns = pd.DataFrame({"strategy": [0.02, 0.01, -0.01, 0.03]}, index=DATES)
    risk_free = pd.Series([0.001, 0.003, 0.004], index=DATES.delete(1))

    summary = performance_summary(returns, risk_free)

    assert summary.loc["strategy", "months"] == 4
    assert summary.loc["strategy", "risk_adjusted_months"] == 3
