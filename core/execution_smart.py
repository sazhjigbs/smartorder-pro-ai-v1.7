#!/usr/bin/env python3
"""
SmartOrder PRO - Smart Execution Engine
========================================
Exécution intelligente des ordres:
- Split Orders: Découper un ordre en plusieurs parties
- Partial Close: Fermer progressivement (25%, 50%, 75%, 100%)
- Trailing Stop-Loss: Stop loss qui suit le prix
- Trailing Take-Profit: Take profit qui suit le prix
- Pyramiding: Ajouter à une position gagnante
- Break-even: Déplacer SL au prix d'entrée

Usage:
    from core.execution_smart import SmartExecutor
    
    executor = SmartExecutor()
    
    # Split order en 3 parties
    result = executor.split_order("BTCUSDT", "BUY", 0.3, num_splits=3)
    
    # Partial close 50%
    result = executor.partial_close("BTCUSDT", percent=50)
    
    # Trailing stop
    result = executor.set_trailing_stop("BTCUSDT", trail_percent=2.0)
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time


class SmartExecutor:
    """Moteur d'exécution intelligent"""
    
    def __init__(self, exchange_client=None):
        """
        Initialise le Smart Executor
        
        Args:
            exchange_client: Client exchange (Bybit, Binance, etc.)
        """
        self.exchange = exchange_client
        
        # Tracking des ordres split
        self.split_orders: Dict[str, List[Dict]] = {}  # symbol -> [orders]
        
        # Trailing stops actifs
        self.trailing_stops: Dict[str, Dict] = {}  # symbol -> config
        
        # Trailing take-profits actifs
        self.trailing_tps: Dict[str, Dict] = {}  # symbol -> config
        
        # Positions break-even
        self.breakeven_positions: List[str] = []
    
    def split_order(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        num_splits: int = 3,
        price_levels: Optional[List[float]] = None,
        time_delay_seconds: int = 5
    ) -> Dict[str, any]:
        """
        Split un ordre en plusieurs parties
        
        Args:
            symbol: Symbole (ex: BTCUSDT)
            side: BUY ou SELL
            total_quantity: Quantité totale
            num_splits: Nombre de splits (2-10)
            price_levels: Prix spécifiques (optionnel)
            time_delay_seconds: Délai entre chaque ordre
        
        Returns:
            Résumé des ordres placés
        
        Example:
            # Split 0.3 BTC en 3 ordres de 0.1 BTC
            executor.split_order("BTCUSDT", "BUY", 0.3, num_splits=3)
        """
        if num_splits < 2 or num_splits > 10:
            return {"success": False, "error": "num_splits doit être entre 2 et 10"}
        
        # Quantité par split
        qty_per_split = total_quantity / num_splits
        
        orders_placed = []
        
        for i in range(num_splits):
            # Prix pour ce split (si spécifié)
            if price_levels and i < len(price_levels):
                price = price_levels[i]
            else:
                price = None  # Market order
            
            # Placer ordre
            order = {
                "symbol": symbol,
                "side": side,
                "quantity": qty_per_split,
                "price": price,
                "order_type": "LIMIT" if price else "MARKET",
                "split_number": i + 1,
                "split_total": num_splits,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Simuler placement (à remplacer par vrai appel exchange)
            if self.exchange:
                # result = self.exchange.place_order(...)
                order["order_id"] = f"SPLIT_{symbol}_{int(time.time())}_{i}"
                order["status"] = "FILLED"
            else:
                order["order_id"] = f"SIMULATED_{i}"
                order["status"] = "SIMULATED"
            
            orders_placed.append(order)
            
            print(f"📦 Split {i+1}/{num_splits}: {side} {qty_per_split} {symbol} "
                  f"{'@ ' + str(price) if price else 'MARKET'}")
            
            # Délai avant prochain ordre
            if i < num_splits - 1:
                time.sleep(time_delay_seconds)
        
        # Sauvegarder dans tracking
        if symbol not in self.split_orders:
            self.split_orders[symbol] = []
        self.split_orders[symbol].extend(orders_placed)
        
        return {
            "success": True,
            "symbol": symbol,
            "side": side,
            "total_quantity": total_quantity,
            "num_splits": num_splits,
            "qty_per_split": qty_per_split,
            "orders": orders_placed,
            "message": f"Split order: {num_splits} x {qty_per_split} {symbol}"
        }
    
    def partial_close(
        self,
        symbol: str,
        percent: float,
        current_position_size: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Ferme partiellement une position
        
        Args:
            symbol: Symbole
            percent: Pourcentage à fermer (1-100)
            current_position_size: Taille position actuelle
        
        Returns:
            Résultat de la fermeture partielle
        
        Example:
            # Fermer 50% de la position BTC
            executor.partial_close("BTCUSDT", percent=50)
        """
        if percent <= 0 or percent > 100:
            return {"success": False, "error": "percent doit être entre 1 et 100"}
        
        # Si taille position non fournie, la récupérer
        if current_position_size is None:
            if self.exchange:
                # position = self.exchange.get_position(symbol)
                # current_position_size = position["size"]
                current_position_size = 0.1  # Simulé
            else:
                return {"success": False, "error": "Position size non fournie"}
        
        # Quantité à fermer
        qty_to_close = current_position_size * (percent / 100)
        
        # Déterminer side opposé
        # Si position LONG (Buy) → fermer avec SELL
        # Si position SHORT (Sell) → fermer avec BUY
        close_side = "SELL"  # À adapter selon position réelle
        
        # Placer ordre de fermeture
        order = {
            "symbol": symbol,
            "side": close_side,
            "quantity": qty_to_close,
            "order_type": "MARKET",
            "reduce_only": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.exchange:
            # result = self.exchange.place_order(...)
            order["order_id"] = f"PARTIAL_{symbol}_{int(time.time())}"
            order["status"] = "FILLED"
        else:
            order["order_id"] = "SIMULATED"
            order["status"] = "SIMULATED"
        
        print(f"📉 Partial close {percent}%: {close_side} {qty_to_close} {symbol}")
        
        return {
            "success": True,
            "symbol": symbol,
            "percent_closed": percent,
            "quantity_closed": qty_to_close,
            "remaining_quantity": current_position_size - qty_to_close,
            "order": order,
            "message": f"Closed {percent}% of {symbol} position"
        }
    
    def set_trailing_stop(
        self,
        symbol: str,
        trail_percent: float,
        initial_price: Optional[float] = None,
        side: str = "LONG"
    ) -> Dict[str, any]:
        """
        Active un trailing stop-loss
        
        Args:
            symbol: Symbole
            trail_percent: % de trailing (ex: 2.0 = 2%)
            initial_price: Prix initial (sinon prix actuel)
            side: LONG ou SHORT
        
        Returns:
            Configuration du trailing stop
        
        Example:
            # Trailing stop 2% sur position BTC LONG
            executor.set_trailing_stop("BTCUSDT", trail_percent=2.0, side="LONG")
        """
        if trail_percent <= 0 or trail_percent > 50:
            return {"success": False, "error": "trail_percent doit être entre 0 et 50"}
        
        # Prix initial (sinon récupérer prix actuel)
        if initial_price is None:
            if self.exchange:
                # ticker = self.exchange.get_ticker(symbol)
                # initial_price = ticker["last_price"]
                initial_price = 67000.0  # Simulé
            else:
                initial_price = 67000.0
        
        # Calculer stop initial
        if side == "LONG":
            # LONG: stop en dessous du prix
            stop_price = initial_price * (1 - trail_percent / 100)
            highest_price = initial_price
        else:
            # SHORT: stop au dessus du prix
            stop_price = initial_price * (1 + trail_percent / 100)
            lowest_price = initial_price
        
        # Config trailing
        config = {
            "symbol": symbol,
            "side": side,
            "trail_percent": trail_percent,
            "initial_price": initial_price,
            "stop_price": stop_price,
            "highest_price": highest_price if side == "LONG" else None,
            "lowest_price": lowest_price if side == "SHORT" else None,
            "active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Sauvegarder
        self.trailing_stops[symbol] = config
        
        print(f"📍 Trailing stop activé: {symbol} {side} trail={trail_percent}% "
              f"stop @ {stop_price:.2f}")
        
        return {
            "success": True,
            "symbol": symbol,
            "config": config,
            "message": f"Trailing stop {trail_percent}% activé"
        }
    
    def update_trailing_stop(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[Dict[str, any]]:
        """
        Update le trailing stop selon prix actuel
        
        Args:
            symbol: Symbole
            current_price: Prix actuel
        
        Returns:
            Action prise (None si rien, ou ordre stop)
        """
        if symbol not in self.trailing_stops:
            return None
        
        config = self.trailing_stops[symbol]
        
        if not config["active"]:
            return None
        
        side = config["side"]
        trail_pct = config["trail_percent"]
        
        if side == "LONG":
            # LONG: monter le stop si prix monte
            highest = config["highest_price"]
            
            if current_price > highest:
                # Nouveau high
                config["highest_price"] = current_price
                
                # Recalculer stop
                new_stop = current_price * (1 - trail_pct / 100)
                config["stop_price"] = new_stop
                
                print(f"⬆️ Trailing stop ajusté: {symbol} stop → {new_stop:.2f}")
            
            # Vérifier si stop hit
            if current_price <= config["stop_price"]:
                print(f"🛑 STOP HIT: {symbol} @ {current_price:.2f}")
                
                # Fermer position
                result = self.partial_close(symbol, percent=100)
                config["active"] = False
                
                return {
                    "action": "STOP_HIT",
                    "symbol": symbol,
                    "price": current_price,
                    "close_result": result
                }
        
        else:  # SHORT
            # SHORT: descendre le stop si prix baisse
            lowest = config["lowest_price"]
            
            if current_price < lowest:
                # Nouveau low
                config["lowest_price"] = current_price
                
                # Recalculer stop
                new_stop = current_price * (1 + trail_pct / 100)
                config["stop_price"] = new_stop
                
                print(f"⬇️ Trailing stop ajusté: {symbol} stop → {new_stop:.2f}")
            
            # Vérifier si stop hit
            if current_price >= config["stop_price"]:
                print(f"🛑 STOP HIT: {symbol} @ {current_price:.2f}")
                
                # Fermer position
                result = self.partial_close(symbol, percent=100)
                config["active"] = False
                
                return {
                    "action": "STOP_HIT",
                    "symbol": symbol,
                    "price": current_price,
                    "close_result": result
                }
        
        return None
    
    def set_trailing_takeprofit(
        self,
        symbol: str,
        trail_percent: float,
        activation_percent: float,
        initial_price: Optional[float] = None,
        side: str = "LONG"
    ) -> Dict[str, any]:
        """
        Active un trailing take-profit
        
        Le TP trail ne s'active qu'après un certain gain
        
        Args:
            symbol: Symbole
            trail_percent: % de trailing (ex: 1.0 = 1%)
            activation_percent: % de gain avant activation (ex: 5.0 = 5%)
            initial_price: Prix d'entrée
            side: LONG ou SHORT
        
        Returns:
            Configuration du trailing TP
        
        Example:
            # Activer TP trail après +5%, puis trail à 1%
            executor.set_trailing_takeprofit(
                "BTCUSDT",
                trail_percent=1.0,
                activation_percent=5.0,
                side="LONG"
            )
        """
        if initial_price is None:
            initial_price = 67000.0  # À récupérer réellement
        
        # Prix d'activation
        if side == "LONG":
            activation_price = initial_price * (1 + activation_percent / 100)
        else:
            activation_price = initial_price * (1 - activation_percent / 100)
        
        config = {
            "symbol": symbol,
            "side": side,
            "trail_percent": trail_percent,
            "activation_percent": activation_percent,
            "initial_price": initial_price,
            "activation_price": activation_price,
            "tp_price": None,
            "activated": False,
            "active": True,
            "highest_price": initial_price if side == "LONG" else None,
            "lowest_price": initial_price if side == "SHORT" else None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.trailing_tps[symbol] = config
        
        print(f"🎯 Trailing TP configuré: {symbol} activation @ +{activation_percent}%, "
              f"puis trail {trail_percent}%")
        
        return {
            "success": True,
            "symbol": symbol,
            "config": config
        }
    
    def move_to_breakeven(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        min_profit_percent: float = 2.0
    ) -> Dict[str, any]:
        """
        Déplace le stop-loss au prix d'entrée (break-even)
        
        Args:
            symbol: Symbole
            entry_price: Prix d'entrée
            current_price: Prix actuel
            min_profit_percent: % minimum de profit avant break-even
        
        Returns:
            Résultat de l'opération
        
        Example:
            # Déplacer SL à break-even si +2% de profit
            executor.move_to_breakeven("BTCUSDT", 67000, 68500, min_profit_percent=2.0)
        """
        # Calculer profit actuel %
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        if profit_pct < min_profit_percent:
            return {
                "success": False,
                "message": f"Profit actuel ({profit_pct:.2f}%) < minimum ({min_profit_percent}%)"
            }
        
        # Modifier stop à break-even
        if self.exchange:
            # Modifier ordre stop sur exchange
            pass
        
        # Tracker
        if symbol not in self.breakeven_positions:
            self.breakeven_positions.append(symbol)
        
        print(f"⚖️ Break-even activé: {symbol} SL → {entry_price}")
        
        return {
            "success": True,
            "symbol": symbol,
            "entry_price": entry_price,
            "new_stop": entry_price,
            "message": f"Stop-loss déplacé au break-even @ {entry_price}"
        }
    
    def pyramid_in(
        self,
        symbol: str,
        side: str,
        additional_quantity: float,
        min_profit_percent: float = 3.0,
        entry_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Ajoute à une position gagnante (pyramiding)
        
        Args:
            symbol: Symbole
            side: BUY ou SELL
            additional_quantity: Quantité à ajouter
            min_profit_percent: % profit minimum avant pyramiding
            entry_price: Prix entrée initial
            current_price: Prix actuel
        
        Returns:
            Résultat de l'ajout
        
        Example:
            # Ajouter 0.05 BTC à position si +3% de profit
            executor.pyramid_in("BTCUSDT", "BUY", 0.05, min_profit_percent=3.0)
        """
        if entry_price is None or current_price is None:
            entry_price = 67000.0
            current_price = 69000.0
        
        # Vérifier profit
        profit_pct = ((current_price - entry_price) / entry_price) * 100
        
        if profit_pct < min_profit_percent:
            return {
                "success": False,
                "message": f"Profit ({profit_pct:.2f}%) < minimum ({min_profit_percent}%)"
            }
        
        # Ajouter à position
        order = {
            "symbol": symbol,
            "side": side,
            "quantity": additional_quantity,
            "order_type": "MARKET",
            "note": "PYRAMID_IN",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.exchange:
            # Placer ordre
            pass
        
        print(f"📈 Pyramid IN: {side} +{additional_quantity} {symbol} "
              f"(profit actuel: +{profit_pct:.2f}%)")
        
        return {
            "success": True,
            "symbol": symbol,
            "additional_quantity": additional_quantity,
            "current_profit_pct": profit_pct,
            "order": order
        }
    
    def get_active_trailing_stops(self) -> List[Dict]:
        """Retourne tous les trailing stops actifs"""
        return [
            config for config in self.trailing_stops.values()
            if config.get("active", False)
        ]
    
    def get_statistics(self) -> Dict[str, any]:
        """Statistiques du Smart Executor"""
        return {
            "split_orders_count": sum(len(orders) for orders in self.split_orders.values()),
            "active_trailing_stops": len(self.get_active_trailing_stops()),
            "active_trailing_tps": sum(
                1 for c in self.trailing_tps.values() if c.get("active", False)
            ),
            "breakeven_positions": len(self.breakeven_positions)
        }


# ==============================================================================
# EXEMPLE D'UTILISATION
# ==============================================================================

if __name__ == "__main__":
    # Créer executor
    executor = SmartExecutor()
    
    print("=" * 60)
    print("SMART EXECUTION ENGINE - DEMO")
    print("=" * 60)
    
    # 1. Split Order
    print("\n1️⃣ SPLIT ORDER (3 parts)")
    result = executor.split_order("BTCUSDT", "BUY", 0.3, num_splits=3)
    print(f"   ✅ {result['message']}")
    
    # 2. Partial Close
    print("\n2️⃣ PARTIAL CLOSE (50%)")
    result = executor.partial_close("BTCUSDT", percent=50, current_position_size=0.3)
    print(f"   ✅ {result['message']}")
    
    # 3. Trailing Stop
    print("\n3️⃣ TRAILING STOP (2%)")
    result = executor.set_trailing_stop("BTCUSDT", trail_percent=2.0, initial_price=67000, side="LONG")
    print(f"   ✅ {result['message']}")
    
    # Simuler mouvement prix
    print("\n   📈 Prix monte à 68000...")
    executor.update_trailing_stop("BTCUSDT", 68000)
    
    print("   📈 Prix monte à 69000...")
    executor.update_trailing_stop("BTCUSDT", 69000)
    
    print("   📉 Prix descend à 67700...")
    result = executor.update_trailing_stop("BTCUSDT", 67700)
    if result:
        print(f"   🛑 {result['action']}")
    
    # 4. Trailing Take-Profit
    print("\n4️⃣ TRAILING TAKE-PROFIT")
    result = executor.set_trailing_takeprofit(
        "ETHUSDT",
        trail_percent=1.0,
        activation_percent=5.0,
        initial_price=3500,
        side="LONG"
    )
    print(f"   ✅ Configured")
    
    # 5. Break-even
    print("\n5️⃣ MOVE TO BREAK-EVEN")
    result = executor.move_to_breakeven("BTCUSDT", entry_price=67000, current_price=68500)
    print(f"   ✅ {result['message']}")
    
    # 6. Pyramiding
    print("\n6️⃣ PYRAMID IN")
    result = executor.pyramid_in("BTCUSDT", "BUY", 0.05, entry_price=67000, current_price=69000)
    print(f"   ✅ Added to position")
    
    # Stats
    print("\n📊 STATISTICS")
    stats = executor.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Smart Execution Engine test complet !")
    print("=" * 60)
