#!/usr/bin/env python3
"""
SmartOrder PRO - Charts & Analytics API
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path
import requests

LOG = logging.getLogger("api_charts")

class ChartsAPI:
    """API pour les graphiques et analytics"""
    
    def __init__(self, data_dir: str = "/opt/smartorder-pro/data"):
        self.data_dir = Path(data_dir)
        self.paper_trading_file = self.data_dir / "paper_trading.json"
        
    def get_price_history(self, symbol: str = "BTCUSDT", timeframe: str = "1h", limit: int = 24) -> Dict:
        """
        Récupère l'historique des prix
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe (1h, 4h, 1d, 1w)
            limit: Nombre de points
            
        Returns:
            {timestamps: [...], prices: [...]}
        """
        try:
            # Convertir timeframe en millisecondes
            interval_map = {
                "1h": "1h",
                "4h": "4h",
                "1d": "1d",
                "1w": "1w"
            }
            
            interval = interval_map.get(timeframe, "1h")
            
            # Récupérer depuis Binance API
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            
            timestamps = []
            prices = []
            
            for kline in klines:
                # kline = [open_time, open, high, low, close, ...]
                timestamp = datetime.fromtimestamp(kline[0] / 1000)
                close_price = float(kline[4])
                
                timestamps.append(timestamp.strftime("%H:%M" if timeframe == "1h" else "%d/%m"))
                prices.append(close_price)
            
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "data": {
                    "timestamps": timestamps,
                    "prices": prices
                }
            }
            
        except Exception as e:
            LOG.error(f"Error fetching price history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pnl_history(self) -> Dict:
        """
        Récupère l'historique PNL du paper trading
        
        Returns:
            {timestamps: [...], pnl: [...]}
        """
        try:
            if not self.paper_trading_file.exists():
                return {
                    "success": True,
                    "data": {
                        "timestamps": [],
                        "pnl": []
                    }
                }
            
            with open(self.paper_trading_file, 'r') as f:
                state = json.load(f)
            
            pnl_history = state.get('pnl_history', [])
            
            timestamps = []
            pnl_values = []
            
            # Accumuler le PNL au fil du temps
            cumulative_pnl = 0
            
            for entry in pnl_history:
                timestamp = datetime.fromisoformat(entry.get('timestamp', datetime.now().isoformat()))
                pnl_change = entry.get('pnl', 0)
                cumulative_pnl += pnl_change
                
                timestamps.append(timestamp.strftime("%H:%M"))
                pnl_values.append(round(cumulative_pnl, 2))
            
            return {
                "success": True,
                "data": {
                    "timestamps": timestamps,
                    "pnl": pnl_values,
                    "total_pnl": cumulative_pnl
                }
            }
            
        except Exception as e:
            LOG.error(f"Error fetching PNL history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_portfolio_distribution(self) -> Dict:
        """
        Récupère la distribution du portfolio
        
        Returns:
            {labels: [...], values: [...]}
        """
        try:
            if not self.paper_trading_file.exists():
                return {
                    "success": True,
                    "data": {
                        "labels": ["USDT"],
                        "values": [100]
                    }
                }
            
            with open(self.paper_trading_file, 'r') as f:
                state = json.load(f)
            
            balance = state.get('balance', 10000)
            positions = state.get('positions', {})
            
            labels = ["USDT"]
            values = [balance]
            
            # Calculer la valeur de chaque position
            for symbol, position in positions.items():
                quantity = position.get('quantity', 0)
                entry_price = position.get('entry_price', 0)
                value = quantity * entry_price
                
                if value > 0:
                    # Extraire le nom de l'asset (ex: BTCUSDT -> BTC)
                    asset = symbol.replace("USDT", "").replace("USD", "")
                    labels.append(asset)
                    values.append(value)
            
            return {
                "success": True,
                "data": {
                    "labels": labels,
                    "values": values
                }
            }
            
        except Exception as e:
            LOG.error(f"Error fetching portfolio distribution: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trading_stats(self) -> Dict:
        """
        Récupère les statistiques de trading avancées
        
        Returns:
            Statistiques complètes
        """
        try:
            if not self.paper_trading_file.exists():
                return {
                    "success": True,
                    "stats": {
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0,
                        "avg_profit": 0,
                        "avg_loss": 0,
                        "best_trade": 0,
                        "worst_trade": 0,
                        "profit_factor": 0,
                        "total_fees": 0
                    }
                }
            
            with open(self.paper_trading_file, 'r') as f:
                state = json.load(f)
            
            trades = state.get('trades', [])
            orders = state.get('orders', {})
            
            # Analyser les trades
            total_trades = len(trades)
            total_fees = sum(t.get('fees', 0) for t in trades)
            
            # Calculer PNL par trade (buy-sell pairs)
            buy_trades = {}
            pnls = []
            
            for trade in trades:
                symbol = trade.get('symbol')
                side = trade.get('side')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                
                if side == 'buy':
                    if symbol not in buy_trades:
                        buy_trades[symbol] = []
                    buy_trades[symbol].append({'quantity': quantity, 'price': price})
                elif side == 'sell' and symbol in buy_trades and buy_trades[symbol]:
                    # Associer avec un buy
                    buy = buy_trades[symbol].pop(0)
                    pnl = (price - buy['price']) * min(quantity, buy['quantity'])
                    pnls.append(pnl)
            
            winning_trades = len([p for p in pnls if p > 0])
            losing_trades = len([p for p in pnls if p < 0])
            win_rate = (winning_trades / len(pnls) * 100) if pnls else 0
            
            profits = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]
            
            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            best_trade = max(pnls) if pnls else 0
            worst_trade = min(pnls) if pnls else 0
            
            total_profit = sum(profits)
            total_loss = abs(sum(losses))
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
            
            return {
                "success": True,
                "stats": {
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": losing_trades,
                    "win_rate": round(win_rate, 2),
                    "avg_profit": round(avg_profit, 2),
                    "avg_loss": round(avg_loss, 2),
                    "best_trade": round(best_trade, 2),
                    "worst_trade": round(worst_trade, 2),
                    "profit_factor": round(profit_factor, 2),
                    "total_fees": round(total_fees, 2),
                    "total_pnl": round(sum(pnls), 2)
                }
            }
            
        except Exception as e:
            LOG.error(f"Error calculating trading stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recent_trades(self, limit: int = 20) -> Dict:
        """
        Récupère les derniers trades
        
        Args:
            limit: Nombre de trades
            
        Returns:
            Liste des trades récents
        """
        try:
            if not self.paper_trading_file.exists():
                return {
                    "success": True,
                    "trades": []
                }
            
            with open(self.paper_trading_file, 'r') as f:
                state = json.load(f)
            
            trades = state.get('trades', [])
            
            # Trier par timestamp et prendre les derniers
            sorted_trades = sorted(
                trades,
                key=lambda t: t.get('timestamp', ''),
                reverse=True
            )[:limit]
            
            return {
                "success": True,
                "trades": sorted_trades
            }
            
        except Exception as e:
            LOG.error(f"Error fetching recent trades: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Instance globale
charts_api = ChartsAPI()


def register_chart_routes(app):
    """
    Enregistre les routes pour les graphiques
    
    Args:
        app: Instance FastAPI
    """
    
    @app.get("/api/chart/price")
    async def get_price_chart(symbol: str = "BTCUSDT", timeframe: str = "1h", limit: int = 24):
        """Récupère l'historique des prix"""
        return charts_api.get_price_history(symbol, timeframe, limit)
    
    @app.get("/api/chart/pnl")
    async def get_pnl_chart():
        """Récupère l'historique PNL"""
        return charts_api.get_pnl_history()
    
    @app.get("/api/chart/portfolio")
    async def get_portfolio_chart():
        """Récupère la distribution du portfolio"""
        return charts_api.get_portfolio_distribution()
    
    @app.get("/api/stats/trading")
    async def get_trading_statistics():
        """Récupère les statistiques de trading"""
        return charts_api.get_trading_stats()
    
    @app.get("/api/trades/recent")
    async def get_recent_trades_endpoint(limit: int = 20):
        """Récupère les derniers trades"""
        return charts_api.get_recent_trades(limit)
    
    @app.get("/api/portfolio")
    async def get_portfolio():
        """Récupère le portfolio complet"""
        try:
            from pathlib import Path
            import json
            
            paper_file = Path("/opt/smartorder-pro/data/paper_trading.json")
            if not paper_file.exists():
                return {
                    "balance": 0,
                    "positions": {},
                    "total_pnl": 0,
                    "initial_balance": 10000
                }
            
            with open(paper_file, 'r') as f:
                state = json.load(f)
            
            # Calculer PNL total
            trades = state.get('trades', [])
            buy_trades = {}
            total_pnl = 0
            
            for trade in trades:
                symbol = trade.get('symbol')
                side = trade.get('side')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                
                if side == 'buy':
                    if symbol not in buy_trades:
                        buy_trades[symbol] = []
                    buy_trades[symbol].append({'quantity': quantity, 'price': price})
                elif side == 'sell' and symbol in buy_trades and buy_trades[symbol]:
                    buy = buy_trades[symbol].pop(0)
                    pnl = (price - buy['price']) * min(quantity, buy['quantity'])
                    total_pnl += pnl
            
            return {
                "balance": state.get('balance', 0),
                "positions": state.get('positions', {}),
                "total_pnl": round(total_pnl, 2),
                "initial_balance": state.get('initial_balance', 10000)
            }
        except Exception as e:
            LOG.error(f"Error fetching portfolio: {e}")
            return {
                "balance": 0,
                "positions": {},
                "total_pnl": 0,
                "initial_balance": 10000
            }
    
    @app.get("/api/orders")
    async def get_orders():
        """Récupère tous les ordres"""
        try:
            from pathlib import Path
            import json
            
            paper_file = Path("/opt/smartorder-pro/data/paper_trading.json")
            if not paper_file.exists():
                return []
            
            with open(paper_file, 'r') as f:
                state = json.load(f)
            
            orders = state.get('orders', {})
            return list(orders.values())
        except Exception as e:
            LOG.error(f"Error fetching orders: {e}")
            return []
    
    LOG.info("✅ Chart routes registered")
