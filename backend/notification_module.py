"""
Comprehensive Notification System for Yacco EMR
HIPAA-Compliant Multi-Channel Notification Management

Features:
- In-app notifications with real-time updates
- Email notifications (optional, configurable)
- Alert types:
  - Record access requests (incoming/outgoing)
  - Approvals and denials
  - Expiring access warnings
  - Emergency access usage alerts
  - Consent expirations
  - Security alerts
- Notification lifecycle management
- Read/unread tracking
- Notification preferences
- Batch operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import os

notification_router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ============================================================================
# ENUMERATIONS
# ============================================================================

class NotificationType(str, Enum):
    """Types of notifications in the system"""
    # Records Sharing
    RECORDS_REQUEST_RECEIVED = "records_request_received"
    RECORDS_REQUEST_SENT = "records_request_sent"
    RECORDS_REQUEST_APPROVED = "records_request_approved"
    RECORDS_REQUEST_REJECTED = "records_request_rejected"
    RECORDS_ACCESS_GRANTED = "records_access_granted"
    RECORDS_ACCESS_EXPIRING = "records_access_expiring"
    RECORDS_ACCESS_EXPIRED = "records_access_expired"
    RECORDS_ACCESS_REVOKED = "records_access_revoked"
    
    # Emergency Access
    EMERGENCY_ACCESS_USED = "emergency_access_used"
    EMERGENCY_ACCESS_REQUESTED = "emergency_access_requested"
    
    # Consent
    CONSENT_REQUIRED = "consent_required"
    CONSENT_EXPIRING = "consent_expiring"
    CONSENT_EXPIRED = "consent_expired"
    CONSENT_REVOKED = "consent_revoked"
    
    # Security
    SECURITY_LOGIN_NEW_DEVICE = "security_login_new_device"
    SECURITY_PASSWORD_CHANGED = "security_password_changed"
    SECURITY_2FA_ENABLED = "security_2fa_enabled"
    SECURITY_2FA_DISABLED = "security_2fa_disabled"
    SECURITY_FAILED_LOGINS = "security_failed_logins"
    SECURITY_ACCOUNT_LOCKED = "security_account_locked"
    
    # Clinical
    LAB_RESULT_AVAILABLE = "lab_result_available"
    IMAGING_RESULT_AVAILABLE = "imaging_result_available"
    PRESCRIPTION_READY = "prescription_ready"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    
    # Administrative
    USER_INVITED = "user_invited"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"
    
    # General
    GENERAL_INFO = "general_info"
    GENERAL_WARNING = "general_warning"
    GENERAL_ALERT = "general_alert"


class NotificationPriority(str, Enum):
    """Priority levels for notifications"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Delivery channels for notifications"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Status of a notification"""
    PENDING = "pending"       # Created, not yet delivered
    DELIVERED = "delivered"   # Delivered to channel
    READ = "read"            # User has read it
    DISMISSED = "dismissed"  # User dismissed without reading
    EXPIRED = "expired"      # TTL expired
    FAILED = "failed"        # Delivery failed


# ============================================================================
# MODELS
# ============================================================================

class NotificationCreate(BaseModel):
    """Create a new notification"""
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Related entity
    related_type: Optional[str] = None  # request, consent, patient, etc.
    related_id: Optional[str] = None
    
    # Action
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    
    # Channels
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    
    # Expiration
    expires_in_hours: Optional[int] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Notification response model"""
    id: str
    user_id: str
    notification_type: str
    title: str
    message: str
    priority: str
    status: str
    
    related_type: Optional[str] = None
    related_id: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    
    is_read: bool = False
    read_at: Optional[str] = None
    is_dismissed: bool = False
    dismissed_at: Optional[str] = None
    
    created_at: str
    expires_at: Optional[str] = None
    
    # Delivery status
    in_app_delivered: bool = False
    email_sent: bool = False
    email_sent_at: Optional[str] = None


class NotificationPreferences(BaseModel):
    """User notification preferences"""
    # By type
    records_sharing: bool = True
    security_alerts: bool = True
    clinical_updates: bool = True
    administrative: bool = True
    
    # By channel
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    
    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    
    # Digest
    email_digest: bool = False
    digest_frequency: str = "daily"  # daily, weekly


