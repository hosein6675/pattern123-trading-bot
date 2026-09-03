# Backtest Lab

## Purpose

The Backtest Lab evaluates the existing strategy independently from optional CME / Level 2 / Delta data. It is designed for controlled A/B testing rather than assuming that additional market data improves a strategy.

## Modes

- `baseline`: Pattern123/Price Action logic without Order Flow inputs.
- `observe`: collect and inspect Order Flow data without allowing it to influence decisions.
- `order_flow`: explicitly opt in to Order Flow inputs for an A/B experiment.

## Historical replay

Historical events are replayed chronologically and deterministically. The replay engine does not manufacture missing ticks, Level 2 records, Delta values, latency, or fills. Provider- and venue-specific replay rules should be added only when reliable historical data is available.

## Data adapters

The replay layer uses a provider-agnostic adapter contract. MT5, CME, Level 2, and future providers can implement the contract independently. Adapters preserve the provider payload and timestamp semantics; they do not translate ordinary OHLC or tick volume into Delta/Level 2 data.

## Execution realism

Historical replay must keep execution assumptions explicit. The execution model supports separate inputs for spread, slippage, and commission. No cost is silently invented. Latency and fill behavior should be added as provider- or venue-specific replay rules once reliable historical data is available.

## Required comparisons

For a valid experiment, use the same historical period, symbols, timeframe, execution assumptions, fees/spread model, and strategy configuration for both baseline and order-flow runs. Only the Order Flow input should change.

Compare at minimum:

- trade count
- win rate
- net P&L after explicit execution costs
- maximum drawdown
- expectancy / profit factor when implemented
- out-of-sample performance

No result should be promoted to production solely because of a higher win rate. The experiment must be reproducible and evaluated on unseen data before an Order Flow feature can influence live decisions.
