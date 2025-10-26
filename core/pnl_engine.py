#!/usr/bin/env python3
"""
SmartOrder PRO - PnL Calculation Engine
========================================
Moteur de calcul PnL temps réel avec métriques avancées:
- PnL par position (USD + %)
- PnL global (toutes positions)
- ROI journalier/hebdo/mensuel
- Win rate
- Best/Worst trades
- Drawdown
- Sharpe ratio

Usage:
    from core.pnl_engine import PnLEngine
    
    engine = PnLEngine()
    pnl = engine.calculate_position_pnl(entry_price, mark_price, size, side)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class Position:
    """Représente une position"""
    symbol: str
    side: str  # Buy or Sell
    size: float
    entry_price: float
    mark_price: float
    leverage: int = 1
    entry_time: Optional[datetime] = None


@dataclass
class Trade:
    """Représente un trade fermé"""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    pnl_usd: float
    pnl_percent: float
    entry_time: datetime
    exit_time: datetime
    duration_minutes: float


class PnLEngine:
    """Moteur de calcul PnL temps réel"""
    
    def __init__(self, initial_balance: float = 10000):
        """
        Initialise le moteur PnL
        
        Args:
            initial_balance: Capital initial en USDT
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Historique
        self.closed_trades: List[Trade] = []
        self.daily_pnl: Dict[str, float] = {}  # date -> pnl
        
        # Métriques courantes
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.best_trade = None
        self.worst_trade = None
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance
    
    def calculate_position_pnl(
        self,
        entry_price: float,
        mark_price: float,
        size: float,
        side: str,
        leverage: int = 1
    ) -> Dict[str, float]:
        """
        Calcule le PnL d'une position
        
        Args:
            entry_price: Prix d'entrée
            mark_price: Prix actuel (mark price)
            size: Taille position
            side: Buy (LONG) ou Sell (SHORT)
            leverage: Leverage utilisé
        
        Returns:
            Dict avec pnl_usd, pnl_percent, roi_percent
        """
        if side == "Buy":
            # LONG: profit si prix monte
            pnl_usd = (mark_price - entry_price) * size
            pnl_percent = ((mark_price - entry_price) / entry_price) * 100
        else:
            # SHORT: profit si prix baisse
            pnl_usd = (entry_price - mark_price) * size
            pnl_percent = ((entry_price - mark_price) / entry_price) * 100
        
        # ROI avec leverage
        position_value = entry_price * size
        margin_used = position_value / leverage
        roi_percent = (pnl_usd / margin_used) * 100 if margin_used > 0 else 0
        
        return {
            "pnl_usd": round(pnl_usd, 2),
            "pnl_percent": round(pnl_percent, 2),
            "roi_percent": round(roi_percent, 2),
            "margin_used": round(margin_used, 2),
            "position_value": round(position_value, 2)
        }
    
    def calculate_liquidation_price(
        self,
        entry_price: float,
        leverage: int,
        side: str
    ) -> float:
        """
        Calcule prix de liquidation approximatif
        
        Args:
            entry_price: Prix d'entrée
            leverage: Leverage utilisé
            side: Buy ou Sell
        
        Returns:
            Prix de liquidation
        """
        # Formule simplifiée (Bybit utilise un calcul plus complexe)
        # Liquidation ≈ entry_price * (1 ± 1/leverage)
        
        if side == "Buy":
            # LONG: liquidation si prix baisse
            liq_price = entry_price * (1 - (1 / leverage) * 0.95)
        else:
            # SHORT: liquidation si prix monte
            liq_price = entry_price * (1 + (1 / leverage) * 0.95)
        
        return round(liq_price, 2)
    
    def calculate_portfolio_pnl(
        self,
        positions: List[Position]
    ) -> Dict[str, any]:
        """
        Calcule PnL global du portfolio
        
        Args:
            positions: Liste des positions ouvertes
        
        Returns:
            Métriques globales du portfolio
        """
        total_pnl_usd = 0.0
        total_margin_used = 0.0
        positions_count = len(positions)
        long_count = 0
        short_count = 0
        
        position_details = []
        
        for pos in positions:
            pnl = self.calculate_position_pnl(
                pos.entry_price,
                pos.mark_price,
                pos.size,
                pos.side,
                pos.leverage
            )
            
            total_pnl_usd += pnl["pnl_usd"]
            total_margin_used += pnl["margin_used"]
            
            if pos.side == "Buy":
                long_count += 1
            else:
                short_count += 1
            
            position_details.append({
                "symbol": pos.symbol,
                "side": pos.side,
                "pnl_usd": pnl["pnl_usd"],
                "pnl_percent": pnl["pnl_percent"],
                "roi_percent": pnl["roi_percent"]
            })
        
        # ROI global
        roi_percent = (total_pnl_usd / total_margin_used * 100) if total_margin_used > 0 else 0
        
        # Balance effective
        effective_balance = self.current_balance + total_pnl_usd
        
        return {
            "total_pnl_usd": round(total_pnl_usd, 2),
            "total_margin_used": round(total_margin_used, 2),
            "roi_percent": round(roi_percent, 2),
            "positions_count": positions_count,
            "long_count": long_count,
            "short_count": short_count,
            "current_balance": round(self.current_balance, 2),
            "effective_balance": round(effective_balance, 2),
            "position_details": position_details
        }
    
    def record_closed_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        size: float,
        entry_time: datetime,
        exit_time: datetime
    ):
        """
        Enregistre un trade fermé
        
        Args:
            symbol: Symbole tradé
            side: Buy ou Sell
            entry_price: Prix d'entrée
            exit_price: Prix de sortie
            size: Taille
            entry_time: Heure d'entrée
            exit_time: Heure de sortie
        """
        # Calculer PnL
        if side == "Buy":
            pnl_usd = (exit_price - entry_price) * size
            pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        else:
            pnl_usd = (entry_price - exit_price) * size
            pnl_percent = ((entry_price - exit_price) / entry_price) * 100
        
        # Durée
        duration = (exit_time - entry_time).total_seconds() / 60  # minutes
        
        # Créer trade
        trade = Trade(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            size=size,
            pnl_usd=pnl_usd,
            pnl_percent=pnl_percent,
            entry_time=entry_time,
            exit_time=exit_time,
            duration_minutes=duration
        )
        
        # Enregistrer
        self.closed_trades.append(trade)
        
        # Update balance
        self.current_balance += pnl_usd
        self.total_pnl += pnl_usd
        
        # Update compteurs
        if pnl_usd > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        # Best/Worst
        if self.best_trade is None or pnl_usd > self.best_trade.pnl_usd:
            self.best_trade = trade
        
        if self.worst_trade is None or pnl_usd < self.worst_trade.pnl_usd:
            self.worst_trade = trade
        
        # Drawdown
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
        
        drawdown = ((self.peak_balance - self.current_balance) / self.peak_balance) * 100
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # PnL journalier
        date_key = exit_time.strftime("%Y-%m-%d")
        if date_key not in self.daily_pnl:
            self.daily_pnl[date_key] = 0.0
        self.daily_pnl[date_key] += pnl_usd
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Retourne statistiques complètes
        
        Returns:
            Statistiques de trading
        """
        total_trades = len(self.closed_trades)
        win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0
        
        # Moyenne gain/perte
        avg_win = 0.0
        avg_loss = 0.0
        
        if self.win_count > 0:
            wins = [t.pnl_usd for t in self.closed_trades if t.pnl_usd > 0]
            avg_win = sum(wins) / len(wins)
        
        if self.loss_count > 0:
            losses = [t.pnl_usd for t in self.closed_trades if t.pnl_usd < 0]
            avg_loss = sum(losses) / len(losses)
        
        # Profit factor
        total_wins = sum(t.pnl_usd for t in self.closed_trades if t.pnl_usd > 0)
        total_losses = abs(sum(t.pnl_usd for t in self.closed_trades if t.pnl_usd < 0))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0
        
        # ROI total
        roi_percent = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        return {
            "initial_balance": self.initial_balance,
            "current_balance": round(self.current_balance, 2),
            "total_pnl": round(self.total_pnl, 2),
            "roi_percent": round(roi_percent, 2),
            "total_trades": total_trades,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "best_trade": {
                "symbol": self.best_trade.symbol,
                "pnl_usd": round(self.best_trade.pnl_usd, 2),
                "pnl_percent": round(self.best_trade.pnl_percent, 2)
            } if self.best_trade else None,
            "worst_trade": {
                "symbol": self.worst_trade.symbol,
                "pnl_usd": round(self.worst_trade.pnl_usd, 2),
                "pnl_percent": round(self.worst_trade.pnl_percent, 2)
            } if self.worst_trade else None
        }
    
    def get_daily_pnl(self, days: int = 30) -> List[Dict[str, any]]:
        """
        Retourne PnL journalier (N derniers jours)
        
        Args:
            days: Nombre de jours
        
        Returns:
            Liste {date, pnl}
        """
        result = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            pnl = self.daily_pnl.get(date_key, 0.0)
            
            result.append({
                "date": date_key,
                "pnl": round(pnl, 2)
            })
        
        return list(reversed(result))  # Ordre chronologique
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calcule Sharpe Ratio (simplifié)
        
        Args:
            risk_free_rate: Taux sans risque annuel (défaut 2%)
        
        Returns:
            Sharpe ratio
        """
        if not self.closed_trades:
            return 0.0
        
        # Retours journaliers
        returns = []
        for trade in self.closed_trades:
            daily_return = (trade.pnl_usd / self.initial_balance)
            returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        # Moyenne et std
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        # Sharpe = (Rendement moyen - Taux sans risque) / Écart-type
        sharpe = (avg_return - risk_free_rate / 365) / std_dev
        
        return round(sharpe, 2)
    
    def export_trades_json(self, filepath: str = "trades_history.json"):
        """
        Exporte l'historique des trades en JSON
        
        Args:
            filepath: Chemin du fichier
        """
        trades_data = []
        
        for trade in self.closed_trades:
            trades_data.append({
                "symbol": trade.symbol,
                "side": trade.side,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "size": trade.size,
                "pnl_usd": trade.pnl_usd,
                "pnl_percent": trade.pnl_percent,
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat(),
                "duration_minutes": trade.duration_minutes
            })
        
        with open(filepath, 'w') as f:
            json.dump(trades_data, f, indent=2)
        
        print(f"✅ {len(trades_data)} trades exportés → {filepath}")


