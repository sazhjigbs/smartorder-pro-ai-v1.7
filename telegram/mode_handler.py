#!/usr/bin/env python3
"""
SmartOrder PRO - Telegram Mode Handler
=======================================
Gestion des modes de trading via Telegram

Commandes:
- /mode - Afficher mode actuel et changer
- /suggestions - Voir suggestions IA
- /coins - Liste des coins recommandés

Fonctionnalités:
- Boutons inline pour switch mode
- Notifications suggestions en mode HYBRID
- Validation suggestions via boutons
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
import asyncio
import requests
from datetime import datetime

# ==============================================================================
# CONFIGURATION
# ==============================================================================

API_BASE = "http://localhost:8560"

# Icons
MODE_ICONS = {
    "AUTO_SPOT": "🤖",
    "AUTO_FUTURES": "⚡",
    "MANUAL": "👨‍💻",
    "HYBRID": "🤝"
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_current_mode():
    """Récupère le mode actuel"""
    try:
        response = requests.get(f"{API_BASE}/api/mode/current", timeout=5)
        data = response.json()
        if data.get("success"):
            return data["data"]
    except:
        pass
    return None

def get_suggestions():
    """Récupère les suggestions IA"""
    try:
        response = requests.get(f"{API_BASE}/api/mode/suggestions", timeout=5)
        data = response.json()
        if data.get("success"):
            return data["data"]
    except:
        pass
    return None

def set_mode(mode: str, reason: str = None):
    """Change le mode"""
    try:
        response = requests.post(
            f"{API_BASE}/api/mode/set",
            json={"mode": mode, "reason": reason or "Via Telegram"},
            timeout=5
        )
        data = response.json()
        return data
    except:
        return {"success": False, "error": "Erreur de connexion"}

def create_suggestion():
    """Crée une suggestion pour validation"""
    try:
        response = requests.post(f"{API_BASE}/api/mode/hybrid/suggest", timeout=5)
        data = response.json()
        if data.get("success"):
            return data["data"]
    except:
        pass
    return None

def validate_suggestion(suggestion_id: str, approved: bool):
    """Valide ou rejette une suggestion"""
    try:
        response = requests.post(
            f"{API_BASE}/api/mode/hybrid/validate",
            json={"suggestion_id": suggestion_id, "approved": approved},
            timeout=5
        )
        data = response.json()
        return data
    except:
        return {"success": False, "error": "Erreur de connexion"}

# ==============================================================================
# COMMAND HANDLERS
# ==============================================================================

async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /mode
    Affiche le mode actuel et propose de changer
    """
    current = get_current_mode()
    
    if not current:
        await update.message.reply_text(
            "❌ Impossible de récupérer le mode actuel.\n"
            "Vérifiez que l'API Mode Manager est lancée."
        )
        return
    
    mode = current["mode"]
    icon = MODE_ICONS.get(mode, "❓")
    
    # Créer les boutons pour chaque mode
    keyboard = [
        [
            InlineKeyboardButton(
                f"{MODE_ICONS['AUTO_SPOT']} Auto Spot",
                callback_data="mode:AUTO_SPOT"
            ),
            InlineKeyboardButton(
                f"{MODE_ICONS['AUTO_FUTURES']} Auto Futures",
                callback_data="mode:AUTO_FUTURES"
            )
        ],
        [
            InlineKeyboardButton(
                f"{MODE_ICONS['MANUAL']} Manuel",
                callback_data="mode:MANUAL"
            ),
            InlineKeyboardButton(
                f"{MODE_ICONS['HYBRID']} Hybride",
                callback_data="mode:HYBRID"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Rafraîchir",
                callback_data="mode:refresh"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        f"🎯 **Mode de Trading Actuel**\n\n"
        f"{icon} **{mode}**\n"
        f"_{current['description']}_\n\n"
        f"Choisissez un nouveau mode :"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def cmd_suggestions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /suggestions
    Affiche les suggestions IA temps réel
    """
    suggestions = get_suggestions()
    
    if not suggestions:
        await update.message.reply_text(
            "❌ Impossible de récupérer les suggestions.\n"
            "Vérifiez que l'API Mode Manager est lancée."
        )
        return
    
    strategy = suggestions["strategy"]
    confidence = int(suggestions["confidence"] * 100)
    
    # Barre de confiance visuelle
    bar_length = 10
    filled = int((confidence / 100) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    message = (
        f"🤖 **Suggestions IA Temps Réel**\n\n"
        f"🔥 **Stratégie:** {strategy['name']}\n"
        f"📊 **Description:** {strategy['description']}\n\n"
        f"✨ **Confiance:** {confidence}%\n"
        f"`{bar}` {confidence}%\n\n"
        f"📍 **Mode suggéré:** {suggestions['suggested_mode']}\n"
        f"⚠️ **Niveau de risque:** {strategy['risk_level']}\n"
        f"📈 **Timeframes:** {', '.join(strategy['timeframes'])}\n"
        f"💰 **Position Size:** {strategy['position_size_multiplier']}x\n\n"
        f"**📊 Raisons:**\n"
    )
    
    for reason in suggestions["reasons"]:
        message += f"• {reason}\n"
    
    # Bouton pour appliquer la suggestion
    keyboard = [
        [
            InlineKeyboardButton(
                f"✅ Activer {suggestions['suggested_mode']}",
                callback_data=f"mode:{suggestions['suggested_mode']}"
            )
        ],
        [
            InlineKeyboardButton(
                "💎 Voir coins recommandés",
                callback_data="coins:show"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def cmd_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /coins
    Affiche la liste des coins recommandés
    """
    suggestions = get_suggestions()
    
    if not suggestions:
        await update.message.reply_text("❌ Erreur de récupération des coins.")
        return
    
    coins = suggestions.get("recommended_coins", [])
    strategy = suggestions["strategy"]["name"]
    
    if not coins:
        message = (
            f"💎 **Coins Recommandés**\n\n"
            f"Stratégie: **{strategy}**\n\n"
            f"⚠️ Aucun coin recommandé pour cette stratégie.\n"
            f"(Wait & See ou conditions défavorables)"
        )
    else:
        message = (
            f"💎 **Coins Recommandés**\n\n"
            f"Stratégie: **{strategy}**\n\n"
        )
        
        for coin in coins:
            message += f"• **{coin}**\n"
        
        message += f"\n📊 Total: {len(coins)} coins"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Commande /start
    Message de bienvenue
    """
    message = (
        "🎯 **SmartOrder PRO - Mode Manager**\n\n"
        "Gestion intelligente des modes de trading avec IA\n\n"
        "**Commandes disponibles:**\n"
        "/mode - Changer de mode de trading\n"
        "/suggestions - Voir suggestions IA\n"
        "/coins - Liste des coins recommandés\n\n"
        "**Modes disponibles:**\n"
        "🤖 Auto Spot - Trading auto spot uniquement\n"
        "⚡ Auto Futures - Trading auto futures uniquement\n"
        "👨‍💻 Manuel - Contrôle manuel complet\n"
        "🤝 Hybride - IA suggère, vous validez\n\n"
        "Utilisez /mode pour commencer !"
    )
    
    await update.message.reply_text(message, parse_mode="Markdown")

# ==============================================================================
# CALLBACK HANDLERS
# ==============================================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Gère les callbacks des boutons inline
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Mode change
    if data.startswith("mode:"):
        action = data.split(":")[1]
        
        if action == "refresh":
            # Rafraîchir l'affichage du mode
            current = get_current_mode()
            if current:
                mode = current["mode"]
                icon = MODE_ICONS.get(mode, "❓")
                
                message = (
                    f"🎯 **Mode de Trading Actuel**\n\n"
                    f"{icon} **{mode}**\n"
                    f"_{current['description']}_\n\n"
                    f"Choisissez un nouveau mode :"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton(
                            f"{MODE_ICONS['AUTO_SPOT']} Auto Spot",
                            callback_data="mode:AUTO_SPOT"
                        ),
                        InlineKeyboardButton(
                            f"{MODE_ICONS['AUTO_FUTURES']} Auto Futures",
                            callback_data="mode:AUTO_FUTURES"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            f"{MODE_ICONS['MANUAL']} Manuel",
                            callback_data="mode:MANUAL"
                        ),
                        InlineKeyboardButton(
                            f"{MODE_ICONS['HYBRID']} Hybride",
                            callback_data="mode:HYBRID"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔄 Rafraîchir",
                            callback_data="mode:refresh"
                        )
                    ]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        else:
            # Changer de mode
            result = set_mode(action, "Via Telegram")
            
            if result.get("success"):
                icon = MODE_ICONS.get(action, "❓")
                await query.edit_message_text(
                    f"✅ **Mode changé avec succès !**\n\n"
                    f"{icon} **{action}**\n\n"
                    f"Le bot est maintenant en mode {action}.",
                    parse_mode="Markdown"
                )
                
                # Si mode HYBRID, créer suggestion
                if action == "HYBRID":
                    await asyncio.sleep(2)
                    await send_hybrid_suggestion(query.message.chat_id, context)
            else:
                await query.edit_message_text(
                    f"❌ Erreur lors du changement de mode:\n{result.get('error', 'Erreur inconnue')}"
                )
    
    # Coins
    elif data == "coins:show":
        suggestions = get_suggestions()
        if suggestions:
            coins = suggestions.get("recommended_coins", [])
            strategy = suggestions["strategy"]["name"]
            
            if not coins:
                message = f"💎 **Coins Recommandés**\n\nStratégie: **{strategy}**\n\n⚠️ Aucun coin recommandé."
            else:
                message = f"💎 **Coins Recommandés**\n\nStratégie: **{strategy}**\n\n"
                for coin in coins:
                    message += f"• **{coin}**\n"
                message += f"\n📊 Total: {len(coins)} coins"
            
            await query.edit_message_text(message, parse_mode="Markdown")
    
    # Validation suggestion HYBRID
    elif data.startswith("validate:"):
        parts = data.split(":")
        suggestion_id = parts[1]
        approved = parts[2] == "approve"
        
        result = validate_suggestion(suggestion_id, approved)
        
        if result.get("success"):
            if approved:
                await query.edit_message_text(
                    "✅ **Suggestion approuvée !**\n\n"
                    "Le bot va exécuter la stratégie recommandée.",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "❌ **Suggestion rejetée**\n\n"
                    "La suggestion a été ignorée.",
                    parse_mode="Markdown"
                )
        else:
            await query.edit_message_text(
                f"❌ Erreur: {result.get('error', 'Erreur inconnue')}"
            )

# ==============================================================================
# HYBRID MODE SUGGESTIONS
# ==============================================================================

async def send_hybrid_suggestion(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """
    Envoie une notification de suggestion en mode HYBRID
    """
    suggestion = create_suggestion()
    
    if not suggestion:
        return
    
    confidence = int(suggestion["confidence"] * 100)
    
    message = (
        "🤖 **IA Détecte une Opportunité !**\n\n"
        f"🔥 **Stratégie:** {suggestion['strategy']}\n"
        f"📍 **Mode:** {suggestion['mode']}\n"
        f"✨ **Confiance:** {confidence}%\n"
        f"💎 **Coins:** {', '.join(suggestion['recommended_coins'])}\n\n"
        f"**Raisons:**\n"
    )
    
    for reason in suggestion["reasons"]:
        message += f"• {reason}\n"
    
    message += "\n**Voulez-vous approuver cette suggestion ?**"
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Approuver",
                callback_data=f"validate:{suggestion['id']}:approve"
            ),
            InlineKeyboardButton(
                "❌ Rejeter",
                callback_data=f"validate:{suggestion['id']}:reject"
            )
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Lance le bot Telegram"""
    
    # Remplacer par votre token Telegram
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    
    # Créer l'application
    application = Application.builder().token(TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("mode", cmd_mode))
    application.add_handler(CommandHandler("suggestions", cmd_suggestions))
    application.add_handler(CommandHandler("coins", cmd_coins))
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    print("=" * 70)
    print("🤖 SmartOrder PRO - Telegram Mode Handler")
    print("=" * 70)
    print("\n✅ Bot Telegram démarré !")
    print("\nCommandes disponibles:")
    print("   /start - Message de bienvenue")
    print("   /mode - Changer de mode")
    print("   /suggestions - Suggestions IA")
    print("   /coins - Coins recommandés")
    print("\n" + "=" * 70)
    
    # Démarrer le bot
    application.run_polling()

if __name__ == "__main__":
    main()
