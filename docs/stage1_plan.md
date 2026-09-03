# Stage 1 — Money Management + Live Broker

This stage hardens the execution boundary without enabling live trading by default.

Scope:
- deterministic risk and position sizing
- broker-contract-aware lot normalization
- daily/account drawdown and loss-streak guardrails
- fail-closed MT5 live adapter
- broker-aware live trade preparation and directional execution
- explicit live-mode safety checks
- unit coverage with fake brokers; no real broker credentials or network connection in CI

Stage 2 will cover the trading dashboard plus final strategy/pattern/trendline-fan/MACD integration.
