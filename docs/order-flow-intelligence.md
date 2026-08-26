# Order Flow Intelligence (optional)

## Purpose

The platform now reserves a dedicated, strategy-independent layer for order-flow intelligence. It is intended to consume real market-data feeds such as CME-derived data and Level-2/DOM data when an appropriate licensed provider is connected.

This layer is deliberately **not** part of Pattern123, price action, MACD, signal scoring, risk, or execution. It is an independent information service that future platform features may query when the user explicitly chooses to use it.

## Planned data domains

- CME market data where licensing and entitlements permit access
- Level-2 / DOM bid and ask depth
- Bid/ask sizes
- Trade volume
- Delta and cumulative delta when supplied or correctly derived from an entitled feed
- Provider timestamps and sequence identifiers

## Data-integrity rules

1. Never fabricate CME or Level-2 values.
2. Every snapshot must identify its provider and instrument.
3. Provider timestamps and source sequence identifiers should be preserved when available.
4. Missing values remain missing; they are not silently replaced with estimates.
5. A feed adapter must validate its output before it enters the platform.
6. Strategy modules must not depend directly on provider-specific APIs.

## Architecture

```text
CME / Level-2 Provider
        |
        v
Provider Adapter
        |
        v
OrderFlowService
        |
        v
OrderFlowSnapshot
        |
        +----> Future Liquidity Analytics
        +----> Future AI Market Assistant
        +----> Future Platform Dashboard

Pattern123 / Price Action / MACD remain separate.
```

## Important implementation boundary

The repository currently contains the provider-neutral contract and service boundary only. A real CME or Level-2 feed must be connected through a provider adapter after the exact vendor, entitlement, instrument mapping, and API/protocol are selected. This prevents the codebase from pretending that public OHLC data is equivalent to exchange-grade Level-2 data.
