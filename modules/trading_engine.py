from modules.structure import StructureAnalyzer
from modules.price_action import PriceActionEngine
from modules.macd_engine import MACDEngine
from modules.risk_manager import RiskManager
from modules.money_management import MoneyManagement
from modules.journal import JournalEngine
from modules.account_manager import AccountManager
from modules.market_context import MarketContextAnalyzer
from modules.news_filter import NewsFilter
from modules.order_manager import OrderManager
from modules.market_data import MarketDataEngine
from modules.decision_engine import DecisionEngine
from modules.config import active_config
from modules.strategy_engine import StrategyEngine
from modules.trendline_fan import TrendlineFanAnalyzer
from modules.trigger_engine import TriggerEngine
from modules.trigger_engine import TriggerEngine
from modules.live_market_data import TIMEFRAME_OPTIONS


class TradingEngine:
    def __init__(self):
        self.context = MarketContextAnalyzer()
        self.structure = StructureAnalyzer()
        self.price_action = PriceActionEngine()
        self.macd = MACDEngine()
        self.risk = RiskManager()
        self.money = MoneyManagement(self.risk)
        self.journal = JournalEngine()
        self.account = AccountManager()
        self.news = NewsFilter()
        self.orders = OrderManager()
        self.market_data = MarketDataEngine()
        self.decision = DecisionEngine()
        self.strategy = StrategyEngine()
        self.trendline_fan = TrendlineFanAnalyzer()
        self.trigger = TriggerEngine()
        self.trigger = TriggerEngine()

    def _sync_account(self):
        snapshot = self.orders.account_info()
        self.account.sync_from_broker(snapshot)
        return self.account.get_account()

    def analyze_market(self, symbol, timeframe=None, candles=None, structure_timeframe=None, trigger_timeframe=None):
        timeframe = (timeframe or active_config.timeframe).upper()
        symbol = str(symbol).upper()
        account = self._sync_account()
        if not active_config.is_symbol_allowed(symbol):
            return self.no_trade(symbol, timeframe, account, "Symbol not allowed")
        if timeframe not in TIMEFRAME_OPTIONS:
            return self.no_trade(symbol, timeframe, account, "Unsupported timeframe")

        structure_timeframe = (structure_timeframe or timeframe).upper()
        trigger_timeframe = (trigger_timeframe or timeframe).upper()
        for requested in (structure_timeframe, trigger_timeframe):
            if requested not in TIMEFRAME_OPTIONS:
                return self.no_trade(symbol, timeframe, account, f"Unsupported timeframe: {requested}")

        # Each requested timeframe is independently sourced from MT5.
        markets = {}
        requested_timeframes = {timeframe, structure_timeframe, trigger_timeframe}
        for requested_tf in requested_timeframes:
            if requested_tf == timeframe and candles is not None and active_config.mode != "live":
                markets[requested_tf] = {"status": "ready", "candles": candles, "source": "caller", "demo_mode": False}
            else:
                markets[requested_tf] = self.market_data.get_candles(symbol, requested_tf, days=200)

        for requested_tf, layer_market in markets.items():
            if not layer_market or layer_market.get("status") != "ready":
                return self.no_trade(
                    symbol, timeframe, account,
                    layer_market.get("message", f"MT5 market data unavailable for {requested_tf}")
                    if isinstance(layer_market, dict) else f"Market data unavailable for {requested_tf}",
                )
            if active_config.mode == "live" and (
                layer_market.get("source") != "mt5" or layer_market.get("demo_mode") is not False
            ):
                return self.no_trade(symbol, timeframe, account, f"Live analysis requires MT5 data for {requested_tf}")
            if len(layer_market.get("candles", [])) < 50:
                return self.no_trade(symbol, timeframe, account, f"Not enough market candles for {requested_tf}")

        market = markets[timeframe]
        candles = market.get("candles", [])
        structure_candles = markets[structure_timeframe].get("candles", [])
        trigger_candles = markets[trigger_timeframe].get("candles", [])

        news = self.news.check_news(symbol)
        if news is not None and not getattr(news, "allow_trade", True):
            return self.no_trade(symbol, timeframe, account, "News blocked trade")

        context = self.context.analyze(candles, symbol)
        structure = self.structure.analyze(structure_candles)
        price_action = self.price_action.analyze(structure, candles)
        macd = self.macd.analyze(candles)
        trendline_fan = self.trendline_fan.analyze(structure, structure_candles)

        strategy_result = self.strategy.evaluate(
            structure=structure,
            price_action=price_action,
            macd=macd,
            market_context=context,
            trendline_fan=trendline_fan,
            timeframe=timeframe,
        )
        trigger_macd = self.macd.analyze(trigger_candles)
        trigger_result = self.trigger.evaluate(
            strategy=strategy_result,
            price_action=price_action,
            macd=trigger_macd,
            trendline_fan=trendline_fan,
            candles=trigger_candles,
        )
        if trigger_result.status != "READY":
            return {
                "symbol": symbol, "timeframe": timeframe, "status": "analysis_complete",
                "structure_timeframe": structure_timeframe, "trigger_timeframe": trigger_timeframe,
                "account": account, "market_context": context, "structure": structure,
                "price_action": price_action, "macd": macd, "trigger_macd": trigger_macd,
                "trendline_fan": trendline_fan, "strategy": strategy_result,
                "trigger": trigger_result, "news": news, "risk": None, "decision": "NO_TRADE",
                "market_source": market.get("source"), "market_time": market.get("live_tick_time"),
                "open_positions": len(self.get_open_positions()),
            }

        if not strategy_result.approved:
            return {
                "symbol": symbol, "timeframe": timeframe, "status": "strategy_rejected",
                "account": account, "market_context": context, "structure": structure,
                "price_action": price_action, "macd": macd, "trendline_fan": trendline_fan,
                "strategy": strategy_result, "news": news, "decision": "NO_TRADE",
                "market_source": market.get("source"), "market_time": market.get("live_tick_time"),
                "open_positions": len(self.get_open_positions()),
            }

        trigger_result = self.trigger.evaluate(
            strategy=strategy_result,
            price_action=price_action,
            macd=macd,
            trendline_fan=trendline_fan,
            candles=candles,
        )
        if trigger_result.status != "READY":
            # Keep the complete analysis payload visible to Telegram/dashboard while
            # making the pre-execution gate fail closed. No order path may treat this
            # result as executable.
            return {
                "symbol": symbol, "timeframe": timeframe, "status": "analysis_complete",
                "account": account, "market_context": context, "structure": structure,
                "price_action": price_action, "macd": macd, "trendline_fan": trendline_fan,
                "strategy": strategy_result, "trigger": trigger_result, "news": news,
                "risk": None, "decision": "NO_TRADE", "market_source": market.get("source"),
                "market_time": market.get("live_tick_time"),
                "open_positions": len(self.get_open_positions()),
            }

        decision = self.decision.analyze(
            structure=structure, price_action=price_action, macd=macd,
            market_context=context, news=news,
        )
        positions = self.get_open_positions()
        entry = float(getattr(price_action, "entry", 0) or 0)
        stop_loss = float(getattr(price_action, "stop_loss", 0) or 0)
        direction = getattr(decision, "direction", "none")
        risk_per_lot = self.orders.risk_per_lot(symbol, direction, entry, stop_loss) if direction in ("buy", "sell") else 0.0
        risk = self.risk.check(
            balance=account.balance, equity=account.equity, entry=entry, stop_loss=stop_loss,
            quality=getattr(decision, "quality", 0), open_positions=len(positions),
            risk_per_lot=risk_per_lot,
            total_risk_percent=self._total_open_risk_percent(account.balance, positions),
        )
        final_decision = self.decision.analyze(
            structure=structure, price_action=price_action, macd=macd,
            market_context=context, news=news, risk=risk,
        )
        return {
            "symbol": symbol, "timeframe": timeframe, "status": "analysis_complete",
            "structure_timeframe": structure_timeframe, "trigger_timeframe": trigger_timeframe,
            "account": account, "market_context": context, "structure": structure,
            "price_action": price_action, "macd": macd, "trendline_fan": trendline_fan,
            "strategy": strategy_result, "trigger": trigger_result, "news": news, "risk": risk,
            "decision": final_decision, "market_source": market.get("source"),
            "market_time": market.get("live_tick_time"), "open_positions": len(positions),
        }

    def dashboard_snapshot(self, symbol=None, timeframe=None, candles=None):
        from modules.dashboard import snapshot
        return snapshot(self, symbol or active_config.symbol, timeframe or active_config.timeframe, candles)

    def _total_open_risk_percent(self, balance, positions):
        if balance <= 0:
            return 0.0
        total = 0.0
        for position in positions:
            try:
                volume = float(position.get("volume", 0))
                entry = float(position.get("price_open", 0))
                stop = float(position.get("sl", 0))
                if volume > 0 and entry > 0 and stop > 0:
                    total += abs(entry - stop) * volume / balance * 100.0
            except (AttributeError, TypeError, ValueError):
                continue
        return round(total, 4)

    def execute_order(self, symbol, direction, volume, stop_loss, take_profit):
        symbol = str(symbol).upper(); direction = str(direction).lower()
        try:
            volume, stop_loss, take_profit = float(volume), float(stop_loss), float(take_profit)
        except (TypeError, ValueError):
            return {"success": False, "message": "Invalid numeric order parameters"}
        if direction not in ("buy", "sell") or volume <= 0:
            return {"success": False, "message": "Invalid order parameters"}
        if not active_config.is_symbol_allowed(symbol):
            return {"success": False, "message": "Symbol not allowed"}
        if stop_loss <= 0 or take_profit <= 0:
            return {"success": False, "message": "Stop loss and take profit are required"}
        account = self._sync_account(); positions = self.get_open_positions()
        price = self.orders.broker.current_price(symbol) if hasattr(self.orders, "broker") else {}
        if not isinstance(price, dict) or price.get("status") != "ready":
            return {"success": False, "message": "Broker price unavailable"}
        entry = price.get("ask" if direction == "buy" else "bid")
        if entry is None:
            return {"success": False, "message": "Broker price unavailable"}
        entry = float(entry)
        if (direction == "buy" and stop_loss >= entry) or (direction == "sell" and stop_loss <= entry):
            return {"success": False, "message": "Stop loss is on the wrong side of entry"}
        if (direction == "buy" and take_profit <= entry) or (direction == "sell" and take_profit >= entry):
            return {"success": False, "message": "Take profit is on the wrong side of entry"}
        contract = self.orders.broker.contract(symbol) if hasattr(self.orders, "broker") else {}
        risk_per_lot = self.orders.risk_per_lot(symbol, direction, entry, stop_loss)
        plan = self.money.plan_order(
            balance=account.balance,
            equity=account.equity,
            entry=entry,
            stop_loss=stop_loss,
            requested_volume=volume,
            quality=100,
            open_positions=len(positions),
            total_risk_percent=self._total_open_risk_percent(account.balance, positions),
            risk_per_lot=risk_per_lot,
            min_lot=contract.get("volume_min") if isinstance(contract, dict) else None,
            max_lot=contract.get("volume_max") if isinstance(contract, dict) else None,
            lot_step=contract.get("volume_step") if isinstance(contract, dict) else None,
        )
        if not plan.approved:
            return {"success": False, "message": plan.message, "approved_volume": plan.approved_volume, "risk": plan.risk}
        return self.orders.execute_trade(symbol, direction, plan.approved_volume, stop_loss, take_profit)

    def close_order(self, order_id):
        if not order_id:
            return {"success": False, "message": "Invalid order id"}
        return self.orders.close_trade(order_id)

    def get_open_positions(self):
        positions = self.orders.get_open_positions()
        return positions if positions else []

    def no_trade(self, symbol, timeframe, account, reason):
        return {"symbol": symbol, "timeframe": timeframe, "status": "rejected", "reason": reason, "account": account, "decision": "NO_TRADE"}
