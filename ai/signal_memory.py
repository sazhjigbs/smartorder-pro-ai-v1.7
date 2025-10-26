#!/usr/bin/env python3
"""
🧠 SAFELOGIC SmartOrder PRO — Signal Memory AI
Historique SQLite pour Trust Score des signaux
Optimisé VPS faible RAM
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from core.logger import logger

# Config DB
DB_DIR = Path("/opt/smartorder-pro/db")
DB_PATH = DB_DIR / "signal_memory.db"

# Windows fallback
if not DB_DIR.exists():
    DB_DIR = Path("db")
    DB_PATH = DB_DIR / "signal_memory.db"
    DB_DIR.mkdir(exist_ok=True)

class SignalMemory:
    """Mémoire SQLite ultra-légère pour signaux"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Crée tables si nécessaire"""
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Dict-like rows
            
            cursor = self.conn.cursor()
            
            # Table signals_history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal_type TEXT NOT NULL,  -- BUY, SELL, LONG, SHORT
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    pnl_pct REAL,
                    pnl_usdt REAL,
                    leverage INTEGER DEFAULT 1,
                    outcome TEXT,  -- WIN, LOSS, NEUTRAL, PENDING
                    confidence REAL,  -- Score confiance AI (0-100)
                    timestamp INTEGER NOT NULL,  -- Unix timestamp
                    exit_timestamp INTEGER,
                    metadata TEXT  -- JSON extra data
                )
            """)
            
            # Index pour perfs
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_symbol_timeframe 
                ON signals_history(symbol, timeframe)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON signals_history(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_outcome 
                ON signals_history(outcome)
            """)
            
            self.conn.commit()
            logger.info(f"Signal Memory DB initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"DB init error: {str(e)}")
            raise
    
    def add_signal(self, symbol: str, timeframe: str, signal_type: str,
                   entry_price: float, confidence: float = 75.0,
                   leverage: int = 1, metadata: Dict = None) -> int:
        """
        Ajoute nouveau signal
        
        Returns:
            signal_id
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO signals_history 
                (symbol, timeframe, signal_type, entry_price, confidence, leverage, 
                 outcome, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol.upper(),
                timeframe,
                signal_type.upper(),
                entry_price,
                confidence,
                leverage,
                "PENDING",
                int(datetime.now().timestamp()),
                json.dumps(metadata or {})
            ))
            
            self.conn.commit()
            signal_id = cursor.lastrowid
            
            logger.info(f"Signal added: {signal_id} - {symbol} {signal_type} @ {entry_price}")
            
            return signal_id
            
        except Exception as e:
            logger.error(f"Add signal error: {str(e)}")
            return -1
    
    def close_signal(self, signal_id: int, exit_price: float, pnl_usdt: float = None):
        """
        Ferme signal avec résultat
        
        Calcule automatiquement outcome et PnL%
        """
        try:
            cursor = self.conn.cursor()
            
            # Récupère signal
            cursor.execute("""
                SELECT entry_price, signal_type, leverage 
                FROM signals_history WHERE id = ?
            """, (signal_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.error(f"Signal {signal_id} not found")
                return False
            
            entry = row["entry_price"]
            signal_type = row["signal_type"]
            leverage = row["leverage"]
            
            # Calcul PnL %
            if signal_type in ["BUY", "LONG"]:
                pnl_pct = ((exit_price - entry) / entry) * 100 * leverage
            else:  # SELL, SHORT
                pnl_pct = ((entry - exit_price) / entry) * 100 * leverage
            
            # Outcome
            if pnl_pct > 0.5:
                outcome = "WIN"
            elif pnl_pct < -0.5:
                outcome = "LOSS"
            else:
                outcome = "NEUTRAL"
            
            # Update
            cursor.execute("""
                UPDATE signals_history 
                SET exit_price = ?, 
                    pnl_pct = ?,
                    pnl_usdt = ?,
                    outcome = ?,
                    exit_timestamp = ?
                WHERE id = ?
            """, (
                exit_price,
                round(pnl_pct, 2),
                pnl_usdt,
                outcome,
                int(datetime.now().timestamp()),
                signal_id
            ))
            
            self.conn.commit()
            
            logger.info(f"Signal closed: {signal_id} - {outcome} {pnl_pct:.2f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"Close signal error: {str(e)}")
            return False
    
    def get_trust_score(self, symbol: str, timeframe: str = None, 
                       last_n: int = 50) -> Dict:
        """
        Calcule Trust Score pour symbol/timeframe
        
        Basé sur les N derniers signaux
        """
        try:
            cursor = self.conn.cursor()
            
            # Query
            if timeframe:
                query = """
                    SELECT * FROM signals_history 
                    WHERE symbol = ? AND timeframe = ?
                    AND outcome IN ('WIN', 'LOSS', 'NEUTRAL')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params = (symbol.upper(), timeframe, last_n)
            else:
                query = """
                    SELECT * FROM signals_history 
                    WHERE symbol = ?
                    AND outcome IN ('WIN', 'LOSS', 'NEUTRAL')
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params = (symbol.upper(), last_n)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "trust_score": 50.0,  # Neutre
                    "total_signals": 0,
                    "win_rate": 0.0,
                    "avg_pnl_pct": 0.0,
                    "status": "no_history"
                }
            
            # Calculs
            total = len(rows)
            wins = sum(1 for r in rows if r["outcome"] == "WIN")
            losses = sum(1 for r in rows if r["outcome"] == "LOSS")
            neutrals = sum(1 for r in rows if r["outcome"] == "NEUTRAL")
            
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            avg_pnl = sum(r["pnl_pct"] for r in rows if r["pnl_pct"]) / total
            
            # Trust Score (pondéré)
            # 70% winrate + 30% avg_pnl
            trust_score = (win_rate * 0.7) + ((avg_pnl + 10) * 3 * 0.3)  # Normalisé
            trust_score = max(0, min(100, trust_score))  # Clamp 0-100
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "trust_score": round(trust_score, 1),
                "total_signals": total,
                "wins": wins,
                "losses": losses,
                "neutrals": neutrals,
                "win_rate": round(win_rate, 1),
                "avg_pnl_pct": round(avg_pnl, 2),
                "status": "ok"
            }
            
        except Exception as e:
            logger.error(f"Trust score error: {str(e)}")
            return {"error": str(e)}
    
    def get_recent_signals(self, symbol: str = None, limit: int = 20) -> List[Dict]:
        """Récupère signaux récents"""
        try:
            cursor = self.conn.cursor()
            
            if symbol:
                query = """
                    SELECT * FROM signals_history 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params = (symbol.upper(), limit)
            else:
                query = """
                    SELECT * FROM signals_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params = (limit,)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Get recent signals error: {str(e)}")
            return []
    
    def get_stats_summary(self) -> Dict:
        """Stats globales"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN outcome = 'PENDING' THEN 1 ELSE 0 END) as pending,
                    AVG(pnl_pct) as avg_pnl,
                    SUM(pnl_usdt) as total_pnl_usdt
                FROM signals_history
            """)
            
            row = cursor.fetchone()
            
            total = row["total"] or 0
            wins = row["wins"] or 0
            losses = row["losses"] or 0
            
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            
            return {
                "total_signals": total,
                "wins": wins,
                "losses": losses,
                "pending": row["pending"] or 0,
                "win_rate": round(win_rate, 1),
                "avg_pnl_pct": round(row["avg_pnl"] or 0, 2),
                "total_pnl_usdt": round(row["total_pnl_usdt"] or 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Stats summary error: {str(e)}")
            return {}
    
    def cleanup_old_signals(self, days: int = 90):
        """Supprime signaux > N jours (économie disque)"""
        try:
            threshold = int((datetime.now() - timedelta(days=days)).timestamp())
            
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM signals_history 
                WHERE timestamp < ?
            """, (threshold,))
            
            deleted = cursor.rowcount
            self.conn.commit()
            
            logger.info(f"Cleaned {deleted} old signals (>{days} days)")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
            return 0
    
    def close(self):
        """Ferme connexion DB"""
        if self.conn:
            self.conn.close()

