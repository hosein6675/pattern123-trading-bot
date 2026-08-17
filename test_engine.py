"""Smoke test for the full TradingEngine import/initialization chain."""

import sys
import traceback


def main():
    print("=" * 60)
    print("TRADING ENGINE SMOKE TEST")
    print("=" * 60)

    try:
        print("[1/2] Importing TradingEngine...")
        from modules.trading_engine import TradingEngine
        print("[OK] TradingEngine imported successfully.")

        print("[2/2] Initializing TradingEngine...")
        engine = TradingEngine()
        print("[OK] TradingEngine initialized successfully.")

        print("=" * 60)
        print("TEST RESULT: PASS")
        print("All TradingEngine imports and initialization completed.")
        print("=" * 60)

        return 0

    except Exception as exc:
        print("=" * 60)
        print("TEST RESULT: FAIL")
        print("=" * 60)
        print(f"{type(exc).__name__}: {exc}")
        print()
        print("FULL TRACEBACK:")
        traceback.print_exc()
        print("=" * 60)

        return 1


if __name__ == "__main__":
    sys.exit(main())
