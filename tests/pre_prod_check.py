import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n" + "=" * 60)
print("PRE-PRODUCTION VALIDATION")
print("=" * 60 + "\n")

checks_passed = 0
checks_failed = 0

# 1. Environment
print("1. Environment variables...")
if os.getenv('ACTIVE_EXCHANGE'):
    print("   [OK]")
    checks_passed += 1
else:
    print("   [FAIL]")
    checks_failed += 1

# 2. Config files
print("2. Config files...")
if Path('.env').exists() and Path('config/exchanges.json').exists():
    print("   [OK]")
    checks_passed += 1
else:
    print("   [FAIL]")
    checks_failed += 1

# 3. Exchanges
print("3. Exchanges...")
try:
    from core.unified_trading_manager import UnifiedTradingManager
    manager = UnifiedTradingManager()
    print(f"   [OK] {len(manager.connectors)} exchanges")
    checks_passed += 1
except Exception as e:
    print(f"   [FAIL] {e}")
    checks_failed += 1

# 4. Strategies
print("4. Strategies...")
try:
    from strategies.risk_manager import RiskManager
    risk = RiskManager()
    print("   [OK]")
    checks_passed += 1
except:
    print("   [FAIL]")
    checks_failed += 1

print("\n" + "=" * 60)
print(f"RESULTS: {checks_passed} OK, {checks_failed} FAIL")
print("=" * 60)

if checks_failed == 0:
    print("\nREADY FOR PRODUCTION!")
    sys.exit(0)
else:
    print("\nFIX ERRORS FIRST!")
    sys.exit(1)
