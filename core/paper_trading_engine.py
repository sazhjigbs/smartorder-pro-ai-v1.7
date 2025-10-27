#!/usr/bin/env python3
"""
🎮 SAFELOGIC SmartOrder PRO - Paper Trading Engine
==================================================
Moteur de simulation de trading pour tester sans risque réel
by MAIGA ABOUBACAR

Features:
- Simulation complète des ordres (MARKET, LIMIT, STOP)
- Virtual wallet avec USDT
- Historique des trades
- Calcul PNL réaliste
- Sauvegarde en JSON + SQLite

Usage:
    from core.paper_trading_engine import PaperTradingEngine
    
    engine = PaperTradingEngine()
    
    # Placer un ordre
    order = engine.place_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.01,
        price=None  # Market price
    )
    
    # Voir le wallet virtuel
    wallet = engine.get_wallet()
    
    # Voir l'historique
    history = engine.get_trade_history()
"""

import json
import sqlite3
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

LOG = logging.getLogger("paper_trading")
LOG.setLevel(logging.INFO)

# Windows-compatible logging
try:
    log_dir = "C:\\smartorder-pro\\logs"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(f"{log_dir}\\paper_trading.log")
except:
    fh = logging.FileHandler("paper_trading.log")

fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
LOG.addHandler(fh)


