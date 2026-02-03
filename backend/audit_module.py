"""
HIPAA Audit Logging Module for Yacco EMR
Tracks all access to PHI (Protected Health Information)
Enhanced with comprehensive reporting and analytics
"""

from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import csv
import io
import json

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
    PERMISSION_DENIED = "permission_denied"
    TWO_FACTOR_SETUP = "2fa_setup"
    TWO_FACTOR_VERIFY = "2fa_verify"
    TWO_FACTOR_DISABLE = "2fa_disable"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    SHARE_REQUEST = "share_request"
    SHARE_APPROVE = "share_approve"
    SHARE_REJECT = "share_reject"

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
    LAB_ORDER = "lab_order"
    LAB_RESULT = "lab_result"
    IMAGING_STUDY = "imaging_study"
    PRESCRIPTION = "prescription"
    TELEHEALTH_SESSION = "telehealth_session"
    BILLING = "billing"
    ORGANIZATION = "organization"
    AUTHENTICATION = "authentication"
    RECORDS_SHARING = "records_sharing"

class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"

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
    organization_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    success: bool = True
    severity: AuditSeverity = AuditSeverity.INFO
    metadata: Optional[Dict[str, Any]] = None

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
    organization_id: Optional[str]
    ip_address: Optional[str]
    details: Optional[str]
    success: bool
    severity: Optional[str] = "info"

