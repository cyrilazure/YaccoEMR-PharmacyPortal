"""
Notifications Module for Yacco EMR
Real-time notifications for prescription updates, system alerts, and user messages
REFACTORED to use db_service_v2 for database abstraction.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from enum import Enum

from db_service_v2 import get_db_service

notifications_router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ============== Enums ==============

class NotificationType(str, Enum):
    PRESCRIPTION_SENT = "prescription_sent"
    PRESCRIPTION_ACCEPTED = "prescription_accepted"
    PRESCRIPTION_REJECTED = "prescription_rejected"
    PRESCRIPTION_FILLED = "prescription_filled"
    PRESCRIPTION_READY = "prescription_ready"
    LAB_RESULTS = "lab_results"
    IMAGING_RESULTS = "imaging_results"
    APPOINTMENT_REMINDER = "appointment_reminder"
    AMBULANCE_DISPATCHED = "ambulance_dispatched"
    AMBULANCE_ARRIVED = "ambulance_arrived"
    NHIS_CLAIM_APPROVED = "nhis_claim_approved"
    NHIS_CLAIM_REJECTED = "nhis_claim_rejected"
    SYSTEM_ALERT = "system_alert"
    LOW_STOCK = "low_stock"
    EXPIRING_DRUGS = "expiring_drugs"
    MESSAGE = "message"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============== Pydantic Models ==============

class NotificationCreate(BaseModel):
    recipient_id: str
    recipient_role: Optional[str] = None
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    related_resource_type: Optional[str] = None  # prescription, patient, claim, etc.
    related_resource_id: Optional[str] = None
    action_url: Optional[str] = None  # URL to navigate to
    metadata: Optional[dict] = None


class NotificationBroadcast(BaseModel):
    organization_id: Optional[str] = None
    roles: Optional[List[str]] = None  # Send to specific roles
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM_ALERT
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Optional[dict] = None


def create_notification_endpoints(db, get_current_user):
    """Create notification API endpoints"""
    
    @notifications_router.get("")
    async def get_notifications(
        unread_only: bool = Query(False, description="Show only unread notifications"),
        notification_type: Optional[str] = None,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        user: dict = Depends(get_current_user)
    ):
        """Get user's notifications"""
        db_svc = get_db_service()
        
        query = {"recipient_id": user.get("id")}
        
        if unread_only:
            query["read"] = False
        if notification_type:
            query["notification_type"] = notification_type
        
        notifications = await db_svc.find(
            "notifications",
            query,
            sort=[("created_at", -1)],
            skip=offset,
            limit=limit
        )
        
        # Get unread count
        unread_count = await db_svc.count(
            "notifications",
            {"recipient_id": user.get("id"), "read": False}
        )
        
        return {
            "notifications": notifications,
            "total": len(notifications),
            "unread_count": unread_count
        }
    
    @notifications_router.get("/unread-count")
    async def get_unread_count(user: dict = Depends(get_current_user)):
        """Get count of unread notifications"""
        db_svc = get_db_service()
        count = await db_svc.count(
            "notifications",
            {"recipient_id": user.get("id"), "read": False}
        )
        return {"unread_count": count}
    
    @notifications_router.post("")
    async def create_notification(
        data: NotificationCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a notification for a user"""
        db_svc = get_db_service()
        notification_id = str(uuid.uuid4())
        
        notification_doc = {
            "id": notification_id,
            "recipient_id": data.recipient_id,
            "recipient_role": data.recipient_role,
            "sender_id": user.get("id"),
            "sender_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "title": data.title,
            "message": data.message,
            "notification_type": data.notification_type.value if hasattr(data.notification_type, "value") else data.notification_type,
            "priority": data.priority.value if hasattr(data.priority, "value") else data.priority,
            "related_resource_type": data.related_resource_type,
            "related_resource_id": data.related_resource_id,
            "action_url": data.action_url,
            "metadata": data.metadata,
            "read": False,
            "read_at": None,
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db_svc.insert("notifications", notification_doc, generate_id=False)
        
        return {"message": "Notification created", "notification": notification_doc}
    
    @notifications_router.post("/broadcast")
    async def broadcast_notification(
        data: NotificationBroadcast,
        user: dict = Depends(get_current_user)
    ):
        """Broadcast notification to multiple users"""
        db_svc = get_db_service()
        
        allowed_roles = ["hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Find recipients
        query = {}
        if data.organization_id:
            query["organization_id"] = data.organization_id
        elif user.get("organization_id"):
            query["organization_id"] = user.get("organization_id")
        
        if data.roles:
            query["role"] = {"$in": data.roles}
        
        recipients = await db_svc.find(
            "users",
            query,
            projection={"id": 1, "role": 1},
            limit=1000
        )
        
        # Create notifications for all recipients
        notifications = []
        for recipient in recipients:
            notification_id = str(uuid.uuid4())
            notification_doc = {
                "id": notification_id,
                "recipient_id": recipient.get("id"),
                "recipient_role": recipient.get("role"),
                "sender_id": user.get("id"),
                "sender_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "title": data.title,
                "message": data.message,
                "notification_type": data.notification_type.value if hasattr(data.notification_type, "value") else data.notification_type,
                "priority": data.priority.value if hasattr(data.priority, "value") else data.priority,
                "metadata": data.metadata,
                "read": False,
                "read_at": None,
                "organization_id": user.get("organization_id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            notifications.append(notification_doc)
        
        if notifications:
            await db_svc.insert_many("notifications", notifications, generate_ids=False)
        
        return {"message": f"Notification sent to {len(notifications)} recipients"}
    
    @notifications_router.put("/{notification_id}/read")
    async def mark_as_read(
        notification_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Mark notification as read"""
        db_svc = get_db_service()
        
        result = await db_svc.update(
            "notifications",
            {"id": notification_id, "recipient_id": user.get("id")},
            {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Marked as read"}
    
    @notifications_router.put("/mark-all-read")
    async def mark_all_as_read(user: dict = Depends(get_current_user)):
        """Mark all notifications as read"""
        db_svc = get_db_service()
        
        await db_svc.update_many(
            "notifications",
            {"recipient_id": user.get("id"), "read": False},
            {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}
        )
        
        return {"message": "All notifications marked as read"}
    
    @notifications_router.delete("/{notification_id}")
    async def delete_notification(
        notification_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Delete a notification"""
        db_svc = get_db_service()
        
        result = await db_svc.delete(
            "notifications",
            {"id": notification_id, "recipient_id": user.get("id")}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted"}
    
    @notifications_router.delete("/clear-all")
    async def clear_all_notifications(user: dict = Depends(get_current_user)):
        """Clear all notifications for user"""
        db_svc = get_db_service()
        
        count = await db_svc.delete_many(
            "notifications",
            {"recipient_id": user.get("id")}
        )
        return {"message": f"Cleared {count} notifications"}
    
    # ============== Helper function for internal use ==============
    
    async def send_notification(
        recipient_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        related_resource_type: str = None,
        related_resource_id: str = None,
        action_url: str = None,
        metadata: dict = None,
        organization_id: str = None
    ):
        """Internal helper to send notifications from other modules"""
        db_svc = get_db_service()
        notification_id = str(uuid.uuid4())
        
        notification_doc = {
            "id": notification_id,
            "recipient_id": recipient_id,
            "title": title,
            "message": message,
            "notification_type": notification_type.value if hasattr(notification_type, "value") else notification_type,
            "priority": priority.value if hasattr(priority, "value") else priority,
            "related_resource_type": related_resource_type,
            "related_resource_id": related_resource_id,
            "action_url": action_url,
            "metadata": metadata,
            "read": False,
            "read_at": None,
            "organization_id": organization_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db_svc.insert("notifications", notification_doc, generate_id=False)
        return notification_id
    
    # Store the helper function for external access
    notifications_router.send_notification = send_notification
    
    return notifications_router


# Export for use in other modules
__all__ = ["notifications_router", "create_notification_endpoints", "NotificationType", "NotificationPriority"]
