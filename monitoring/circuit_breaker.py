"""
Circuit Breaker Pattern
Stop automatique si trop d'erreurs sur un exchange

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import time
import logging
from enum import Enum
from typing import Dict, Callable
from datetime import datetime, timedelta

LOG = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Too many failures, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker pour protéger contre cascades d'erreurs
    
    States:
    - CLOSED: Normal, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    Features:
    - Configurable failure threshold
    - Automatic recovery attempt after timeout
    - Per-exchange configuration
    - Metrics tracking
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 timeout: int = 60,
                 half_open_max_calls: int = 3):
        """
        Initialize Circuit Breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting recovery (OPEN -> HALF_OPEN)
            half_open_max_calls: Max calls allowed in HALF_OPEN state
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        
        # Circuit state per exchange
        self.circuits = {}
        
        LOG.info(f"✅ Circuit Breaker initialized (threshold={failure_threshold}, timeout={timeout}s)")
    
    def _init_circuit(self, name: str):
        """Initialize circuit for an exchange"""
        if name not in self.circuits:
            self.circuits[name] = {
                'state': CircuitState.CLOSED,
                'failure_count': 0,
                'success_count': 0,
                'last_failure_time': None,
                'last_state_change': datetime.now(),
                'half_open_calls': 0,
                'total_calls': 0,
                'total_failures': 0
            }
    
    def call(self, name: str, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        
        Args:
            name: Circuit name (e.g., exchange name)
            func: Function to execute
            *args, **kwargs: Function arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is OPEN or function fails
        """
        self._init_circuit(name)
        circuit = self.circuits[name]
        
        circuit['total_calls'] += 1
        
        # Check circuit state
        state = self._get_state(name)
        
        if state == CircuitState.OPEN:
            LOG.warning(f"⚠️ Circuit {name} is OPEN, request blocked")
            raise Exception(f"Circuit {name} is OPEN")
        
        if state == CircuitState.HALF_OPEN:
            if circuit['half_open_calls'] >= self.half_open_max_calls:
                LOG.warning(f"⚠️ Circuit {name} HALF_OPEN limit reached")
                raise Exception(f"Circuit {name} HALF_OPEN limit reached")
            
            circuit['half_open_calls'] += 1
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success(name)
            return result
        
        except Exception as e:
            self._on_failure(name)
            raise
    
    def _get_state(self, name: str) -> CircuitState:
        """
        Get current circuit state (with auto-transition from OPEN to HALF_OPEN)
        
        Args:
            name: Circuit name
        
        Returns:
            Current circuit state
        """
        self._init_circuit(name)
        circuit = self.circuits[name]
        
        # Check if should transition from OPEN to HALF_OPEN
        if circuit['state'] == CircuitState.OPEN:
            if circuit['last_failure_time']:
                elapsed = time.time() - circuit['last_failure_time']
                
                if elapsed >= self.timeout:
                    LOG.info(f"🔄 Circuit {name}: OPEN -> HALF_OPEN (timeout reached)")
                    self._set_state(name, CircuitState.HALF_OPEN)
        
        return circuit['state']
    
    def _set_state(self, name: str, new_state: CircuitState):
        """Set circuit state"""
        self._init_circuit(name)
        circuit = self.circuits[name]
        
        old_state = circuit['state']
        circuit['state'] = new_state
        circuit['last_state_change'] = datetime.now()
        
        if new_state == CircuitState.HALF_OPEN:
            circuit['half_open_calls'] = 0
        
        LOG.info(f"🔄 Circuit {name}: {old_state.value} -> {new_state.value}")
    
    def _on_success(self, name: str):
        """Handle successful call"""
        self._init_circuit(name)
        circuit = self.circuits[name]
        
        circuit['success_count'] += 1
        
        state = circuit['state']
        
        if state == CircuitState.HALF_OPEN:
            # Success in HALF_OPEN -> transition to CLOSED
            LOG.info(f"✅ Circuit {name}: HALF_OPEN -> CLOSED (success)")
            self._set_state(name, CircuitState.CLOSED)
            circuit['failure_count'] = 0
        
        elif state == CircuitState.CLOSED:
            # Reset failure count on success
            circuit['failure_count'] = 0
    
    def _on_failure(self, name: str):
        """Handle failed call"""
        self._init_circuit(name)
        circuit = self.circuits[name]
        
        circuit['failure_count'] += 1
        circuit['total_failures'] += 1
        circuit['last_failure_time'] = time.time()
        
        state = circuit['state']
        
        if state == CircuitState.HALF_OPEN:
            # Failure in HALF_OPEN -> back to OPEN
            LOG.error(f"❌ Circuit {name}: HALF_OPEN -> OPEN (failure)")
            self._set_state(name, CircuitState.OPEN)
        
        elif state == CircuitState.CLOSED:
            if circuit['failure_count'] >= self.failure_threshold:
                # Too many failures -> OPEN
                LOG.error(f"❌ Circuit {name}: CLOSED -> OPEN (threshold reached: {circuit['failure_count']})")
                self._set_state(name, CircuitState.OPEN)
    
    def reset(self, name: str):
        """
        Manually reset a circuit to CLOSED state
        
        Args:
            name: Circuit name
        """
        self._init_circuit(name)
        
        self._set_state(name, CircuitState.CLOSED)
        self.circuits[name]['failure_count'] = 0
        self.circuits[name]['half_open_calls'] = 0
        
        LOG.info(f"🔄 Circuit {name} manually reset to CLOSED")
    
    def get_state(self, name: str) -> str:
        """
        Get current circuit state
        
        Args:
            name: Circuit name
        
        Returns:
            State as string
        """
        return self._get_state(name).value
    
    def is_available(self, name: str) -> bool:
        """
        Check if circuit allows requests
        
        Args:
            name: Circuit name
        
        Returns:
            True if requests allowed
        """
        state = self._get_state(name)
        return state in [CircuitState.CLOSED, CircuitState.HALF_OPEN]
    
    def get_stats(self, name: str) -> Dict:
        """
        Get circuit statistics
        
        Args:
            name: Circuit name
        
        Returns:
            Statistics dictionary
        """
        self._init_circuit(name)
        circuit = self.circuits[name]
        
        return {
            'name': name,
            'state': circuit['state'].value,
            'failure_count': circuit['failure_count'],
            'success_count': circuit['success_count'],
            'total_calls': circuit['total_calls'],
            'total_failures': circuit['total_failures'],
            'success_rate': (circuit['success_count'] / circuit['total_calls'] * 100) if circuit['total_calls'] > 0 else 0,
            'last_state_change': circuit['last_state_change'].isoformat() if circuit['last_state_change'] else None
        }
    
    def get_all_stats(self) -> Dict:
        """
        Get statistics for all circuits
        
        Returns:
            Dictionary with all circuit stats
        """
        return {
            name: self.get_stats(name)
            for name in self.circuits.keys()
        }


# Global circuit breaker instance
_global_circuit_breaker = None


def get_circuit_breaker(
    failure_threshold: int = 5,
    timeout: int = 60,
    half_open_max_calls: int = 3
) -> CircuitBreaker:
    """
    Get or create global circuit breaker instance
    
    Args:
        failure_threshold: Number of failures before opening
        timeout: Seconds before recovery attempt
        half_open_max_calls: Max calls in half-open state
    
    Returns:
        CircuitBreaker instance
    """
    global _global_circuit_breaker
    
    if _global_circuit_breaker is None:
        _global_circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            half_open_max_calls=half_open_max_calls
        )
    
    return _global_circuit_breaker


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    breaker = CircuitBreaker(failure_threshold=3, timeout=5)
    
    def failing_function():
        """Function that always fails"""
        raise Exception("Simulated failure")
    
    def success_function():
        """Function that succeeds"""
        return "Success!"
    
    # Test circuit breaker
    print("Testing Circuit Breaker...")
    print("=" * 50)
    
    # Simulate failures
    for i in range(5):
        try:
            breaker.call('test_exchange', failing_function)
        except Exception as e:
            print(f"Attempt {i+1}: {e}")
        
        stats = breaker.get_stats('test_exchange')
        print(f"State: {stats['state']}, Failures: {stats['failure_count']}")
    
    # Try after circuit opens
    print("\nCircuit should be OPEN now:")
    try:
        breaker.call('test_exchange', success_function)
    except Exception as e:
        print(f"Blocked: {e}")
    
    # Wait for timeout
    print(f"\nWaiting {breaker.timeout} seconds for timeout...")
    time.sleep(breaker.timeout + 1)
    
    # Try again (should be HALF_OPEN)
    print("\nCircuit should be HALF_OPEN now:")
    try:
        result = breaker.call('test_exchange', success_function)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Final stats
    print("\nFinal stats:")
    stats = breaker.get_stats('test_exchange')
    print(f"State: {stats['state']}")
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total failures: {stats['total_failures']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
