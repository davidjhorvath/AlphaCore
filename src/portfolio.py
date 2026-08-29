from pathlib import Path

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SIGNAL_DIR = PROJECT_ROOT / "data" / "processed" / "signals"
FEATURE_DIR = PROJECT_ROOT / "data" / "processed" / "features"


RISKY_ASSETS = ["SPY", "QQQ", "EFA", "EEM", "VNQ", "DBC", "GLD"]
TACTICAL_RISKY_ASSETS = ["EFA", "EEM", "VNQ", "DBC", "GLD"]
DEFENSIVE_ASSETS = ["AGG", "IEF", "TLT", "SHY"]


def load_yaml_config(path: str | Path) -> dict:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_total_score() -> pd.DataFrame:
    path = SIGNAL_DIR / "total_score.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Total score file not found. Run src/signals.py first."
        )

    return pd.read_parquet(path)


def load_investable() -> pd.DataFrame:
    path = SIGNAL_DIR / "investable.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Investable file not found. Run src/signals.py first."
        )

    return pd.read_parquet(path)


def load_spy_trend() -> pd.Series:
    path = FEATURE_DIR / "trend_10m.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "Trend feature not found. Run src/features.py first."
        )

    trend = pd.read_parquet(path)
    return trend["SPY"]

def load_spy_momentum_6m() -> pd.Series:
    """
    Load SPY 6-month momentum.
    Used to identify strong risk-on regimes.
    """
    path = FEATURE_DIR / "momentum_6m.parquet"

    if not path.exists():
        raise FileNotFoundError(
            "6M momentum feature not found. Run src/features.py first."
        )

    momentum = pd.read_parquet(path)

    return momentum["SPY"]


def select_top_assets(scores: pd.Series, candidates: list[str], top_n: int) -> list[str]:
    available_candidates = [asset for asset in candidates if asset in scores.index]
    valid_scores = scores.loc[available_candidates].dropna()

    if valid_scores.empty:
        return []

    return valid_scores.sort_values(ascending=False).head(top_n).index.tolist()


def add_weight(weights: pd.Series, asset: str, weight: float) -> None:
    if asset in weights.index and weight > 0:
        weights[asset] += weight


def allocate_equal(
    weights: pd.Series,
    selected_assets: list[str],
    sleeve_weight: float,
    cash_ticker: str,
) -> None:
    """
    Allocate equal weights to selected assets.
    If no assets are selected, put the sleeve into cash.
    """
    if sleeve_weight <= 0:
        return

    if len(selected_assets) == 0:
        add_weight(weights, cash_ticker, sleeve_weight)
        return

    weight_per_asset = sleeve_weight / len(selected_assets)

    for asset in selected_assets:
        add_weight(weights, asset, weight_per_asset)


