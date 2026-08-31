# Final validation sequence

1. Source compilation.
2. Smoke execution.
3. Full pytest regression with coverage.
4. Ruff engineering-surface validation.
5. Workflow YAML validation.

Market-data policy: historical inputs must pass timestamp/order/uniqueness gates. Live Level-2 remains opt-in and requires an explicitly registered real provider; synthetic Level-2 data is prohibited.
