#!/bin/bash
echo '==================================================='
echo 'SMARTORDER PRO - RAPPORT DE VALIDATION COMPLET'
echo 'Date:' $(date)
echo '==================================================='
echo ''
echo '1. FICHIERS JSON SOURCES DE VÉRITÉ'
echo '-----------------------------------'
echo ''
echo '--- PnL Tracker ---'
cat /opt/smartorder-pro/config/pnl_tracker.json
echo ''
echo ''
echo '--- Paper Wallet ---'
cat /opt/smartorder-pro/config/paper_wallet.json
echo ''
echo ''
echo '--- Positions ---'
cat /opt/smartorder-pro/config/positions.json
echo ''
echo ''
echo '2. ENDPOINTS API (données retournées)'
echo '--------------------------------------'
echo ''
echo '--- /api/pnl ---'
curl -s http://localhost:8000/api/pnl
echo ''
echo ''
echo '--- /api/wallet ---'
curl -s http://localhost:8000/api/wallet
echo ''
echo ''
echo '--- /api/strategies (nombre) ---'
curl -s http://localhost:8000/api/strategies | grep -o '"id"' | wc -l
echo ' strategies total'
echo ''
echo ''
echo '3. SERVICES STATUS'
echo '------------------'
systemctl status smartorder-paper --no-pager -n 3 | grep -E 'Active:|Main PID:'
echo ''
systemctl status smartorder-api --no-pager -n 3 | grep -E 'Active:|Main PID:'
echo ''
echo ''
echo '4. LOGS RÉCENTS (last 10 lines each)'
echo '-------------------------------------'
echo ''
echo '--- Paper Trades (last 10) ---'
tail -n 10 /opt/smartorder-pro/logs/paper_trades.log 2>/dev/null || echo 'Non disponible'
echo ''
echo ''
echo '--- Last Signals ---'
cat /opt/smartorder-pro/config/last_signals.json
echo ''
echo ''
echo '5. COHÉRENCE API vs FICHIERS'
echo '-----------------------------'
API_PNL=$(curl -s http://localhost:8000/api/pnl | grep -o '"total_pnl": [0-9.]*' | grep -o '[0-9.]*')
FILE_PNL=$(grep -o '"total_pnl": [0-9.]*' /opt/smartorder-pro/config/pnl_tracker.json | grep -o '[0-9.]*')
echo "PnL API: $API_PNL"
echo "PnL File: $FILE_PNL"
if [ "$API_PNL" = "$FILE_PNL" ]; then
    echo "✅ PnL cohérent"
else
    echo "❌ PnL incohérent"
fi
echo ''
API_WALLET=$(curl -s http://localhost:8000/api/wallet | grep -o '"balance_usdt": [0-9.]*' | grep -o '[0-9.]*')
FILE_WALLET=$(grep -o '"balance_usdt": [0-9.]*' /opt/smartorder-pro/config/paper_wallet.json | grep -o '[0-9.]*')
echo "Wallet API: $API_WALLET"
echo "Wallet File: $FILE_WALLET"
if [ "$API_WALLET" = "$FILE_WALLET" ]; then
    echo "✅ Wallet cohérent"
else
    echo "❌ Wallet incohérent"
fi
echo ''
echo '==================================================='
echo 'FIN DU RAPPORT'
echo '==================================================='
