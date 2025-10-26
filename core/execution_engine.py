#!/usr/bin/env python3
"""
⚡ SAFELOGIC SmartOrder PRO — Smart Execution Engine
Exécution avancée : Split orders, Partial close, Trailing stop
Optimisé VPS faible RAM
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from core.logger import logger

class SmartExecutionEngine:
    """Moteur d'exécution avancé pour trading pro"""
    
    def __init__(self):
        self.trailing_stops = {}  # symbol -> trailing stop config
        self.split_orders = {}    # order_id -> split info
        
    def split_order(self, symbol: str, side: str, total_quantity: float, 
                    price: float, num_splits: int = 3, 
                    delay_seconds: int = 2) -> List[Dict]:
        """
        Split un gros ordre en plusieurs petits ordres
        
        Args:
            symbol: BTCUSDT, ETHUSDT, etc.
            side: BUY, SELL
            total_quantity: Quantité totale
            price: Prix limite
            num_splits: Nombre de splits (défaut 3)
            delay_seconds: Délai entre chaque split
            
        Returns:
            Liste des ordres splits
        """
        try:
            # Calcul quantité par split
            split_qty = total_quantity / num_splits
            
            splits = []
            for i in range(num_splits):
                split_info = {
                    "split_id": f"{symbol}_{int(time.time())}_{i}",
                    "symbol": symbol,
                    "side": side,
                    "quantity": split_qty,
                    "price": price,
                    "order_number": i + 1,
                    "total_splits": num_splits,
                    "delay": delay_seconds * i,
                    "status": "pending"
                }
                splits.append(split_info)
            
            # Stocke pour suivi
            order_id = f"{symbol}_{int(time.time())}"
            self.split_orders[order_id] = {
                "total_quantity": total_quantity,
                "splits": splits,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(
                f"Split order created: {total_quantity} {symbol} → {num_splits} splits",
                symbol=symbol,
                splits=num_splits
            )
            
            return splits
            
        except Exception as e:
            logger.error(f"Split order error: {str(e)}")
            return []
    
    def execute_split_order(self, splits: List[Dict], exchange_client) -> List[Dict]:
        """
        Exécute les ordres splits avec délai
        
        Args:
            splits: Liste des splits à exécuter
            exchange_client: Client exchange (Bybit, Binance, etc.)
            
        Returns:
            Résultats d'exécution
        """
        results = []
        
        for split in splits:
            try:
                # Attends délai
                if split['delay'] > 0:
                    logger.info(f"Waiting {split['delay']}s before split {split['order_number']}...")
                    time.sleep(split['delay'])
                
                # Place ordre
                logger.info(
                    f"Executing split {split['order_number']}/{split['total_splits']}: "
                    f"{split['side']} {split['quantity']} {split['symbol']} @ {split['price']}"
                )
                
                # Ici on appellerait l'exchange client
                # order = exchange_client.place_order(...)
                
                # Simulation pour l'instant
                result = {
                    "split_id": split['split_id'],
                    "order_id": f"ORDER_{int(time.time())}",
                    "status": "filled",
                    "executed_qty": split['quantity'],
                    "executed_price": split['price'],
                    "timestamp": datetime.now().isoformat()
                }
                
                split['status'] = 'executed'
                results.append(result)
                
                logger.info(
                    f"Split {split['order_number']} executed successfully",
                    order_id=result['order_id']
                )
                
            except Exception as e:
                logger.error(f"Split execution error: {str(e)}")
                split['status'] = 'failed'
                results.append({
                    "split_id": split['split_id'],
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def partial_close(self, symbol: str, position_size: float, 
                     close_percentage: float, current_price: float) -> Dict:
        """
        Ferme partiellement une position
        
        Args:
            symbol: BTCUSDT, etc.
            position_size: Taille totale position
            close_percentage: % à fermer (25, 50, 75, 100)
            current_price: Prix actuel
            
        Returns:
            Info fermeture partielle
        """
        try:
            # Calcul quantité à fermer
            close_qty = position_size * (close_percentage / 100)
            remaining_qty = position_size - close_qty
            
            partial_info = {
                "symbol": symbol,
                "original_size": position_size,
                "close_percentage": close_percentage,
                "close_quantity": close_qty,
                "remaining_quantity": remaining_qty,
                "close_price": current_price,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(
                f"Partial close: {close_percentage}% of {symbol} "
                f"({close_qty}/{position_size})",
                symbol=symbol,
                pct=close_percentage
            )
            
            return partial_info
            
        except Exception as e:
            logger.error(f"Partial close error: {str(e)}")
            return {"error": str(e)}
    
    def setup_trailing_stop(self, symbol: str, side: str, 
                           entry_price: float, trail_percent: float,
                           current_price: float = None) -> Dict:
        """
        Configure trailing stop-loss dynamique
        
        Args:
            symbol: BTCUSDT, etc.
            side: LONG ou SHORT
            entry_price: Prix d'entrée
            trail_percent: % de trailing (ex: 2.0 pour 2%)
            current_price: Prix actuel (optionnel)
            
        Returns:
            Config trailing stop
        """
        try:
            if current_price is None:
                current_price = entry_price
            
            # Calcul stop initial
            if side.upper() == "LONG":
                # Pour LONG: stop en dessous du prix
                stop_price = current_price * (1 - trail_percent / 100)
                highest_price = current_price
            else:  # SHORT
                # Pour SHORT: stop au dessus du prix
                stop_price = current_price * (1 + trail_percent / 100)
                highest_price = current_price  # lowest pour SHORT
            
            trail_config = {
                "symbol": symbol,
                "side": side.upper(),
                "entry_price": entry_price,
                "trail_percent": trail_percent,
                "stop_price": stop_price,
                "highest_price": highest_price if side.upper() == "LONG" else None,
                "lowest_price": highest_price if side.upper() == "SHORT" else None,
                "active": True,
                "triggered": False,
                "created_at": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat()
            }
            
            # Stocke
            self.trailing_stops[symbol] = trail_config
            
            logger.info(
                f"Trailing stop setup: {symbol} {side} @ {entry_price}, "
                f"trail {trail_percent}%, stop @ {stop_price}",
                symbol=symbol,
                trail_pct=trail_percent
            )
            
            return trail_config
            
        except Exception as e:
            logger.error(f"Trailing stop setup error: {str(e)}")
            return {"error": str(e)}
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> Tuple[bool, Dict]:
        """
        Met à jour trailing stop selon nouveau prix
        
        Args:
            symbol: BTCUSDT, etc.
            current_price: Prix actuel
            
        Returns:
            (triggered, trail_config)
        """
        try:
            if symbol not in self.trailing_stops:
                return False, {"error": "No trailing stop found"}
            
            trail = self.trailing_stops[symbol]
            
            if not trail['active'] or trail['triggered']:
                return trail['triggered'], trail
            
            side = trail['side']
            trail_pct = trail['trail_percent']
            
            if side == "LONG":
                # Update highest price
                if current_price > trail['highest_price']:
                    trail['highest_price'] = current_price
                    # Recalcule stop
                    new_stop = current_price * (1 - trail_pct / 100)
                    trail['stop_price'] = new_stop
                    
                    logger.info(
                        f"Trailing stop updated: {symbol} highest {current_price}, "
                        f"new stop {new_stop}",
                        symbol=symbol
                    )
                
                # Check trigger
                if current_price <= trail['stop_price']:
                    trail['triggered'] = True
                    trail['trigger_price'] = current_price
                    
                    logger.warning(
                        f"Trailing stop TRIGGERED: {symbol} @ {current_price} "
                        f"(stop was {trail['stop_price']})",
                        symbol=symbol,
                        alert=True
                    )
                    
                    return True, trail
            
            else:  # SHORT
                # Update lowest price
                if current_price < trail['lowest_price']:
                    trail['lowest_price'] = current_price
                    # Recalcule stop
                    new_stop = current_price * (1 + trail_pct / 100)
                    trail['stop_price'] = new_stop
                    
                    logger.info(
                        f"Trailing stop updated: {symbol} lowest {current_price}, "
                        f"new stop {new_stop}",
                        symbol=symbol
                    )
                
                # Check trigger
                if current_price >= trail['stop_price']:
                    trail['triggered'] = True
                    trail['trigger_price'] = current_price
                    
                    logger.warning(
                        f"Trailing stop TRIGGERED: {symbol} @ {current_price} "
                        f"(stop was {trail['stop_price']})",
                        symbol=symbol,
                        alert=True
                    )
                    
                    return True, trail
            
            trail['last_update'] = datetime.now().isoformat()
            return False, trail
            
        except Exception as e:
            logger.error(f"Trailing stop update error: {str(e)}")
            return False, {"error": str(e)}
    
    def get_trailing_stop_status(self, symbol: str) -> Optional[Dict]:
        """Récupère status trailing stop"""
        return self.trailing_stops.get(symbol)
    
    def cancel_trailing_stop(self, symbol: str) -> bool:
        """Annule trailing stop"""
        if symbol in self.trailing_stops:
            self.trailing_stops[symbol]['active'] = False
            logger.info(f"Trailing stop cancelled: {symbol}")
            return True
        return False
    
    def get_all_trailing_stops(self) -> Dict[str, Dict]:
        """Récupère tous les trailing stops actifs"""
        return {
            symbol: config 
            for symbol, config in self.trailing_stops.items()
            if config['active'] and not config['triggered']
        }

# Singleton
_engine = None

def get_engine() -> SmartExecutionEngine:
    """Récupère instance singleton"""
    global _engine
    if _engine is None:
        _engine = SmartExecutionEngine()
    return _engine

# Raccourcis
def split_order(*args, **kwargs):
    return get_engine().split_order(*args, **kwargs)

def partial_close(*args, **kwargs):
    return get_engine().partial_close(*args, **kwargs)

def setup_trailing_stop(*args, **kwargs):
    return get_engine().setup_trailing_stop(*args, **kwargs)

def update_trailing_stop(*args, **kwargs):
    return get_engine().update_trailing_stop(*args, **kwargs)

# Test
if __name__ == "__main__":
    print("🧪 Testing Smart Execution Engine...")
    
    engine = get_engine()
    
    # Test 1: Split order
    print("\n1️⃣ Test Split Order:")
    splits = engine.split_order("BTCUSDT", "BUY", 0.003, 67000, num_splits=3)
    print(f"Created {len(splits)} splits")
    
    # Test 2: Partial close
    print("\n2️⃣ Test Partial Close:")
    partial = engine.partial_close("BTCUSDT", 0.01, 50, 67500)
    print(f"Partial close: {partial}")
    
    # Test 3: Trailing stop
    print("\n3️⃣ Test Trailing Stop:")
    trail = engine.setup_trailing_stop("BTCUSDT", "LONG", 67000, 2.0, 67500)
    print(f"Trailing stop: {trail}")
    
    # Update prices
    print("\n   Price: 68000")
    triggered, trail = engine.update_trailing_stop("BTCUSDT", 68000)
    print(f"   Triggered: {triggered}, Stop: {trail['stop_price']}")
    
    print("\n   Price: 67800")
    triggered, trail = engine.update_trailing_stop("BTCUSDT", 67800)
    print(f"   Triggered: {triggered}")
    
    print("\n   Price: 66500 (should trigger)")
    triggered, trail = engine.update_trailing_stop("BTCUSDT", 66500)
    print(f"   Triggered: {triggered} ✅")
    
    print("\n✅ Test complete")
