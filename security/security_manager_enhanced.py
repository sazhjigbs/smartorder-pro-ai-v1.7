#!/usr/bin/env python3
"""
🔥 SmartOrder PRO - Security Manager Enhanced
by MAIGA ABOUBACAR

Features:
- IP Whitelist
- Rate Limiting
- 2FA Support
- Circuit Breaker renforcé
"""

import os
import time
import hashlib
import logging
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta

LOG = logging.getLogger("security")
LOG.setLevel(logging.INFO)

class RateLimiter:
    """Rate limiting avancé"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Vérifie si requête autorisée"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            LOG.warning(f"⚠️ Rate limit exceeded for {key}")
            return False
        
        self.requests[key].append(now)
        return True

class IPWhitelist:
    """Gestion whitelist IP"""
    def __init__(self, whitelist: List[str] = None):
        self.whitelist = set(whitelist or ["127.0.0.1", "::1"])
        LOG.info(f"✅ IP Whitelist initialized: {len(self.whitelist)} IPs")
    
    def is_allowed(self, ip: str) -> bool:
        """Vérifie si IP autorisée"""
        return ip in self.whitelist
    
    def add_ip(self, ip: str):
        """Ajoute IP"""
        self.whitelist.add(ip)
        LOG.info(f"✅ IP added to whitelist: {ip}")
    
    def remove_ip(self, ip: str):
        """Retire IP"""
        if ip in self.whitelist:
            self.whitelist.remove(ip)
            LOG.info(f"✅ IP removed from whitelist: {ip}")

class TwoFactorAuth:
    """2FA simple (TOTP)"""
    def __init__(self):
        self.enabled = os.getenv("ENABLE_2FA", "false").lower() == "true"
        self.secret = os.getenv("2FA_SECRET", "")
        LOG.info(f"✅ 2FA {'enabled' if self.enabled else 'disabled'}")
    
    def verify_code(self, code: str) -> bool:
        """Vérifie code 2FA"""
        if not self.enabled:
            return True
        # TODO: Implement TOTP verification
        return code == "123456"  # Mock

class CircuitBreakerEnhanced:
    """Circuit breaker renforcé"""
    def __init__(self, threshold: int = 5, timeout: int = 300):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = defaultdict(int)
        self.last_failure = {}
        self.state = {}  # closed | open | half_open
    
    def record_failure(self, key: str):
        """Enregistre échec"""
        self.failures[key] += 1
        self.last_failure[key] = time.time()
        
        if self.failures[key] >= self.threshold:
            self.state[key] = "open"
            LOG.warning(f"🔴 Circuit breaker OPEN for {key}")
    
    def record_success(self, key: str):
        """Enregistre succès"""
        self.failures[key] = 0
        self.state[key] = "closed"
    
    def is_allowed(self, key: str) -> bool:
        """Vérifie si opération autorisée"""
        state = self.state.get(key, "closed")
        
        if state == "closed":
            return True
        
        if state == "open":
            # Check if timeout expired
            last_fail = self.last_failure.get(key, 0)
            if time.time() - last_fail > self.timeout:
                self.state[key] = "half_open"
                LOG.info(f"🟡 Circuit breaker HALF-OPEN for {key}")
                return True
            return False
        
        # half_open
        return True

class SecurityManager:
    """Manager de sécurité global"""
    def __init__(self):
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.ip_whitelist = IPWhitelist()
        self.two_fa = TwoFactorAuth()
        self.circuit_breaker = CircuitBreakerEnhanced()
        LOG.info("✅ Security Manager Enhanced initialized")
    
    def check_access(self, ip: str, user_id: str, two_fa_code: str = None) -> bool:
        """Vérifie accès complet"""
        # IP whitelist
        if not self.ip_whitelist.is_allowed(ip):
            LOG.warning(f"❌ IP not whitelisted: {ip}")
            return False
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user_id):
            LOG.warning(f"❌ Rate limit exceeded: {user_id}")
            return False
        
        # 2FA
        if self.two_fa.enabled and not self.two_fa.verify_code(two_fa_code or ""):
            LOG.warning(f"❌ 2FA failed: {user_id}")
            return False
        
        return True

_security_mgr = None
def get_security_manager():
    global _security_mgr
    if _security_mgr is None:
        _security_mgr = SecurityManager()
    return _security_mgr
