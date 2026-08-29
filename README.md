# AlphaCore

AlphaCore is a private AI-quant hedge fund research engine and personal paper hedge fund lab.

The project is not a public SaaS product and not a real-money trading bot. The purpose is to build a disciplined, research-driven quantitative investment system that combines financial theory, market data, macro signals, momentum, trend, risk management, portfolio construction, backtesting, and paper trading.

Current working model:

**AlphaCore v1.3b — Corrected Cross-Sectional Ranking**

---

## 1. Project purpose

AlphaCore is designed as a long-term personal quant research lab.

The goal is to test whether systematic multi-asset allocation rules can improve risk-adjusted performance, reduce drawdowns, and create a more disciplined investment process compared with simple benchmarks such as:

- SPY
- 60/40 portfolio
- equal-weight ETF portfolio
- cash proxy

AlphaCore starts as a paper-traded demo fund with virtual capital. It should not be used with real money until the system has been tested, documented, and monitored over a long live paper-trading period.

---

## 2. Current model: AlphaCore v1.3b

AlphaCore v1.3b is a defensive tactical multi-asset allocation model with corrected cross-sectional signal ranking.

It uses:

- monthly rebalancing,
- ETF universe,
- trend signals,
- momentum signals,
- volatility and drawdown risk filters,
- core-satellite portfolio construction,
- strong risk-on regime,
- benchmark comparison,
- transaction costs,
- one-month signal lag to reduce look-ahead bias.

The model is not a high-return equity strategy. Its current strength is drawdown control, smoother compounding, and capital preservation.

---

## 3. ETF universe

Current research universe:

- SPY — S&P 500
- QQQ — Nasdaq 100
- EFA — Developed markets ex-US
- EEM — Emerging markets
- AGG — Aggregate bonds
- IEF — 7–10Y Treasuries
- TLT — Long-term Treasuries
- SHY — Short-term Treasuries / cash proxy
- GLD — Gold
- DBC — Commodities
- VNQ — Real estate

Important limitation: these are US ETF proxies used for research. They are not necessarily directly tradable or optimal for a European investor. Later versions should evaluate UCITS ETF equivalents.

---

## 4. Model architecture

The project currently includes:

```text
Data Layer
Feature Layer
Signal Engine
Portfolio Engine
Backtest Engine
Performance Engine
Relative Metrics
Rolling Metrics
Chart Reporting
Research Journal

Main source files:

```text

src/data_loader.py

src/features.py

src/signals.py

src/portfolio.py

src/backtest.py

src/performance.py

src/reporting.py

```

---

## 5. Current portfolio logic

### Strong risk-on

Strong risk-on is active when:

- SPY is above its 10-month moving average,

- QQQ is investable,

- SPY 6-month momentum is positive.

Allocation:

- 35% SPY

- 20% QQQ

- 25% top 2 tactical risky assets

- 20% top defensive asset

### Normal risk-on

Allocation:

- 25% SPY

- 15% QQQ

- 35% top 2 tactical risky assets

- 25% top defensive asset

### Risk-off

Allocation:

- 20% SPY if investable, otherwise SHY

- 20% top 1 tactical risky asset

- 60% top defensive asset

---

## 6. Current performance summary

AlphaCore v1.3b net results:

- CAGR: 8.40%

- Annualized volatility: 8.21%

- Risk-free-adjusted Sharpe ratio: 0.818

- Sortino ratio: 1.344

- Max drawdown: -14.91%

- Calmar ratio: 0.564

- Average monthly turnover: 21.93%

Main interpretation:

AlphaCore v1.3b has strong drawdown control and smoother compounding. Its full-period CAGR slightly exceeds 60/40, but robustness tests show that this small advantage is sensitive to costs, execution timing, and start date. It is best understood as a defensive tactical multi-asset allocator, not a proven alpha engine.

---

## 7. Key research findings

### Strengths

- Much lower drawdown than SPY and 60/40.

- More stable rolling 36-month performance than SPY.

- Positive rolling CAGR in all tested 36-month windows.

- Stronger behavior during crisis periods such as 2008 and 2022.

- Lower beta and lower correlation compared with SPY.

### Weaknesses

- Lower absolute CAGR than SPY and 60/40.

- Negative information ratio versus SPY.

- Upside capture remains limited.

- Underperforms during strong equity bull markets.

- Uses Yahoo Finance data, which is acceptable for research MVP but not institutional-grade.

- Absolute CAGR superiority over 60/40 is not robust.

- True out-of-sample and live paper-trading evidence are not available yet.

---

## 8. How to run the project

Activate the virtual environment:

```bash

cd ~/Desktop/AlphaCore

source .venv/bin/activate

```

Run the full pipeline in order:

```bash

python src/data_loader.py

python src/features.py

python src/signals.py

python src/portfolio.py

python src/backtest.py

python src/performance.py

python src/reporting.py

```

After refreshing all monthly datasets and signals, create the next validated paper-trading decision:

```bash
python src/paper_trading.py
```

The command refuses to create a snapshot if inputs do not reach the last completed calendar month, the decision is generated more than seven days after month-end, or a decision already exists for that month.

Generated outputs:

```text

data/processed/

reports/backtests/

reports/backtests/charts/

```

Charts:

```text

equity_curve_alphacore_vs_benchmarks.png

drawdown_alphacore_vs_benchmarks.png

rolling_sharpe_36m.png

```

---

## 9. Research discipline rules

AlphaCore must follow strict research discipline:

1. No model goes into the system without a backtest.

2. Every signal must have an economic reason.

3. Avoid overfitting and parameter fishing.

4. Use signal lag to reduce look-ahead bias.

5. Compare every model to simple benchmarks.

6. Track turnover and transaction costs.

7. Document every model version.

8. Do not change rules after every bad result.

9. Do not use real money in the early phase.

10. Treat attractive backtests with skepticism.

---

## 10. Current status

Current working model:

```text

AlphaCore v1.3b — Corrected Cross-Sectional Ranking

```

Current diagnosis:

```text

Conditional GO for controlled monthly paper trading as a defensive allocator.

NO-GO for real-money deployment, individual-stock expansion, or further historical parameter optimization.

```

Next phase:

- refresh data through the last completed month,

- generate one immutable target-weight decision per month,

- log data quality, turnover, costs, overrides, and execution deviations,

- complete at least 12 scheduled decisions before the first operational review.

## 11. Running tests

Run all tests:

```bash
python -m pytest
```

Current test coverage includes:

* feature calculations,
* risk-free alignment and adjusted metrics,
* portfolio construction rules,
* backtest timing logic,
* turnover calculation,
* look-ahead and sample-alignment protection,
* robustness scenario calculations,
* paper-trading freshness and regime gates.

Current status:
45 tests passing
