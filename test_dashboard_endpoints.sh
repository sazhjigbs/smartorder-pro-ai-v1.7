#!/bin/bash

echo "========================================="
echo "DASHBOARD v3.0 FINAL - TESTS ENDPOINTS"
echo "========================================="
echo ""

API="http://localhost:8091"

echo "1. TEST EXCHANGE TOGGLE"
echo "-----------------------"
curl -s -X POST $API/api/exchanges/simple-toggle \
  -H "Content-Type: application/json" \
  -d '{"exchange":"binance","action":"enable"}' | jq -c '{status, exchange, enabled}'
echo ""

echo "2. TEST STRATEGY TOGGLE"
echo "-----------------------"
curl -s -X POST $API/api/strategies/simple-toggle \
  -H "Content-Type: application/json" \
  -d '{"strategy":"scalping_ai","action":"enable"}' | jq -c '{status, strategy, enabled}'
echo ""

echo "3. TEST POSITIONS FILTERING"
echo "---------------------------"
echo "Spot:" $(curl -s "$API/api/positions?mode=spot" | jq 'length')
echo "Futures:" $(curl -s "$API/api/positions?mode=futures" | jq 'length')
echo "All:" $(curl -s "$API/api/positions" | jq 'length')
echo ""

echo "4. TEST WATCHLIST"
echo "-----------------"
curl -s $API/api/watchlist | jq 'length, .[0].symbol, .[0].change_24h'
echo ""

echo "5. TEST RISK MANAGER"
echo "--------------------"
curl -s $API/api/risk/status | jq -c '{reliability_score, current_mode, auto_mode}'
echo ""

echo "6. TEST ALL MAIN ENDPOINTS"
echo "--------------------------"
echo "Wallet:" $(curl -s $API/api/wallet | jq -c '{balance: .balance_usdt, pnl: .total_pnl}')
echo "Exchanges:" $(curl -s $API/api/exchanges | jq 'length')
echo "Strategies:" $(curl -s $API/api/strategies | jq '.strategies | length')
echo "Market Regime:" $(curl -s $API/api/market-regime | jq -c '{regime, volatility, ai_confidence}')
echo "PnL:" $(curl -s $API/api/pnl | jq -c '{total, daily}')
echo ""

echo "========================================="
echo "TESTS COMPLETED"
echo "========================================="
