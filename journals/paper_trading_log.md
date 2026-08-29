# AlphaCore v1.3b Paper-Trading Log

## Operating status

- Model: AlphaCore v1.3b Corrected Cross-Sectional Ranking
- Status: conditional GO for controlled monthly paper trading
- Real-money deployment: prohibited
- Model rules: frozen
- Required history before first operational review: 12 scheduled monthly decisions

No paper-trading decision may be recorded from stale or incomplete monthly data. A decision must be generated within seven calendar days after its month-end; retrospective decisions are rejected. Each generated decision is stored under `reports/paper_trading/decisions/YYYY-MM-DD/` and must remain immutable.

## Monthly review template

### Decision month: YYYY-MM-DD

- Input data current through:
- Generation timestamp:
- Regime:
- Target weights file:
- Monthly turnover:
- Estimated transaction cost:
- Data-quality incidents:
- Manual overrides: none / describe
- Execution deviations: none / describe
- Notes:

## Decision history

No validated live paper-trading decisions recorded yet.
