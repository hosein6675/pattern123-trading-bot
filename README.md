# Pattern 123 Trading Bot

نسخه MVP دستیار تلگرام بر اساس قواعدی که کاربر در گفتگو تعریف کرده است.

## وضعیت فنی پروژه

هسته پروژه اکنون شامل مسیر داده/بازپخش تاریخی، جداسازی point-in-time، walk-forward validation، مدل هزینه اجرای صریح، معیارهای عملکرد، گیت‌های OOS، مدیریت ریسک، لایه broker fail-closed، و داشبورد تصمیم است.

## ماژول‌ها
- Price Action
- Price Action Fractal
- MACD: 12,26,9 / 3,6,2 / 48,104,36
- EMA: 30 / 60 / 100 / 200
- Fibonacci retracement
- ساختار 1H / 4H / Daily
- Webhook برای دریافت داده بازار
- Walk-forward validation و release-readiness gate

## مرزهای مهم

این پروژه عمداً بدون ادعای «درصد موفقیت» یا تضمین سود طراحی شده است. CI سبز به معنی سودده بودن استراتژی نیست.

برای اعتبارسنجی واقعی باید یک dataset تاریخی واقعی و معتبر وارد شود و نتیجه OOS با هزینه‌های واقعی/مناسب broker محاسبه شود. بدون داده تاریخی واقعی، نباید نتیجه عملکرد عددی ساخته یا ادعا شود.

برای اجرای واقعی:
- کریپتو: می‌توان TradingView Alert را به endpoint وبهوک متصل کرد.
- فارکس/MT5: یک EA یا bridge روی MetaTrader 5 باید داده OHLC را به endpoint وبهوک ارسال کند.
- اجرای live نیازمند broker/account/credentials/permissions واقعی کاربر است و در CI یا این release gate هیچ معامله واقعی ارسال نمی‌شود.
- Order Flow / Level-2 فقط با provider واقعی و داده point-in-time مجاز است؛ داده مصنوعی برای validation استفاده نمی‌شود.
- توکن Telegram و سایر secrets فقط در Environment Variables قرار گیرند.

## مستندات

- `backtest/VALIDATION_PROTOCOL.md` — پروتکل اعتبارسنجی تاریخی
- `docs/BACKTEST_LAB.md` — آزمایشگاه backtest
- `docs/FINAL_RELEASE_GATE.md` — گیت نهایی انتشار
- `docs/DEVELOPMENT_GATES.md` — قواعد توسعه و merge
