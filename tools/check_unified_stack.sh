#!/bin/bash
echo "=============================================================="
echo "🧩 SAFELOGIC SMARTORDER PRO — Unified Stack Checker"
echo "Date : $(date)"
echo "=============================================================="

# Vérification services
echo -e "\n🔹 [1] Services SmartOrder"
for svc in smartorder-proxy smartorder-websync-bridge smartorder-portal-v5 smartorder-watchdog; do
  state=$(systemctl is-active $svc 2>/dev/null || echo "❌ absent")
  printf "  %-35s : %s\n" "$svc" "$state"
done

# Vérification ports
echo -e "\n🔹 [2] Ports actifs"
ss -tulnp | grep -E '8555|8787|8088|8090' || echo "Aucun port détecté."

# Vérification processus
echo -e "\n🔹 [3] Processus Python / NodeJS"
ps -ef | grep -E "python3|node" | grep -v grep | head -n 10

# Test Proxy local
echo -e "\n🔹 [4] Test du Proxy WebSocket local (ws://127.0.0.1:8787)"
if ss -tulnp | grep -q ":8787"; then
  echo "✅ Proxy NodeJS détecté sur le port 8787"
else
  echo "⚠️  Proxy NodeJS inactif — relancer : systemctl restart smartorder-proxy"
fi

# Test API Portal
echo -e "\n🔹 [5] Test API Portal (http://127.0.0.1:8555/api/unified)"
if curl -s http://127.0.0.1:8555/api/unified | grep -q "OK"; then
  echo "✅ API Portal répond correctement"
else
  echo "⚠️  API Portal ne répond pas ou endpoint manquant"
fi

# Vérification logs récents
echo -e "\n🔹 [6] Dernières lignes des logs"
for log in /opt/smartorder-pro/logs/*.log; do
  echo -e "\n📄 $log"
  tail -n 3 "$log" 2>/dev/null
done

# Vérification latence et ressources
echo -e "\n🔹 [7] Ressources VPS"
CPU=$(top -bn1 | awk '/Cpu\(s\)/{print $2 + $4}')
RAM=$(free -m | awk '/Mem/{printf("%s/%s MB (%.1f%%)", $3,$2,($3/$2)*100)}')
DISK=$(df -h / | awk 'NR==2{print $5}')
echo "CPU : ${CPU}% | RAM : ${RAM} | DISK : ${DISK}"

echo "--------------------------------------------------------------"
echo "✅ Rapport complet généré avec succès"
echo "📁 Fichier : /opt/smartorder-pro/tools/check_unified_stack.sh"
echo "=============================================================="
