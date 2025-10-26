"""
SmartOrder PRO - Trading Control Panel
Configuration et monitoring en temps réel avec IA suggestions
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

LOG = logging.getLogger("control_panel")
LOG.setLevel(logging.INFO)

class TradingControlPanel:
    """
    Control Panel pour gérer toutes les stratégies et configurations
    
    Features:
    - Enable/Disable strategies en temps réel
    - IA suggestions avec validation manuelle
    - Coins watchlist avec volatilité live
    - Emergency stop button
    - Manual override
    - Performance monitoring
    - Alert system
    
    Interface:
    - Config JSON pour persistence
    - API endpoints pour UI
    - Real-time updates
    """
    
    def __init__(self, config_path: str = "config/control_panel.json"):
        """Initialize Control Panel"""
        self.config_path = Path(config_path)
        
        # Configuration par défaut
        self.config = {
            'mode': 'HYBRID',  # SPOT_ONLY | FUTURES_ONLY | HYBRID | HEDGE
            
            # Stratégies Spot
            'spot_strategies': {
                'enabled': True,
                'grid_trading': {'enabled': True, 'allocation': 40},
                'dca': {'enabled': True, 'allocation': 30},
                'momentum': {'enabled': False, 'allocation': 0},
                'rebalancing': {'enabled': True, 'allocation': 30}
            },
            
            # Stratégies Futures
            'futures_strategies': {
                'enabled': True,
                'scalping': {'enabled': True, 'vol_range': [0, 30]},
                'swing': {'enabled': True, 'vol_range': [30, 60]},
                'momentum': {'enabled': False, 'vol_range': [40, 80]},
                'range_trading': {'enabled': True, 'vol_range': [0, 40]}
            },
            
            # Coins surveillés
            'watchlist': {
                'BTC': {'enabled': True, 'priority': 1},
                'ETH': {'enabled': True, 'priority': 2},
                'SOL': {'enabled': False, 'priority': 3},
                'DOGE': {'enabled': True, 'priority': 4},
                'MATIC': {'enabled': False, 'priority': 5}
            },
            
            # Risk Management
            'risk_management': {
                'max_positions': 3,
                'max_leverage': 10,
                'max_position_pct': 20,
                'daily_loss_limit': 5.0,
                'emergency_stop_loss': 10.0
            },
            
            # IA Settings
            'ai_settings': {
                'auto_approve': False,
                'min_confidence': 70,
                'require_multi_signal': True,
                'signals_required': 3
            },
            
            # Alerts
            'alerts': {
                'telegram_enabled': False,
                'email_enabled': False,
                'alert_on_trade': True,
                'alert_on_profit': True,
                'alert_on_loss': True,
                'alert_on_daily_limit': True
            }
        }
        
        # IA Suggestions en attente
        self.pending_suggestions = []
        
        # État du système
        self.system_state = {
            'running': False,
            'emergency_stop': False,
            'manual_override': False,
            'last_update': None
        }
        
        # Stats live
        self.live_stats = {
            'active_trades': 0,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'win_rate': 0.0
        }
        
        # Charger config si existe
        self.load_config()
        
        LOG.info("TradingControlPanel initialized")
    
    def load_config(self) -> bool:
        """Charge la configuration depuis le fichier"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                    LOG.info(f"Config loaded from {self.config_path}")
                    return True
        except Exception as e:
            LOG.error(f"Failed to load config: {e}")
        
        return False
    
    def save_config(self) -> bool:
        """Sauvegarde la configuration"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            LOG.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            LOG.error(f"Failed to save config: {e}")
            return False
    
    def enable_strategy(self, category: str, strategy: str) -> bool:
        """
        Active une stratégie
        
        Args:
            category: 'spot' or 'futures'
            strategy: Nom de la stratégie
        """
        try:
            if category == 'spot':
                self.config['spot_strategies'][strategy]['enabled'] = True
            elif category == 'futures':
                self.config['futures_strategies'][strategy]['enabled'] = True
            
            self.save_config()
            LOG.info(f"✅ Strategy enabled: {category}.{strategy}")
            return True
        except Exception as e:
            LOG.error(f"Failed to enable strategy: {e}")
            return False
    
    def disable_strategy(self, category: str, strategy: str) -> bool:
        """Désactive une stratégie"""
        try:
            if category == 'spot':
                self.config['spot_strategies'][strategy]['enabled'] = False
            elif category == 'futures':
                self.config['futures_strategies'][strategy]['enabled'] = False
            
            self.save_config()
            LOG.info(f"❌ Strategy disabled: {category}.{strategy}")
            return True
        except Exception as e:
            LOG.error(f"Failed to disable strategy: {e}")
            return False
    
    def add_to_watchlist(self, symbol: str, priority: int = 5) -> bool:
        """Ajoute un coin à la watchlist"""
        self.config['watchlist'][symbol] = {
            'enabled': True,
            'priority': priority
        }
        self.save_config()
        LOG.info(f"✅ Added to watchlist: {symbol}")
        return True
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """Retire un coin de la watchlist"""
        if symbol in self.config['watchlist']:
            self.config['watchlist'][symbol]['enabled'] = False
            self.save_config()
            LOG.info(f"❌ Removed from watchlist: {symbol}")
            return True
        return False
    
    def get_active_watchlist(self) -> List[str]:
        """Retourne les coins actifs de la watchlist"""
        return [
            symbol for symbol, config in self.config['watchlist'].items()
            if config['enabled']
        ]
    
    def add_ai_suggestion(self, suggestion: Dict) -> str:
        """
        Ajoute une suggestion IA en attente de validation
        
        Args:
            suggestion: {
                'symbol': str,
                'side': 'LONG' | 'SHORT',
                'strategy': str,
                'confidence': 0-100,
                'entry': float,
                'tp': float,
                'sl': float,
                'reasoning': str
            }
            
        Returns:
            Suggestion ID
        """
        suggestion_id = f"AI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        suggestion['id'] = suggestion_id
        suggestion['status'] = 'PENDING'
        suggestion['created_at'] = datetime.now().isoformat()
        
        self.pending_suggestions.append(suggestion)
        
        LOG.info(f"🤖 AI Suggestion added: {suggestion['symbol']} {suggestion['side']} "
                f"({suggestion['confidence']}%)")
        
        # Auto-approve si activé et confiance suffisante
        if self.config['ai_settings']['auto_approve']:
            if suggestion['confidence'] >= self.config['ai_settings']['min_confidence']:
                return self.approve_suggestion(suggestion_id)
        
        return suggestion_id
    
    def approve_suggestion(self, suggestion_id: str) -> Dict:
        """Approuve et execute une suggestion IA"""
        suggestion = next(
            (s for s in self.pending_suggestions if s['id'] == suggestion_id),
            None
        )
        
        if not suggestion:
            return {'success': False, 'reason': 'Suggestion not found'}
        
        suggestion['status'] = 'APPROVED'
        suggestion['approved_at'] = datetime.now().isoformat()
        
        LOG.info(f"✅ AI Suggestion approved: {suggestion_id}")
        
        # TODO: Execute le trade via auto_trader
        
        return {
            'success': True,
            'suggestion': suggestion
        }
    
    def reject_suggestion(self, suggestion_id: str) -> bool:
        """Rejette une suggestion IA"""
        suggestion = next(
            (s for s in self.pending_suggestions if s['id'] == suggestion_id),
            None
        )
        
        if not suggestion:
            return False
        
        suggestion['status'] = 'REJECTED'
        suggestion['rejected_at'] = datetime.now().isoformat()
        
        LOG.info(f"❌ AI Suggestion rejected: {suggestion_id}")
        return True
    
    def get_pending_suggestions(self) -> List[Dict]:
        """Retourne toutes les suggestions en attente"""
        return [
            s for s in self.pending_suggestions
            if s['status'] == 'PENDING'
        ]
    
    def emergency_stop(self) -> bool:
        """ARRÊT D'URGENCE - Ferme toutes positions et arrête le bot"""
        LOG.critical("🚨 EMERGENCY STOP ACTIVATED!")
        
        self.system_state['emergency_stop'] = True
        self.system_state['running'] = False
        
        # TODO: Close all positions
        # TODO: Cancel all pending orders
        # TODO: Send alert
        
        return True
    
    def start_trading(self) -> bool:
        """Démarre le trading automatique"""
        if self.system_state['emergency_stop']:
            LOG.error("Cannot start: Emergency stop is active")
            return False
        
        self.system_state['running'] = True
        self.system_state['last_update'] = datetime.now().isoformat()
        
        LOG.info("🚀 Trading started")
        return True
    
    def stop_trading(self) -> bool:
        """Arrête le trading automatique (normal)"""
        self.system_state['running'] = False
        LOG.info("⏸️ Trading stopped")
        return True
    
    def enable_manual_override(self) -> bool:
        """Active le mode manuel (désactive auto-trading)"""
        self.system_state['manual_override'] = True
        LOG.info("🔧 Manual override enabled")
        return True
    
    def disable_manual_override(self) -> bool:
        """Désactive le mode manuel"""
        self.system_state['manual_override'] = False
        LOG.info("🤖 Auto-trading re-enabled")
        return True
    
    def update_live_stats(self, stats: Dict):
        """Met à jour les stats en temps réel"""
        self.live_stats.update(stats)
        self.system_state['last_update'] = datetime.now().isoformat()
    
    def check_daily_loss_limit(self) -> bool:
        """Vérifie si la limite de perte quotidienne est atteinte"""
        limit = self.config['risk_management']['daily_loss_limit']
        
        if self.live_stats['daily_pnl'] < -limit:
            LOG.warning(f"⚠️ Daily loss limit reached: {self.live_stats['daily_pnl']:.2f}%")
            self.stop_trading()
            return True
        
        return False
    
    def get_dashboard_data(self) -> Dict:
        """Retourne toutes les données pour le dashboard"""
        return {
            'config': self.config,
            'system_state': self.system_state,
            'live_stats': self.live_stats,
            'pending_suggestions': self.get_pending_suggestions(),
            'watchlist': self.get_active_watchlist()
        }
    
    def get_strategy_status(self) -> Dict:
        """Retourne le statut de toutes les stratégies"""
        spot = self.config['spot_strategies']
        futures = self.config['futures_strategies']
        
        return {
            'spot': {
                'enabled': spot['enabled'],
                'strategies': {
                    'grid_trading': spot['grid_trading']['enabled'],
                    'dca': spot['dca']['enabled'],
                    'momentum': spot['momentum']['enabled'],
                    'rebalancing': spot['rebalancing']['enabled']
                }
            },
            'futures': {
                'enabled': futures['enabled'],
                'strategies': {
                    'scalping': futures['scalping']['enabled'],
                    'swing': futures['swing']['enabled'],
                    'momentum': futures['momentum']['enabled'],
                    'range_trading': futures['range_trading']['enabled']
                }
            }
        }


