# Order Flow / CME / Level 2 Experiment Protocol

Order-flow intelligence is an optional, isolated information domain.

## Operating modes

1. **OFF** — no CME/Level 2/Delta data is consumed.
2. **OBSERVE** — collect and display data, but it cannot affect Pattern123 decisions.
3. **BACKTEST** — compare the baseline strategy against a variant that consumes order-flow features.
4. **OPT-IN** — only after explicit validation may a future integration expose the features to a strategy consumer.

The default is **OFF**.

## Required backtest comparison

Every experiment should report at least:

- Pattern123 baseline without order flow
- Pattern123 + selected order-flow features
- same symbols, periods, sessions, costs, and execution assumptions
- aligned timestamps and provider provenance
- no look-ahead or future-data leakage
- sample size and out-of-sample results
- drawdown, expectancy, win rate, profit factor, and trade count

A positive result does not automatically justify production use. A negative result should leave the baseline strategy unchanged.

## Data-quality rule

CME/Level 2/Delta data must never be silently substituted with OHLC, tick volume, or synthetic values. Missing, delayed, malformed, or unverified provider data must be marked unavailable and excluded from any order-flow-dependent conclusion.

## Architectural rule

The order-flow layer must not import or call Pattern123 strategy, price-action, MACD, risk, or execution decision modules. Strategy integration, if ever approved, must happen through an explicit adapter/interface after backtesting.
