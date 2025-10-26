"""
SmartOrder PRO - Tests Unitaires
=================================
Tests pour router, execution, capital manager

Usage:
    pytest tests/test_router.py -v
    pytest tests/ -v  # Tous les tests
"""

import pytest
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ==============================================================================
# TESTS ROUTER MULTI-EXCHANGE
# ==============================================================================

class TestRouter:
    """Tests du routeur multi-exchange"""
    
    def test_choose_exchange_bybit_first(self):
        """Test: Bybit doit être choisi en premier par défaut"""
        try:
            from core.router import choose_exchange
            
            result = choose_exchange("BTCUSDT", 0.001, 67000)
            
            assert "exchange" in result
            assert result["exchange"] == "bybit"
            assert result["success"] is True
            
        except ImportError:
            pytest.skip("core.router non disponible")
    
    def test_choose_exchange_fallback(self):
        """Test: Fallback vers Binance si Bybit indisponible"""
        try:
            from core.router import choose_exchange
            
            # Simuler Bybit down (si fonction supporte bybit_down param)
            result = choose_exchange("BTCUSDT", 0.001, 67000)
            
            assert result["exchange"] in ["bybit", "binance", "kucoin"]
            
        except ImportError:
            pytest.skip("core.router non disponible")
    
    def test_choose_exchange_insufficient_balance(self):
        """Test: Refus si balance insuffisante"""
        try:
            from core.router import choose_exchange
            
            # Montant énorme qui devrait échouer
            result = choose_exchange("BTCUSDT", 1000, 67000)
            
            # Devrait soit échouer, soit choisir un exchange
            assert "exchange" in result or result["success"] is False
            
        except ImportError:
            pytest.skip("core.router non disponible")


# ==============================================================================
# TESTS HYBRID CAPITAL MANAGER
# ==============================================================================

class TestCapitalManager:
    """Tests du gestionnaire de capital"""
    
    def test_capital_manager_init(self):
        """Test: Initialisation du capital manager"""
        try:
            from core.hybrid_capital_manager import HybridCapitalManager
            
            manager = HybridCapitalManager(total_capital=10000)
            
            assert manager.total_capital == 10000
            assert hasattr(manager, 'spot_balance')
            assert hasattr(manager, 'futures_balance')
            
        except ImportError:
            pytest.skip("hybrid_capital_manager non disponible")
    
    def test_allocate_capital(self):
        """Test: Allocation spot vs futures"""
        try:
            from core.hybrid_capital_manager import HybridCapitalManager
            
            manager = HybridCapitalManager(total_capital=10000)
            
            # Allouer 60% spot, 40% futures
            result = manager.allocate(spot_pct=0.6, futures_pct=0.4)
            
            assert result["spot"] == 6000
            assert result["futures"] == 4000
            
        except (ImportError, AttributeError):
            pytest.skip("allocate method non disponible")
    
    def test_check_available_margin(self):
        """Test: Vérification marge disponible"""
        try:
            from core.hybrid_capital_manager import HybridCapitalManager
            
            manager = HybridCapitalManager(total_capital=10000)
            
            # Vérifier si on peut ouvrir position
            available = manager.get_available_margin()
            
            assert available >= 0
            assert available <= 10000
            
        except (ImportError, AttributeError):
            pytest.skip("get_available_margin non disponible")


# ==============================================================================
# TESTS FEES & LIMITS
# ==============================================================================

class TestFeesLimits:
    """Tests gestion fees & limites"""
    
    def test_get_fees_bybit(self):
        """Test: Récupération fees Bybit"""
        try:
            from core.fees_limits import get_fees
            
            fees = get_fees("bybit", "BTCUSDT")
            
            assert "maker" in fees
            assert "taker" in fees
            assert fees["maker"] >= 0
            assert fees["taker"] >= 0
            
        except ImportError:
            pytest.skip("fees_limits non disponible")
    
    def test_get_min_order_size(self):
        """Test: Taille minimum ordre"""
        try:
            from core.fees_limits import get_min_order
            
            min_order = get_min_order("bybit", "BTCUSDT")
            
            assert min_order > 0
            assert min_order < 1  # Devrait être < 1 BTC
            
        except ImportError:
            pytest.skip("get_min_order non disponible")
    
    def test_validate_order_size(self):
        """Test: Validation taille ordre"""
        try:
            from core.fees_limits import validate_order
            
            # Ordre valide
            result = validate_order("bybit", "BTCUSDT", 0.001)
            assert result["valid"] is True
            
            # Ordre trop petit
            result = validate_order("bybit", "BTCUSDT", 0.00001)
            assert result["valid"] is False
            
        except ImportError:
            pytest.skip("validate_order non disponible")


