"""
Tests Unitaires pour SmartOrder PRO AI v1.7
Teste tous les modules créés
"""
import unittest
import asyncio
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trailing_stop_manager import TrailingStopManager, TrailingConfig, TrailingType
from core.smart_order_engine import SmartOrderEngine
from core.copy_trading_engine import CopyTradingEngine, Trader, CopyConfig, CopyMode
from core.market_scanner import MarketScanner
from core.risk_manager_advanced import RiskManagerAdvanced, RiskLimits
from core.multi_timeframe_analyzer import MultiTimeframeAnalyzer, Timeframe
from strategies.quantum_grid import QuantumGrid, QuantumGridConfig
from ai.strategy_composer import AIStrategyComposer, StrategyType, MarketRegime
from notifications.notification_manager import NotificationManager, NotificationConfig, NotificationPriority
from backtesting.backtesting_engine_pro import BacktestingEnginePro, BacktestConfig
from core.arbitrage_executor import ArbitrageExecutor, ArbitrageOpportunity, ArbitrageType
from ai.emotion_detector import EmotionDetector, SocialPost
from core.cross_strategy_hedger import CrossStrategyHedger, HedgingMode
from core.fee_optimizer import FeeOptimizer, FeeStrategy
import numpy as np


class TestTrailingStopManager(unittest.TestCase):
    """Tests pour Trailing Stop Manager"""
    
    def setUp(self):
        self.manager = TrailingStopManager()
    
    def test_add_trailing_stop(self):
        """Test ajout d'un trailing stop"""
        config = TrailingConfig(
            symbol="BTCUSDT",
            side="buy",
            entry_price=50000,
            current_price=50000,
            trailing_type=TrailingType.BOTH,
            stop_loss_percent=2.0
        )
        trail_id = self.manager.add_trailing_stop(config)
        self.assertIsNotNone(trail_id)
        self.assertEqual(len(self.manager.active_trails), 1)
    
    def test_trailing_stop_trigger(self):
        """Test déclenchement du stop loss"""
        config = TrailingConfig(
            symbol="BTCUSDT",
            side="buy",
            entry_price=50000,
            current_price=50000,
            trailing_type=TrailingType.STOP_LOSS,
            stop_loss_percent=2.0
        )
        trail_id = self.manager.add_trailing_stop(config)
        
        # Prix baisse de 3%
        result = self.manager.update_price(trail_id, 48500)
        self.assertTrue(result["triggered"])
        self.assertEqual(result["action"], "SELL")


class TestSmartOrderEngine(unittest.TestCase):
    """Tests pour Smart Order Engine"""
    
    def setUp(self):
        self.engine = SmartOrderEngine()
    
    def test_oco_order(self):
        """Test ordre OCO"""
        async def run_test():
            result = await self.engine.place_oco_order(
                symbol="BTCUSDT",
                side="buy",
                quantity=0.1,
                stop_loss_price=49000,
                take_profit_price=52000
            )
            self.assertIn("group_id", result)
            self.assertEqual(len(self.engine.orders), 2)
        
        asyncio.run(run_test())
    
    def test_twap_order(self):
        """Test ordre TWAP"""
        async def run_test():
            order_id = await self.engine.place_twap_order(
                symbol="BTCUSDT",
                side="buy",
                total_quantity=1.0,
                duration_seconds=10,
                num_slices=2
            )
            self.assertIsNotNone(order_id)
            self.assertIn(order_id, self.engine.orders)
        
        asyncio.run(run_test())


class TestCopyTradingEngine(unittest.TestCase):
    """Tests pour Copy Trading"""
    
    def setUp(self):
        self.engine = CopyTradingEngine()
    
    def test_register_trader(self):
        """Test enregistrement trader"""
        trader = Trader(
            trader_id="test_trader",
            name="Test Trader",
            total_trades=100,
            winning_trades=75,
            total_pnl=5000
        )
        result = self.engine.register_trader(trader)
        self.assertTrue(result)
        self.assertIn("test_trader", self.engine.traders)
    
    def test_copy_trading(self):
        """Test copie de trade"""
        trader = Trader(trader_id="t1", name="Trader1")
        self.engine.register_trader(trader)
        
        config = CopyConfig(
            follower_id="follower1",
            trader_id="t1",
            mode=CopyMode.MIRROR
        )
        copy_id = self.engine.start_copying(config)
        self.assertIsNotNone(copy_id)


