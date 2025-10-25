#!/bin/bash
echo "============================================================="
echo "🔍 SAFELOGIC SMARTORDER PRO — DIAGNOSTIC GLOBAL v1.8-FINAL"
echo "Date : $(date)"
echo "============================================================="

# === 1️⃣  Vérifie les services ===
echo -e "\n🟦 [1] ÉTAT DES SERVICES"
systemctl status smartorder-websync-bridge.service --no-pager | head -n 12
systemctl status smartorder-portal-v5.service --no-pager | head -n 12

# === 2️⃣  Vérifie les processus Python actifs ===
echo -e "\n🟩 [2] PROCESSUS ACTIFS"
ps aux | grep -E 'websync_bridge|portal_v5_pro' | grep -v grep

# === 3️⃣  Ports en écoute ===
echo -e "\n🟨 [3] PORTS EN ÉCOUTE"
ss -tulnp | grep -E '8555|python' || echo "Aucun port actif pour le portail"

# === 4️⃣  Journal des erreurs du Bridge ===
echo -e "\n🟥 [4] DERNIÈRES ERREURS DU BRIDGE"
tail -n 20 /opt/smartorder-pro/logs/websync_bridge.log 2>/dev/null || echo "Journal introuvable"

# === 5️⃣  Vérifie la connectivité Bybit ===
echo -e "\n🟪 [5] TEST CONNEXION BYBIT"
ping -c 2 stream.bybit.com || echo "⚠️  DNS ou réseau Bybit inaccessible"
echo -e "\nTentative d'ouverture WebSocket rapide..."
/opt/smartorder-pro/venv/bin/python3 - <<'PY'
import asyncio, websockets, json
async def test():
    try:
        async with websockets.connect("wss://stream.bybit.com/v5/public/linear") as ws:
            await ws.send(json.dumps({"op":"ping"}))
            print("✅ WebSocket Bybit accessible ✅")
    except Exception as e:
        print(f"❌ Erreur WebSocket :", e)
asyncio.run(test())
PY

# === 6️⃣  Vérifie le statut du portail ===
echo -e "\n🟦 [6] STATUT DU PORTAIL API"
curl -s http://127.0.0.1:8555/api/unified || echo "❌ Portail inactif"

# === 7️⃣  Utilisation CPU/RAM ===
echo -e "\n🟫 [7] RESSOURCES VPS"
echo "CPU : $(top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}')% | RAM : $(free -m | awk '/Mem/{printf(\"%s/%s MB\", $3,$2)}')"

# === 8️⃣  Informations système ===
echo -e "\n🟩 [8] INFO SYSTÈME"
hostnamectl | grep -E 'Operating|Kernel|Architecture'
echo "-------------------------------------------------------------"
echo "Diagnostic complet terminé ✅"
