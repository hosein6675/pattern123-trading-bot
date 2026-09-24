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

## راه‌اندازی Telegram روی Render

فایل `render.yaml` متغیرهای `BOT_TOKEN` و `WEBHOOK_SECRET` را به‌صورت secret و بدون مقدار داخل Git تعریف می‌کند. توکن واقعی Telegram نباید در GitHub، `.env.example` یا کد commit شود.

در Render برای سرویس `pattern123-trading-bot`:
1. به **Environment** بروید.
2. متغیر `BOT_TOKEN` را ایجاد کنید و مقدار توکن BotFather را همان‌جا وارد کنید.
3. برای `WEBHOOK_SECRET` یک مقدار تصادفی و غیرقابل‌حدس قرار دهید.
4. **Save Changes** و سپس **Manual Deploy / Deploy latest commit** را اجرا کنید.
5. پس از بالا آمدن سرویس، endpointهای `/` یا `/health` باید مقدار `telegram: enabled` را نشان دهند.
6. سپس در Telegram دستور `/start` را ارسال کنید.

اگر `BOT_TOKEN` تنظیم نشده باشد، سرویس وب همچنان بالا می‌آید اما Telegram عمداً غیرفعال می‌ماند؛ این رفتار fail-closed است و خطای آن در لاگ startup ثبت می‌شود.

### تست مرحله‌ای Telegram

ترتیب تست عملی:
- `/start` و نمایش منوی اصلی
- انتخاب چند نماد و تغییر هر سه لایه timeframe
- ورود به **اجرای تحلیل** و بررسی اینکه بدون داده معتبر، سیستم سیگنال ساختگی تولید نکند
- بررسی وضعیت حساب و تنظیمات
- بررسی endpoint `/health` برای تأیید فعال بودن Telegram

این تست‌ها جایگزین اتصال واقعی MT5 نیستند. برای تحلیل واقعی، منبع داده باید از broker/MT5 یا یک منبع بازار معتبر وارد شود.