class TestMarketScanner(unittest.TestCase):
    """Tests pour Market Scanner"""
    
    def setUp(self):
        self.scanner = MarketScanner()
    
    def test_scan_patterns(self):
        """Test scan de patterns"""
        candles = [
            {"open": 50000, "high": 50500, "low": 49500, "close": 50200, "volume": 100},
            {"open": 50200, "high": 50800, "low": 50000, "close": 50600, "volume": 120},
            {"open": 50600, "high": 51000, "low": 50500, "close": 50900, "volume": 150}
        ]
        results = self.scanner.scan_candlestick_patterns("BTCUSDT", candles)
        self.assertIsInstance(results, list)
    
    def test_volume_spike(self):
        """Test détection volume spike"""
        candles = [{"close": 50000, "volume": 100} for _ in range(20)]
        candles.append({"close": 50000, "volume": 300})  # Spike
        
        result = self.scanner.scan_volume_spike("BTCUSDT", candles, threshold=2.0)
        self.assertIsNotNone(result)


class TestRiskManagerAdvanced(unittest.TestCase):
    """Tests pour Risk Manager"""
    
    def setUp(self):
        limits = RiskLimits(
            max_daily_loss=500,
            max_drawdown_percent=10.0
        )
        self.manager = RiskManagerAdvanced(10000, limits)
    
    def test_position_sizing(self):
        """Test calcul taille position"""
        result = self.manager.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=50000,
            stop_loss_price=49000,
            risk_percent=1.0
        )
        self.assertIn("quantity", result)
        self.assertGreater(result["quantity"], 0)
    
    def test_daily_loss_limit(self):
        """Test limite de perte journalière"""
        self.manager.daily_pnl = -600
        can_trade = self.manager.check_can_trade()
        self.assertFalse(can_trade["allowed"])


class TestMultiTimeframeAnalyzer(unittest.TestCase):
    """Tests pour Multi-Timeframe Analyzer"""
    
    def setUp(self):
        self.analyzer = MultiTimeframeAnalyzer()
    
    def test_analyze_timeframe(self):
        """Test analyse timeframe"""
        prices = [50000 + i * 10 for i in range(100)]
        data = {'closes': prices, 'volumes': [1000] * 100}
        
        result = self.analyzer.analyze_timeframe("BTCUSDT", Timeframe.H1, data)
        self.assertIsNotNone(result)
    
    def test_confluence(self):
        """Test détection confluence"""
        prices = [50000 + i * 10 for i in range(100)]
        data = {'closes': prices, 'highs': [p * 1.01 for p in prices], 
                'lows': [p * 0.99 for p in prices], 'volumes': [1000] * 100}
        
        self.analyzer.analyze_timeframe("BTCUSDT", Timeframe.H1, data)
        self.analyzer.analyze_timeframe("BTCUSDT", Timeframe.H4, data)
        
        confluence = self.analyzer.get_confluence("BTCUSDT")
        self.assertIn("confluence", confluence)


class TestQuantumGrid(unittest.TestCase):
    """Tests pour Quantum Grid"""
    
    def setUp(self):
        config = QuantumGridConfig(
            symbol="BTCUSDT",
            initial_price=50000,
            total_investment=10000,
            grid_levels=10
        )
        self.grid = QuantumGrid(config)
    
    def test_grid_initialization(self):
        """Test initialisation grille"""
        self.assertGreater(len(self.grid.grid_orders), 0)
    
    def test_grid_update(self):
        """Test mise à jour grille"""
        market_data = {"volatility": 0.03}
        result = self.grid.update(50500, market_data)
        self.assertIn("actions", result)


