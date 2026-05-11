import pandas as pd

from src.portfolio import (
    build_core_satellite_portfolio_for_date,
    select_top_assets,
    allocate_equal,
)


ALL_ASSETS = [
    "SPY",
    "QQQ",
    "EFA",
    "EEM",
    "VNQ",
    "DBC",
    "GLD",
    "AGG",
    "IEF",
    "TLT",
    "SHY",
]


def test_select_top_assets_ignores_nan_scores():
    scores = pd.Series(
        {
            "SPY": 0.90,
            "QQQ": float("nan"),
            "EFA": 0.70,
            "GLD": 0.80,
        }
    )

    selected = select_top_assets(
        scores=scores,
        candidates=["SPY", "QQQ", "EFA", "GLD"],
        top_n=2,
    )

    assert selected == ["SPY", "GLD"]


def test_allocate_equal_allocates_to_cash_when_no_assets_selected():
    weights = pd.Series(0.0, index=ALL_ASSETS)

    allocate_equal(
        weights=weights,
        selected_assets=[],
        sleeve_weight=0.25,
        cash_ticker="SHY",
    )

    assert weights["SHY"] == 0.25
    assert weights.sum() == 0.25


def test_spy_trend_nan_allocates_100_percent_to_cash():
    scores_today = pd.Series(0.5, index=ALL_ASSETS)
    investable_today = pd.Series(1.0, index=ALL_ASSETS)

    weights = build_core_satellite_portfolio_for_date(
        scores_today=scores_today,
        investable_today=investable_today,
        spy_trend_today=float("nan"),
        spy_momentum_6m_today=0.10,
        all_assets=ALL_ASSETS,
        cash_ticker="SHY",
    )

    assert weights["SHY"] == 1.0
    assert weights.drop("SHY").sum() == 0.0
    assert weights.sum() == 1.0


def test_strong_risk_on_weights_sum_to_one():
    scores_today = pd.Series(
        {
            "SPY": 0.90,
            "QQQ": 0.85,
            "EFA": 0.80,
            "EEM": 0.50,
            "VNQ": 0.70,
            "DBC": 0.60,
            "GLD": 0.75,
            "AGG": 0.65,
            "IEF": 0.40,
            "TLT": 0.30,
            "SHY": 0.20,
        }
    )
    investable_today = pd.Series(1.0, index=ALL_ASSETS)

    weights = build_core_satellite_portfolio_for_date(
        scores_today=scores_today,
        investable_today=investable_today,
        spy_trend_today=1.0,
        spy_momentum_6m_today=0.10,
        all_assets=ALL_ASSETS,
        cash_ticker="SHY",
    )

    assert abs(weights.sum() - 1.0) < 1e-12
    assert weights["SPY"] == 0.35
    assert weights["QQQ"] == 0.20
    assert weights["AGG"] == 0.20

    # Top 2 tactical risky assets from EFA, EEM, VNQ, DBC, GLD:
    # EFA = 0.80, GLD = 0.75
    assert weights["EFA"] == 0.125
    assert weights["GLD"] == 0.125


def test_normal_risk_on_weights_sum_to_one():
    scores_today = pd.Series(
        {
            "SPY": 0.90,
            "QQQ": 0.85,
            "EFA": 0.80,
            "EEM": 0.50,
            "VNQ": 0.70,
            "DBC": 0.60,
            "GLD": 0.75,
            "AGG": 0.65,
            "IEF": 0.40,
            "TLT": 0.30,
            "SHY": 0.20,
        }
    )
    investable_today = pd.Series(1.0, index=ALL_ASSETS)

    weights = build_core_satellite_portfolio_for_date(
        scores_today=scores_today,
        investable_today=investable_today,
        spy_trend_today=1.0,
        spy_momentum_6m_today=-0.05,
        all_assets=ALL_ASSETS,
        cash_ticker="SHY",
    )

    assert abs(weights.sum() - 1.0) < 1e-12
    assert weights["SPY"] == 0.25
    assert weights["QQQ"] == 0.15
    assert weights["AGG"] == 0.25

    # Top 2 tactical risky assets receive 35% total, 17.5% each
    assert weights["EFA"] == 0.175
    assert weights["GLD"] == 0.175


def test_risk_off_weights_sum_to_one():
    scores_today = pd.Series(
        {
            "SPY": 0.90,
            "QQQ": 0.85,
            "EFA": 0.80,
            "EEM": 0.50,
            "VNQ": 0.70,
            "DBC": 0.60,
            "GLD": 0.75,
            "AGG": 0.65,
            "IEF": 0.40,
            "TLT": 0.30,
            "SHY": 0.20,
        }
    )
    investable_today = pd.Series(1.0, index=ALL_ASSETS)

    weights = build_core_satellite_portfolio_for_date(
        scores_today=scores_today,
        investable_today=investable_today,
        spy_trend_today=0.0,
        spy_momentum_6m_today=-0.10,
        all_assets=ALL_ASSETS,
        cash_ticker="SHY",
    )

    assert abs(weights.sum() - 1.0) < 1e-12
    assert weights["SPY"] == 0.20
    assert weights["EFA"] == 0.20
    assert weights["AGG"] == 0.60


def test_risk_off_spy_not_investable_sends_core_to_cash():
    scores_today = pd.Series(
        {
            "SPY": 0.90,
            "QQQ": 0.85,
            "EFA": 0.80,
            "EEM": 0.50,
            "VNQ": 0.70,
            "DBC": 0.60,
            "GLD": 0.75,
            "AGG": 0.65,
            "IEF": 0.40,
            "TLT": 0.30,
            "SHY": 0.20,
        }
    )

    investable_today = pd.Series(1.0, index=ALL_ASSETS)
    investable_today["SPY"] = 0.0

    weights = build_core_satellite_portfolio_for_date(
        scores_today=scores_today,
        investable_today=investable_today,
        spy_trend_today=0.0,
        spy_momentum_6m_today=-0.10,
        all_assets=ALL_ASSETS,
        cash_ticker="SHY",
    )

    assert abs(weights.sum() - 1.0) < 1e-12
    assert weights["SPY"] == 0.0
    assert weights["SHY"] == 0.20
    assert weights["EFA"] == 0.20
    assert weights["AGG"] == 0.60