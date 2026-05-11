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