# ==============================================================================
# EXEMPLE D'UTILISATION
# ==============================================================================

if __name__ == "__main__":
    # Créer engine
    engine = PnLEngine(initial_balance=10000)
    
    # Exemple: Position LONG BTC
    pos_btc = Position(
        symbol="BTCUSDT",
        side="Buy",
        size=0.1,
        entry_price=67000,
        mark_price=68500,
        leverage=10
    )
    
    pnl_btc = engine.calculate_position_pnl(
        pos_btc.entry_price,
        pos_btc.mark_price,
        pos_btc.size,
        pos_btc.side,
        pos_btc.leverage
    )
    
    print("📊 PnL Position BTC:")
    print(f"  PnL USD: ${pnl_btc['pnl_usd']}")
    print(f"  PnL %: {pnl_btc['pnl_percent']}%")
    print(f"  ROI %: {pnl_btc['roi_percent']}%")
    
    # Prix liquidation
    liq_price = engine.calculate_liquidation_price(67000, 10, "Buy")
    print(f"  Prix liquidation: ${liq_price}")
    
    # Exemple: Position SHORT ETH
    pos_eth = Position(
        symbol="ETHUSDT",
        side="Sell",
        size=2.0,
        entry_price=3500,
        mark_price=3450,
        leverage=5
    )
    
    # Portfolio PnL
    portfolio = engine.calculate_portfolio_pnl([pos_btc, pos_eth])
    print(f"\n💼 Portfolio:")
    print(f"  PnL total: ${portfolio['total_pnl_usd']}")
    print(f"  ROI: {portfolio['roi_percent']}%")
    print(f"  Positions: {portfolio['long_count']} Long, {portfolio['short_count']} Short")
    
    # Enregistrer trade fermé
    engine.record_closed_trade(
        symbol="BTCUSDT",
        side="Buy",
        entry_price=67000,
        exit_price=68500,
        size=0.1,
        entry_time=datetime.now() - timedelta(hours=2),
        exit_time=datetime.now()
    )
    
    # Statistiques
    stats = engine.get_statistics()
    print(f"\n📈 Statistiques:")
    print(f"  Balance: ${stats['current_balance']}")
    print(f"  ROI: {stats['roi_percent']}%")
    print(f"  Win rate: {stats['win_rate']}%")
    print(f"  Profit factor: {stats['profit_factor']}")
    print(f"  Max drawdown: {stats['max_drawdown']}%")
    
    print("\n✅ PnL Engine test complet !")
