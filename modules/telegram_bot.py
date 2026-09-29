from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from modules.config import active_config
from modules.telegram_controls import (
    ANALYSIS_TIMEFRAMES,
    STRUCTURE_TIMEFRAMES,
    TRIGGER_TIMEFRAMES,
    TelegramSelection,
    analysis_view_from_result,
    render_analysis,
)
from modules.trading_engine import TradingEngine
from modules.mt5_market_gateway import mt5_market_gateway

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
            [self._button("🚀 Workflow Pattern123", "workflow")],
            [self._button("📊 وضعیت و انتخاب‌ها", "status"), self._button("🛰 MT5 Live", "mt5_status")],
            [self._button("🪙 نمادها", "symbols"), self._button("⏱ تایم‌فریم‌ها", "timeframes")],
            [self._button("📈 اجرای تحلیل", "analysis")],
            [self._button("📰 اخبار", "news"), self._button("💰 حساب", "account")],
            [self._button("⚙️ تنظیمات", "settings")],
        ])

    def symbol_menu(self, selection: TelegramSelection, workflow: bool = False) -> InlineKeyboardMarkup:
        rows = []
        for symbol in SYMBOLS:
            marker = "✅" if symbol in selection.symbols else "▫️"
            rows.append([self._button(f"{marker} {symbol}", f"sym:{symbol}")])
        rows += [
            [self._button("🔄 انتخاب همه", "sym:all")],
            [self._button("🧹 پاک کردن انتخاب‌ها", "sym:none")],
            [self._button("➡️ ادامه Workflow", "wf:timeframes")] if workflow
            else [self._button("⬅️ منوی اصلی", "home")],
        ]
        return InlineKeyboardMarkup(rows)

    def timeframe_menu(self, selection: TelegramSelection, workflow: bool = False) -> InlineKeyboardMarkup:
        rows = [[self._button("⏱ تایم‌فریم‌های MT5", "timeframes")]]
        for title, prefix, current in (
            ("🏗 ساختار", "s", selection.structure_timeframe),
            ("🔎 تحلیل", "a", selection.analysis_timeframe),
            ("🎯 تریگر", "t", selection.trigger_timeframe),
        ):
            rows.append([self._button(f"{title}: {current}", "timeframes")])
            options = list(STRUCTURE_TIMEFRAMES)
            for i in range(0, len(options), 3):
                row = []
                for value in options[i:i + 3]:
                    marker = "✅" if value == current else "▫️"
                    row.append(self._button(f"{value} {marker}", f"tf:{prefix}:{value}"))
                rows.append(row)
        rows.append([self._button("➡️ اجرای Pattern123", "wf:analyze")] if workflow else [self._button("⬅️ منوی اصلی", "home")])
        return InlineKeyboardMarkup(rows)

    def workflow_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        stage = selection.workflow_stage
        rows = [[self._button(f"مرحله فعلی: {stage}", "workflow")]]
        rows.append([self._button("1️⃣ نماد", "wf:symbols"), self._button("2️⃣ تایم‌فریم", "wf:timeframes")])
        rows.append([self._button("3️⃣ تحلیل ساختار/Pattern123", "wf:analyze")])
        rows.append([self._button("4️⃣ Trigger", "wf:trigger")])
        rows.append([self._button("5️⃣ Execution / Management", "wf:execution")])
        rows.append([self._button("6️⃣ Journal", "wf:journal")])
        rows.append([self._button("⬅️ منوی اصلی", "home")])
        return InlineKeyboardMarkup(rows)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else 0
        selection = self._selection(user_id)
        selection.reset_workflow()
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
        elif data == "mt5_status":
            text, markup = self._mt5_status_text(selection), self.main_menu()
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
        elif data == "workflow":
            text, markup = self._workflow_text(selection), self.workflow_menu(selection)
        elif data == "wf:symbols":
            selection.workflow_stage = "SYMBOL"
            text, markup = self._symbols_text(selection), self.symbol_menu(selection, workflow=True)
        elif data == "wf:timeframes":
            if not selection.symbols:
                text, markup = "⚠️ ابتدا حداقل یک نماد انتخاب کنید.", self.workflow_menu(selection)
            else:
                selection.workflow_stage = "TIMEFRAME"
                text, markup = self._timeframe_text(selection), self.timeframe_menu(selection, workflow=True)
        elif data == "wf:analyze":
            if not selection.symbols:
                text, markup = "⚠️ مرحله نماد تکمیل نشده است.", self.workflow_menu(selection)
            else:
                selection.workflow_stage = "ANALYSIS"
                text, markup = await self._workflow_analysis(selection), self.workflow_menu(selection)
        elif data == "wf:trigger":
            if selection.last_result is None:
                text, markup = "⚠️ ابتدا تحلیل Pattern123 را اجرا کنید.", self.workflow_menu(selection)
            else:
                selection.workflow_stage = "TRIGGER"
                text, markup = self._trigger_text(selection.last_result, selection), self.workflow_menu(selection)
        elif data == "wf:execution":
            text, markup = self._execution_text(selection), self.workflow_menu(selection)
        elif data == "wf:journal":
            text, markup = self._journal_text(selection), self.workflow_menu(selection)
        elif data == "analysis":
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

    def _mt5_status_text(self, selection: TelegramSelection) -> str:
        lines = ["🛰 وضعیت اتصال واقعی MT5", ""]
        for symbol in sorted(selection.symbols):
            status = mt5_market_gateway.status(symbol)
            state = status.get("status", "unavailable")
            icon = {"ready": "🟢", "stale": "🟠", "unavailable": "🔴"}.get(state, "⚪")
            lines.append(f"{icon} {symbol}: {state}")
            if status.get("live_tick_time"):
                lines.append(f"   Tick: {status['live_tick_time']}")
            if status.get("message"):
                lines.append(f"   {status['message']}")
        lines.extend(["", "منبع مجاز تحلیل: MT5 واقعی.", "بدون snapshot معتبر، تحلیل و معامله fail-closed می‌ماند."])
        return "\n".join(lines)

    def _symbols_text(self, selection: TelegramSelection) -> str:
        return "🪙 انتخاب نماد\n\n" + "\n".join(
            f"{'✅' if symbol in selection.symbols else '▫️'} {symbol}" for symbol in SYMBOLS
        ) + "\n\nامکان انتخاب هم‌زمان چند نماد فعال است."

    def _timeframe_text(self, selection: TelegramSelection) -> str:
        return (
            "⏱ تایم‌فریم‌های قابل انتخاب MT5\n\n"
            f"🏗 ساختار: {selection.structure_timeframe}\n"
            f"🔎 تحلیل: {selection.analysis_timeframe}\n"
            f"🎯 تریگر: {selection.trigger_timeframe}\n\n"
            "پیش‌فرض ژورنالی: M1 / M5 / M15 / H1 / H4 / D1\n"
            "دامنه قابل انتخاب: تایم‌فریم‌های واقعی MT5 تا MN1."
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

    def _workflow_text(self, selection: TelegramSelection) -> str:
        symbols = ", ".join(sorted(selection.symbols)) or "انتخاب نشده"
        return (
            "🚀 Pattern123 Workflow\n\n"
            "1️⃣ Symbol → 2️⃣ Timeframe → 3️⃣ Structure + Analysis → "
            "4️⃣ Trigger → 5️⃣ Execution → 6️⃣ Journal\n\n"
            f"مرحله فعلی: {selection.workflow_stage}\n"
            f"نمادها: {symbols}\n"
            f"Structure TF: {selection.structure_timeframe}\n"
            f"Analysis TF: {selection.analysis_timeframe}\n"
            f"Trigger TF: {selection.trigger_timeframe}"
        )

    async def _workflow_analysis(self, selection: TelegramSelection) -> str:
        if self.engine is None:
            return "❌ موتور تحلیل متصل نیست؛ داده واقعی MT5 لازم است."
        reports = []
        for symbol in sorted(selection.symbols):
            try:
                result = self.engine.analyze_market(symbol, selection.analysis_timeframe,
                    structure_timeframe=selection.structure_timeframe,
                    trigger_timeframe=selection.trigger_timeframe)
                selection.last_result = result
                view = analysis_view_from_result(result, symbol=symbol, selection=selection)
                reports.append(render_analysis(view))
            except Exception as exc:
                reports.append(f"📈 {symbol}\n\n❌ تحلیل اجرا نشد: {type(exc).__name__}")
        return "\n\n━━━━━━━━━━━━━━\n\n".join(reports)

    def _trigger_text(self, result, selection: TelegramSelection) -> str:
        trigger = result.get("trigger") if isinstance(result, dict) else None
        if trigger is None:
            return "🎯 Trigger در نتیجه تحلیل موجود نیست؛ اجرای معامله مجاز نیست."
        status = getattr(trigger, "status", "NO_TRADE")
        direction = getattr(trigger, "direction", "none")
        entry = getattr(trigger, "entry", 0)
        stop_loss = getattr(trigger, "stop_loss", 0)
        take_profit = getattr(trigger, "take_profit", 0)
        risk_reward = getattr(trigger, "risk_reward", 0)
        reasons = "\n".join(f"• {item}" for item in getattr(trigger, "reasons", [])) or "• هیچ تأییدیه‌ای ثبت نشده"
        warnings = "\n".join(f"⚠️ {item}" for item in getattr(trigger, "warnings", [])) or "⚠️ بدون هشدار"
        return (
            f"🎯 Trigger\n\nوضعیت: {status}\nجهت: {direction}\n"
            f"Entry: {entry}\nSL: {stop_loss}\nTP: {take_profit}\nRR: {risk_reward}\n\n"
            f"{reasons}\n\n{warnings}"
        )

    def _execution_text(self, selection: TelegramSelection) -> str:
        result = selection.last_result
        trigger = result.get("trigger") if isinstance(result, dict) else None
        if trigger is None or getattr(trigger, "status", "NO_TRADE") != "READY":
            return "⛔ Execution قفل است. فقط Trigger=READY می‌تواند وارد مرحله اجرا شود؛ در غیر این صورت NO_TRADE."
        return "🔐 Execution آماده است، اما Live Trading همچنان طبق قفل Risk/Live configuration کنترل می‌شود. هیچ سفارش خودکاری از Telegram صادر نمی‌شود."

    def _journal_text(self, selection: TelegramSelection) -> str:
        if selection.last_result is None:
            return "📒 Journal پس از یک lifecycle واقعی MT5 تکمیل می‌شود. هنوز معامله‌ای در این workflow ثبت نشده است."
        return "📒 Journal\n\nپس از باز/بسته‌شدن معامله، lifecycle واقعی MT5 در Journal ثبت می‌شود. داده ساختگی یا دستی وارد Journal نمی‌شود."

    async def _analysis_text(self, selection: TelegramSelection) -> str:
        if self.engine is None:
            return "📈 موتور تحلیل به تلگرام متصل نشده است؛ نتیجه واقعی بدون داده بازار ساخته نمی‌شود."
        reports: list[str] = []
        for symbol in sorted(selection.symbols):
            try:
                result = self.engine.analyze_market(symbol, selection.analysis_timeframe)
                view = analysis_view_from_result(result, symbol=symbol, selection=selection)
                reports.append(render_analysis(view))
            except Exception as exc:
                reports.append(f"📈 {symbol}\n\n❌ تحلیل اجرا نشد.\nخطای فنی: {type(exc).__name__}")
        return "\n\n━━━━━━━━━━━━━━\n\n".join(reports)

    def build(self):
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button))
        return self.application


__all__ = ["TelegramBot", "SYMBOLS", "STRUCTURE_TIMEFRAMES", "ANALYSIS_TIMEFRAMES", "TRIGGER_TIMEFRAMES"]
