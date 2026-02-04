"""
Admin Portal Module for Yacco EMR
Comprehensive administration features for:
- Hospital Admin: User management, role assignment, audit logs, record sharing policies
- Super Admin: Organization management, system-wide audits, security policies
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

admin_router = APIRouter(prefix="/api/admin", tags=["Admin Portal"])


# ============ Enums ============

class SecurityPolicyType(str, Enum):
    PASSWORD = "password"
    SESSION = "session"
    MFA = "mfa"
    ACCESS = "access"
    DATA_RETENTION = "data_retention"


class UserActionType(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    RESET_PASSWORD = "reset_password"
    FORCE_LOGOUT = "force_logout"
    UNLOCK = "unlock"
    UPDATE_ROLE = "update_role"


class PolicyApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


# ============ Models ============

class PermissionGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    organization_id: Optional[str] = None
    permissions: List[str] = []
    is_system: bool = False  # System groups cannot be deleted
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PermissionGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class UserRoleAssignment(BaseModel):
    user_id: str
    role: str
    department_id: Optional[str] = None
    permissions_groups: List[str] = []
    custom_permissions: List[str] = []


class SharingPolicyRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    requesting_organization_id: str
    requesting_organization_name: str
    target_organization_id: str
    target_organization_name: str
    policy_type: str  # "full_access", "limited", "emergency_only"
    requested_data_types: List[str] = []  # ["patient_records", "lab_results", "imaging"]
    justification: str
    duration_days: Optional[int] = 365
    status: PolicyApprovalStatus = PolicyApprovalStatus.PENDING
    requested_at: str
    requested_by: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    denial_reason: Optional[str] = None


class SharingPolicyApproval(BaseModel):
    approved_data_types: List[str] = []
    duration_days: int = 365
    conditions: Optional[str] = None


class SecurityPolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    policy_type: SecurityPolicyType
    name: str
    description: Optional[str] = None
    settings: Dict[str, Any] = {}
    is_active: bool = True
    applies_to_roles: List[str] = []  # Empty = all roles
    organization_id: Optional[str] = None  # None = platform-wide
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecurityPolicyCreate(BaseModel):
    policy_type: SecurityPolicyType
    name: str
    description: Optional[str] = None
    settings: Dict[str, Any] = {}
    applies_to_roles: List[str] = []


class UserBulkAction(BaseModel):
    user_ids: List[str]
    action: UserActionType
    reason: Optional[str] = None


class SystemHealthCheck(BaseModel):
    component: str
    status: str
    latency_ms: Optional[int] = None
    last_check: str
    details: Optional[Dict[str, Any]] = None


# ============ Default Security Policies ============

DEFAULT_PASSWORD_POLICY = {
    "min_length": 12,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special": True,
    "max_age_days": 90,
    "history_count": 5,
    "lockout_attempts": 5,
    "lockout_duration_minutes": 30
}

DEFAULT_SESSION_POLICY = {
    "max_session_duration_hours": 12,
    "idle_timeout_minutes": 30,
    "max_concurrent_sessions": 3,
    "require_ip_binding": False,
    "force_logout_on_password_change": True
}

DEFAULT_MFA_POLICY = {
    "required_for_roles": ["super_admin", "hospital_admin"],
    "required_for_sensitive_actions": True,
    "allowed_methods": ["totp", "email", "sms"],
    "remember_device_days": 30
}

DEFAULT_ACCESS_POLICY = {
    "allowed_ip_ranges": [],
    "blocked_countries": [],
    "require_vpn_for_admin": False,
    "working_hours_only": False,
    "working_hours_start": "06:00",
    "working_hours_end": "22:00"
}


# ============ Available Permissions ============

ALL_PERMISSIONS = {
    "patient": ["view", "create", "update", "delete", "export"],
    "order": ["view", "create", "update", "cancel", "sign"],
    "medication": ["view", "prescribe", "administer", "dispense"],
    "lab": ["view", "order", "result_view", "result_add", "interpret"],
    "imaging": ["view", "order", "view_images", "interpret"],
    "billing": ["view", "create", "update", "void", "export"],
    "appointment": ["view", "create", "update", "cancel"],
    "telehealth": ["view", "create", "join", "manage"],
    "report": ["view", "create", "sign", "export"],
    "audit": ["view", "export"],
    "user": ["view", "create", "update", "deactivate", "manage_roles"],
    "organization": ["view", "update", "manage_settings"],
    "system": ["view_health", "manage_policies", "backup", "restore"]
}


def create_admin_portal_endpoints(db, get_current_user):
    """Create admin portal endpoints with database and auth dependency"""
    
    def require_hospital_admin(user: dict) -> dict:
        """Verify user has hospital admin role"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Hospital admin access required")
        return user
    
    def require_super_admin(user: dict) -> dict:
        """Verify user has super admin role"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super admin access required")
        return user
    
    # ============ Permission Groups Endpoints (Hospital Admin) ============
    
    @admin_router.get("/permission-groups")
    async def get_permission_groups(current_user: dict = Depends(get_current_user)):
        """Get all permission groups for the organization"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        query = {"$or": [{"organization_id": org_id}, {"is_system": True}]}
        groups = await db.permission_groups.find(query, {"_id": 0}).to_list(100)
        
        # Add system groups if empty
        if not groups:
            system_groups = [
                PermissionGroup(name="Physicians", permissions=["patient:view", "patient:update", "order:view", "order:create", "medication:prescribe", "lab:order", "imaging:order"], is_system=True),
                PermissionGroup(name="Nurses", permissions=["patient:view", "patient:update", "order:view", "medication:view", "medication:administer", "lab:result_view"], is_system=True),
                PermissionGroup(name="Schedulers", permissions=["patient:view", "appointment:view", "appointment:create", "appointment:update"], is_system=True),
                PermissionGroup(name="Billing Staff", permissions=["patient:view", "billing:view", "billing:create", "billing:update"], is_system=True),
                PermissionGroup(name="Lab Technicians", permissions=["patient:view", "lab:view", "lab:result_view", "lab:result_add"], is_system=True),
                PermissionGroup(name="Radiology", permissions=["patient:view", "imaging:view", "imaging:view_images", "imaging:interpret"], is_system=True)
            ]
            groups = [g.model_dump() for g in system_groups]
        
        return {"groups": groups}
    
    @admin_router.post("/permission-groups")
    async def create_permission_group(
        group_data: PermissionGroupCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new permission group"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        group = PermissionGroup(
            name=group_data.name,
            description=group_data.description,
            organization_id=org_id,
            permissions=group_data.permissions,
            is_system=False,
            created_by=current_user["id"]
        )
        
        group_dict = group.model_dump()
        await db.permission_groups.insert_one(group_dict)
        if "_id" in group_dict:
            del group_dict["_id"]
        
        return {"message": "Permission group created", "group": group_dict}
    
    @admin_router.put("/permission-groups/{group_id}")
    async def update_permission_group(
        group_id: str,
        group_data: PermissionGroupCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update a permission group"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        # Cannot update system groups
        existing = await db.permission_groups.find_one({"id": group_id})
        if existing and existing.get("is_system"):
            raise HTTPException(status_code=400, detail="Cannot modify system groups")
        
        result = await db.permission_groups.update_one(
            {"id": group_id, "organization_id": org_id},
            {"$set": {
                "name": group_data.name,
                "description": group_data.description,
                "permissions": group_data.permissions
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Permission group not found")
        
        return {"message": "Permission group updated"}
    
    @admin_router.delete("/permission-groups/{group_id}")
    async def delete_permission_group(
        group_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Delete a permission group"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        result = await db.permission_groups.delete_one({
            "id": group_id,
            "organization_id": org_id,
            "is_system": False
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Permission group not found or is system group")
        
        return {"message": "Permission group deleted"}
    
    @admin_router.get("/available-permissions")
    async def get_available_permissions(current_user: dict = Depends(get_current_user)):
        """Get all available permissions"""
        require_hospital_admin(current_user)
        
        permissions = []
        for category, actions in ALL_PERMISSIONS.items():
            for action in actions:
                permissions.append({
                    "key": f"{category}:{action}",
                    "category": category,
                    "action": action,
                    "description": f"{action.replace('_', ' ').title()} {category}"
                })
        
        return {"permissions": permissions, "categories": list(ALL_PERMISSIONS.keys())}
    
    # ============ User Role Assignment (Hospital Admin) ============
    
    @admin_router.get("/users")
    async def get_organization_users(
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        department: Optional[str] = None,
        page: int = 0,
        limit: int = 50,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all users in the organization with filters"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        query = {}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        if search:
            query["$or"] = [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        if role:
            query["role"] = role
        
        if status == "active":
            query["is_active"] = True
        elif status == "inactive":
            query["is_active"] = False
        
        if department:
            query["department"] = department
        
        total = await db.users.count_documents(query)
        users = await db.users.find(
            query,
            {"_id": 0, "password": 0}
        ).skip(page * limit).limit(limit).to_list(limit)
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    @admin_router.put("/users/{user_id}/role")
    async def update_user_role(
        user_id: str,
        assignment: UserRoleAssignment,
        current_user: dict = Depends(get_current_user)
    ):
        """Update a user's role and permissions"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        # Verify user belongs to organization
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if org_id and user.get("organization_id") != org_id and current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Cannot modify users outside your organization")
        
        # Cannot change super_admin role
        if user.get("role") == "super_admin" and current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Cannot modify super admin")
        
        update_data = {
            "role": assignment.role,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if assignment.department_id:
            update_data["department_id"] = assignment.department_id
        
        if assignment.permissions_groups:
            update_data["permission_groups"] = assignment.permissions_groups
        
        if assignment.custom_permissions:
            update_data["custom_permissions"] = assignment.custom_permissions
        
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        
        # Log the role change
        audit_log = {
            "id": str(uuid.uuid4()),
            "action": "user_role_change",
            "user_id": current_user["id"],
            "target_user_id": user_id,
            "old_role": user.get("role"),
            "new_role": assignment.role,
            "organization_id": org_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.audit_logs.insert_one(audit_log)
        
        return {"message": "User role updated successfully"}
    
    @admin_router.post("/users/bulk-action")
    async def perform_bulk_user_action(
        action_data: UserBulkAction,
        current_user: dict = Depends(get_current_user)
    ):
        """Perform bulk actions on users"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        results = {"success": 0, "failed": 0, "errors": []}
        
        for user_id in action_data.user_ids:
            try:
                user = await db.users.find_one({"id": user_id}, {"_id": 0})
                if not user:
                    results["failed"] += 1
                    results["errors"].append(f"User {user_id} not found")
                    continue
                
                if org_id and user.get("organization_id") != org_id:
                    results["failed"] += 1
                    results["errors"].append(f"User {user_id} not in organization")
                    continue
                
                update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
                
                if action_data.action == UserActionType.ACTIVATE:
                    update_data["is_active"] = True
                elif action_data.action == UserActionType.DEACTIVATE:
                    update_data["is_active"] = False
                elif action_data.action == UserActionType.UNLOCK:
                    update_data["failed_login_attempts"] = 0
                    update_data["locked_until"] = None
                elif action_data.action == UserActionType.FORCE_LOGOUT:
                    # Invalidate all sessions
                    await db.user_sessions.delete_many({"user_id": user_id})
                
                await db.users.update_one({"id": user_id}, {"$set": update_data})
                results["success"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"User {user_id}: {str(e)}")
        
        return results
    
    @admin_router.get("/users/{user_id}/activity")
    async def get_user_activity(
        user_id: str,
        days: int = 30,
        current_user: dict = Depends(get_current_user)
    ):
        """Get user's recent activity"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        # Verify user belongs to organization
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if org_id and user.get("organization_id") != org_id and current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Cannot view users outside your organization")
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get audit logs for user
        logs = await db.audit_logs.find({
            "user_id": user_id,
            "timestamp": {"$gte": since}
        }, {"_id": 0}).sort("timestamp", -1).limit(100).to_list(100)
        
        # Get login history
        logins = await db.user_sessions.find({
            "user_id": user_id,
            "created_at": {"$gte": since}
        }, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
        
        return {
            "user": user,
            "activity_logs": logs,
            "login_history": logins,
            "period_days": days
        }
    
    # ============ Record Sharing Policy Management (Hospital Admin) ============
    
    @admin_router.get("/sharing-policies")
    async def get_sharing_policy_requests(
        status: Optional[str] = None,
        direction: str = "incoming",  # incoming or outgoing
        current_user: dict = Depends(get_current_user)
    ):
        """Get sharing policy requests"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        if direction == "incoming":
            query = {"target_organization_id": org_id}
        else:
            query = {"requesting_organization_id": org_id}
        
        if status:
            query["status"] = status
        
        policies = await db.sharing_policies.find(query, {"_id": 0}).sort("requested_at", -1).to_list(100)
        
        return {"policies": policies, "direction": direction}
    
    @admin_router.post("/sharing-policies/{policy_id}/approve")
    async def approve_sharing_policy(
        policy_id: str,
        approval: SharingPolicyApproval,
        current_user: dict = Depends(get_current_user)
    ):
        """Approve a sharing policy request"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        policy = await db.sharing_policies.find_one({
            "id": policy_id,
            "target_organization_id": org_id,
            "status": PolicyApprovalStatus.PENDING.value
        })
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy request not found")
        
        now = datetime.now(timezone.utc)
        
        await db.sharing_policies.update_one(
            {"id": policy_id},
            {"$set": {
                "status": PolicyApprovalStatus.APPROVED.value,
                "reviewed_at": now.isoformat(),
                "reviewed_by": current_user["id"],
                "approved_data_types": approval.approved_data_types,
                "duration_days": approval.duration_days,
                "conditions": approval.conditions,
                "expires_at": (now + timedelta(days=approval.duration_days)).isoformat()
            }}
        )
        
        # Create notification for requesting org
        notification = {
            "id": str(uuid.uuid4()),
            "type": "sharing_policy_approved",
            "organization_id": policy["requesting_organization_id"],
            "title": "Sharing Policy Approved",
            "message": f"Your data sharing request with {policy['target_organization_name']} has been approved",
            "created_at": now.isoformat()
        }
        await db.notifications.insert_one(notification)
        
        return {"message": "Sharing policy approved"}
    
    @admin_router.post("/sharing-policies/{policy_id}/deny")
    async def deny_sharing_policy(
        policy_id: str,
        reason: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Deny a sharing policy request"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        result = await db.sharing_policies.update_one(
            {
                "id": policy_id,
                "target_organization_id": org_id,
                "status": PolicyApprovalStatus.PENDING.value
            },
            {"$set": {
                "status": PolicyApprovalStatus.DENIED.value,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "reviewed_by": current_user["id"],
                "denial_reason": reason
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy request not found")
        
        return {"message": "Sharing policy denied"}
    
    @admin_router.post("/sharing-policies/request")
    async def create_sharing_policy_request(
        target_org_id: str,
        policy_type: str,
        data_types: List[str],
        justification: str,
        duration_days: int = 365,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new sharing policy request"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        # Get organization names
        requesting_org = await db.organizations.find_one({"id": org_id}, {"_id": 0})
        target_org = await db.organizations.find_one({"id": target_org_id}, {"_id": 0})
        
        if not target_org:
            raise HTTPException(status_code=404, detail="Target organization not found")
        
        now = datetime.now(timezone.utc)
        
        policy_request = SharingPolicyRequest(
            requesting_organization_id=org_id,
            requesting_organization_name=requesting_org.get("name", "Unknown") if requesting_org else "Unknown",
            target_organization_id=target_org_id,
            target_organization_name=target_org.get("name", "Unknown"),
            policy_type=policy_type,
            requested_data_types=data_types,
            justification=justification,
            duration_days=duration_days,
            requested_at=now.isoformat(),
            requested_by=current_user["id"]
        )
        
        policy_dict = policy_request.model_dump()
        await db.sharing_policies.insert_one(policy_dict)
        if "_id" in policy_dict:
            del policy_dict["_id"]
        
        return {"message": "Sharing policy request created", "policy": policy_dict}
    
    # ============ Hospital Admin Dashboard Stats ============
    
    @admin_router.get("/dashboard/stats")
    async def get_admin_dashboard_stats(current_user: dict = Depends(get_current_user)):
        """Get hospital admin dashboard statistics"""
        require_hospital_admin(current_user)
        org_id = current_user.get("organization_id")
        
        query = {}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        # User stats
        total_users = await db.users.count_documents(query)
        active_users = await db.users.count_documents({**query, "is_active": True})
        
        # Role distribution
        pipeline = [
            {"$match": query},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]
        role_dist = await db.users.aggregate(pipeline).to_list(20)
        
        # Patient stats
        patient_query = {} if not org_id else {"organization_id": org_id}
        total_patients = await db.patients.count_documents(patient_query)
        
        # Recent activity (last 24 hours)
        since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        recent_logs = await db.audit_logs.count_documents({
            **query,
            "timestamp": {"$gte": since_24h}
        })
        
        # Pending sharing requests
        pending_policies = await db.sharing_policies.count_documents({
            "target_organization_id": org_id,
            "status": PolicyApprovalStatus.PENDING.value
        })
        
        # Locked accounts
        locked_accounts = await db.users.count_documents({
            **query,
            "locked_until": {"$gte": datetime.now(timezone.utc).isoformat()}
        })
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users,
                "locked": locked_accounts
            },
            "role_distribution": {r["_id"]: r["count"] for r in role_dist},
            "patients": {"total": total_patients},
            "activity_24h": recent_logs,
            "pending_sharing_requests": pending_policies,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ Super Admin - Security Policies ============
    
    @admin_router.get("/security-policies")
    async def get_security_policies(
        policy_type: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all security policies"""
        require_super_admin(current_user)
        
        query = {}
        if policy_type:
            query["policy_type"] = policy_type
        
        policies = await db.security_policies.find(query, {"_id": 0}).to_list(100)
        
        # Return defaults if empty
        if not policies:
            policies = [
                {"policy_type": "password", "name": "Password Policy", "settings": DEFAULT_PASSWORD_POLICY, "is_active": True},
                {"policy_type": "session", "name": "Session Policy", "settings": DEFAULT_SESSION_POLICY, "is_active": True},
                {"policy_type": "mfa", "name": "MFA Policy", "settings": DEFAULT_MFA_POLICY, "is_active": True},
                {"policy_type": "access", "name": "Access Policy", "settings": DEFAULT_ACCESS_POLICY, "is_active": True}
            ]
        
        return {"policies": policies}
    
    @admin_router.post("/security-policies")
    async def create_security_policy(
        policy_data: SecurityPolicyCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create or update a security policy"""
        require_super_admin(current_user)
        
        now = datetime.now(timezone.utc)
        
        # Update existing or create new
        existing = await db.security_policies.find_one({"policy_type": policy_data.policy_type.value})
        
        if existing:
            await db.security_policies.update_one(
                {"policy_type": policy_data.policy_type.value},
                {"$set": {
                    "name": policy_data.name,
                    "description": policy_data.description,
                    "settings": policy_data.settings,
                    "applies_to_roles": policy_data.applies_to_roles,
                    "updated_at": now.isoformat()
                }}
            )
            return {"message": "Security policy updated"}
        else:
            policy = SecurityPolicy(
                policy_type=policy_data.policy_type,
                name=policy_data.name,
                description=policy_data.description,
                settings=policy_data.settings,
                applies_to_roles=policy_data.applies_to_roles,
                created_by=current_user["id"]
            )
            policy_dict = policy.model_dump()
            await db.security_policies.insert_one(policy_dict)
            return {"message": "Security policy created"}
    
    @admin_router.put("/security-policies/{policy_type}/toggle")
    async def toggle_security_policy(
        policy_type: str,
        is_active: bool,
        current_user: dict = Depends(get_current_user)
    ):
        """Enable or disable a security policy"""
        require_super_admin(current_user)
        
        result = await db.security_policies.update_one(
            {"policy_type": policy_type},
            {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return {"message": f"Policy {'enabled' if is_active else 'disabled'}"}
    
    # ============ Super Admin - System-Wide Audit ============
    
    @admin_router.get("/system/audit-logs")
    async def get_system_audit_logs(
        organization_id: Optional[str] = None,
        action: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 7,
        page: int = 0,
        limit: int = 100,
        current_user: dict = Depends(get_current_user)
    ):
        """Get system-wide audit logs"""
        require_super_admin(current_user)
        
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        query = {"timestamp": {"$gte": since}}
        if organization_id:
            query["organization_id"] = organization_id
        if action:
            query["action"] = action
        if severity:
            query["severity"] = severity
        if user_id:
            query["user_id"] = user_id
        
        total = await db.audit_logs.count_documents(query)
        logs = await db.audit_logs.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(page * limit).limit(limit).to_list(limit)
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "limit": limit,
            "period_days": days
        }
    
    @admin_router.get("/system/security-alerts")
    async def get_security_alerts(
        hours: int = 24,
        current_user: dict = Depends(get_current_user)
    ):
        """Get security-related alerts across the system"""
        require_super_admin(current_user)
        
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        security_actions = [
            "login_failed", "login_blocked", "password_reset",
            "mfa_failed", "permission_denied", "suspicious_activity",
            "session_hijack_attempt", "brute_force_detected"
        ]
        
        alerts = await db.audit_logs.find({
            "action": {"$in": security_actions},
            "timestamp": {"$gte": since}
        }, {"_id": 0}).sort("timestamp", -1).limit(200).to_list(200)
        
        # Aggregate by type
        alert_counts = {}
        for alert in alerts:
            action = alert.get("action", "unknown")
            alert_counts[action] = alert_counts.get(action, 0) + 1
        
        return {
            "alerts": alerts,
            "summary": alert_counts,
            "total": len(alerts),
            "period_hours": hours
        }
    
    # ============ Super Admin - System Health ============
    
    @admin_router.get("/system/health")
    async def get_system_health(current_user: dict = Depends(get_current_user)):
        """Get system health status"""
        require_super_admin(current_user)
        
        now = datetime.now(timezone.utc)
        health_checks = []
        
        # Database check
        try:
            await db.command("ping")
            health_checks.append(SystemHealthCheck(
                component="MongoDB",
                status="healthy",
                last_check=now.isoformat()
            ).model_dump())
        except:
            health_checks.append(SystemHealthCheck(
                component="MongoDB",
                status="unhealthy",
                last_check=now.isoformat()
            ).model_dump())
        
        # API check
        health_checks.append(SystemHealthCheck(
            component="API Server",
            status="healthy",
            last_check=now.isoformat()
        ).model_dump())
        
        # Get organization stats
        total_orgs = await db.organizations.count_documents({})
        active_orgs = await db.organizations.count_documents({"status": "active"})
        total_users = await db.users.count_documents({})
        total_patients = await db.patients.count_documents({})
        
        return {
            "status": "healthy" if all(h["status"] == "healthy" for h in health_checks) else "degraded",
            "checks": health_checks,
            "stats": {
                "total_organizations": total_orgs,
                "active_organizations": active_orgs,
                "total_users": total_users,
                "total_patients": total_patients
            },
            "timestamp": now.isoformat()
        }
    
    @admin_router.get("/system/stats")
    async def get_platform_stats(current_user: dict = Depends(get_current_user)):
        """Get platform-wide statistics"""
        require_super_admin(current_user)
        
        # Organization stats
        org_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        org_stats = await db.organizations.aggregate(org_pipeline).to_list(10)
        
        # User stats by role
        user_pipeline = [
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]
        user_stats = await db.users.aggregate(user_pipeline).to_list(20)
        
        # Activity trend (last 7 days)
        activity_trend = []
        for i in range(7):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0).isoformat()
            day_end = day.replace(hour=23, minute=59, second=59).isoformat()
            
            count = await db.audit_logs.count_documents({
                "timestamp": {"$gte": day_start, "$lte": day_end}
            })
            activity_trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "count": count
            })
        
        return {
            "organizations": {s["_id"]: s["count"] for s in org_stats},
            "users_by_role": {s["_id"]: s["count"] for s in user_stats},
            "activity_trend": list(reversed(activity_trend)),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return admin_router
