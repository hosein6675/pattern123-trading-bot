# Final release gate

This stage is the production-hardening boundary. It does not claim that the strategy is profitable and it does not create market evidence.

## What is now enforced

- Execution costs must be explicit, finite, and non-negative.
- CI can never be considered safe when live trading is enabled.
- Production webhook configuration must use a non-placeholder secret.
- A production strategy release requires a real validation result unless the build is explicitly software-only/demo.
- Required validation modes must pass their configured out-of-sample gates.

## Release sequence

1. Run the automated CI suite and keep it green.
2. Supply a real, validated historical dataset; do not use synthetic market data as evidence.
3. Run the validation lab with chronological walk-forward evaluation and broker-appropriate execution costs.
4. Review every required mode's out-of-sample gate and retain the validation artifact/report.
5. Run a demo/forward test with the intended broker/data bridge.
6. Only after the above evidence is accepted should a live environment be configured.

## Important boundary

The repository can be software-complete while empirical strategy validation remains data-dependent. No historical dataset means no honest profitability result. Live trading also requires the user's own broker account, credentials, permissions, and an approved execution environment; CI and this release gate never place real orders.

## Order-flow boundary

Order-flow/Level-2 remains opt-in. The project must use a real provider and point-in-time observations. Synthetic Level-2 data is not acceptable as validation evidence.
