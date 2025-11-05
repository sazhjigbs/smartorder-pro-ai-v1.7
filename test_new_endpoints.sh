#!/bin/bash

API="http://localhost:8091"

echo "==========================================="
echo "TESTS ENDPOINTS STRATEGIES + AUTO AI"
echo "==========================================="
echo ""

echo "1. /api/strategies (14 total)"
echo "-------------------------------"
curl -s $API/api/strategies | jq '{count, total, spot: ([.strategies[] | select(.type == "SPOT")] | length), futures: ([.strategies[] | select(.type == "FUTURES")] | length), hybrid: ([.strategies[] | select(.type == "HYBRID")] | length)}'
echo ""

echo "2. /api/strategies?mode=futures (6)"
echo "-------------------------------"
curl -s "$API/api/strategies?mode=futures" | jq '{count, ids: [.strategies[].id]}'
echo ""

echo "3. /api/modes/status"
echo "-------------------------------"
curl -s $API/api/modes/status | jq
echo ""

echo "4. /api/modes/auto-select (SPOT ≥70)"
echo "-------------------------------"
curl -s -X POST $API/api/modes/auto-select \
  -H "Content-Type: application/json" \
  -d '{"type":"spot","threshold":70}' | jq
echo ""

echo "5. Vérifier stratégies Spot après auto-select"
echo "-------------------------------"
curl -s "$API/api/strategies?mode=spot" | jq '[.strategies[] | {id, score, enabled}]' | head -20
echo ""

echo "6. /api/modes/auto-select (FUTURES ≥75)"
echo "-------------------------------"
curl -s -X POST $API/api/modes/auto-select \
  -H "Content-Type: application/json" \
  -d '{"type":"futures","threshold":75}' | jq
echo ""

echo "==========================================="
echo "TESTS TERMINÉS"
echo "==========================================="
