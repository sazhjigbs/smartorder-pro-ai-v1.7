#!/bin/bash
set -e

echo "🔧 Déploiement complet Quantum Grid..."

cd /opt/smartorder-pro

# 1. Fix AI Composer (pandas Series)
echo "📝 Fix AI Composer..."
python3 << 'EOF'
content = open('ai/strategy_composer_real.py').read()
if 'import pandas as pd' not in content:
    content = content.replace('import numpy as np', 'import numpy as np\nimport pandas as pd')
content = content.replace("'close': np.array([x[4] for x in ohlcv], dtype=float)", "'close': pd.Series([x[4] for x in ohlcv], dtype=float)")
content = content.replace("'high': np.array([x[2] for x in ohlcv], dtype=float)", "'high': pd.Series([x[2] for x in ohlcv], dtype=float)")
content = content.replace("'low': np.array([x[3] for x in ohlcv], dtype=float)", "'low': pd.Series([x[3] for x in ohlcv], dtype=float)")
content = content.replace("'volume': np.array([x[5] for x in ohlcv], dtype=float)", "'volume': pd.Series([x[5] for x in ohlcv], dtype=float)")
open('ai/strategy_composer_real.py', 'w').write(content)
print("✅ AI Composer fixed")
EOF

# 2. Fix quantum runner
echo "📝 Fix Quantum Runner..."
cat > /tmp/fix_runner.py << 'EOF'
with open('/opt/smartorder-pro/run_paper_quantum_pro.py', 'r') as f:
    content = f.read()

# Fix imports
content = content.replace('from core.risk_manager_advanced import AdvancedRiskManager', 'from core.risk_manager_advanced import RiskManagerAdvanced')

# Rebuild __init__ proprement
lines = content.split('\n')
new_lines = []
skip_mode = False

for i, line in enumerate(lines):
    # Skip old quantum grid init
    if 'self.quantum_grid = QuantumGrid(' in line and 'symbol=' in lines[i+1]:
        skip_mode = True
        new_lines.append('        # Stratégie Quantum Grid')
        new_lines.append('        from strategies.quantum_grid import QuantumGridConfig')
        new_lines.append('        config = QuantumGridConfig(')
        new_lines.append("            symbol='BTCUSDT',")
        new_lines.append('            initial_price=95000.0,')
        new_lines.append('            total_investment=5000.0,')
        new_lines.append('            grid_levels=20')
        new_lines.append('        )')
        new_lines.append('        self.quantum_grid = QuantumGrid(config)')
        continue
    
    if skip_mode:
        if ')' in line and 'investment' in ''.join(lines[max(0,i-5):i]):
            skip_mode = False
            continue
        else:
            continue
    
    # Remove trailing stop avec mauvais params
    if 'self.trailing_stop = TrailingStopManager(' in line:
        new_lines.append('        self.trailing_stop = TrailingStopManager()')
        # Skip les lignes suivantes jusqu'au )
        for j in range(i+1, len(lines)):
            if ')' in lines[j]:
                break
        continue
    
    # Skip activation_price_distance line
    if 'activation_price_distance' in line or 'callback_rate' in line:
        continue
    
    new_lines.append(line)

with open('/opt/smartorder-pro/run_paper_quantum_pro.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Runner fixed")
EOF

python3 /tmp/fix_runner.py

# 3. Install deps
echo "📦 Vérification dépendances..."
source venv/bin/activate
pip install -q ccxt ta pandas numpy 2>/dev/null || true

# 4. Test import
echo "🧪 Test imports..."
python3 << 'EOF'
from ai.strategy_composer_real import AIStrategyComposerReal
from strategies.quantum_grid import QuantumGrid, QuantumGridConfig
from core.paper_trading_engine import PaperTradingEngine
from core.risk_manager_advanced import RiskManagerAdvanced
from core.trailing_stop_manager import TrailingStopManager
print("✅ All imports OK")
EOF

# 5. Kill old processes
echo "🛑 Stop anciens processus..."
pkill -f run_paper_quantum || true
sleep 2

# 6. Start bot
echo "🚀 Lancement Quantum Grid Bot..."
nohup python3 run_paper_quantum_pro.py > logs/quantum_live.log 2>&1 &
BOT_PID=$!

sleep 5

# 7. Verify
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Bot lancé avec succès (PID: $BOT_PID)"
    echo ""
    echo "📊 Logs en temps réel:"
    tail -30 logs/quantum_live.log
    echo ""
    echo "📝 Pour suivre les logs: tail -f /opt/smartorder-pro/logs/quantum_live.log"
else
    echo "❌ Erreur au démarrage:"
    tail -50 logs/quantum_live.log
    exit 1
fi
