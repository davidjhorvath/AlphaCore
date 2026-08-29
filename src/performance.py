from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.backtest import (
        build_benchmark_returns,
        build_signal_lag_scenarios,
        build_transaction_cost_scenarios,
        calculate_strategy_returns,
        calculate_turnover,
        load_monthly_returns,
        load_monthly_weights,
    )
    from src.data_loader import load_risk_free_data
    from src.features import calculate_trend_signal, load_monthly_prices
    from src.portfolio import build_monthly_weights_from_signals
    from src.signals import calculate_signal_scores, load_feature
except ModuleNotFoundError:
    from backtest import (
        build_benchmark_returns,
        build_signal_lag_scenarios,
        build_transaction_cost_scenarios,
        calculate_strategy_returns,
        calculate_turnover,
        load_monthly_returns,
        load_monthly_weights,
    )
    from data_loader import load_risk_free_data
    from features import calculate_trend_signal, load_monthly_prices
    from portfolio import build_monthly_weights_from_signals
    from signals import calculate_signal_scores, load_feature


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _monthly_excess_returns(
    returns: pd.Series,
    risk_free_rate: float | pd.Series,
    periods_per_year: int,
) -> pd.Series:
    """Align returns with monthly risk-free returns and calculate excess returns."""
    if isinstance(risk_free_rate, pd.Series):
        aligned = pd.concat(
            [returns.rename("return"), risk_free_rate.rename("risk_free_return")],
            axis=1,
            sort=False,
        ).dropna()
        return aligned["return"] - aligned["risk_free_return"]

    return returns.dropna() - (risk_free_rate / periods_per_year)


def _calendar_monthly_excess_returns(
    returns: pd.Series,
    risk_free_rate: float | pd.Series,
    periods_per_year: int,
) -> pd.Series:
    """Calculate excess returns on a complete month-end calendar without filling."""
    returns = returns.copy()
    returns.index = pd.to_datetime(returns.index)

    if returns.empty:
        return returns

    monthly_index = pd.period_range(
        returns.index.min().to_period("M"),
        returns.index.max().to_period("M"),
        freq="M",
    ).to_timestamp("M")
    calendar_returns = returns.reindex(monthly_index)

    if isinstance(risk_free_rate, pd.Series):
        risk_free_returns = risk_free_rate.copy()
        risk_free_returns.index = pd.to_datetime(risk_free_returns.index)
        return calendar_returns - risk_free_returns.reindex(monthly_index)

    return calendar_returns - (risk_free_rate / periods_per_year)


def _aligned_capm_excess_returns(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float | pd.Series,
    periods_per_year: int,
) -> pd.DataFrame:
    """Align CAPM inputs and return strategy and benchmark excess returns."""
    series = [
        strategy_returns.rename("strategy"),
        benchmark_returns.rename("benchmark"),
    ]
    if isinstance(risk_free_rate, pd.Series):
        series.append(risk_free_rate.rename("risk_free"))

    data = pd.concat(series, axis=1, sort=False).dropna()
    if data.empty:
        return pd.DataFrame(columns=["strategy_excess", "benchmark_excess"])

    if isinstance(risk_free_rate, pd.Series):
        monthly_risk_free = data["risk_free"]
    else:
        monthly_risk_free = risk_free_rate / periods_per_year

    return pd.DataFrame(
        {
            "strategy_excess": data["strategy"] - monthly_risk_free,
            "benchmark_excess": data["benchmark"] - monthly_risk_free,
        },
        index=data.index,
    )


def _beta_from_excess_returns(excess_returns: pd.DataFrame) -> float:
    """Estimate CAPM beta from aligned strategy and benchmark excess returns."""
    if excess_returns.empty:
        return np.nan

    benchmark_variance = excess_returns["benchmark_excess"].var()
    if benchmark_variance == 0 or np.isnan(benchmark_variance):
        return np.nan

    return (
        excess_returns["strategy_excess"].cov(
            excess_returns["benchmark_excess"]
        )
        / benchmark_variance
    )


def load_backtest_returns() -> pd.DataFrame:
    """
    Load AlphaCore v1 backtest returns.
    """
    path = PROJECT_ROOT / "data" / "processed" / "backtests" / "alphacore_v1_returns.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Backtest results not found. Run src/backtest.py first."
        )

    return pd.read_parquet(path)


def cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    Calculate cumulative return curve.
    """
    returns = returns.dropna()
    return (1 + returns).cumprod()


def cagr(returns: pd.Series, periods_per_year: int = 12) -> float:
    """
    Compound annual growth rate.
    """
    returns = returns.dropna()

    if returns.empty:
        return np.nan

    total_return = (1 + returns).prod()
    years = len(returns) / periods_per_year

    if years <= 0:
        return np.nan

    return total_return ** (1 / years) - 1


def annualized_volatility(returns: pd.Series, periods_per_year: int = 12) -> float:
    """
    Annualized volatility.
    """
    returns = returns.dropna()

    if returns.empty:
        return np.nan

    return returns.std() * np.sqrt(periods_per_year)


def sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float | pd.Series = 0.0,
    periods_per_year: int = 12,
) -> float:
    """
    Annualized Sharpe ratio.

    A scalar risk-free rate is interpreted as an annual rate for backward
    compatibility. A Series must contain monthly decimal returns.
    """
    excess_returns = _monthly_excess_returns(
        returns, risk_free_rate, periods_per_year
    )

    if excess_returns.empty:
        return np.nan

    vol = excess_returns.std()

    if vol == 0:
        return np.nan

    return excess_returns.mean() / vol * np.sqrt(periods_per_year)


def sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float | pd.Series = 0.0,
    periods_per_year: int = 12,
) -> float:
    """
    Annualized Sortino ratio.
    """
    excess_returns = _monthly_excess_returns(
        returns, risk_free_rate, periods_per_year
    )

    if excess_returns.empty:
        return np.nan

    shortfall = np.minimum(excess_returns, 0.0)
    downside_deviation = np.sqrt(np.mean(shortfall ** 2))

    if downside_deviation == 0 or np.isnan(downside_deviation):
        return np.nan

    return excess_returns.mean() / downside_deviation * np.sqrt(periods_per_year)


def max_drawdown(returns: pd.Series) -> float:
    """
    Maximum drawdown from cumulative return curve.
    """
    wealth = cumulative_returns(returns)

    if wealth.empty:
        return np.nan

    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1

    return drawdown.min()


def calmar_ratio(returns: pd.Series) -> float:
    """
    Calmar ratio = CAGR / absolute max drawdown.
    """
    strategy_cagr = cagr(returns)
    mdd = max_drawdown(returns)

    if mdd == 0 or np.isnan(mdd):
        return np.nan

    return strategy_cagr / abs(mdd)


def hit_rate(returns: pd.Series) -> float:
    """
    Share of positive months.
    """
    returns = returns.dropna()

    if returns.empty:
        return np.nan

    return (returns > 0).mean()


def cumulative_total_return(returns: pd.Series) -> float:
    """
    Total cumulative return over the full period.
    """
    returns = returns.dropna()

    if returns.empty:
        return np.nan

    return (1 + returns).prod() - 1


def performance_summary(
    returns: pd.DataFrame,
    risk_free_returns: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Create performance summary for all return columns.
    """
    return_columns = [
        col for col in returns.columns
        if col != "turnover"
    ]

    rows = []

    for col in return_columns:
        series = returns[col].dropna()

        rows.append({
            "strategy": col,
            "months": len(series),
            "risk_adjusted_months": len(
                _monthly_excess_returns(
                    series,
                    risk_free_returns if risk_free_returns is not None else 0.0,
                    12,
                )
            ),
            "cumulative_return": cumulative_total_return(series),
            "CAGR": cagr(series),
            "annualized_volatility": annualized_volatility(series),
            "Sharpe": sharpe_ratio(
                series, risk_free_returns if risk_free_returns is not None else 0.0
            ),
            "Sortino": sortino_ratio(
                series, risk_free_returns if risk_free_returns is not None else 0.0
            ),
            "max_drawdown": max_drawdown(series),
            "Calmar": calmar_ratio(series),
            "hit_rate": hit_rate(series),
        })

    summary = pd.DataFrame(rows).set_index("strategy")

    return summary


def run_performance_report() -> pd.DataFrame:
    """
    Run AlphaCore v1 performance report.
    """
    returns = load_backtest_returns()
    risk_free_returns = load_risk_free_data()["risk_free_return"]
    summary = performance_summary(returns, risk_free_returns)

    if "turnover" in returns.columns:
        avg_turnover = returns["turnover"].dropna().mean()
        summary.loc["AlphaCore_net", "avg_monthly_turnover"] = avg_turnover

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary.to_csv(output_dir / "alphacore_v1_performance_summary.csv")

    print("Performance report completed successfully.")
    print(f"Report saved to: {output_dir / 'alphacore_v1_performance_summary.csv'}")
    print()
    print(summary.sort_values(by="Sharpe", ascending=False))

    return summary


