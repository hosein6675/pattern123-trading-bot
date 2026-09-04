# Historical validation runner

`backtest.historical_validation` is the integration boundary between a real OHLC CSV and the research-grade validation lab.

## Flow

1. Load a provider-supplied CSV through the strict OHLC loader.
2. Require explicit `symbol`, `timeframe`, `start`, and `end` metadata.
3. Apply the requested `[start, end)` window without modifying source observations.
4. Convert validated candles into immutable `BacktestSnapshot` inputs.
5. Run the existing chronological walk-forward validation lab.
6. Require an explicit `OutcomeExtractor`; the runner never infers trade outcomes from OHLC data.
7. Require explicit execution costs and pass them into the validation lab.

This integration does not bundle market data, invent trade outcomes, connect to a broker, or claim profitability. Actual performance evidence still requires a real historical dataset with preserved provenance.
