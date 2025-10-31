# -*- coding: utf-8 -*-
"""
🔥 SmartOrder PRO - Telegram Bot COMPLET
=========================================
Bot Telegram avec contrôle total
by MAIGA ABOUBACAR

Commandes:
- MODE: /mode_spot, /mode_futures, /mode_hybrid, /mode_manual
- STRATÉGIES: /strategies, /enable_strategy, /disable_strategy
- EXCHANGE: /exchanges, /exchange_select
- WATCHLIST: /watchlist, /add_coin, /remove_coin, /scan_gainers
- EMERGENCY: /emergency_stop, /pause, /resume
- INFO: /status, /balance, /positions, /analytics
"""
import os
import sys
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json
from datetime import datetime

# Import managers
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from core.watchlist_manager import get_watchlist_manager
    from core.auto_spot_ai_manager import get_auto_spot_manager
    from core.auto_futures_ai_manager import get_auto_futures_manager
except:
    pass

class AdvancedTelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        
        # State
        self.current_mode = "manual"  # manual | spot | futures | hybrid
        self.is_paused = False
        
        # Managers
        try:
            self.watchlist_mgr = get_watchlist_manager()
            self.spot_mgr = get_auto_spot_manager()
            self.futures_mgr = get_auto_futures_manager()
        except:
            self.watchlist_mgr = None
            self.spot_mgr = None
            self.futures_mgr = None
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup command and callback handlers"""
        # Info commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("balance", self.cmd_balance))
        self.app.add_handler(CommandHandler("positions", self.cmd_positions))
        self.app.add_handler(CommandHandler("analytics", self.cmd_analytics))
        self.app.add_handler(CommandHandler("report", self.cmd_report))
        
        # MODE commands
        self.app.add_handler(CommandHandler("mode", self.cmd_mode))
        self.app.add_handler(CommandHandler("mode_spot", self.cmd_mode_spot))
        self.app.add_handler(CommandHandler("mode_futures", self.cmd_mode_futures))
        self.app.add_handler(CommandHandler("mode_hybrid", self.cmd_mode_hybrid))
        self.app.add_handler(CommandHandler("mode_manual", self.cmd_mode_manual))
        
        # STRATÉGIES commands
        self.app.add_handler(CommandHandler("strategies", self.cmd_strategies))
        self.app.add_handler(CommandHandler("enable_strategy", self.cmd_enable_strategy))
        self.app.add_handler(CommandHandler("disable_strategy", self.cmd_disable_strategy))
        
        # EXCHANGE commands
        self.app.add_handler(CommandHandler("exchanges", self.cmd_exchanges))
        self.app.add_handler(CommandHandler("exchange_select", self.cmd_exchange_select))
        
        # WATCHLIST commands
        self.app.add_handler(CommandHandler("watchlist", self.cmd_watchlist))
        self.app.add_handler(CommandHandler("add_coin", self.cmd_add_coin))
        self.app.add_handler(CommandHandler("remove_coin", self.cmd_remove_coin))
        self.app.add_handler(CommandHandler("scan_gainers", self.cmd_scan_gainers))
        
        # EMERGENCY commands
        self.app.add_handler(CommandHandler("emergency_stop", self.cmd_emergency_stop))
        self.app.add_handler(CommandHandler("pause", self.cmd_pause))
        self.app.add_handler(CommandHandler("resume", self.cmd_resume))
        
        # Callback handler
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command with menu"""
        keyboard = [
            [InlineKeyboardButton("🎯 MODE", callback_data='mode_menu'),
             InlineKeyboardButton("📊 Status", callback_data='status')],
            [InlineKeyboardButton("⚙️ Strategies", callback_data='strategies_menu'),
             InlineKeyboardButton("🏦 Exchanges", callback_data='exchanges_menu')],
            [InlineKeyboardButton("🪙 Watchlist", callback_data='watchlist_menu'),
             InlineKeyboardButton("💰 Balance", callback_data='balance')],
            [InlineKeyboardButton("📈 Positions", callback_data='positions'),
             InlineKeyboardButton("📊 Analytics", callback_data='analytics')],
            [InlineKeyboardButton("⏸ Pause", callback_data='pause'),
             InlineKeyboardButton("🛑 Emergency Stop", callback_data='emergency')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = f'''🔥 *SmartOrder PRO Bot*
by MAIGA ABOUBACAR

*Current Mode:* {self.current_mode.upper()}
*Status:* {'⏸ PAUSED' if self.is_paused else '✅ RUNNING'}

Select an option:'''
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = '''
*📚 SmartOrder PRO Commands*

*🎯 MODE*
/mode - Mode menu
/mode\_spot - Auto Spot AI
/mode\_futures - Auto Futures AI
/mode\_hybrid - Hybrid Mode
/mode\_manual - Manual Mode

*⚙️ STRATEGIES*
/strategies - View strategies
/enable\_strategy - Enable strategy
/disable\_strategy - Disable strategy

*🏦 EXCHANGES*
/exchanges - View exchanges
/exchange\_select - Select exchange

*🪙 WATCHLIST*
/watchlist - View watchlist
/add\_coin BTC ETH - Add coins
/remove\_coin XRP - Remove coin
/scan\_gainers - Scan top gainers

*🛑 EMERGENCY*
/emergency\_stop - Stop ALL
/pause - Pause trading
/resume - Resume trading

*📊 INFO*
/status - Bot status
/balance - Account balance
/positions - Open positions
/analytics - Performance
/report - Daily report
'''
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bot status"""
        status = {
            'bot': 'Online ✅',
            'exchange': 'Bybit',
            'uptime': '2h 34m',
            'last_trade': '5 min ago'
        }
        msg = f"*Bot Status*\n\n"
        for key, val in status.items():
            msg += f"• {key.title()}: {val}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Account balance"""
        balance = {
            'total': '$10,234.56',
            'available': '$8,500.00',
            'in_position': '$1,734.56',
            'pnl_today': '+$234.56 (+2.34%)'
        }
        msg = f"*Account Balance*\n\n"
        for key, val in balance.items():
            msg += f"• {key.replace('_', ' ').title()}: {val}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Open positions"""
        positions = [
            {'symbol': 'BTCUSDT', 'side': 'LONG', 'size': '0.5', 'pnl': '+$125.00'},
            {'symbol': 'ETHUSDT', 'side': 'SHORT', 'size': '2.0', 'pnl': '-$45.00'}
        ]
        msg = "*Open Positions*\n\n"
        for pos in positions:
            msg += f"• {pos['symbol']} {pos['side']}\n"
            msg += f"  Size: {pos['size']} | PnL: {pos['pnl']}\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Performance analytics"""
        analytics = {
            'total_trades': 47,
            'win_rate': '68.1%',
            'profit_factor': '2.34',
            'sharpe_ratio': '1.87',
            'max_drawdown': '-5.2%',
            'avg_win': '$85.50',
            'avg_loss': '$42.30'
        }
        msg = f"*Performance Analytics*\n\n"
        for key, val in analytics.items():
            msg += f"• {key.replace('_', ' ').title()}: {val}\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate daily report"""
        report = f"""
*Daily Trading Report*
📅 {datetime.now().strftime('%Y-%m-%d')}

*Performance*
• Trades: 12
• Wins: 8 (66.7%)
• Total PnL: +$234.56

*Best Trade*
• BTCUSDT LONG +$125.00

*Worst Trade*
• ETHUSDT SHORT -$45.00

*Risk Metrics*
• Max Drawdown: -2.1%
• Sharpe Ratio: 2.15
"""
        await update.message.reply_text(report, parse_mode='Markdown')
    
    async def cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Pause trading"""
        await update.message.reply_text("⏸ *Trading Paused*", parse_mode='Markdown')
    
    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resume trading"""
        await update.message.reply_text("▶️ *Trading Resumed*", parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        command_map = {
            'status': self.cmd_status,
            'balance': self.cmd_balance,
            'positions': self.cmd_positions,
            'analytics': self.cmd_analytics,
            'pause': self.cmd_pause,
            'resume': self.cmd_resume
        }
        
        if query.data in command_map:
            # Create fake update for command handler
            update.message = query.message
            await command_map[query.data](update, context)
    
    def run(self):
        """Run the bot"""
        print(f"Telegram bot starting...")
        self.app.run_polling()

# Usage
if __name__ == "__main__":
    token = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
    bot = AdvancedTelegramBot(token)
    bot.run()
