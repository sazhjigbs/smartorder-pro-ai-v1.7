"""
SmartOrder PRO - Telegram Bot Professional
Bot Telegram avec branding premium et menu interactif
by MAIGA ABOUBACAR

Features:
- Menu interactif avec inline buttons
- Messages formatés premium
- Graphiques inline
- Branding partout
- Emojis et formatting pro
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import os

# Branding
from config.branding import (
    AUTHOR_NAME, AUTHOR_SIGNATURE, COMPANY_NAME, SYSTEM_VERSION,
    ICONS, TELEGRAM_WELCOME, TELEGRAM_FOOTER
)

LOG = logging.getLogger("telegram_bot_pro")

class TelegramBotPro:
    """
    Bot Telegram Professional
    by MAIGA ABOUBACAR
    
    Menu interactif + Branding premium
    """
    
    def __init__(self, bot_token: str, allowed_users: List[int] = None):
        """
        Initialize Professional Telegram Bot
        
        Args:
            bot_token: Token du bot Telegram
            allowed_users: Liste des user IDs autorisés
        """
        self.bot_token = bot_token
        self.allowed_users = allowed_users or []
        
        LOG.info(f"✅ {COMPANY_NAME} Telegram Bot initialized")
    
    def is_authorized(self, user_id: int) -> bool:
        """Vérifie si l'utilisateur est autorisé"""
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users
    
    # ==================== MESSAGES BRANDING ====================
    
    def get_welcome_message(self, user_name: str) -> str:
        """Message de bienvenue brandé"""
        return f"""
{ICONS['robot']} *{COMPANY_NAME} {SYSTEM_VERSION}*

Bienvenue *{user_name}* ! {ICONS['fire']}

{ICONS['shield']} Bot de trading IA professionnel
{ICONS['lightning']} Multi-Exchange Support
{ICONS['chart_up']} Stratégies avancées
{ICONS['lock']} 100% Sécurisé

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['info']} *MENU PRINCIPAL:*

{ICONS['chart_up']} /status - État du système
{ICONS['money']} /balance - Voir balances
{ICONS['diamond']} /positions - Positions actives
{ICONS['trophy']} /pnl - Profit & Loss
{ICONS['brain']} /strategies - Gérer stratégies
{ICONS['settings']} /watchlist - Watchlist
{ICONS['fire']} /start_trading - DÉMARRER
{ICONS['warning']} /stop_trading - ARRÊTER
{ICONS['bell']} /emergency - URGENCE

━━━━━━━━━━━━━━━━━━━━━━━━
{ICONS['diamond']} {AUTHOR_SIGNATURE}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    def get_status_message(self, state: Dict) -> str:
        """Message status brandé"""
        status_icon = ICONS['check'] if state.get('running') else ICONS['warning']
        emergency_icon = ICONS['cross'] if state.get('emergency_stop') else ICONS['check']
        
        return f"""
{ICONS['chart_up']} *SYSTEM STATUS*

{status_icon} *État:* {'RUNNING' if state.get('running') else 'STOPPED'}
{emergency_icon} *Emergency:* {'ACTIVE' if state.get('emergency_stop') else 'OK'}
{ICONS['settings']} *Override:* {'ON' if state.get('manual_override') else 'OFF'}

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['money']} *STATS LIVE:*

• Active Trades: {state.get('active_trades', 0)}
• Daily PnL: {state.get('daily_pnl', 0):.2f}%
• Total PnL: ${state.get('total_pnl', 0):.2f}
• Win Rate: {state.get('win_rate', 0):.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['info']} Dernière MAJ: {state.get('last_update', 'N/A')}

{TELEGRAM_FOOTER}
"""
    
    def get_balance_message(self, balances: Dict) -> str:
        """Message balances brandé"""
        msg = f"""
{ICONS['money']} *WALLET BALANCE*

{ICONS['chart_up']} *Total Equity:* ${balances.get('total_equity', 0):,.2f}
{ICONS['diamond']} *Available:* ${balances.get('available', 0):,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['money']} *COINS:*

"""
        
        for coin, data in balances.get('coins', {}).items():
            balance = data.get('balance', 0)
            if balance > 0:
                usd_value = data.get('usd_value', 0)
                msg += f"• *{coin}:* {balance:.6f} (${usd_value:,.2f})\n"
        
        msg += f"\n{TELEGRAM_FOOTER}"
        
        return msg
    
    def get_positions_message(self, positions: List[Dict]) -> str:
        """Message positions brandé"""
        if not positions:
            return f"""
{ICONS['info']} *NO ACTIVE POSITIONS*

