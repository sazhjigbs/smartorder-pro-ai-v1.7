#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Auto Futures AI Manager
============================================
Gestionnaire intelligent pour trading FUTURES automatisé
by MAIGA ABOUBACAR

Features:
- Sélection IA de stratégies (Adaptive Leverage, Dual Direction, Scalping HF, Trend Following, Breakout)
- Allocation dynamique du capital
- Groupes de stratégies paramétrables
- Gestion leverage adaptatif
- Risk management avancé
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

sys.path.insert(0, str(Path(__file__).parent.parent))

LOG = logging.getLogger("auto_futures_ai")
LOG.setLevel(logging.INFO)

class FuturesStrategy(Enum):
    """Types de stratégies FUTURES disponibles"""
    ADAPTIVE_LEVERAGE = "adaptive_leverage"
    DUAL_DIRECTION = "dual_direction"
    MICRO_SCALPING_HF = "micro_scalping_hf"
    TREND_FOLLOWING = "trend_following"
    BREAKOUT_HUNTER = "breakout_hunter"


@dataclass
class FuturesStrategyGroup:
    """Groupe de stratégies futures"""
    name: str
    strategies: List[FuturesStrategy]
    allocation_percent: Dict[str, float]
    max_leverage: int = 5
    enabled: bool = True
    description: str = ""
    
    def to_dict(self):
        return {
            "name": self.name,
            "strategies": [s.value for s in self.strategies],
            "allocation_percent": self.allocation_percent,
            "max_leverage": self.max_leverage,
            "enabled": self.enabled,
            "description": self.description
        }


@dataclass
class FuturesPerformance:
    """Performance d'une stratégie futures"""
    strategy_name: str
    total_trades: int = 0
    long_trades: int = 0
    short_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    total_fees: float = 0.0
    win_rate: float = 0.0
    avg_leverage: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    liquidations: int = 0
    last_updated: str = ""


