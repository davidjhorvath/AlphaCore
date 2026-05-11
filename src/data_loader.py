from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml_config(path: str | Path) -> Dict:
    """
    Load a YAML configuration file.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config


def get_tickers_from_universe(config: Dict) -> List[str]:
    """
    Extract a flat list of ETF tickers from universe.yaml.
    """
    tickers = []

    universe = config.get("universe", {})

    for category, assets in universe.items():
        if isinstance(assets, dict):
            tickers.extend(list(assets.keys()))

    return sorted(set(tickers))


def download_adjusted_prices(
    tickers: List[str],
    start_date: str,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Download adjusted close prices from Yahoo Finance.
    """
    data = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=True,
    )

    if data.empty:
        raise ValueError("No data downloaded. Check tickers or internet connection.")

    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" not in data.columns.get_level_values(0):
            raise ValueError("Adjusted close prices not found in downloaded data.")
        prices = data["Adj Close"].copy()
    else:
        prices = data[["Adj Close"]].copy()
        prices.columns = tickers

    prices = prices.dropna(how="all")
    prices.index = pd.to_datetime(prices.index)

    return prices


def save_prices(prices: pd.DataFrame, output_path: str | Path) -> None:
    """
    Save prices to a parquet file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(output_path)


def load_prices(path: str | Path) -> pd.DataFrame:
    """
    Load prices from a parquet file.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Price file not found: {path}")

    return pd.read_parquet(path)


def resample_to_monthly(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Convert daily prices to month-end prices.
    """
    return prices.resample("ME").last()


def calculate_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate simple percentage returns.
    """
    return prices.pct_change()


def build_price_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Full first data pipeline:
    1. Load universe.yaml
    2. Extract tickers
    3. Download daily adjusted prices
    4. Convert to monthly prices
    5. Calculate monthly returns
    6. Save processed datasets
    """
    universe_path = PROJECT_ROOT / "configs" / "universe.yaml"
    config = load_yaml_config(universe_path)

    tickers = get_tickers_from_universe(config)
    start_date = config["settings"]["start_date"]

    print(f"Downloading data for tickers: {tickers}")
    print(f"Start date: {start_date}")

    daily_prices = download_adjusted_prices(
        tickers=tickers,
        start_date=start_date,
        end_date=None,
    )

    monthly_prices = resample_to_monthly(daily_prices)
    monthly_returns = calculate_returns(monthly_prices)

    save_prices(daily_prices, PROJECT_ROOT / "data" / "processed" / "prices_daily.parquet")
    save_prices(monthly_prices, PROJECT_ROOT / "data" / "processed" / "prices_monthly.parquet")
    save_prices(monthly_returns, PROJECT_ROOT / "data" / "processed" / "returns_monthly.parquet")

    print("Data pipeline completed successfully.")
    print(f"Daily prices shape: {daily_prices.shape}")
    print(f"Monthly prices shape: {monthly_prices.shape}")
    print(f"Monthly returns shape: {monthly_returns.shape}")

    return monthly_prices, monthly_returns


if __name__ == "__main__":
    build_price_dataset()