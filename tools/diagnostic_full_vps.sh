#!/bin/bash
echo "=============================================================="
echo "🧠 SAFELOGIC SMARTORDER PRO — DIAGNOSTIC GLOBAL UNIFIÉ"
echo "Date : $(date)"
echo "=============================================================="

# 1️⃣ Informations système
echo -e "\n🔹 [1] Infos Système"
hostnamectl | grep -E 'Operating|Kernel|Architecture'
uptime -p
echo "--------------------------------------------------------------"

# 2️⃣ Ressources VPS
echo -e "\n🔹 [2] Ressources Globales"
CPU=$(top -bn1 | awk '/Cpu\(s\)/{print $2 + $4}')
RAM=$(free -m | awk '/Mem/{printf("%s/%s MB (%.1f%%)", $3,$2,($3/$2)*100)}')
DISK=$(df -h / | awk 'NR==2{print $5}')
echo "CPU Utilisé : ${CPU}%"
echo "RAM Utilisée : ${RAM}"
echo "Espace disque : ${DISK}"
echo "--------------------------------------------------------------"

# 3️⃣ Services systemd SmartOrder
echo -e "\n🔹 [3] Services SmartOrder"
for svc in smartorder-portal-v5 smartorder-websync-bridge smartorder-proxy smartorder-watchdog; do
    printf "  %-35s : %s\n" "$svc" "$(systemctl is-active $svc 2>/dev/null || echo '❌ absent')"
done
echo "--------------------------------------------------------------"

# 4️⃣ Processus Python & NodeJS
echo -e "\n🔹 [4] Processus Python / NodeJS"
ps -ef | grep -E "python3|node" | grep -v grep | awk '{printf "PID:%-6s %-30s %s\n", $2, $8, $9}'
echo "--------------------------------------------------------------"

# 5️⃣ Ports ouverts
echo -e "\n🔹 [5] Ports actifs"
ss -tulnp | grep -E '8555|8787|8090|8088' || echo "Aucun port détecté."
echo "--------------------------------------------------------------"

# 6️⃣ Structure du projet
echo -e "\n🔹 [6] Structure du dossier /opt/smartorder-pro"
tree -L 3 /opt/smartorder-pro 2>/dev/null || ls -R /opt/smartorder-pro
echo "--------------------------------------------------------------"

# 7️⃣ Environnements Python
echo -e "\n🔹 [7] Environnements Python"
find /opt -type d -name "venv" -exec bash -c 'echo "➡️  {}" && source {}/bin/activate && python3 --version && pip list | wc -l && deactivate' \; 2>/dev/null
echo "--------------------------------------------------------------"

# 8️⃣ Logs récents
echo -e "\n🔹 [8] Dernières lignes des logs"
for log in /opt/smartorder-pro/logs/*.log; do
    echo -e "\n📄 $log"
    tail -n 5 "$log" 2>/dev/null
done
echo "--------------------------------------------------------------"

# 9️⃣ Vérification des dépendances critiques
echo -e "\n🔹 [9] Paquets critiques"
for pkg in node npm python3 pip3 git; do
    printf "%-10s : %s\n" "$pkg" "$(command -v $pkg >/dev/null 2>&1 && echo '✅ OK' || echo '❌ Manquant')"
done
echo "--------------------------------------------------------------"

# 🔟 Test GitHub Sync (si repo lié)
if [ -d "/opt/smartorder-pro/.git" ]; then
    echo -e "\n🔹 [10] GitHub Sync"
    cd /opt/smartorder-pro
    git remote -v
    git status -s
else
    echo -e "\n🔹 [10] GitHub Sync : ❌ Aucun repo git détecté"
fi

echo "=============================================================="
echo "✅ Rapport complet généré : /opt/smartorder-pro/tools/diagnostic_full_vps.sh"
echo "=============================================================="
