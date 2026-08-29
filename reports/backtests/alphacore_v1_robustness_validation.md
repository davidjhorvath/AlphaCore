# AlphaCore v1.3b Robustness Validation Scorecard

**Decision date:** 2026-08-29
**Model:** AlphaCore v1.3b — Corrected Cross-Sectional Ranking
**Universe:** Frozen 11-ETF research universe
**Test status:** 37 passed

## Executive decision

AlphaCore v1.3b is approved for controlled, monitored paper trading as a defensive tactical multi-asset allocator.

It is not approved for real-money deployment and should not be described as a proven alpha engine or a reliable absolute-return winner over 60/40.

The evidence supports a narrower claim:

> AlphaCore v1.3b has historically delivered stable absolute returns and materially better drawdown control than simple benchmarks, but its return advantage over 60/40 is small, implementation-sensitive, and statistically uncertain.

## Decision matrix

| Validation area | Status | Main finding |
|---|---|---|
| Backtest sample alignment | PASS | Strategy and benchmarks use 244 common valid months from February 2006. |
| Initial allocation costs | PASS | The first actual portfolio establishment is now charged consistently. |
| Transaction-cost sensitivity | CONDITIONAL | Defensive behavior survives 50 bps, but the CAGR edge over 60/40 disappears by 25 bps. |
| Additional execution delay | CONDITIONAL | A second month of delay reduces CAGR and Sharpe, while drawdown control survives. |
| 9/10/11-month trend neighborhood | PASS | Results are locally stable; the frozen 10-month setting is not an isolated optimum. |
| Start-date sensitivity | CONDITIONAL | Drawdown improves in 11/11 samples, but CAGR beats 60/40 in only 3/11. |
| Moving-block bootstrap | CONDITIONAL | Drawdown benefit is probable, while CAGR and Sharpe superiority are not statistically reliable. |
| True out-of-sample evidence | NOT TESTED | Historical resampling is not a substitute for a live record. |
| Paper-trading readiness | CONDITIONAL GO | Operationally ready if the model remains frozen and all decisions are logged. |
| Real-money readiness | NO-GO | Live operational evidence and investable-instrument validation are missing. |

## Evidence summary

### Frozen baseline

- Net CAGR: 8.40%
- Annualized volatility: 8.21%
- Risk-free-adjusted Sharpe: 0.818
- Sortino: 1.344
- Maximum drawdown: -14.91%
- Average monthly turnover: 21.93%
- CAGR spread over 60/40: +0.31 percentage points

### Transaction costs

At 25 bps, net CAGR falls to 7.98% and trails 60/40 by 0.11 percentage points. At 50 bps, Sharpe remains 0.689 and maximum drawdown remains limited to -15.81%, but CAGR trails 60/40 by 0.82 percentage points.

### Execution timing

Increasing the signal lag from one to two months lowers CAGR from 8.44% to 7.94% on the common sample and lowers Sharpe from 0.822 to 0.688. Maximum drawdown remains near -14.5%.

### Trend-window neighborhood

The 9-, 10-, and 11-month windows produce CAGRs of 9.25%, 8.40%, and 8.43%. Nearby variants retain high return correlations and identical monthly weights in more than 93% of months. The superior 9-month result is not a reason to optimize after observing the test.

### Start dates

Across annual start dates from 2006 through 2016, AlphaCore CAGR remains between 7.83% and 9.12%. It has a smaller maximum drawdown than 60/40 in all 11 samples and a higher Sharpe ratio in 8, but a higher CAGR in only 3.

### Bootstrap uncertainty

Using 5,000 paired circular 12-month block samples:

- probability of positive CAGR spread over 60/40: 53.88%;
- probability of positive Sharpe spread: 70.92%;
- probability of better maximum drawdown: 88.78%;
- all relative 95% intervals cross zero.

## Paper-trading operating rules

1. Freeze the ETF universe, signal formula, 10-month trend window, regime rules, and portfolio construction.
2. Generate and record one scheduled decision per month, including input-data timestamp, signals, target weights, turnover, and assumed costs.
3. Record data failures, missing prices, stale signals, manual overrides, and deviations from target weights as operational incidents.
4. Do not alter the model because of short-term underperformance. Only documented correctness defects may be fixed during the initial observation period.
5. Compare paper results with AlphaCore net, 60/40, and SPY using the same calendar months and risk-free series.
6. Complete at least 12 scheduled monthly decisions before the first formal operational review. Treat 12 months as an operational checkpoint, not proof of performance.
7. Keep real capital out of scope until the paper record, European/UCITS implementation mapping, data quality, and execution assumptions receive separate approval.

## Claims discipline

Allowed description:

> AlphaCore v1.3b is a research-stage defensive tactical allocator with historically stable returns and materially lower drawdowns than 60/40 and SPY.

Disallowed description:

> AlphaCore v1.3b is a proven alpha engine or reliably beats 60/40.

## Method limitations

All historical tests share the same underlying data and model-development history. Start-date samples overlap, and bootstrap samples reuse historical observations. These tests measure sensitivity and uncertainty; they do not create independent out-of-sample evidence.

## Final gate

- **Controlled paper trading:** GO, conditional on the operating rules above.
- **Further historical parameter optimization:** NO-GO.
- **Expansion to individual stocks:** NO-GO at this stage.
- **Real-money deployment:** NO-GO.
