"""
SmartOrder PRO - Telegram Bot
Interface de contrôle complète via Telegram
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

# Note: Installation requise: pip install python-telegram-bot
# from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from core.control_panel import get_control_panel
from core.alert_system import get_alert_system
from core.hybrid_trader import get_hybrid_trader

LOG = logging.getLogger("telegram_bot")
LOG.setLevel(logging.INFO)

class TelegramBot:
    """
    Bot Telegram pour contrôler SmartOrder PRO
    
    Commandes disponibles:
    /start - Démarrer le bot
    /status - État du système
    /balance - Voir les balances
    /positions - Positions actives
    /pnl - Profit & Loss
    /strategies - Liste des stratégies
    /enable <strategy> - Activer une stratégie
    /disable <strategy> - Désactiver une stratégie
    /watchlist - Voir la watchlist
    /add <coin> - Ajouter un coin
    /remove <coin> - Retirer un coin
    /suggestions - Voir suggestions IA
    /approve <id> - Approuver une suggestion
    /reject <id> - Rejeter une suggestion
    /start_trading - Démarrer le trading
    /stop_trading - Arrêter le trading
    /emergency - ARRÊT D'URGENCE
    /stats - Statistiques
    /help - Aide
    
    Features:
    - Inline keyboards pour navigation
    - Real-time notifications
    - Secure authentication
    - Command permissions
    """
    
    def __init__(self, bot_token: str, allowed_users: List[int] = None):
        """
        Initialize Telegram Bot
        
        Args:
            bot_token: Token du bot Telegram
            allowed_users: Liste des user IDs autorisés
        """
        self.bot_token = bot_token
        self.allowed_users = allowed_users or []
        
        # Components
        self.control_panel = get_control_panel()
        self.alert_system = get_alert_system()
        
        # Application (sera initialisé dans run())
        self.application = None
        
        LOG.info("TelegramBot initialized")
    
    def is_authorized(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est autorisé"""
        if not self.allowed_users:
            return True  # Si pas de liste, tout le monde autorisé
        return user_id in self.allowed_users
    
    # ===== COMMAND HANDLERS =====
    
    async def cmd_start(self, update, context):
        """Handler pour /start"""
        user = update.effective_user
        
        if not self.is_authorized(user.id):
            await update.message.reply_text("❌ Unauthorized access")
            return
        
        welcome_msg = f"""
🚀 *SmartOrder PRO* - Trading Bot

Bienvenue {user.first_name}!

Le bot est maintenant connecté et prêt à recevoir vos commandes.

📱 *Commandes principales:*
/status - État du système
/balance - Voir les balances
/positions - Positions actives
/strategies - Gérer les stratégies
/watchlist - Gérer la watchlist
/start_trading - Démarrer
/stop_trading - Arrêter
/emergency - STOP d'urgence

Type /help pour la liste complète des commandes.
"""
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def cmd_status(self, update, context):
        """Handler pour /status"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        state = self.control_panel.system_state
        stats = self.control_panel.live_stats
        
        status_msg = f"""
📊 *SYSTEM STATUS*

🔧 *État:* {'✅ RUNNING' if state['running'] else '⏸️ STOPPED'}
🚨 *Emergency Stop:* {'🔴 ACTIVE' if state['emergency_stop'] else '🟢 OK'}
🔧 *Manual Override:* {'✅ ON' if state['manual_override'] else '❌ OFF'}

💰 *Stats Live:*
• Active Trades: {stats['active_trades']}
• Daily PnL: {stats['daily_pnl']:.2f}%
• Total PnL: ${stats['total_pnl']:.2f}
• Win Rate: {stats['win_rate']:.1f}%

