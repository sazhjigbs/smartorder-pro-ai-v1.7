"""
Position Manager - Gestion des positions ouvertes
Inspiré de Freqtrade + Hummingbot avec innovations SmartOrder PRO
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Représente une position ouverte (spot ou futures)"""
    position_id: str
    symbol: str
    side: str  # 'long' ou 'short'
    market_type: str  # 'spot' ou 'futures'
    strategy: str  # 'infinite_grid', 'momentum', etc.
    
    entry_price: float
    quantity: float
    entry_time: datetime
    
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    orders: List[Dict] = None  # Liste des ordres liés
    metadata: Dict = None  # Données stratégie spécifiques
    
    status: str = "open"  # 'open', 'closed', 'partial'
    
    def __post_init__(self):
        if self.orders is None:
            self.orders = []
        if self.metadata is None:
            self.metadata = {}
        if isinstance(self.entry_time, str):
            self.entry_time = datetime.fromisoformat(self.entry_time)
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calcule le PnL non réalisé"""
        self.current_price = current_price
        
        if self.market_type == "spot":
            # Spot: simple différence de prix
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            # Futures: prend en compte le side
            if self.side == "long":
                self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
            else:  # short
                self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
        
        return self.unrealized_pnl
    
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour persistence"""
        data = asdict(self)
        data['entry_time'] = self.entry_time.isoformat()
        return data


