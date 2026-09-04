# Strategy validation protocol

This repository treats historical validation as a research gate, not proof of future profitability.

## Required sequence

1. Validate timestamps, ordering, uniqueness, and positive prices before replay.
2. Use immutable point-in-time snapshots.
3. Split observations into chronological train/test windows.
4. Create a fresh strategy instance for each walk-forward window.
5. If a strategy implements `fit(train_snapshots)`, fit only on that window's training data.
6. Evaluate the following test segment without using future observations.
7. Apply only explicit spread, slippage, and commission costs.
8. Report in-sample and out-of-sample metrics separately.
9. Apply an explicit acceptance gate before calling a variant a candidate.

## Metrics

The validation lab reports:

- trade count and win/loss count
- win rate
- net P&L
- gross profit/loss
- profit factor
- expectancy per trade
- maximum drawdown and drawdown percentage when starting equity is supplied
- a deterministic Sharpe-like ratio for relative comparison
- average winning and losing trade

## Comparing strategy variants

The strategy factory explicitly maps a validation mode to a strategy implementation. A `BacktestMode` must not be interpreted as meaning Pattern123, MACD, Trendline Fan, news, or order flow unless the caller deliberately defines that mapping.

Recommended research variants are therefore explicit implementations such as:

- Pattern123 baseline
- Pattern123 + MACD confirmation
- Pattern123 + MACD + Trendline Fan
- Pattern123 + MACD + Trendline Fan + approved contextual filters

The repository does not manufacture Level-2/order-flow observations. A real provider is required for order-flow research.

## Acceptance gate

Default gates are intentionally conservative and configurable. They are not claims that a strategy is profitable. A candidate should normally require sufficient out-of-sample trade count, positive expectancy, profit factor above one, and drawdown within the configured ceiling.

A failed gate is a research result: do not tune the strategy against the same out-of-sample period and call that validation.

## No leakage rule

Training data must precede test data. Strategy fitting is isolated per window. Future news, order-flow, or other contextual observations must not be visible to a snapshot at an earlier timestamp.

## Execution realism

Backtests must supply explicit execution costs. Zero cost is permitted only when deliberately requested for a baseline. Production conclusions should use broker-appropriate costs and, where available, historically observed spread/slippage/commission assumptions.
