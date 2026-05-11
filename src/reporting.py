from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_backtest_returns() -> pd.DataFrame:
    """
    Load AlphaCore backtest returns.
    """
    path = PROJECT_ROOT / "data" / "processed" / "backtests" / "alphacore_v1_returns.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Backtest results not found. Run src/backtest.py first."
        )

    return pd.read_parquet(path)


def load_rolling_metrics() -> pd.DataFrame:
    """
    Load rolling 36-month metrics.
    """
    path = PROJECT_ROOT / "reports" / "backtests" / "alphacore_v1_rolling_36m_metrics.csv"

    if not path.exists():
        raise FileNotFoundError(
            "Rolling metrics not found. Run src/performance.py first."
        )

    data = pd.read_csv(path, index_col=0, parse_dates=True)

    return data


def cumulative_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Convert periodic returns into cumulative wealth index.
    Starts at 1.0.
    """
    return (1 + returns).cumprod()


def drawdown_series(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate drawdown series for each strategy.
    """
    wealth = cumulative_returns(returns)
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1

    return drawdown


def save_equity_curve_chart(
    returns: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Save equity curve comparison chart.
    """
    columns = [
        "AlphaCore_net",
        "SPY",
        "balanced_60_40",
        "equal_weight",
        "SHY_cash",
    ]

    available_columns = [
        col for col in columns
        if col in returns.columns
    ]

    wealth = cumulative_returns(returns[available_columns].dropna(how="all"))

    plt.figure(figsize=(12, 7))

    for column in available_columns:
        plt.plot(wealth.index, wealth[column], label=column)

    plt.title("AlphaCore v1.3 Equity Curve vs Benchmarks")
    plt.xlabel("Date")
    plt.ylabel("Growth of $1")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_drawdown_chart(
    returns: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Save drawdown comparison chart.
    """
    columns = [
        "AlphaCore_net",
        "SPY",
        "balanced_60_40",
        "equal_weight",
        "SHY_cash",
    ]

    available_columns = [
        col for col in columns
        if col in returns.columns
    ]

    drawdowns = drawdown_series(returns[available_columns].dropna(how="all"))

    plt.figure(figsize=(12, 7))

    for column in available_columns:
        plt.plot(drawdowns.index, drawdowns[column], label=column)

    plt.title("AlphaCore v1.3 Drawdown vs Benchmarks")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_rolling_sharpe_chart(
    rolling_metrics: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Save rolling 36-month Sharpe comparison chart.
    """
    columns = [
        "AlphaCore_net_rolling_Sharpe",
        "SPY_rolling_Sharpe",
    ]

    available_columns = [
        col for col in columns
        if col in rolling_metrics.columns
    ]

    plt.figure(figsize=(12, 7))

    for column in available_columns:
        plt.plot(rolling_metrics.index, rolling_metrics[column], label=column)

    plt.axhline(0, linewidth=1)
    plt.title("Rolling 36-Month Sharpe Ratio")
    plt.xlabel("Date")
    plt.ylabel("Sharpe Ratio")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def run_chart_report() -> None:
    """
    Generate AlphaCore visual report charts.
    """
    returns = load_backtest_returns()
    rolling_metrics = load_rolling_metrics()

    chart_dir = PROJECT_ROOT / "reports" / "backtests" / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    equity_curve_path = chart_dir / "equity_curve_alphacore_vs_benchmarks.png"
    drawdown_path = chart_dir / "drawdown_alphacore_vs_benchmarks.png"
    rolling_sharpe_path = chart_dir / "rolling_sharpe_36m.png"

    save_equity_curve_chart(
        returns=returns,
        output_path=equity_curve_path,
    )

    save_drawdown_chart(
        returns=returns,
        output_path=drawdown_path,
    )

    save_rolling_sharpe_chart(
        rolling_metrics=rolling_metrics,
        output_path=rolling_sharpe_path,
    )

    print("Chart report completed successfully.")
    print(f"Saved: {equity_curve_path}")
    print(f"Saved: {drawdown_path}")
    print(f"Saved: {rolling_sharpe_path}")


if __name__ == "__main__":
    run_chart_report()