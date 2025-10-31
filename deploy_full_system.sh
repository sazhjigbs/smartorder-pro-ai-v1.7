#!/bin/bash

echo "=================================="
echo "DÉPLOIEMENT SYSTÈME COMPLET"
echo "Test TOUS modes en PAPER"
echo "=================================="

# 1. Arrêter tous les anciens processus
echo "🛑 Arrêt des anciens processus..."
pkill -f "python.*trading" 2>/dev/null
pkill -f "python.*api" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
sleep 2

# 2. Créer structure dossiers
echo "📁 Création structure..."
mkdir -p /opt/smartorder-pro/{data,logs,backups}

# 3. Reset état initial
echo "🔄 Reset état initial..."
cat > /opt/smartorder-pro/data/trading_state.json << 'EOF'
{
  "mode": "PAPER",
  "current_capital": 10000,
  "total_pnl": 0,
  "active_strategies": [
    "Grid Trading",
    "DCA Strategy",
    "Scalping"
  ],
  "positions": [],
  "last_update": "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
}
EOF

# 4. Copier fichiers
echo "📦 Déploiement fichiers..."
cp ~/smartorder-pro-ai-v1.7/test_all_modes.py /opt/smartorder-pro/
cp ~/smartorder-pro-ai-v1.7/backend_api_full.py /opt/smartorder-pro/
chmod +x /opt/smartorder-pro/*.py

# 5. Lancer API Backend
echo "🚀 Lancement API Backend..."
cd /opt/smartorder-pro
nohup python3 backend_api_full.py > logs/api.log 2>&1 &
API_PID=$!
echo "API Backend lancée (PID: $API_PID)"
sleep 3

# 6. Vérifier API
echo "🔍 Vérification API..."
if curl -s http://localhost:8001/health | grep -q "ok"; then
    echo "✅ API Backend fonctionnelle"
else
    echo "❌ API Backend non accessible"
    cat logs/api.log | tail -n 20
fi

# 7. Lancer bot test tous modes
echo "🤖 Lancement bot test complet..."
nohup python3 test_all_modes.py > logs/test_all_modes.log 2>&1 &
BOT_PID=$!
echo "Bot test lancé (PID: $BOT_PID)"
sleep 3

# 8. Afficher statut
echo ""
echo "=================================="
echo "✅ SYSTÈME DÉPLOYÉ"
echo "=================================="
echo "API Backend: PID $API_PID"
echo "Bot Test: PID $BOT_PID"
echo ""
echo "📊 URLs:"
echo "  - Dashboard: https://107.189.22.255/dashboard"
echo "  - API: http://107.189.22.255:8001/api/state"
echo "  - Health: http://107.189.22.255:8001/health"
echo ""
echo "📝 Logs:"
echo "  - API: tail -f /opt/smartorder-pro/logs/api.log"
echo "  - Bot: tail -f /opt/smartorder-pro/logs/test_all_modes.log"
echo ""
echo "🔍 Processus actifs:"
ps aux | grep -E "(backend_api_full|test_all_modes)" | grep -v grep

echo ""
echo "=================================="
echo "🧪 TEST INITIAL"
echo "=================================="

# Attendre 10 secondes
sleep 10

# Tester API
echo "Test /api/state:"
curl -s http://localhost:8001/api/state | python3 -m json.tool | head -n 15

echo ""
echo "Test /api/exchanges:"
curl -s http://localhost:8001/api/exchanges | python3 -m json.tool

echo ""
echo "Test /api/modes:"
curl -s http://localhost:8001/api/modes | python3 -m json.tool

echo ""
echo "=================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=================================="
echo ""
echo "Le système teste TOUS les modes en PAPER:"
echo "  - SPOT"
echo "  - FUTURES"
echo "  - HYBRIDE"
echo "  - MANUEL"
echo ""
echo "Avec toutes les stratégies:"
echo "  - Grid Trading"
echo "  - DCA Strategy"
echo "  - Scalping"
echo "  - Trend Following"
echo ""
echo "Rafraîchis le dashboard avec Ctrl+Shift+R"
echo "et vérifie les données en temps réel !"