class PaperTradingEngine:
    """Moteur de simulation de trading"""
    
    def __init__(self, 
                 db_path: str = "data/paper_trading.db",
                 initial_balance: float = 10000.0):
        """
        Initialise le moteur de paper trading
        
        Args:
            db_path: Chemin vers la DB SQLite
            initial_balance: Balance USDT de départ
        """
        self.db_path = db_path
        self.initial_balance = initial_balance
        
        # Wallet virtuel
        self.wallet = {
            "USDT": initial_balance,
            "positions": {}  # {symbol: {quantity, avg_price}}
        }
        
        # Historique trades
        self.trades_history = []
        
        # Init DB
        self._init_database()
        
        # Charger état depuis DB
        self._load_state()
        
        LOG.info(f"🎮 Paper Trading Engine initialized with {initial_balance} USDT")
    
    def _init_database(self):
        """Initialise la base de données"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table wallet
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                usdt_balance REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Table positions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                entry_time TEXT NOT NULL,
                last_update TEXT NOT NULL
            )
        """)
        
        # Table trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_usdt REAL NOT NULL,
                fee REAL NOT NULL,
                pnl REAL,
                status TEXT NOT NULL
            )
        """)
        
        # Table PNL summary
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pnl_summary (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_pnl REAL NOT NULL,
                total_trades INTEGER NOT NULL,
                winning_trades INTEGER NOT NULL,
                losing_trades INTEGER NOT NULL,
                win_rate REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
        LOG.info("✅ Database initialized")
    
    def _load_state(self):
        """Charge l'état depuis la DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Charger wallet
        cursor.execute("SELECT usdt_balance FROM wallet WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            self.wallet["USDT"] = row[0]
        else:
            # Premier lancement
            cursor.execute(
                "INSERT INTO wallet (id, usdt_balance, updated_at) VALUES (1, ?, ?)",
                (self.initial_balance, datetime.utcnow().isoformat())
            )
            conn.commit()
        
        # Charger positions
        cursor.execute("SELECT symbol, quantity, avg_price FROM positions")
        for row in cursor.fetchall():
            symbol, qty, avg_price = row
            self.wallet["positions"][symbol] = {
                "quantity": qty,
                "avg_price": avg_price
            }
        
        # Charger historique récent (100 derniers trades)
        cursor.execute("""
            SELECT order_id, timestamp, symbol, side, order_type, quantity, price, total_usdt, fee, pnl, status
            FROM trades
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        for row in cursor.fetchall():
            self.trades_history.append({
                "order_id": row[0],
                "timestamp": row[1],
                "symbol": row[2],
                "side": row[3],
                "order_type": row[4],
                "quantity": row[5],
                "price": row[6],
                "total_usdt": row[7],
                "fee": row[8],
                "pnl": row[9],
                "status": row[10]
            })
        
        conn.close()
        
        LOG.info(f"📥 State loaded: {self.wallet['USDT']:.2f} USDT, {len(self.wallet['positions'])} positions")
    
    def _save_state(self):
        """Sauvegarde l'état en DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update wallet
        cursor.execute(
            "UPDATE wallet SET usdt_balance = ?, updated_at = ? WHERE id = 1",
            (self.wallet["USDT"], datetime.utcnow().isoformat())
        )
        
        # Update positions
        cursor.execute("DELETE FROM positions")
        for symbol, pos in self.wallet["positions"].items():
            cursor.execute(
                """INSERT INTO positions (symbol, quantity, avg_price, entry_time, last_update)
                   VALUES (?, ?, ?, ?, ?)""",
                (symbol, pos["quantity"], pos["avg_price"], 
                 datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
            )
        
        conn.commit()
        conn.close()
    
    def place_order(self,
                   symbol: str,
                   side: str,  # BUY or SELL
                   order_type: str,  # MARKET, LIMIT
                   quantity: float,
                   price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place un ordre simulé
        
        Args:
            symbol: Paire trading (ex: BTCUSDT)
            side: BUY ou SELL
            order_type: MARKET ou LIMIT
            quantity: Quantité
            price: Prix (optionnel pour MARKET)
        
        Returns:
            Ordre exécuté
        """
        # Générer order ID
        order_id = f"PAPER_{int(time.time() * 1000)}"
        timestamp = datetime.utcnow().isoformat()
        
        # Si MARKET, utiliser un prix fictif (simulé)
        if order_type == "MARKET" and price is None:
            # TODO: Récupérer prix réel depuis API ou utiliser prix simulé
            price = self._get_simulated_price(symbol)
        
        # Calculer total et frais
        total_usdt = quantity * price
        fee = total_usdt * 0.001  # 0.1% de frais
        
        # Validation
        if side == "BUY":
            required = total_usdt + fee
            if self.wallet["USDT"] < required:
                LOG.error(f"❌ Insufficient balance: {self.wallet['USDT']:.2f} < {required:.2f}")
                return {
                    "success": False,
                    "error": "Insufficient USDT balance",
                    "required": required,
                    "available": self.wallet["USDT"]
                }
        elif side == "SELL":
            current_qty = self.wallet["positions"].get(symbol, {}).get("quantity", 0)
            if current_qty < quantity:
                LOG.error(f"❌ Insufficient position: {current_qty} < {quantity}")
                return {
                    "success": False,
                    "error": f"Insufficient {symbol} position",
                    "required": quantity,
                    "available": current_qty
                }
        
        # Exécuter l'ordre
        pnl = None
        
        if side == "BUY":
            # Débiter USDT
            self.wallet["USDT"] -= (total_usdt + fee)
            
            # Ajouter/augmenter position
            if symbol not in self.wallet["positions"]:
                self.wallet["positions"][symbol] = {
                    "quantity": quantity,
                    "avg_price": price
                }
            else:
                # Calcul nouveau prix moyen
                pos = self.wallet["positions"][symbol]
                total_qty = pos["quantity"] + quantity
                avg_price = ((pos["quantity"] * pos["avg_price"]) + (quantity * price)) / total_qty
                
                self.wallet["positions"][symbol] = {
                    "quantity": total_qty,
                    "avg_price": avg_price
                }
        
        elif side == "SELL":
            # Réduire/fermer position
            pos = self.wallet["positions"][symbol]
            avg_entry = pos["avg_price"]
            
            # Calcul PNL
            pnl = (price - avg_entry) * quantity - fee
            
            # Créditer USDT
            self.wallet["USDT"] += (total_usdt - fee)
            
            # Update position
            new_qty = pos["quantity"] - quantity
            if new_qty <= 0.0001:  # Position fermée
                del self.wallet["positions"][symbol]
            else:
                self.wallet["positions"][symbol]["quantity"] = new_qty
        
        # Enregistrer le trade
        trade = {
            "order_id": order_id,
            "timestamp": timestamp,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "total_usdt": total_usdt,
            "fee": fee,
            "pnl": pnl,
            "status": "FILLED"
        }
        
        self.trades_history.insert(0, trade)
        
        # Sauvegarder en DB
        self._save_trade_to_db(trade)
        self._save_state()
        
        LOG.info(f"✅ Order {side} {quantity} {symbol} @ {price:.2f} - PNL: {pnl if pnl else 'N/A'}")
        
        return {
            "success": True,
            "order": trade,
            "wallet": self.get_wallet()
        }
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Retourne un prix simulé (à remplacer par API réelle)"""
        # Prix fictifs par défaut
        prices = {
            "BTCUSDT": 65000.0,
            "ETHUSDT": 3500.0,
            "BNBUSDT": 580.0,
            "SOLUSDT": 140.0,
            "ADAUSDT": 0.60
        }
        return prices.get(symbol, 100.0)
    
    def _save_trade_to_db(self, trade: Dict[str, Any]):
        """Sauvegarde un trade en DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trades (order_id, timestamp, symbol, side, order_type, quantity, price, total_usdt, fee, pnl, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade["order_id"],
            trade["timestamp"],
            trade["symbol"],
            trade["side"],
            trade["order_type"],
            trade["quantity"],
            trade["price"],
            trade["total_usdt"],
            trade["fee"],
            trade["pnl"],
            trade["status"]
        ))
        
        conn.commit()
        conn.close()
    
    def get_wallet(self) -> Dict[str, Any]:
        """Retourne l'état du wallet"""
        return {
            "usdt_balance": round(self.wallet["USDT"], 2),
            "positions": self.wallet["positions"],
            "total_value": self._calculate_total_value(),
            "pnl": self._calculate_total_pnl()
        }
    
    def _calculate_total_value(self) -> float:
        """Calcul valeur totale du portefeuille"""
        total = self.wallet["USDT"]
        
        for symbol, pos in self.wallet["positions"].items():
            current_price = self._get_simulated_price(symbol)
            total += pos["quantity"] * current_price
        
        return round(total, 2)
    
    def _calculate_total_pnl(self) -> float:
        """Calcul PNL total réalisé"""
        total_pnl = 0.0
        
        for trade in self.trades_history:
            if trade["pnl"] is not None:
                total_pnl += trade["pnl"]
        
        return round(total_pnl, 2)
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne l'historique des trades"""
        return self.trades_history[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de trading"""
        total_trades = len(self.trades_history)
        
        if total_trades == 0:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl_per_trade": 0
            }
        
        winning = sum(1 for t in self.trades_history if t["pnl"] and t["pnl"] > 0)
        losing = sum(1 for t in self.trades_history if t["pnl"] and t["pnl"] < 0)
        total_pnl = self._calculate_total_pnl()
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning,
            "losing_trades": losing,
            "win_rate": round((winning / total_trades) * 100, 2) if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "avg_pnl_per_trade": round(total_pnl / total_trades, 2) if total_trades > 0 else 0,
            "initial_balance": self.initial_balance,
            "current_balance": self.wallet["USDT"],
            "total_value": self._calculate_total_value(),
            "roi_percent": round(((self._calculate_total_value() - self.initial_balance) / self.initial_balance) * 100, 2)
        }
    
    def reset_wallet(self):
        """Reset le wallet à la balance initiale"""
        self.wallet = {
            "USDT": self.initial_balance,
            "positions": {}
        }
        self.trades_history = []
        
        # Nettoyer DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM trades")
        cursor.execute("DELETE FROM positions")
        cursor.execute("UPDATE wallet SET usdt_balance = ?, updated_at = ? WHERE id = 1",
                      (self.initial_balance, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        LOG.warning("⚠️ Wallet reset to initial balance")


# ========== API Helper Functions ==========

def get_paper_engine(initial_balance: float = 10000.0) -> PaperTradingEngine:
    """Retourne une instance du paper trading engine"""
    return PaperTradingEngine(initial_balance=initial_balance)


if __name__ == "__main__":
    # Test du moteur
    print("🎮 Testing Paper Trading Engine...")
    
    engine = PaperTradingEngine(initial_balance=10000)
    
    # Test BUY
    print("\n📈 Testing BUY order...")
    result = engine.place_order("BTCUSDT", "BUY", "MARKET", 0.1, 65000)
    print(json.dumps(result, indent=2))
    
    # Test SELL
    print("\n📉 Testing SELL order...")
    result = engine.place_order("BTCUSDT", "SELL", "MARKET", 0.05, 66000)
    print(json.dumps(result, indent=2))
    
    # Stats
    print("\n📊 Statistics:")
    print(json.dumps(engine.get_statistics(), indent=2))
    
    print("\n✅ Tests completed!")
