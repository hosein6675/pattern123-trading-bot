#property strict
#property version   "1.0"
#property description "Pattern123 EA: authenticated signal bridge, risk sizing, magic-number isolation."

#include <Trade/Trade.mqh>

CTrade trade;

enum EA_MODE
  {
   MODE_MONITOR=0,
   MODE_SIGNAL_ONLY=1,
   MODE_AUTO_TRADING=2
  };

input string   ServerURL="http://127.0.0.1:10000";
input string   WebhookSecret="";
input EA_MODE  Mode=MODE_SIGNAL_ONLY;
input ENUM_TIMEFRAMES StructureTimeframe=PERIOD_H4;
input ENUM_TIMEFRAMES AnalysisTimeframe=PERIOD_M15;
input ENUM_TIMEFRAMES TriggerTimeframe=PERIOD_M1;
input int      BarsToSend=100;
input double   RiskPercent=1.0;
input int      MaxOpenPositions=5;
input ulong    MagicNumber=123123;
input int      DeviationPoints=20;
input int      PollSeconds=15;
input bool     ManageOnlyOwnMagic=true;

string TfName(const ENUM_TIMEFRAMES tf)
  {
   switch(tf)
     {
      case PERIOD_M1: return "M1"; case PERIOD_M5: return "M5"; case PERIOD_M15: return "M15";
      case PERIOD_H1: return "H1"; case PERIOD_H4: return "H4"; case PERIOD_D1: return "D1";
     }
   return "M15";
  }

string JsonEscape(const string value)
  {
   string out=value; StringReplace(out,"\\","\\\\"); StringReplace(out,"\"","\\\""); return out;
  }

string RatesJson(const ENUM_TIMEFRAMES tf)
  {
   MqlRates rates[]; ArraySetAsSeries(rates,false);
   int copied=CopyRates(_Symbol,tf,0,BarsToSend,rates);
   if(copied<50) return "[]";
   string body="[";
   for(int i=0;i<copied;i++)
     {
      if(i>0) body+=",";
      body+=StringFormat("{\"open\":%.10f,\"high\":%.10f,\"low\":%.10f,\"close\":%.10f}",rates[i].open,rates[i].high,rates[i].low,rates[i].close);
     }
   body+="]"; return body;
  }

string BuildPayload()
  {
   return StringFormat("{\"symbol\":\"%s\",\"structure_timeframe\":\"%s\",\"analysis_timeframe\":\"%s\",\"trigger_timeframe\":\"%s\",\"candles\":{\"%s\":%s,\"%s\":%s,\"%s\":%s}}",
                       JsonEscape(_Symbol),TfName(StructureTimeframe),TfName(AnalysisTimeframe),TfName(TriggerTimeframe),
                       TfName(StructureTimeframe),RatesJson(StructureTimeframe),TfName(AnalysisTimeframe),RatesJson(AnalysisTimeframe),TfName(TriggerTimeframe),RatesJson(TriggerTimeframe));
  }

bool RequestSignal(string &response)
  {
   if(StringLen(WebhookSecret)==0) return false;
   string url=ServerURL+"/mt5/signal";
   string headers="Content-Type: application/json\r\nX-Webhook-Secret: "+WebhookSecret+"\r\n";
   string payload_text=BuildPayload(); char payload[]; int size=StringToCharArray(payload_text,payload,0,WHOLE_ARRAY,CP_UTF8); if(size>0) size--;
   char result[]; string result_headers;
   ResetLastError(); int code=WebRequest("POST",url,headers,5000,payload,size,result,result_headers);
   if(code!=200) { PrintFormat("Pattern123 signal request failed: http=%d error=%d",code,GetLastError()); return false; }
   response=CharArrayToString(result,0,-1,CP_UTF8); return StringLen(response)>0;
  }

string Field(const string json,const string key)
  {
   string token="\""+key+"\":"; int p=StringFind(json,token); if(p<0) return ""; p+=StringLen(token);
   while(p<StringLen(json) && (StringGetCharacter(json,p)==' ' || StringGetCharacter(json,p)=='\"')) p++;
   int end=p; bool quoted=(p>0 && StringGetCharacter(json,p-1)=='\"');
   while(end<StringLen(json))
     {
      ushort c=StringGetCharacter(json,end);
      if(quoted && c=='\"') break;
      if(!quoted && (c==',' || c=='}')) break;
      end++;
     }
   return StringSubstr(json,p,end-p);
  }

int OwnPositions()
  {
   int count=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
     {
      ulong ticket=PositionGetTicket(i); if(ticket==0 || !PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if(ManageOnlyOwnMagic && (ulong)PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      count++;
     }
   return count;
  }

double NormalizeVolume(double volume)
  {
   double minv=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN), maxv=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX), step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0) step=0.01; volume=MathMin(volume,maxv); volume=MathFloor(volume/step)*step; if(volume<minv) return 0.0; return NormalizeDouble(volume,2);
  }

double RiskVolume(const ENUM_ORDER_TYPE type,const double entry,const double sl)
  {
   if(RiskPercent<=0 || entry<=0 || sl<=0) return 0.0;
   double balance=AccountInfoDouble(ACCOUNT_BALANCE), risk_amount=balance*RiskPercent/100.0, loss=0.0;
   if(!OrderCalcProfit(type,_Symbol,1.0,entry,sl,loss)) return 0.0;
   if(MathAbs(loss)<1e-12) return 0.0;
   return NormalizeVolume(risk_amount/MathAbs(loss));
  }

bool HasNewBar()
  {
   static datetime last_bar=0; datetime current=iTime(_Symbol,TriggerTimeframe,0); if(current==0 || current==last_bar) return false; last_bar=current; return true;
  }

void EvaluateSignal()
  {
   if(Mode==MODE_MONITOR) return;
   string response; if(!RequestSignal(response)) return;
   string status=Field(response,"status"); if(status!="signal") return;
   string direction=Field(response,"direction"); double sl=StringToDouble(Field(response,"stop_loss")); double tp=StringToDouble(Field(response,"take_profit"));
   if(direction!="buy" && direction!="sell") return; if(sl<=0 || tp<=0) return; if(OwnPositions()>=MaxOpenPositions) return;
   if(Mode!=MODE_AUTO_TRADING) { PrintFormat("Pattern123 signal-only: %s SL=%f TP=%f",direction,sl,tp); return; }
   trade.SetExpertMagicNumber(MagicNumber); trade.SetDeviationInPoints(DeviationPoints);
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK), bid=SymbolInfoDouble(_Symbol,SYMBOL_BID); double entry=(direction=="buy"?ask:bid);
   if((direction=="buy" && (sl>=entry || tp<=entry)) || (direction=="sell" && (sl<=entry || tp>=entry))) return;
   double volume=RiskVolume(direction=="buy"?ORDER_TYPE_BUY:ORDER_TYPE_SELL,entry,sl); if(volume<=0) return;
   bool ok=(direction=="buy") ? trade.Buy(volume,_Symbol,0.0,sl,tp,"Pattern123") : trade.Sell(volume,_Symbol,0.0,sl,tp,"Pattern123");
   if(!ok) PrintFormat("Pattern123 order failed: retcode=%u %s",trade.ResultRetcode(),trade.ResultRetcodeDescription());
  }

int OnInit()
  {
   EventSetTimer(MathMax(PollSeconds,5)); trade.SetExpertMagicNumber(MagicNumber); return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { EventKillTimer(); }

void OnTick() { if(HasNewBar()) EvaluateSignal(); }
void OnTimer() { if(Mode!=MODE_MONITOR) EvaluateSignal(); }