def run_transaction_cost_sensitivity_report(
    cost_bps_levels: tuple[float, ...] = (10, 25, 50),
) -> pd.DataFrame:
    """Stress test fixed AlphaCore returns under higher trading costs."""
    returns = load_backtest_returns()
    risk_free_returns = load_risk_free_data()["risk_free_return"]

    scenarios = build_transaction_cost_scenarios(
        strategy_returns=returns["AlphaCore_gross"],
        turnover=returns["turnover"],
        cost_bps_levels=cost_bps_levels,
    )
    summary = performance_summary(scenarios, risk_free_returns)
    summary.insert(0, "transaction_cost_bps", list(cost_bps_levels))
    summary["CAGR_vs_balanced_60_40"] = (
        summary["CAGR"] - cagr(returns["balanced_60_40"])
    )
    summary["avg_monthly_turnover"] = returns["turnover"].dropna().mean()

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alphacore_v1_transaction_cost_sensitivity.csv"
    summary.to_csv(output_path)

    print("Transaction-cost sensitivity report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(summary.to_string())

    return summary


def run_signal_lag_sensitivity_report(
    signal_lags: tuple[int, ...] = (1, 2),
    cost_bps: float = 10,
) -> pd.DataFrame:
    """Stress test a one-month additional delay on a common sample."""
    returns = load_monthly_returns()
    weights = load_monthly_weights()
    risk_free_returns = load_risk_free_data()["risk_free_return"]

    scenarios, turnover = build_signal_lag_scenarios(
        returns=returns,
        weights=weights,
        signal_lags=signal_lags,
        cost_bps=cost_bps,
    )
    summary = performance_summary(scenarios, risk_free_returns)
    summary.insert(0, "signal_lag_months", list(signal_lags))
    summary.insert(1, "transaction_cost_bps", cost_bps)
    summary.insert(2, "sample_start", scenarios.index.min().date().isoformat())
    summary.insert(3, "sample_end", scenarios.index.max().date().isoformat())
    summary["avg_monthly_turnover"] = [
        turnover[column].mean() for column in scenarios.columns
    ]

    baseline_cagr = summary.iloc[0]["CAGR"]
    common_benchmark_cagr = cagr(
        build_benchmark_returns(returns)
        .loc[scenarios.index, "balanced_60_40"]
    )
    summary["CAGR_vs_lag_1m"] = summary["CAGR"] - baseline_cagr
    summary["CAGR_vs_balanced_60_40"] = summary["CAGR"] - common_benchmark_cagr
    summary["correlation_vs_lag_1m"] = [
        scenarios[column].corr(scenarios.iloc[:, 0])
        for column in scenarios.columns
    ]

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alphacore_v1_signal_lag_sensitivity.csv"
    summary.to_csv(output_path)

    print("Signal-lag sensitivity report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(summary.to_string())

    return summary


def run_trend_window_sensitivity_report(
    trend_windows: tuple[int, ...] = (9, 10, 11),
    signal_lag: int = 1,
    cost_bps: float = 10,
) -> pd.DataFrame:
    """Test nearby trend windows without changing the frozen production model."""
    if 10 not in trend_windows:
        raise ValueError("Trend-window sensitivity requires the 10-month baseline.")

    prices = load_monthly_prices()
    returns = load_monthly_returns()
    frozen_weights = load_monthly_weights()
    risk_free_returns = load_risk_free_data()["risk_free_return"]
    momentum = load_feature("composite_momentum")
    volatility = load_feature("realized_volatility_12m")
    drawdown = load_feature("drawdown")
    spy_momentum_6m = load_feature("momentum_6m")["SPY"]

    gross_scenarios = pd.DataFrame(index=returns.index)
    shifted_weights: dict[int, pd.DataFrame] = {}

    for trend_window in trend_windows:
        trend = calculate_trend_signal(prices, window=trend_window)
        scores = calculate_signal_scores(
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            drawdown=drawdown,
        )
        weights = build_monthly_weights_from_signals(
            total_score=scores["total_score"],
            investable=scores["investable"],
            spy_trend=trend["SPY"],
            spy_momentum_6m=spy_momentum_6m,
            cash_ticker="SHY",
        )

        if trend_window == 10:
            aligned_frozen = frozen_weights.loc[weights.index, weights.columns]
            max_weight_difference = (weights - aligned_frozen).abs().max().max()
            if max_weight_difference > 1e-12:
                raise ValueError(
                    "Reconstructed 10-month weights do not match the frozen model."
                )

        label = f"AlphaCore_net_trend_{trend_window}m"
        gross_scenarios[label] = calculate_strategy_returns(
            returns=returns,
            weights=weights,
            signal_lag=signal_lag,
        )
        shifted_weights[trend_window] = weights.shift(signal_lag)

    common_index = gross_scenarios.dropna().index
    scenarios = pd.DataFrame(index=common_index)
    turnover = pd.DataFrame(index=common_index)

    for trend_window in trend_windows:
        label = f"AlphaCore_net_trend_{trend_window}m"
        scenario_weights = shifted_weights[trend_window].loc[common_index]
        scenario_turnover = calculate_turnover(scenario_weights)
        scenarios[label] = (
            gross_scenarios.loc[common_index, label]
            - scenario_turnover * (cost_bps / 10000)
        )
        turnover[label] = scenario_turnover

    summary = performance_summary(scenarios, risk_free_returns)
    summary.insert(0, "trend_window_months", list(trend_windows))
    summary.insert(1, "signal_lag_months", signal_lag)
    summary.insert(2, "transaction_cost_bps", cost_bps)
    summary.insert(3, "sample_start", scenarios.index.min().date().isoformat())
    summary.insert(4, "sample_end", scenarios.index.max().date().isoformat())
    summary["avg_monthly_turnover"] = [
        turnover[column].mean() for column in scenarios.columns
    ]

    baseline_position = trend_windows.index(10)
    baseline_label = scenarios.columns[baseline_position]
    baseline_cagr = summary.iloc[baseline_position]["CAGR"]
    baseline_weights = shifted_weights[10].loc[common_index]
    common_benchmark_cagr = cagr(
        build_benchmark_returns(returns)
        .loc[common_index, "balanced_60_40"]
    )
    summary["CAGR_vs_10m"] = summary["CAGR"] - baseline_cagr
    summary["CAGR_vs_balanced_60_40"] = summary["CAGR"] - common_benchmark_cagr
    summary["correlation_vs_10m"] = [
        scenarios[column].corr(scenarios[baseline_label])
        for column in scenarios.columns
    ]
    summary["avg_weight_distance_vs_10m"] = [
        (
            (shifted_weights[window].loc[common_index] - baseline_weights)
            .abs()
            .sum(axis=1)
            .div(2)
            .mean()
        )
        for window in trend_windows
    ]
    summary["same_weight_month_fraction_vs_10m"] = [
        (
            (shifted_weights[window].loc[common_index] - baseline_weights)
            .abs()
            .le(1e-12)
            .all(axis=1)
            .mean()
        )
        for window in trend_windows
    ]

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alphacore_v1_trend_window_sensitivity.csv"
    summary.to_csv(output_path)

    print("Trend-window sensitivity report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(summary.to_string())

    return summary


def start_date_sensitivity_summary(
    returns: pd.DataFrame,
    start_years: list[int] | tuple[int, ...],
    strategy: str = "AlphaCore_net",
    benchmark: str = "balanced_60_40",
    risk_free_returns: pd.Series | None = None,
) -> pd.DataFrame:
    """Compare a fixed strategy and benchmark across annual start dates."""
    rows = []

    for start_year in start_years:
        sample = returns.loc[f"{start_year}-01-01":, [strategy, benchmark]].dropna()
        if sample.empty:
            continue

        strategy_returns = sample[strategy]
        benchmark_returns = sample[benchmark]
        risk_free_rate = risk_free_returns if risk_free_returns is not None else 0.0

        strategy_cagr = cagr(strategy_returns)
        benchmark_cagr = cagr(benchmark_returns)
        strategy_sharpe = sharpe_ratio(strategy_returns, risk_free_rate)
        benchmark_sharpe = sharpe_ratio(benchmark_returns, risk_free_rate)
        strategy_drawdown = max_drawdown(strategy_returns)
        benchmark_drawdown = max_drawdown(benchmark_returns)

        rows.append({
            "start_year": start_year,
            "sample_start": sample.index.min().date().isoformat(),
            "sample_end": sample.index.max().date().isoformat(),
            "months": len(sample),
            "AlphaCore_CAGR": strategy_cagr,
            "balanced_60_40_CAGR": benchmark_cagr,
            "CAGR_spread": strategy_cagr - benchmark_cagr,
            "AlphaCore_Sharpe": strategy_sharpe,
            "balanced_60_40_Sharpe": benchmark_sharpe,
            "Sharpe_spread": strategy_sharpe - benchmark_sharpe,
            "AlphaCore_max_drawdown": strategy_drawdown,
            "balanced_60_40_max_drawdown": benchmark_drawdown,
            "drawdown_improvement": strategy_drawdown - benchmark_drawdown,
            "AlphaCore_Calmar": calmar_ratio(strategy_returns),
            "balanced_60_40_Calmar": calmar_ratio(benchmark_returns),
        })

    return pd.DataFrame(rows).set_index("start_year")


def run_start_date_sensitivity_report(
    minimum_years: int = 10,
) -> pd.DataFrame:
    """Run annual start-date sensitivity with a minimum remaining history."""
    returns = load_backtest_returns()
    risk_free_returns = load_risk_free_data()["risk_free_return"]
    first_year = returns[["AlphaCore_net", "balanced_60_40"]].dropna().index.min().year
    final_year = returns.index.max().year
    latest_start_year = final_year - minimum_years
    start_years = list(range(first_year, latest_start_year + 1))

    summary = start_date_sensitivity_summary(
        returns=returns,
        start_years=start_years,
        risk_free_returns=risk_free_returns,
    )

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "alphacore_v1_start_date_sensitivity.csv"
    summary.to_csv(output_path)

    print("Start-date sensitivity report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(summary.to_string())

    return summary

def subperiod_performance_summary(
    returns: pd.DataFrame,
    periods: dict[str, tuple[str, str]],
    risk_free_returns: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Calculate performance metrics for selected subperiods.

    This helps check whether AlphaCore works across different market regimes
    or only in one lucky historical period.
    """
    rows = []

    return_columns = [
        col for col in returns.columns
        if col != "turnover"
    ]

    for period_name, (start_date, end_date) in periods.items():
        period_returns = returns.loc[start_date:end_date]

        for col in return_columns:
            series = period_returns[col].dropna()

            if series.empty:
                continue

            rows.append({
                "period": period_name,
                "strategy": col,
                "months": len(series),
                "risk_adjusted_months": len(
                    _monthly_excess_returns(
                        series,
                        risk_free_returns if risk_free_returns is not None else 0.0,
                        12,
                    )
                ),
                "cumulative_return": cumulative_total_return(series),
                "CAGR": cagr(series),
                "annualized_volatility": annualized_volatility(series),
                "Sharpe": sharpe_ratio(
                    series, risk_free_returns if risk_free_returns is not None else 0.0
                ),
                "Sortino": sortino_ratio(
                    series, risk_free_returns if risk_free_returns is not None else 0.0
                ),
                "max_drawdown": max_drawdown(series),
                "Calmar": calmar_ratio(series),
                "hit_rate": hit_rate(series),
            })

    summary = pd.DataFrame(rows)

    return summary


def run_subperiod_report() -> pd.DataFrame:
    """
    Run subperiod performance report for AlphaCore v1.2.
    """
    returns = load_backtest_returns()
    risk_free_returns = load_risk_free_data()["risk_free_return"]

    periods = {
        "2006-2010": ("2006-01-01", "2010-12-31"),
        "2011-2015": ("2011-01-01", "2015-12-31"),
        "2016-2020": ("2016-01-01", "2020-12-31"),
        "2021-2026": ("2021-01-01", "2026-12-31"),
    }

    summary = subperiod_performance_summary(
        returns=returns,
        periods=periods,
        risk_free_returns=risk_free_returns,
    )

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "alphacore_v1_subperiod_summary.csv"
    summary.to_csv(output_path, index=False)

    print("Subperiod performance report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()

    display_columns = [
        "period",
        "strategy",
        "CAGR",
        "annualized_volatility",
        "Sharpe",
        "max_drawdown",
        "Calmar",
        "hit_rate",
    ]

    print(
        summary[display_columns]
        .sort_values(by=["period", "Sharpe"], ascending=[True, False])
        .to_string(index=False)
    )

    return summary

def yearly_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate calendar-year returns for each strategy.

    This shows in which years AlphaCore outperformed or underperformed
    benchmarks and whether protection worked in difficult periods.
    """
    return_columns = [
        col for col in returns.columns
        if col != "turnover"
    ]

    yearly = (1 + returns[return_columns]).resample("YE").prod() - 1
    yearly.index = yearly.index.year

    return yearly


def run_yearly_returns_report() -> pd.DataFrame:
    """
    Run yearly returns report.
    """
    returns = load_backtest_returns()
    yearly = yearly_returns(returns)

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "alphacore_v1_yearly_returns.csv"
    yearly.to_csv(output_path)

    print("Yearly returns report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(yearly.to_string())

    return yearly


def worst_months_report(
    returns: pd.DataFrame,
    strategy: str = "AlphaCore_net",
    benchmark_columns: list[str] | None = None,
    n_months: int = 10,
) -> pd.DataFrame:
    """
    Show the worst months for AlphaCore and compare them with benchmarks.

    This helps evaluate downside protection during stress months.
    """
    if benchmark_columns is None:
        benchmark_columns = [
            "SPY",
            "balanced_60_40",
            "equal_weight",
            "SHY_cash",
        ]

    columns = [strategy] + benchmark_columns

    available_columns = [
        col for col in columns
        if col in returns.columns
    ]

    worst_dates = returns[strategy].dropna().sort_values().head(n_months).index

    worst = returns.loc[worst_dates, available_columns].copy()
    worst = worst.sort_values(by=strategy)

    return worst


def run_worst_months_report() -> pd.DataFrame:
    """
    Run worst months report for AlphaCore v1.2.
    """
    returns = load_backtest_returns()

    worst = worst_months_report(
        returns=returns,
        strategy="AlphaCore_net",
        n_months=10,
    )

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "alphacore_v1_worst_months.csv"
    worst.to_csv(output_path)

    print("Worst months report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(worst.to_string())

    return worst


def best_months_report(
    returns: pd.DataFrame,
    strategy: str = "AlphaCore_net",
    benchmark_columns: list[str] | None = None,
    n_months: int = 10,
) -> pd.DataFrame:
    """
    Show the best months for AlphaCore and compare them with benchmarks.

    This helps evaluate upside participation.
    """
    if benchmark_columns is None:
        benchmark_columns = [
            "SPY",
            "balanced_60_40",
            "equal_weight",
            "SHY_cash",
        ]

    columns = [strategy] + benchmark_columns

    available_columns = [
        col for col in columns
        if col in returns.columns
    ]

    best_dates = returns[strategy].dropna().sort_values(ascending=False).head(n_months).index

    best = returns.loc[best_dates, available_columns].copy()
    best = best.sort_values(by=strategy, ascending=False)

    return best


def run_best_months_report() -> pd.DataFrame:
    """
    Run best months report for AlphaCore v1.2.
    """
    returns = load_backtest_returns()

    best = best_months_report(
        returns=returns,
        strategy="AlphaCore_net",
        n_months=10,
    )

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "alphacore_v1_best_months.csv"
    best.to_csv(output_path)

    print("Best months report completed successfully.")
    print(f"Report saved to: {output_path}")
    print()
    print(best.to_string())

    return best

def beta_vs_benchmark(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 12,
    risk_free_rate: float | pd.Series = 0.0,
) -> float:
    """
    Calculate CAPM beta from aligned strategy and benchmark excess returns.
    """
    excess_returns = _aligned_capm_excess_returns(
        strategy_returns,
        benchmark_returns,
        risk_free_rate,
        periods_per_year,
    )
    return _beta_from_excess_returns(excess_returns)


def alpha_vs_benchmark(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 12,
    risk_free_rate: float | pd.Series = 0.0,
) -> float:
    """
    Calculate annualized CAPM-style alpha from monthly excess returns.

    Beta is estimated from strategy and benchmark excess returns. Alpha is the
    arithmetic annualization of the mean monthly CAPM residual:
    (strategy - risk-free) - beta * (benchmark - risk-free).
    """
    excess_returns = _aligned_capm_excess_returns(
        strategy_returns,
        benchmark_returns,
        risk_free_rate,
        periods_per_year,
    )
    beta = _beta_from_excess_returns(excess_returns)
    if np.isnan(beta):
        return np.nan

    monthly_alpha = (
        excess_returns["strategy_excess"]
        - beta * excess_returns["benchmark_excess"]
    ).mean()
    return monthly_alpha * periods_per_year


def correlation_vs_benchmark(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    """
    Calculate correlation between strategy and benchmark.
    """
    data = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()

    if data.empty:
        return np.nan

    return data.iloc[:, 0].corr(data.iloc[:, 1])


def tracking_error(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 12,
) -> float:
    """
    Annualized tracking error.
    """
    data = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()

    if data.empty:
        return np.nan

    active_returns = data.iloc[:, 0] - data.iloc[:, 1]

    return active_returns.std() * np.sqrt(periods_per_year)


def information_ratio(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    periods_per_year: int = 12,
) -> float:
    """
    Information ratio:
    annualized active return divided by annualized tracking error.
    """
    data = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()

    if data.empty:
        return np.nan

    active_returns = data.iloc[:, 0] - data.iloc[:, 1]

    active_return_annualized = active_returns.mean() * periods_per_year
    te = tracking_error(strategy_returns, benchmark_returns, periods_per_year)

    if te == 0 or np.isnan(te):
        return np.nan

    return active_return_annualized / te


def upside_capture(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    """
    Upside capture:
    strategy return during positive benchmark months divided by
    benchmark return during positive benchmark months.
    """
    data = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()

    if data.empty:
        return np.nan

    strategy = data.iloc[:, 0]
    benchmark = data.iloc[:, 1]

    up_months = benchmark > 0

    if up_months.sum() == 0:
        return np.nan

    strategy_up = (1 + strategy[up_months]).prod() - 1
    benchmark_up = (1 + benchmark[up_months]).prod() - 1

    if benchmark_up == 0:
        return np.nan

    return strategy_up / benchmark_up


def downside_capture(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    """
    Downside capture:
    strategy return during negative benchmark months divided by
    benchmark return during negative benchmark months.

    Lower is better if benchmark return is negative.
    Example:
    0.40 means the strategy captured about 40% of benchmark downside.
    """
    data = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()

    if data.empty:
        return np.nan

    strategy = data.iloc[:, 0]
    benchmark = data.iloc[:, 1]

    down_months = benchmark < 0

    if down_months.sum() == 0:
        return np.nan

    strategy_down = (1 + strategy[down_months]).prod() - 1
    benchmark_down = (1 + benchmark[down_months]).prod() - 1

    if benchmark_down == 0:
        return np.nan

    return strategy_down / benchmark_down

def average_capture_metrics(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict:
    """
    Calculate intuitive average upside/downside capture metrics.

    Unlike geometric capture, this uses average monthly returns
    during benchmark up and down months.

    Interpretation:
    - average_upside_capture of 0.50 means the strategy captured
      about 50% of the benchmark's average positive monthly return.
    - average_downside_capture of 0.30 means the strategy captured
      about 30% of the benchmark's average negative monthly return.
      Lower downside capture is better.
    """
    data = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()

    if data.empty:
        return {
            "up_months": np.nan,
            "down_months": np.nan,
            "avg_strategy_up_month_return": np.nan,
            "avg_benchmark_up_month_return": np.nan,
            "average_upside_capture": np.nan,
            "avg_strategy_down_month_return": np.nan,
            "avg_benchmark_down_month_return": np.nan,
            "average_downside_capture": np.nan,
        }

    strategy = data.iloc[:, 0]
    benchmark = data.iloc[:, 1]

    up_months_mask = benchmark > 0
    down_months_mask = benchmark < 0

    up_months = int(up_months_mask.sum())
    down_months = int(down_months_mask.sum())

    if up_months > 0:
        avg_strategy_up = strategy[up_months_mask].mean()
        avg_benchmark_up = benchmark[up_months_mask].mean()
        avg_up_capture = (
            avg_strategy_up / avg_benchmark_up
            if avg_benchmark_up != 0
            else np.nan
        )
    else:
        avg_strategy_up = np.nan
        avg_benchmark_up = np.nan
        avg_up_capture = np.nan

    if down_months > 0:
        avg_strategy_down = strategy[down_months_mask].mean()
        avg_benchmark_down = benchmark[down_months_mask].mean()
        avg_down_capture = (
            avg_strategy_down / avg_benchmark_down
            if avg_benchmark_down != 0
            else np.nan
        )
    else:
        avg_strategy_down = np.nan
        avg_benchmark_down = np.nan
        avg_down_capture = np.nan

    return {
        "up_months": up_months,
        "down_months": down_months,
        "avg_strategy_up_month_return": avg_strategy_up,
        "avg_benchmark_up_month_return": avg_benchmark_up,
        "average_upside_capture": avg_up_capture,
        "avg_strategy_down_month_return": avg_strategy_down,
        "avg_benchmark_down_month_return": avg_benchmark_down,
        "average_downside_capture": avg_down_capture,
    }

def relative_metrics_summary(
    returns: pd.DataFrame,
    strategy_columns: list[str] | None = None,
    benchmark: str = "SPY",
    risk_free_returns: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Calculate benchmark-relative metrics for selected strategies.
    """
    if strategy_columns is None:
        strategy_columns = [
            "AlphaCore_net",
            "AlphaCore_gross",
            "balanced_60_40",
            "equal_weight",
            "SHY_cash",
        ]

    rows = []

    benchmark_returns = returns[benchmark]

    for strategy in strategy_columns:
        if strategy not in returns.columns:
            continue

        strategy_returns = returns[strategy]

        avg_capture = average_capture_metrics(
            strategy_returns=strategy_returns,
            benchmark_returns=benchmark_returns,
        )

        row = {
            "strategy": strategy,
            "benchmark": benchmark,
            "beta": beta_vs_benchmark(
                strategy_returns,
                benchmark_returns,
                risk_free_rate=(
                    risk_free_returns if risk_free_returns is not None else 0.0
                ),
            ),
            "alpha_annualized": alpha_vs_benchmark(
                strategy_returns,
                benchmark_returns,
                risk_free_rate=(
                    risk_free_returns if risk_free_returns is not None else 0.0
                ),
            ),
            "correlation": correlation_vs_benchmark(strategy_returns, benchmark_returns),
            "tracking_error": tracking_error(strategy_returns, benchmark_returns),
            "information_ratio": information_ratio(strategy_returns, benchmark_returns),

            # Geometric capture metrics
            "upside_capture_geometric": upside_capture(strategy_returns, benchmark_returns),
            "downside_capture_geometric": downside_capture(strategy_returns, benchmark_returns),
        }

        row.update(avg_capture)
        rows.append(row)

    summary = pd.DataFrame(rows).set_index("strategy")

    return summary


def run_relative_metrics_report(

    benchmark: str = "SPY",

) -> pd.DataFrame:

    """

    Run benchmark-relative metrics report.

    Examples:

    - benchmark="SPY"

    - benchmark="balanced_60_40"

    - benchmark="equal_weight"

    """

    returns = load_backtest_returns()
    risk_free_returns = load_risk_free_data()["risk_free_return"]

    summary = relative_metrics_summary(

        returns=returns,

        benchmark=benchmark,

        risk_free_returns=risk_free_returns,

    )

    output_dir = PROJECT_ROOT / "reports" / "backtests"

    output_dir.mkdir(parents=True, exist_ok=True)

    safe_benchmark_name = benchmark.lower().replace("/", "_").replace(" ", "_")

    output_path = output_dir / f"alphacore_v1_relative_metrics_vs_{safe_benchmark_name}.csv"

    summary.to_csv(output_path)

    print(f"Relative metrics report completed successfully vs {benchmark}.")

    print(f"Report saved to: {output_path}")

    print()

    print(summary.sort_values(by="information_ratio", ascending=False).to_string())

    return summary

def rolling_cagr(
    returns: pd.Series,
    window: int = 36,
    periods_per_year: int = 12,
) -> pd.Series:
    """
    Calculate rolling CAGR over a given monthly window.
    """
    def _cagr(window_returns: pd.Series) -> float:
        window_returns = window_returns.dropna()

        if len(window_returns) == 0:
            return np.nan

        total_return = (1 + window_returns).prod()
        years = len(window_returns) / periods_per_year

        if years <= 0:
            return np.nan

        return total_return ** (1 / years) - 1

    return returns.rolling(window=window).apply(_cagr, raw=False)


def rolling_volatility(
    returns: pd.Series,
    window: int = 36,
    periods_per_year: int = 12,
) -> pd.Series:
    """
    Calculate rolling annualized volatility.
    """
    return returns.rolling(window=window).std() * np.sqrt(periods_per_year)


def rolling_sharpe(
    returns: pd.Series,
    window: int = 36,
    periods_per_year: int = 12,
    risk_free_rate: float | pd.Series = 0.0,
) -> pd.Series:
    """
    Calculate rolling Sharpe using consecutive month-end excess returns.

    Missing calendar months or missing return/risk-free values remain NaN, so
    every result requires a complete window of consecutive monthly observations.
    """
    excess_returns = _calendar_monthly_excess_returns(
        returns, risk_free_rate, periods_per_year
    )
    rolling_mean = excess_returns.rolling(
        window=window, min_periods=window
    ).mean()
    rolling_std = excess_returns.rolling(
        window=window, min_periods=window
    ).std()

    sharpe = rolling_mean / rolling_std * np.sqrt(periods_per_year)

    return sharpe.reindex(returns.index)


def rolling_max_drawdown(
    returns: pd.Series,
    window: int = 36,
) -> pd.Series:
    """
    Calculate rolling maximum drawdown over a given window.
    """
    def _max_drawdown(window_returns: pd.Series) -> float:
        window_returns = window_returns.dropna()

        if len(window_returns) == 0:
            return np.nan

        wealth = (1 + window_returns).cumprod()
        running_max = wealth.cummax()
        drawdown = wealth / running_max - 1

        return drawdown.min()

    return returns.rolling(window=window).apply(_max_drawdown, raw=False)


def rolling_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    window: int = 36,
) -> pd.Series:
    """
    Calculate rolling beta vs benchmark.
    """
    rolling_covariance = strategy_returns.rolling(window=window).cov(benchmark_returns)
    rolling_variance = benchmark_returns.rolling(window=window).var()

    beta = rolling_covariance / rolling_variance

    return beta


def rolling_metrics_report(
    returns: pd.DataFrame,
    strategy: str = "AlphaCore_net",
    benchmark: str = "SPY",
    window: int = 36,
    risk_free_returns: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Build rolling metrics report for AlphaCore.
    """
    strategy_returns = returns[strategy]
    benchmark_returns = returns[benchmark]

    report = pd.DataFrame(index=returns.index)

    report[f"{strategy}_rolling_CAGR"] = rolling_cagr(
        strategy_returns,
        window=window,
    )

    report[f"{strategy}_rolling_volatility"] = rolling_volatility(
        strategy_returns,
        window=window,
    )

    report[f"{strategy}_rolling_Sharpe"] = rolling_sharpe(
        strategy_returns,
        window=window,
        risk_free_rate=(
            risk_free_returns if risk_free_returns is not None else 0.0
        ),
    )

    report[f"{strategy}_rolling_max_drawdown"] = rolling_max_drawdown(
        strategy_returns,
        window=window,
    )

    report[f"{strategy}_rolling_beta_vs_{benchmark}"] = rolling_beta(
        strategy_returns=strategy_returns,
        benchmark_returns=benchmark_returns,
        window=window,
    )

    report[f"{benchmark}_rolling_CAGR"] = rolling_cagr(
        benchmark_returns,
        window=window,
    )

    report[f"{benchmark}_rolling_volatility"] = rolling_volatility(
        benchmark_returns,
        window=window,
    )

    report[f"{benchmark}_rolling_Sharpe"] = rolling_sharpe(
        benchmark_returns,
        window=window,
        risk_free_rate=(
            risk_free_returns if risk_free_returns is not None else 0.0
        ),
    )

    report[f"{benchmark}_rolling_max_drawdown"] = rolling_max_drawdown(
        benchmark_returns,
        window=window,
    )

    return report


def summarize_rolling_metrics(
    rolling_report: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize rolling metrics using mean, min and max.

    This gives a quick robustness overview.
    """
    rows = []

    for column in rolling_report.columns:
        series = rolling_report[column].dropna()

        if series.empty:
            continue

        rows.append({
            "metric": column,
            "mean": series.mean(),
            "median": series.median(),
            "min": series.min(),
            "max": series.max(),
            "latest": series.iloc[-1],
        })

    summary = pd.DataFrame(rows).set_index("metric")

    return summary


def run_rolling_metrics_report() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run rolling 36-month metrics report.
    """
    returns = load_backtest_returns()
    risk_free_returns = load_risk_free_data()["risk_free_return"]

    rolling_report = rolling_metrics_report(
        returns=returns,
        strategy="AlphaCore_net",
        benchmark="SPY",
        window=36,
        risk_free_returns=risk_free_returns,
    )

    rolling_summary = summarize_rolling_metrics(rolling_report)

    output_dir = PROJECT_ROOT / "reports" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    rolling_report_path = output_dir / "alphacore_v1_rolling_36m_metrics.csv"
    rolling_summary_path = output_dir / "alphacore_v1_rolling_36m_summary.csv"

    rolling_report.to_csv(rolling_report_path)
    rolling_summary.to_csv(rolling_summary_path)

    print("Rolling metrics report completed successfully.")
    print(f"Rolling metrics saved to: {rolling_report_path}")
    print(f"Rolling summary saved to: {rolling_summary_path}")
    print()
    print(rolling_summary.to_string())

    return rolling_report, rolling_summary

if __name__ == "__main__":
    run_performance_report()

    print("\n" + "=" * 100 + "\n")
    run_transaction_cost_sensitivity_report()

    print("\n" + "=" * 100 + "\n")
    run_signal_lag_sensitivity_report()

    print("\n" + "=" * 100 + "\n")
    run_trend_window_sensitivity_report()

    print("\n" + "=" * 100 + "\n")
    run_start_date_sensitivity_report()

    print("\n" + "=" * 100 + "\n")
    run_subperiod_report()

    print("\n" + "=" * 100 + "\n")
    run_yearly_returns_report()

    print("\n" + "=" * 100 + "\n")
    run_worst_months_report()

    print("\n" + "=" * 100 + "\n")
    run_best_months_report()

    print("\n" + "=" * 100 + "\n")
    run_relative_metrics_report(benchmark="SPY")

    print("\n" + "=" * 100 + "\n")
    run_relative_metrics_report(benchmark="balanced_60_40")

    print("\n" + "=" * 100 + "\n")
    run_rolling_metrics_report()
