#!/bin/bash
cd /opt/smartorder-pro || exit
echo "🔄 [$(date)] Auto-Pull depuis GitHub..."
git fetch origin main
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "📦 Nouvelle version détectée — mise à jour..."
    git reset --hard origin/main
    sudo systemctl restart smartorder-pro
    echo "✅ Bot mis à jour et redémarré."
else
    echo "⏸️ Déjà à jour."
fi
