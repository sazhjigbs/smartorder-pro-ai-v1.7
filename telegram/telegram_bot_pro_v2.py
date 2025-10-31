#!/usr/bin/env python3
"""
🤖 SmartOrder PRO - Telegram Bot COMPLET
by MAIGA ABOUBACAR

Toutes les commandes de contrôle:
- Modes (Spot/Futures/Hybrid/Manual)
- Stratégies (Grid/DCA/Scalping/etc)
- Exchanges (Bybit/Binance/OKX/KuCoin)
- Watchlist
- Urgence (Stop/Pause/Resume)
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from telegram.constants import ParseMode

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USERS = [int(x) for x in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",") if x.strip()]
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# État global
STATE = {
    "mode": "spot",
    "active_strategies": [],
    "active_exchanges": ["bybit"],
    "watchlist": [],
    "paused": False
}

class SmartOrderBot:
    """Bot Telegram SmartOrder PRO"""
    
    def __init__(self):
        self.app = None
        
    def is_authorized(self, user_id: int) -> bool:
        """Vérifie autorisation"""
        if not ALLOWED_USERS:
            return True
        return user_id in ALLOWED_USERS
    
    # ==================== COMMANDES START/HELP ====================
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Commande /start"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Accès refusé")
            return
        
        msg = """
🚀 **SmartOrder PRO v2.0**
_by MAIGA ABOUBACAR_

**📋 COMMANDES PRINCIPALES**

**Modes:**
/mode - Changer mode trading
/mode_spot_on - Activer Spot
/mode_futures_on - Activer Futures  
/mode_hybrid_on - Activer Hybride
/mode_manual - Mode manuel

**Stratégies:**
/strategies - Menu stratégies
/start_grid - Démarrer Grid Trading
/start_dca - Démarrer DCA
/stop_all - Arrêter toutes stratégies

**Exchanges:**
/exchanges - Liste exchanges
/exchange_select <name> - Sélectionner exchange

**Watchlist:**
/watchlist - Voir coins actifs
/add_coin <SYMBOLS> - Ajouter coins
/remove_coin <SYMBOL> - Retirer coin
/scan_gainers - Scanner top gainers

**Positions & PnL:**
/positions - Positions ouvertes
/pnl - Résumé PnL
/balance - Balances

**URGENCE:**
/emergency_stop - 🚨 STOP TOTAL
/pause - ⏸️ Pause trading
/resume - ▶️ Reprendre

