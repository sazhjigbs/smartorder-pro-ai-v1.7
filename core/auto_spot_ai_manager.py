#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Auto Spot AI Manager
=========================================
Gestionnaire intelligent pour trading SPOT automatisé
by MAIGA ABOUBACAR

Features:
- Sélection IA de stratégies (Infinity Grid, DCA, Scalping, Mean Reversion, Rebalancing)
- Allocation dynamique du capital
- Groupes de stratégies paramétrables
- Gestion multi-coins
- Performance tracking par stratégie
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

# Import strategies
sys.path.insert(0, str(Path(__file__).parent.parent))

LOG = logging.getLogger("auto_spot_ai")
LOG.setLevel(logging.INFO)

class SpotStrategy(Enum):
    """Types de stratégies SPOT disponibles"""
    INFINITY_GRID = "infinity_grid"
    DCA_INTELLIGENT = "dca_intelligent"
    SCALPING_VOLATILITY = "scalping_volatility"
    MEAN_REVERSION = "mean_reversion"
    SMART_REBALANCING = "smart_rebalancing"


@dataclass
class StrategyGroup:
    """Groupe de stratégies activables ensemble"""
    name: str
    strategies: List[SpotStrategy]
    allocation_percent: Dict[str, float]  # Strategy name -> % allocation
    enabled: bool = True
    description: str = ""
    
    def to_dict(self):
        return {
            "name": self.name,
            "strategies": [s.value for s in self.strategies],
            "allocation_percent": self.allocation_percent,
            "enabled": self.enabled,
            "description": self.description
        }


@dataclass
class StrategyPerformance:
    """Performance d'une stratégie"""
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    sharpe_ratio: float = 0.0
    last_updated: str = ""


