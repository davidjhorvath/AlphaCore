from pathlib import Path

import pandas as pd

try:
    from src.backtest import load_monthly_weights, load_yaml_config
    from src.features import load_monthly_prices
    from src.portfolio import (
        load_investable,
        load_spy_momentum_6m,
        load_spy_trend,
    )
except ModuleNotFoundError:
    from backtest import load_monthly_weights, load_yaml_config
    from features import load_monthly_prices
    from portfolio import load_investable, load_spy_momentum_6m, load_spy_trend


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_VERSION = "AlphaCore v1.3b"
MAX_DECISION_DELAY_DAYS = 7


def last_completed_month_end(
    as_of_date: str | pd.Timestamp | None = None,
) -> pd.Timestamp:
    """Return the final day of the last completed calendar month."""
    as_of = pd.Timestamp(as_of_date) if as_of_date is not None else pd.Timestamp.today()
    return (as_of.to_period("M") - 1).to_timestamp("M")


def validate_monthly_data_freshness(
    latest_data_date: str | pd.Timestamp,
    as_of_date: str | pd.Timestamp | None = None,
) -> pd.Timestamp:
    """Require monthly inputs through the most recently completed month."""
    latest = pd.Timestamp(latest_data_date).to_period("M").to_timestamp("M")
    expected = last_completed_month_end(as_of_date)

    if latest != expected:
        raise ValueError(
            "Paper-trading data is not current. "
            f"Expected completed month {expected.date()}, found {latest.date()}."
        )

    return expected


def validate_decision_timeliness(
    decision_month: str | pd.Timestamp,
    as_of_date: str | pd.Timestamp | None = None,
    max_delay_days: int = MAX_DECISION_DELAY_DAYS,
) -> int:
    """Reject retrospective paper decisions created outside the live window."""
    decision_month_end = pd.Timestamp(decision_month).to_period("M").to_timestamp("M")
    generated_on = pd.Timestamp(
        as_of_date if as_of_date is not None else pd.Timestamp.today()
    ).normalize()
    delay_days = (generated_on - decision_month_end).days

    if delay_days < 0 or delay_days > max_delay_days:
        raise ValueError(
            "Paper-trading decision is outside the allowed generation window. "
            f"Decision month {decision_month_end.date()}, generation date "
            f"{generated_on.date()}, allowed delay 0-{max_delay_days} days."
        )

    return delay_days


def classify_regime(
    spy_trend: float,
    qqq_investable: float,
    spy_momentum_6m: float,
) -> str:
    """Classify the frozen v1.3b portfolio regime for an audit snapshot."""
    if pd.isna(spy_trend):
        return "cash_fallback"

    strong_risk_on = (
        spy_trend == 1.0
        and qqq_investable == 1.0
        and not pd.isna(spy_momentum_6m)
        and spy_momentum_6m > 0
    )
    if strong_risk_on:
        return "strong_risk_on"
    if spy_trend == 1.0:
        return "normal_risk_on"
    return "risk_off"


def build_paper_trading_decision(
    as_of_date: str | pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a validated monthly metadata and target-weight snapshot."""
    config = load_yaml_config(PROJECT_ROOT / "configs" / "backtest_config.yaml")
    prices = load_monthly_prices()
    weights = load_monthly_weights()
    investable = load_investable()
    spy_trend = load_spy_trend()
    spy_momentum_6m = load_spy_momentum_6m()

    latest_price_date = prices.dropna(how="all").index.max()
    decision_date = weights.dropna(how="all").index.max()
    expected_month = validate_monthly_data_freshness(
        latest_price_date,
        as_of_date,
    )
    validate_monthly_data_freshness(decision_date, as_of_date)
    generation_delay_days = validate_decision_timeliness(
        expected_month,
        as_of_date,
    )

    required_datasets = {
        "investable": investable,
        "spy_trend": spy_trend,
        "spy_momentum_6m": spy_momentum_6m,
    }
    for name, dataset in required_datasets.items():
        if decision_date not in dataset.index:
            raise ValueError(
                f"Paper-trading dataset {name} has no row for {decision_date.date()}."
            )

    target_weights = weights.loc[decision_date].astype(float)
    weight_history = weights.loc[:decision_date]
    if len(weight_history) == 1:
        turnover = target_weights.abs().sum() / 2
    else:
        previous_weights = weight_history.iloc[-2].astype(float)
        turnover = (target_weights - previous_weights).abs().sum() / 2

    transaction_cost_bps = config["backtest"]["transaction_cost_bps"]
    regime = classify_regime(
        spy_trend=float(spy_trend.loc[decision_date]),
        qqq_investable=float(investable.loc[decision_date, "QQQ"]),
        spy_momentum_6m=float(spy_momentum_6m.loc[decision_date]),
    )
    metadata = pd.DataFrame([{
        "model_version": MODEL_VERSION,
        "as_of_date": pd.Timestamp(as_of_date or pd.Timestamp.today()).date().isoformat(),
        "decision_month": expected_month.date().isoformat(),
        "latest_price_month": pd.Timestamp(latest_price_date).date().isoformat(),
        "generation_delay_days": generation_delay_days,
        "regime": regime,
        "signal_lag_months": config["backtest"]["signal_lag"],
        "transaction_cost_bps": transaction_cost_bps,
        "target_weight_sum": target_weights.sum(),
        "monthly_turnover": turnover,
        "estimated_cost_return": turnover * (transaction_cost_bps / 10000),
    }])
    targets = target_weights.rename("target_weight").to_frame()
    targets.index.name = "asset"
    targets["selected"] = targets["target_weight"] > 0

    return metadata, targets


def run_paper_trading_decision(
    as_of_date: str | pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate and save one immutable monthly paper-trading decision."""
    metadata, targets = build_paper_trading_decision(as_of_date)
    decision_month = metadata.loc[0, "decision_month"]
    output_dir = (
        PROJECT_ROOT
        / "reports"
        / "paper_trading"
        / "decisions"
        / decision_month
    )
    metadata_path = output_dir / "metadata.csv"
    targets_path = output_dir / "target_weights.csv"

    if metadata_path.exists() or targets_path.exists():
        raise FileExistsError(
            f"Paper-trading decision already exists for {decision_month}."
        )

    output_dir.mkdir(parents=True, exist_ok=False)
    metadata.to_csv(metadata_path, index=False)
    targets.to_csv(targets_path)

    print("Paper-trading decision completed successfully.")
    print(f"Metadata saved to: {metadata_path}")
    print(f"Target weights saved to: {targets_path}")
    print()
    print(metadata.to_string(index=False))
    print()
    print(targets[targets["selected"]].to_string())

    return metadata, targets


if __name__ == "__main__":
    try:
        run_paper_trading_decision()
    except (ValueError, FileExistsError) as error:
        print(f"Paper-trading decision not created: {error}")
        raise SystemExit(1) from None
