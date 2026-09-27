#property strict
#property version   "1.0.0"
#property description "Pattern 123 / ARMOS - secure MT5 market-data connector"

input string InpBackendUrl = "https://pattern123-trading-bot.onrender.com";
input string InpWebhookSecret = "";
input string InpSymbol = "";
input int    InpBarsPerTimeframe = 200;
input int    InpPushIntervalSeconds = 15;
input int    InpHttpTimeoutMs = 5000;
input bool   InpEnableTradingCommands = false;

string ApiUrl()
{
   string base = InpBackendUrl;
   while(StringLen(base) > 0 && StringSubstr(base, StringLen(base)-1, 1) == "/")
      base = StringSubstr(base, 0, StringLen(base)-1);
   return base + "/webhook/mt5";
}

string ActiveSymbol()
{
   if(StringLen(InpSymbol) > 0)
      return InpSymbol;
   return _Symbol;
}

string JsonEscape(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, """, "\\"");
   StringReplace(value, "\r", "\\r");
   StringReplace(value, "\n", "\\n");
   return value;
}

string TimeframeName(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
   }
   return "";
}

bool IsAllowedTimeframe(ENUM_TIMEFRAMES tf)
{
   return tf == PERIOD_M1 || tf == PERIOD_M5 || tf == PERIOD_M15 ||
          tf == PERIOD_H1 || tf == PERIOD_H4 || tf == PERIOD_D1;
}

string BuildCandleJson(string symbol, ENUM_TIMEFRAMES tf)
{
   MqlRates rates[];
   ArraySetAsSeries(rates, false);

   int requested = MathMax(InpBarsPerTimeframe, 50);
   int copied = CopyRates(symbol, tf, 0, requested, rates);
   if(copied < 50)
   {
      PrintFormat("Pattern123: insufficient bars %s %s copied=%d error=%d",
                  symbol, TimeframeName(tf), copied, GetLastError());
      return "";
   }

   string json = "[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0)
         json += ",";
      json += StringFormat(
         "{\"time\":%I64d,\"open\":%.10f,\"high\":%.10f,\"low\":%.10f,\"close\":%.10f,\"volume\":%I64d}",
         (long)rates[i].time,
         rates[i].open,
         rates[i].high,
         rates[i].low,
         rates[i].close,
         (long)rates[i].tick_volume
      );
   }
   json += "]";
   return json;
}

string BuildMarketPayload(string symbol)
{
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
   {
      PrintFormat("Pattern123: SymbolInfoTick failed for %s error=%d", symbol, GetLastError());
      return "";
   }

   long serverTime = (long)tick.time;
   if(serverTime <= 0)
   {
      Print("Pattern123: invalid MT5 tick timestamp");
      return "";
   }

   string payload = StringFormat(
      "{\"connector\":\"pattern123-mt5-ea\",\"version\":\"1.0.0\",\"source\":\"mt5\",\"demo_mode\":false,"
      "\"symbol\":\"%s\",\"tick\":{\"bid\":%.10f,\"ask\":%.10f,\"time\":%I64d},\"timeframes\":{",
      JsonEscape(symbol), tick.bid, tick.ask, serverTime
   );

   ENUM_TIMEFRAMES tfs[6] = {PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_H1, PERIOD_H4, PERIOD_D1};
   bool first = true;
   for(int i = 0; i < 6; i++)
   {
      if(!IsAllowedTimeframe(tfs[i]))
         continue;

      string name = TimeframeName(tfs[i]);
      string candles = BuildCandleJson(symbol, tfs[i]);
      if(candles == "")
         return "";

      if(!first)
         payload += ",";
      payload += "\"";
      payload += name;
      payload += "\":";
      payload += candles;
      first = false;
   }

   payload += "}}";
   return payload;
}

bool PostJson(string url, string body, string &response)
{
   char data[];
   char result[];
   string headers = "Content-Type: application/json\r\n";
   if(StringLen(InpWebhookSecret) > 0)
      headers += "X-Webhook-Secret: " + InpWebhookSecret + "\r\n";

   int size = StringToCharArray(body, data, 0, WHOLE_ARRAY, CP_UTF8);
   if(size > 0)
      ArrayResize(data, size - 1);

   ResetLastError();
   int code = WebRequest("POST", url, headers, InpHttpTimeoutMs, data, ArraySize(data), result, headers);
   if(code == -1)
   {
      int err = GetLastError();
      PrintFormat("Pattern123: WebRequest failed error=%d. Add backend URL to MT5 Tools -> Options -> Expert Advisors -> allowed WebRequest URLs.",
                  err);
      return false;
   }

   response = CharArrayToString(result, 0, -1, CP_UTF8);
   if(code < 200 || code >= 300)
   {
      PrintFormat("Pattern123: backend HTTP %d response=%s", code, response);
      return false;
   }

   return true;
}

bool PushMarket()
{
   string symbol = ActiveSymbol();
   if(!SymbolSelect(symbol, true))
   {
      PrintFormat("Pattern123: cannot select symbol %s error=%d", symbol, GetLastError());
      return false;
   }

   string body = BuildMarketPayload(symbol);
   if(body == "")
      return false;

   string response = "";
   bool ok = PostJson(ApiUrl(), body, response);
   if(ok)
      PrintFormat("Pattern123: market snapshot delivered. symbol=%s response=%s", symbol, response);
   return ok;
}

int OnInit()
{
   string symbol = ActiveSymbol();
   if(!SymbolSelect(symbol, true))
   {
      PrintFormat("Pattern123: OnInit cannot select %s error=%d", symbol, GetLastError());
      return INIT_FAILED;
   }

   if(StringLen(InpBackendUrl) == 0)
   {
      Print("Pattern123: backend URL is empty");
      return INIT_PARAMETERS_INCORRECT;
   }

   if(InpPushIntervalSeconds < 5)
   {
      Print("Pattern123: push interval must be >= 5 seconds");
      return INIT_PARAMETERS_INCORRECT;
   }

   EventSetTimer(InpPushIntervalSeconds);
   PrintFormat("Pattern123: MT5 connector started symbol=%s backend=%s trading_commands=%s",
               symbol, InpBackendUrl, InpEnableTradingCommands ? "ON" : "OFF");

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   PrintFormat("Pattern123: connector stopped reason=%d", reason);
}

void OnTick()
{
   // Market delivery is timer-driven to avoid flooding the backend on every tick.
}

void OnTimer()
{
   PushMarket();
}