class AutoSpotAIManager:
    """
    Gestionnaire Auto Spot AI
    
    Gère le trading spot automatisé avec:
    - Sélection intelligente de stratégies par l'IA
    - Groupes de stratégies paramétrables
    - Allocation dynamique du capital
    - Performance tracking
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize Auto Spot AI Manager
        
        Args:
            config_dir: Répertoire de configuration
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "auto_spot_config.json"
        self.performance_file = self.config_dir / "auto_spot_performance.json"
        
        # Load configuration
        self.config = self._load_config()
        
        # Strategy groups
        self.strategy_groups: Dict[str, StrategyGroup] = {}
        self._initialize_strategy_groups()
        
        # Performance tracking
        self.performance: Dict[str, StrategyPerformance] = {}
        self._load_performance()
        
        # State
        self.is_running = False
        self.active_strategies = []
        self.selected_coins = []
        
        LOG.info("✅ Auto Spot AI Manager initialized")
    
    def _load_config(self) -> Dict:
        """Charge la configuration"""
        default_config = {
            "enabled": False,
            "mode": "auto",  # auto | manual | hybrid
            "capital_allocation": {
                "total_capital_usd": 1000,
                "max_per_coin_percent": 20,
                "reserve_percent": 10
            },
            "risk_management": {
                "max_positions": 5,
                "max_daily_loss_percent": 5.0,
                "max_position_size_usd": 200,
                "stop_loss_percent": 2.5,
                "take_profit_percent": 5.0
            },
            "ai_selector": {
                "enabled": True,
                "min_confidence": 0.7,
                "rebalance_interval_hours": 24,
                "auto_switch_strategies": True
            },
            "filters": {
                "min_volume_24h_usd": 50_000_000,
                "min_liquidity": 1_000_000,
                "max_volatility_percent": 15.0
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
                LOG.info("✅ Auto Spot config loaded")
            except Exception as e:
                LOG.error(f"❌ Error loading config: {e}")
        else:
            self._save_config(default_config)
        
        return default_config
    
    def _save_config(self, config: Dict = None):
        """Sauvegarde la configuration"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            LOG.info("✅ Auto Spot config saved")
        except Exception as e:
            LOG.error(f"❌ Error saving config: {e}")
    
    def _initialize_strategy_groups(self):
        """Initialise les groupes de stratégies prédéfinis"""
        # Groupe 1: Conservative (Grid + DCA)
        self.strategy_groups["conservative"] = StrategyGroup(
            name="Conservative",
            strategies=[SpotStrategy.INFINITY_GRID, SpotStrategy.DCA_INTELLIGENT],
            allocation_percent={
                "infinity_grid": 60.0,
                "dca_intelligent": 40.0
            },
            enabled=True,
            description="Stratégies conservatrices avec grille et DCA"
        )
        
        # Groupe 2: Aggressive (Scalping + Mean Reversion)
        self.strategy_groups["aggressive"] = StrategyGroup(
            name="Aggressive",
            strategies=[SpotStrategy.SCALPING_VOLATILITY, SpotStrategy.MEAN_REVERSION],
            allocation_percent={
                "scalping_volatility": 50.0,
                "mean_reversion": 50.0
            },
            enabled=False,
            description="Stratégies agressives pour marchés volatils"
        )
        
        # Groupe 3: Balanced (Mix de tout)
        self.strategy_groups["balanced"] = StrategyGroup(
            name="Balanced",
            strategies=[
                SpotStrategy.INFINITY_GRID,
                SpotStrategy.DCA_INTELLIGENT,
                SpotStrategy.MEAN_REVERSION
            ],
            allocation_percent={
                "infinity_grid": 40.0,
                "dca_intelligent": 30.0,
                "mean_reversion": 30.0
            },
            enabled=False,
            description="Mix équilibré de stratégies"
        )
        
        # Groupe 4: Grid Only
        self.strategy_groups["grid_only"] = StrategyGroup(
            name="Grid Only",
            strategies=[SpotStrategy.INFINITY_GRID],
            allocation_percent={
                "infinity_grid": 100.0
            },
            enabled=False,
            description="Uniquement Infinity Grid Trading"
        )
        
        # Groupe 5: DCA Only
        self.strategy_groups["dca_only"] = StrategyGroup(
            name="DCA Only",
            strategies=[SpotStrategy.DCA_INTELLIGENT],
            allocation_percent={
                "dca_intelligent": 100.0
            },
            enabled=False,
            description="Uniquement DCA Intelligent"
        )
        
        LOG.info(f"✅ Initialized {len(self.strategy_groups)} strategy groups")
    
    def _load_performance(self):
        """Charge les performances des stratégies"""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r') as f:
                    data = json.load(f)
                    for strategy_name, perf_data in data.items():
                        self.performance[strategy_name] = StrategyPerformance(**perf_data)
                LOG.info(f"✅ Loaded performance for {len(self.performance)} strategies")
            except Exception as e:
                LOG.error(f"❌ Error loading performance: {e}")
    
    def _save_performance(self):
        """Sauvegarde les performances"""
        try:
            data = {name: asdict(perf) for name, perf in self.performance.items()}
            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2)
            LOG.info("✅ Performance saved")
        except Exception as e:
            LOG.error(f"❌ Error saving performance: {e}")
    
    def enable_strategy_group(self, group_name: str) -> bool:
        """Active un groupe de stratégies"""
        if group_name not in self.strategy_groups:
            LOG.error(f"❌ Strategy group '{group_name}' not found")
            return False
        
        # Disable all other groups (only one active at a time)
        for name, group in self.strategy_groups.items():
            group.enabled = (name == group_name)
        
        LOG.info(f"✅ Enabled strategy group: {group_name}")
        self._update_active_strategies()
        return True
    
    def disable_all_groups(self):
        """Désactive tous les groupes"""
        for group in self.strategy_groups.values():
            group.enabled = False
        self.active_strategies = []
        LOG.info("⏸️ All strategy groups disabled")
    
    def _update_active_strategies(self):
        """Met à jour la liste des stratégies actives"""
        self.active_strategies = []
        
        for group in self.strategy_groups.values():
            if group.enabled:
                self.active_strategies.extend(group.strategies)
        
        LOG.info(f"✅ Active strategies: {[s.value for s in self.active_strategies]}")
    
    def add_strategy_to_group(self, group_name: str, strategy: SpotStrategy, allocation_percent: float = 0.0):
        """Ajoute une stratégie à un groupe"""
        if group_name not in self.strategy_groups:
            LOG.error(f"❌ Strategy group '{group_name}' not found")
            return False
        
        group = self.strategy_groups[group_name]
        
        if strategy not in group.strategies:
            group.strategies.append(strategy)
            group.allocation_percent[strategy.value] = allocation_percent
            LOG.info(f"✅ Added {strategy.value} to group {group_name}")
            return True
        
        return False
    
    def remove_strategy_from_group(self, group_name: str, strategy: SpotStrategy):
        """Retire une stratégie d'un groupe"""
        if group_name not in self.strategy_groups:
            return False
        
        group = self.strategy_groups[group_name]
        
        if strategy in group.strategies:
            group.strategies.remove(strategy)
            if strategy.value in group.allocation_percent:
                del group.allocation_percent[strategy.value]
            LOG.info(f"✅ Removed {strategy.value} from group {group_name}")
            return True
        
        return False
    
    def create_custom_group(self, name: str, strategies: List[SpotStrategy], 
                           allocation: Dict[str, float], description: str = ""):
        """Crée un groupe de stratégies personnalisé"""
        if name in self.strategy_groups:
            LOG.warning(f"⚠️ Group '{name}' already exists")
            return False
        
        self.strategy_groups[name] = StrategyGroup(
            name=name,
            strategies=strategies,
            allocation_percent=allocation,
            enabled=False,
            description=description
        )
        
        LOG.info(f"✅ Created custom strategy group: {name}")
        return True
    
    def delete_custom_group(self, name: str) -> bool:
        """Supprime un groupe personnalisé"""
        # Protect default groups
        default_groups = ["conservative", "aggressive", "balanced", "grid_only", "dca_only"]
        
        if name in default_groups:
            LOG.error(f"❌ Cannot delete default group: {name}")
            return False
        
        if name in self.strategy_groups:
            del self.strategy_groups[name]
            LOG.info(f"✅ Deleted custom group: {name}")
            return True
        
        return False
    
    def get_active_group(self) -> Optional[StrategyGroup]:
        """Récupère le groupe actif"""
        for group in self.strategy_groups.values():
            if group.enabled:
                return group
        return None
    
    def get_all_groups(self) -> Dict[str, StrategyGroup]:
        """Récupère tous les groupes"""
        return self.strategy_groups
    
    def calculate_capital_allocation(self) -> Dict[str, float]:
        """
        Calcule l'allocation de capital par stratégie
        
        Returns:
            Dict[strategy_name, capital_usd]
        """
        active_group = self.get_active_group()
        if not active_group:
            return {}
        
        total_capital = self.config["capital_allocation"]["total_capital_usd"]
        reserve_percent = self.config["capital_allocation"]["reserve_percent"]
        
        # Capital disponible après réserve
        available_capital = total_capital * (1 - reserve_percent / 100)
        
        # Allocation par stratégie
        allocation = {}
        for strategy_name, percent in active_group.allocation_percent.items():
            allocation[strategy_name] = available_capital * (percent / 100)
        
        return allocation
    
    def ai_select_best_strategy(self, market_conditions: Dict) -> SpotStrategy:
        """
        IA sélectionne la meilleure stratégie selon conditions marché
        
        Args:
            market_conditions: Dict avec volatility, trend, volume, etc.
        
        Returns:
            Meilleure stratégie recommandée
        """
        # Analyse des conditions de marché
        volatility = market_conditions.get("volatility", 0)
        trend = market_conditions.get("trend", "neutral")  # bullish | bearish | neutral
        volume = market_conditions.get("volume", 0)
        
        # Logique de sélection IA
        if volatility > 10 and volume > 100_000_000:
            # Marché volatile et liquide -> Scalping
            return SpotStrategy.SCALPING_VOLATILITY
        elif trend == "sideways" or trend == "ranging":
            # Marché en range -> Grid Trading
            return SpotStrategy.INFINITY_GRID
        elif trend == "bearish" and volatility < 5:
            # Marché baissier stable -> DCA
            return SpotStrategy.DCA_INTELLIGENT
        elif volatility > 5 and volatility < 10:
            # Volatilité modérée -> Mean Reversion
            return SpotStrategy.MEAN_REVERSION
        else:
            # Par défaut -> Rebalancing
            return SpotStrategy.SMART_REBALANCING
    
    def start(self, coins: List[str] = None):
        """
        Démarre le mode Auto Spot AI
        
        Args:
            coins: Liste des coins à trader (None = use watchlist)
        """
        if self.is_running:
            LOG.warning("⚠️ Auto Spot AI already running")
            return
        
        self.is_running = True
        self.selected_coins = coins or []
        
        active_group = self.get_active_group()
        if not active_group:
            LOG.error("❌ No strategy group enabled")
            self.is_running = False
            return
        
        LOG.info(f"🚀 Auto Spot AI started with group: {active_group.name}")
        LOG.info(f"📊 Trading coins: {self.selected_coins}")
        LOG.info(f"💰 Capital allocation: {self.calculate_capital_allocation()}")
    
    def stop(self):
        """Arrête le mode Auto Spot AI"""
        if not self.is_running:
            LOG.warning("⚠️ Auto Spot AI not running")
            return
        
        self.is_running = False
        LOG.info("⏹️ Auto Spot AI stopped")
    
    def get_status(self) -> Dict:
        """Récupère le status actuel"""
        active_group = self.get_active_group()
        
        return {
            "running": self.is_running,
            "active_group": active_group.name if active_group else None,
            "active_strategies": [s.value for s in self.active_strategies],
            "coins": self.selected_coins,
            "capital_allocation": self.calculate_capital_allocation(),
            "total_capital": self.config["capital_allocation"]["total_capital_usd"],
            "max_positions": self.config["risk_management"]["max_positions"]
        }
    
    def update_performance(self, strategy_name: str, trade_pnl: float, is_win: bool):
        """Met à jour les performances d'une stratégie"""
        if strategy_name not in self.performance:
            self.performance[strategy_name] = StrategyPerformance(strategy_name=strategy_name)
        
        perf = self.performance[strategy_name]
        perf.total_trades += 1
        if is_win:
            perf.winning_trades += 1
        perf.total_pnl += trade_pnl
        perf.win_rate = (perf.winning_trades / perf.total_trades) * 100 if perf.total_trades > 0 else 0
        perf.avg_profit = perf.total_pnl / perf.total_trades if perf.total_trades > 0 else 0
        perf.best_trade = max(perf.best_trade, trade_pnl)
        perf.worst_trade = min(perf.worst_trade, trade_pnl)
        perf.last_updated = datetime.now().isoformat()
        
        self._save_performance()
    
    def get_performance_summary(self) -> Dict:
        """Récupère un résumé des performances"""
        total_trades = sum(p.total_trades for p in self.performance.values())
        total_pnl = sum(p.total_pnl for p in self.performance.values())
        
        return {
            "total_strategies": len(self.performance),
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "strategies": {name: asdict(perf) for name, perf in self.performance.items()}
        }


# Singleton instance
_auto_spot_manager = None

def get_auto_spot_manager() -> AutoSpotAIManager:
    """Get singleton instance"""
    global _auto_spot_manager
    if _auto_spot_manager is None:
        _auto_spot_manager = AutoSpotAIManager()
    return _auto_spot_manager


if __name__ == "__main__":
    # Test du Auto Spot AI Manager
    print("🔥 Testing Auto Spot AI Manager...")
    
    manager = AutoSpotAIManager()
    
    # Enable group
    print("\n✅ Enabling conservative group...")
    manager.enable_strategy_group("conservative")
    
    # Get status
    print(f"\n📊 Status: {json.dumps(manager.get_status(), indent=2)}")
    
    # Calculate allocation
    print(f"\n💰 Capital Allocation: {manager.calculate_capital_allocation()}")
    
    # Start
    manager.start(coins=["BTC", "ETH", "SOL"])
    
    print("\n✅ Auto Spot AI Manager test complete!")
