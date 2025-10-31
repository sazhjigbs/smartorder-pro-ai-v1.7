"""
Copy Trading Engine
Permet de copier les trades de traders performants
"""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class CopyMode(Enum):
    MIRROR = "mirror"  # Copie exacte
    PROPORTIONAL = "proportional"  # Proportionnel au capital
    FIXED_AMOUNT = "fixed_amount"  # Montant fixe
    INVERSE = "inverse"  # Position opposée


@dataclass
class Trader:
    """Trader à copier"""
    trader_id: str
    name: str
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    followers: int = 0
    subscription_fee: float = 0.0  # % des profits
    verified: bool = False
    rating: float = 0.0
    trades_history: List[Dict] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        return (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
    
    @property
    def profit_factor(self) -> float:
        total_wins = sum(t['pnl'] for t in self.trades_history if t['pnl'] > 0)
        total_losses = abs(sum(t['pnl'] for t in self.trades_history if t['pnl'] < 0))
        return total_wins / total_losses if total_losses > 0 else 0.0


@dataclass
class CopyConfig:
    """Configuration de copie"""
    follower_id: str
    trader_id: str
    mode: CopyMode
    
    # Limites
    max_copy_amount: float = 1000.0  # Max par trade
    max_daily_trades: int = 50
    max_exposure: float = 5000.0  # Exposition totale max
    
    # Filtres
    min_trade_size: float = 10.0
    max_trade_size: float = 1000.0
    copy_symbols: Optional[List[str]] = None  # Symbols à copier (None = tous)
    skip_symbols: Optional[List[str]] = None  # Symbols à ignorer
    
    # Risk
    stop_loss_percent: float = 5.0
    take_profit_percent: float = 10.0
    
    # État
    active: bool = True
    trades_today: int = 0
    total_copied: int = 0
    total_pnl: float = 0.0


class CopyTradingEngine:
    """Moteur de Copy Trading"""
    
    def __init__(self):
        self.traders: Dict[str, Trader] = {}
        self.copy_configs: Dict[str, CopyConfig] = {}  # follower_id -> config
        self.active_copies: List[Dict] = []
        self.trade_log: List[Dict] = []
        
    def register_trader(self, trader: Trader) -> bool:
        """Enregistre un trader"""
        if trader.trader_id in self.traders:
            return False
        
        self.traders[trader.trader_id] = trader
        return True
    
    def start_copying(self, config: CopyConfig) -> str:
        """Commence à copier un trader"""
        if config.trader_id not in self.traders:
            raise ValueError(f"Trader {config.trader_id} not found")
        
        copy_id = f"COPY_{config.follower_id}_{config.trader_id}_{int(time.time())}"
        self.copy_configs[copy_id] = config
        
        return copy_id
    
    def stop_copying(self, copy_id: str) -> bool:
        """Arrête de copier"""
        if copy_id not in self.copy_configs:
            return False
        
        self.copy_configs[copy_id].active = False
        return True
    
    def on_trader_signal(self, trader_id: str, signal: Dict) -> List[Dict]:
        """
        Reçoit un signal d'un trader et le copie à tous ses followers
        
        signal = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'quantity': 0.1,
            'price': 50000,
            'type': 'market'
        }
        """
        if trader_id not in self.traders:
            return []
        
        copied_trades = []
        
        # Trouver tous les followers actifs
        for copy_id, config in self.copy_configs.items():
            if not config.active or config.trader_id != trader_id:
                continue
            
            # Vérifier filtres
            if not self._should_copy_trade(config, signal):
                continue
            
            # Calculer quantité à copier
            copy_quantity = self._calculate_copy_quantity(config, signal)
            
            if copy_quantity <= 0:
                continue
            
            # Créer le trade copié
            copied_trade = {
                "copy_id": copy_id,
                "follower_id": config.follower_id,
                "trader_id": trader_id,
                "symbol": signal["symbol"],
                "side": signal["side"],
                "quantity": copy_quantity,
                "price": signal.get("price"),
                "type": signal.get("type", "market"),
                "original_quantity": signal["quantity"],
                "timestamp": time.time()
            }
            
            self.active_copies.append(copied_trade)
            copied_trades.append(copied_trade)
            
            config.trades_today += 1
            config.total_copied += 1
            
            self.trade_log.append({
                "action": "copy_trade",
                "trade": copied_trade,
                "timestamp": time.time()
            })
        
        return copied_trades
    
    def _should_copy_trade(self, config: CopyConfig, signal: Dict) -> bool:
        """Vérifie si le trade doit être copié"""
        
        # Limite quotidienne
        if config.trades_today >= config.max_daily_trades:
            return False
        
        # Filtre par symbole
        if config.copy_symbols and signal["symbol"] not in config.copy_symbols:
            return False
        
        if config.skip_symbols and signal["symbol"] in config.skip_symbols:
            return False
        
        # Taille du trade
        trade_value = signal["quantity"] * signal.get("price", 0)
        if trade_value < config.min_trade_size or trade_value > config.max_trade_size:
            return False
        
        # Exposition totale
        current_exposure = sum(
            t["quantity"] * t.get("price", 0)
            for t in self.active_copies
            if t["follower_id"] == config.follower_id
        )
        if current_exposure >= config.max_exposure:
            return False
        
        return True
    
    def _calculate_copy_quantity(self, config: CopyConfig, signal: Dict) -> float:
        """Calcule la quantité à copier selon le mode"""
        original_qty = signal["quantity"]
        price = signal.get("price", 0)
        
        if config.mode == CopyMode.MIRROR:
            # Copie exacte
            return original_qty
        
        elif config.mode == CopyMode.PROPORTIONAL:
            # Proportionnel (ex: 50% du trade original)
            proportion = 0.5  # À configurer
            return original_qty * proportion
        
        elif config.mode == CopyMode.FIXED_AMOUNT:
            # Montant fixe (ex: toujours 100 USD)
            fixed_amount = config.max_copy_amount
            return fixed_amount / price if price > 0 else 0
        
        elif config.mode == CopyMode.INVERSE:
            # Position inverse
            return original_qty
        
        return 0.0
    
    def get_top_traders(self, limit: int = 10, sort_by: str = "pnl") -> List[Trader]:
        """Retourne les meilleurs traders"""
        traders_list = list(self.traders.values())
        
        if sort_by == "pnl":
            traders_list.sort(key=lambda t: t.total_pnl, reverse=True)
        elif sort_by == "win_rate":
            traders_list.sort(key=lambda t: t.win_rate, reverse=True)
        elif sort_by == "sharpe":
            traders_list.sort(key=lambda t: t.sharpe_ratio, reverse=True)
        elif sort_by == "followers":
            traders_list.sort(key=lambda t: t.followers, reverse=True)
        
        return traders_list[:limit]
    
    def get_trader_stats(self, trader_id: str) -> Optional[Dict]:
        """Stats d'un trader"""
        if trader_id not in self.traders:
            return None
        
        trader = self.traders[trader_id]
        return {
            "trader_id": trader.trader_id,
            "name": trader.name,
            "win_rate": trader.win_rate,
            "total_trades": trader.total_trades,
            "total_pnl": trader.total_pnl,
            "profit_factor": trader.profit_factor,
            "sharpe_ratio": trader.sharpe_ratio,
            "max_drawdown": trader.max_drawdown,
            "followers": trader.followers,
            "verified": trader.verified,
            "rating": trader.rating
        }
    
    def get_follower_stats(self, follower_id: str) -> Dict:
        """Stats d'un follower"""
        configs = [c for c in self.copy_configs.values() if c.follower_id == follower_id]
        
        total_copied = sum(c.total_copied for c in configs)
        total_pnl = sum(c.total_pnl for c in configs)
        active_copies = sum(1 for c in configs if c.active)
        
        return {
            "follower_id": follower_id,
            "active_copies": active_copies,
            "total_traders_followed": len(configs),
            "total_trades_copied": total_copied,
            "total_pnl": total_pnl
        }
    
    def simulate_trade_result(self, copied_trade: Dict, pnl: float):
        """Simule le résultat d'un trade copié"""
        copy_id = copied_trade["copy_id"]
        
        if copy_id in self.copy_configs:
            config = self.copy_configs[copy_id]
            config.total_pnl += pnl
            
            # Mettre à jour aussi les stats du trader
            trader = self.traders.get(copied_trade["trader_id"])
            if trader:
                trader.total_pnl += pnl
                trader.total_trades += 1
                if pnl > 0:
                    trader.winning_trades += 1
                
                trader.trades_history.append({
                    "symbol": copied_trade["symbol"],
                    "pnl": pnl,
                    "timestamp": time.time()
                })


# Exemple d'utilisation
if __name__ == "__main__":
    engine = CopyTradingEngine()
    
    # Enregistrer des traders
    trader1 = Trader(
        trader_id="trader_001",
        name="CryptoMaster",
        total_trades=150,
        winning_trades=120,
        total_pnl=5000.0,
        sharpe_ratio=2.5,
        max_drawdown=-500,
        followers=250,
        verified=True,
        rating=4.8
    )
    
    engine.register_trader(trader1)
    
    # Suivre un trader
    config = CopyConfig(
        follower_id="user_123",
        trader_id="trader_001",
        mode=CopyMode.PROPORTIONAL,
        max_copy_amount=500.0,
        copy_symbols=["BTCUSDT", "ETHUSDT"]
    )
    
    copy_id = engine.start_copying(config)
    print(f"✅ Copy trading started: {copy_id}")
    
    # Simuler un signal du trader
    signal = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "quantity": 0.1,
        "price": 50000,
        "type": "market"
    }
    
    copied = engine.on_trader_signal("trader_001", signal)
    print(f"✅ {len(copied)} trades copiés")
    
    # Stats
    print("\n📊 Top Traders:")
    for t in engine.get_top_traders(limit=5):
        print(f"  {t.name}: Win Rate {t.win_rate:.1f}%, PnL ${t.total_pnl:.2f}")
