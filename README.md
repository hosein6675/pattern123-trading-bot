# Pattern 123 Trading Bot

هسته Pattern123، رابط Telegram، ژورنال، کنترل ریسک و bridge رسمی MT5 در یک معماری fail-closed توسعه داده شده‌اند.

## معماری

```text
Telegram / MT5 EA
       |
       v
 BotController / HTTP boundary
       |
       +--> Pattern123 Strategy + MTF Analysis
       +--> Risk / Money Management
       +--> Execution / Broker Adapter
       +--> Persistent Journal
       +--> Analytics / AI Report
       +--> Distribution / System Control
```

## Telegram

- انتخاب هم‌زمان چند نماد
- سه لایه Structure / Analysis / Trigger
- تحلیل واقعی MTF؛ بدون ساختن داده جعلی
- Permission roles: viewer / trader / admin
- Journal / AI Report / Risk / MT5 Status
- System Control: monitor / signal-only / auto-trading / emergency stop
- Distribution با جلوگیری از ارسال داده حساس به مقصد عمومی
- File Manager محدود به `data/`
- خطاهای فنی در لاگ سرور ثبت می‌شوند و به کاربر leak نمی‌شوند

## Journal و Analytics

- SQLite persistence در `data/journal.sqlite3`
- شناسه مستقل برای هر معامله
- broker order correlation
- entry/exit timestamps به‌صورت timezone-aware UTC
- TP/SL، ریسک، R:R، عوامل مثبت/منفی، اشتباهات و نسخه استراتژی
- تحلیل win rate، P/L، BUY/SELL، symbol، timeframe، ساعت‌های پرتکرار
- تشخیص عوامل موفق تکرارشونده و اشتباهات تکرارشونده
- گزارش batch در هر 100 معامله
- AI فقط گزارش و پیشنهاد تولید می‌کند و مستقیماً strategy را تغییر نمی‌دهد

## MT5 EA

فایل `mt5/Pattern123EA.mq5` یک bridge رسمی برای MetaTrader 5 است:

- Monitor / Signal-only / Auto-trading
- دریافت سیگنال MTF از `/mt5/signal`
- Risk-based lot sizing با `OrderCalcProfit`
- Magic Number isolation
- حداکثر تعداد position
- SL/TP از هسته Pattern123
- ارسال statement دوره‌ای به `/mt5/report`
- در صورت قطع سرور/secret نامعتبر، معامله جدید انجام نمی‌شود
- معامله دستی با Magic Number متفاوت توسط EA مدیریت نمی‌شود

برای `WebRequest` باید URL سرور در لیست Allowed URLs ترمینال MT5 ثبت شود.

## امنیت مالی

ربات و EA هیچ API برای deposit / withdrawal / transfer / margin transfer / تغییر leverage یا جابه‌جایی پول ندارند. سطح دسترسی فقط برای market data، تحلیل، order execution/trade management و reporting است.

## اجرای امن

پیش‌فرض‌ها:

- `TRADING_MODE=demo`
- `LIVE_TRADING_ENABLED=false`
- `TEST_TRADE_ENABLED=false`
- `WEBHOOK_SECRET` اجباری برای endpointهای MT5/webhook

ترتیب اعتبارسنجی پیشنهادی:

1. data-only
2. signal-only
3. MT5 demo
4. حداقل 100 معامله معتبر
5. بررسی Journal و Analytics
6. بررسی OOS / release gate
7. فقط پس از تأیید کاربر، live

## CI

CI شامل compileall، smoke test، pytest، coverage، Ruff و validation فایل‌های workflow است.

**سبز شدن CI به‌تنهایی به معنی سودده بودن استراتژی نیست.** اعتبار عملکرد باید با داده تاریخی واقعی و OOS معتبر انجام شود.
