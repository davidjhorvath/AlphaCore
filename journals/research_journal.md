## Research Note — AlphaCore v1.2 Subperiod Analysis

**Date:** 2026-05-11  
**Model:** AlphaCore v1.2 Core-Satellite Portfolio

### Objective
Test whether AlphaCore v1.2 performance is stable across different historical market regimes.

### Key results
AlphaCore v1.2 shows strong drawdown control and performs best during crisis or volatile regimes.

Full-period net results:
- CAGR: 6.20%
- Volatility: 7.34%
- Sharpe: 0.86
- Max drawdown: -11.25%
- Calmar: 0.55

### Subperiod observations

**2006–2010**
AlphaCore net achieved 6.46% CAGR, Sharpe 0.86, and max drawdown -9.10%.
It strongly outperformed SPY and 60/40 on risk-adjusted metrics during the global financial crisis period.

**2011–2015**
AlphaCore net underperformed materially. CAGR was 3.37% and Sharpe 0.50, while 60/40 achieved 8.81% CAGR and Sharpe 1.25.
This is the weakest period for the model.

**2016–2020**
AlphaCore produced acceptable risk-adjusted performance with lower drawdown than SPY and 60/40, but lower CAGR.

**2021–2026**
AlphaCore performed well on a risk-adjusted basis, with Sharpe 1.07 and max drawdown -7.94%, outperforming 60/40 on Sharpe and drawdown, but underperforming SPY on CAGR.

### Diagnosis
AlphaCore v1.2 is a strong defensive tactical allocation model. It protects capital well in crisis and volatile markets, but it underperforms in strong bull market regimes.

### Main weakness
The model still lacks enough upside participation during persistent equity bull markets.

### Decision
Do not optimize parameters yet. Next step is to add rolling metrics and yearly return analysis to understand when and why the model lags.

## Research Note — AlphaCore v1.3 Rolling Metrics

**Date:** 2026-05-11  
**Model:** AlphaCore v1.3 Strong Risk-On Core-Satellite Portfolio

### Objective
Evaluate whether AlphaCore v1.3 performance is stable across rolling 36-month windows.

### Key rolling results
- Mean rolling CAGR: 6.81%
- Minimum rolling CAGR: 1.20%
- Latest rolling CAGR: 10.89%
- Mean rolling Sharpe: 0.86
- Minimum rolling Sharpe: 0.17
- Latest rolling Sharpe: 1.36
- Mean rolling max drawdown: -8.56%
- Worst rolling max drawdown: -10.81%
- Mean rolling beta vs SPY: 0.40
- Latest rolling beta vs SPY: 0.47

### Comparison with SPY
SPY had a higher mean rolling CAGR of 11.09%, but also much worse downside behavior.
SPY minimum rolling CAGR was -15.08%, while AlphaCore remained positive in all 36-month windows.
SPY worst rolling drawdown reached -50.78%, while AlphaCore worst rolling drawdown was -10.81%.

### Interpretation
AlphaCore v1.3 appears robust as a defensive tactical allocation model. It sacrifices upside participation but significantly reduces drawdown and improves return stability across rolling windows.

### Main conclusion
AlphaCore v1.3 is not yet a high-return alpha engine. Its current edge is downside control, volatility reduction, and smoother compounding.

### Decision
Freeze AlphaCore v1.3 as the current working model. Do not change allocation rules until risk-free adjusted metrics and benchmark-relative analysis versus 60/40 are completed.

## Robustness Validation — Signal-Lag Sample Alignment

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Objective
Verify that the one-month signal lag does not introduce an artificial return in the warm-up month and that AlphaCore is compared with its benchmarks over the same sample.

### Finding
The first month had no prior-period weights, but the row-wise return calculation converted the all-missing product into a 0.00% strategy return. AlphaCore therefore had 245 reported observations while the benchmarks had 244.

### Correction
Require at least one valid asset contribution when summing portfolio returns. The warm-up month now remains missing, as intended. A regression test also verifies that the first valid AlphaCore return matches the benchmark sample start.

