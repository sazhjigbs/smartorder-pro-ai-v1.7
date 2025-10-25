from fastapi import Request, HTTPException
import os

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "SafeLogicProAI2025")

async def verify_admin(request: Request):
    token = request.headers.get("X-Admin-Token")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
