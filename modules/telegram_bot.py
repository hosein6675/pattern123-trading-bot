from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from modules.config import active_config


SYMBOLS = [
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "BTCUSD",
    "ETHUSD"
]


class TelegramBot:

    def __init__(self, token: str):

        self.token = token
        self.application = None


    def main_menu(self):

        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 وضعیت بازار",
                    callback_data="market_status"
                )
            ],
            [
                InlineKeyboardButton(
                    "🪙 نماد",
                    callback_data="symbol"
                ),
                InlineKeyboardButton(
                    "⏱ تایم‌فریم",
                    callback_data="timeframe"
                )
            ],
            [
                InlineKeyboardButton(
                    "📰 اخبار",
                    callback_data="news"
                ),
                InlineKeyboardButton(
                    "💰 حساب",
                    callback_data="account"
                )
            ],
            [
                InlineKeyboardButton(
                    "📈 تحلیل",
                    callback_data="analysis"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ تنظیمات",
                    callback_data="settings"
                )
            ],
        ]

        return InlineKeyboardMarkup(keyboard)



    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        await update.message.reply_text(
            "🤖 دستیار Pattern 123 فعال شد.\n\n"
            "از منوی زیر انتخاب کن:",
            reply_markup=self.main_menu()
        )



    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query

        await query.answer()


        if query.data == "market_status":

            text = (
                "📊 وضعیت بازار\n\n"
                f"بازار: {active_config.market}\n"
                f"نماد: {active_config.symbol}\n"
                f"حالت: {active_config.mode}"
            )


        elif query.data == "symbol":

            text = (
                "🪙 نمادهای فعال:\n\n"
                + "\n".join(SYMBOLS)
            )


        elif query.data == "timeframe":

            text = (
                "⏱ تایم‌فریم چندلایه\n\n"

                "📈 روند:\n"
                + "\n".join(active_config.trend_timeframes)

                + "\n\n🏗 ساختار:\n"
                + "\n".join(active_config.structure_timeframes)

                + "\n\n🎯 ورود:\n"
                + "\n".join(active_config.entry_timeframes)
            )


        elif query.data == "news":

            text = (
                "📰 وضعیت اخبار\n\n"
                f"معامله هنگام اخبار: "
                f"{'فعال' if active_config.trade_news else 'غیرفعال'}"
            )


        elif query.data == "account":

            text = (
                "💰 وضعیت حساب\n\n"
                f"حالت: {active_config.mode}\n"
                f"سرمایه: ${active_config.initial_balance:.2f}"
            )


        elif query.data == "analysis":

            text = (
                "📈 موتور تحلیل Pattern 123\n\n"
                "📌 Trend:\n"
                "D1 + H4\n\n"
                "📌 Structure:\n"
                "H4 + H1 + M15\n\n"
                "📌 Entry:\n"
                "M15 + M5 + M1\n\n"
                "وضعیت: آماده اتصال به موتور تحلیل"
            )


        elif query.data == "settings":

            text = (
                "⚙️ تنظیمات فعلی\n\n"
                f"بازار: {active_config.market}\n"
                f"نماد: {active_config.symbol}\n"
                f"Auto Trading: "
                f"{'فعال' if active_config.auto_trading else 'غیرفعال'}"
            )


        else:

            text = "دستور ناشناخته است."


        await query.edit_message_text(
            text,
            reply_markup=self.main_menu()
        )



    def build(self):

        self.application = (
            Application
            .builder()
            .token(self.token)
            .build()
        )


        self.application.add_handler(
            CommandHandler(
                "start",
                self.start
            )
        )


        self.application.add_handler(
            CallbackQueryHandler(
                self.button
            )
        )


        return self.application
