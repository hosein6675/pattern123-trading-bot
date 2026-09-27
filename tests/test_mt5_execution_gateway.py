import os
import time

from modules.mt5_execution_gateway import (
    MT5ExecutionGateway,
    sign_command,
    verify_command_signature,
)


def test_signature_round_trip():
    command = {
        "command_id": "abc",
        "symbol": "EURUSD",
        "direction": "buy",
        "volume": 0.01,
        "stop_loss": 1.09,
        "take_profit": 1.12,
        "expires_at": int(time.time()) + 30,
    }
    signature = sign_command("secret", command)
    assert verify_command_signature("secret", command, signature)
    assert not verify_command_signature("wrong", command, signature)


def test_issue_fails_closed_when_live_execution_disabled(monkeypatch):
    monkeypatch.setattr("modules.mt5_execution_gateway.active_config.mode", "live")
    monkeypatch.setattr("modules.mt5_execution_gateway.active_config.live_trading_enabled", False)
    gateway = MT5ExecutionGateway()
    ok, reason, command = gateway.issue("EURUSD", "buy", 0.01, 1.09, 1.12)
    assert not ok
    assert reason == "live_execution_disabled"
    assert command is None


def test_issue_creates_signed_pending_command(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "secret")
    monkeypatch.setattr("modules.mt5_execution_gateway.active_config.mode", "live")
    monkeypatch.setattr("modules.mt5_execution_gateway.active_config.live_trading_enabled", True)
    gateway = MT5ExecutionGateway()
    ok, reason, command = gateway.issue("EURUSD", "buy", 0.01, 1.09, 1.12)
    assert ok
    assert reason == "queued"
    assert command["status"] == "pending"
    assert verify_command_signature("secret", command, command["signature"])
    assert len(gateway.pending("EURUSD")) == 1


def test_result_requires_known_pending_command(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "secret")
    gateway = MT5ExecutionGateway()
    result = {
        "command_id": "missing",
        "status": "executed",
        "order_id": "1",
        "message": "ok",
        "timestamp": int(time.time()),
        "signature": "bad",
    }
    ok, reason = gateway.accept_result(result)
    assert not ok
    assert reason == "invalid_signature"