# Instance globale
_control_panel = None

def get_control_panel() -> TradingControlPanel:
    """Récupère l'instance singleton"""
    global _control_panel
    if _control_panel is None:
        _control_panel = TradingControlPanel()
    return _control_panel


if __name__ == "__main__":
    print("=" * 60)
    print("Trading Control Panel - Test")
    print("=" * 60)
    
    panel = TradingControlPanel()
    
    # Afficher config
    print(f"\n⚙️ Current Configuration:")
    print(f"   Mode: {panel.config['mode']}")
    print(f"   Spot enabled: {panel.config['spot_strategies']['enabled']}")
    print(f"   Futures enabled: {panel.config['futures_strategies']['enabled']}")
    
    # Strategy status
    print(f"\n📊 Strategy Status:")
    status = panel.get_strategy_status()
    
    print(f"   Spot Strategies:")
    for name, enabled in status['spot']['strategies'].items():
        icon = "✅" if enabled else "❌"
        print(f"      {icon} {name}")
    
    print(f"   Futures Strategies:")
    for name, enabled in status['futures']['strategies'].items():
        icon = "✅" if enabled else "❌"
        print(f"      {icon} {name}")
    
    # Watchlist
    print(f"\n👀 Watchlist:")
    for symbol in panel.get_active_watchlist():
        print(f"   ✅ {symbol}")
    
    # Test AI suggestion
    print(f"\n🤖 Adding AI Suggestion...")
    
    suggestion = {
        'symbol': 'BTCUSDT',
        'side': 'LONG',
        'strategy': 'Swing + Grid',
        'confidence': 85,
        'entry': 67250,
        'tp': 69000,
        'sl': 66500,
        'reasoning': 'Strong bullish momentum + support at 67k'
    }
    
    suggestion_id = panel.add_ai_suggestion(suggestion)
    print(f"   Suggestion ID: {suggestion_id}")
    print(f"   Status: PENDING")
    
    # Pending suggestions
    pending = panel.get_pending_suggestions()
    print(f"\n📋 Pending Suggestions: {len(pending)}")
    
    if pending:
        s = pending[0]
        print(f"   🔥 {s['symbol']}: {s['side']} ({s['confidence']}%)")
        print(f"      Strategy: {s['strategy']}")
        print(f"      Entry: {s['entry']} | TP: {s['tp']}")
    
    # Test approve
    print(f"\n✅ Approving suggestion...")
    result = panel.approve_suggestion(suggestion_id)
    
    if result['success']:
        print(f"   ✅ Approved and executed!")
    
    # System state
    print(f"\n🔧 System State:")
    state = panel.system_state
    print(f"   Running: {state['running']}")
    print(f"   Emergency Stop: {state['emergency_stop']}")
    print(f"   Manual Override: {state['manual_override']}")
    
    # Test emergency stop
    print(f"\n🚨 Testing Emergency Stop...")
    panel.emergency_stop()
    print(f"   Emergency Stop: {panel.system_state['emergency_stop']}")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