# Singleton
_memory = None

def get_memory() -> SignalMemory:
    """Récupère instance singleton"""
    global _memory
    if _memory is None:
        _memory = SignalMemory()
    return _memory

# Raccourcis
def add_signal(*args, **kwargs):
    return get_memory().add_signal(*args, **kwargs)

def close_signal(*args, **kwargs):
    return get_memory().close_signal(*args, **kwargs)

def get_trust_score(*args, **kwargs):
    return get_memory().get_trust_score(*args, **kwargs)

def get_recent_signals(*args, **kwargs):
    return get_memory().get_recent_signals(*args, **kwargs)

def get_stats():
    return get_memory().get_stats_summary()

# Test
if __name__ == "__main__":
    print("🧪 Testing Signal Memory...")
    
    mem = get_memory()
    
    # Add test signal
    sig_id = mem.add_signal("BTCUSDT", "15m", "LONG", 67000, confidence=85)
    print(f"Signal added: {sig_id}")
    
    # Close it
    mem.close_signal(sig_id, 67500, pnl_usdt=5.0)
    
    # Trust score
    trust = mem.get_trust_score("BTCUSDT", "15m")
    print(f"Trust Score: {trust}")
    
    # Stats
    stats = mem.get_stats_summary()
    print(f"Stats: {stats}")
    
    print("✅ Test complete")