class BulkNotificationCreate(BaseModel):
    """Create notifications for multiple users"""
    user_ids: List[str]
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]


# ============================================================================
# NOTIFICATION TEMPLATES
# ============================================================================

NOTIFICATION_TEMPLATES = {
    NotificationType.RECORDS_REQUEST_RECEIVED: {
        "title": "New Records Request",
        "message_template": "Dr. {requester_name} from {requester_org} is requesting access to patient {patient_name}'s medical records.",
        "priority": NotificationPriority.HIGH,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.RECORDS_REQUEST_APPROVED: {
        "title": "Records Request Approved",
        "message_template": "Your request for {patient_name}'s records has been approved by Dr. {approver_name}. Access expires on {expiry_date}.",
        "priority": NotificationPriority.NORMAL,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.RECORDS_REQUEST_REJECTED: {
        "title": "Records Request Denied",
        "message_template": "Your request for {patient_name}'s records has been denied by Dr. {denier_name}. Reason: {reason}",
        "priority": NotificationPriority.NORMAL,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.RECORDS_ACCESS_EXPIRING: {
        "title": "Records Access Expiring Soon",
        "message_template": "Your access to {patient_name}'s records will expire in {days_remaining} days on {expiry_date}.",
        "priority": NotificationPriority.HIGH,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.RECORDS_ACCESS_EXPIRED: {
        "title": "Records Access Expired",
        "message_template": "Your access to {patient_name}'s records has expired. Submit a new request if continued access is needed.",
        "priority": NotificationPriority.NORMAL,
        "channels": [NotificationChannel.IN_APP]
    },
    NotificationType.RECORDS_ACCESS_REVOKED: {
        "title": "Records Access Revoked",
        "message_template": "Your access to {patient_name}'s records has been revoked by Dr. {revoker_name}. Reason: {reason}",
        "priority": NotificationPriority.HIGH,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.EMERGENCY_ACCESS_USED: {
        "title": "⚠️ Emergency Access Alert",
        "message_template": "Dr. {accessor_name} has used emergency access to view {patient_name}'s records. Reason: {reason}",
        "priority": NotificationPriority.CRITICAL,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.CONSENT_EXPIRING: {
        "title": "Patient Consent Expiring",
        "message_template": "{consent_type} consent for {patient_name} will expire in {days_remaining} days.",
        "priority": NotificationPriority.HIGH,
        "channels": [NotificationChannel.IN_APP]
    },
    NotificationType.SECURITY_FAILED_LOGINS: {
        "title": "Security Alert: Failed Login Attempts",
        "message_template": "Multiple failed login attempts detected for your account from IP {ip_address}.",
        "priority": NotificationPriority.URGENT,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    },
    NotificationType.SECURITY_ACCOUNT_LOCKED: {
        "title": "Account Locked",
        "message_template": "Your account has been locked due to multiple failed login attempts. It will unlock at {unlock_time}.",
        "priority": NotificationPriority.URGENT,
        "channels": [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    }
}


# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

def generate_email_html(notification: dict) -> str:
    """Generate HTML email content for a notification"""
    priority_colors = {
        "low": "#6b7280",
        "normal": "#3b82f6",
        "high": "#f59e0b",
        "urgent": "#ef4444",
        "critical": "#dc2626"
    }
    
    color = priority_colors.get(notification.get("priority", "normal"), "#3b82f6")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
            .footer {{ background: #f3f4f6; padding: 15px; text-align: center; font-size: 12px; color: #6b7280; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
            .priority {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; text-transform: uppercase; background: {color}20; color: {color}; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="margin: 0;">{notification.get('title', 'Notification')}</h2>
                <span class="priority">{notification.get('priority', 'normal')}</span>
            </div>
            <div class="content">
                <p>{notification.get('message', '')}</p>
                {f'<a href="{notification.get("action_url")}" class="button">{notification.get("action_label", "View Details")}</a>' if notification.get('action_url') else ''}
            </div>
            <div class="footer">
                <p>This is an automated notification from Yacco EMR.</p>
                <p>Please do not reply to this email.</p>
                <p>&copy; {datetime.now().year} Yacco EMR - HIPAA Compliant Healthcare Platform</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


# ============================================================================
# NOTIFICATION SERVICE
# ============================================================================

def create_notification_endpoints(db, get_current_user):
    """Create notification system endpoints"""
    
    # ============ HELPER FUNCTIONS ============
    
    async def create_notification(
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        related_type: str = None,
        related_id: str = None,
        action_url: str = None,
        action_label: str = None,
        channels: List[NotificationChannel] = None,
        expires_in_hours: int = None,
        metadata: dict = None,
        send_email: bool = False
    ) -> dict:
        """Create and store a notification"""
        if channels is None:
            channels = [NotificationChannel.IN_APP]
        
        now = datetime.now(timezone.utc)
        expires_at = None
        if expires_in_hours:
            expires_at = (now + timedelta(hours=expires_in_hours)).isoformat()
        
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "notification_type": notification_type.value if isinstance(notification_type, NotificationType) else notification_type,
            "title": title,
            "message": message,
            "priority": priority.value if isinstance(priority, NotificationPriority) else priority,
            "status": NotificationStatus.DELIVERED.value,
            
            "related_type": related_type,
            "related_id": related_id,
            "action_url": action_url,
            "action_label": action_label,
            
            "channels": [c.value if isinstance(c, NotificationChannel) else c for c in channels],
            
            "is_read": False,
            "read_at": None,
            "is_dismissed": False,
            "dismissed_at": None,
            
            "created_at": now.isoformat(),
            "expires_at": expires_at,
            
            "in_app_delivered": NotificationChannel.IN_APP in channels or NotificationChannel.IN_APP.value in channels,
            "email_sent": False,
            "email_sent_at": None,
            "sms_sent": False,
            "push_sent": False,
            
            "metadata": metadata
        }
        
        await db.notifications.insert_one(notification)
        
        # Log notification creation for audit
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "user_id": "system",
            "user_name": "System",
            "user_role": "system",
            "action": "notification_created",
            "resource_type": "notification",
            "resource_id": notification["id"],
            "details": f"Notification created for user {user_id}: {title}",
            "success": True,
            "severity": "info"
        })
        
        return notification
    
    async def create_notification_from_template(
        user_id: str,
        notification_type: NotificationType,
        template_vars: dict,
        related_type: str = None,
        related_id: str = None,
        action_url: str = None,
        action_label: str = None
    ) -> dict:
        """Create notification using a predefined template"""
        template = NOTIFICATION_TEMPLATES.get(notification_type, {})
        
        title = template.get("title", "Notification")
        message_template = template.get("message_template", "")
        priority = template.get("priority", NotificationPriority.NORMAL)
        channels = template.get("channels", [NotificationChannel.IN_APP])
        
        # Fill in template variables
        try:
            message = message_template.format(**template_vars)
        except KeyError:
            message = message_template
        
        return await create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            related_type=related_type,
            related_id=related_id,
            action_url=action_url,
            action_label=action_label,
            channels=channels
        )
    
    async def send_bulk_notification(
        user_ids: List[str],
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> int:
        """Send notification to multiple users"""
        count = 0
        for user_id in user_ids:
            await create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority
            )
            count += 1
        return count
    
    async def check_expiring_access():
        """Check for expiring access grants and send notifications"""
        now = datetime.now(timezone.utc)
        warning_periods = [7, 3, 1]  # Days before expiration to warn
        
        notifications_sent = 0
        
        for days in warning_periods:
            target_date = now + timedelta(days=days)
            
            # Find access grants expiring on this date
            expiring_grants = await db.access_grants.find({
                "active": True,
                "expires_at": {
                    "$gte": target_date.replace(hour=0, minute=0, second=0).isoformat(),
                    "$lt": (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
                },
                f"warned_{days}d": {"$ne": True}
            }).to_list(100)
            
            for grant in expiring_grants:
                # Get patient info
                patient = await db.patients.find_one({"id": grant.get("patient_id")})
                patient_name = f"{patient['first_name']} {patient['last_name']}" if patient else "Unknown"
                
                await create_notification_from_template(
                    user_id=grant["granted_physician_id"],
                    notification_type=NotificationType.RECORDS_ACCESS_EXPIRING,
                    template_vars={
                        "patient_name": patient_name,
                        "days_remaining": days,
                        "expiry_date": grant.get("expires_at", "")[:10]
                    },
                    related_type="access_grant",
                    related_id=grant["id"],
                    action_url=f"/records-sharing",
                    action_label="View Access Details"
                )
                
                # Mark as warned
                await db.access_grants.update_one(
                    {"id": grant["id"]},
                    {"$set": {f"warned_{days}d": True}}
                )
                
                notifications_sent += 1
        
        return notifications_sent
    
    async def check_expiring_consents():
        """Check for expiring consents and send notifications"""
        now = datetime.now(timezone.utc)
        warning_periods = [30, 14, 7]  # Days before expiration
        
        notifications_sent = 0
        
        for days in warning_periods:
            target_date = now + timedelta(days=days)
            
            expiring_consents = await db.consent_forms.find({
                "status": "active",
                "expiration_date": {
                    "$gte": target_date.replace(hour=0, minute=0, second=0).isoformat(),
                    "$lt": (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
                },
                f"warned_{days}d": {"$ne": True}
            }).to_list(100)
            
            for consent in expiring_consents:
                patient = await db.patients.find_one({"id": consent.get("patient_id")})
                patient_name = f"{patient['first_name']} {patient['last_name']}" if patient else "Unknown"
                
                # Notify the user who created the consent
                await create_notification(
                    user_id=consent.get("created_by"),
                    notification_type=NotificationType.CONSENT_EXPIRING,
                    title="Patient Consent Expiring",
                    message=f"{consent.get('consent_type', 'Consent').replace('_', ' ').title()} for {patient_name} will expire in {days} days.",
                    priority=NotificationPriority.HIGH,
                    related_type="consent",
                    related_id=consent["id"]
                )
                
                await db.consent_forms.update_one(
                    {"id": consent["id"]},
                    {"$set": {f"warned_{days}d": True}}
                )
                
                notifications_sent += 1
        
        return notifications_sent
    
    # ============ API ENDPOINTS ============
    
    @notification_router.get("/types")
    async def get_notification_types():
        """Get all available notification types"""
        return [
            {"value": nt.value, "name": nt.name.replace("_", " ").title()}
            for nt in NotificationType
        ]
    
    @notification_router.get("/priorities")
    async def get_notification_priorities():
        """Get all priority levels"""
        return [
            {"value": p.value, "name": p.name.title()}
            for p in NotificationPriority
        ]
    
    @notification_router.get("")
    async def get_notifications(
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        current_user: dict = Depends(get_current_user)
    ):
        """Get notifications for the current user"""
        query = {"user_id": current_user["id"]}
        
        if unread_only:
            query["is_read"] = False
        if notification_type:
            query["notification_type"] = notification_type
        if priority:
            query["priority"] = priority
        
        # Exclude expired
        now = datetime.now(timezone.utc).isoformat()
        query["$or"] = [
            {"expires_at": None},
            {"expires_at": {"$gt": now}}
        ]
        
        notifications = await db.notifications.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await db.notifications.count_documents(query)
        unread_count = await db.notifications.count_documents({
            "user_id": current_user["id"],
            "is_read": False,
            "$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}]
        })
        
        return {
            "notifications": [NotificationResponse(**n) for n in notifications],
            "total": total,
            "unread_count": unread_count,
            "limit": limit,
            "skip": skip
        }
    
    @notification_router.get("/unread-count")
    async def get_unread_count(
        current_user: dict = Depends(get_current_user)
    ):
        """Get count of unread notifications"""
        now = datetime.now(timezone.utc).isoformat()
        count = await db.notifications.count_documents({
            "user_id": current_user["id"],
            "is_read": False,
            "$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}]
        })
        
        # Count by priority
        priority_counts = {}
        for p in NotificationPriority:
            p_count = await db.notifications.count_documents({
                "user_id": current_user["id"],
                "is_read": False,
                "priority": p.value,
                "$or": [{"expires_at": None}, {"expires_at": {"$gt": now}}]
            })
            if p_count > 0:
                priority_counts[p.value] = p_count
        
        return {
            "unread_count": count,
            "by_priority": priority_counts
        }
    
    @notification_router.get("/{notification_id}")
    async def get_notification(
        notification_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get a specific notification"""
        notification = await db.notifications.find_one({
            "id": notification_id,
            "user_id": current_user["id"]
        }, {"_id": 0})
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return NotificationResponse(**notification)
    
    @notification_router.put("/{notification_id}/read")
    async def mark_as_read(
        notification_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Mark a notification as read"""
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": current_user["id"]},
            {"$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc).isoformat(),
                "status": NotificationStatus.READ.value
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    
    @notification_router.put("/{notification_id}/unread")
    async def mark_as_unread(
        notification_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Mark a notification as unread"""
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": current_user["id"]},
            {"$set": {
                "is_read": False,
                "read_at": None,
                "status": NotificationStatus.DELIVERED.value
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as unread"}
    
    @notification_router.put("/{notification_id}/dismiss")
    async def dismiss_notification(
        notification_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Dismiss a notification"""
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": current_user["id"]},
            {"$set": {
                "is_dismissed": True,
                "dismissed_at": datetime.now(timezone.utc).isoformat(),
                "status": NotificationStatus.DISMISSED.value
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification dismissed"}
    
    @notification_router.put("/read-all")
    async def mark_all_as_read(
        current_user: dict = Depends(get_current_user)
    ):
        """Mark all notifications as read"""
        result = await db.notifications.update_many(
            {"user_id": current_user["id"], "is_read": False},
            {"$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc).isoformat(),
                "status": NotificationStatus.READ.value
            }}
        )
        
        return {"message": f"Marked {result.modified_count} notifications as read"}
    
    @notification_router.delete("/{notification_id}")
    async def delete_notification(
        notification_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Delete a notification"""
        result = await db.notifications.delete_one({
            "id": notification_id,
            "user_id": current_user["id"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted"}
    
    @notification_router.delete("/clear-all")
    async def clear_all_notifications(
        read_only: bool = True,
        current_user: dict = Depends(get_current_user)
    ):
        """Clear all notifications (optionally only read ones)"""
        query = {"user_id": current_user["id"]}
        if read_only:
            query["is_read"] = True
        
        result = await db.notifications.delete_many(query)
        
        return {"message": f"Deleted {result.deleted_count} notifications"}
    
    # ============ NOTIFICATION PREFERENCES ============
    
    @notification_router.get("/preferences/me")
    async def get_my_preferences(
        current_user: dict = Depends(get_current_user)
    ):
        """Get current user's notification preferences"""
        prefs = await db.notification_preferences.find_one(
            {"user_id": current_user["id"]},
            {"_id": 0}
        )
        
        if not prefs:
            # Return defaults
            return NotificationPreferences().model_dump()
        
        return prefs
    
    @notification_router.put("/preferences/me")
    async def update_my_preferences(
        preferences: NotificationPreferences,
        current_user: dict = Depends(get_current_user)
    ):
        """Update current user's notification preferences"""
        prefs_dict = preferences.model_dump()
        prefs_dict["user_id"] = current_user["id"]
        prefs_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.notification_preferences.update_one(
            {"user_id": current_user["id"]},
            {"$set": prefs_dict},
            upsert=True
        )
        
        return {"message": "Preferences updated", "preferences": prefs_dict}
    
    # ============ ADMIN ENDPOINTS ============
    
    @notification_router.post("/send")
    async def send_notification(
        notification: NotificationCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Send a notification to a user (Admin only)"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        created = await create_notification(
            user_id=notification.user_id,
            notification_type=notification.notification_type,
            title=notification.title,
            message=notification.message,
            priority=notification.priority,
            related_type=notification.related_type,
            related_id=notification.related_id,
            action_url=notification.action_url,
            action_label=notification.action_label,
            channels=notification.channels,
            expires_in_hours=notification.expires_in_hours,
            metadata=notification.metadata
        )
        
        return {"message": "Notification sent", "notification_id": created["id"]}
    
    @notification_router.post("/send-bulk")
    async def send_bulk_notifications(
        bulk: BulkNotificationCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Send notification to multiple users (Admin only)"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        count = await send_bulk_notification(
            user_ids=bulk.user_ids,
            notification_type=bulk.notification_type,
            title=bulk.title,
            message=bulk.message,
            priority=bulk.priority
        )
        
        return {"message": f"Sent {count} notifications"}
    
    @notification_router.post("/check-expirations")
    async def run_expiration_checks(
        current_user: dict = Depends(get_current_user)
    ):
        """Run expiration checks and send notifications (Admin only)"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        access_notifications = await check_expiring_access()
        consent_notifications = await check_expiring_consents()
        
        return {
            "message": "Expiration checks complete",
            "access_expiring_notifications": access_notifications,
            "consent_expiring_notifications": consent_notifications
        }
    
    # ============ STATISTICS ============
    
    @notification_router.get("/stats/overview")
    async def get_notification_stats(
        days: int = 30,
        current_user: dict = Depends(get_current_user)
    ):
        """Get notification statistics"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = current_user.get("organization_id")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get user IDs for this org
        org_filter = {}
        if org_id and current_user.get("role") != "super_admin":
            users = await db.users.find({"organization_id": org_id}, {"id": 1}).to_list(1000)
            user_ids = [u["id"] for u in users]
            org_filter = {"user_id": {"$in": user_ids}}
        
        # Total notifications
        total = await db.notifications.count_documents({
            **org_filter,
            "created_at": {"$gte": start_date}
        })
        
        # By type
        type_pipeline = [
            {"$match": {**org_filter, "created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$notification_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_type = await db.notifications.aggregate(type_pipeline).to_list(50)
        
        # By priority
        priority_pipeline = [
            {"$match": {**org_filter, "created_at": {"$gte": start_date}}},
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]
        by_priority = await db.notifications.aggregate(priority_pipeline).to_list(10)
        
        # Read rate
        read_count = await db.notifications.count_documents({
            **org_filter,
            "created_at": {"$gte": start_date},
            "is_read": True
        })
        
        read_rate = round((read_count / total * 100) if total > 0 else 0, 1)
        
        return {
            "period_days": days,
            "total_notifications": total,
            "read_count": read_count,
            "unread_count": total - read_count,
            "read_rate_percent": read_rate,
            "by_type": {item["_id"]: item["count"] for item in by_type},
            "by_priority": {item["_id"]: item["count"] for item in by_priority}
        }
    
    # ============ EMERGENCY ACCESS ALERTS ============
    
    @notification_router.post("/emergency-access-alert")
    async def create_emergency_access_alert(
        patient_id: str,
        reason: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Create emergency access notification (called when break-the-glass is used)"""
        # Get patient info
        patient = await db.patients.find_one({"id": patient_id})
        patient_name = f"{patient['first_name']} {patient['last_name']}" if patient else "Unknown"
        
        # Get all admins in the organization
        admins = await db.users.find({
            "organization_id": current_user.get("organization_id"),
            "role": {"$in": ["admin", "hospital_admin"]},
            "is_active": True
        }).to_list(50)
        
        accessor_name = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        
        # Notify all admins
        for admin in admins:
            await create_notification_from_template(
                user_id=admin["id"],
                notification_type=NotificationType.EMERGENCY_ACCESS_USED,
                template_vars={
                    "accessor_name": accessor_name,
                    "patient_name": patient_name,
                    "reason": reason
                },
                related_type="emergency_access",
                related_id=patient_id,
                action_url=f"/audit-logs?patient_id={patient_id}",
                action_label="View Audit Trail"
            )
        
        # Also log to audit
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.get("id"),
            "user_name": accessor_name,
            "user_role": current_user.get("role"),
            "organization_id": current_user.get("organization_id"),
            "action": "emergency_access",
            "resource_type": "patient",
            "resource_id": patient_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "details": f"Emergency access used. Reason: {reason}",
            "success": True,
            "severity": "critical",
            "phi_accessed": True
        })
        
        return {
            "message": "Emergency access alert sent to administrators",
            "admins_notified": len(admins)
        }
    
    return notification_router, create_notification, create_notification_from_template


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'notification_router',
    'create_notification_endpoints',
    'NotificationType',
    'NotificationPriority',
    'NotificationChannel',
    'NotificationStatus',
    'NotificationCreate',
    'NotificationResponse',
    'NotificationPreferences',
    'NOTIFICATION_TEMPLATES'
]