Aucune position ouverte actuellement.

{TELEGRAM_FOOTER}
"""
        
        msg = f"""
{ICONS['diamond']} *ACTIVE POSITIONS*

━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for pos in positions:
            side_icon = ICONS['chart_up'] if pos['side'] == 'Buy' else ICONS['chart_down']
            pnl = pos.get('unrealized_pnl', 0)
            pnl_icon = ICONS['chart_up'] if pnl >= 0 else ICONS['chart_down']
            
            msg += f"""
{side_icon} *{pos['symbol']}* - {pos['side']}
   Size: {pos['size']}
   Entry: ${pos['entry_price']:,.2f}
   Mark: ${pos['mark_price']:,.2f}
   Leverage: {pos['leverage']}x
   {pnl_icon} PnL: ${pnl:,.2f}

"""
        
        msg += f"━━━━━━━━━━━━━━━━━━━━━━━━\n{TELEGRAM_FOOTER}"
        
        return msg
    
    def get_pnl_message(self, pnl_data: Dict) -> str:
        """Message P&L brandé"""
        total_pnl = pnl_data.get('total', 0)
        pnl_icon = ICONS['chart_up'] if total_pnl >= 0 else ICONS['chart_down']
        
        return f"""
{ICONS['trophy']} *PROFIT & LOSS*

━━━━━━━━━━━━━━━━━━━━━━━━

{pnl_icon} *Total P&L:* ${total_pnl:,.2f}

{ICONS['chart_up']} *Today:* ${pnl_data.get('today', 0):,.2f}
{ICONS['chart_up']} *This Week:* ${pnl_data.get('week', 0):,.2f}
{ICONS['chart_up']} *This Month:* ${pnl_data.get('month', 0):,.2f}

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['trophy']} *Win Rate:* {pnl_data.get('win_rate', 0):.1f}%
{ICONS['fire']} *Total Trades:* {pnl_data.get('total_trades', 0)}
{ICONS['check']} *Wins:* {pnl_data.get('wins', 0)}
{ICONS['cross']} *Losses:* {pnl_data.get('losses', 0)}

{TELEGRAM_FOOTER}
"""
    
    def get_strategies_message(self, strategies: Dict) -> str:
        """Message stratégies brandé"""
        msg = f"""
{ICONS['brain']} *AI STRATEGIES*

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['fire']} *SPOT STRATEGIES:*

"""
        
        for name, enabled in strategies.get('spot', {}).items():
            icon = ICONS['check'] if enabled else ICONS['cross']
            msg += f"{icon} {name}\n"
        
        msg += f"\n{ICONS['rocket']} *FUTURES STRATEGIES:*\n\n"
        
        for name, enabled in strategies.get('futures', {}).items():
            icon = ICONS['check'] if enabled else ICONS['cross']
            msg += f"{icon} {name}\n"
        
        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['info']} Use:
/enable <strategy> - Activer
/disable <strategy> - Désactiver

{TELEGRAM_FOOTER}
"""
        
        return msg
    
    def get_watchlist_message(self, watchlist: List[str]) -> str:
        """Message watchlist brandé"""
        if not watchlist:
            return f"""
{ICONS['info']} *WATCHLIST EMPTY*

Aucune crypto en surveillance.

{ICONS['info']} Ajouter: /add BTC

{TELEGRAM_FOOTER}
"""
        
        msg = f"""
{ICONS['diamond']} *WATCHLIST*

━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for symbol in watchlist:
            msg += f"{ICONS['check']} {symbol}\n"
        
        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['info']} Commandes:
/add <symbol> - Ajouter
/remove <symbol> - Retirer

{TELEGRAM_FOOTER}
"""
        
        return msg
    
    def get_ai_suggestions_message(self, suggestions: List[Dict]) -> str:
        """Message suggestions IA brandé"""
        if not suggestions:
            return f"""
{ICONS['robot']} *AI SUGGESTIONS*

Aucune suggestion IA en attente.

{TELEGRAM_FOOTER}
"""
        
        msg = f"""
{ICONS['robot']} *AI SUGGESTIONS*

