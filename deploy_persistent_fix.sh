#!/bin/bash
###############################################################################
# DÉPLOIEMENT COMPLET - SmartOrder PRO Dashboard Persistent Fix
###############################################################################

echo "=================================================="
echo "🚀 DÉPLOIEMENT DASHBOARD PERSISTENT FIX v3.0"
echo "=================================================="

VPS_IP="188.245.188.145"
VPS_USER="root"
DASHBOARD_DIR="/opt/smartorder-pro/web"

# 1. Upload du script de persistance
echo ""
echo "1️⃣  Upload dashboard_persistent_fix.js..."
scp dashboard_persistent_fix.js ${VPS_USER}@${VPS_IP}:${DASHBOARD_DIR}/
if [ $? -eq 0 ]; then
    echo "   ✅ Script uploadé"
else
    echo "   ❌ Erreur upload"
    exit 1
fi

# 2. Backup dashboard actuel
echo ""
echo "2️⃣  Backup dashboard actuel..."
ssh ${VPS_USER}@${VPS_IP} "cp ${DASHBOARD_DIR}/dashboard.html ${DASHBOARD_DIR}/dashboard.html.backup.$(date +%Y%m%d_%H%M%S)"
echo "   ✅ Backup créé"

# 3. Injection du script dans dashboard.html
echo ""
echo "3️⃣  Injection du script de persistance..."
ssh ${VPS_USER}@${VPS_IP} << 'EOF'
DASHBOARD_FILE="/opt/smartorder-pro/web/dashboard.html"

# Vérifier si déjà injecté
if grep -q "dashboard_persistent_fix.js" "${DASHBOARD_FILE}"; then
    echo "   ⚠️  Script déjà présent, remplacement..."
    # Supprimer l'ancienne référence
    sed -i '/dashboard_persistent_fix\.js/d' "${DASHBOARD_FILE}"
fi

# Injecter avant </body>
sed -i 's|</body>|    <script src="dashboard_persistent_fix.js"></script>\n</body>|' "${DASHBOARD_FILE}"

# Vérifier injection
if grep -q "dashboard_persistent_fix.js" "${DASHBOARD_FILE}"; then
    echo "   ✅ Script injecté avec succès"
else
    echo "   ❌ Erreur injection"
    exit 1
fi
EOF

if [ $? -ne 0 ]; then
    echo "   ❌ Erreur lors de l'injection"
    exit 1
fi

# 4. Upload diagnostic_memory.py
echo ""
echo "4️⃣  Upload diagnostic avec mémoire..."
scp diagnostic_memory.py ${VPS_USER}@${VPS_IP}:/root/smartorder-pro-ai-v1.7/
ssh ${VPS_USER}@${VPS_IP} "chmod +x /root/smartorder-pro-ai-v1.7/diagnostic_memory.py"
echo "   ✅ Diagnostic uploadé"

# 5. Vérification finale
echo ""
echo "5️⃣  Vérification finale..."
ssh ${VPS_USER}@${VPS_IP} << 'EOF'
echo "   Fichiers présents:"
ls -lh /opt/smartorder-pro/web/dashboard_persistent_fix.js
grep -c "dashboard_persistent_fix.js" /opt/smartorder-pro/web/dashboard.html && echo "   ✅ Script référencé dans dashboard.html"
EOF

# 6. Redémarrage nginx (pour cache)
echo ""
echo "6️⃣  Redémarrage nginx..."
ssh ${VPS_USER}@${VPS_IP} "systemctl reload nginx"
echo "   ✅ Nginx rechargé"

echo ""
echo "=================================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=================================================="
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo "   1. Ouvrir le dashboard dans un nouvel onglet privé"
echo "   2. Ouvrir la console navigateur (F12)"
echo "   3. Vérifier le message: '✅ Persistence Fix v3.0 loaded'"
echo "   4. Tester toggle stratégie/exchange"
echo "   5. Recharger page (F5) et vérifier persistance"
echo ""
echo "🔍 DIAGNOSTIC:"
echo "   ssh root@${VPS_IP}"
echo "   python3 /root/smartorder-pro-ai-v1.7/diagnostic_memory.py"
echo ""
