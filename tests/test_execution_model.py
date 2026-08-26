from modules.market_intelligence.backtest.execution import ExecutionCosts, ExecutionModel


def test_execution_costs_are_explicit():
    model = ExecutionModel()
    costs = ExecutionCosts(spread=1.5, slippage=0.5, commission=2.0)

    assert costs.total == 4.0
    assert model.net_pnl(25.0, costs) == 21.0


def test_default_model_has_zero_assumed_costs():
    assert ExecutionModel().net_pnl(25.0) == 25.0