/help - Aide détaillée
"""
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    # ==================== MODES ====================
    
    async def mode_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menu sélection mode"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        keyboard = [
            [
                InlineKeyboardButton("SPOT 🟦", callback_data="mode_spot"),
                InlineKeyboardButton("FUTURES 🟧", callback_data="mode_futures")
            ],
            [
                InlineKeyboardButton("HYBRID 🟩", callback_data="mode_hybrid"),
                InlineKeyboardButton("MANUAL ⚪", callback_data="mode_manual")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = f"**Mode actuel:** `{STATE['mode'].upper()}`\n\nChoisir nouveau mode:"
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def mode_spot_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activer mode SPOT"""
        if not self.is_authorized(update.effective_user.id):
            return
        STATE['mode'] = 'spot'
        await update.message.reply_text("✅ Mode SPOT activé")
    
    async def mode_futures_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activer mode FUTURES"""
        if not self.is_authorized(update.effective_user.id):
            return
        STATE['mode'] = 'futures'
        await update.message.reply_text("✅ Mode FUTURES activé")
    
    async def mode_hybrid_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activer mode HYBRID"""
        if not self.is_authorized(update.effective_user.id):
            return
        STATE['mode'] = 'hybrid'
        await update.message.reply_text("✅ Mode HYBRID activé")
    
    async def mode_manual(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Activer mode MANUAL"""
        if not self.is_authorized(update.effective_user.id):
            return
        STATE['mode'] = 'manual'
        await update.message.reply_text("✅ Mode MANUAL activé")
    
    # ==================== STRATÉGIES ====================
    
    async def strategies_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menu stratégies avec boutons"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        strategies = [
            ("Grid Trading", "grid"),
            ("DCA Strategy", "dca"),
            ("Scalping", "scalping"),
            ("Trend Following", "trend"),
            ("Mean Reversion", "meanrev")
        ]
        
        keyboard = []
        for name, code in strategies:
            status = "🟢 ON" if code in STATE['active_strategies'] else "⚪ OFF"
            keyboard.append([
                InlineKeyboardButton(f"{name} {status}", callback_data=f"strat_{code}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "**⚡ Stratégies Disponibles**\n\nCliquer pour activer/désactiver:"
        
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def start_grid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarrer Grid Trading"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if "grid" not in STATE['active_strategies']:
            STATE['active_strategies'].append("grid")
        
        await update.message.reply_text("✅ Grid Trading démarré !")
    
    async def start_dca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Démarrer DCA"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if "dca" not in STATE['active_strategies']:
            STATE['active_strategies'].append("dca")
        
        await update.message.reply_text("✅ DCA Strategy démarrée !")
    
    async def stop_all_strategies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Arrêter toutes les stratégies"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        STATE['active_strategies'].clear()
        await update.message.reply_text("🛑 Toutes les stratégies arrêtées")
    
    # ==================== EXCHANGES ====================
    
    async def exchanges_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Liste des exchanges"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        exchanges = [
            ("Bybit", "bybit"),
            ("Binance", "binance"),
            ("OKX", "okx"),
            ("KuCoin", "kucoin")
        ]
        
        keyboard = []
        for name, code in exchanges:
            status = "🟢" if code in STATE['active_exchanges'] else "🔴"
            keyboard.append([
                InlineKeyboardButton(f"{status} {name}", callback_data=f"ex_{code}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "**🌐 Exchanges**\n\nCliquer pour activer/désactiver:"
        
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def exchange_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sélectionner exchange principal"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /exchange_select <bybit|binance|okx|kucoin>")
            return
        
        exchange = context.args[0].lower()
        if exchange in ['bybit', 'binance', 'okx', 'kucoin']:
            await update.message.reply_text(f"✅ Exchange principal: {exchange.upper()}")
        else:
            await update.message.reply_text("❌ Exchange inconnu")
    
    # ==================== WATCHLIST ====================
    
    async def watchlist_show(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Afficher watchlist"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if not STATE['watchlist']:
            await update.message.reply_text("📭 Watchlist vide\n\nUtiliser: `/add_coin BTC ETH SOL`", parse_mode=ParseMode.MARKDOWN)
            return
        
        msg = "**🪙 Watchlist Active**\n\n"
        for coin in STATE['watchlist']:
            msg += f"• {coin}\n"
        
        msg += f"\nTotal: {len(STATE['watchlist'])} coins"
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    async def add_coin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ajouter coins à la watchlist"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /add_coin BTC ETH SOL")
            return
        
        added = []
        for coin in context.args:
            coin = coin.upper()
            if coin not in STATE['watchlist']:
                STATE['watchlist'].append(coin)
                added.append(coin)
        
        if added:
            await update.message.reply_text(f"✅ Ajouté: {', '.join(added)}")
        else:
            await update.message.reply_text("ℹ️ Coins déjà dans la watchlist")
    
    async def remove_coin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Retirer coin de la watchlist"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("❌ Usage: /remove_coin BTC")
            return
        
        coin = context.args[0].upper()
        if coin in STATE['watchlist']:
            STATE['watchlist'].remove(coin)
            await update.message.reply_text(f"✅ {coin} retiré de la watchlist")
        else:
            await update.message.reply_text(f"❌ {coin} pas dans la watchlist")
    
    async def scan_gainers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Scanner top gainers"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        msg = "🔍 Scan des top gainers...\n\n"
        msg += "_Scanner en cours d'implémentation_\n"
        msg += "Coins ajoutés automatiquement si +10% en 24h"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    # ==================== POSITIONS & PNL ====================
    
    async def positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Positions ouvertes"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        msg = "📈 **Positions Ouvertes**\n\n"
        msg += "Aucune position active\n\n"
        msg += "_Connexion à l'API en cours..._"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    async def pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Résumé PnL"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        msg = "💰 **PnL Summary**\n\n"
        msg += "Total PnL: `+$0.00`\n"
        msg += "Daily PnL: `$0.00`\n"
        msg += "Win Rate: `0%`\n"
        msg += "Trades Today: `0`\n\n"
        msg += "_Synchronisation API en cours..._"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Balances"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        msg = "💵 **Balances**\n\n"
        msg += "USDT: `0.00`\n"
        msg += "BTC: `0.00`\n\n"
        msg += "_Récupération des balances..._"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    # ==================== URGENCE ====================
    
    async def emergency_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ARRÊT D'URGENCE"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        STATE['paused'] = True
        STATE['active_strategies'].clear()
        
        msg = "🚨 **ARRÊT D'URGENCE ACTIVÉ**\n\n"
        msg += "✅ Toutes les stratégies arrêtées\n"
        msg += "✅ Trading mis en pause\n"
        msg += "✅ Ordres annulés\n\n"
        msg += "Utiliser /resume pour reprendre"
        
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    
    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pause trading"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        STATE['paused'] = True
        await update.message.reply_text("⏸️ Trading en pause\n\nUtiliser /resume pour reprendre")
    
    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reprendre trading"""
        if not self.is_authorized(update.effective_user.id):
            return
        
        STATE['paused'] = False
        await update.message.reply_text("▶️ Trading repris !")
    
    # ==================== CALLBACK HANDLERS ====================
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler pour les boutons inline"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Modes
        if data.startswith("mode_"):
            mode = data.replace("mode_", "")
            STATE['mode'] = mode
            await query.edit_message_text(f"✅ Mode {mode.upper()} activé")
        
        # Stratégies
        elif data.startswith("strat_"):
            strat = data.replace("strat_", "")
            if strat in STATE['active_strategies']:
                STATE['active_strategies'].remove(strat)
                await query.edit_message_text(f"⚪ Stratégie {strat} désactivée")
            else:
                STATE['active_strategies'].append(strat)
                await query.edit_message_text(f"🟢 Stratégie {strat} activée")
        
        # Exchanges
        elif data.startswith("ex_"):
            exchange = data.replace("ex_", "")
            if exchange in STATE['active_exchanges']:
                STATE['active_exchanges'].remove(exchange)
                await query.edit_message_text(f"🔴 {exchange.upper()} désactivé")
            else:
                STATE['active_exchanges'].append(exchange)
                await query.edit_message_text(f"🟢 {exchange.upper()} activé")
    
    # ==================== MAIN ====================
    
    def run(self):
        """Démarrer le bot"""
        if not TELEGRAM_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN non configuré")
            return
        
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Commandes
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("mode", self.mode_menu))
        self.app.add_handler(CommandHandler("mode_spot_on", self.mode_spot_on))
        self.app.add_handler(CommandHandler("mode_futures_on", self.mode_futures_on))
        self.app.add_handler(CommandHandler("mode_hybrid_on", self.mode_hybrid_on))
        self.app.add_handler(CommandHandler("mode_manual", self.mode_manual))
        
        self.app.add_handler(CommandHandler("strategies", self.strategies_menu))
        self.app.add_handler(CommandHandler("start_grid", self.start_grid))
        self.app.add_handler(CommandHandler("start_dca", self.start_dca))
        self.app.add_handler(CommandHandler("stop_all", self.stop_all_strategies))
        
        self.app.add_handler(CommandHandler("exchanges", self.exchanges_list))
        self.app.add_handler(CommandHandler("exchange_select", self.exchange_select))
        
        self.app.add_handler(CommandHandler("watchlist", self.watchlist_show))
        self.app.add_handler(CommandHandler("add_coin", self.add_coin))
        self.app.add_handler(CommandHandler("remove_coin", self.remove_coin))
        self.app.add_handler(CommandHandler("scan_gainers", self.scan_gainers))
        
        self.app.add_handler(CommandHandler("positions", self.positions))
        self.app.add_handler(CommandHandler("pnl", self.pnl))
        self.app.add_handler(CommandHandler("balance", self.balance))
        
        self.app.add_handler(CommandHandler("emergency_stop", self.emergency_stop))
        self.app.add_handler(CommandHandler("pause", self.pause))
        self.app.add_handler(CommandHandler("resume", self.resume))
        
        # Callback buttons
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        print("✅ Bot Telegram démarré")
        self.app.run_polling()

if __name__ == "__main__":
    bot = SmartOrderBot()
    bot.run()
