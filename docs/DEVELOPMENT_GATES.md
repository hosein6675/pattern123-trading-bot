# Development Gates

## Rule

No production change should be merged into `main` without automated validation.

## Required sequence

1. Design and document the change.
2. Implement on a feature/fix/chore branch.
3. Run Python compilation checks.
4. Run the TradingEngine smoke test.
5. Run the test suite when test files are present.
6. Review the diff for security, regression, and strategy-logic impact.
7. Merge only after the pull request checks pass.

## AI review protocol

AI assistants are reviewers and implementation aids, not sources of truth. Conflicting AI recommendations must be resolved against repository code, tests, explicit project requirements, and reproducible evidence.

Every non-trivial change should record:

- the intended behavior;
- affected modules;
- validation performed;
- known limitations or unresolved risks.

## Trading safety

The CI pipeline must never be treated as proof that a trading strategy is profitable. Backtests, forward tests, broker behavior, execution quality, and risk controls require separate validation.
