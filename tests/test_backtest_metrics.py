from math import inf

import pytest

from backtest.metrics import max_drawdown, profit_factor, win_rate


def test_win_rate():
    assert win_rate([2, -1, 3, 0]) == pytest.approx(0.5)
    assert win_rate([]) == 0.0


def test_profit_factor():
    assert profit_factor([2, -1, 3, -2]) == pytest.approx(5 / 3)
    assert profit_factor([1, 2]) == inf
    assert profit_factor([]) == 0.0


def test_max_drawdown():
    assert max_drawdown([5, -2, -4, 3]) == pytest.approx(6)
    assert max_drawdown([]) == 0.0