class AutoFuturesAIManager:
    """
    Gestionnaire Auto Futures AI
    
    Gère le trading futures automatisé avec:
    - Sélection intelligente de stratégies par l'IA
    - Groupes de stratégies paramétrables
    - Leverage adaptatif
    - Risk management avancé
    """
    
    def __init__(self, config_dir: str = "config"):
        """Initialize Auto Futures AI Manager"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "auto_futures_config.json"
        self.performance_file = self.config_dir / "auto_futures_performance.json"
        
        # Load configuration
        self.config = self._load_config()
        
        # Strategy groups
        self.strategy_groups: Dict[str, FuturesStrategyGroup] = {}
        self._initialize_strategy_groups()
        
        # Performance tracking
        self.performance: Dict[str, FuturesPerformance] = {}
        self._load_performance()
        
        # State
        self.is_running = False
        self.active_strategies = []
        self.selected_coins = []
        self.current_leverage = {}  # coin -> leverage
        
        LOG.info("✅ Auto Futures AI Manager initialized")
    
    def _load_config(self) -> Dict:
        """Charge la configuration"""
        default_config = {
            "enabled": False,
            "mode": "auto",  # auto | manual | hybrid
            "capital_allocation": {
                "total_capital_usd": 1000,
                "max_per_coin_percent": 15,
                "reserve_percent": 20
            },
            "leverage": {
                "min_leverage": 1,
                "max_leverage": 10,
                "default_leverage": 3,
                "adaptive_enabled": True
            },
            "risk_management": {
                "max_positions": 3,
                "max_daily_loss_percent": 10.0,
                "max_position_size_usd": 300,
                "stop_loss_percent": 3.0,
                "take_profit_percent": 6.0,
                "trailing_stop_enabled": True,
                "trailing_stop_percent": 1.5,
                "liquidation_buffer_percent": 20.0
            },
            "ai_selector": {
                "enabled": True,
                "min_confidence": 0.75,
                "rebalance_interval_hours": 12,
                "auto_switch_strategies": True,
                "auto_adjust_leverage": True
            },
            "filters": {
                "min_volume_24h_usd": 100_000_000,
                "min_liquidity": 2_000_000,
                "max_volatility_percent": 20.0,
                "min_funding_rate": -0.01
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
                LOG.info("✅ Auto Futures config loaded")
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
            LOG.info("✅ Auto Futures config saved")
        except Exception as e:
            LOG.error(f"❌ Error saving config: {e}")
    
    def _initialize_strategy_groups(self):
        """Initialise les groupes de stratégies futures"""
        # Groupe 1: Conservative (Low Leverage)
        self.strategy_groups["conservative"] = FuturesStrategyGroup(
            name="Conservative",
            strategies=[FuturesStrategy.ADAPTIVE_LEVERAGE, FuturesStrategy.TREND_FOLLOWING],
            allocation_percent={
                "adaptive_leverage": 60.0,
                "trend_following": 40.0
            },
            max_leverage=3,
            enabled=True,
            description="Stratégies conservatrices avec leverage limité"
        )
        
        # Groupe 2: Aggressive (High Leverage)
        self.strategy_groups["aggressive"] = FuturesStrategyGroup(
            name="Aggressive",
            strategies=[FuturesStrategy.MICRO_SCALPING_HF, FuturesStrategy.BREAKOUT_HUNTER],
            allocation_percent={
                "micro_scalping_hf": 50.0,
                "breakout_hunter": 50.0
            },
            max_leverage=10,
            enabled=False,
            description="Stratégies agressives haute fréquence"
        )
        
        # Groupe 3: Dual Direction (Long + Short)
        self.strategy_groups["dual_direction"] = FuturesStrategyGroup(
            name="Dual Direction",
            strategies=[FuturesStrategy.DUAL_DIRECTION],
            allocation_percent={
                "dual_direction": 100.0
            },
            max_leverage=5,
            enabled=False,
            description="Trading bidirectionnel long/short simultané"
        )
        
        # Groupe 4: Balanced
        self.strategy_groups["balanced"] = FuturesStrategyGroup(
            name="Balanced",
            strategies=[
                FuturesStrategy.ADAPTIVE_LEVERAGE,
                FuturesStrategy.TREND_FOLLOWING,
                FuturesStrategy.BREAKOUT_HUNTER
            ],
            allocation_percent={
                "adaptive_leverage": 40.0,
                "trend_following": 30.0,
                "breakout_hunter": 30.0
            },
            max_leverage=5,
            enabled=False,
            description="Mix équilibré de stratégies futures"
        )
        
        # Groupe 5: Scalping Only
        self.strategy_groups["scalping_only"] = FuturesStrategyGroup(
            name="Scalping Only",
            strategies=[FuturesStrategy.MICRO_SCALPING_HF],
            allocation_percent={
                "micro_scalping_hf": 100.0
            },
            max_leverage=8,
            enabled=False,
            description="Uniquement scalping haute fréquence"
        )
        
        LOG.info(f"✅ Initialized {len(self.strategy_groups)} futures strategy groups")
    
    def _load_performance(self):
        """Charge les performances"""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r') as f:
                    data = json.load(f)
                    for strategy_name, perf_data in data.items():
                        self.performance[strategy_name] = FuturesPerformance(**perf_data)
                LOG.info(f"✅ Loaded performance for {len(self.performance)} futures strategies")
            except Exception as e:
                LOG.error(f"❌ Error loading performance: {e}")
    
    def _save_performance(self):
        """Sauvegarde les performances"""
        try:
            data = {name: asdict(perf) for name, perf in self.performance.items()}
            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2)
            LOG.info("✅ Futures performance saved")
        except Exception as e:
            LOG.error(f"❌ Error saving performance: {e}")
    
    def enable_strategy_group(self, group_name: str) -> bool:
        """Active un groupe de stratégies"""
        if group_name not in self.strategy_groups:
            LOG.error(f"❌ Strategy group '{group_name}' not found")
            return False
        
        # Disable all other groups
        for name, group in self.strategy_groups.items():
            group.enabled = (name == group_name)
        
        LOG.info(f"✅ Enabled futures strategy group: {group_name}")
        self._update_active_strategies()
        return True
    
    def disable_all_groups(self):
        """Désactive tous les groupes"""
        for group in self.strategy_groups.values():
            group.enabled = False
        self.active_strategies = []
        LOG.info("⏸️ All futures strategy groups disabled")
    
    def _update_active_strategies(self):
        """Met à jour la liste des stratégies actives"""
        self.active_strategies = []
        
        for group in self.strategy_groups.values():
            if group.enabled:
                self.active_strategies.extend(group.strategies)
        
        LOG.info(f"✅ Active futures strategies: {[s.value for s in self.active_strategies]}")
    
    def get_active_group(self) -> Optional[FuturesStrategyGroup]:
        """Récupère le groupe actif"""
        for group in self.strategy_groups.values():
            if group.enabled:
                return group
        return None
    
    def get_all_groups(self) -> Dict[str, FuturesStrategyGroup]:
        """Récupère tous les groupes"""
        return self.strategy_groups
    
    def calculate_capital_allocation(self) -> Dict[str, float]:
        """Calcule l'allocation de capital par stratégie"""
        active_group = self.get_active_group()
        if not active_group:
            return {}
        
        total_capital = self.config["capital_allocation"]["total_capital_usd"]
        reserve_percent = self.config["capital_allocation"]["reserve_percent"]
        
        available_capital = total_capital * (1 - reserve_percent / 100)
        
        allocation = {}
        for strategy_name, percent in active_group.allocation_percent.items():
            allocation[strategy_name] = available_capital * (percent / 100)
        
        return allocation
    
    def calculate_adaptive_leverage(self, coin: str, market_conditions: Dict) -> int:
        """
        Calcule le leverage adaptatif selon conditions marché
        
        Args:
            coin: Coin symbol
            market_conditions: Dict avec volatility, trend, etc.
        
        Returns:
            Leverage optimal (1-10)
        """
        active_group = self.get_active_group()
        if not active_group:
            return self.config["leverage"]["default_leverage"]
        
        max_leverage = active_group.max_leverage
        min_leverage = self.config["leverage"]["min_leverage"]
        
        # Facteurs d'ajustement
        volatility = market_conditions.get("volatility", 0)
        trend_strength = market_conditions.get("trend_strength", 0)  # 0-100
        volume = market_conditions.get("volume", 0)
        
        # Logique adaptive
        if volatility > 15:
            # Haute volatilité -> leverage réduit
            leverage = min_leverage
        elif volatility > 10:
            # Volatilité moyenne
            leverage = int(max_leverage * 0.6)
        elif trend_strength > 80 and volume > 100_000_000:
            # Trend fort + volume élevé -> leverage augmenté
            leverage = max_leverage
        else:
            # Conditions normales
            leverage = int(max_leverage * 0.7)
        
        # Clamp entre min et max
        leverage = max(min_leverage, min(leverage, max_leverage))
        
        return leverage
    
    def set_leverage(self, coin: str, leverage: int):
        """Définit le leverage pour un coin"""
        max_lev = self.config["leverage"]["max_leverage"]
        min_lev = self.config["leverage"]["min_leverage"]
        
        leverage = max(min_lev, min(leverage, max_lev))
        self.current_leverage[coin] = leverage
        
        LOG.info(f"✅ Set leverage for {coin}: {leverage}x")
    
    def get_leverage(self, coin: str) -> int:
        """Récupère le leverage actuel d'un coin"""
        return self.current_leverage.get(coin, self.config["leverage"]["default_leverage"])
    
    def ai_select_best_strategy(self, market_conditions: Dict) -> FuturesStrategy:
        """IA sélectionne la meilleure stratégie futures"""
        volatility = market_conditions.get("volatility", 0)
        trend = market_conditions.get("trend", "neutral")
        volume = market_conditions.get("volume", 0)
        funding_rate = market_conditions.get("funding_rate", 0)
        
        # Logique de sélection IA
        if volatility > 15 and volume > 200_000_000:
            # Haute volatilité + volume -> Scalping HF
            return FuturesStrategy.MICRO_SCALPING_HF
        elif trend in ["strong_bullish", "strong_bearish"]:
            # Trend fort -> Trend Following
            return FuturesStrategy.TREND_FOLLOWING
        elif volatility > 8 and abs(funding_rate) > 0.005:
            # Volatilité + funding rate élevé -> Breakout Hunter
            return FuturesStrategy.BREAKOUT_HUNTER
        elif trend == "neutral" and volatility < 10:
            # Marché calme -> Dual Direction
            return FuturesStrategy.DUAL_DIRECTION
        else:
            # Par défaut -> Adaptive Leverage
            return FuturesStrategy.ADAPTIVE_LEVERAGE
    
    def start(self, coins: List[str] = None):
        """Démarre le mode Auto Futures AI"""
        if self.is_running:
            LOG.warning("⚠️ Auto Futures AI already running")
            return
        
        self.is_running = True
        self.selected_coins = coins or []
        
        active_group = self.get_active_group()
        if not active_group:
            LOG.error("❌ No futures strategy group enabled")
            self.is_running = False
            return
        
        # Initialize leverage for each coin
        for coin in self.selected_coins:
            if coin not in self.current_leverage:
                self.current_leverage[coin] = self.config["leverage"]["default_leverage"]
        
        LOG.info(f"🚀 Auto Futures AI started with group: {active_group.name}")
        LOG.info(f"📊 Trading coins: {self.selected_coins}")
        LOG.info(f"💰 Capital allocation: {self.calculate_capital_allocation()}")
        LOG.info(f"📈 Max leverage: {active_group.max_leverage}x")
    
    def stop(self):
        """Arrête le mode Auto Futures AI"""
        if not self.is_running:
            LOG.warning("⚠️ Auto Futures AI not running")
            return
        
        self.is_running = False
        LOG.info("⏹️ Auto Futures AI stopped")
    
    def get_status(self) -> Dict:
        """Récupère le status actuel"""
        active_group = self.get_active_group()
        
        return {
            "running": self.is_running,
            "active_group": active_group.name if active_group else None,
            "active_strategies": [s.value for s in self.active_strategies],
            "coins": self.selected_coins,
            "current_leverage": self.current_leverage,
            "max_leverage": active_group.max_leverage if active_group else 0,
            "capital_allocation": self.calculate_capital_allocation(),
            "total_capital": self.config["capital_allocation"]["total_capital_usd"],
            "max_positions": self.config["risk_management"]["max_positions"]
        }
    
    def update_performance(self, strategy_name: str, trade_data: Dict):
        """Met à jour les performances d'une stratégie"""
        if strategy_name not in self.performance:
            self.performance[strategy_name] = FuturesPerformance(strategy_name=strategy_name)
        
        perf = self.performance[strategy_name]
        perf.total_trades += 1
        
        if trade_data.get("side") == "long":
            perf.long_trades += 1
        else:
            perf.short_trades += 1
        
        if trade_data.get("is_win", False):
            perf.winning_trades += 1
        
        perf.total_pnl += trade_data.get("pnl", 0)
        perf.total_fees += trade_data.get("fees", 0)
        perf.win_rate = (perf.winning_trades / perf.total_trades) * 100 if perf.total_trades > 0 else 0
        
        # Update average leverage
        leverage = trade_data.get("leverage", 1)
        perf.avg_leverage = ((perf.avg_leverage * (perf.total_trades - 1)) + leverage) / perf.total_trades
        
        if trade_data.get("liquidated", False):
            perf.liquidations += 1
        
        perf.last_updated = datetime.now().isoformat()
        
        self._save_performance()
    
    def get_performance_summary(self) -> Dict:
        """Récupère un résumé des performances"""
        total_trades = sum(p.total_trades for p in self.performance.values())
        total_pnl = sum(p.total_pnl for p in self.performance.values())
        total_fees = sum(p.total_fees for p in self.performance.values())
        total_liquidations = sum(p.liquidations for p in self.performance.values())
        
        return {
            "total_strategies": len(self.performance),
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "total_fees": total_fees,
            "net_pnl": total_pnl - total_fees,
            "total_liquidations": total_liquidations,
            "strategies": {name: asdict(perf) for name, perf in self.performance.items()}
        }
    
    def create_custom_group(self, name: str, strategies: List[FuturesStrategy], 
                           allocation: Dict[str, float], max_leverage: int, description: str = ""):
        """Crée un groupe de stratégies personnalisé"""
        if name in self.strategy_groups:
            LOG.warning(f"⚠️ Group '{name}' already exists")
            return False
        
        self.strategy_groups[name] = FuturesStrategyGroup(
            name=name,
            strategies=strategies,
            allocation_percent=allocation,
            max_leverage=max_leverage,
            enabled=False,
            description=description
        )
        
        LOG.info(f"✅ Created custom futures strategy group: {name}")
        return True


# Singleton instance
_auto_futures_manager = None

def get_auto_futures_manager() -> AutoFuturesAIManager:
    """Get singleton instance"""
    global _auto_futures_manager
    if _auto_futures_manager is None:
        _auto_futures_manager = AutoFuturesAIManager()
    return _auto_futures_manager


if __name__ == "__main__":
    # Test
    print("🔥 Testing Auto Futures AI Manager...")
    
    manager = AutoFuturesAIManager()
    
    # Enable group
    print("\n✅ Enabling conservative group...")
    manager.enable_strategy_group("conservative")
    
    # Get status
    print(f"\n📊 Status: {json.dumps(manager.get_status(), indent=2)}")
    
    # Calculate adaptive leverage
    market = {"volatility": 8, "trend_strength": 75, "volume": 150_000_000}
    leverage = manager.calculate_adaptive_leverage("BTC", market)
    print(f"\n📈 Adaptive Leverage for BTC: {leverage}x")
    
    # Start
    manager.start(coins=["BTCUSDT", "ETHUSDT"])
    
    print("\n✅ Auto Futures AI Manager test complete!")
