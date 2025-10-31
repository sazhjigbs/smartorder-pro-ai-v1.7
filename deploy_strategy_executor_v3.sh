#!/bin/bash
# Déploiement Strategy Executor v3 REAL
# A exécuter directement sur le VPS

echo "🚀 Déploiement Strategy Executor v3 REAL"
echo "========================================="

# Vérifier CCXT et dépendances
echo "✅ Vérification dépendances Python..."
pip3 list | grep -E "ccxt|pandas|ta" || {
    echo "📦 Installation des packages manquants..."
    pip3 install ccxt pandas ta -q
}

# Donner permissions
chmod +x /opt/smartorder-pro/strategy_executor_v3_real.py

# Créer service systemd
echo "🔧 Création service systemd..."
cat > /etc/systemd/system/strategy-executor-v3.service << 'EOF'
[Unit]
Description=SmartOrder PRO - Strategy Executor v3 REAL
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/smartorder-pro
ExecStart=/usr/bin/python3 /opt/smartorder-pro/strategy_executor_v3_real.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/smartorder-pro/logs/strategy_executor_v3_real.log
StandardError=append:/opt/smartorder-pro/logs/strategy_executor_v3_real_error.log

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd
systemctl daemon-reload

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📋 Commandes disponibles:"
echo "  systemctl start strategy-executor-v3      # Démarrer"
echo "  systemctl status strategy-executor-v3     # Statut"
echo "  systemctl stop strategy-executor-v3       # Arrêter"
echo "  tail -f /opt/smartorder-pro/logs/strategy_executor_v3_real.log  # Logs"
echo ""
echo "🔥 Pour lancer en manuel (test):"
echo "  cd /opt/smartorder-pro"
echo "  python3 strategy_executor_v3_real.py"
echo ""
