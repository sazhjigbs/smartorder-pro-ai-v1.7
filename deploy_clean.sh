#!/bin/bash
# Script de déploiement propre SmartOrder PRO sur VPS

echo "🚀 Déploiement propre de SmartOrder PRO..."

# Variables
VPS_HOST="root@107.189.22.255"
VPS_PATH="/opt/smartorder-pro"
LOCAL_PATH="."

# Nettoyer le VPS
echo "🧹 Nettoyage du VPS..."
ssh $VPS_HOST "rm -rf $VPS_PATH/* && mkdir -p $VPS_PATH"

# Copier les fichiers (en excluant venv, __pycache__, logs, node_modules)
echo "📦 Copie des fichiers..."
rsync -avz --progress \
  --exclude='venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='logs/' \
  --exclude='node_modules/' \
  --exclude='.git/' \
  --exclude='*.log' \
  $LOCAL_PATH/ $VPS_HOST:$VPS_PATH/

# Installer les dépendances sur le VPS
echo "📥 Installation des dépendances..."
ssh $VPS_HOST "cd $VPS_PATH && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Créer les répertoires nécessaires
echo "📁 Création des répertoires..."
ssh $VPS_HOST "cd $VPS_PATH && mkdir -p logs data memory ai"

# Donner les permissions
echo "🔐 Configuration des permissions..."
ssh $VPS_HOST "cd $VPS_PATH && chmod +x scripts/*.sh deployment/*.sh"

# Copier le fichier .env si nécessaire
if [ -f ".env" ]; then
    echo "🔑 Copie du fichier .env..."
    scp .env $VPS_HOST:$VPS_PATH/.env
fi

echo "✅ Déploiement terminé !"
echo "🎯 Pour démarrer: ssh $VPS_HOST 'cd $VPS_PATH && ./start_bot.sh'"
