#!/bin/bash
cd /opt/smartorder-pro || exit
git fetch origin main
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "🔄 Nouvelle version détectée — mise à jour..."
    git pull origin main
    systemctl restart smartorder-pro
else
    echo "✅ Aucune mise à jour détectée."
fi
