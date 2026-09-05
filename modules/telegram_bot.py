from __future__ import annotations

from dataclasses import replace
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from modules.bot_controller import BotController
from modules.config import active_config
from modules.system_control import SystemMode
from modules.telegram_controls import ANALYSIS_TIMEFRAMES, STRUCTURE_TIMEFRAMES, TRIGGER_TIMEFRAMES, TelegramSelection, analysis_view_from_result, render_analysis
from modules.telegram_permissions import TelegramPermissionManager
from modules.trading_engine import TradingEngine

logger = logging.getLogger(__name__)
SYMBOLS = tuple(sorted(active_config.allowed_symbols))


class TelegramBot:
    """Telegram transport only: authorization and business operations live behind BotController."""

    def __init__(self, token: str, engine: TradingEngine | None = None, permissions: TelegramPermissionManager | None = None, controller: BotController | None = None):
        self.token = token
        self.application = None
        self.controller = controller or BotController(engine=engine, permissions=permissions)
        self.engine = self.controller.engine
        self.permissions = self.controller.permissions
        self._selections: dict[int, TelegramSelection] = {}

    def _selection(self, user_id: int) -> TelegramSelection:
        if user_id not in self._selections:
            self._selections[user_id] = TelegramSelection(symbols={active_config.symbol})
        return self._selections[user_id]

    def _allowed(self, user_id: int, capability: str) -> bool:
        return self.permissions.allowed(user_id, capability)

    @staticmethod
    def _button(label: str, callback: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(label, callback_data=callback)

    def main_menu(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [self._button("📊 وضعیت", "status"), self._button("📈 تحلیل", "analysis")],
            [self._button("🪙 نمادها", "symbols"), self._button("⏱ تایم‌فریم‌ها", "timeframes")],
            [self._button("📓 ژورنال", "journal"), self._button("🤖 AI Report", "ai")],
            [self._button("🛡 ریسک", "risk"), self._button("💹 MT5 Status", "mt5")],
            [self._button("🔐 دسترسی", "permissions"), self._button("⚙️ تنظیمات", "settings")],
            [self._button("📰 اخبار", "news"), self._button("🛠 ابزار سیستم", "system")],
            [self._button("📤 Distribution", "distribution"), self._button("📁 File Manager", "files")],
        ])

    def symbol_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        rows = [[self._button(f"{'✅' if s in selection.symbols else '▫️'} {s}", f"sym:{s}")] for s in SYMBOLS]
        rows += [[self._button("🔄 همه", "sym:all")], [self._button("🧹 پاک کردن", "sym:none")], [self._button("⬅️ اصلی", "home")]]
        return InlineKeyboardMarkup(rows)

    def timeframe_menu(self, selection: TelegramSelection) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [self._button(f"🏗 ساختار: {selection.structure_timeframe}", "tf:structure")],
            [self._button(f"D1 {'✅' if selection.structure_timeframe == 'D1' else '▫️'}", "tf:s:D1"), self._button(f"H4 {'✅' if selection.structure_timeframe == 'H4' else '▫️'}", "tf:s:H4"), self._button(f"H1 {'✅' if selection.structure_timeframe == 'H1' else '▫️'}", "tf:s:H1")],
            [self._button(f"🔎 تحلیل: {selection.analysis_timeframe}", "tf:analysis")],
            [self._button(f"H1 {'✅' if selection.analysis_timeframe == 'H1' else '▫️'}", "tf:a:H1"), self._button(f"M15 {'✅' if selection.analysis_timeframe == 'M15' else '▫️'}", "tf:a:M15")],
            [self._button(f"M5 {'✅' if selection.analysis_timeframe == 'M5' else '▫️'}", "tf:a:M5"), self._button(f"M1 {'✅' if selection.analysis_timeframe == 'M1' else '▫️'}", "tf:a:M1")],
            [self._button(f"🎯 تریگر: {selection.trigger_timeframe}", "tf:trigger")],
            [self._button(f"M15 {'✅' if selection.trigger_timeframe == 'M15' else '▫️'}", "tf:t:M15"), self._button(f"M5 {'✅' if selection.trigger_timeframe == 'M5' else '▫️'}", "tf:t:M5"), self._button(f"M1 {'✅' if selection.trigger_timeframe == 'M1' else '▫️'}", "tf:t:M1")],
            [self._button("⬅️ اصلی", "home")],
        ])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id if update.effective_user else 0
        self._selection(user_id)
        if not self._allowed(user_id, "can_view"):
            await update.message.reply_text("⛔ دسترسی رد شد.")
            return
        await update.message.reply_text("🤖 Pattern 123\n\nپنل کنترل آماده است.", reply_markup=self.main_menu())

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id if update.effective_user else 0
        selection = self._selection(user_id)
        data = query.data or ""
        try:
            text, markup = await self._dispatch(user_id, selection, data)
        except Exception:
            logger.exception("Telegram callback failed: user_id=%s callback=%s", user_id, data)
            text, markup = "❌ عملیات انجام نشد. خطا ثبت شد و اطلاعات فنی به کاربر نمایش داده نشد.", self.main_menu()
        await query.edit_message_text(text, reply_markup=markup)

    async def _dispatch(self, user_id: int, selection: TelegramSelection, data: str):
        if data in {"home", "status"}: return self._status_text(), self.main_menu()
        if data == "permissions": return self._permissions_text(user_id), self.main_menu()
        if data == "symbols": return self._symbols_text(selection), self.symbol_menu(selection)
        if data.startswith("sym:"):
            value = data.split(":", 1)[1]
            if value == "all": selection.set_symbols(list(SYMBOLS), set(SYMBOLS))
            elif value == "none": return "⚠️ حداقل یک نماد باید انتخاب شود.", self.symbol_menu(selection)
            else: selection.toggle_symbol(value, set(SYMBOLS)); selection.symbols = selection.symbols or {value}
            return self._symbols_text(selection), self.symbol_menu(selection)
        if data in {"timeframes", "tf:structure", "tf:analysis", "tf:trigger"}: return self._timeframe_text(selection), self.timeframe_menu(selection)
        if data.startswith("tf:s:"): selection.set_structure_timeframe(data.rsplit(":", 1)[1]); return self._timeframe_text(selection), self.timeframe_menu(selection)
        if data.startswith("tf:a:"): selection.set_analysis_timeframe(data.rsplit(":", 1)[1]); return self._timeframe_text(selection), self.timeframe_menu(selection)
        if data.startswith("tf:t:"): selection.set_trigger_timeframe(data.rsplit(":", 1)[1]); return self._timeframe_text(selection), self.timeframe_menu(selection)
        if data == "analysis":
            if not self._allowed(user_id, "can_analyze"): return "⛔ دسترسی تحلیل قفل است.", self.main_menu()
            return await self._analysis_text(selection), self.main_menu()
        if data == "journal": return self._journal_text(user_id), self.main_menu()
        if data == "ai": return self._ai_text(user_id), self.main_menu()
        if data == "risk": return self._risk_text(user_id), self.main_menu()
        if data == "mt5": return self._mt5_text(user_id), self.main_menu()
        if data == "system": return self._system_text(user_id), self.system_menu(user_id)
        if data == "system:monitor": return self._set_mode(user_id, SystemMode.MONITOR), self.system_menu(user_id)
        if data == "system:signal": return self._set_mode(user_id, SystemMode.SIGNAL_ONLY), self.system_menu(user_id)
        if data == "system:auto": return self._set_mode(user_id, SystemMode.AUTO_TRADING), self.system_menu(user_id)
        if data == "system:stop":
            if not self._allowed(user_id, "can_manage_system"): return "⛔ دسترسی مدیر سیستم لازم است.", self.main_menu()
            self.controller.system.activate_emergency_stop(); return self._system_text(user_id), self.system_menu(user_id)
        if data == "distribution": return self._distribution_text(user_id), self.main_menu()
        if data == "files": return self._files_text(user_id), self.main_menu()
        if data == "news": return "📰 فیلتر خبر: قابل مشاهده از سرویس News؛ هیچ سیگنال جعلی تولید نمی‌شود.", self.main_menu()
        if data == "account": return self._account_text(user_id), self.main_menu()
        if data == "settings": return self._settings_text(), self.main_menu()
        return "دستور ناشناخته است.", self.main_menu()

    def system_menu(self, user_id: int):
        if not self._allowed(user_id, "can_manage_system"): return self.main_menu()
        return InlineKeyboardMarkup([[self._button("👁 Monitor", "system:monitor"), self._button("📡 Signal-only", "system:signal")], [self._button("🤖 Auto", "system:auto"), self._button("🛑 Emergency Stop", "system:stop")], [self._button("⬅️ اصلی", "home")]])

    def _set_mode(self, user_id, mode):
        if not self._allowed(user_id, "can_manage_system"): return "⛔ دسترسی مدیر سیستم لازم است."
        self.controller.system.set_mode(mode)
        return self._system_text(user_id)

    def _status_text(self):
        status = self.controller.get_status(); return f"📊 وضعیت سیستم\n\nMode: {status['mode']}\nSymbol: {status['symbol']}\nTimeframe: {status['timeframe']}\nJournal: {status['journal_trades']} trades\nLive trading: {'ON' if status['live_trading_enabled'] else 'LOCKED'}"

    def _permissions_text(self, user_id):
        p = self.permissions.profile_for(user_id); yn = lambda v: "فعال" if v else "قفل"
        return f"🔐 دسترسی\n\nRole: {p.role.value}\nمشاهده: {yn(p.can_view)}\nتحلیل: {yn(p.can_analyze)}\nمعامله: {yn(p.can_trade)}\nسیستم: {yn(p.can_manage_system)}\nDistribution: {yn(p.can_manage_distribution)}\nداده حساس: {yn(p.can_view_sensitive)}"

    def _symbols_text(self, selection): return "🪙 نمادها\n\n" + "\n".join(f"{'✅' if s in selection.symbols else '▫️'} {s}" for s in SYMBOLS)
    def _timeframe_text(self, selection): return f"⏱ تایم‌فریم‌ها\n\n🏗 ساختار: {selection.structure_timeframe} / {', '.join(STRUCTURE_TIMEFRAMES)}\n🔎 تحلیل: {selection.analysis_timeframe} / {', '.join(ANALYSIS_TIMEFRAMES)}\n🎯 تریگر: {selection.trigger_timeframe} / {', '.join(TRIGGER_TIMEFRAMES)}"
    def _settings_text(self): return f"⚙️ تنظیمات\n\nMarket: {active_config.market}\nDefault: {active_config.symbol} / {active_config.timeframe}\nAllowed symbols: {len(active_config.allowed_symbols)}\nLive: {'enabled' if active_config.live_trading_enabled else 'fail-closed'}"
    def _account_text(self, user_id):
        if not self._allowed(user_id, "can_view_sensitive"): return "⛔ اطلاعات حساب در دسترس این نقش نیست."
        a = self.engine.account.get_account(); return f"💰 حساب\n\nBalance: {a.balance:.2f}\nEquity: {a.equity:.2f}\nDrawdown: {a.drawdown_percent:.2f}%\nDaily P/L: {a.daily_profit_loss:.2f}"
    def _risk_text(self, user_id):
        if not self._allowed(user_id, "can_view_sensitive"): return "⛔ اطلاعات ریسک حساس است."
        r = self.controller.risk_status(); return f"🛡 ریسک\n\nBalance: {r['balance']:.2f}\nEquity: {r['equity']:.2f}\nDD: {r['drawdown_percent']:.2f}%\nDaily P/L: {r['daily_profit_loss']:.2f}\nOpen: {r['open_positions']}\nOpen risk: {r['open_risk_percent']:.4f}%\nLimits: {r['limits']}"
    def _mt5_text(self, user_id):
        if not self._allowed(user_id, "can_view_sensitive"): return "⛔ وضعیت MT5 حساس است."
        return f"💹 MT5 / Broker\n\n{self.controller.broker_status()}"
    def _journal_text(self, user_id):
        if not self._allowed(user_id, "can_view_sensitive"): return "⛔ ژورنال شامل داده حساس است."
        a = self.controller.journal_summary(); return f"📓 Journal\n\nTotal: {a.total}\nClosed: {a.closed}\nWins: {a.wins}\nLosses: {a.losses}\nWin rate: {a.win_rate:.2f}%\nNet P/L: {a.net_profit:.4f}\nBest hours: {a.best_hours}"
    def _ai_text(self, user_id):
        if not self._allowed(user_id, "can_view_sensitive"): return "⛔ گزارش AI حساس است."
        r = self.controller.ai_report(); return "🤖 AI Report\n\n" + r.summary + ("\n\n⚠️ " + "\n".join(r.warnings) if r.warnings else "") + ("\n\nپیشنهادها:\n• " + "\n• ".join(r.recommendations) if r.recommendations else "")
    def _system_text(self, user_id):
        if not self._allowed(user_id, "can_manage_system"): return "⛔ دسترسی مدیر سیستم لازم است."
        s = self.controller.system.snapshot(); return f"🛠 System Control\n\nMode: {s['mode']}\nEmergency stop: {s['emergency_stop']}\nModules: {', '.join(s['modules'])}"
    def _distribution_text(self, user_id):
        if not self._allowed(user_id, "can_manage_distribution"): return "⛔ دسترسی Distribution فقط برای مدیر است."
        return f"📤 Distribution\n\nDestinations: {len(self.controller.distribution.destinations)}\nDelivery log: {len(self.controller.distribution.delivery_log)}\nSensitive data: public groups/channels are blocked by policy."
    def _files_text(self, user_id):
        if not self._allowed(user_id, "can_manage_system"): return "⛔ File Manager فقط برای مدیر سیستم است."
        return "📁 File Manager\n\nJournal database: data/journal.sqlite3\nArchive/delete/move operations remain admin-only and are not exposed as arbitrary filesystem commands."

    async def _analysis_text(self, selection):
        if self.engine is None: return "📈 موتور تحلیل متصل نیست."
        reports = []
        for symbol in sorted(selection.symbols):
            try:
                multi = self.controller.analyze_multi_timeframe(symbol, selection)
                layers = (("🏗 ساختار", multi.structure, selection.structure_timeframe), ("🔎 تحلیل", multi.analysis, selection.analysis_timeframe), ("🎯 تریگر", multi.trigger, selection.trigger_timeframe))
                layer_reports = []
                for label, result, timeframe in layers:
                    view = analysis_view_from_result(result, symbol=symbol, selection=selection)
                    view = replace(view, structure_timeframe=timeframe, analysis_timeframe=timeframe, trigger_timeframe=timeframe)
                    layer_reports.append(f"{label}\n{render_analysis(view)}")
                if multi.warnings: layer_reports.append("⚠️ MTF\n" + "\n".join(f"• {w}" for w in multi.warnings))
                reports.append("\n\n━━━━━━━━━━━━━━\n\n".join(layer_reports))
            except Exception:
                logger.exception("Analysis failed: symbol=%s", symbol); reports.append(f"📈 {symbol}\n\n❌ تحلیل انجام نشد؛ خطا در سرور ثبت شد.")
        return "\n\n════════════════════\n\n".join(reports)

    def build(self):
        self.application = Application.builder().token(self.token).build(); self.application.add_handler(CommandHandler("start", self.start)); self.application.add_handler(CallbackQueryHandler(self.button)); return self.application


__all__ = ["TelegramBot", "SYMBOLS", "STRUCTURE_TIMEFRAMES", "ANALYSIS_TIMEFRAMES", "TRIGGER_TIMEFRAMES"]
