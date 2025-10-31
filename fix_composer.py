#!/usr/bin/env python3
import sys

with open('/opt/smartorder-pro/ai/strategy_composer_real.py', 'r') as f:
    content = f.read()

# Add pandas import if missing
if 'import pandas as pd' not in content:
    content = content.replace('import numpy as np', 'import numpy as np\nimport pandas as pd')

# Fix numpy arrays to pandas Series
content = content.replace(
    "'close': np.array([x[4] for x in ohlcv], dtype=float)",
    "'close': pd.Series([x[4] for x in ohlcv], dtype=float)"
)
content = content.replace(
    "'high': np.array([x[2] for x in ohlcv], dtype=float)",
    "'high': pd.Series([x[2] for x in ohlcv], dtype=float)"
)
content = content.replace(
    "'low': np.array([x[3] for x in ohlcv], dtype=float)",
    "'low': pd.Series([x[3] for x in ohlcv], dtype=float)"
)
content = content.replace(
    "'volume': np.array([x[5] for x in ohlcv], dtype=float)",
    "'volume': pd.Series([x[5] for x in ohlcv], dtype=float)"
)

with open('/opt/smartorder-pro/ai/strategy_composer_real.py', 'w') as f:
    f.write(content)

print('✅ AI Composer fixed successfully')