class TestAIStrategyComposer(unittest.TestCase):
    """Tests pour AI Strategy Composer"""
    
    def setUp(self):
        self.composer = AIStrategyComposer()
    
    def test_regime_detection(self):
        """Test détection régime marché"""
        prices = [50000 + i * 50 for i in range(100)]
        data = {
            'closes': prices,
            'highs': [p * 1.01 for p in prices],
            'lows': [p * 0.99 for p in prices],
            'volumes': [1000] * 100
        }
        regime = self.composer.detect_market_regime(data)
        self.assertIsNotNone(regime)
    
    def test_strategy_selection(self):
        """Test sélection stratégie"""
        prices = [50000] * 100
        data = {'closes': prices, 'highs': prices, 'lows': prices, 'volumes': [1000] * 100}
        
        result = self.composer.select_best_strategy(data)
        self.assertIn("selected_strategy", result)


class TestBacktestingEngine(unittest.TestCase):
    """Tests pour Backtesting Engine"""
    
    def setUp(self):
        config = BacktestConfig(initial_capital=10000)
        self.engine = BacktestingEnginePro(config)
    
    def test_backtest(self):
        """Test backtest simple"""
        def strategy(data, **params):
            return {"action": "buy", "quantity": 0.1}
        
        prices = [10000 + i * 10 for i in range(100)]
        data = {'closes': prices, 'timestamps': list(range(100))}
        
        results = self.engine.run_backtest(strategy, data)
        self.assertIn("total_trades", results)
    
    def test_monte_carlo(self):
        """Test Monte Carlo"""
        # Créer trades fictifs
        from backtesting.backtesting_engine_pro import Trade
        self.engine.trades = [
            Trade(0, 1, 100, 110, 1, "buy", 10, 10, 0.1) for _ in range(20)
        ]
        
        mc_results = self.engine.monte_carlo_simulation()
        self.assertIn("mean_return", mc_results)


class TestArbitrageExecutor(unittest.TestCase):
    """Tests pour Arbitrage Executor"""
    
    def setUp(self):
        self.executor = ArbitrageExecutor()
        self.executor.register_exchange_client("binance", {})
        self.executor.register_exchange_client("bybit", {})
    
    def test_arbitrage_execution(self):
        """Test exécution arbitrage"""
        async def run_test():
            opp = ArbitrageOpportunity(
                type=ArbitrageType.SIMPLE,
                symbol="BTCUSDT",
                buy_exchange="binance",
                sell_exchange="bybit",
                buy_price=50000,
                sell_price=50500,
                spread_percent=1.0,
                estimated_profit=50,
                min_quantity=0.001,
                max_quantity=0.1,
                timestamp=time.time()
            )
            
            result = await self.executor.execute_arbitrage(opp)
            self.assertIn("success", result)
        
        asyncio.run(run_test())


class TestEmotionDetector(unittest.TestCase):
    """Tests pour Emotion Detector"""
    
    def setUp(self):
        self.detector = EmotionDetector()
    
    def test_sentiment_analysis(self):
        """Test analyse sentiment"""
        posts = [
            SocialPost("twitter", "Bitcoin to the moon!", "user1", time.time(), likes=100),
            SocialPost("reddit", "BTC is crashing", "user2", time.time(), likes=20)
        ]
        
        result = self.detector.analyze_batch(posts)
        self.assertIn("overall_sentiment", result)
    
    def test_fomo_panic_detection(self):
        """Test détection FOMO/Panic"""
        posts = [
            SocialPost("twitter", "FOMO all in!", "user1", time.time()),
            SocialPost("twitter", "Buy now!", "user2", time.time())
        ]
        
        result = self.detector.detect_fomo_panic(posts)
        self.assertIn("emotion", result)


