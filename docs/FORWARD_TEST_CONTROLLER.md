# Forward Test Controller

The operational demo cycle is bounded by two conditions and ends on the first one reached:

- **100 completed trades**, or
- **30 calendar days** in the test window.

This is intentionally not a 30-day minimum followed by a 100-trade minimum. If market opportunity is high and 100 trades are completed on day 18, the cycle is ready for review on day 18. If the trade target is not reached, the cycle continues until day 30 and is reviewed then.

## Review behavior

At completion the controller freezes an auditable cycle snapshot containing the completion trigger, trade count, elapsed days, sample-quality classification, and any parameter/version changes recorded during the cycle.

A 30-day cycle with fewer than 100 trades is **not** treated as conclusive solely because the calendar window ended. Its sample quality is reported as limited or insufficient, allowing the operator to extend the test or modify the strategy deliberately.

## Parameter changes

Changes during a cycle are allowed, but each change must record:

- date,
- source version,
- destination version,
- reason,
- changed parameters.

This preserves the distinction between pre-change and post-change behavior and prevents silent modification of a test result.

The controller is an orchestration/audit component only. It does not generate market data, infer trade outcomes, or place broker orders. MT5 remains the execution environment for demo trading and its Strategy Tester remains the source of historical backtest results.
