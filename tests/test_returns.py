import pandas as pd

from src.performance import start_date_sensitivity_summary


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
