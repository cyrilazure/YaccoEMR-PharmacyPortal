"""
Granular Role-Based Access Control (RBAC) Module for Yacco EMR
Provides fine-grained permissions for each role with action-resource combinations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Set
from enum import Enum
from datetime import datetime, timezone
import uuid

rbac_router = APIRouter(prefix="/api/rbac", tags=["RBAC"])


# ============ PERMISSION DEFINITIONS ============

class Permission(str, Enum):
    # Patient Management
    PATIENT_VIEW = "patient:view"
    PATIENT_CREATE = "patient:create"
    PATIENT_UPDATE = "patient:update"
    PATIENT_DELETE = "patient:delete"
    
    # Clinical Documentation
    NOTE_VIEW = "note:view"
    NOTE_CREATE = "note:create"
    NOTE_UPDATE = "note:update"
    NOTE_SIGN = "note:sign"
    NOTE_DELETE = "note:delete"
    
    # Vitals
    VITALS_VIEW = "vitals:view"
    VITALS_CREATE = "vitals:create"
    
    # Medications
    MEDICATION_VIEW = "medication:view"
    MEDICATION_PRESCRIBE = "medication:prescribe"
    MEDICATION_ADMINISTER = "medication:administer"
    MEDICATION_UPDATE = "medication:update"
    
    # Orders
    ORDER_VIEW = "order:view"
    ORDER_CREATE = "order:create"
    ORDER_UPDATE_STATUS = "order:update_status"
    ORDER_CANCEL = "order:cancel"
    ORDER_ADD_RESULT = "order:add_result"
    
    # Appointments
    APPOINTMENT_VIEW = "appointment:view"
    APPOINTMENT_CREATE = "appointment:create"
    APPOINTMENT_UPDATE = "appointment:update"
    APPOINTMENT_CANCEL = "appointment:cancel"
    
    # Lab
    LAB_ORDER_CREATE = "lab:order_create"
    LAB_ORDER_VIEW = "lab:order_view"
    LAB_RESULT_VIEW = "lab:result_view"
    LAB_RESULT_ADD = "lab:result_add"
    
    # Imaging
    IMAGING_ORDER_CREATE = "imaging:order_create"
    IMAGING_VIEW = "imaging:view"
    IMAGING_INTERPRET = "imaging:interpret"
    
    # Telehealth
    TELEHEALTH_CREATE = "telehealth:create"
    TELEHEALTH_JOIN = "telehealth:join"
    TELEHEALTH_MANAGE = "telehealth:manage"
    
    # Pharmacy
    PRESCRIPTION_CREATE = "prescription:create"
    PRESCRIPTION_VIEW = "prescription:view"
    PRESCRIPTION_DISPENSE = "prescription:dispense"
    
    # Billing
    BILLING_VIEW = "billing:view"
    BILLING_CREATE = "billing:create"
    BILLING_UPDATE = "billing:update"
    
    # User Management
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DEACTIVATE = "user:deactivate"
    
    # Audit
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    
    # Organization Management
    ORG_VIEW = "organization:view"
    ORG_UPDATE = "organization:update"
    ORG_MANAGE = "organization:manage"
    
    # Records Sharing
    RECORDS_SHARE = "records:share"
    RECORDS_REQUEST = "records:request"
    RECORDS_APPROVE = "records:approve"
    
    # Reports
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_EXPORT = "report:export"
    
    # Clinical Decision Support
    CDS_VIEW = "cds:view"
    CDS_OVERRIDE = "cds:override"
    
    # System Admin
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"


# ============ ROLE PERMISSION MAPPINGS ============

# Define which permissions each role has
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "physician": {
        # Full patient access
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.PATIENT_UPDATE,
        
        # Full clinical documentation
        Permission.NOTE_VIEW,
        Permission.NOTE_CREATE,
        Permission.NOTE_UPDATE,
        Permission.NOTE_SIGN,
        
        # Vitals (view and record)
        Permission.VITALS_VIEW,
        Permission.VITALS_CREATE,
        
        # Medications - can prescribe
        Permission.MEDICATION_VIEW,
        Permission.MEDICATION_PRESCRIBE,
        Permission.MEDICATION_UPDATE,
        
        # Orders - full access
        Permission.ORDER_VIEW,
        Permission.ORDER_CREATE,
        Permission.ORDER_UPDATE_STATUS,
        Permission.ORDER_CANCEL,
        Permission.ORDER_ADD_RESULT,
        
        # Appointments
        Permission.APPOINTMENT_VIEW,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_UPDATE,
        Permission.APPOINTMENT_CANCEL,
        
        # Lab
        Permission.LAB_ORDER_CREATE,
        Permission.LAB_ORDER_VIEW,
        Permission.LAB_RESULT_VIEW,
        Permission.LAB_RESULT_ADD,
        
        # Imaging
        Permission.IMAGING_ORDER_CREATE,
        Permission.IMAGING_VIEW,
        Permission.IMAGING_INTERPRET,
        
        # Telehealth
        Permission.TELEHEALTH_CREATE,
        Permission.TELEHEALTH_JOIN,
        Permission.TELEHEALTH_MANAGE,
        
        # Pharmacy
        Permission.PRESCRIPTION_CREATE,
        Permission.PRESCRIPTION_VIEW,
        
        # Records Sharing
        Permission.RECORDS_SHARE,
        Permission.RECORDS_REQUEST,
        Permission.RECORDS_APPROVE,
        
        # Reports
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
        
        # CDS
        Permission.CDS_VIEW,
        Permission.CDS_OVERRIDE,
        
        # Basic user view
        Permission.USER_VIEW,
    },
    
    "nurse": {
        # Patient access (view and update)
        Permission.PATIENT_VIEW,
        Permission.PATIENT_UPDATE,
        
        # Clinical documentation (view and create - cannot sign)
        Permission.NOTE_VIEW,
        Permission.NOTE_CREATE,
        Permission.NOTE_UPDATE,
        
        # Vitals - full access
        Permission.VITALS_VIEW,
        Permission.VITALS_CREATE,
        
        # Medications - can view and administer, NOT prescribe
        Permission.MEDICATION_VIEW,
        Permission.MEDICATION_ADMINISTER,
        
        # Orders - view and update status only, NOT create
        Permission.ORDER_VIEW,
        Permission.ORDER_UPDATE_STATUS,
        
        # Appointments - view only
        Permission.APPOINTMENT_VIEW,
        
        # Lab - view only
        Permission.LAB_ORDER_VIEW,
        Permission.LAB_RESULT_VIEW,
        
        # Imaging - view only
        Permission.IMAGING_VIEW,
        
        # Telehealth - join only
        Permission.TELEHEALTH_JOIN,
        
        # Pharmacy - view prescriptions
        Permission.PRESCRIPTION_VIEW,
        
        # CDS - view alerts
        Permission.CDS_VIEW,
        
        # Reports - view only
        Permission.REPORT_VIEW,
        
        # Basic user view
        Permission.USER_VIEW,
    },
    
    "scheduler": {
        # Patient - view and create only
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        
        # Appointments - full access
        Permission.APPOINTMENT_VIEW,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_UPDATE,
        Permission.APPOINTMENT_CANCEL,
        
        # Telehealth - create and view sessions
        Permission.TELEHEALTH_CREATE,
        
        # User view for scheduling
        Permission.USER_VIEW,
        
        # Basic report view
        Permission.REPORT_VIEW,
    },
    
    "admin": {
        # Patient management
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.PATIENT_UPDATE,
        Permission.PATIENT_DELETE,
        
        # User management
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DEACTIVATE,
        
        # Audit access
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        
        # Billing
        Permission.BILLING_VIEW,
        Permission.BILLING_CREATE,
        Permission.BILLING_UPDATE,
        
        # Reports
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
        
        # Organization (view only)
        Permission.ORG_VIEW,
        
        # View everything clinical (read-only)
        Permission.NOTE_VIEW,
        Permission.VITALS_VIEW,
        Permission.MEDICATION_VIEW,
        Permission.ORDER_VIEW,
        Permission.APPOINTMENT_VIEW,
        Permission.LAB_ORDER_VIEW,
        Permission.LAB_RESULT_VIEW,
        Permission.IMAGING_VIEW,
        Permission.PRESCRIPTION_VIEW,
        Permission.CDS_VIEW,
    },
    
    "hospital_admin": {
        # Full patient management
        Permission.PATIENT_VIEW,
        Permission.PATIENT_CREATE,
        Permission.PATIENT_UPDATE,
        Permission.PATIENT_DELETE,
        
        # Full user management
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DEACTIVATE,
        
        # Organization management
        Permission.ORG_VIEW,
        Permission.ORG_UPDATE,
        
        # Audit access
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        
        # Billing full access
        Permission.BILLING_VIEW,
        Permission.BILLING_CREATE,
        Permission.BILLING_UPDATE,
        
        # Reports full access
        Permission.REPORT_VIEW,
        Permission.REPORT_CREATE,
        Permission.REPORT_EXPORT,
        
        # View clinical data
        Permission.NOTE_VIEW,
        Permission.VITALS_VIEW,
        Permission.MEDICATION_VIEW,
        Permission.ORDER_VIEW,
        Permission.APPOINTMENT_VIEW,
        Permission.APPOINTMENT_CREATE,
        Permission.APPOINTMENT_UPDATE,
        Permission.APPOINTMENT_CANCEL,
        Permission.LAB_ORDER_VIEW,
        Permission.LAB_RESULT_VIEW,
        Permission.IMAGING_VIEW,
        Permission.PRESCRIPTION_VIEW,
        Permission.CDS_VIEW,
        Permission.TELEHEALTH_CREATE,
        Permission.TELEHEALTH_JOIN,
        Permission.TELEHEALTH_MANAGE,
        Permission.RECORDS_SHARE,
        Permission.RECORDS_REQUEST,
        Permission.RECORDS_APPROVE,
    },
    
    "super_admin": {
        # ALL PERMISSIONS - platform level access
        *Permission.__members__.values()
    }
}


# ============ MODELS ============

class RoleInfo(BaseModel):
    role: str
    display_name: str
    description: str
    permissions: List[str]
    permission_count: int


class PermissionCheck(BaseModel):
    permission: str
    allowed: bool
    role: str


class BulkPermissionCheck(BaseModel):
    role: str
    checks: List[PermissionCheck]


# ============ HELPER FUNCTIONS ============

def get_role_permissions(role: str) -> Set[str]:
    """Get all permissions for a role"""
    permissions = ROLE_PERMISSIONS.get(role, set())
    # Convert Permission enum to string values
    return {p.value if isinstance(p, Permission) else p for p in permissions}


def has_permission(user_role: str, permission: str) -> bool:
    """Check if a role has a specific permission"""
    role_perms = get_role_permissions(user_role)
    return permission in role_perms


def check_permission(user: dict, permission: str) -> bool:
    """Check if user has permission, raise HTTPException if not"""
    if not has_permission(user.get("role", ""), permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} required"
        )
    return True


def require_any_permission(user: dict, permissions: List[str]) -> bool:
    """Check if user has at least one of the permissions"""
    user_perms = get_role_permissions(user.get("role", ""))
    if not any(p in user_perms for p in permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: one of {permissions} required"
        )
    return True


def require_all_permissions(user: dict, permissions: List[str]) -> bool:
    """Check if user has all of the permissions"""
    user_perms = get_role_permissions(user.get("role", ""))
    missing = [p for p in permissions if p not in user_perms]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: missing {missing}"
        )
    return True


# ============ ROLE DESCRIPTIONS ============

ROLE_DESCRIPTIONS = {
    "physician": {
        "display_name": "Physician",
        "description": "Licensed medical doctor with full clinical privileges including prescribing, ordering, and documentation"
    },
    "nurse": {
        "display_name": "Nurse",
        "description": "Registered nurse with medication administration, vital signs, and patient care capabilities"
    },
    "scheduler": {
        "display_name": "Scheduler",
        "description": "Front desk staff responsible for patient registration and appointment scheduling"
    },
    "admin": {
        "display_name": "Administrator",
        "description": "Department administrator with user management and reporting capabilities"
    },
    "hospital_admin": {
        "display_name": "Hospital Administrator",
        "description": "Hospital-level administrator with full organizational management capabilities"
    },
    "super_admin": {
        "display_name": "Platform Super Admin",
        "description": "Platform-level administrator with unrestricted access to all hospitals and features"
    }
}


# ============ API ENDPOINTS ============

def create_rbac_endpoints(db, get_current_user):
    """Create RBAC endpoints"""
    
    @rbac_router.get("/permissions/my")
    async def get_my_permissions(current_user: dict = Depends(get_current_user)):
        """Get current user's permissions"""
        role = current_user.get("role", "")
        permissions = list(get_role_permissions(role))
        role_info = ROLE_DESCRIPTIONS.get(role, {"display_name": role.title(), "description": ""})
        
        return {
            "user_id": current_user.get("id"),
            "role": role,
            "display_name": role_info["display_name"],
            "description": role_info["description"],
            "permissions": sorted(permissions),
            "permission_count": len(permissions)
        }
    
    @rbac_router.get("/permissions/check/{permission}")
    async def check_single_permission(
        permission: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Check if current user has a specific permission"""
        allowed = has_permission(current_user.get("role", ""), permission)
        return {
            "permission": permission,
            "allowed": allowed,
            "role": current_user.get("role")
        }
    
    @rbac_router.post("/permissions/check-bulk")
    async def check_bulk_permissions(
        permissions: List[str],
        current_user: dict = Depends(get_current_user)
    ):
        """Check multiple permissions at once"""
        role = current_user.get("role", "")
        user_perms = get_role_permissions(role)
        
        checks = [
            {"permission": p, "allowed": p in user_perms}
            for p in permissions
        ]
        
        return {
            "role": role,
            "checks": checks,
            "allowed_count": sum(1 for c in checks if c["allowed"]),
            "denied_count": sum(1 for c in checks if not c["allowed"])
        }
    
    @rbac_router.get("/roles")
    async def get_all_roles(current_user: dict = Depends(get_current_user)):
        """Get all roles and their permissions"""
        # Only admin/super_admin can see all roles
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        roles = []
        for role, perms in ROLE_PERMISSIONS.items():
            role_info = ROLE_DESCRIPTIONS.get(role, {"display_name": role.title(), "description": ""})
            perm_list = sorted([p.value if isinstance(p, Permission) else p for p in perms])
            roles.append({
                "role": role,
                "display_name": role_info["display_name"],
                "description": role_info["description"],
                "permissions": perm_list,
                "permission_count": len(perm_list)
            })
        
        return roles
    
    @rbac_router.get("/roles/{role}")
    async def get_role_details(
        role: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get details for a specific role"""
        if role not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=404, detail=f"Role '{role}' not found")
        
        perms = list(get_role_permissions(role))
        role_info = ROLE_DESCRIPTIONS.get(role, {"display_name": role.title(), "description": ""})
        
        # Group permissions by category
        grouped = {}
        for p in sorted(perms):
            category = p.split(":")[0] if ":" in p else "other"
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(p)
        
        return {
            "role": role,
            "display_name": role_info["display_name"],
            "description": role_info["description"],
            "permissions": sorted(perms),
            "permission_count": len(perms),
            "permissions_by_category": grouped
        }
    
    @rbac_router.get("/permissions/all")
    async def get_all_permissions(current_user: dict = Depends(get_current_user)):
        """Get list of all available permissions"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Group permissions by category
        grouped = {}
        for perm in Permission:
            category = perm.value.split(":")[0]
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                "permission": perm.value,
                "name": perm.name.replace("_", " ").title()
            })
        
        return {
            "total_permissions": len(Permission),
            "categories": list(grouped.keys()),
            "permissions_by_category": grouped
        }
    
    @rbac_router.get("/matrix")
    async def get_permission_matrix(current_user: dict = Depends(get_current_user)):
        """Get complete permission matrix for all roles"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Build matrix
        matrix = {}
        all_perms = [p.value for p in Permission]
        
        for role in ROLE_PERMISSIONS.keys():
            role_perms = get_role_permissions(role)
            matrix[role] = {
                "display_name": ROLE_DESCRIPTIONS.get(role, {}).get("display_name", role.title()),
                "permissions": {p: p in role_perms for p in all_perms}
            }
        
        return {
            "roles": list(ROLE_PERMISSIONS.keys()),
            "all_permissions": all_perms,
            "matrix": matrix
        }
    
    return rbac_router, check_permission, has_permission, require_any_permission


# Export utilities
__all__ = [
    'Permission',
    'ROLE_PERMISSIONS', 
    'get_role_permissions',
    'has_permission',
    'check_permission',
    'require_any_permission',
    'require_all_permissions',
    'create_rbac_endpoints',
    'rbac_router'
]
