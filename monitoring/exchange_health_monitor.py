"""
SmartOrder PRO - Exchange Health Monitor
Surveillance en temps réel de la santé des exchanges
by MAIGA ABOUBACAR

Features:
- Ping check (latency)
- API status check
- Rate limit monitoring
- Auto-failover si exchange down
- Circuit breaker pattern
- Health score par exchange
"""

import time
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import threading

LOG = logging.getLogger("monitoring.health")

class HealthStatus(Enum):
    """Status de santé"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"

class CircuitState(Enum):
    """États du circuit breaker"""
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Trop d'erreurs, stop requests
    HALF_OPEN = "half_open"  # Test recovery

class ExchangeHealthMonitor:
    """
    Moniteur de santé des exchanges
    
    Surveille:
    - Latency (ping)
    - API availability
    - Error rate
    - Rate limits
    
    Actions:
    - Auto-failover
    - Circuit breaker
    - Alertes
    """
    
    def __init__(self):
        """Initialize Health Monitor"""
        self.exchanges = {}
        
        # Circuit breaker config
        self.circuit_breaker = {}
        self.error_threshold = 5  # Erreurs avant OPEN
        self.recovery_timeout = 60  # Secondes avant HALF_OPEN
        
        # Health check config
        self.check_interval = 30  # Secondes
        self.ping_timeout = 5  # Secondes
        
        # Metrics storage
        self.latency_history = defaultdict(lambda: deque(maxlen=100))
        self.error_count = defaultdict(int)
        self.last_check = {}
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitor_thread = None
        
        LOG.info("✅ Exchange Health Monitor initialized")
    
    def register_exchange(
        self,
        name: str,
        ping_url: str,
        api_url: Optional[str] = None,
        priority: int = 1
    ):
        """
        Enregistre un exchange à monitorer
        
        Args:
            name: Exchange name
            ping_url: URL pour ping check
            api_url: URL API pour health check
            priority: Priorité (1 = highest)
        """
        self.exchanges[name] = {
            'name': name,
            'ping_url': ping_url,
            'api_url': api_url,
            'priority': priority,
            'status': HealthStatus.UNKNOWN,
            'latency': 0,
            'last_check': None,
            'error_count': 0,
            'uptime_percent': 100.0
        }
        
        # Initialize circuit breaker
        self.circuit_breaker[name] = {
            'state': CircuitState.CLOSED,
            'failures': 0,
            'last_failure': None,
            'last_success': datetime.now()
        }
        
        LOG.info(f"✅ Exchange registered: {name}")
    
    def check_ping(self, exchange: str) -> Dict:
        """
        Vérifie le ping d'un exchange
        
        Args:
            exchange: Exchange name
            
        Returns:
            {'success': bool, 'latency': int (ms), 'status': str}
        """
        if exchange not in self.exchanges:
            return {'success': False, 'latency': 0, 'status': 'unknown'}
        
        ping_url = self.exchanges[exchange]['ping_url']
        
        try:
            start = time.time()
            response = requests.get(ping_url, timeout=self.ping_timeout)
            latency = int((time.time() - start) * 1000)  # ms
            
            success = response.status_code == 200
            
            # Update metrics
            self.latency_history[exchange].append(latency)
            
            if success:
                self._on_check_success(exchange, latency)
            else:
                self._on_check_failure(exchange, f"HTTP {response.status_code}")
            
            return {
                'success': success,
                'latency': latency,
                'status': 'ok' if success else 'error'
            }
            
        except requests.Timeout:
            self._on_check_failure(exchange, 'timeout')
            return {'success': False, 'latency': self.ping_timeout * 1000, 'status': 'timeout'}
        
        except Exception as e:
            self._on_check_failure(exchange, str(e))
            return {'success': False, 'latency': 0, 'status': 'error'}
    
    def check_api_status(self, exchange: str) -> bool:
        """
        Vérifie si l'API fonctionne
        
        Args:
            exchange: Exchange name
            
        Returns:
            True si API OK
        """
        if exchange not in self.exchanges:
            return False
        
        api_url = self.exchanges[exchange].get('api_url')
        if not api_url:
            # Pas d'URL API, on se fie au ping
            return self.exchanges[exchange]['status'] == HealthStatus.HEALTHY
        
        try:
            response = requests.get(api_url, timeout=self.ping_timeout)
            return response.status_code == 200
        except:
            return False
    
    def get_health_score(self, exchange: str) -> float:
        """
        Calcule score de santé (0-100)
        
        Args:
            exchange: Exchange name
            
        Returns:
            Health score (0-100)
        """
        if exchange not in self.exchanges:
            return 0.0
        
        ex = self.exchanges[exchange]
        score = 100.0
        
        # Status impact
        if ex['status'] == HealthStatus.DOWN:
            return 0.0
        elif ex['status'] == HealthStatus.DEGRADED:
            score -= 30
        
        # Latency impact
        if self.latency_history[exchange]:
            avg_latency = sum(self.latency_history[exchange]) / len(self.latency_history[exchange])
            
            if avg_latency > 1000:  # > 1s
                score -= 40
            elif avg_latency > 500:  # > 500ms
                score -= 20
            elif avg_latency > 200:  # > 200ms
                score -= 10
        
        # Error rate impact
        if ex['error_count'] > 10:
            score -= 30
        elif ex['error_count'] > 5:
            score -= 15
        
        return max(0.0, min(100.0, score))
    
    def get_best_exchange(self) -> Optional[str]:
        """
        Retourne le meilleur exchange disponible
        
        Returns:
            Exchange name ou None
        """
        best_exchange = None
        best_score = -1
        
        for name in self.exchanges:
            if self.exchanges[name]['status'] == HealthStatus.DOWN:
                continue
            
            score = self.get_health_score(name)
            
            # Prendre en compte la priorité
            priority_bonus = (10 - self.exchanges[name]['priority']) * 5
            total_score = score + priority_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_exchange = name
        
        return best_exchange
    
    def should_use_exchange(self, exchange: str) -> bool:
        """
        Détermine si on peut utiliser cet exchange
        
        Args:
            exchange: Exchange name
            
        Returns:
            True si utilisable
        """
        if exchange not in self.exchanges:
            return False
        
        # Check circuit breaker
        circuit = self.circuit_breaker[exchange]
        
        if circuit['state'] == CircuitState.OPEN:
            # Check si on peut passer en HALF_OPEN
            if circuit['last_failure']:
                time_since_failure = (datetime.now() - circuit['last_failure']).total_seconds()
                if time_since_failure > self.recovery_timeout:
                    circuit['state'] = CircuitState.HALF_OPEN
                    LOG.info(f"🔄 Circuit breaker HALF_OPEN: {exchange}")
                else:
                    return False
            else:
                return False
        
        # Check health status
        status = self.exchanges[exchange]['status']
        
        return status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def report_error(self, exchange: str, error: str):
        """
        Signale une erreur sur un exchange
        
        Args:
            exchange: Exchange name
            error: Error message
        """
        if exchange not in self.exchanges:
            return
        
        self._on_check_failure(exchange, error)
    
    def report_success(self, exchange: str):
        """
        Signale un succès sur un exchange
        
        Args:
            exchange: Exchange name
        """
        if exchange not in self.exchanges:
            return
        
        self._on_check_success(exchange)
    
    def _on_check_success(self, exchange: str, latency: int = 0):
        """Handler pour check réussi"""
        ex = self.exchanges[exchange]
        circuit = self.circuit_breaker[exchange]
        
        # Update status
        if latency > 1000:
            ex['status'] = HealthStatus.DEGRADED
        else:
            ex['status'] = HealthStatus.HEALTHY
        
        ex['latency'] = latency
        ex['last_check'] = datetime.now()
        ex['error_count'] = max(0, ex['error_count'] - 1)  # Decrease error count
        
        # Update circuit breaker
        circuit['failures'] = 0
        circuit['last_success'] = datetime.now()
        
        if circuit['state'] == CircuitState.HALF_OPEN:
            circuit['state'] = CircuitState.CLOSED
            LOG.info(f"✅ Circuit breaker CLOSED: {exchange}")
    
    def _on_check_failure(self, exchange: str, error: str):
        """Handler pour check échoué"""
        ex = self.exchanges[exchange]
        circuit = self.circuit_breaker[exchange]
        
        ex['status'] = HealthStatus.DOWN
        ex['last_check'] = datetime.now()
        ex['error_count'] += 1
        
        # Update circuit breaker
        circuit['failures'] += 1
        circuit['last_failure'] = datetime.now()
        
        if circuit['failures'] >= self.error_threshold:
            if circuit['state'] != CircuitState.OPEN:
                circuit['state'] = CircuitState.OPEN
                LOG.error(f"🔴 Circuit breaker OPEN: {exchange} (too many failures)")
        
        LOG.warning(f"⚠️ Health check failed for {exchange}: {error}")
    
    def auto_failover(self, current_exchange: str) -> Optional[str]:
        """
        Bascule automatiquement sur un exchange de backup
        
        Args:
            current_exchange: Exchange actuel (down)
            
        Returns:
            Nouvel exchange ou None
        """
        LOG.warning(f"🔄 Auto-failover triggered for {current_exchange}")
        
        # Trouver meilleur exchange de remplacement
        backup_exchange = self.get_best_exchange()
        
        if backup_exchange and backup_exchange != current_exchange:
            LOG.info(f"✅ Failover to {backup_exchange}")
            return backup_exchange
        else:
            LOG.error("❌ No healthy exchange available for failover!")
            return None
    
    def start_monitoring(self):
        """Démarre monitoring en background"""
        if self.monitoring_active:
            LOG.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        LOG.info("✅ Health monitoring started")
    
    def stop_monitoring(self):
        """Arrête monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        LOG.info("⏹️ Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Boucle de monitoring"""
        while self.monitoring_active:
            try:
                for exchange in self.exchanges:
                    self.check_ping(exchange)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                LOG.error(f"❌ Monitoring loop error: {e}")
                time.sleep(5)
    
    def get_status_report(self) -> Dict:
        """
        Génère rapport de statut
        
        Returns:
            Rapport complet de santé
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'exchanges': {},
            'best_exchange': self.get_best_exchange(),
            'summary': {
                'total': len(self.exchanges),
                'healthy': 0,
                'degraded': 0,
                'down': 0
            }
        }
        
        for name, ex in self.exchanges.items():
            health_score = self.get_health_score(name)
            circuit = self.circuit_breaker[name]
            
            report['exchanges'][name] = {
                'status': ex['status'].value,
                'health_score': health_score,
                'latency': ex['latency'],
                'error_count': ex['error_count'],
                'circuit_state': circuit['state'].value,
                'last_check': ex['last_check'].isoformat() if ex['last_check'] else None,
                'usable': self.should_use_exchange(name)
            }
            
            # Update summary
            if ex['status'] == HealthStatus.HEALTHY:
                report['summary']['healthy'] += 1
            elif ex['status'] == HealthStatus.DEGRADED:
                report['summary']['degraded'] += 1
            elif ex['status'] == HealthStatus.DOWN:
                report['summary']['down'] += 1
        
        return report


# Instance globale
_health_monitor = None

def get_health_monitor() -> ExchangeHealthMonitor:
    """Récupère l'instance singleton"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = ExchangeHealthMonitor()
    return _health_monitor


if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ SmartOrder PRO - Health Monitor")
    print("by MAIGA ABOUBACAR")
    print("=" * 60)
    
    monitor = ExchangeHealthMonitor()
    
    # Register exchanges
    print("\n✅ Registering exchanges...")
    monitor.register_exchange('bybit', 'https://api.bybit.com/v5/market/time', priority=1)
    monitor.register_exchange('binance', 'https://api.binance.com/api/v3/ping', priority=2)
    
    # Test ping
    print("\n✅ Testing ping...")
    for exchange in ['bybit', 'binance']:
        result = monitor.check_ping(exchange)
        print(f"   {exchange}: {result['status']} ({result['latency']}ms)")
    
    # Health scores
    print("\n✅ Health scores:")
    for exchange in ['bybit', 'binance']:
        score = monitor.get_health_score(exchange)
        print(f"   {exchange}: {score:.1f}/100")
    
    # Best exchange
    best = monitor.get_best_exchange()
    print(f"\n✅ Best exchange: {best}")
    
    # Status report
    print("\n✅ Status report:")
    report = monitor.get_status_report()
    print(f"   Total exchanges: {report['summary']['total']}")
    print(f"   Healthy: {report['summary']['healthy']}")
    print(f"   Degraded: {report['summary']['degraded']}")
    print(f"   Down: {report['summary']['down']}")
    
    print("\n" + "=" * 60)
    print("✅ Health Monitor Ready!")
    print("=" * 60)
