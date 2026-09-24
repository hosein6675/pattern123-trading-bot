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
