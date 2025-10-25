#!/bin/bash
echo "=============================================================="
echo "🧩 SAFELOGIC SMARTORDER PRO AI v1.8-FINAL — FULL ETA REPORT"
echo "Date : $(date)"
echo "=============================================================="

# 1️⃣ Services
echo -e "\n🔹 [1] Services SmartOrder"
for svc in smartorder-portal-v5 smartorder-websync-bridge smartorder-proxy smartorder-watchdog; do
    status=$(systemctl is-active $svc)
    printf "  %-30s : %s\n" "$svc" "$status"
done

# 2️⃣ Ports
echo -e "\n🔹 [2] Ports en écoute"
ss -tulnp | grep -E '8555|8787' || echo "Aucun port actif détecté."

# 3️⃣ Ressources
echo -e "\n🔹 [3] Ressources VPS"
CPU=$(top -bn1 | awk '/Cpu\(s\)/{print $2 + $4}')
RAM=$(free -m | awk '/Mem/{printf("%s/%s MB", $3,$2)}')
DISK=$(df -h / | awk 'NR==2{print $5}')
echo "CPU : ${CPU}% | RAM : ${RAM} | Disk : ${DISK}"

# 4️⃣ Flux Bridge
echo -e "\n🔹 [4] Flux WebSocket Bridge (10 dernières lignes)"
tail -n 10 /opt/smartorder-pro/logs/websync_bridge.log 2>/dev/null || echo "Journal introuvable."

# 5️⃣ Proxy
echo -e "\n🔹 [5] Proxy Status"
systemctl status smartorder-proxy.service --no-pager | grep "Active:"

# 6️⃣ Système
echo -e "\n🔹 [6] Infos Système"
hostnamectl | grep -E 'Operating|Kernel|Architecture'
echo "--------------------------------------------------------------"
echo "✅ Rapport complet généré avec succès."
