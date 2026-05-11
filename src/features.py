from pathlib import Path
from typing import Dict

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_monthly_prices() -> pd.DataFrame:
    """
    Load monthly ETF prices from processed data.
    """
    path = PROJECT_ROOT / "data" / "processed" / "prices_monthly.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Monthly prices not found. Run src/data_loader.py first."
        )

    return pd.read_parquet(path)


def calculate_momentum(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    Calculate price momentum over a given number of months.

    Example:
    window=12 means 12-month percentage return.
    """
    return prices.pct_change(periods=window)


def calculate_composite_momentum(

    prices: pd.DataFrame,

    weights: Dict[int, float] | None = None,

) -> pd.DataFrame:

    """

    Calculate composite momentum from 3M, 6M and 12M returns.

    Important:

    Composite momentum should only be available when all required

    momentum windows are available. Therefore, early months remain NaN.

    """

    if weights is None:

        weights = {

            3: 0.25,

            6: 0.25,

            12: 0.50,

        }

    momentum_parts = []

    for window, weight in weights.items():

        momentum = calculate_momentum(prices, window)

        momentum_parts.append(momentum * weight)

    composite = sum(momentum_parts)

    return composite
   
def calculate_moving_average(prices: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    Calculate moving average using monthly prices.
    """
    return prices.rolling(window=window).mean()


def calculate_trend_signal(prices: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    Trend signal:
    1 if price is above moving average
    0 if price is below moving average
    """
    moving_average = calculate_moving_average(prices, window)
    trend = (prices > moving_average).astype(float)

    trend[moving_average.isna()] = float("nan")

    return trend


def calculate_realized_volatility(
    monthly_returns: pd.DataFrame,
    window: int = 12,
) -> pd.DataFrame:
    """
    Calculate rolling annualized volatility from monthly returns.

    Annualization factor for monthly data is sqrt(12).
    """
    return monthly_returns.rolling(window=window).std() * (12 ** 0.5)


def calculate_drawdown(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate drawdown from historical peak.
    """
    running_max = prices.cummax()
    drawdown = prices / running_max - 1

    return drawdown


def build_feature_dataset() -> dict[str, pd.DataFrame]:
    """
    Build and save the first AlphaCore feature set.
    """
    prices = load_monthly_prices()
    returns = prices.pct_change()

    momentum_3m = calculate_momentum(prices, 3)
    momentum_6m = calculate_momentum(prices, 6)
    momentum_12m = calculate_momentum(prices, 12)
    composite_momentum = calculate_composite_momentum(prices)

    moving_average_10m = calculate_moving_average(prices, 10)
    trend_10m = calculate_trend_signal(prices, 10)

    realized_volatility_12m = calculate_realized_volatility(returns, 12)
    drawdown = calculate_drawdown(prices)

    output_dir = PROJECT_ROOT / "data" / "processed" / "features"
    output_dir.mkdir(parents=True, exist_ok=True)

    feature_sets = {
        "momentum_3m": momentum_3m,
        "momentum_6m": momentum_6m,
        "momentum_12m": momentum_12m,
        "composite_momentum": composite_momentum,
        "moving_average_10m": moving_average_10m,
        "trend_10m": trend_10m,
        "realized_volatility_12m": realized_volatility_12m,
        "drawdown": drawdown,
    }

    for name, data in feature_sets.items():
        data.to_parquet(output_dir / f"{name}.parquet")

    print("Feature dataset completed successfully.")
    print(f"Prices shape: {prices.shape}")
    print(f"Feature files saved to: {output_dir}")

    return feature_sets


if __name__ == "__main__":
    build_feature_dataset()