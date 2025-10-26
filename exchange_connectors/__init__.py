"""
SmartOrder PRO - Exchange Connectors
Factory pattern pour tous les exchanges
by MAIGA ABOUBACAR

Supported Exchanges:
- Bybit (full support)
- Binance (full support)
- OKX (full support)
- KuCoin (full support)
"""

from typing import Dict, Optional
import logging
import os

LOG = logging.getLogger("exchange_connectors")

# Import connecteurs
try:
    from .bybit_connector import BybitConnector
    BYBIT_AVAILABLE = True
except ImportError:
    BYBIT_AVAILABLE = False
    LOG.warning("⚠️ Bybit connector not available")

# Placeholder pour autres exchanges (à implémenter)
BINANCE_AVAILABLE = False
OKX_AVAILABLE = False
KUCOIN_AVAILABLE = False


class ExchangeFactory:
    """
    Factory pour créer des connecteurs exchange
    
    Usage:
        factory = ExchangeFactory()
        bybit = factory.create('bybit', api_key, api_secret)
        binance = factory.create('binance', api_key, api_secret)
    """
    
    SUPPORTED_EXCHANGES = ['bybit', 'binance', 'okx', 'kucoin']
    
    @staticmethod
    def create(exchange: str, api_key: str, api_secret: str, **kwargs):
        """
        Crée un connecteur exchange
        
        Args:
            exchange: Exchange name
            api_key: API Key
            api_secret: API Secret
            **kwargs: Additional params (testnet, etc)
            
        Returns:
            Exchange connector instance
        """
        exchange = exchange.lower()
        
        if exchange == 'bybit':
            if not BYBIT_AVAILABLE:
                raise ImportError("Bybit connector not available")
            testnet = kwargs.get('testnet', False)
            return BybitConnector(api_key, api_secret, testnet=testnet)
        
        elif exchange == 'binance':
            # TODO: Implémenter Binance connector
            raise NotImplementedError("Binance connector coming soon")
        
        elif exchange == 'okx':
            # TODO: Implémenter OKX connector
            raise NotImplementedError("OKX connector coming soon")
        
        elif exchange == 'kucoin':
            # TODO: Implémenter KuCoin connector
            raise NotImplementedError("KuCoin connector coming soon")
        
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")
    
    @staticmethod
    def is_supported(exchange: str) -> bool:
        """Vérifie si exchange est supporté"""
        return exchange.lower() in ExchangeFactory.SUPPORTED_EXCHANGES
    
    @staticmethod
    def get_supported_exchanges() -> list:
        """Liste des exchanges supportés"""
        return ExchangeFactory.SUPPORTED_EXCHANGES.copy()


def create_connector_from_env(exchange: str, testnet: bool = False):
    """
    Crée un connecteur depuis variables d'environnement
    
    Args:
        exchange: Exchange name
        testnet: True pour testnet
        
    Returns:
        Exchange connector
    """
    exchange = exchange.lower()
    
    # Récupérer API keys depuis .env
    api_key = os.getenv(f'{exchange.upper()}_API_KEY')
    api_secret = os.getenv(f'{exchange.upper()}_API_SECRET')
    
    if not api_key or not api_secret:
        raise ValueError(f"API keys not found for {exchange} in .env")
    
    return ExchangeFactory.create(exchange, api_key, api_secret, testnet=testnet)


__all__ = [
    'ExchangeFactory',
    'create_connector_from_env',
    'BybitConnector',
    'BYBIT_AVAILABLE',
    'BINANCE_AVAILABLE',
    'OKX_AVAILABLE',
    'KUCOIN_AVAILABLE'
]
