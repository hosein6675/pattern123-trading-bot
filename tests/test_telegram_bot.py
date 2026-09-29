from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.telegram_bot import TelegramBot


def test_telegram_application_builds_and_registers_handlers():
    bot = TelegramBot("123456:TEST_TOKEN")
    application = bot.build()

    assert application is bot.application
    assert len(application.handlers.get(0, [])) == 2


@pytest.mark.asyncio
async def test_start_handler_sends_main_menu():
    bot = TelegramBot("123456:TEST_TOKEN")
    bot.build()

    update = MagicMock()
    update.effective_user.id = 42
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await bot.start(update, context)

    update.message.reply_text.assert_awaited_once()
    call = update.message.reply_text.await_args
    assert "Pattern 123" in call.args[0]
    assert call.kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_analysis_without_engine_fails_closed():
    bot = TelegramBot("123456:TEST_TOKEN")
    bot.build()

    selection = bot._selection(42)
    text = await bot._analysis_text(selection)

    assert "موتور تحلیل" in text
    assert "نتیجه واقعی بدون داده بازار ساخته نمی‌شود" in text


def test_workflow_starts_at_symbol_and_exposes_gated_stages():
    bot = TelegramBot("123456:TEST_TOKEN")
    selection = bot._selection(42)
    assert selection.workflow_stage == "SYMBOL"
    markup = bot.workflow_menu(selection)
    callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
    assert "wf:symbols" in callbacks
    assert "wf:timeframes" in callbacks
    assert "wf:analyze" in callbacks
    assert "wf:trigger" in callbacks
    assert "wf:execution" in callbacks
    assert "wf:journal" in callbacks


def test_main_menu_exposes_mt5_live_status():
    bot = TelegramBot("123456:TEST_TOKEN")
    callbacks = [
        button.callback_data
        for row in bot.main_menu().inline_keyboard
        for button in row
    ]
    assert "mt5_status" in callbacks


def test_mt5_status_is_fail_closed_without_live_snapshot():
    bot = TelegramBot("123456:TEST_TOKEN")
    selection = bot._selection(42)
    text = bot._mt5_status_text(selection)
    assert "MT5" in text
    assert "unavailable" in text


def test_workflow_keeps_results_per_symbol():
    bot = TelegramBot("123456:TEST_TOKEN")
    selection = bot._selection(42)
    selection.results_by_symbol["EURUSD"] = {"status": "analysis_complete"}
    selection.results_by_symbol["XAUUSD"] = {"status": "analysis_complete"}
    assert set(selection.results_by_symbol) == {"EURUSD", "XAUUSD"}
    selection.reset_workflow()
    assert selection.results_by_symbol == {}


def test_execution_and_journal_are_locked_before_analysis():
    bot = TelegramBot("123456:TEST_TOKEN")
    selection = bot._selection(42)
    assert "قفل" in bot._execution_text(selection)
    assert "تحلیل" in bot._journal_text(selection) or "lifecycle" in bot._journal_text(selection)
