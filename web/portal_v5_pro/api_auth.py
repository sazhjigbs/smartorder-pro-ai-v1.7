#!/usr/bin/env python3
"""
🔐 SAFELOGIC SmartOrder PRO — Authentication API Routes
Login, logout, user management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from pydantic import BaseModel, EmailStr
from typing import Optional

from web.portal_v5_pro.auth_advanced import (
    authenticate_user,
    create_access_token,
    create_session,
    delete_session,
    verify_session,
    user_db,
    require_auth,
    require_admin
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    role: str = "user"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    enabled: Optional[bool] = None

class MessageResponse(BaseModel):
    message: str
    success: bool

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, response: Response):
    """
    Login endpoint
    Returns JWT token for authentication
    """
    user = authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    
    # Create session
    session_id = create_session(user["username"])
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user["username"],
        role=user["role"]
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    """
    Logout endpoint
    Invalidates session
    """
    session_id = request.cookies.get("session_id")
    
    if session_id:
        delete_session(session_id)
    
    response.delete_cookie("session_id")
    
    return MessageResponse(message="Logged out successfully", success=True)

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """
    Get current user information
    Requires authentication
    """
    return {
        "username": current_user["username"],
        "email": current_user.get("email"),
        "role": current_user["role"],
        "created_at": current_user.get("created_at")
    }

@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users():
    """
    List all users
    Admin only
    """
    return {"users": user_db.list_users()}

@router.post("/users", dependencies=[Depends(require_admin)], response_model=MessageResponse)
async def create_user(user_data: UserCreate):
    """
    Create a new user
    Admin only
    """
    success = user_db.create_user(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email,
        role=user_data.role
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    return MessageResponse(message=f"User {user_data.username} created successfully", success=True)

@router.put("/users/{username}", dependencies=[Depends(require_admin)], response_model=MessageResponse)
async def update_user(username: str, user_data: UserUpdate):
    """
    Update user information
    Admin only
    """
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}
    
    success = user_db.update_user(username, **update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return MessageResponse(message=f"User {username} updated successfully", success=True)

@router.delete("/users/{username}", dependencies=[Depends(require_admin)], response_model=MessageResponse)
async def delete_user(username: str):
    """
    Delete a user
    Admin only
    Cannot delete admin user
    """
    success = user_db.delete_user(username)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete user (user not found or is admin)"
        )
    
    return MessageResponse(message=f"User {username} deleted successfully", success=True)

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(require_auth)
):
    """
    Change current user's password
    """
    # Verify old password
    user = authenticate_user(current_user["username"], old_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )
    
    # Update password
    user_db.update_user(current_user["username"], password=new_password)
    
    return MessageResponse(message="Password changed successfully", success=True)