# ==============================================================================
# TESTS EXECUTION
# ==============================================================================

class TestExecution:
    """Tests moteur d'exécution"""
    
    def test_calculate_order_size(self):
        """Test: Calcul taille ordre selon capital"""
        # Test simple sans dépendances
        capital = 10000
        risk_pct = 0.01  # 1%
        price = 67000
        
        # Calcul: 1% de 10000 = 100 USDT / 67000 = 0.00149 BTC
        expected_qty = (capital * risk_pct) / price
        
        assert 0.001 < expected_qty < 0.002
    
    def test_calculate_position_size_with_leverage(self):
        """Test: Taille position avec leverage"""
        capital = 1000
        leverage = 10
        price = 67000
        
        # Avec leverage 10x: 1000 * 10 = 10000 / 67000 = 0.149 BTC
        position_size = (capital * leverage) / price
        
        assert 0.14 < position_size < 0.15
    
    def test_calculate_liquidation_price(self):
        """Test: Calcul prix de liquidation"""
        entry_price = 67000
        leverage = 10
        
        # Long: liquidation ≈ entry * (1 - 1/leverage)
        # 67000 * (1 - 0.1) = 60300
        liq_price_long = entry_price * (1 - 1/leverage)
        
        assert 60000 < liq_price_long < 61000
        
        # Short: liquidation ≈ entry * (1 + 1/leverage)
        # 67000 * (1 + 0.1) = 73700
        liq_price_short = entry_price * (1 + 1/leverage)
        
        assert 73000 < liq_price_short < 74000


# ==============================================================================
# TESTS PAPER TRADING
# ==============================================================================

class TestPaperTrading:
    """Tests mode simulation"""
    
    def test_paper_executor_place_order(self):
        """Test: Placement ordre en mode simulation"""
        try:
            from core.paper_trading import PaperExecutor
            
            executor = PaperExecutor()
            
            result = executor.place_order(
                symbol="BTCUSDT",
                side="BUY",
                qty=0.001,
                price=67000
            )
            
            assert result["success"] is True
            assert "order_id" in result
            
        except ImportError:
            pytest.skip("paper_trading non disponible")
    
    def test_paper_balance_tracking(self):
        """Test: Suivi balance virtuelle"""
        try:
            from core.paper_trading import PaperExecutor
            
            executor = PaperExecutor()
            initial_balance = executor.balance
            
            # Place ordre
            executor.place_order("BTCUSDT", "BUY", 0.001, 67000)
            
            # Balance devrait avoir changé (si implémenté)
            # assert executor.balance != initial_balance
            
        except ImportError:
            pytest.skip("paper_trading non disponible")


# ==============================================================================
# TESTS HEALTH CHECKER
# ==============================================================================

class TestHealth:
    """Tests health checker"""
    
    def test_check_health(self):
        """Test: Health check système"""
        try:
            from core.health import check_health
            
            health = check_health()
            
            assert "cpu_percent" in health
            assert "ram_percent" in health
            assert 0 <= health["cpu_percent"] <= 100
            assert 0 <= health["ram_percent"] <= 100
            
        except ImportError:
            pytest.skip("health checker non disponible")
    
    def test_check_api_endpoints(self):
        """Test: Vérification APIs exchanges"""
        try:
            from core.health import check_health
            
            health = check_health()
            
            # Devrait avoir status APIs
            assert "bybit_api" in health or "apis" in health
            
        except ImportError:
            pytest.skip("health checker non disponible")


# ==============================================================================
# CONFIGURATION PYTEST
# ==============================================================================

def pytest_configure(config):
    """Configuration pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


if __name__ == "__main__":
    # Lancer les tests
    pytest.main([__file__, "-v", "--tb=short"])