### Impact on AlphaCore v1.3b net results
- Valid observations: 245 to 244
- First valid month: 2006-02-28, matching the benchmarks
- Cumulative return after the subsequent initial-allocation cost correction: 415.91%
- CAGR: 8.37% to 8.40%
- Annualized volatility: 8.20% to 8.21%
- Sharpe ratio: 0.815 to 0.818
- Sortino ratio: 1.339 to 1.344
- Maximum drawdown: unchanged at -14.91%
- Average monthly turnover after the subsequent initial-allocation correction: 21.93%
- Test status after the subsequent correction: 33 passed

### Decision
The correction improves sample consistency without changing the ETF universe, signals, regime rules, or portfolio construction. AlphaCore v1.3b remains the frozen working model. The next small robustness test should be transaction-cost sensitivity.

## Robustness Validation — Transaction-Cost Sensitivity

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Objective
Test whether the fixed v1.3b portfolio remains economically viable under transaction-cost assumptions above the 10 bps baseline, without changing signals, weights, or turnover.

### Scenarios
- 10 bps: current baseline
- 25 bps: moderate implementation stress
- 50 bps: severe implementation stress

### Results

| Cost | CAGR | Sharpe | Sortino | Max drawdown | CAGR vs 60/40 |
|---:|---:|---:|---:|---:|---:|
| 10 bps | 8.40% | 0.818 | 1.344 | -14.91% | +0.31 pp |
| 25 bps | 7.98% | 0.770 | 1.253 | -15.25% | -0.11 pp |
| 50 bps | 7.27% | 0.689 | 1.103 | -15.81% | -0.82 pp |

Average monthly turnover remains 21.93% in every scenario because portfolio decisions are held fixed.

### Interpretation
Risk-adjusted performance and drawdown control degrade gradually rather than collapsing. Even at 50 bps, AlphaCore retains a slightly higher Sharpe ratio and substantially lower maximum drawdown than the 60/40 benchmark. However, the baseline CAGR advantage over 60/40 is small and disappears by 25 bps. The claim that v1.3b beats 60/40 on absolute CAGR is therefore implementation-cost sensitive.

### Decision
AlphaCore v1.3b passes the transaction-cost test as a defensive risk-managed allocator, but not as a robust absolute-return winner over 60/40. Keep the model frozen and do not optimize turnover in response to this result.

## Robustness Validation — Initial Allocation Cost Accounting

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Finding
After applying the one-month signal lag, the turnover series starts with a missing row. The previous turnover calculation only charged initial allocation when valid weights appeared in the first physical row, so it missed the first actual portfolio establishment in February 2006.

### Correction and impact
The first valid 100% allocation now receives turnover of 50% under the model's existing two-sided turnover convention. Leading missing rows remain missing. This changes the baseline cumulative return from 416.17% to 415.91%, CAGR from 8.4065% to 8.4038%, and average monthly turnover from 21.63% to 21.93%. Maximum drawdown remains unchanged at -14.91%.

### Decision
This is an accounting correction, not a model change. The economic conclusions of the sample-alignment and transaction-cost validations remain unchanged.

## Robustness Validation — Additional Execution Delay

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Objective
Test whether v1.3b depends excessively on applying monthly portfolio weights at the first permitted return period. Compare the production one-month signal lag with a stressed two-month lag while holding the universe, signals, portfolio rules, and 10 bps transaction cost fixed.

Both scenarios use the same 243-month sample from 2006-03-31 through 2026-05-31. Turnover and initial allocation costs are recalculated independently from the active weights at the common sample start.

### Results

| Signal lag | CAGR | Volatility | Sharpe | Sortino | Max drawdown | CAGR vs 60/40 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 month | 8.44% | 8.23% | 0.822 | 1.351 | -14.91% | +0.33 pp |
| 2 months | 7.94% | 9.31% | 0.688 | 1.106 | -14.44% | -0.17 pp |

The two-month scenario has 0.751 correlation with the one-month scenario. Average monthly turnover is 22.02% at one month and 21.69% at two months.

