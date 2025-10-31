#!/usr/bin/env python3
"""
SmartOrder PRO - Paper Trading avec Quantum Grid + Modules Avancés
"""
import sys
import os
import asyncio
from datetime import datetime

# Ajouter le path
sys.path.insert(0, '/opt/smartorder-pro')

from core.paper_trading_engine_v2 import PaperTradingEngine
from strategies.quantum_grid import QuantumGrid
from core.trailing_stop_manager import TrailingStopManager
from core.smart_order_engine import SmartOrderEngine
from core.risk_manager_advanced import AdvancedRiskManager
from core.fee_optimizer import FeeOptimizer
from ai.strategy_composer import AIStrategyComposer

class QuantumPaperTrader:
    def __init__(self):
        print("=" * 70)
        print("🚀 SmartOrder PRO - Paper Trading QUANTUM")
        print("=" * 70)
        
        # Engine principal
        self.paper_engine = PaperTradingEngine(
            initial_balance=10000,
            exchange_name='bybit'
        )
        
        # Stratégie Quantum Grid
        self.quantum_grid = QuantumGrid(
            symbol='BTCUSDT',
            grid_levels=20,
            upper_price=120000,
            lower_price=100000,
            investment=5000
        )
        
        # Modules avancés
        self.trailing_stop = TrailingStopManager(
            callback_rate=2.0,  # 2% trailing
            activation_price_distance=1.5  # Active après +1.5%
        )
        
        self.smart_orders = SmartOrderEngine()
        
        self.risk_manager = AdvancedRiskManager(
            max_daily_loss=500,  # Max -500 USDT par jour
            max_position_size_pct=30,  # Max 30% du capital par position
            max_total_risk_pct=60  # Max 60% du capital en risque
        )
        
        self.fee_optimizer = FeeOptimizer(
            target_fee_tier='VIP1',
            enable_batching=True
        )
        
        self.ai_composer = AIStrategyComposer()
        
        print(f"\n✅ Modules chargés:")
        print(f"   📊 Quantum Grid: {self.quantum_grid.grid_levels} niveaux")
        print(f"   🎯 Trailing Stop: {self.trailing_stop.callback_rate}%")
        print(f"   🛡️  Risk Manager: -${self.risk_manager.max_daily_loss}/jour max")
        print(f"   💰 Fee Optimizer: Tier {self.fee_optimizer.target_fee_tier}")
        print(f"   🤖 AI Composer: Actif")
        
    async def run(self):
        """Lancer le trading en boucle"""
        print(f"\n🎯 Démarrage du trading...")
        print(f"   Symbol: BTCUSDT")
        print(f"   Balance: {self.paper_engine.balance} USDT")
        print(f"   Mode: PAPER TRADING")
        print("=" * 70 + "\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 1. Vérifier le risk manager
                if not self.risk_manager.can_open_position(
                    symbol='BTCUSDT',
                    current_balance=self.paper_engine.balance
                ):
                    print(f"[{timestamp}] ⚠️  Risk Manager: Limite atteinte, pause...")
                    await asyncio.sleep(60)
                    continue
                
                # 2. AI Strategy Composer suggère le meilleur setup
                market_regime = await self.get_market_regime()
                ai_suggestion = self.ai_composer.suggest_strategy(market_regime)
                
                # 3. Quantum Grid génère les ordres
                orders = self.quantum_grid.generate_orders(
                    current_price=await self.get_current_price(),
                    balance=self.paper_engine.balance
                )
                
                # 4. Fee Optimizer optimise le timing
                if self.fee_optimizer.should_batch_orders(orders):
                    orders = self.fee_optimizer.batch_orders(orders)
                
                # 5. Exécuter les ordres via Smart Order Engine
                for order in orders:
                    result = await self.smart_orders.execute_smart_order(
                        order_type=order['type'],
                        symbol=order['symbol'],
                        side=order['side'],
                        quantity=order['quantity'],
                        price=order.get('price'),
                        engine=self.paper_engine
                    )
                    
                    if result['success']:
                        print(f"[{timestamp}] ✅ {order['side'].upper()} {order['quantity']} @ {order.get('price', 'MARKET')}")
                
                # 6. Vérifier les trailing stops
                await self.check_trailing_stops()
                
                # 7. Afficher les stats
                if iteration % 10 == 0:
                    self.print_stats()
                
                # Attendre 30s avant la prochaine itération
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            print("\n\n⏸️  Trading arrêté par l'utilisateur")
            self.print_final_stats()
    
    async def get_current_price(self):
        """Récupérer le prix actuel"""
        try:
            import ccxt
            exchange = ccxt.bybit()
            ticker = exchange.fetch_ticker('BTC/USDT')
            return ticker['last']
        except:
            return 110000  # Fallback
    
    async def get_market_regime(self):
        """Détecter le régime de marché"""
        # Simplifié pour le moment
        return 'trending_up'
    
    async def check_trailing_stops(self):
        """Vérifier et mettre à jour les trailing stops"""
        for position in self.paper_engine.get_positions():
            current_price = await self.get_current_price()
            
            should_close = self.trailing_stop.update_and_check(
                symbol=position['symbol'],
                current_price=current_price,
                position=position
            )
            
            if should_close:
                # Fermer la position
                self.paper_engine.close_position(position['symbol'])
                print(f"🎯 Trailing Stop triggered: {position['symbol']} @ {current_price}")
    
    def print_stats(self):
        """Afficher les statistiques"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        stats = self.paper_engine.get_stats()
        
        print(f"\n[{timestamp}] 📊 Stats:")
        print(f"   Balance: {stats['balance']:.2f} USDT")
        print(f"   PNL: {stats['total_pnl']:.2f} USDT ({stats['pnl_pct']:.2f}%)")
        print(f"   Positions: {stats['active_positions']}")
        print(f"   Trades: {stats['total_trades']} (Win: {stats['win_rate']:.1f}%)")
        print()
    
    def print_final_stats(self):
        """Afficher les stats finales"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ FINAL")
        print("=" * 70)
        
        stats = self.paper_engine.get_stats()
        
        print(f"\n💰 Performance:")
        print(f"   Balance finale: {stats['balance']:.2f} USDT")
        print(f"   Balance initiale: {stats['initial_balance']:.2f} USDT")
        print(f"   PNL total: {stats['total_pnl']:.2f} USDT")
        print(f"   ROI: {stats['pnl_pct']:.2f}%")
        
        print(f"\n📈 Trading:")
        print(f"   Trades total: {stats['total_trades']}")
        print(f"   Win rate: {stats['win_rate']:.1f}%")
        print(f"   Meilleur trade: {stats['best_trade']:.2f} USDT")
        print(f"   Pire trade: {stats['worst_trade']:.2f} USDT")
        
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    trader = QuantumPaperTrader()
    asyncio.run(trader.run())