class AuditStatsResponse(BaseModel):
    total_logs: int
    today_logs: int
    failed_logins: int
    permission_denied_count: int
    critical_events: int
    action_breakdown: Dict[str, int]
    resource_breakdown: Dict[str, int]
    user_activity: List[Dict[str, Any]]
    hourly_activity: List[Dict[str, Any]]

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
        success: bool = True,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: dict = None
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
            organization_id=user.get("organization_id"),
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success,
            severity=severity,
            metadata=metadata
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
        severity: Optional[str] = Query(None),
        success: Optional[bool] = Query(None),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, le=1000),
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit logs (Admin only) with advanced filtering"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        
        # Organization scoping for hospital admin
        if current_user["role"] == "hospital_admin":
            query["organization_id"] = current_user.get("organization_id")
        
        if user_id:
            query["user_id"] = user_id
        if patient_id:
            query["patient_id"] = patient_id
        if action:
            query["action"] = action
        if resource_type:
            query["resource_type"] = resource_type
        if severity:
            query["severity"] = severity
        if success is not None:
            query["success"] = success
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        if search:
            query["$or"] = [
                {"user_name": {"$regex": search, "$options": "i"}},
                {"details": {"$regex": search, "$options": "i"}},
                {"patient_name": {"$regex": search, "$options": "i"}}
            ]
        
        logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        return [AuditLogResponse(**log) for log in logs]
    
    @audit_router.get("/logs/count")
    async def get_audit_logs_count(
        user_id: Optional[str] = Query(None),
        patient_id: Optional[str] = Query(None),
        action: Optional[str] = Query(None),
        resource_type: Optional[str] = Query(None),
        severity: Optional[str] = Query(None),
        success: Optional[bool] = Query(None),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get count of audit logs matching filters"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if current_user["role"] == "hospital_admin":
            query["organization_id"] = current_user.get("organization_id")
        
        if user_id:
            query["user_id"] = user_id
        if patient_id:
            query["patient_id"] = patient_id
        if action:
            query["action"] = action
        if resource_type:
            query["resource_type"] = resource_type
        if severity:
            query["severity"] = severity
        if success is not None:
            query["success"] = success
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        
        count = await db.audit_logs.count_documents(query)
        return {"count": count}
    
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
    
    @audit_router.get("/logs/user/{user_id}", response_model=List[AuditLogResponse])
    async def get_user_audit_logs(
        user_id: str,
        limit: int = Query(100, le=1000),
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit logs for a specific user"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            if current_user["id"] != user_id:
                raise HTTPException(status_code=403, detail="Cannot view other users' audit logs")
        
        logs = await db.audit_logs.find(
            {"user_id": user_id}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        return [AuditLogResponse(**log) for log in logs]
    
    @audit_router.get("/stats")
    async def get_audit_stats(
        days: int = Query(7, ge=1, le=90),
        current_user: dict = Depends(get_current_user)
    ):
        """Get comprehensive audit log statistics"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_filter = {}
        if current_user["role"] == "hospital_admin":
            org_filter["organization_id"] = current_user.get("organization_id")
        
        total_logs = await db.audit_logs.count_documents(org_filter)
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_filter = {**org_filter, "timestamp": {"$regex": f"^{today}"}}
        today_logs = await db.audit_logs.count_documents(today_filter)
        
        # Get action breakdown
        action_pipeline = [
            {"$match": org_filter},
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        action_stats = await db.audit_logs.aggregate(action_pipeline).to_list(50)
        
        # Get resource breakdown
        resource_pipeline = [
            {"$match": org_filter},
            {"$group": {"_id": "$resource_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        resource_stats = await db.audit_logs.aggregate(resource_pipeline).to_list(50)
        
        # Get failed logins
        failed_login_filter = {**org_filter, "action": "failed_login"}
        failed_logins = await db.audit_logs.count_documents(failed_login_filter)
        
        # Get permission denied count
        perm_denied_filter = {**org_filter, "action": "permission_denied"}
        permission_denied_count = await db.audit_logs.count_documents(perm_denied_filter)
        
        # Get critical events
        critical_filter = {**org_filter, "severity": "critical"}
        critical_events = await db.audit_logs.count_documents(critical_filter)
        
        # Get top users by activity (last N days)
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        user_pipeline = [
            {"$match": {**org_filter, "timestamp": {"$gte": start_date}}},
            {"$group": {"_id": {"user_id": "$user_id", "user_name": "$user_name"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        user_stats = await db.audit_logs.aggregate(user_pipeline).to_list(10)
        user_activity = [
            {"user_id": item["_id"]["user_id"], "user_name": item["_id"]["user_name"], "count": item["count"]}
            for item in user_stats
        ]
        
        # Get hourly activity pattern (last 24 hours)
        hourly_pipeline = [
            {"$match": {**org_filter, "timestamp": {"$gte": start_date}}},
            {"$addFields": {"hour": {"$substr": ["$timestamp", 11, 2]}}},
            {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        hourly_stats = await db.audit_logs.aggregate(hourly_pipeline).to_list(24)
        hourly_activity = [{"hour": int(item["_id"]), "count": item["count"]} for item in hourly_stats]
        
        return {
            "total_logs": total_logs,
            "today_logs": today_logs,
            "failed_logins": failed_logins,
            "permission_denied_count": permission_denied_count,
            "critical_events": critical_events,
            "action_breakdown": {item["_id"]: item["count"] for item in action_stats},
            "resource_breakdown": {item["_id"]: item["count"] for item in resource_stats},
            "user_activity": user_activity,
            "hourly_activity": hourly_activity,
            "period_days": days
        }
    
    @audit_router.get("/stats/security")
    async def get_security_stats(
        days: int = Query(30, ge=1, le=90),
        current_user: dict = Depends(get_current_user)
    ):
        """Get security-focused audit statistics"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        org_filter = {}
        if current_user["role"] == "hospital_admin":
            org_filter["organization_id"] = current_user.get("organization_id")
        
        base_filter = {**org_filter, "timestamp": {"$gte": start_date}}
        
        # Security-related actions
        security_actions = ["failed_login", "permission_denied", "2fa_setup", "2fa_verify", 
                          "2fa_disable", "password_change", "password_reset"]
        
        security_stats = {}
        for action in security_actions:
            count = await db.audit_logs.count_documents({**base_filter, "action": action})
            security_stats[action] = count
        
        # Failed login by IP
        failed_ip_pipeline = [
            {"$match": {**base_filter, "action": "failed_login"}},
            {"$group": {"_id": "$ip_address", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        failed_by_ip = await db.audit_logs.aggregate(failed_ip_pipeline).to_list(10)
        
        # Suspicious activity (multiple failed logins)
        suspicious_users_pipeline = [
            {"$match": {**base_filter, "action": "failed_login"}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gte": 3}}},
            {"$sort": {"count": -1}}
        ]
        suspicious_users = await db.audit_logs.aggregate(suspicious_users_pipeline).to_list(20)
        
        # 2FA adoption
        users_with_2fa = await db.users.count_documents({**org_filter, "two_factor_enabled": True})
        total_users = await db.users.count_documents(org_filter)
        
        return {
            "period_days": days,
            "security_events": security_stats,
            "failed_logins_by_ip": [{"ip": item["_id"], "count": item["count"]} for item in failed_by_ip],
            "suspicious_users": [{"user_id": item["_id"], "failed_attempts": item["count"]} for item in suspicious_users],
            "two_factor_adoption": {
                "enabled": users_with_2fa,
                "total": total_users,
                "percentage": round((users_with_2fa / total_users * 100) if total_users > 0 else 0, 1)
            }
        }
    
    @audit_router.get("/export")
    async def export_audit_logs(
        format: str = Query("csv", regex="^(csv|json)$"),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None),
        action: Optional[str] = Query(None),
        resource_type: Optional[str] = Query(None),
        limit: int = Query(10000, le=50000),
        current_user: dict = Depends(get_current_user)
    ):
        """Export audit logs as CSV or JSON"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        if current_user["role"] == "hospital_admin":
            query["organization_id"] = current_user.get("organization_id")
        
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        if action:
            query["action"] = action
        if resource_type:
            query["resource_type"] = resource_type
        
        logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Log the export action
        await log_audit_event(
            user=current_user,
            action=AuditAction.EXPORT,
            resource_type=AuditResourceType.REPORT,
            details=f"Exported {len(logs)} audit logs in {format} format",
            severity=AuditSeverity.INFO
        )
        
        if format == "json":
            return {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "exported_by": f"{current_user['first_name']} {current_user['last_name']}",
                "record_count": len(logs),
                "logs": logs
            }
        else:
            # CSV export
            output = io.StringIO()
            if logs:
                fieldnames = ["timestamp", "user_name", "user_role", "action", "resource_type", 
                            "resource_id", "patient_id", "patient_name", "ip_address", "success", 
                            "severity", "details"]
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(logs)
            
            output.seek(0)
            filename = f"audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
    
    @audit_router.get("/alerts")
    async def get_security_alerts(
        hours: int = Query(24, ge=1, le=168),
        current_user: dict = Depends(get_current_user)
    ):
        """Get recent security alerts"""
        if current_user["role"] not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        start_time = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        org_filter = {}
        if current_user["role"] == "hospital_admin":
            org_filter["organization_id"] = current_user.get("organization_id")
        
        alerts = []
        
        # Check for multiple failed logins
        failed_pipeline = [
            {"$match": {**org_filter, "timestamp": {"$gte": start_time}, "action": "failed_login"}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "last_attempt": {"$max": "$timestamp"}}},
            {"$match": {"count": {"$gte": 3}}}
        ]
        failed_results = await db.audit_logs.aggregate(failed_pipeline).to_list(50)
        for item in failed_results:
            alerts.append({
                "type": "multiple_failed_logins",
                "severity": "warning" if item["count"] < 5 else "critical",
                "user_id": item["_id"],
                "count": item["count"],
                "last_attempt": item["last_attempt"],
                "message": f"User {item['_id']} has {item['count']} failed login attempts"
            })
        
        # Check for permission denied events
        perm_denied = await db.audit_logs.count_documents({
            **org_filter, 
            "timestamp": {"$gte": start_time}, 
            "action": "permission_denied"
        })
        if perm_denied > 0:
            alerts.append({
                "type": "permission_denied",
                "severity": "info" if perm_denied < 10 else "warning",
                "count": perm_denied,
                "message": f"{perm_denied} permission denied events in the last {hours} hours"
            })
        
        # Check for critical events
        critical_events = await db.audit_logs.find({
            **org_filter,
            "timestamp": {"$gte": start_time},
            "severity": "critical"
        }, {"_id": 0}).limit(20).to_list(20)
        
        for event in critical_events:
            alerts.append({
                "type": "critical_event",
                "severity": "critical",
                "timestamp": event.get("timestamp"),
                "action": event.get("action"),
                "user_name": event.get("user_name"),
                "message": event.get("details", "Critical security event detected")
            })
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return {
            "period_hours": hours,
            "alert_count": len(alerts),
            "alerts": alerts
        }
    
    @audit_router.get("/actions")
    async def get_audit_actions():
        """Get list of all audit actions"""
        return [{"value": a.value, "name": a.name} for a in AuditAction]
    
    @audit_router.get("/resource-types")
    async def get_resource_types():
        """Get list of all resource types"""
        return [{"value": r.value, "name": r.name} for r in AuditResourceType]
    
    return audit_router, log_audit_event
