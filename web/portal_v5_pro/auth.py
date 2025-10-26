#!/usr/bin/env python3
"""
🔐 SAFELOGIC SmartOrder PRO — Authentication Module
Simple auth pour sécuriser dashboard
"""

import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

# Credentials (à changer en production!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "SmartOrder2025!"  # Change this!

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Vérifie username/password"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Helper pour routes protégées
def require_auth(username: str = Depends(verify_credentials)):
    """Decorator pour routes nécessitant auth"""
    return username
