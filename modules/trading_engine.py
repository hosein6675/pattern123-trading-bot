from modules.structure import StructureAnalyzer
from modules.price_action import PriceActionEngine
from modules.macd_engine import MACDEngine
from modules.risk_manager import RiskManager
from modules.journal import JournalEngine
from modules.account_manager import AccountManager
from modules.market_context import MarketContextAnalyzer
from modules.news_filter import NewsFilter
from modules.order_manager import OrderManager
from modules.market_data import MarketDataEngine
from modules.decision_engine import DecisionEngine
from modules.config import active_config
from modules.strategy_engine import StrategyEngine


class TradingEngine:
    def __init__(self):
        self.context = MarketContextAnalyzer()
        self.structure = StructureAnalyzer()
        self.price_action = PriceActionEngine()
        self.macd = MACDEngine()
        self.risk = RiskManager()
        self.journal = JournalEngine()
        self.account = AccountManager()
        self.news = NewsFilter()
        self.orders = OrderManager()
        self.market_data = MarketDataEngine()
        self.decision = DecisionEngine()
        self.strategy = StrategyEngine()

    def _sync_account(self):
        snapshot = self.orders.account_info()
        self.account.sync_from_broker(snapshot)
        return self.account.get_account()

    def analyze_market(self, symbol, timeframe=None, candles=None):
        timeframe = (timeframe or active_config.timeframe).upper()
        symbol = str(symbol).upper()
        account = self._sync_account()

        if not active_config.is_symbol_allowed(symbol):
            return self.no_trade(symbol, timeframe, account, "Symbol not allowed")
        if timeframe not in ("M1", "M5", "M15", "H1", "H4", "D1"):
            return self.no_trade(symbol, timeframe, account, "Unsupported timeframe")

        if candles is None:
            market = self.market_data.get_candles(symbol, timeframe, days=200)
            if not market or market.get("status") != "ready":
                return self.no_trade(symbol, timeframe, account, "Market data unavailable")
            candles = market.get("candles", [])
        if not candles:
            return self.no_trade(symbol, timeframe, account, "No candles available")
        if len(candles) < 50:
            return self.no_trade(symbol, timeframe, account, "Not enough candles")

        news = self.news.check_news(symbol)
        if news is not None and not getattr(news, "allow_trade", True):
            return self.no_trade(symbol, timeframe, account, "News blocked trade")

        context = self.context.analyze(candles, symbol)
        if context is None:
            return self.no_trade(symbol, timeframe, account, "Market context unavailable")
        structure = self.structure.analyze(candles)
        if structure is None:
            return self.no_trade(symbol, timeframe, account, "Market structure unavailable")
        price_action = self.price_action.analyze(structure, candles)
        if price_action is None:
            return self.no_trade(symbol, timeframe, account, "Price action unavailable")
        macd = self.macd.analyze(candles)
        if macd is None:
            return self.no_trade(symbol, timeframe, account, "MACD unavailable")

        strategy_result = self.strategy.evaluate(
            structure=structure,
            price_action=price_action,
            macd=macd,
            market_context=context,
            timeframe=timeframe,
        )
        if strategy_result is None or not getattr(strategy_result, "approved", False):
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "strategy_rejected",
                "account": account,
                "market_context": context,
                "structure": structure,
                "price_action": price_action,
                "macd": macd,
                "strategy": strategy_result,
                "news": news,
                "decision": "NO_TRADE",
                "open_positions": len(self.get_open_positions()),
            }

        decision = self.decision.analyze(
            structure=structure,
            price_action=price_action,
            macd=macd,
            market_context=context,
            news=news,
        )
        if decision is None:
            return self.no_trade(symbol, timeframe, account, "Decision engine failed")

        positions = self.get_open_positions()
        entry = float(getattr(price_action, "entry", 0) or 0)
        stop_loss = float(getattr(price_action, "stop_loss", 0) or 0)
        direction = getattr(decision, "direction", "none")
        risk_per_lot = self.orders.risk_per_lot(symbol, direction, entry, stop_loss) if direction in ("buy", "sell") else 0.0
        risk = self.risk.check(
            balance=account.balance,
            equity=account.equity,
            entry=entry,
            stop_loss=stop_loss,
            quality=getattr(decision, "quality", 0),
            open_positions=len(positions),
            risk_per_lot=risk_per_lot,
            total_risk_percent=self._total_open_risk_percent(account.balance, positions),
        )
        final_decision = self.decision.analyze(
            structure=structure,
            price_action=price_action,
            macd=macd,
            market_context=context,
            news=news,
            risk=risk,
        )
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "analysis_complete",
            "account": account,
            "market_context": context,
            "structure": structure,
            "price_action": price_action,
            "macd": macd,
            "strategy": strategy_result,
            "news": news,
            "risk": risk,
            "decision": final_decision,
            "open_positions": len(positions),
        }

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
        symbol = str(symbol).upper()
        direction = str(direction).lower()
        try:
            volume = float(volume)
            stop_loss = float(stop_loss)
            take_profit = float(take_profit)
        except (TypeError, ValueError):
            return {"success": False, "message": "Invalid numeric order parameters"}
        if direction not in ("buy", "sell") or volume <= 0:
            return {"success": False, "message": "Invalid order parameters"}
        if not active_config.is_symbol_allowed(symbol):
            return {"success": False, "message": "Symbol not allowed"}
        if stop_loss <= 0 or take_profit <= 0:
            return {"success": False, "message": "Stop loss and take profit are required"}

        account = self._sync_account()
        positions = self.get_open_positions()
        price = self.orders.broker.current_price(symbol) if hasattr(self.orders, "broker") else {}
        entry = price.get("ask" if direction == "buy" else "bid") if isinstance(price, dict) else None
        if entry is None:
            return {"success": False, "message": "Broker price unavailable"}
        entry = float(entry)
        if (direction == "buy" and stop_loss >= entry) or (direction == "sell" and stop_loss <= entry):
            return {"success": False, "message": "Stop loss is on the wrong side of entry"}
        if (direction == "buy" and take_profit <= entry) or (direction == "sell" and take_profit >= entry):
            return {"success": False, "message": "Take profit is on the wrong side of entry"}

        contract = self.orders.broker.contract(symbol) if hasattr(self.orders, "broker") else {}
        risk_per_lot = self.orders.risk_per_lot(symbol, direction, entry, stop_loss)
        risk = self.risk.check(
            balance=account.balance,
            equity=account.equity,
            entry=entry,
            stop_loss=stop_loss,
            quality=100,
            open_positions=len(positions),
            risk_per_lot=risk_per_lot,
            total_risk_percent=self._total_open_risk_percent(account.balance, positions),
            min_lot=contract.get("volume_min") if isinstance(contract, dict) else None,
            max_lot=contract.get("volume_max") if isinstance(contract, dict) else None,
            lot_step=contract.get("volume_step") if isinstance(contract, dict) else None,
        )
        if not risk.allowed:
            return {"success": False, "message": risk.message, "risk": risk}
        if volume > risk.lot_size + 1e-12:
            return {"success": False, "message": "Requested volume exceeds risk-approved size", "approved_volume": risk.lot_size, "risk": risk}
        return self.orders.execute_trade(symbol, direction, volume, stop_loss, take_profit)

    def close_order(self, order_id):
        if not order_id:
            return {"success": False, "message": "Invalid order id"}
        return self.orders.close_trade(order_id)

    def get_open_positions(self):
        positions = self.orders.get_open_positions()
        return positions if positions else []

    def no_trade(self, symbol, timeframe, account, reason):
        return {"symbol": symbol, "timeframe": timeframe, "status": "rejected", "reason": reason, "account": account, "decision": "NO_TRADE"}
