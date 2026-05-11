from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURE_DIR = PROJECT_ROOT / "data" / "processed" / "features"


def load_feature(name: str) -> pd.DataFrame:
    """
    Load one feature dataset from parquet.
    """
    path = FEATURE_DIR / f"{name}.parquet"

    if not path.exists():
        raise FileNotFoundError(f"Feature file not found: {path}")

    return pd.read_parquet(path)


def cross_sectional_rank(feature: pd.DataFrame, higher_is_better: bool = True) -> pd.DataFrame:
    """
    Convert raw feature values into cross-sectional percentile ranks by date.

    Output range:
    0 to 1.

    If higher_is_better=True:
    higher values get higher ranks.

    If higher_is_better=False:
    lower values get higher ranks.
    """
    return feature.rank(
        axis=1,
        pct=True,
        ascending=higher_is_better,
    )


def build_signal_scores() -> dict[str, pd.DataFrame]:
    """
    Build AlphaCore v1 signal scores.

    Components:
    - Trend score: 1 if ETF is above 10M moving average, else 0
    - Momentum score: cross-sectional rank of composite momentum
    - Volatility score: lower volatility gets better rank
    - Drawdown score: smaller drawdown gets better rank

    Final score:
    40% trend
    40% momentum
    10% volatility
    10% drawdown
    """
    trend = load_feature("trend_10m")
    momentum = load_feature("composite_momentum")
    volatility = load_feature("realized_volatility_12m")
    drawdown = load_feature("drawdown")

    momentum_rank = cross_sectional_rank(momentum, higher_is_better=True)
    volatility_rank = cross_sectional_rank(volatility, higher_is_better=False)
    drawdown_rank = cross_sectional_rank(drawdown, higher_is_better=True)

    total_score = (
        0.40 * trend
        + 0.40 * momentum_rank
        + 0.10 * volatility_rank
        + 0.10 * drawdown_rank
    )

    # ETF is investable only if:
    # 1. trend is positive
    # 2. momentum is positive
    investable = (trend == 1.0) & (momentum > 0)

    total_score = total_score.where(investable)

    output_dir = PROJECT_ROOT / "data" / "processed" / "signals"
    output_dir.mkdir(parents=True, exist_ok=True)

    scores = {
        "momentum_rank": momentum_rank,
        "volatility_rank": volatility_rank,
        "drawdown_rank": drawdown_rank,
        "total_score": total_score,
        "investable": investable.astype(float),
    }

    for name, data in scores.items():
        data.to_parquet(output_dir / f"{name}.parquet")

    print("Signal scores completed successfully.")
    print(f"Signal files saved to: {output_dir}")
    print("Latest total score:")
    print(total_score.tail(1).T.sort_values(by=total_score.index[-1], ascending=False))

    return scores


if __name__ == "__main__":
    build_signal_scores()
