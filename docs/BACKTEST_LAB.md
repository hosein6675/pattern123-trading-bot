# Backtest Lab

## Purpose

The Backtest Lab evaluates the existing strategy independently from optional CME / Level 2 / Delta data. It is designed for controlled A/B testing rather than assuming that additional market data improves a strategy.

## Modes

- `baseline`: Pattern123/Price Action logic without Order Flow inputs.
- `observe`: collect and inspect Order Flow data without allowing it to influence decisions.
- `order_flow`: explicitly opt in to Order Flow inputs for an A/B experiment.

## Required comparisons

For a valid experiment, use the same historical period, symbols, timeframe, execution assumptions, fees/spread model, and strategy configuration for both baseline and order-flow runs. Only the Order Flow input should change.

Compare at minimum:

- trade count
- win rate
- net P&L
- maximum drawdown
- expectancy / profit factor when implemented
- out-of-sample performance

No result should be promoted to production solely because of a higher win rate. The experiment must be reproducible and evaluated on unseen data before an Order Flow feature can influence live decisions.
