#!/usr/bin/env python3
"""
🤖 SAFELOGIC SmartOrder PRO — Telegram Bot
Contrôle total du bot via Telegram
"""

import os
import sys
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.bybit_client import wallet_spot_balances, futures_positions
from core.execution_engine import get_engine
from core.logger import logger

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_IDS = [int(x.strip()) for x in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",") if x.strip()]

# État global du trading auto
TRADING_STATE = {
    "auto_trading_enabled": False,
    "last_trade": None,
    "trades_today": 0
}

class TelegramBot:
    """Bot Telegram pour SmartOrder PRO"""
    
    def __init__(self):
        self.app = None
        
    def is_authorized(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est autorisé"""
        if not ALLOWED_USER_IDS:
            return True  # Si pas de whitelist, tout le monde passe
        return user_id in ALLOWED_USER_IDS
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        welcome_msg = """
🚀 **SAFELOGIC SmartOrder PRO v6.0**

Bot de trading professionnel activé !

**Commandes disponibles :**
📊 `/position` - Voir positions ouvertes
💰 `/balance` - Voir balances
📈 `/pnl` - Résumé PNL
⚡ `/trade BUY/SELL SYMBOL QTY` - Trade manuel
🎯 `/split SYMBOL QTY PRICE` - Split order
🛑 `/stop` - Arrêter trading auto
▶️ `/start_trading` - Démarrer trading auto
📋 `/status` - État du bot
🔄 `/trailing SYMBOL SIDE ENTRY TRAIL%` - Setup trailing stop

**Exemple :**
`/trade BUY BTCUSDT 0.001`
`/split BTCUSDT 0.003 67000`
`/trailing BTCUSDT LONG 67000 2.0`

Bon trading ! 🎯
        """
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
    
    async def position_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /position"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            positions_data = futures_positions()
            positions = positions_data.get("futures", [])
            
            if not positions or all(p.get("size") == "0" for p in positions):
                await update.message.reply_text("📭 Aucune position ouverte")
                return
            
            msg = "💼 **Positions Ouvertes:**\n\n"
            
            for pos in positions:
                if pos.get("size", "0") != "0":
                    symbol = pos.get("symbol", "?")
                    side = pos.get("side", "?")
                    size = pos.get("size", "0")
                    entry = pos.get("entryPrice", "0")
                    pnl = pos.get("unrealPnl", "0")
                    
                    pnl_emoji = "🟢" if float(pnl) >= 0 else "🔴"
                    
                    msg += f"{pnl_emoji} **{symbol}** {side}\n"
                    msg += f"   Size: `{size}`\n"
                    msg += f"   Entry: `{entry}`\n"
                    msg += f"   PnL: `{pnl}` USDT\n\n"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Position command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /balance"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            balance_data = wallet_spot_balances()
            balances = balance_data.get("spot", [])
            
            if not balances:
                await update.message.reply_text("📭 Aucun solde")
                return
            
            msg = "💰 **Balances:**\n\n"
            
            for bal in balances:
                asset = bal.get("asset", "?")
                free = bal.get("free", "0")
                locked = bal.get("locked", "0")
                
                if float(free) > 0 or float(locked) > 0:
                    msg += f"**{asset}**\n"
                    msg += f"   Free: `{free}`\n"
                    if float(locked) > 0:
                        msg += f"   Locked: `{locked}`\n"
                    msg += "\n"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Balance command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def pnl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /pnl"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            # TODO: Récupérer PNL depuis l'API
            msg = "📈 **PNL Summary:**\n\n"
            msg += "Total Positions: `0`\n"
            msg += "Total PNL: `0.00` USDT\n"
            msg += "Win Rate: `0%`\n"
            msg += "\n_API PNL en cours d'intégration..._"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"PNL command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /trade BUY/SELL SYMBOL QTY"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            args = context.args
            
            if len(args) < 3:
                await update.message.reply_text(
                    "❌ Usage: `/trade BUY/SELL SYMBOL QTY`\n"
                    "Exemple: `/trade BUY BTCUSDT 0.001`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            side = args[0].upper()
            symbol = args[1].upper()
            qty = args[2]
            
            if side not in ["BUY", "SELL"]:
                await update.message.reply_text("❌ Side doit être BUY ou SELL")
                return
            
            # TODO: Exécuter l'ordre via Bybit
            msg = f"⚡ **Ordre placé:**\n\n"
            msg += f"Side: `{side}`\n"
            msg += f"Symbol: `{symbol}`\n"
            msg += f"Quantity: `{qty}`\n"
            msg += f"\n_Exécution en cours..._"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
            logger.info(f"Trade command: {side} {symbol} {qty} by user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Trade command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def split_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /split SYMBOL QTY PRICE [SPLITS]"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            args = context.args
            
            if len(args) < 3:
                await update.message.reply_text(
                    "❌ Usage: `/split SYMBOL QTY PRICE [SPLITS]`\n"
                    "Exemple: `/split BTCUSDT 0.003 67000 3`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            symbol = args[0].upper()
            qty = float(args[1])
            price = float(args[2])
            num_splits = int(args[3]) if len(args) > 3 else 3
            
            # Créer split order
            engine = get_engine()
            splits = engine.split_order(symbol, "BUY", qty, price, num_splits)
            
            msg = f"📊 **Split Order créé:**\n\n"
            msg += f"Symbol: `{symbol}`\n"
            msg += f"Total Qty: `{qty}`\n"
            msg += f"Price: `{price}`\n"
            msg += f"Splits: `{len(splits)}`\n\n"
            
            for i, split in enumerate(splits, 1):
                msg += f"{i}. Qty: `{split['quantity']}` @ `{split['price']}`\n"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Split command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def trailing_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /trailing SYMBOL SIDE ENTRY TRAIL%"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            args = context.args
            
            if len(args) < 4:
                await update.message.reply_text(
                    "❌ Usage: `/trailing SYMBOL SIDE ENTRY TRAIL%`\n"
                    "Exemple: `/trailing BTCUSDT LONG 67000 2.0`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            symbol = args[0].upper()
            side = args[1].upper()
            entry = float(args[2])
            trail_pct = float(args[3])
            
            # Setup trailing stop
            engine = get_engine()
            trail = engine.setup_trailing_stop(symbol, side, entry, trail_pct)
            
            msg = f"🎯 **Trailing Stop configuré:**\n\n"
            msg += f"Symbol: `{symbol}`\n"
            msg += f"Side: `{side}`\n"
            msg += f"Entry: `{entry}`\n"
            msg += f"Trail: `{trail_pct}%`\n"
            msg += f"Stop Price: `{trail['stop_price']:.2f}`\n"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Trailing command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /status"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        try:
            engine = get_engine()
            trailing_stops = engine.get_all_trailing_stops()
            
            status_emoji = "🟢" if TRADING_STATE["auto_trading_enabled"] else "🔴"
            
            msg = f"📋 **Status SmartOrder PRO:**\n\n"
            msg += f"{status_emoji} Trading Auto: `{'ON' if TRADING_STATE['auto_trading_enabled'] else 'OFF'}`\n"
            msg += f"🎯 Trailing Stops: `{len(trailing_stops)}`\n"
            msg += f"📊 Trades aujourd'hui: `{TRADING_STATE['trades_today']}`\n"
            
            if TRADING_STATE["last_trade"]:
                msg += f"\n⏰ Dernier trade: `{TRADING_STATE['last_trade']}`\n"
            
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Status command error: {str(e)}")
            await update.message.reply_text(f"❌ Erreur: {str(e)}")
    
    async def start_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start_trading"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        TRADING_STATE["auto_trading_enabled"] = True
        await update.message.reply_text("✅ Trading automatique **ACTIVÉ** 🚀", parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Auto trading enabled by user {update.effective_user.id}")
    
    async def stop_trading_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /stop_trading"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès non autorisé")
            return
        
        TRADING_STATE["auto_trading_enabled"] = False
        await update.message.reply_text("🛑 Trading automatique **DÉSACTIVÉ**", parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Auto trading disabled by user {update.effective_user.id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /help"""
        await self.start_command(update, context)
    
    def run(self):
        """Lance le bot"""
        if not TELEGRAM_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not set in .env")
            return
        
        logger.info("Starting Telegram Bot...")
        
        # Créer application
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Ajouter handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("position", self.position_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("pnl", self.pnl_command))
        self.app.add_handler(CommandHandler("trade", self.trade_command))
        self.app.add_handler(CommandHandler("split", self.split_command))
        self.app.add_handler(CommandHandler("trailing", self.trailing_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("start_trading", self.start_trading_command))
        self.app.add_handler(CommandHandler("stop_trading", self.stop_trading_command))
        
        # Lancer
        logger.info("Telegram Bot started successfully!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Point d'entrée"""
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()
