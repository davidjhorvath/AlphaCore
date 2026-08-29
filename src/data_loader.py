from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
RISK_FREE_SERIES_ID = "DGS3MO"
RISK_FREE_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "risk_free_monthly.parquet"


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
    import yfinance as yf

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


def download_fred_series(
    series_id: str = RISK_FREE_SERIES_ID,
) -> pd.Series:
    """Download a daily FRED series using FRED's lightweight CSV endpoint."""
    return load_fred_series(f"{FRED_CSV_URL}?id={series_id}", series_id)


def load_fred_series(
    source: str | Path,
    series_id: str = RISK_FREE_SERIES_ID,
) -> pd.Series:
    """Load a FRED CSV from a URL or local path."""
    data = pd.read_csv(source)

    date_column = "observation_date" if "observation_date" in data.columns else "DATE"
    if date_column not in data.columns or series_id not in data.columns:
        raise ValueError(f"Unexpected FRED response for series {series_id}.")

    series = pd.Series(
        pd.to_numeric(data[series_id], errors="coerce").to_numpy(),
        index=pd.to_datetime(data[date_column]),
        name=series_id,
    )
    return series.sort_index()


def annual_yield_percent_to_monthly_return(
    annual_yield_percent: pd.Series | float,
) -> pd.Series | float:
    """
    Convert a quoted Treasury CMT yield percentage to a monthly return proxy.

    Treasury CMT yields are quoted on an investment basis. Converting the
    decimal yield I to APY as (1 + I / 2) ** 2 - 1 implies the equivalent
    monthly proxy (1 + I / 2) ** (1 / 6) - 1. This is a yield-derived proxy,
    not a realized Treasury bill total-return series.
    """
    decimal_yield = annual_yield_percent / 100
    return (1 + decimal_yield / 2) ** (1 / 6) - 1


def align_risk_free_to_monthly(daily_yields: pd.Series) -> pd.DataFrame:
    """
    Build month-end risk-free returns without look-ahead.

    Each month's return uses the final available DGS3MO observation from the
    preceding calendar month. The observation is therefore shifted to the next
    month-end before converting the annualized percentage yield.
    """
    yields = daily_yields.copy()
    yields.index = pd.to_datetime(yields.index)
    yields = pd.to_numeric(yields, errors="coerce").sort_index()

    monthly_yields = yields.groupby(yields.index.to_period("M")).last().dropna()
    monthly_yields.index = monthly_yields.index.to_timestamp("M") + pd.offsets.MonthEnd(1)

    monthly_returns = annual_yield_percent_to_monthly_return(monthly_yields)
    monthly_returns.name = "risk_free_return"
    monthly_returns.index.name = "Date"
    return monthly_returns.to_frame()


def save_risk_free_data(
    risk_free_returns: pd.DataFrame,
    output_path: str | Path = RISK_FREE_DATA_PATH,
) -> None:
    """Save processed monthly risk-free returns to parquet."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    risk_free_returns.to_parquet(output_path)


def load_risk_free_data(
    path: str | Path = RISK_FREE_DATA_PATH,
) -> pd.DataFrame:
    """Load processed monthly risk-free returns from parquet."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            "Risk-free data not found. Run build_risk_free_dataset() first."
        )

    data = pd.read_parquet(path)
    if "risk_free_return" not in data.columns:
        raise ValueError("Risk-free data must contain a risk_free_return column.")
    data.index = pd.to_datetime(data.index)
    return data.sort_index()


def build_risk_free_dataset() -> pd.DataFrame:
    """Download DGS3MO, create lagged monthly returns, and save the dataset."""
    daily_yields = download_fred_series(RISK_FREE_SERIES_ID)
    monthly_returns = align_risk_free_to_monthly(daily_yields)
    current_month_end = pd.Timestamp.today().normalize() + pd.offsets.MonthEnd(0)
    monthly_returns = monthly_returns.loc[:current_month_end]
    save_risk_free_data(monthly_returns)

    print("Risk-free data pipeline completed successfully.")
    print(f"Monthly risk-free returns shape: {monthly_returns.shape}")
    print(f"Saved to: {RISK_FREE_DATA_PATH}")
    return monthly_returns


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
    build_risk_free_dataset()
