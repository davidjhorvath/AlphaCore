# AlphaCore Model Version Log

## AlphaCore v1.0 — Basic Top-N ETF Rotation

**Date:** 2026-05-11  
**Universe:** SPY, QQQ, EFA, EEM, AGG, IEF, TLT, SHY, GLD, DBC, VNQ  
**Rebalancing:** Monthly  
**Signal lag:** 1 month  
**Transaction costs:** 10 bps per turnover  

### Model logic
- Rank all ETF assets together using:
  - 40% trend score
  - 40% composite momentum rank
  - 10% volatility rank
  - 10% drawdown rank
- Select top 4 investable ETFs.
- Equal weight selected ETFs.
- Use SHY as cash fallback.

### Result summary
- CAGR: 4.66%
- Volatility: 7.41%
- Sharpe: 0.65
- Max drawdown: -13.98%

### Diagnosis
The model reduced drawdowns effectively but was too defensive. SHY and bond ETFs competed directly with equity ETFs and were selected too often.

---

## AlphaCore v1.1 — Risky/Defensive Sleeve Portfolio

**Date:** 2026-05-11  

### Model logic
- Separate universe into:
  - Risky sleeve: SPY, QQQ, EFA, EEM, VNQ, DBC, GLD
  - Defensive sleeve: AGG, IEF, TLT, SHY
- Risk-on if SPY is above 10-month moving average.
- Risk-off if SPY is below 10-month moving average.
- Risk-on allocation:
  - 75% risky sleeve
  - 25% defensive sleeve
- Risk-off allocation:
  - 40% risky sleeve
  - 60% defensive sleeve

### Result summary
- CAGR: 5.25%
- Volatility: 8.25%
- Sharpe: 0.66
- Max drawdown: -13.77%

### Diagnosis
The model increased risky exposure but still had insufficient exposure to the main equity premium, especially SPY and QQQ.

---

## AlphaCore v1.2 — Core-Satellite Portfolio

**Date:** 2026-05-11  

### Model logic
- Introduced core-satellite structure.
- Risk-on:
  - 25% SPY
  - 15% QQQ
  - 35% top 2 tactical risky assets
  - 25% top defensive asset
- Risk-off:
  - 20% SPY if investable, otherwise SHY
  - 20% top tactical risky asset
  - 60% top defensive asset

### Result summary
- CAGR: 6.20%
- Volatility: 7.34%
- Sharpe: 0.86
- Sortino: 1.29
- Max drawdown: -11.25%
- Calmar: 0.55
- Average monthly turnover: 26.37%

### Diagnosis
This version significantly improved risk-adjusted performance and drawdown control. It nearly matched the 60/40 Sharpe ratio while having much lower maximum drawdown. However, it still underperformed 60/40 and SPY on absolute CAGR.

### Current status
Promising, but not validated. Needs robustness testing, subperiod analysis, rolling metrics, and out-of-sample evaluation.

---

## AlphaCore v1.3 — Strong Risk-On Core-Satellite Portfolio

**Date:** 2026-05-11  

### Model logic
AlphaCore v1.3 adds a strong risk-on regime to improve upside participation.

Strong risk-on is active when:
- SPY is above its 10-month moving average,
- QQQ is investable,
- SPY 6-month momentum is positive.

### Allocation rules

**Strong risk-on**
- 35% SPY
- 20% QQQ
- 25% top 2 tactical risky assets
- 20% top defensive asset

**Normal risk-on**
- 25% SPY
- 15% QQQ
- 35% top 2 tactical risky assets
- 25% top defensive asset

**Risk-off**
- 20% SPY if investable, otherwise SHY
- 20% top 1 tactical risky asset
- 60% top defensive asset

### Result summary
- CAGR: 6.97%
- Volatility: 7.80%
- Sharpe: 0.90
- Sortino: 1.33
- Max drawdown: -10.81%
- Calmar: 0.64
- Average monthly turnover: 24.39%

