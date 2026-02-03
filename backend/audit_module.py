"""
HIPAA Audit Logging Module for Yacco EMR
Tracks all access to PHI (Protected Health Information)
"""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

audit_router = APIRouter(prefix="/api/audit", tags=["HIPAA Audit"])

class AuditAction(str, Enum):
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    PRINT = "print"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"

class AuditResourceType(str, Enum):
    PATIENT = "patient"
    CLINICAL_NOTE = "clinical_note"
    VITALS = "vitals"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    PROBLEM = "problem"
    ORDER = "order"
    APPOINTMENT = "appointment"
    USER = "user"
    REPORT = "report"

class AuditLogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str
    user_name: str
    user_role: str
    action: AuditAction
    resource_type: AuditResourceType
    resource_id: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    success: bool = True

class AuditLogResponse(BaseModel):
    id: str
    timestamp: str
    user_id: str
    user_name: str
    user_role: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    patient_id: Optional[str]
    patient_name: Optional[str]
    ip_address: Optional[str]
    details: Optional[str]
    success: bool

def create_audit_endpoints(db, get_current_user):
    """Create audit log endpoints with database access"""
    
    async def log_audit_event(
        user: dict,
        action: AuditAction,
        resource_type: AuditResourceType,
        resource_id: str = None,
        patient_id: str = None,
        patient_name: str = None,
        details: str = None,
        ip_address: str = None,
        user_agent: str = None,
        success: bool = True
    ):
        """Log an audit event to the database"""
        entry = AuditLogEntry(
            user_id=user.get("id", "system"),
            user_name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "System",
            user_role=user.get("role", "system"),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            patient_name=patient_name,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success
        )
        entry_dict = entry.model_dump()
        entry_dict["timestamp"] = entry_dict["timestamp"].isoformat()
        await db.audit_logs.insert_one(entry_dict)
        return entry
    
    @audit_router.get("/logs", response_model=List[AuditLogResponse])
    async def get_audit_logs(
        user_id: Optional[str] = Query(None),
        patient_id: Optional[str] = Query(None),
        action: Optional[str] = Query(None),
        resource_type: Optional[str] = Query(None),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None),
        limit: int = Query(100, le=1000),
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit logs (Admin only)"""
        if current_user["role"] not in ["admin"]:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        if patient_id:
            query["patient_id"] = patient_id
        if action:
            query["action"] = action
        if resource_type:
            query["resource_type"] = resource_type
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        
        logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
        return [AuditLogResponse(**log) for log in logs]
    
    @audit_router.get("/logs/patient/{patient_id}", response_model=List[AuditLogResponse])
    async def get_patient_audit_logs(
        patient_id: str,
        limit: int = Query(100, le=1000),
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit logs for a specific patient"""
        logs = await db.audit_logs.find(
            {"patient_id": patient_id}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return [AuditLogResponse(**log) for log in logs]
    
    @audit_router.get("/stats")
    async def get_audit_stats(current_user: dict = Depends(get_current_user)):
        """Get audit log statistics"""
        if current_user["role"] not in ["admin"]:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin access required")
        
        total_logs = await db.audit_logs.count_documents({})
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_logs = await db.audit_logs.count_documents({"timestamp": {"$regex": f"^{today}"}})
        
        # Get action breakdown
        pipeline = [
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        action_stats = await db.audit_logs.aggregate(pipeline).to_list(20)
        
        # Get failed logins
        failed_logins = await db.audit_logs.count_documents({"action": "failed_login"})
        
        return {
            "total_logs": total_logs,
            "today_logs": today_logs,
            "failed_logins": failed_logins,
            "action_breakdown": {item["_id"]: item["count"] for item in action_stats}
        }
    
    return audit_router, log_audit_event