def build_core_satellite_portfolio_for_date(
    scores_today: pd.Series,
    investable_today: pd.Series,
    spy_trend_today: float,
    spy_momentum_6m_today: float,
    all_assets: list[str],
    cash_ticker: str = "SHY",
) -> pd.Series:
    """
    AlphaCore v1.3 Core-Satellite portfolio with strong risk-on regime.

    Strong risk-on:
    - 35% SPY core
    - 20% QQQ core
    - 25% top 2 tactical risky assets
    - 20% top 1 defensive asset

    Normal risk-on:
    - 25% SPY core
    - 15% QQQ core
    - 35% top 2 tactical risky assets
    - 25% top 1 defensive asset

    Risk-off:
    - 20% SPY core only if SPY is investable, otherwise SHY
    - 20% top 1 tactical risky asset
    - 60% top 1 defensive asset
    """
    weights = pd.Series(0.0, index=all_assets)

    if pd.isna(spy_trend_today):
        weights[cash_ticker] = 1.0
        return weights

    spy_is_investable = bool(investable_today.get("SPY", 0) == 1.0)
    qqq_is_investable = bool(investable_today.get("QQQ", 0) == 1.0)

    strong_risk_on = (
        spy_trend_today == 1.0
        and qqq_is_investable
        and not pd.isna(spy_momentum_6m_today)
        and spy_momentum_6m_today > 0
    )

    if strong_risk_on:
        # Strong risk-on allocation
        add_weight(weights, "SPY" if spy_is_investable else cash_ticker, 0.35)
        add_weight(weights, "QQQ" if qqq_is_investable else cash_ticker, 0.20)

        top_tactical = select_top_assets(
            scores=scores_today,
            candidates=TACTICAL_RISKY_ASSETS,
            top_n=2,
        )
        allocate_equal(
            weights=weights,
            selected_assets=top_tactical,
            sleeve_weight=0.25,
            cash_ticker=cash_ticker,
        )

        top_defensive = select_top_assets(
            scores=scores_today,
            candidates=DEFENSIVE_ASSETS,
            top_n=1,
        )
        allocate_equal(
            weights=weights,
            selected_assets=top_defensive,
            sleeve_weight=0.20,
            cash_ticker=cash_ticker,
        )

    elif spy_trend_today == 1.0:
        # Normal risk-on allocation
        add_weight(weights, "SPY" if spy_is_investable else cash_ticker, 0.25)
        add_weight(weights, "QQQ" if qqq_is_investable else cash_ticker, 0.15)

        top_tactical = select_top_assets(
            scores=scores_today,
            candidates=TACTICAL_RISKY_ASSETS,
            top_n=2,
        )
        allocate_equal(
            weights=weights,
            selected_assets=top_tactical,
            sleeve_weight=0.35,
            cash_ticker=cash_ticker,
        )

        top_defensive = select_top_assets(
            scores=scores_today,
            candidates=DEFENSIVE_ASSETS,
            top_n=1,
        )
        allocate_equal(
            weights=weights,
            selected_assets=top_defensive,
            sleeve_weight=0.25,
            cash_ticker=cash_ticker,
        )

    else:
        # Reduced core equity allocation
        add_weight(weights, "SPY" if spy_is_investable else cash_ticker, 0.20)

        # Tactical risky sleeve
        top_tactical = select_top_assets(
            scores=scores_today,
            candidates=TACTICAL_RISKY_ASSETS,
            top_n=1,
        )
        allocate_equal(
            weights=weights,
            selected_assets=top_tactical,
            sleeve_weight=0.20,
            cash_ticker=cash_ticker,
        )

        # Defensive sleeve
        top_defensive = select_top_assets(
            scores=scores_today,
            candidates=DEFENSIVE_ASSETS,
            top_n=1,
        )
        allocate_equal(
            weights=weights,
            selected_assets=top_defensive,
            sleeve_weight=0.60,
            cash_ticker=cash_ticker,
        )

    # Safety normalization for floating point issues
    total_weight = weights.sum()

    if total_weight <= 0:
        weights[cash_ticker] = 1.0
    elif abs(total_weight - 1.0) > 1e-8:
        weights = weights / total_weight

    return weights


def build_monthly_weights_from_signals(
    total_score: pd.DataFrame,
    investable: pd.DataFrame,
    spy_trend: pd.Series,
    spy_momentum_6m: pd.Series,
    cash_ticker: str = "SHY",
) -> pd.DataFrame:
    """Build monthly portfolio weights from in-memory signal datasets."""
    all_assets = total_score.columns.tolist()
    weights = pd.DataFrame(0.0, index=total_score.index, columns=all_assets)

    for date in total_score.index:
        weights.loc[date] = build_core_satellite_portfolio_for_date(
            scores_today=total_score.loc[date],
            investable_today=investable.loc[date],
            spy_trend_today=spy_trend.loc[date],
            spy_momentum_6m_today=spy_momentum_6m.loc[date],
            all_assets=all_assets,
            cash_ticker=cash_ticker,
        )

    return weights


def build_monthly_weights() -> pd.DataFrame:
    config_path = PROJECT_ROOT / "configs" / "backtest_config.yaml"
    config = load_yaml_config(config_path)

    cash_ticker = config["backtest"]["cash_ticker"]

    total_score = load_total_score()
    investable = load_investable()
    spy_trend = load_spy_trend()
    spy_momentum_6m = load_spy_momentum_6m()

    weights = build_monthly_weights_from_signals(
        total_score=total_score,
        investable=investable,
        spy_trend=spy_trend,
        spy_momentum_6m=spy_momentum_6m,
        cash_ticker=cash_ticker,
    )

    output_dir = PROJECT_ROOT / "data" / "processed" / "portfolio"
    output_dir.mkdir(parents=True, exist_ok=True)

    weights.to_parquet(output_dir / "monthly_weights.parquet")

    print("Portfolio weights completed successfully.")
    print("Model version: AlphaCore v1.3 strong risk-on core-satellite portfolio")
    print(f"Portfolio files saved to: {output_dir}")
    print("Latest portfolio weights:")
    print(weights.tail(1).T.sort_values(by=weights.index[-1], ascending=False))
    print("Latest weight sum:")
    print(weights.tail(1).sum(axis=1))

    return weights


if __name__ == "__main__":
    build_monthly_weights()
