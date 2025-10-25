#!/bin/bash
# 🚀 SAFELOGIC SmartOrder PRO - Déploiement Hybrid Manager
# Auto-déploiement du nouveau module de gestion intelligente

set -e  # Arrêter sur erreur

BOT_DIR="/root/smartorder-pro-ai-v1.7"
BACKUP_DIR="/root/backups/$(date +%Y%m%d_%H%M%S)"
TELEGRAM_TOKEN="$TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT="$TELEGRAM_CHAT_ID"

# Fonction notification Telegram
notify_telegram() {
    if [[ -n "$TELEGRAM_TOKEN" && -n "$TELEGRAM_CHAT" ]]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
             -d chat_id="$TELEGRAM_CHAT" \
             -d text="🤖 SmartOrder: $1" \
             -d parse_mode="Markdown" > /dev/null
    fi
}

echo "🚀 [$(date)] Déploiement Hybrid Capital Manager..."
notify_telegram "🚀 Déploiement du nouveau module Hybrid Manager..."

# 1. Backup avant déploiement
echo "💾 Création backup..."
mkdir -p "$BACKUP_DIR"
cp -r "$BOT_DIR" "$BACKUP_DIR/"
echo "✅ Backup créé: $BACKUP_DIR"

# 2. Pull depuis GitHub
cd "$BOT_DIR" || exit 1
echo "📡 Pull depuis GitHub..."
git pull origin main

# 3. Vérifier que le nouveau module existe
if [[ ! -f "hybrid_capital_manager.py" ]]; then
    echo "❌ ERREUR: hybrid_capital_manager.py introuvable!"
    notify_telegram "❌ Déploiement échoué: module introuvable"
    exit 1
fi

echo "✅ Module hybrid_capital_manager.py trouvé"

# 4. Test syntaxique du module
echo "🧪 Test syntaxique du module..."
python3 -m py_compile hybrid_capital_manager.py
if [[ $? -eq 0 ]]; then
    echo "✅ Syntaxe validée"
else
    echo "❌ ERREUR: Syntaxe invalide dans hybrid_capital_manager.py"
    notify_telegram "❌ Déploiement échoué: erreur syntaxe"
    exit 1
fi

# 5. Test d'import du module (sans exécution complète)
echo "🔍 Test d'import du module..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import hybrid_capital_manager
    print('✅ Import réussi')
except Exception as e:
    print(f'❌ Erreur import: {e}')
    sys.exit(1)
"

if [[ $? -ne 0 ]]; then
    echo "❌ ERREUR: Import du module échoué"
    notify_telegram "❌ Déploiement échoué: erreur import"
    exit 1
fi

# 6. Création du répertoire data si nécessaire
mkdir -p data
chmod 755 data

# 7. Installation des dépendances si nécessaire
echo "📦 Vérification dépendances..."
pip3 install --quiet --upgrade asyncio

# 8. Redémarrage intelligent du bot
echo "🔄 Redémarrage du bot principal..."
if systemctl is-active --quiet smartorder-pro; then
    systemctl restart smartorder-pro
    echo "✅ Bot redémarré"
else
    echo "⚠️ Service pas actif, démarrage..."
    systemctl start smartorder-pro
fi

# 9. Test de santé post-déploiement
echo "🏥 Test de santé..."
sleep 5
if systemctl is-active --quiet smartorder-pro; then
    echo "✅ Bot actif après redémarrage"
    notify_telegram "✅ Hybrid Manager déployé avec succès! 🎉"
else
    echo "❌ Bot inactif après redémarrage"
    notify_telegram "⚠️ Déploiement complété mais bot inactif"
fi

# 10. Affichage statut final
echo ""
echo "🎯 DÉPLOIEMENT TERMINÉ"
echo "📊 Nouveau module: hybrid_capital_manager.py"
echo "📁 Backup: $BACKUP_DIR"
echo "🤖 Bot Status: $(systemctl is-active smartorder-pro)"
echo ""
echo "🔧 Prochaines étapes:"
echo "   - Tester: python3 hybrid_capital_manager.py"
echo "   - API scan: import hybrid_capital_manager; await hybrid_capital_manager.scan_portfolio()"
echo "   - Auto mode: import hybrid_capital_manager; await hybrid_capital_manager.enable_auto_mode()"

notify_telegram "
🎯 *Hybrid Manager Actif*
📊 Module: \`hybrid_capital_manager.py\`
🤖 Status: \`$(systemctl is-active smartorder-pro)\`
✨ Prêt pour trading intelligent!
"