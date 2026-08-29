import pandas as pd

from src.performance import (
    max_drawdown,
    moving_block_bootstrap_metrics,
    start_date_sensitivity_summary,
)


def test_max_drawdown_includes_initial_capital_peak():
    returns = pd.Series([-0.10, 0.05])

    assert abs(max_drawdown(returns) - (-0.10)) < 1e-12


def test_start_date_sensitivity_uses_common_strategy_benchmark_sample():
    dates = pd.date_range("2020-01-31", periods=24, freq="ME")
    monthly_returns = [0.01 if month % 2 == 0 else -0.005 for month in range(24)]
    strategy = pd.Series(monthly_returns, index=dates)
    benchmark = pd.Series(monthly_returns, index=dates)
    benchmark.iloc[0] = float("nan")
    returns = pd.DataFrame(
        {
            "AlphaCore_net": strategy,
            "balanced_60_40": benchmark,
        }
    )

    result = start_date_sensitivity_summary(
        returns=returns,
        start_years=(2020, 2021),
    )

    assert result.loc[2020, "sample_start"] == "2020-02-29"
    assert result.loc[2020, "months"] == 23
    assert result.loc[2021, "sample_start"] == "2021-01-31"
    assert result.loc[2021, "months"] == 12
    assert (result["CAGR_spread"].abs() < 1e-12).all()
    assert (result["Sharpe_spread"].abs() < 1e-12).all()


def test_moving_block_bootstrap_is_paired_and_reproducible():
    dates = pd.date_range("2020-01-31", periods=24, freq="ME")
    monthly_returns = pd.Series(
        [0.02 if month % 3 else -0.01 for month in range(24)],
        index=dates,
    )
    risk_free = pd.Series(0.001, index=dates)

    first = moving_block_bootstrap_metrics(
        strategy_returns=monthly_returns,
        benchmark_returns=monthly_returns,
        risk_free_returns=risk_free,
        iterations=100,
        block_length=6,
        seed=7,
    )
    second = moving_block_bootstrap_metrics(
        strategy_returns=monthly_returns,
        benchmark_returns=monthly_returns,
        risk_free_returns=risk_free,
        iterations=100,
        block_length=6,
        seed=7,
    )

    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 100
    assert (first["CAGR_spread"].abs() < 1e-12).all()
    assert (first["Sharpe_spread"].abs() < 1e-12).all()
    assert (first["drawdown_improvement"].abs() < 1e-12).all()
