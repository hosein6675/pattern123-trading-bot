from dataclasses import dataclass, field


@dataclass
class StrategyConfig:


    # =====================================
    # نام استراتژی
    # =====================================

    name: str = "Pattern123 Advanced"


    # =====================================
    # تایم فریم های مجاز
    # =====================================

    allowed_timeframes: list = field(
        default_factory=lambda: [
            "M15",
            "H1",
            "H4"
        ]
    )


    # =====================================
    # فیلتر ساختار بازار
    # =====================================

    require_structure: bool = True

    minimum_structure_quality: int = 60

    allow_range_market: bool = False



    # =====================================
    # Price Action
    # =====================================

    require_pattern_confirmation: bool = True

    minimum_price_action_confidence: int = 60

    require_engulfing: bool = True



    # =====================================
    # MACD
    # =====================================

    use_macd_filter: bool = True

    minimum_macd_score: int = 50

    require_macd_momentum: bool = True



    # =====================================
    # امتیاز نهایی ورود
    # =====================================

    minimum_trade_quality: int = 70

    minimum_trade_confidence: int = 70



    # =====================================
    # مدیریت معامله
    # =====================================

    risk_reward_ratio: float = 3.0

    use_multiple_targets: bool = True

    close_partial_positions: bool = True



    # =====================================
    # سشن های معاملاتی
    # =====================================

    trade_sessions: list = field(
        default_factory=lambda: [
            "London",
            "NewYork"
        ]
    )


    avoid_sessions: list = field(
        default_factory=lambda: []
    )



    # =====================================
    # کنترل هوشمند
    # =====================================

    adaptive_mode: bool = True

    allow_journal_learning: bool = True

    allow_strategy_update: bool = False



    # =====================================
    # توضیحات
    # =====================================

    description: str = (
        "Pattern123 + Structure + Price Action + MACD strategy configuration"
    )



# نمونه فعال استراتژی

active_strategy = StrategyConfig()
