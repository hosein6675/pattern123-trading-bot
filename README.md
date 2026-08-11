# Pattern 123 Trading Bot

نسخه MVP دستیار تلگرام بر اساس قواعدی که کاربر در گفتگو تعریف کرده است.

## ماژول‌ها
- Price Action
- Price Action Fractal
- MACD: 12,26,9 / 3,6,2 / 48,104,36
- EMA: 30 / 60 / 100 / 200
- Fibonacci retracement
- ساختار 1H / 4H / Daily
- Webhook برای دریافت داده بازار

## نکته مهم
این نسخه زیرساخت ربات و هسته محاسباتی اولیه را فراهم می‌کند. برای اجرای واقعی داده:
- کریپتو: می‌توان TradingView Alert را به endpoint وبهوک متصل کرد.
- فارکس/MT5: یک EA یا bridge روی MetaTrader 5 باید داده OHLC را به endpoint وبهوک ارسال کند.
- توکن Telegram فقط در Environment Variables سرویس Render قرار گیرد.

این پروژه عمداً بدون ادعای «درصد موفقیت» یا تضمین سود طراحی شده است.
