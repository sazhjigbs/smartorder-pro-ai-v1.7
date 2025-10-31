"""
Quantum Grid - Version RÉELLE avec TA-Lib et CCXT
Grid Trading auto-optimisé basé sur indicateurs techniques professionnels
"""
import time
import numpy as np
import ccxt
import talib
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("quantum_grid_real")


class GridMode(Enum):
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    BEARISH = "bearish"
    VOLATILE = "volatile"


@dataclass
class QuantumGridConfig:
    symbol: str = "BTC/USDT"
    total_investment: float = 5000
    grid_levels: int = 10
    initial_spacing: float = 1.5  # %
    auto_optimize: bool = True
    rebalance_interval: int = 300  # 5 minutes
    use_talib: bool = True
    exchange_name: str = "bybit"


class QuantumGridReal:
    """Grid Trading avec indicateurs techniques réels"""
    
    def __init__(self, config: QuantumGridConfig):
        self.config = config
        self.exchange = self._init_exchange()
        
        # État
        self.grid_orders: List[Dict] = []
        self.filled_orders: List[Dict] = []
        self.price_history: List[float] = []
        self.current_mode = GridMode.NEUTRAL
        self.last_rebalance = time.time()
        
        # Récupère prix initial
        self.current_price = self._get_current_price()
        
        # Initialise grille
        self._initialize_grid()
        
        LOG.info(f"✅ Quantum Grid REAL initialisé")
        LOG.info(f"   Symbol: {self.config.symbol}")
        LOG.info(f"   Prix actuel: {self.current_price:.2f}")
        LOG.info(f"   Niveaux: {self.config.grid_levels}")
        LOG.info(f"   Mode: {self.current_mode.value}")
    
    def _init_exchange(self) -> ccxt.Exchange:
        """Initialise exchange CCXT"""
        try:
            if self.config.exchange_name == "bybit":
                exchange = ccxt.bybit({'enableRateLimit': True})
            elif self.config.exchange_name == "binance":
                exchange = ccxt.binance({'enableRateLimit': True})
            else:
                exchange = ccxt.bybit({'enableRateLimit': True})
            
            # Test connexion
            exchange.load_markets()
            LOG.info(f"✅ Connecté à {self.config.exchange_name}")
            return exchange
        except Exception as e:
            LOG.error(f"❌ Erreur connexion exchange: {e}")
            raise
    
    def _get_current_price(self, retries=3) -> float:
        """Récupère prix réel avec retry"""
        for attempt in range(retries):
            try:
                ticker = self.exchange.fetch_ticker(self.config.symbol)
                return float(ticker['last'])
            except Exception as e:
                if attempt == retries - 1:
                    LOG.error(f"❌ Impossible de récupérer le prix: {e}")
                    raise
                time.sleep(2 ** attempt)
    
    def get_real_indicators(self) -> Dict:
        """Récupère données réelles et calcule indicateurs TA-Lib"""
        try:
            # 1. Récupère OHLCV réel (100 bougies 1h)
            ohlcv = self.exchange.fetch_ohlcv(
                self.config.symbol,
                timeframe='1h',
                limit=100
            )
            
            # Convertir en arrays
            close = np.array([x[4] for x in ohlcv], dtype=float)
            high = np.array([x[2] for x in ohlcv], dtype=float)
            low = np.array([x[3] for x in ohlcv], dtype=float)
            volume = np.array([x[5] for x in ohlcv], dtype=float)
            
            # 2. Calcule indicateurs TA-Lib
            rsi = talib.RSI(close, timeperiod=14)
            macd, macd_signal, macd_hist = talib.MACD(close, 
                                                       fastperiod=12, 
                                                       slowperiod=26, 
                                                       signalperiod=9)
            upper_bb, middle_bb, lower_bb = talib.BBANDS(close, 
                                                          timeperiod=20, 
                                                          nbdevup=2, 
                                                          nbdevdn=2)
            atr = talib.ATR(high, low, close, timeperiod=14)
            adx = talib.ADX(high, low, close, timeperiod=14)
            
            # 3. Indicateurs supplémentaires
            ema_20 = talib.EMA(close, timeperiod=20)
            ema_50 = talib.EMA(close, timeperiod=50)
            
            # 4. Volatilité normalisée
            volatility = atr[-1] / close[-1] if close[-1] > 0 else 0
            
            # 5. Force de la tendance
            trend_strength = abs(close[-1] - close[-20]) / close[-20] if close[-20] > 0 else 0
            
            # 6. BB Squeeze
            bb_squeeze = (upper_bb[-1] - lower_bb[-1]) / middle_bb[-1] if middle_bb[-1] > 0 else 0
            
            return {
                'rsi': float(rsi[-1]) if not np.isnan(rsi[-1]) else 50,
                'macd': float(macd[-1]) if not np.isnan(macd[-1]) else 0,
                'macd_signal': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else 0,
                'macd_histogram': float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else 0,
                'bb_upper': float(upper_bb[-1]),
                'bb_middle': float(middle_bb[-1]),
                'bb_lower': float(lower_bb[-1]),
                'atr': float(atr[-1]),
                'volatility': float(volatility),
                'adx': float(adx[-1]) if not np.isnan(adx[-1]) else 0,
                'ema_20': float(ema_20[-1]),
                'ema_50': float(ema_50[-1]),
                'trend_strength': float(trend_strength),
                'bb_squeeze': float(bb_squeeze),
                'current_price': float(close[-1]),
                'volume': float(volume[-1])
            }
        
        except Exception as e:
            LOG.error(f"❌ Erreur calcul indicateurs: {e}")
            return {'error': str(e)}
    
    def detect_market_regime(self, indicators: Dict) -> GridMode:
        """Détecte régime de marché basé sur indicateurs réels"""
        rsi = indicators['rsi']
        macd_hist = indicators['macd_histogram']
        adx = indicators['adx']
        volatility = indicators['volatility']
        
        # Tendance forte (ADX > 25)
        if adx > 25:
            if macd_hist > 0 and rsi > 50:
                return GridMode.BULLISH
            elif macd_hist < 0 and rsi < 50:
                return GridMode.BEARISH
        
        # Volatilité élevée
        if volatility > 0.03:
            return GridMode.VOLATILE
        
        # Par défaut: neutral/ranging
        return GridMode.NEUTRAL
    
    def optimize_grid_spacing(self, indicators: Dict) -> tuple:
        """Optimise spacing et niveaux selon marché"""
        volatility = indicators['volatility']
        rsi = indicators['rsi']
        bb_squeeze = indicators['bb_squeeze']
        
        # 1. Ajuste spacing selon volatilité
        if volatility > 0.03:  # Haute volatilité
            spacing = 2.5
        elif volatility < 0.01:  # Basse volatilité
            spacing = 1.0
        else:
            spacing = 1.5
        
        # 2. Ajuste niveaux selon RSI
        if rsi > 70:  # Suracheté -> plus de ventes
            buy_levels = 3
            sell_levels = 7
        elif rsi < 30:  # Survendu -> plus d'achats
            buy_levels = 7
            sell_levels = 3
        else:
            buy_levels = 5
            sell_levels = 5
        
        # 3. Ajuste selon BB Squeeze
        if bb_squeeze < 0.04:  # Squeeze = expansion probable
            spacing *= 1.2
        
        return spacing, buy_levels, sell_levels
    
    def _initialize_grid(self):
        """Initialise grille avec prix actuel"""
        indicators = self.get_real_indicators()
        self.current_mode = self.detect_market_regime(indicators)
        
        spacing_pct, buy_levels, sell_levels = self.optimize_grid_spacing(indicators)
        
        base_price = self.current_price
        spacing = spacing_pct / 100
        
        # Niveaux BUY (en dessous du prix)
        for i in range(1, buy_levels + 1):
            level_price = base_price * (1 - i * spacing)
            self.grid_orders.append({
                "level": -i,
                "price": level_price,
                "side": "buy",
                "quantity": self.config.total_investment / (buy_levels + sell_levels) / level_price,
                "filled": False
            })
        
        # Niveaux SELL (au-dessus du prix)
        for i in range(1, sell_levels + 1):
            level_price = base_price * (1 + i * spacing)
            self.grid_orders.append({
                "level": i,
                "price": level_price,
                "side": "sell",
                "quantity": self.config.total_investment / (buy_levels + sell_levels) / level_price,
                "filled": False
            })
        
        LOG.info(f"📊 Grille initialisée: {buy_levels} buy + {sell_levels} sell")
        LOG.info(f"📊 Spacing: {spacing_pct:.2f}% | Mode: {self.current_mode.value}")
    
    def update(self) -> Dict:
        """Update principal - à appeler régulièrement"""
        try:
            # 1. Récupère prix actuel
            self.current_price = self._get_current_price()
            self.price_history.append(self.current_price)
            
            # 2. Récupère indicateurs
            indicators = self.get_real_indicators()
            
            # 3. Détecte régime
            new_mode = self.detect_market_regime(indicators)
            if new_mode != self.current_mode:
                LOG.info(f"🔄 Changement mode: {self.current_mode.value} → {new_mode.value}")
                self.current_mode = new_mode
            
            # 4. Check ordres remplis
            actions = self._check_filled_orders()
            
            # 5. Auto-rebalance si nécessaire
            if time.time() - self.last_rebalance > self.config.rebalance_interval:
                if self._should_rebalance(indicators):
                    self._rebalance_grid(indicators)
                    self.last_rebalance = time.time()
            
            return {
                "success": True,
                "current_price": self.current_price,
                "mode": self.current_mode.value,
                "actions": actions,
                "indicators": indicators,
                "grid_orders": len(self.grid_orders),
                "filled_orders": len(self.filled_orders)
            }
        
        except Exception as e:
            LOG.error(f"❌ Erreur update: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_filled_orders(self) -> List[Dict]:
        """Vérifie ordres remplis"""
        actions = []
        
        for order in self.grid_orders:
            if order["filled"]:
                continue
            
            # BUY rempli si prix descend
            if order["side"] == "buy" and self.current_price <= order["price"]:
                order["filled"] = True
                self.filled_orders.append(order)
                actions.append({
                    "action": "buy_filled",
                    "price": order["price"],
                    "quantity": order["quantity"]
                })
                LOG.info(f"✅ BUY @ {order['price']:.2f}")
            
            # SELL rempli si prix monte
            elif order["side"] == "sell" and self.current_price >= order["price"]:
                order["filled"] = True
                self.filled_orders.append(order)
                actions.append({
                    "action": "sell_filled",
                    "price": order["price"],
                    "quantity": order["quantity"]
                })
                LOG.info(f"✅ SELL @ {order['price']:.2f}")
        
        return actions
    
    def _should_rebalance(self, indicators: Dict) -> bool:
        """Détermine si rebalance nécessaire"""
        # Rebalance si prix sort de 20% de la grille
        min_price = min([o["price"] for o in self.grid_orders])
        max_price = max([o["price"] for o in self.grid_orders])
        
        if self.current_price < min_price or self.current_price > max_price:
            return True
        
        # Rebalance si changement volatilité majeur
        if indicators['volatility'] > 0.05:  # Très volatile
            return True
        
        return False
    
    def _rebalance_grid(self, indicators: Dict):
        """Rebalance grille complète"""
        LOG.info(f"🔄 Rebalancing grille @ {self.current_price:.2f}")
        
        # Réinitialise ordres non remplis
        self.grid_orders = [o for o in self.grid_orders if o["filled"]]
        
        # Crée nouvelle grille
        self._initialize_grid()
    
    def get_statistics(self) -> Dict:
        """Statistiques de performance"""
        total_trades = len(self.filled_orders)
        
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0
            }
        
        # Calcule PnL approximatif
        buys = [o for o in self.filled_orders if o["side"] == "buy"]
        sells = [o for o in self.filled_orders if o["side"] == "sell"]
        
        pnl = 0
        for i in range(min(len(buys), len(sells))):
            pnl += (sells[i]["price"] - buys[i]["price"]) * buys[i]["quantity"]
        
        return {
            "total_trades": total_trades,
            "buys": len(buys),
            "sells": len(sells),
            "estimated_pnl": pnl,
            "current_mode": self.current_mode.value,
            "grid_levels": len(self.grid_orders)
        }


if __name__ == "__main__":
    # Test
    config = QuantumGridConfig(
        symbol="BTC/USDT",
        total_investment=5000,
        grid_levels=10,
        auto_optimize=True
    )
    
    grid = QuantumGridReal(config)
    
    # Simule quelques updates
    for i in range(3):
        result = grid.update()
        print(f"\n📊 Update {i+1}:")
        print(f"   Prix: {result['current_price']:.2f}")
        print(f"   Mode: {result['mode']}")
        print(f"   RSI: {result['indicators']['rsi']:.2f}")
        print(f"   Volatilité: {result['indicators']['volatility']:.4f}")
        time.sleep(5)
    
    stats = grid.get_statistics()
    print(f"\n📈 Stats: {stats}")
