from __future__ import annotations

from telegram import Bot

from modules.config import active_config


class MT5Reporter:
    """Sends broker statement summaries only to explicitly configured Telegram admins."""

    def __init__(self, token: str):
        self.token = token

    async def send(self, text: str) -> int:
        if not self.token or not active_config.telegram_admin_ids:
            return 0
        sent = 0
        async with Bot(self.token) as bot:
            for chat_id in sorted(active_config.telegram_admin_ids):
                await bot.send_message(chat_id=chat_id, text=text[:3900])
                sent += 1
        return sent


__all__ = ["MT5Reporter"]
