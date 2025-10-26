#!/usr/bin/env python3
"""
💰 SAFELOGIC SmartOrder PRO — Hybrid Capital Manager
Auto-management intelligent des positions existantes sur tous exchanges
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hybrid_capital_manager")

class HybridCapitalManager:
    """
    Gestionnaire intelligent du capital et positions existantes
    """
    
    def __init__(self):
        self.exchanges = {}
        self.portfolio_cache = {}
        self.auto_mode = False
        self.last_scan = None
        
        # Configuration depuis .env
        self.load_configuration()
        
        # Initialiser clients exchange
        self.init_exchange_clients()
    
    def load_configuration(self):
        """Charge la configuration depuis .env"""
        self.auto_mode = os.getenv("AUTO_MODE", "false").lower() == "true"
        self.max_simultaneous_orders = int(os.getenv("MAX_ORDERS", "20"))
        self.risk_per_trade = float(os.getenv("RISK_PER_TRADE", "0.02"))  # 2%
        self.min_profit_threshold = float(os.getenv("MIN_PROFIT", "0.001"))  # 0.1%
        
        logger.info(f"Configuration loaded - Auto mode: {self.auto_mode}")
    
    def init_exchange_clients(self):
        """Initialise les clients pour tous les exchanges"""
        try:
            # Bybit client (existant)
            from core.bybit_client import wallet_spot_balances, futures_positions
            self.exchanges['bybit'] = {
                'spot_balances': wallet_spot_balances,
                'futures_positions': futures_positions,
                'active': True
            }
            
            logger.info("✅ Bybit client initialized")
            
            # TODO: Ajouter Binance et KuCoin clients
            # self.exchanges['binance'] = {...}
            # self.exchanges['kucoin'] = {...}
            
        except Exception as e:
            logger.error(f"Error initializing exchange clients: {str(e)}")
    
    async def scan_all_positions(self) -> Dict[str, Any]:
        """Scanner complet de toutes les positions sur tous exchanges"""
        logger.info("🔍 Scanning all positions across exchanges...")
        
        portfolio = {
            "timestamp": datetime.now().isoformat(),
            "total_value_usdt": 0.0,
            "total_unrealized_pnl": 0.0,
            "spot_positions": {},
            "futures_positions": {},
            "exchanges_summary": {}
        }
        
        for exchange_name, client in self.exchanges.items():
            if not client['active']:
                continue
                
            try:
                logger.info(f"📊 Scanning {exchange_name}...")
                
                # Scan positions spot
                spot_data = client['spot_balances']()
                spot_positions = self.process_spot_positions(spot_data, exchange_name)
                
                # Scan positions futures
                futures_data = client['futures_positions']()
                futures_positions = self.process_futures_positions(futures_data, exchange_name)
                
                # Ajouter au portfolio global
                portfolio["spot_positions"][exchange_name] = spot_positions
                portfolio["futures_positions"][exchange_name] = futures_positions
                
                # Calculer valeurs totales
                exchange_value = sum(pos["value_usdt"] for pos in spot_positions)
                exchange_pnl = sum(pos["unrealized_pnl"] for pos in futures_positions)
                
                portfolio["exchanges_summary"][exchange_name] = {
                    "spot_value": exchange_value,
                    "futures_pnl": exchange_pnl,
                    "total_positions": len(spot_positions) + len(futures_positions)
                }
                
                portfolio["total_value_usdt"] += exchange_value
                portfolio["total_unrealized_pnl"] += exchange_pnl
                
                logger.info(f"✅ {exchange_name}: ${exchange_value:.2f} spot, ${exchange_pnl:.2f} PnL")
                
            except Exception as e:
                logger.error(f"Error scanning {exchange_name}: {str(e)}")
                portfolio["exchanges_summary"][exchange_name] = {"error": str(e)}
        
        # Cache du portfolio
        self.portfolio_cache = portfolio
        self.last_scan = datetime.now()
        
        logger.info(f"🎯 Portfolio scan complete: ${portfolio['total_value_usdt']:.2f} total")
        return portfolio
    
    def process_spot_positions(self, spot_data: Dict, exchange: str) -> List[Dict]:
        """Traite les données spot et identifie les opportunités"""
        positions = []
        
        if "spot" not in spot_data:
            return positions
        
        for asset_data in spot_data["spot"]:
            if isinstance(asset_data, dict) and "error" not in asset_data:
                asset = asset_data.get("asset", "UNKNOWN")
                quantity = float(asset_data.get("free", 0))
                
                if quantity > 0:  # Seulement les positions non-nulles
                    # Récupérer prix actuel (simulation)
                    current_price = self.get_mock_price(f"{asset}USDT")
                    value_usdt = quantity * current_price
                    
                    # Analyser l'opportunité
                    opportunity = self.analyze_spot_opportunity(asset, quantity, current_price)
                    
                    position = {
                        "asset": asset,
                        "quantity": quantity,
                        "current_price": current_price,
                        "value_usdt": value_usdt,
                        "exchange": exchange,
                        "opportunity": opportunity,
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    positions.append(position)
        
        return positions
    
    def process_futures_positions(self, futures_data: Dict, exchange: str) -> List[Dict]:
        """Traite les positions futures et calcule les optimisations"""
        positions = []
        
        if "futures" not in futures_data:
            return positions
        
        for position_data in futures_data["futures"]:
            if isinstance(position_data, dict) and "error" not in position_data:
                symbol = position_data.get("symbol", "UNKNOWN")
                size = float(position_data.get("size", 0))
                
                if size > 0:  # Position active
                    entry_price = float(position_data.get("entryPrice", 0))
                    current_price = self.get_mock_price(symbol)
                    unrealized_pnl = float(position_data.get("unrealPnl", 0))
                    side = position_data.get("side", "Buy")
                    leverage = float(position_data.get("leverage", 1))
                    
                    # Analyser l'optimisation possible
                    optimization = self.analyze_futures_optimization(
                        symbol, side, size, entry_price, current_price, leverage
                    )
                    
                    position = {
                        "symbol": symbol,
                        "side": side,
                        "size": size,
                        "entry_price": entry_price,
                        "current_price": current_price,
                        "unrealized_pnl": unrealized_pnl,
                        "leverage": leverage,
                        "exchange": exchange,
                        "optimization": optimization,
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    positions.append(position)
        
        return positions
    
    def analyze_spot_opportunity(self, asset: str, quantity: float, price: float) -> Dict:
        """Analyse les opportunités pour position spot"""
        # Simulation d'analyse technique
        volatility = 0.05  # 5% volatility simulée
        trend = "neutral"  # neutral/bullish/bearish
        
        # Déterminer la stratégie recommandée
        if asset in ["BTC", "ETH"]:
            if volatility > 0.08:
                strategy = "swing_trade"
                confidence = 0.75
            else:
                strategy = "hold_dca"
                confidence = 0.65
        else:
            strategy = "take_profit"
            confidence = 0.60
        
        return {
            "strategy": strategy,
            "confidence": confidence,
            "volatility": volatility,
            "trend": trend,
            "take_profit_levels": [price * 1.05, price * 1.10, price * 1.15],
            "stop_loss": price * 0.95
        }
    
    def analyze_futures_optimization(self, symbol: str, side: str, size: float, 
                                   entry_price: float, current_price: float, leverage: float) -> Dict:
        """Analyse l'optimisation pour position futures"""
        
        # Calculer PnL%
        if side == "Buy":
            pnl_pct = ((current_price - entry_price) / entry_price) * 100 * leverage
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100 * leverage
        
        # Volatilité simulée
        volatility = 0.08  # 8%
        
        # Recommandations d'optimisation
        if pnl_pct > 5:  # Profit > 5%
            action = "take_partial_profit"
            urgency = "medium"
        elif pnl_pct < -3:  # Loss > 3%
            action = "add_position_or_stop"
            urgency = "high"
        else:
            action = "monitor"
            urgency = "low"
        
        # Calcul leverage optimal selon volatilité
        if volatility > 0.10:
            optimal_leverage = min(leverage, 3)
        elif volatility < 0.05:
            optimal_leverage = min(leverage * 1.5, 10)
        else:
            optimal_leverage = leverage
        
        return {
            "action": action,
            "urgency": urgency,
            "pnl_pct": round(pnl_pct, 2),
            "volatility": volatility,
            "optimal_leverage": optimal_leverage,
            "stop_loss": current_price * (0.97 if side == "Buy" else 1.03),
            "take_profit_levels": self.calculate_take_profit_levels(current_price, side)
        }
    
    def calculate_take_profit_levels(self, price: float, side: str) -> List[float]:
        """Calcule les niveaux de take profit optimaux"""
        if side == "Buy":
            return [price * 1.02, price * 1.05, price * 1.08, price * 1.12]
        else:
            return [price * 0.98, price * 0.95, price * 0.92, price * 0.88]
    
    def get_mock_price(self, symbol: str) -> float:
        """Prix simulés (remplacer par vraie API)"""
        mock_prices = {
            "BTCUSDT": 67500,
            "ETHUSDT": 2480,
            "SOLUSDT": 185,
            "ADAUSDT": 0.45,
            "DOTUSDT": 5.2
        }
        return mock_prices.get(symbol, 100.0)
    
    async def execute_auto_management(self):
        """Exécution automatique de la gestion de portfolio"""
        if not self.auto_mode:
            logger.info("Auto mode disabled - skipping auto management")
            return
        
        logger.info("🤖 Starting auto-management cycle...")
        
        # 1. Scanner le portfolio
        portfolio = await self.scan_all_positions()
        
        # 2. Identifier les actions à prendre
        actions = self.identify_actions(portfolio)
        
        # 3. Exécuter les actions (simulation)
        if actions:
            logger.info(f"📋 {len(actions)} actions identified:")
            for action in actions[:5]:  # Limiter à 5 actions pour éviter spam
                logger.info(f"  - {action['type']}: {action['asset']} on {action['exchange']}")
        
        # 4. Sauvegarder l'état
        self.save_portfolio_state(portfolio)
        
        logger.info("✅ Auto-management cycle completed")
    
    def identify_actions(self, portfolio: Dict) -> List[Dict]:
        """Identifie les actions à prendre sur le portfolio"""
        actions = []
        
        # Analyser positions spot
        for exchange, positions in portfolio["spot_positions"].items():
            for position in positions:
                opportunity = position["opportunity"]
                
                if opportunity["confidence"] > 0.7:
                    if opportunity["strategy"] == "take_profit":
                        actions.append({
                            "type": "SPOT_TAKE_PROFIT",
                            "asset": position["asset"],
                            "exchange": exchange,
                            "quantity": position["quantity"] * 0.5,  # 50%
                            "price": opportunity["take_profit_levels"][0],
                            "confidence": opportunity["confidence"]
                        })
                    elif opportunity["strategy"] == "swing_trade":
                        actions.append({
                            "type": "SPOT_SWING_SETUP",
                            "asset": position["asset"],
                            "exchange": exchange,
                            "quantity": position["quantity"] * 0.3,  # 30%
                            "confidence": opportunity["confidence"]
                        })
        
        # Analyser positions futures
        for exchange, positions in portfolio["futures_positions"].items():
            for position in positions:
                optimization = position["optimization"]
                
                if optimization["urgency"] == "high":
                    actions.append({
                        "type": "FUTURES_URGENT_ACTION",
                        "symbol": position["symbol"],
                        "exchange": exchange,
                        "action": optimization["action"],
                        "current_pnl": optimization["pnl_pct"]
                    })
                elif optimization["action"] == "take_partial_profit":
                    actions.append({
                        "type": "FUTURES_PARTIAL_PROFIT",
                        "symbol": position["symbol"],
                        "exchange": exchange,
                        "size": position["size"] * 0.4,  # 40%
                        "price": optimization["take_profit_levels"][0]
                    })
        
        return actions
    
    def save_portfolio_state(self, portfolio: Dict):
        """Sauvegarde l'état du portfolio"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/portfolio_state.json", "w") as f:
                json.dump(portfolio, f, indent=2, default=str)
            
            logger.info("💾 Portfolio state saved")
        except Exception as e:
            logger.error(f"Error saving portfolio state: {str(e)}")
    
    def get_portfolio_summary(self) -> Dict:
        """Résumé rapide du portfolio"""
        if not self.portfolio_cache:
            return {"error": "No portfolio data available"}
        
        return {
            "total_value": self.portfolio_cache["total_value_usdt"],
            "total_pnl": self.portfolio_cache["total_unrealized_pnl"],
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "auto_mode": self.auto_mode,
            "exchanges_count": len([e for e in self.exchanges.values() if e['active']])
        }

# Instance globale
capital_manager = HybridCapitalManager()

# API publique
async def scan_portfolio():
    """API: Scanner le portfolio"""
    return await capital_manager.scan_all_positions()

async def enable_auto_mode():
    """API: Activer le mode automatique"""
    capital_manager.auto_mode = True
    logger.info("🤖 Auto mode ENABLED")
    return {"status": "auto_mode_enabled"}

async def disable_auto_mode():
    """API: Désactiver le mode automatique"""
    capital_manager.auto_mode = False
    logger.info("⏸️ Auto mode DISABLED")
    return {"status": "auto_mode_disabled"}

def get_portfolio_summary():
    """API: Résumé rapide du portfolio"""
    return capital_manager.get_portfolio_summary()

async def run_auto_management():
    """API: Lancer un cycle d'auto-management"""
    return await capital_manager.execute_auto_management()

if __name__ == "__main__":
    # Test du module
    async def test():
        print("🧪 Testing Hybrid Capital Manager...")
        
        # Scanner portfolio
        portfolio = await scan_portfolio()
        print(f"Portfolio value: ${portfolio['total_value_usdt']:.2f}")
        
        # Résumé
        summary = get_portfolio_summary()
        print(f"Summary: {summary}")
        
        # Test auto-management
        await enable_auto_mode()
        await run_auto_management()
    
    asyncio.run(test())