### Interpretation
An additional month of execution delay reduces CAGR by 0.50 percentage points and materially lowers Sharpe, but it does not cause a drawdown failure. The strategy's defensive behavior survives while its small absolute-return advantage over 60/40 disappears. Performance is therefore moderately sensitive to execution timing.

### Decision
AlphaCore v1.3b passes the delay test as a defensive allocator, but prompt monthly implementation matters for return capture. Do not change the production signal lag in response to this test.

## Robustness Validation — Trend-Window Neighborhood

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Objective
Test whether the model depends on the exact 10-month trend-filter setting. Compare 9-, 10-, and 11-month moving-average windows while keeping the ETF universe, momentum, volatility, drawdown ranking, regime logic, portfolio construction, one-month signal lag, and 10 bps transaction cost fixed.

The scenarios are calculated in memory and do not overwrite production features, signals, or weights. The reconstructed 10-month scenario was required to match the frozen production weights exactly before the report could complete.

### Results

| Trend window | CAGR | Volatility | Sharpe | Sortino | Max drawdown | Turnover | CAGR vs 60/40 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 9 months | 9.25% | 8.29% | 0.905 | 1.516 | -14.91% | 21.29% | +1.16 pp |
| 10 months | 8.40% | 8.21% | 0.818 | 1.344 | -14.91% | 21.93% | +0.31 pp |
| 11 months | 8.43% | 8.30% | 0.815 | 1.345 | -15.97% | 20.81% | +0.34 pp |

The 9- and 11-month scenarios have return correlations of 0.973 and 0.988 with the 10-month baseline. Their monthly portfolio weights are exactly the same as the baseline in 93.85% and 94.67% of months, respectively.

### Interpretation
The defensive behavior and positive CAGR spread over 60/40 survive both nearby parameter changes. The 10-month result is not an isolated optimum: 11 months is nearly identical, while 9 months is historically stronger. This supports local parameter robustness but does not justify selecting 9 months after observing the result.

### Decision
Keep the frozen production trend window at 10 months. Do not optimize or broaden the parameter search in response to the superior 9-month backtest.

## Robustness Validation — Start-Date Sensitivity

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Objective
Test whether the full-period conclusion depends on a favorable backtest start date. Evaluate the frozen AlphaCore net return series and the 60/40 benchmark from every calendar-year start between 2006 and 2016, leaving at least approximately ten years in each sample.

Each row uses the same valid months for AlphaCore and 60/40. The samples overlap and should be interpreted as sensitivity checks, not independent trials.

### Results summary
- AlphaCore CAGR range: 7.83% to 9.12%
- AlphaCore Sharpe range: 0.710 to 0.925
- AlphaCore maximum drawdown: -14.91% in every tested start-date sample
- Positive AlphaCore CAGR spread over 60/40: 3 of 11 start dates
- Positive AlphaCore Sharpe spread over 60/40: 8 of 11 start dates
- Better AlphaCore maximum drawdown than 60/40: 11 of 11 start dates
- Worst CAGR spread versus 60/40: -2.00 percentage points for the 2009 start
- Best CAGR spread versus 60/40: +0.63 percentage points for the 2007 start

### Interpretation
AlphaCore's own absolute CAGR and downside behavior are stable across start dates. Its maximum drawdown advantage is universal in this test, and its Sharpe ratio is usually higher than 60/40. However, the claim that AlphaCore beats 60/40 on absolute CAGR depends strongly on including the 2006–2008 crisis period and does not survive most later start dates.

### Decision
AlphaCore v1.3b passes start-date sensitivity as a defensive allocator but fails it as a robust absolute-CAGR winner over 60/40. Keep the model frozen and retain the narrower defensive positioning claim.

## Robustness Validation — Initial-Capital Drawdown Accounting

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Finding and correction
The maximum-drawdown function previously started its running peak at the first observed cumulative wealth value instead of the initial capital value of 1.0. A sample beginning with a negative month could therefore omit that initial loss from drawdown. The running peak now has a floor of 1.0, and bootstrap drawdowns use the same convention.

