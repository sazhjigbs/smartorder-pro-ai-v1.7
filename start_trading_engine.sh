#!/bin/bash
# 🚀 Lancement du moteur de trading SmartOrder PRO

echo "=========================================="
echo "🚀 DÉMARRAGE MOTEUR DE TRADING"
echo "=========================================="

cd /opt/smartorder-pro

# Vérifier stratégies activées
echo ""
echo "📊 Stratégies activées:"
python3 << 'PYEOF'
import json
try:
    with open('/opt/smartorder-pro/config/strategies_state.json') as f:
        data = json.load(f)
        total = 0
        for mode in ['spot', 'futures', 'hybride']:
            enabled = [s['name'] for s in data.get(mode, []) if s.get('enabled')]
            if enabled:
                print(f"  {mode.upper()}: {len(enabled)} - {', '.join(enabled)}")
                total += len(enabled)
        print(f"\n  TOTAL: {total} stratégies actives")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
PYEOF

echo ""
echo "🔄 Lancement du bot..."

# Lancer le bot de trading
nohup python3 ultimate_trading_bot.py > logs/trading_engine.log 2>&1 &
TRADING_PID=$!

echo "✅ Moteur démarré (PID: $TRADING_PID)"
echo ""
echo "📋 Pour voir les logs:"
echo "   tail -f /opt/smartorder-pro/logs/trading_engine.log"
echo ""
echo "⚠️  IMPORTANT:"
echo "   Le bot exécutera les stratégies ENABLED en mode Paper Trading"
echo "   PnL sera mis à jour en temps réel sur le dashboard"
echo "=========================================="
