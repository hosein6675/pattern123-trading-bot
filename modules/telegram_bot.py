from __future__ import annotations

from dataclasses import replace

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from modules.config import active_config
from modules.multi_timeframe_analysis import analyze as analyze_multi_timeframe
from modules.telegram_controls import (
    ANALYSIS_TIMEFRAMES,
    STRUCTURE_TIMEFRAMES,
    TRIGGER_TIMEFRAMES,
    TelegramSelection,
    analysis_view_from_result,
    render_analysis,
)
from modules.telegram_permissions import TelegramPermissionManager
from modules.trading_engine import TradingEngine

SYMBOLS = tuple(sorted(active_config.allowed_symbols))


class TelegramBot:
    """Telegram control surface with an explicit authorization boundary."""

    def __init__(self, token: str, engine: TradingEngine | None = None, permissions: TelegramPermissionManager | None = None):
        self.token = token
        self.application = None
        self.engine = engine
        self.permissions = permissions or TelegramPermissionManager()
        self._selections: dict[int, TelegramSelection] = {}

    def _selection(self, user_id: int) -> TelegramSelection:
        if user_id not in self._selections:
            self._selections[user_id] = TelegramSelection(symbols={active_config.symbol})
        return self._selections[user_id]

    def _is_allowed(self, user_id: int, capability: str) -> bool:
        return self.permissions.allowed(user_id, capability)

    @staticmethod
    def _button(label: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(label, callback_data=callback)

    def main_menu(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [self._button("📊 وضعیت و انتخاب‌ها", "status")],
            [self._button("🪙 نمادها", "symbols"), self._button("⏱ تایم‌فریم‌ها", "timeframes")],
            [self._button("📈 اجرای تحلیل", "analysis")],
            [self._button("📰 اخبار", "news"), self._button("💰 حساب", "account")],
            [self._button("🔐 دسترسی من", "permissions"), self._button("⚙️ تنظیمات", "settings")],
        ])

    def symbol_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        rows = []
        for symbol in SYMBOLS:
            marker = "✅" if symbol in selection.symbols else "▫️"
            rows.append([self._button(f"{marker} {symbol}", f"sym:{symbol}")])
        rows += [
            [self._button("🔄 انتخاب همه", "sym:all")],
            [self._button("🧹 پاک کردن انتخاب‌ها", "sym:none")],
            [self._button("⬅️ منوی اصلی", "home")],
        ]
        return InlineKeyboardMarkup(rows)

    def timeframe_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [self._button("🏗 تایم ساختار: D1 / H4 / H1", "tf:structure")],
            [self._button(f"D1 {'✅' if selection.structure_timeframe == 'D1' else '▫️'}", "tf:s:D1"), self._button(f"H4 {'✅' if selection.structure_timeframe == 'H4' else '▫️'}", "tf:s:H4"), self._button(f"H1 {'✅' if selection.structure_timeframe == 'H1' else '▫️'}", "tf:s:H1")],
            [self._button("🔎 تایم تحلیل: H1 / M15 / M5 / M1", "tf:analysis")],
            [self._button(f"H1 {'✅' if selection.analysis_timeframe == 'H1' else '▫️'}", "tf:a:H1"), self._button(f"M15 {'✅' if selection.analysis_timeframe == 'M15' else '▫️'}", "tf:a:M15")],
            [self._button(f"M5 {'✅' if selection.analysis_timeframe == 'M5' else '▫️'}", "tf:a:M5"), self._button(f"M1 {'✅' if selection.analysis_timeframe == 'M1' else '▫️'}", "tf:a:M1")],
            [self._button("🎯 تایم تریگر: M15 / M5 / M1", "tf:trigger")],
            [self._button(f"M15 {'✅' if selection.trigger_timeframe == 'M15' else '▫️'}", "tf:t:M15"), self._button(f"M5 {'✅' if selection.trigger_timeframe == 'M5' else '▫️'}", "tf:t:M5"), self._button(f"M1 {'✅' if selection.trigger_timeframe == 'M1' else '▫️'}", "tf:t:M1")],
            [self._button("⬅️ منوی اصلی", "home")],
        ])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else 0
        self._selection(user_id)
        await update.message.reply_text(
            "🤖 Pattern 123\n\nنمادها و سه لایه زمانی را انتخاب کنید؛ سپس اجرای تحلیل را بزنید.",
            reply_markup=self.main_menu(),
        )

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id if update.effective_user else 0
        selection = self._selection(user_id)
        data = query.data or ""

        if data in {"home", "status"}:
            text, markup = self._status_text(selection), self.main_menu()
        elif data == "permissions":
            text, markup = self._permissions_text(user_id), self.main_menu()
        elif data == "symbols":
            text, markup = self._symbols_text(selection), self.symbol_menu(selection)
        elif data.startswith("sym:"):
            value = data.split(":", 1)[1]
            if value == "all":
                selection.set_symbols(list(SYMBOLS), set(SYMBOLS))
            elif value == "none":
                await query.edit_message_text("⚠️ حداقل یک نماد باید انتخاب شود.", reply_markup=self.symbol_menu(selection))
                return
            else:
                selection.toggle_symbol(value, set(SYMBOLS))
                if not selection.symbols:
                    selection.symbols.add(value)
            text, markup = self._symbols_text(selection), self.symbol_menu(selection)
        elif data in {"timeframes", "tf:structure", "tf:analysis", "tf:trigger"}:
            text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data.startswith("tf:s:"):
            selection.set_structure_timeframe(data.rsplit(":", 1)[1])
            text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data.startswith("tf:a:"):
            selection.set_analysis_timeframe(data.rsplit(":", 1)[1])
            text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data.startswith("tf:t:"):
            selection.set_trigger_timeframe(data.rsplit(":", 1)[1])
            text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data == "analysis":
            if not self._is_allowed(user_id, "can_analyze"):
                text, markup = "⛔ دسترسی اجرای تحلیل برای این کاربر فعال نیست.", self.main_menu()
            else:
                text, markup = await self._analysis_text(selection), self.main_menu()
        elif data == "news":
            enabled = bool(getattr(active_config, "trade_news", False))
            text, markup = f"📰 فیلتر خبر: {'فعال' if enabled else 'غیرفعال'}", self.main_menu()
        elif data == "account":
            text, markup = self._account_text(), self.main_menu()
        elif data == "settings":
            text, markup = self._settings_text(), self.main_menu()
        else:
            text, markup = "دستور ناشناخته است.", self.main_menu()
        await query.edit_message_text(text, reply_markup=markup)

    def _status_text(self, selection: TelegramSelection) -> str:
        return (
            "📊 وضعیت انتخاب‌ها\n\n"
            f"🪙 نمادها: {', '.join(sorted(selection.symbols))}\n"
            f"🏗 تایم ساختار: {selection.structure_timeframe}\n"
            f"🔎 تایم تحلیل: {selection.analysis_timeframe}\n"
            f"🎯 تایم تریگر: {selection.trigger_timeframe}\n"
            f"⚙️ حالت: {active_config.mode}"
        )

    def _permissions_text(self, user_id: int) -> str:
        profile = self.permissions.profile_for(user_id)
        yes_no = lambda value: "فعال" if value else "قفل"
        return (
            "🔐 دسترسی Telegram\n\n"
            f"نقش: {profile.role.value}\n"
            f"مشاهده: {yes_no(profile.can_view)}\n"
            f"تحلیل: {yes_no(profile.can_analyze)}\n"
            f"معامله: {yes_no(profile.can_trade)}\n"
            f"مدیریت سیستم: {yes_no(profile.can_manage_system)}\n"
            f"مدیریت Distribution: {yes_no(profile.can_manage_distribution)}\n"
            f"داده حساس: {yes_no(profile.can_view_sensitive)}"
        )

    def _symbols_text(self, selection: TelegramSelection) -> str:
        return "🪙 انتخاب نماد\n\n" + "\n".join(
            f"{'✅' if symbol in selection.symbols else '▫️'} {symbol}" for symbol in SYMBOLS
        ) + "\n\nامکان انتخاب هم‌زمان چند نماد فعال است."

    def _timeframe_text(self, selection: TelegramSelection) -> str:
        return (
            "⏱ ساختار تایم‌فریم‌ها\n\n"
            f"🏗 ساختار: {selection.structure_timeframe}  |  گزینه‌ها: {', '.join(STRUCTURE_TIMEFRAMES)}\n"
            f"🔎 تحلیل: {selection.analysis_timeframe}  |  گزینه‌ها: {', '.join(ANALYSIS_TIMEFRAMES)}\n"
            f"🎯 تریگر: {selection.trigger_timeframe}  |  گزینه‌ها: {', '.join(TRIGGER_TIMEFRAMES)}"
        )

    def _account_text(self) -> str:
        return (
            "💰 حساب\n\n"
            f"حالت: {active_config.mode}\n"
            f"نماد پیش‌فرض: {active_config.symbol}\n"
            f"Live trading: {'فعال' if active_config.live_trading_enabled else 'قفل'}"
        )

    def _settings_text(self) -> str:
        return (
            "⚙️ تنظیمات\n\n"
            f"Market: {active_config.market}\n"
            f"Default symbol: {active_config.symbol}\n"
            f"Default timeframe: {active_config.timeframe}\n"
            f"Allowed symbols: {len(active_config.allowed_symbols)}\n"
            "اجرای Live مستقل از این رابط و همچنان fail-closed است."
        )

    async def _analysis_text(self, selection: TelegramSelection) -> str:
        if self.engine is None:
            return "📈 موتور تحلیل به تلگرام متصل نشده است؛ نتیجه واقعی بدون داده بازار ساخته نمی‌شود."
        reports: list[str] = []
        for symbol in sorted(selection.symbols):
            try:
                multi = analyze_multi_timeframe(self.engine, symbol, selection)
                layers = (("🏗 ساختار", multi.structure, selection.structure_timeframe), ("🔎 تحلیل", multi.analysis, selection.analysis_timeframe), ("🎯 تریگر", multi.trigger, selection.trigger_timeframe))
                layer_reports: list[str] = []
                for label, result, timeframe in layers:
                    view = analysis_view_from_result(result, symbol=symbol, selection=selection)
                    view = replace(view, structure_timeframe=timeframe, analysis_timeframe=timeframe, trigger_timeframe=timeframe)
                    layer_reports.append(f"{label}\n{render_analysis(view)}")
                if multi.warnings:
                    layer_reports.append("⚠️ وضعیت چندتایم‌فریمی\n" + "\n".join(f"• {item}" for item in multi.warnings))
                reports.append("\n\n━━━━━━━━━━━━━━\n\n".join(layer_reports))
            except Exception as exc:
                reports.append(f"📈 {symbol}\n\n❌ تحلیل اجرا نشد.\nخطای فنی: {type(exc).__name__}")
        return "\n\n════════════════════\n\n".join(reports)

    def build(self):
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button))
        return self.application


__all__ = ["TelegramBot", "SYMBOLS", "STRUCTURE_TIMEFRAMES", "ANALYSIS_TIMEFRAMES", "TRIGGER_TIMEFRAMES"]
