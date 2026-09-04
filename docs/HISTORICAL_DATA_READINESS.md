# Historical data readiness

The validation lab can now consume a strict, real historical OHLC CSV contract.

Required columns:

- `timestamp` — ISO-8601 timestamp with an explicit timezone/offset
- `open`
- `high`
- `low`
- `close`
- optional `volume`

The loader rejects malformed values, naive timestamps, non-positive/non-finite prices, impossible OHLC ranges, negative/non-finite volume, duplicate timestamps, and non-chronological rows.

No market data is bundled or fabricated by the repository. To produce actual strategy-performance evidence, supply a real dataset from a trusted provider and preserve its provenance, symbol, timeframe, timezone, and collection range outside the codebase.

This stage intentionally stops at the data boundary. It does not manufacture trade outcomes from OHLC alone and does not claim profitability.