class PositionManager:
    """
    Gestionnaire de positions - inspiré de Freqtrade
    Fonctionnalités:
    - Tracking temps réel des positions
    - Persistence JSON + SQLite
    - Calcul PnL automatique
    - Support spot + futures
    - Historique complet
    """
    
    def __init__(self, data_dir: str = "data/positions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        
        # Fichiers de persistence
        self.json_file = self.data_dir / "positions.json"
        self.db_file = self.data_dir / "positions.db"
        
        self._init_database()
        self._load_positions()
    
    def _init_database(self):
        """Initialise la base SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                market_type TEXT NOT NULL,
                strategy TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                entry_time TEXT NOT NULL,
                current_price REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT NOT NULL,
                orders TEXT,
                metadata TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS position_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_positions(self):
        """Charge les positions depuis JSON et SQLite"""
        # Charger depuis JSON (backup rapide)
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r') as f:
                    data = json.load(f)
                    for pos_data in data.get('open_positions', []):
                        pos = Position(**pos_data)
                        self.positions[pos.position_id] = pos
                    logger.info(f"✅ {len(self.positions)} positions chargées depuis JSON")
            except Exception as e:
                logger.error(f"❌ Erreur chargement JSON: {e}")
        
        # Vérifier cohérence avec SQLite
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status='open'")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        if db_count != len(self.positions):
            logger.warning(f"⚠️ Incohérence JSON({len(self.positions)}) vs SQLite({db_count})")
    
    def _save_positions(self):
        """Sauvegarde les positions (JSON + SQLite)"""
        # JSON - backup rapide
        data = {
            'open_positions': [pos.to_dict() for pos in self.positions.values()],
            'last_update': datetime.now().isoformat()
        }
        with open(self.json_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # SQLite - persistence robuste
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        for pos in self.positions.values():
            cursor.execute("""
                INSERT OR REPLACE INTO positions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                pos.position_id, pos.symbol, pos.side, pos.market_type,
                pos.strategy, pos.entry_price, pos.quantity,
                pos.entry_time.isoformat(), pos.current_price,
                pos.unrealized_pnl, pos.realized_pnl,
                pos.stop_loss, pos.take_profit, pos.status,
                json.dumps(pos.orders), json.dumps(pos.metadata),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def add_position(self, position: Position) -> bool:
        """Ajoute une nouvelle position"""
        if position.position_id in self.positions:
            logger.error(f"❌ Position {position.position_id} existe déjà")
            return False
        
        self.positions[position.position_id] = position
        self._save_positions()
        self._log_action(position.position_id, "OPEN", position.to_dict())
        
        logger.info(f"✅ Position ouverte: {position.symbol} {position.side} "
                   f"@ {position.entry_price} ({position.strategy})")
        return True
    
    def update_position(self, position_id: str, **kwargs) -> bool:
        """Met à jour une position existante"""
        if position_id not in self.positions:
            logger.error(f"❌ Position {position_id} introuvable")
            return False
        
        pos = self.positions[position_id]
        for key, value in kwargs.items():
            if hasattr(pos, key):
                setattr(pos, key, value)
        
        self._save_positions()
        self._log_action(position_id, "UPDATE", kwargs)
        return True
    
    def close_position(self, position_id: str, exit_price: float, 
                      realized_pnl: float) -> bool:
        """Ferme une position"""
        if position_id not in self.positions:
            logger.error(f"❌ Position {position_id} introuvable")
            return False
        
        pos = self.positions[position_id]
        pos.status = "closed"
        pos.current_price = exit_price
        pos.realized_pnl = realized_pnl
        
        # Déplacer vers historique
        self.closed_positions.append(pos)
        del self.positions[position_id]
        
        self._save_positions()
        self._log_action(position_id, "CLOSE", {
            'exit_price': exit_price,
            'realized_pnl': realized_pnl
        })
        
        logger.info(f"✅ Position fermée: {pos.symbol} PnL: {realized_pnl:.2f}")
        return True
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Récupère une position spécifique"""
        return self.positions.get(position_id)
    
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Récupère toutes les positions d'un symbole"""
        return [pos for pos in self.positions.values() if pos.symbol == symbol]
    
    def get_positions_by_strategy(self, strategy: str) -> List[Position]:
        """Récupère toutes les positions d'une stratégie"""
        return [pos for pos in self.positions.values() if pos.strategy == strategy]
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Récupère toutes les positions ouvertes"""
        return self.positions.copy()
    
    def update_prices(self, prices: Dict[str, float]):
        """Met à jour les prix et recalcule les PnL"""
        for pos in self.positions.values():
            if pos.symbol in prices:
                pos.calculate_pnl(prices[pos.symbol])
        self._save_positions()
    
    def get_total_pnl(self) -> Dict[str, float]:
        """Calcule le PnL total"""
        unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
        realized = sum(pos.realized_pnl for pos in self.closed_positions)
        
        return {
            'unrealized_pnl': unrealized,
            'realized_pnl': realized,
            'total_pnl': unrealized + realized,
            'open_positions': len(self.positions),
            'closed_positions': len(self.closed_positions)
        }
    
    def get_statistics(self) -> Dict:
        """Statistiques complètes"""
        stats = self.get_total_pnl()
        
        # Par marché
        spot_positions = [p for p in self.positions.values() if p.market_type == "spot"]
        futures_positions = [p for p in self.positions.values() if p.market_type == "futures"]
        
        stats['by_market'] = {
            'spot': len(spot_positions),
            'futures': len(futures_positions)
        }
        
        # Par stratégie
        strategies = {}
        for pos in self.positions.values():
            strategies[pos.strategy] = strategies.get(pos.strategy, 0) + 1
        stats['by_strategy'] = strategies
        
        return stats
    
    def _log_action(self, position_id: str, action: str, data: Dict):
        """Log une action dans l'historique"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO position_history (position_id, action, timestamp, data)
            VALUES (?, ?, ?, ?)
        """, (position_id, action, datetime.now().isoformat(), json.dumps(data)))
        
        conn.commit()
        conn.close()
    
    def cleanup_old_positions(self, days: int = 30):
        """Nettoie les anciennes positions fermées"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        self.closed_positions = [
            pos for pos in self.closed_positions
            if pos.entry_time.timestamp() > cutoff
        ]
        
        logger.info(f"🧹 Nettoyage: {len(self.closed_positions)} positions gardées")


# Test rapide
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Créer le manager
    pm = PositionManager()
    
    # Créer une position test
    pos = Position(
        position_id="TEST_001",
        symbol="BTC/USDT",
        side="long",
        market_type="spot",
        strategy="infinite_grid",
        entry_price=50000.0,
        quantity=0.1,
        entry_time=datetime.now()
    )
    
    # Ajouter la position
    pm.add_position(pos)
    
    # Mettre à jour le prix
    pm.update_prices({"BTC/USDT": 51000.0})
    
    # Afficher les stats
    print("\n📊 Statistiques:")
    print(json.dumps(pm.get_statistics(), indent=2))
    
    print("\n✅ Position Manager testé avec succès!")
