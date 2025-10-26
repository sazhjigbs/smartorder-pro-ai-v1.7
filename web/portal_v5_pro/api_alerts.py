#!/usr/bin/env python3
"""
🚨 SAFELOGIC SmartOrder PRO — Alerts API
REST endpoints for alert management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from web.portal_v5_pro.auth_advanced import require_auth
from web.portal_v5_pro.alert_manager import (
    alert_manager,
    AlertType,
    AlertCondition,
    AlertStatus,
    ALERT_TEMPLATES
)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Pydantic models
class AlertCreate(BaseModel):
    alert_type: str
    condition: str
    threshold: float
    symbol: Optional[str] = None
    message: Optional[str] = ""
    telegram_notify: bool = True
    email_notify: bool = False
    expires_hours: Optional[int] = None

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    threshold: Optional[float] = None
    message: Optional[str] = None

@router.get("/")
async def list_alerts(
    status: Optional[str] = None,
    current_user: dict = Depends(require_auth)
):
    """
    List all alerts for current user
    """
    alert_status = AlertStatus(status) if status else None
    alerts = alert_manager.get_alerts(
        user=current_user["username"],
        status=alert_status
    )
    
    return {
        "success": True,
        "alerts": [alert.to_dict() for alert in alerts],
        "count": len(alerts)
    }

@router.post("/")
async def create_alert(
    alert_data: AlertCreate,
    current_user: dict = Depends(require_auth)
):
    """
    Create a new alert
    """
    try:
        alert_type = AlertType(alert_data.alert_type)
        condition = AlertCondition(alert_data.condition)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid alert type or condition: {e}")
    
    # Calculate expiration
    expires_at = None
    if alert_data.expires_hours:
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(hours=alert_data.expires_hours)
    
    alert = alert_manager.create_alert(
        user=current_user["username"],
        alert_type=alert_type,
        condition=condition,
        threshold=alert_data.threshold,
        symbol=alert_data.symbol,
        message=alert_data.message,
        telegram_notify=alert_data.telegram_notify,
        email_notify=alert_data.email_notify,
        expires_at=expires_at
    )
    
    return {
        "success": True,
        "alert": alert.to_dict(),
        "message": "Alert created successfully"
    }

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Delete an alert
    """
    success = alert_manager.delete_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "message": "Alert deleted successfully"
    }

@router.put("/{alert_id}")
async def update_alert(
    alert_id: str,
    update_data: AlertUpdate,
    current_user: dict = Depends(require_auth)
):
    """
    Update an alert
    """
    if alert_id not in alert_manager.alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert = alert_manager.alerts[alert_id]
    
    # Verify ownership
    if alert.user != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    if update_data.status:
        try:
            alert.status = AlertStatus(update_data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if update_data.threshold is not None:
        alert.threshold = update_data.threshold
    
    if update_data.message is not None:
        alert.message = update_data.message
    
    alert_manager.save_alerts()
    
    return {
        "success": True,
        "alert": alert.to_dict(),
        "message": "Alert updated successfully"
    }

@router.get("/templates")
async def get_alert_templates(current_user: dict = Depends(require_auth)):
    """
    Get predefined alert templates
    """
    return {
        "success": True,
        "templates": ALERT_TEMPLATES
    }

@router.post("/templates/{template_id}")
async def create_from_template(
    template_id: str,
    current_user: dict = Depends(require_auth)
):
    """
    Create alert from template
    """
    if template_id not in ALERT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = ALERT_TEMPLATES[template_id]
    
    alert = alert_manager.create_alert(
        user=current_user["username"],
        alert_type=template["alert_type"],
        condition=template["condition"],
        threshold=template["threshold"],
        symbol=template.get("symbol"),
        message=f"Created from template: {template['name']}"
    )
    
    return {
        "success": True,
        "alert": alert.to_dict(),
        "message": f"Alert created from template: {template['name']}"
    }

@router.get("/stats")
async def get_alert_stats(current_user: dict = Depends(require_auth)):
    """
    Get alert statistics for current user
    """
    all_alerts = alert_manager.get_alerts(user=current_user["username"])
    
    stats = {
        "total": len(all_alerts),
        "active": len([a for a in all_alerts if a.status == AlertStatus.ACTIVE]),
        "triggered": len([a for a in all_alerts if a.status == AlertStatus.TRIGGERED]),
        "disabled": len([a for a in all_alerts if a.status == AlertStatus.DISABLED]),
        "expired": len([a for a in all_alerts if a.status == AlertStatus.EXPIRED]),
        "by_type": {}
    }
    
    # Count by type
    for alert_type in AlertType:
        count = len([a for a in all_alerts if a.alert_type == alert_type])
        if count > 0:
            stats["by_type"][alert_type.value] = count
    
    return {
        "success": True,
        "stats": stats
    }

@router.post("/test")
async def test_notification(
    notification_type: str = "telegram",
    current_user: dict = Depends(require_auth)
):
    """
    Test notification system
    """
    import os
    
    message = f"""
🧪 <b>Test Notification</b>

This is a test notification from SmartOrder PRO.

<b>User:</b> {current_user["username"]}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this, your notification system is working! ✅
    """
    
    if notification_type == "telegram":
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id:
            raise HTTPException(status_code=400, detail="Telegram chat ID not configured")
        
        success = await alert_manager.send_telegram_notification(chat_id, message)
        
        return {
            "success": success,
            "message": "Telegram test sent" if success else "Telegram test failed"
        }
    
    elif notification_type == "email":
        user_email = os.getenv("USER_EMAIL")
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not configured")
        
        success = alert_manager.send_email_notification(
            user_email,
            "SmartOrder PRO - Test Notification",
            message.replace('<b>', '<strong>').replace('</b>', '</strong>')
        )
        
        return {
            "success": success,
            "message": "Email test sent" if success else "Email test failed"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid notification type")
