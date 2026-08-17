from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StructureResult:
    trend: str = "unknown"
    swing_highs: List[Dict[str, Any]] = field(default_factory=list)
    swing_lows: List[Dict[str, Any]] = field(default_factory=list)

    bos: bool = False
    choch: bool = False

    last_bos_level: float = 0.0
    last_choch_level: float = 0.0

    impulse_leg: Dict[str, Any] = field(default_factory=dict)
    correction_leg: Dict[str, Any] = field(default_factory=dict)

    structure_quality: int = 0
    market_state: str = "no_data"
    description: str = ""


class StructureAnalyzer:

    def __init__(self):
        pass

    def analyze(self, candles):
        """
        Base structure analyzer.

        This is intentionally a clean implementation.
        No dependency on the previous structure logic.
        """

        if not isinstance(candles, list):
            return self.empty_result("Invalid candles data")

        if len(candles) == 0:
            return self.empty_result("No candles")

        return StructureResult(
            trend="unknown",
            swing_highs=[],
            swing_lows=[],
            bos=False,
            choch=False,
            last_bos_level=0.0,
            last_choch_level=0.0,
            impulse_leg={},
            correction_leg={},
            structure_quality=0,
            market_state="no_data",
            description="Structure analyzer initialized",
        )

    def empty_result(self, reason):
        return StructureResult(
            trend="unknown",
            swing_highs=[],
            swing_lows=[],
            bos=False,
            choch=False,
            last_bos_level=0.0,
            last_choch_level=0.0,
            impulse_leg={},
            correction_leg={},
            structure_quality=0,
            market_state="no_data",
            description=reason,
        )