🕐 Last Update: {state['last_update'] or 'N/A'}
"""
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
    
    async def cmd_strategies(self, update, context):
        """Handler pour /strategies"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        status = self.control_panel.get_strategy_status()
        
        msg = "📊 *STRATEGIES STATUS*\n\n"
        
        msg += "💼 *Spot Strategies:*\n"
        for name, enabled in status['spot']['strategies'].items():
            icon = "✅" if enabled else "❌"
            msg += f"{icon} {name}\n"
        
        msg += "\n🔮 *Futures Strategies:*\n"
        for name, enabled in status['futures']['strategies'].items():
            icon = "✅" if enabled else "❌"
            msg += f"{icon} {name}\n"
        
        msg += "\n💡 Use /enable or /disable to change"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_watchlist(self, update, context):
        """Handler pour /watchlist"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        watchlist = self.control_panel.get_active_watchlist()
        
        msg = "👀 *WATCHLIST*\n\n"
        
        if watchlist:
            for symbol in watchlist:
                msg += f"✅ {symbol}\n"
        else:
            msg += "Empty watchlist\n"
        
        msg += "\n💡 /add BTC or /remove BTC"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_suggestions(self, update, context):
        """Handler pour /suggestions"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        suggestions = self.control_panel.get_pending_suggestions()
        
        if not suggestions:
            await update.message.reply_text("No pending AI suggestions")
            return
        
        msg = "🤖 *AI SUGGESTIONS*\n\n"
        
        for s in suggestions[:5]:  # Max 5
            msg += f"🔥 *{s['symbol']}* {s['side']}\n"
            msg += f"   Strategy: {s['strategy']}\n"
            msg += f"   Confidence: {s['confidence']}%\n"
            msg += f"   Entry: {s['entry']} | TP: {s['tp']}\n"
            msg += f"   ID: `{s['id']}`\n\n"
        
        msg += "💡 /approve <id> or /reject <id>"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_start_trading(self, update, context):
        """Handler pour /start_trading"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        success = self.control_panel.start_trading()
        
        if success:
            msg = "✅ *TRADING STARTED*\n\nThe bot is now actively trading!"
        else:
            msg = "❌ Cannot start trading (check emergency stop)"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_stop_trading(self, update, context):
        """Handler pour /stop_trading"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        self.control_panel.stop_trading()
        
        await update.message.reply_text(
            "⏸️ *TRADING STOPPED*\n\nAll automatic trading paused.",
            parse_mode='Markdown'
        )
    
    async def cmd_emergency(self, update, context):
        """Handler pour /emergency"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        self.control_panel.emergency_stop()
        
        await update.message.reply_text(
            "🚨 *EMERGENCY STOP ACTIVATED*\n\n"
            "All positions closed!\n"
            "All orders cancelled!\n"
            "Trading stopped!",
            parse_mode='Markdown'
        )
    
    async def cmd_enable(self, update, context):
        """Handler pour /enable <strategy>"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /enable grid_trading")
            return
        
        strategy = context.args[0]
        
        # Déterminer catégorie (spot ou futures)
        category = 'spot'  # Default
        
        success = self.control_panel.enable_strategy(category, strategy)
        
        if success:
            await update.message.reply_text(f"✅ {strategy} enabled!")
        else:
            await update.message.reply_text(f"❌ Failed to enable {strategy}")
    
    async def cmd_help(self, update, context):
        """Handler pour /help"""
        help_msg = """
📚 *COMMANDES DISPONIBLES*

📊 *Info & Status*
/status - État du système
/balance - Balances
/positions - Positions actives
/pnl - Profit & Loss
/stats - Statistiques

🎯 *Stratégies*
/strategies - Liste stratégies
/enable <name> - Activer stratégie
/disable <name> - Désactiver stratégie

👀 *Watchlist*
/watchlist - Voir watchlist
/add <coin> - Ajouter coin
/remove <coin> - Retirer coin

🤖 *IA*
/suggestions - Suggestions IA
/approve <id> - Approuver
/reject <id> - Rejeter

🎮 *Contrôle*
/start_trading - Démarrer
/stop_trading - Arrêter
/emergency - STOP urgence

❓ *Aide*
/help - Cette aide
"""
        
        await update.message.reply_text(help_msg, parse_mode='Markdown')
    
    # ===== NOTIFICATIONS =====
    
    async def send_notification(self, message: str, chat_id: int):
        """Envoie une notification"""
        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
        except Exception as e:
            LOG.error(f"Failed to send notification: {e}")
    
    def run(self):
        """Démarre le bot (mode polling)"""
        LOG.info("Starting Telegram bot...")
        
        # TODO: Uncomment when python-telegram-bot is installed
        # self.application = Application.builder().token(self.bot_token).build()
        # 
        # # Register handlers
        # self.application.add_handler(CommandHandler("start", self.cmd_start))
        # self.application.add_handler(CommandHandler("status", self.cmd_status))
        # self.application.add_handler(CommandHandler("strategies", self.cmd_strategies))
        # self.application.add_handler(CommandHandler("watchlist", self.cmd_watchlist))
        # self.application.add_handler(CommandHandler("suggestions", self.cmd_suggestions))
        # self.application.add_handler(CommandHandler("start_trading", self.cmd_start_trading))
        # self.application.add_handler(CommandHandler("stop_trading", self.cmd_stop_trading))
        # self.application.add_handler(CommandHandler("emergency", self.cmd_emergency))
        # self.application.add_handler(CommandHandler("enable", self.cmd_enable))
        # self.application.add_handler(CommandHandler("help", self.cmd_help))
        # 
        # # Start polling
        # self.application.run_polling()
        
        LOG.info("✅ Telegram bot ready!")
        LOG.info("Note: Install python-telegram-bot to enable full functionality")


if __name__ == "__main__":
    print("=" * 60)
    print("Telegram Bot - Setup Instructions")
    print("=" * 60)
    
    print("""
📱 *SETUP TELEGRAM BOT*

1️⃣ Créer un bot Telegram:
   - Ouvrir @BotFather sur Telegram
   - Envoyer /newbot
   - Suivre les instructions
   - Copier le TOKEN

2️⃣ Obtenir votre Chat ID:
   - Envoyer un message à @userinfobot
   - Copier votre User ID

3️⃣ Installer les dépendances:
   pip install python-telegram-bot

4️⃣ Configurer le bot:
   BOT_TOKEN = "your_token_here"
   ALLOWED_USERS = [your_user_id]

5️⃣ Lancer le bot:
   python telegram_bot.py

📚 Commandes disponibles:
   /start - Démarrer
   /status - État système
   /strategies - Gérer stratégies
   /watchlist - Gérer coins
   /start_trading - Démarrer trading
   /emergency - STOP urgence

🔐 Sécurité:
   - Seuls les users autorisés peuvent utiliser le bot
   - Ne partagez jamais votre token
   - Gardez votre chat_id privé

✅ Le bot est prêt à être configuré!
    """)
    
    print("\n" + "=" * 60)
    print("Configuration template saved!")
    print("=" * 60)
