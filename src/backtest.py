from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml_config(path: str | Path) -> dict:
    """
    Load YAML configuration file.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_monthly_returns() -> pd.DataFrame:
    """
    Load monthly ETF returns.
    """
    path = PROJECT_ROOT / "data" / "processed" / "returns_monthly.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Monthly returns not found. Run src/data_loader.py first."
        )

    return pd.read_parquet(path)


def load_monthly_weights() -> pd.DataFrame:
    """
    Load monthly portfolio weights.
    """
    path = PROJECT_ROOT / "data" / "processed" / "portfolio" / "monthly_weights.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Monthly weights not found. Run src/portfolio.py first."
        )

    return pd.read_parquet(path)


def calculate_turnover(weights: pd.DataFrame) -> pd.Series:
    """
    Calculate monthly portfolio turnover.

    Turnover is defined as the sum of absolute weight changes.
    We divide by 2 because buying one asset and selling another creates
    two-sided weight changes for one portfolio rebalance.
    """
    turnover = weights.diff().abs().sum(axis=1) / 2
    turnover.iloc[0] = weights.iloc[0].abs().sum() / 2

    return turnover


def calculate_strategy_returns(
    returns: pd.DataFrame,
    weights: pd.DataFrame,
    signal_lag: int = 1,
) -> pd.Series:
    """
    Calculate strategy returns with signal lag.

    Critical anti-look-ahead rule:
    weights calculated at month t are used for returns in month t+1.
    """
    aligned_returns = returns.loc[weights.index, weights.columns]

    shifted_weights = weights.shift(signal_lag)

    strategy_returns = (shifted_weights * aligned_returns).sum(axis=1)

    return strategy_returns


def apply_transaction_costs(
    strategy_returns: pd.Series,
    weights: pd.DataFrame,
    cost_bps: float,
    signal_lag: int = 1,
) -> tuple[pd.Series, pd.Series]:
    """
    Apply transaction costs based on portfolio turnover.

    cost_bps:
    10 means 0.10%
    """
    shifted_weights = weights.shift(signal_lag)
    turnover = calculate_turnover(shifted_weights)

    cost_rate = cost_bps / 10000
    costs = turnover * cost_rate

    net_returns = strategy_returns - costs

    return net_returns, turnover


def build_benchmark_returns(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Build simple benchmark return series.
    """
    benchmarks = pd.DataFrame(index=returns.index)

    benchmarks["SPY"] = returns["SPY"]
    benchmarks["SHY_cash"] = returns["SHY"]
    benchmarks["balanced_60_40"] = 0.60 * returns["SPY"] + 0.40 * returns["AGG"]
    benchmarks["equal_weight"] = returns.mean(axis=1)

    return benchmarks


def run_backtest() -> pd.DataFrame:
    """
    Run AlphaCore v1 backtest.
    """
    config_path = PROJECT_ROOT / "configs" / "backtest_config.yaml"
    config = load_yaml_config(config_path)

    signal_lag = config["backtest"]["signal_lag"]
    transaction_cost_bps = config["backtest"]["transaction_cost_bps"]

    returns = load_monthly_returns()
    weights = load_monthly_weights()

    strategy_returns_gross = calculate_strategy_returns(
        returns=returns,
        weights=weights,
        signal_lag=signal_lag,
    )

    strategy_returns_net, turnover = apply_transaction_costs(
        strategy_returns=strategy_returns_gross,
        weights=weights,
        cost_bps=transaction_cost_bps,
        signal_lag=signal_lag,
    )

    benchmarks = build_benchmark_returns(returns)

    results = benchmarks.copy()
    results["AlphaCore_gross"] = strategy_returns_gross
    results["AlphaCore_net"] = strategy_returns_net
    results["turnover"] = turnover

    # Remove periods before the strategy has valid signals
    results = results.dropna(how="all")

    output_dir = PROJECT_ROOT / "data" / "processed" / "backtests"
    output_dir.mkdir(parents=True, exist_ok=True)

    results.to_parquet(output_dir / "alphacore_v1_returns.parquet")

    print("Backtest completed successfully.")
    print(f"Backtest files saved to: {output_dir}")
    print(results.tail())

    return results


if __name__ == "__main__":
    run_backtest()