### Relative metrics vs SPY
- Beta: 0.34
- Correlation: 0.66
- Annualized alpha estimate: 3.22%
- Information ratio vs SPY: -0.40
- Average upside capture: 49.38%
- Average downside capture: 40.47%

### Diagnosis
v1.3 improves upside participation compared with v1.2 while keeping drawdown low. The model still does not beat SPY or 60/40 on absolute CAGR, but it improves risk-adjusted performance and preserves the defensive character of the system.

### Decision
v1.3 becomes the current working model. Do not optimize parameters further until rolling performance, regime exposure, and benchmark-relative robustness are analyzed.

---

---

## AlphaCore v1.3b — Corrected Cross-Sectional Ranking

**Date:** 2026-05-11

### Reason for update

Unit tests revealed that the `cross_sectional_rank()` function in `src/signals.py` ranked features in the wrong direction. The function used:

```python
ascending=not higher_is_better
```

This was incorrect. It was replaced with:

```python
ascending=higher_is_better
```

### Impact

The previous v1.3 results were based on incorrectly ranked signal components and should no longer be treated as valid.

After the correction, signal ranking became economically consistent:

- higher momentum receives a higher rank,
- lower volatility receives a higher rank when `higher_is_better=False`,
- smaller drawdown receives a higher rank when appropriate.

### Updated AlphaCore v1.3b net results

- CAGR: 8.37%
- Annualized volatility: 8.20%
- Max drawdown: -14.91%
- Calmar ratio: 0.56
- Average monthly turnover: 21.63%

### Benchmark comparison

- AlphaCore net CAGR: 8.37%
- 60/40 CAGR: 8.09%
- SPY CAGR: 11.05%
- Equal-weight CAGR: 7.01%

### Relative metrics vs SPY

- Beta: 0.31
- Correlation: 0.57
- Annualized alpha estimate: 4.97%
- Information ratio: -0.26
- Average upside capture: 51.31%
- Average downside capture: 35.16%

### Relative metrics vs 60/40

- Beta: 0.51
- Correlation: 0.60
- Annualized alpha estimate: 4.28%
- Information ratio: 0.02
- Average upside capture: 79.30%
- Average downside capture: 59.25%

### Rolling 36-month metrics

- Mean rolling CAGR: 8.20%
- Minimum rolling CAGR: 2.11%
- Mean rolling Sharpe: 1.00
- Minimum rolling Sharpe: 0.32
- Worst rolling max drawdown: -14.91%
- Mean rolling beta vs SPY: 0.36

### Test status

- 20 tests passing
- Feature calculations tested
- Signal ranking tested
- Portfolio regime logic tested
- Backtest anti-look-ahead logic tested

### Diagnosis

AlphaCore v1.3b is now the current valid working model. It appears to be a stronger risk-managed tactical multi-asset allocator than the previous v1.3 version. It beats 60/40 on CAGR while maintaining substantially lower drawdown, but still trails SPY on absolute return.

### Decision

Freeze v1.3b as the current working model. Do not optimize further until additional validation is completed.

## AlphaCore v1.3b — Robustness Validation Gate

**Date:** 2026-08-29

### Completed validation
- Common-sample and signal-lag alignment
- Initial allocation cost accounting
- Transaction-cost sensitivity at 10, 25, and 50 bps
- Additional one-month execution-delay stress
- 9/10/11-month trend-window neighborhood
- Annual start-date sensitivity from 2006 through 2016
- 5,000-sample paired 12-month moving-block bootstrap
- 37 passing unit tests

### Final diagnosis
The model is robust enough to support the narrow description of a defensive tactical multi-asset allocator. Drawdown control is the most persistent result. Absolute CAGR superiority over 60/40 is not robust across implementation costs, execution delay, later start dates, or bootstrap uncertainty.

### Gate decision
- Controlled paper trading: conditional GO
- Historical parameter optimization: NO-GO
- Individual-stock expansion: NO-GO
- Real-money deployment: NO-GO

AlphaCore v1.3b remains frozen. The next phase is operational paper-trading validation, not further backtest optimization.
