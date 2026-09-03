# Stage 1 — Money Management + Live Broker

## Scope

This stage combines two planned workstreams:

1. execution-facing money management;
2. the live broker boundary.

## Money management

The `MoneyManagement` policy now sits between the trading engine and order execution. It reuses `RiskManager` and requires explicit:

- account balance/equity;
- entry and stop-loss;
- requested volume;
- setup quality;
- open-position count;
- current total portfolio risk;
- broker risk-per-lot and volume constraints.

The policy rejects a requested size above the risk-approved position size instead of silently increasing risk.

Daily drawdown is checked against both registered realized losses and current equity relative to the start-of-day balance. Account drawdown uses the observed peak account value maintained by the risk manager.

## Live broker

MetaTrader 5 remains the real live adapter. No live market or order data is fabricated.

Live mode now requires both:

```text
TRADING_MODE=live
LIVE_TRADING_ENABLED=true
```

If `TRADING_MODE=live` but the explicit enable flag is false, the system uses a fail-closed disabled broker and cannot place live orders.

The `/trade/test` endpoint is demo-only and is explicitly blocked in live mode. `/broker/status` exposes connectivity state without placing an order.

Credentials remain environment-only. The MT5 package/terminal is intentionally not part of the default CI/runtime dependency set because the live adapter requires a real MT5-capable host.

## Safety boundary

The live broker is an execution adapter, not a strategy. Strategy approval and money-management checks remain upstream. A broker error is returned as a failure; it is never converted into a simulated success.
