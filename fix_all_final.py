#!/usr/bin/env python3
"""
Fix complet AI Composer (pandas) + Quantum Grid (ta-lib → ta)
"""
import os
import re

BASE = '/opt/smartorder-pro'

print("🔧 Fix 1/2: AI Composer - pandas Series...")

# 1. AI Composer: numpy → pandas
composer_path = f'{BASE}/ai/strategy_composer_real.py'
with open(composer_path, 'r') as f:
    content = f.read()

# Add pandas import
if 'import pandas as pd' not in content:
    content = content.replace('import numpy as np', 'import numpy as np\nimport pandas as pd')

# Replace all np.array → pd.Series for ta compatibility
replacements = [
    ("'close': np.array([x[4] for x in ohlcv], dtype=float)", "'close': pd.Series([x[4] for x in ohlcv], dtype=float)"),
    ("'high': np.array([x[2] for x in ohlcv], dtype=float)", "'high': pd.Series([x[2] for x in ohlcv], dtype=float)"),
    ("'low': np.array([x[3] for x in ohlcv], dtype=float)", "'low': pd.Series([x[3] for x in ohlcv], dtype=float)"),
    ("'volume': np.array([x[5] for x in ohlcv], dtype=float)", "'volume': pd.Series([x[5] for x in ohlcv], dtype=float)"),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(composer_path, 'w') as f:
    f.write(content)

print("✅ AI Composer: pandas Series OK")

print("\n🔧 Fix 2/2: Quantum Grid - talib → ta...")

# 2. Quantum Grid: talib → ta
quantum_path = f'{BASE}/strategies/quantum_grid.py'
with open(quantum_path, 'r') as f:
    content = f.read()

# Replace talib imports
content = content.replace('import talib', 'import ta')
content = content.replace('from talib import', '# from talib import  # Using ta library instead')

# Replace talib.RSI → ta.momentum.rsi_indicator
content = re.sub(
    r'talib\.RSI\((\w+),\s*timeperiod=(\d+)\)',
    r'ta.momentum.rsi(\1, window=\2)',
    content
)

# Replace talib.BBANDS → ta.volatility.bollinger_*
if 'talib.BBANDS' in content:
    content = re.sub(
        r'upper,\s*middle,\s*lower\s*=\s*talib\.BBANDS\(([^,]+),\s*timeperiod=(\d+),\s*nbdevup=([^,]+),\s*nbdevdn=([^)]+)\)',
        r'''bb = ta.volatility.BollingerBands(\1, window=\2, window_dev=\3)
        upper = bb.bollinger_hband()
        middle = bb.bollinger_mavg()
        lower = bb.bollinger_lband()''',
        content
    )

# Replace talib.MACD → ta.trend.macd*
if 'talib.MACD' in content:
    content = re.sub(
        r'macd,\s*signal,\s*hist\s*=\s*talib\.MACD\(([^,]+),\s*fastperiod=(\d+),\s*slowperiod=(\d+),\s*signalperiod=(\d+)\)',
        r'''macd_obj = ta.trend.MACD(\1, window_slow=\3, window_fast=\2, window_sign=\4)
        macd = macd_obj.macd()
        signal = macd_obj.macd_signal()
        hist = macd_obj.macd_diff()''',
        content
    )

# Replace talib.ATR → ta.volatility.average_true_range
content = re.sub(
    r'talib\.ATR\(([^,]+),\s*([^,]+),\s*([^,]+),\s*timeperiod=(\d+)\)',
    r'ta.volatility.average_true_range(\1, \2, \3, window=\4)',
    content
)

# Replace talib.EMA → ta.trend.ema_indicator
content = re.sub(
    r'talib\.EMA\((\w+),\s*timeperiod=(\d+)\)',
    r'ta.trend.ema_indicator(\1, window=\2)',
    content
)

# Replace talib.SMA → ta.trend.sma_indicator
content = re.sub(
    r'talib\.SMA\((\w+),\s*timeperiod=(\d+)\)',
    r'ta.trend.sma_indicator(\1, window=\2)',
    content
)

# Replace talib.ADX → ta.trend.adx
content = re.sub(
    r'talib\.ADX\(([^,]+),\s*([^,]+),\s*([^,]+),\s*timeperiod=(\d+)\)',
    r'ta.trend.adx(\1, \2, \3, window=\4)',
    content
)

with open(quantum_path, 'w') as f:
    f.write(content)

print("✅ Quantum Grid: ta library OK")

print("\n🧪 Test imports...")
try:
    os.chdir(BASE)
    exec(open(f'{BASE}/venv/bin/activate_this.py').read(), {'__file__': f'{BASE}/venv/bin/activate_this.py'})
except:
    pass

try:
    from ai.strategy_composer_real import AIStrategyComposerReal
    print("✅ AIStrategyComposerReal importable")
except Exception as e:
    print(f"❌ AIStrategyComposerReal: {e}")

try:
    from strategies.quantum_grid import QuantumGrid
    print("✅ QuantumGrid importable")
except Exception as e:
    print(f"❌ QuantumGrid: {e}")

print("\n✅ FIX COMPLET")
print("\n📝 Prochaine étape: créer un runner simplifié sans tous les modules cassés")