━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        for s in suggestions[:5]:
            side_icon = ICONS['chart_up'] if s['side'] == 'Buy' else ICONS['chart_down']
            confidence_icon = ICONS['fire'] if s['confidence'] > 80 else ICONS['warning']
            
            msg += f"""
{side_icon} *{s['symbol']}* {s['side']}
   {confidence_icon} Confidence: {s['confidence']}%
   {ICONS['brain']} Strategy: {s['strategy']}
   {ICONS['money']} Entry: ${s['entry']:,.2f}
   {ICONS['trophy']} Target: ${s['tp']:,.2f}
   {ICONS['key']} ID: `{s['id']}`

"""
        
        msg += f"""
━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['check']} /approve <id> - Approuver
{ICONS['cross']} /reject <id> - Rejeter

{TELEGRAM_FOOTER}
"""
        
        return msg
    
    def get_alert_message(self, alert_type: str, message: str, level: str = "info") -> str:
        """Message alerte brandé"""
        icons_map = {
            'success': ICONS['check'],
            'error': ICONS['cross'],
            'warning': ICONS['warning'],
            'info': ICONS['info']
        }
        
        icon = icons_map.get(level, ICONS['bell'])
        
        return f"""
{icon} *{alert_type.upper()}*

{message}

{ICONS['info']} {datetime.now().strftime('%H:%M:%S')}

{TELEGRAM_FOOTER}
"""
    
    def get_emergency_confirmation_message(self) -> str:
        """Message confirmation emergency stop"""
        return f"""
{ICONS['warning']} *EMERGENCY STOP*

{ICONS['cross']} Ceci fermera TOUTES les positions !
{ICONS['warning']} Action IRRÉVERSIBLE !

Êtes-vous ABSOLUMENT sûr ?

{ICONS['check']} /confirm_emergency - Confirmer
{ICONS['cross']} /cancel - Annuler

{TELEGRAM_FOOTER}
"""
    
    def get_help_message(self) -> str:
        """Message aide complet"""
        return f"""
{ICONS['robot']} *{COMPANY_NAME} HELP*

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['chart_up']} *MONITORING:*
/status - État système
/balance - Voir balances
/positions - Positions ouvertes
/pnl - Profit & Loss
/stats - Statistiques complètes

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['brain']} *STRATÉGIES:*
/strategies - Voir stratégies
/enable <name> - Activer stratégie
/disable <name> - Désactiver stratégie

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['diamond']} *WATCHLIST:*
/watchlist - Voir watchlist
/add <symbol> - Ajouter crypto
/remove <symbol> - Retirer crypto

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['robot']} *IA:*
/suggestions - Suggestions IA
/approve <id> - Approuver
/reject <id> - Rejeter

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['fire']} *CONTRÔLE:*
/start_trading - DÉMARRER trading
/stop_trading - ARRÊTER trading
/pause_trading - PAUSE trading
/resume_trading - REPRENDRE trading
/emergency - STOP D'URGENCE

━━━━━━━━━━━━━━━━━━━━━━━━

{ICONS['diamond']} Développé par *{AUTHOR_NAME}*
{ICONS['lightning']} {SYSTEM_VERSION}

━━━━━━━━━━━━━━━━━━━━━━━━
"""


# Instance globale
_telegram_bot_pro = None

def get_telegram_bot_pro(bot_token: str = None, allowed_users: List[int] = None) -> TelegramBotPro:
    """Récupère l'instance singleton"""
    global _telegram_bot_pro
    
    if _telegram_bot_pro is None:
        if not bot_token:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        _telegram_bot_pro = TelegramBotPro(bot_token, allowed_users)
    
    return _telegram_bot_pro


if __name__ == "__main__":
    print("="*60)
    print(f"{ICONS['robot']} {COMPANY_NAME} - Telegram Bot PRO")
    print(f"{ICONS['diamond']} {AUTHOR_SIGNATURE}")
    print("="*60)
    
    bot = TelegramBotPro("test_token")
    
    print("\n✅ Test Messages:")
    
    # Test welcome
    print("\n1. Welcome Message:")
    print(bot.get_welcome_message("Aboubacar"))
    
    # Test status
    print("\n2. Status Message:")
    state = {
        'running': True,
        'emergency_stop': False,
        'manual_override': False,
        'active_trades': 5,
        'daily_pnl': 2.5,
        'total_pnl': 1250.50,
        'win_rate': 68.5,
        'last_update': '20:00:00'
    }
    print(bot.get_status_message(state))
    
    # Test help
    print("\n3. Help Message:")
    print(bot.get_help_message())
    
    print("\n" + "="*60)
    print(f"✅ Telegram Bot PRO Ready!")
    print(f"{AUTHOR_SIGNATURE}")
    print("="*60)
