from dataclasses import dataclass, field


@dataclass
class StrategyConfig:
    name: str = "Pattern123 Advanced"
    allowed_timeframes: list = field(default_factory=lambda: ["M15", "H1", "H4"])
    require_structure: bool = True
    minimum_structure_quality: int = 60
    allow_range_market: bool = False
    require_pattern_confirmation: bool = True
    minimum_price_action_confidence: int = 60
    require_engulfing: bool = True
    use_macd_filter: bool = True
    minimum_macd_score: int = 50
    require_macd_momentum: bool = True
    require_trendline_fan: bool = True
    minimum_trendline_score: int = 20
    minimum_trade_quality: int = 70
    minimum_trade_confidence: int = 70
    risk_reward_ratio: float = 3.0
    use_multiple_targets: bool = True
    close_partial_positions: bool = True
    trade_sessions: list = field(default_factory=lambda: ["London", "NewYork"])
    avoid_sessions: list = field(default_factory=list)
    adaptive_mode: bool = True
    allow_journal_learning: bool = True
    allow_strategy_update: bool = False
    description: str = "Pattern123 + Structure + Price Action + Trendline Fan + MACD strategy configuration"


active_strategy = StrategyConfig()