class TestCrossStrategyHedger(unittest.TestCase):
    """Tests pour Cross-Strategy Hedger"""
    
    def setUp(self):
        self.hedger = CrossStrategyHedger(mode=HedgingMode.MODERATE)
    
    def test_add_position(self):
        """Test ajout position"""
        result = self.hedger.add_spot_position(
            symbol="BTCUSDT",
            side="buy",
            quantity=0.5,
            entry_price=50000
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(self.hedger.spot_positions), 1)
    
    def test_hedge_creation(self):
        """Test création hedge"""
        self.hedger.add_spot_position("BTCUSDT", "buy", 0.5, 50000)
        self.assertGreater(len(self.hedger.hedge_positions), 0)


class TestFeeOptimizer(unittest.TestCase):
    """Tests pour Fee Optimizer"""
    
    def setUp(self):
        self.optimizer = FeeOptimizer(strategy=FeeStrategy.BALANCED)
    
    def test_add_order(self):
        """Test ajout ordre"""
        result = self.optimizer.add_order("BTCUSDT", "buy", 0.1, urgency="low")
        self.assertIsNotNone(result)
    
    def test_batching(self):
        """Test batching d'ordres"""
        orders = [
            {"symbol": "BTCUSDT", "side": "buy", "quantity": 0.1},
            {"symbol": "BTCUSDT", "side": "buy", "quantity": 0.2},
            {"symbol": "ETHUSDT", "side": "sell", "quantity": 1.0}
        ]
        
        batched = self.optimizer.batch_similar_orders(orders)
        self.assertEqual(len(batched), 2)


class TestIntegration(unittest.TestCase):
    """Tests d'intégration entre modules"""
    
    def test_risk_manager_with_trailing_stop(self):
        """Test intégration Risk Manager + Trailing Stop"""
        limits = RiskLimits(max_daily_loss=500)
        risk_mgr = RiskManagerAdvanced(10000, limits)
        trail_mgr = TrailingStopManager()
        
        # Vérifier si trading autorisé
        can_trade = risk_mgr.check_can_trade()
        self.assertTrue(can_trade["allowed"])
        
        # Ajouter trailing stop
        config = TrailingConfig(
            symbol="BTCUSDT",
            side="buy",
            entry_price=50000,
            current_price=50000,
            trailing_type=TrailingType.BOTH
        )
        trail_id = trail_mgr.add_trailing_stop(config)
        self.assertIsNotNone(trail_id)
    
    def test_strategy_composer_with_market_scanner(self):
        """Test AI Composer + Market Scanner"""
        composer = AIStrategyComposer()
        scanner = MarketScanner()
        
        # Scanner détecte opportunités
        candles = [
            {"open": 50000, "high": 50500, "low": 49500, "close": 50200, "volume": 100}
            for _ in range(50)
        ]
        opportunities = scanner.scan_candlestick_patterns("BTCUSDT", candles)
        
        # AI Composer sélectionne stratégie
        prices = [c["close"] for c in candles]
        market_data = {'closes': prices, 'highs': prices, 'lows': prices, 'volumes': [100] * 50}
        strategy = composer.select_best_strategy(market_data)
        
        self.assertIsNotNone(strategy)
        self.assertIsInstance(opportunities, list)


def run_all_tests():
    """Lance tous les tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestTrailingStopManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartOrderEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestCopyTradingEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketScanner))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManagerAdvanced))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiTimeframeAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantumGrid))
    suite.addTests(loader.loadTestsFromTestCase(TestAIStrategyComposer))
    suite.addTests(loader.loadTestsFromTestCase(TestBacktestingEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestArbitrageExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestEmotionDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossStrategyHedger))
    suite.addTests(loader.loadTestsFromTestCase(TestFeeOptimizer))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 SMARTORDER PRO AI v1.7 - TESTS UNITAIRES")
    print("=" * 70)
    
    result = run_all_tests()
    
    print("\n" + "=" * 70)
    print("📊 RÉSULTATS:")
    print(f"✅ Tests réussis: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Échecs: {len(result.failures)}")
    print(f"⚠️  Erreurs: {len(result.errors)}")
    print(f"⏭️  Ignorés: {len(result.skipped)}")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("✅ TOUS LES TESTS PASSÉS!")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
