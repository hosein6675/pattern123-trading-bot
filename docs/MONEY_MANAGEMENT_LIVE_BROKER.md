# Stage 1 — Money Management + Live Broker

## Money management

The execution path now has explicit guardrails:

- risk per trade, default 1%
- quality-adjusted risk capped by configuration
- broker-aware cash risk per lot when supported
- daily loss/drawdown limit, default 5%
- maximum account drawdown, default 20%
- maximum open positions, default 5
- maximum total portfolio risk, default 3%
- maximum consecutive losses, default 3
- broker min/max/step volume normalization
- mandatory stop-loss and take-profit for execution
- stop-loss/take-profit direction validation

A requested order is rejected when its volume exceeds the risk-approved size.

## Live broker boundary

`TRADING_MODE=demo` is the default and is deterministic.

`TRADING_MODE=live` selects the optional `MT5Broker` adapter. The adapter lazily imports the MetaTrader5 Python package and requires a reachable MetaTrader 5 terminal plus environment configuration:

- `MT5_LOGIN`
- `MT5_PASSWORD`
- `MT5_SERVER`
- `MT5_TERMINAL_PATH` (when needed)

The adapter supplies account/equity, positions, live tick price, broker contract limits, live OHLC candles, broker-calculated one-lot stop loss, and order open/close operations.

If the SDK, terminal, account, symbol, or order is unavailable, the operation fails. No live result is simulated.

## Deployment note

The MetaTrader 5 Python integration requires a host where the MT5 terminal can actually run and be reached by the Python process. A generic Linux web service cannot be treated as a connected MT5 terminal merely because environment variables are present. Use a Windows/VPS/bridge deployment appropriate for the broker.

Never commit real broker credentials. Store them in the deployment environment.
