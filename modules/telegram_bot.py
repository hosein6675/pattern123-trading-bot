from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from modules.config import active_config
from modules.multi_timeframe_analysis import MultiTimeframeAnalysis, analyze as analyze_multi_timeframe
from modules.telegram_controls import ANALYSIS_TIMEFRAMES, STRUCTURE_TIMEFRAMES, TRIGGER_TIMEFRAMES, TelegramSelection
from modules.trading_engine import TradingEngine

SYMBOLS = tuple(sorted(active_config.allowed_symbols))


class TelegramBot:
    """Telegram control surface for multi-symbol, multi-timeframe analysis."""

    def __init__(self, token: str, engine: TradingEngine | None = None):
        self.token = token
        self.application = None
        self.engine = engine
        self._selections: dict[int, TelegramSelection] = {}

    def _selection(self, user_id: int) -> TelegramSelection:
        if user_id not in self._selections:
            self._selections[user_id] = TelegramSelection(symbols={active_config.symbol})
        return self._selections[user_id]

    @staticmethod
    def _button(label: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(label, callback_data=callback)

    def main_menu(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [self._button("📊 وضعیت و انتخاب‌ها", "status")],
            [self._button("🪙 نمادها", "symbols"), self._button("⏱ تایم‌فریم‌ها", "timeframes")],
            [self._button("📈 اجرای تحلیل چندتایم‌فریمی", "analysis")],
            [self._button("📰 اخبار", "news"), self._button("💰 حساب", "account")],
            [self._button("⚙️ تنظیمات", "settings")],
        ])

    def symbol_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        rows = [[self._button(f"{'✅' if symbol in selection.symbols else '▫️'} {symbol}", f"sym:{symbol}")] for symbol in SYMBOLS]
        rows += [[self._button("🔄 انتخاب همه", "sym:all")], [self._button("🧹 پاک کردن انتخاب‌ها", "sym:none")], [self._button("⬅️ منوی اصلی", "home")]]
        return InlineKeyboardMarkup(rows)

    def timeframe_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [self._button("🏗 تایم ساختار", "tf:structure")],
            [self._button(f"D1 {'✅' if selection.structure_timeframe == 'D1' else '▫️'}", "tf:s:D1"), self._button(f"H4 {'✅' if selection.structure_timeframe == 'H4' else '▫️'}", "tf:s:H4"), self._button(f"H1 {'✅' if selection.structure_timeframe == 'H1' else '▫️'}", "tf:s:H1")],
            [self._button("🔎 تایم تحلیل", "tf:analysis")],
            [self._button(f"H1 {'✅' if selection.analysis_timeframe == 'H1' else '▫️'}", "tf:a:H1"), self._button(f"M15 {'✅' if selection.analysis_timeframe == 'M15' else '▫️'}", "tf:a:M15")],
            [self._button(f"M5 {'✅' if selection.analysis_timeframe == 'M5' else '▫️'}", "tf:a:M5"), self._button(f"M1 {'✅' if selection.analysis_timeframe == 'M1' else '▫️'}", "tf:a:M1")],
            [self._button("🎯 تایم تریگر", "tf:trigger")],
            [self._button(f"M15 {'✅' if selection.trigger_timeframe == 'M15' else '▫️'}", "tf:t:M15"), self._button(f"M5 {'✅' if selection.trigger_timeframe == 'M5' else '▫️'}", "tf:t:M5"), self._button(f"M1 {'✅' if selection.trigger_timeframe == 'M1' else '▫️'}", "tf:t:M1")],
            [self._button("⬅️ منوی اصلی", "home")],
        ])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else 0
        self._selection(user_id)
        await update.message.reply_text("🤖 Pattern 123\n\nنمادها و سه لایه زمانی را انتخاب کنید؛ سپس تحلیل چندتایم‌فریمی را اجرا کنید.", reply_markup=self.main_menu())

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id if update.effective_user else 0
        selection = self._selection(user_id)
        data = query.data or ""
        if data in {"home", "status"}:
            text, markup = self._status_text(selection), self.main_menu()
        elif data == "symbols":
            text, markup = self._symbols_text(selection), self.symbol_menu(selection)
        elif data.startswith("sym:"):
            value = data.split(":", 1)[1]
            if value == "all":
                selection.set_symbols(list(SYMBOLS), set(SYMBOLS))
            elif value == "none":
                await query.edit_message_text("⚠️ حداقل یک نماد باید انتخاب شود.", reply_markup=self.symbol_menu(selection)); return
            else:
                selection.toggle_symbol(value, set(SYMBOLS))
                if not selection.symbols: selection.symbols.add(value)
            text, markup = self._symbols_text(selection), self.symbol_menu(selection)
        elif data in {"timeframes", "tf:structure", "tf:analysis", "tf:trigger"}:
            text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data.startswith("tf:s:"):
            selection.set_structure_timeframe(data.rsplit(":", 1)[1]); text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data.startswith("tf:a:"):
            selection.set_analysis_timeframe(data.rsplit(":", 1)[1]); text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data.startswith("tf:t:"):
            selection.set_trigger_timeframe(data.rsplit(":", 1)[1]); text, markup = self._timeframe_text(selection), self.timeframe_menu(selection)
        elif data == "analysis":
            text, markup = await self._analysis_text(selection), self.main_menu()
        elif data == "news":
            enabled = bool(getattr(active_config, "trade_news", False)); text, markup = f"📰 فیلتر خبر: {'فعال' if enabled else 'غیرفعال'}", self.main_menu()
        elif data == "account":
            text, markup = self._account_text(), self.main_menu()
        elif data == "settings":
            text, markup = self._settings_text(), self.main_menu()
        else:
            text, markup = "دستور ناشناخته است.", self.main_menu()
        await query.edit_message_text(text, reply_markup=markup)

    def _status_text(self, selection: TelegramSelection) -> str:
        return ("📊 وضعیت انتخاب‌ها\n\n" f"🪙 نمادها: {', '.join(sorted(selection.symbols))}\n" f"🏗 تایم ساختار: {selection.structure_timeframe}\n" f"🔎 تایم تحلیل: {selection.analysis_timeframe}\n" f"🎯 تایم تریگر: {selection.trigger_timeframe}\n" f"⚙️ حالت: {active_config.mode}")

    def _symbols_text(self, selection: TelegramSelection) -> str:
        return "🪙 انتخاب نماد\n\n" + "\n".join(f"{'✅' if symbol in selection.symbols else '▫️'} {symbol}" for symbol in SYMBOLS) + "\n\nانتخاب هم‌زمان چند نماد فعال است."

    def _timeframe_text(self, selection: TelegramSelection) -> str:
        return ("⏱ تنظیم سه‌لایه زمانی\n\n" f"🏗 ساختار: {selection.structure_timeframe} | {', '.join(STRUCTURE_TIMEFRAMES)}\n" f"🔎 تحلیل: {selection.analysis_timeframe} | {', '.join(ANALYSIS_TIMEFRAMES)}\n" f"🎯 تریگر: {selection.trigger_timeframe} | {', '.join(TRIGGER_TIMEFRAMES)}")

    def _account_text(self) -> str:
        return ("💰 حساب\n\n" f"حالت: {active_config.mode}\n" f"نماد پیش‌فرض: {active_config.symbol}\n" f"Live trading: {'فعال' if active_config.live_trading_enabled else 'قفل'}")

    def _settings_text(self) -> str:
        return ("⚙️ تنظیمات\n\n" f"Market: {active_config.market}\n" f"Default symbol: {active_config.symbol}\n" f"Default timeframe: {active_config.timeframe}\n" f"Allowed symbols: {len(active_config.allowed_symbols)}\n" "اجرای Live مستقل از این رابط و همچنان fail-closed است.")

    @staticmethod
    def _value(result: object, name: str, default: object = "unknown") -> object:
        return result.get(name, default) if isinstance(result, dict) else getattr(result, name, default)

    def _layer_summary(self, title: str, timeframe: str, result: object) -> str:
        structure = self._value(self._value(result, "structure", None), "trend", self._value(self._value(result, "market_context", None), "structure", "unknown"))
        trendline = self._value(self._value(result, "trendline_fan", None), "direction", "unknown")
        context = self._value(result, "market_context", None); price_action = self._value(result, "price_action", None)
        zone = self._value(context, "fib_zone", self._value(price_action, "zone", "unknown"))
        authenticity = self._value(context, "zone_authenticity", self._value(price_action, "zone_authenticity", "unknown"))
        position = self._value(context, "price_position", self._value(price_action, "price_position", "unknown"))
        macd = self._value(self._value(result, "macd", None), "direction", "unknown")
        decision = self._value(self._value(result, "decision", None), "decision", self._value(result, "decision", "NO_TRADE"))
        return (f"{title} [{timeframe}]\n" f"• وضعیت داده: {self._value(result, 'status')}\n" f"• ساختار: {structure}\n" f"• خط روند: {trendline}\n" f"• منطقه قیمت: {zone}\n" f"• اصالت منطقه: {authenticity}\n" f"• موقعیت قیمت: {position}\n" f"• MACD: {macd}\n" f"• تصمیم: {decision}")

    async def _analysis_text(self, selection: TelegramSelection) -> str:
        if self.engine is None:
            return "📈 موتور تحلیل به تلگرام متصل نشده است؛ نتیجه واقعی بدون داده بازار ساخته نمی‌شود."
        reports = []
        for symbol in sorted(selection.symbols):
            try:
                report: MultiTimeframeAnalysis = analyze_multi_timeframe(self.engine, symbol, selection)
                text = (f"📈 تحلیل چندتایم‌فریمی Pattern 123\n\n🪙 {report.symbol}\n" f"🏗 ساختار: {report.structure_timeframe}\n🔎 تحلیل: {report.analysis_timeframe}\n🎯 تریگر: {report.trigger_timeframe}\n" f"📡 وضعیت کلی: {report.status}\n\n" f"{self._layer_summary('🏗 لایه ساختار', report.structure_timeframe, report.structure)}\n\n" f"{self._layer_summary('🔎 لایه تحلیل', report.analysis_timeframe, report.analysis)}\n\n" f"{self._layer_summary('🎯 لایه تریگر', report.trigger_timeframe, report.trigger)}")
                if report.warnings: text += "\n\n⚠️ هشدارها:\n" + "\n".join(f"• {item}" for item in report.warnings)
                reports.append(text)
            except Exception as exc:
                reports.append(f"📈 {symbol}\n\n❌ تحلیل اجرا نشد.\nخطای فنی: {type(exc).__name__}")
        return "\n\n━━━━━━━━━━━━━━\n\n".join(reports)

    def build(self):
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button))
        return self.application


__all__ = ["TelegramBot", "SYMBOLS", "STRUCTURE_TIMEFRAMES", "ANALYSIS_TIMEFRAMES", "TRIGGER_TIMEFRAMES"]