### Impact
The full-period AlphaCore maximum drawdown remains unchanged at -14.91%. The correction affects only samples whose early decline is deeper than their later peak-to-trough drawdown; for example, the 60/40 maximum drawdown in the 2008 start-date sample changes from -29.69% to -30.74%. The conclusions of prior validations remain unchanged.

## Robustness Validation — Moving-Block Bootstrap

**Date:** 2026-08-29
**Model:** AlphaCore v1.3b Corrected Cross-Sectional Ranking

### Objective
Estimate uncertainty around AlphaCore and 60/40 performance using 5,000 paired circular moving-block bootstrap samples. Twelve-month blocks preserve short-run serial dependence, and AlphaCore, 60/40, and risk-free returns are resampled together. The random seed is fixed at 42 for reproducibility.

### Results

| Metric | Observed | Bootstrap 95% interval | Probability of positive AlphaCore spread |
|---|---:|---:|---:|
| AlphaCore CAGR | 8.40% | 4.67% to 12.21% | — |
| CAGR spread vs 60/40 | +0.31 pp | -3.14 pp to +4.77 pp | 53.88% |
| AlphaCore Sharpe | 0.818 | 0.393 to 1.273 | — |
| Sharpe spread vs 60/40 | +0.141 | -0.274 to +0.590 | 70.92% |
| Drawdown improvement vs 60/40 | +17.40 pp | -4.98 pp to +30.97 pp | 88.78% |

The bootstrap AlphaCore maximum-drawdown interval is -25.54% to -8.59%, compared with -45.82% to -11.49% for 60/40.

### Interpretation
AlphaCore's positive full-period CAGR spread over 60/40 is statistically weak and close to a coin flip under block resampling. The Sharpe and drawdown advantages are more persistent, especially drawdown control, but their 95% relative intervals still cross zero. This supports a defensive-allocation hypothesis rather than a proven alpha claim.

### Limitations
The bootstrap reuses the same historical observations, assumes the return-generating process is sufficiently stable, and can rearrange economic regimes. It is an uncertainty analysis, not a true out-of-sample test or proof of future performance.

### Decision
AlphaCore v1.3b passes bootstrap validation only for the narrower claim of probable defensive benefit. It does not demonstrate statistically reliable CAGR or risk-adjusted outperformance over 60/40. Keep the model frozen.

## AlphaCore v1.3b — Final Robustness Gate

**Date:** 2026-08-29

The completed robustness evidence has been consolidated into `reports/backtests/alphacore_v1_robustness_validation.md` and `reports/backtests/alphacore_v1_robustness_scorecard.csv`.

### Final decision
- Conditional GO for controlled monthly paper trading
- NO-GO for further historical parameter optimization
- NO-GO for individual-stock expansion
- NO-GO for real-money deployment

The approved research claim is limited to a defensive tactical allocation profile with historically stable own returns and materially lower drawdowns. Robust absolute or statistically reliable outperformance over 60/40 has not been demonstrated.

## Paper-Trading Operational Gate

**Date:** 2026-08-29

### Implemented safeguards
- Monthly price processing excludes the incomplete current calendar month.
- A paper decision requires prices, signals, and target weights through the last completed month.
- A paper decision must be generated within seven calendar days after month-end, preventing retrospective live records.
- Each validated decision is written to its own immutable month directory.
- The snapshot records model version, regime, signal lag, target weights, turnover, and estimated transaction cost.
- Duplicate decisions for the same month are rejected.

### Current dry-gate result
On 2026-08-29 the most recently completed month is 2026-07-31, while local processed prices and target weights end at 2026-05-31. The generator correctly refused to create a paper-trading decision, and no snapshot was written.

### Decision
Operational scaffolding is ready, but a July 2026 decision would now be retrospective and is therefore ineligible even after a data refresh. The first eligible live snapshot is the August 2026 decision generated during the first seven days of September, after data is refreshed through August and the full feature, signal, and portfolio pipeline completes successfully. Historical validation artifacts must remain distinguishable from subsequent live paper observations.
