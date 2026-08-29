import pandas as pd
import pytest

from src.paper_trading import (
    classify_regime,
    last_completed_month_end,
    validate_decision_timeliness,
    validate_monthly_data_freshness,
)


def test_last_completed_month_end_excludes_current_calendar_month():
    assert last_completed_month_end("2026-08-29") == pd.Timestamp("2026-07-31")


def test_monthly_freshness_accepts_last_completed_month():
    result = validate_monthly_data_freshness(
        latest_data_date="2026-07-31",
        as_of_date="2026-08-29",
    )

    assert result == pd.Timestamp("2026-07-31")


def test_monthly_freshness_rejects_stale_data():
    with pytest.raises(ValueError, match="Expected completed month 2026-07-31"):
        validate_monthly_data_freshness(
            latest_data_date="2026-05-31",
            as_of_date="2026-08-29",
        )


def test_decision_timeliness_accepts_early_next_month():
    delay_days = validate_decision_timeliness(
        decision_month="2026-07-31",
        as_of_date="2026-08-05",
    )

    assert delay_days == 5


def test_decision_timeliness_rejects_retrospective_decision():
    with pytest.raises(ValueError, match="outside the allowed generation window"):
        validate_decision_timeliness(
            decision_month="2026-07-31",
            as_of_date="2026-08-29",
        )


@pytest.mark.parametrize(
    ("spy_trend", "qqq_investable", "spy_momentum_6m", "expected"),
    [
        (1.0, 1.0, 0.10, "strong_risk_on"),
        (1.0, 0.0, 0.10, "normal_risk_on"),
        (0.0, 1.0, 0.10, "risk_off"),
        (float("nan"), 1.0, 0.10, "cash_fallback"),
    ],
)
def test_classify_regime_matches_frozen_portfolio_logic(
    spy_trend,
    qqq_investable,
    spy_momentum_6m,
    expected,
):
    assert classify_regime(
        spy_trend,
        qqq_investable,
        spy_momentum_6m,
    ) == expected
