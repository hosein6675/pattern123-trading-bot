def __init__(self):
    self.engine = TradingEngine()

def get_status(self):
    return {
        "market": active_config.market,
        "symbol": active_config.symbol,
        "timeframe": active_config.timeframe,
        "mode": active_config.mode,
    }

def analyze(self, candles):
    return self.engine.analyze_market(
        active_config.symbol,
        active_config.timeframe,
        candles,
    )
