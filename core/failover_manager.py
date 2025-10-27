"""
Failover Manager
Bascule automatiquement vers autre exchange si l'actif tombe

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime

LOG = logging.getLogger(__name__)


class FailoverManager:
    """
    Gère le failover automatique entre exchanges
    
    Features:
    - Auto-switch si exchange down
    - Priority-based failover
    - Integration avec health monitor + circuit breaker
    - Fallback chain configurable
    - Notify on failover
    """
    
    def __init__(self,
                 unified_manager,
                 health_monitor=None,
                 circuit_breaker=None):
        """
        Initialize Failover Manager
        
        Args:
            unified_manager: UnifiedTradingManager instance
            health_monitor: ExchangeHealthMonitor instance (optional)
            circuit_breaker: CircuitBreaker instance (optional)
        """
        self.manager = unified_manager
        self.health_monitor = health_monitor or unified_manager.health_monitor
        self.circuit_breaker = circuit_breaker
        
        # Failover configuration per exchange
        self.failover_config = {}
        
        # Failover history
        self.failover_history = []
        
        # Notification callbacks
        self.notification_callbacks = []
        
        LOG.info("✅ Failover Manager initialized")
    
    def set_failover_chain(self, exchange: str, fallback_chain: List[str]):
        """
        Configure failover chain for an exchange
        
        Args:
            exchange: Primary exchange
            fallback_chain: List of fallback exchanges (in priority order)
        
        Example:
            manager.set_failover_chain('bybit', ['binance', 'okx', 'kucoin'])
        """
        self.failover_config[exchange] = {
            'fallback_chain': fallback_chain,
            'current_fallback': None,
            'failover_count': 0,
            'last_failover': None
        }
        
        LOG.info(f"✅ Failover chain set for {exchange}: {' -> '.join(fallback_chain)}")
    
    def add_notification_callback(self, callback: Callable):
        """
        Add callback to be notified on failover
        
        Args:
            callback: Function(from_exchange, to_exchange, reason)
        """
        self.notification_callbacks.append(callback)
    
    def get_available_exchange(self, preferred_exchange: str) -> Optional[str]:
        """
        Get available exchange (with automatic failover)
        
        Args:
            preferred_exchange: Preferred exchange
        
        Returns:
            Available exchange name (may be different if failover occurred)
        """
        # Check if preferred exchange is available
        if self._is_exchange_available(preferred_exchange):
            # Reset fallback if back to primary
            if preferred_exchange in self.failover_config:
                if self.failover_config[preferred_exchange]['current_fallback']:
                    LOG.info(f"✅ {preferred_exchange} recovered, switching back from {self.failover_config[preferred_exchange]['current_fallback']}")
                    self.failover_config[preferred_exchange]['current_fallback'] = None
            
            return preferred_exchange
        
        # Primary down, try failover
        LOG.warning(f"⚠️ {preferred_exchange} unavailable, attempting failover...")
        
        # Get failover chain
        if preferred_exchange not in self.failover_config:
            LOG.error(f"❌ No failover chain configured for {preferred_exchange}")
            return None
        
        config = self.failover_config[preferred_exchange]
        fallback_chain = config['fallback_chain']
        
        # Try each fallback in order
        for fallback_exchange in fallback_chain:
            if self._is_exchange_available(fallback_exchange):
                # Failover successful
                self._execute_failover(
                    from_exchange=preferred_exchange,
                    to_exchange=fallback_exchange,
                    reason="Primary exchange unavailable"
                )
                
                config['current_fallback'] = fallback_exchange
                config['failover_count'] += 1
                config['last_failover'] = datetime.now()
                
                return fallback_exchange
        
        # All fallbacks failed
        LOG.error(f"❌ All failover options exhausted for {preferred_exchange}")
        return None
    
    def _is_exchange_available(self, exchange: str) -> bool:
        """
        Check if exchange is available
        
        Args:
            exchange: Exchange name
        
        Returns:
            True if available
        """
        # Check if exchange is initialized
        if exchange not in self.manager.connectors:
            return False
        
        # Check health monitor
        if self.health_monitor:
            if not self.health_monitor.is_healthy(exchange):
                return False
        
        # Check circuit breaker
        if self.circuit_breaker:
            if not self.circuit_breaker.is_available(exchange):
                return False
        
        return True
    
    def _execute_failover(self,
                          from_exchange: str,
                          to_exchange: str,
                          reason: str):
        """
        Execute failover and notify
        
        Args:
            from_exchange: Source exchange (down)
            to_exchange: Target exchange (fallback)
            reason: Reason for failover
        """
        LOG.warning(f"🔄 FAILOVER: {from_exchange} -> {to_exchange} (reason: {reason})")
        
        # Record failover
        failover_event = {
            'timestamp': datetime.now().isoformat(),
            'from_exchange': from_exchange,
            'to_exchange': to_exchange,
            'reason': reason
        }
        
        self.failover_history.append(failover_event)
        
        # Notify callbacks
        for callback in self.notification_callbacks:
            try:
                callback(from_exchange, to_exchange, reason)
            except Exception as e:
                LOG.error(f"❌ Notification callback failed: {e}")
    
    def execute_with_failover(self,
                              exchange: str,
                              func: Callable,
                              *args,
                              **kwargs):
        """
        Execute function with automatic failover on failure
        
        Args:
            exchange: Preferred exchange
            func: Function to execute (should accept exchange parameter)
            *args, **kwargs: Function arguments
        
        Returns:
            Function result
        """
        # Get available exchange (with auto failover)
        available_exchange = self.get_available_exchange(exchange)
        
        if not available_exchange:
            raise Exception(f"No available exchange for failover from {exchange}")
        
        # Execute function with available exchange
        try:
            # Inject exchange parameter
            if 'exchange' in kwargs:
                kwargs['exchange'] = available_exchange
            else:
                # Assume first arg is exchange
                args = (available_exchange,) + args[1:]
            
            result = func(*args, **kwargs)
            
            return result
        
        except Exception as e:
            LOG.error(f"❌ Failed to execute on {available_exchange}: {e}")
            raise
    
    def get_failover_stats(self, exchange: str = None) -> Dict:
        """
        Get failover statistics
        
        Args:
            exchange: Exchange name (optional, returns all if not specified)
        
        Returns:
            Failover stats
        """
        if exchange:
            if exchange not in self.failover_config:
                return {}
            
            config = self.failover_config[exchange]
            
            return {
                'exchange': exchange,
                'fallback_chain': config['fallback_chain'],
                'current_fallback': config['current_fallback'],
                'failover_count': config['failover_count'],
                'last_failover': config['last_failover'].isoformat() if config['last_failover'] else None
            }
        else:
            # Return all
            return {
                ex: self.get_failover_stats(ex)
                for ex in self.failover_config.keys()
            }
    
    def get_failover_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent failover history
        
        Args:
            limit: Max number of events to return
        
        Returns:
            List of failover events
        """
        return self.failover_history[-limit:]
    
    def reset_failover(self, exchange: str):
        """
        Reset failover state for an exchange
        
        Args:
            exchange: Exchange name
        """
        if exchange in self.failover_config:
            self.failover_config[exchange]['current_fallback'] = None
            LOG.info(f"✅ Failover reset for {exchange}")


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Mock objects for testing
    class MockManager:
        def __init__(self):
            self.connectors = {
                'bybit': None,
                'binance': None,
                'okx': None
            }
            self.health_monitor = MockHealthMonitor()
    
    class MockHealthMonitor:
        def __init__(self):
            self.health_status = {
                'bybit': False,  # Down
                'binance': True,
                'okx': True
            }
        
        def is_healthy(self, exchange):
            return self.health_status.get(exchange, False)
    
    # Create failover manager
    manager = MockManager()
    failover = FailoverManager(manager)
    
    # Configure failover chain
    failover.set_failover_chain('bybit', ['binance', 'okx', 'kucoin'])
    
    # Add notification callback
    def on_failover(from_ex, to_ex, reason):
        print(f"📢 ALERT: Failover from {from_ex} to {to_ex} - {reason}")
    
    failover.add_notification_callback(on_failover)
    
    # Test failover
    print("\nTesting failover...")
    print("=" * 50)
    
    available = failover.get_available_exchange('bybit')
    print(f"\nPreferred: bybit")
    print(f"Available: {available}")
    
    # Stats
    print("\nFailover stats:")
    stats = failover.get_failover_stats('bybit')
    print(f"Fallback chain: {stats['fallback_chain']}")
    print(f"Current fallback: {stats['current_fallback']}")
    print(f"Failover count: {stats['failover_count']}")
    
    # History
    print("\nFailover history:")
    for event in failover.get_failover_history():
        print(f"  {event['timestamp']}: {event['from_exchange']} -> {event['to_exchange']}")
