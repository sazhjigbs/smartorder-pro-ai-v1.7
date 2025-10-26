#!/usr/bin/env python3
"""
🔐 SAFELOGIC SmartOrder PRO — Advanced Authentication Module
JWT-based auth with sessions, multi-users, and role management
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import json

from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Users database (in production, use real database)
USERS_DB_FILE = "users.json"

class UserDatabase:
    """Simple file-based user database"""
    
    def __init__(self, file_path: str = USERS_DB_FILE):
        self.file_path = file_path
        self._ensure_default_user()
    
    def _ensure_default_user(self):
        """Create default admin user if no users exist"""
        if not os.path.exists(self.file_path):
            default_users = {
                "admin": {
                    "username": "admin",
                    "hashed_password": self.hash_password("SmartOrder2025!"),
                    "role": "admin",
                    "email": "admin@smartorder.pro",
                    "created_at": datetime.now().isoformat(),
                    "enabled": True
                }
            }
            self.save_users(default_users)
    
    def load_users(self) -> Dict:
        """Load users from file"""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_users(self, users: Dict):
        """Save users to file"""
        with open(self.file_path, 'w') as f:
            json.dump(users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        users = self.load_users()
        return users.get(username)
    
    def create_user(self, username: str, password: str, email: str, role: str = "user") -> bool:
        """Create a new user"""
        users = self.load_users()
        
        if username in users:
            return False
        
        users[username] = {
            "username": username,
            "hashed_password": self.hash_password(password),
            "role": role,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }
        
        self.save_users(users)
        return True
    
    def update_user(self, username: str, **kwargs) -> bool:
        """Update user information"""
        users = self.load_users()
        
        if username not in users:
            return False
        
        for key, value in kwargs.items():
            if key == "password":
                users[username]["hashed_password"] = self.hash_password(value)
            elif key in ["email", "role", "enabled"]:
                users[username][key] = value
        
        self.save_users(users)
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        users = self.load_users()
        
        if username not in users or username == "admin":  # Can't delete admin
            return False
        
        del users[username]
        self.save_users(users)
        return True
    
    def list_users(self) -> Dict:
        """List all users (without passwords)"""
        users = self.load_users()
        return {
            username: {k: v for k, v in user.items() if k != "hashed_password"}
            for username, user in users.items()
        }

# Initialize database
user_db = UserDatabase()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        return {"username": username, "role": payload.get("role")}
    
    except JWTError:
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password"""
    user = user_db.get_user(username)
    
    if not user:
        return None
    
    if not user.get("enabled", False):
        return None
    
    if not user_db.verify_password(password, user["hashed_password"]):
        return None
    
    return user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(credentials.credentials)
    
    if token_data is None:
        raise credentials_exception
    
    user = user_db.get_user(token_data["username"])
    
    if user is None:
        raise credentials_exception
    
    return user

async def require_auth(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Require authentication for route"""
    return current_user

async def require_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """Require admin role for route"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Session management
SESSIONS = {}  # In production, use Redis or similar

def create_session(username: str) -> str:
    """Create a session for user"""
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = {
        "username": username,
        "created_at": datetime.now(),
        "last_activity": datetime.now()
    }
    return session_id

def verify_session(session_id: str) -> Optional[str]:
    """Verify session and return username"""
    session = SESSIONS.get(session_id)
    
    if not session:
        return None
    
    # Check if session expired (24 hours)
    if datetime.now() - session["last_activity"] > timedelta(hours=24):
        del SESSIONS[session_id]
        return None
    
    # Update last activity
    session["last_activity"] = datetime.now()
    return session["username"]

def delete_session(session_id: str):
    """Delete session (logout)"""
    if session_id in SESSIONS:
        del SESSIONS[session_id]
