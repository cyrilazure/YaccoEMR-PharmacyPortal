"""
Hospital Super Admin IT Module
Dedicated IT administration for each hospital:
- Staff account management (onboarding, credentials)
- Role/Department/Unit assignments
- Account activation/deactivation
- NO access to patient data, appointments, billing, analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import secrets
import os

hospital_it_admin_router = APIRouter(prefix="/api/hospital", tags=["Hospital IT Admin"])

# ============ Enums ============

class ITStaffRole(str, Enum):
    PHYSICIAN = "physician"
    NURSE = "nurse"
    SCHEDULER = "scheduler"
    BILLER = "biller"
    HOSPITAL_ADMIN = "hospital_admin"
    RECEPTIONIST = "receptionist"
    LAB_TECH = "lab_tech"
    PHARMACIST = "pharmacist"
    DEPARTMENT_HEAD = "department_head"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

# ============ Models ============

class ITStaffCreate(BaseModel):
    """Staff creation by IT Admin - minimal fields"""
    email: EmailStr
    first_name: str
    last_name: str
    role: ITStaffRole
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None

class ITStaffUpdate(BaseModel):
    """Staff update by IT Admin"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[ITStaffRole] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None

class BulkStaffCreate(BaseModel):
    """Bulk staff creation"""
    staff_list: List[ITStaffCreate]

# ============ API Factory ============

def create_hospital_it_admin_endpoints(db, get_current_user, hash_password):
    """Create Hospital IT Admin API endpoints"""
    
    def verify_it_admin(user: dict, hospital_id: str):
        """Verify user is IT Super Admin for this hospital"""
        if user.get("role") == "super_admin":
            return True
        if user.get("role") not in ["hospital_it_admin", "hospital_admin"]:
            raise HTTPException(status_code=403, detail="Hospital IT Admin access required")
        if user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        return True
    
    async def log_it_action(user: dict, hospital_id: str, action: str, 
                            resource_type: str, resource_id: str, details: dict = None):
        """Log IT administrative action"""
        await db["it_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": action,
            "admin_id": user["id"],
            "admin_email": user.get("email"),
            "organization_id": hospital_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # ============ IT Admin Dashboard ============
    
    @hospital_it_admin_router.get("/{hospital_id}/super-admin/dashboard")
    async def get_it_admin_dashboard(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """
        IT Admin Dashboard - Staff management overview only.
        NO patient data, appointments, billing, analytics.
        """
        verify_it_admin(user, hospital_id)
        
        # Get hospital basic info (no patient counts)
        hospital = await db["hospitals"].find_one(
            {"id": hospital_id},
            {"_id": 0, "id": 1, "name": 1, "city": 1, "region_id": 1, "status": 1}
        )
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Staff counts only
        total_staff = await db["users"].count_documents({
            "organization_id": hospital_id
        })
        active_staff = await db["users"].count_documents({
            "organization_id": hospital_id, "is_active": True
        })
        inactive_staff = await db["users"].count_documents({
            "organization_id": hospital_id, "is_active": False
        })
        pending_staff = await db["users"].count_documents({
            "organization_id": hospital_id, "status": "pending"
        })
        
        # Role distribution
        role_distribution = await db["users"].aggregate([
            {"$match": {"organization_id": hospital_id}},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]).to_list(20)
        
        # Department counts
        departments = await db["departments"].find(
            {"organization_id": hospital_id, "is_active": True},
            {"_id": 0, "id": 1, "name": 1, "code": 1}
        ).to_list(50)
        
        for dept in departments:
            dept["staff_count"] = await db["users"].count_documents({
                "organization_id": hospital_id,
                "department_id": dept["id"],
                "is_active": True
            })
        
        # Location counts
        locations = await db["hospital_locations"].find(
            {"hospital_id": hospital_id, "is_active": True},
            {"_id": 0, "id": 1, "name": 1, "location_type": 1}
        ).to_list(50)
        
        for loc in locations:
            loc["staff_count"] = await db["users"].count_documents({
                "organization_id": hospital_id,
                "location_id": loc["id"],
                "is_active": True
            })
        
        # Recent IT actions (not patient audits)
        recent_actions = await db["it_audit_logs"].find({
            "organization_id": hospital_id
        }).sort("timestamp", -1).limit(10).to_list(10)
        
        return {
            "hospital": hospital,
            "staff_stats": {
                "total": total_staff,
                "active": active_staff,
                "inactive": inactive_staff,
                "pending": pending_staff
            },
            "role_distribution": {r["_id"]: r["count"] for r in role_distribution},
            "departments": departments,
            "locations": locations,
            "recent_it_actions": recent_actions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ Staff Account Management ============
    
    @hospital_it_admin_router.get("/{hospital_id}/super-admin/staff")
    async def list_staff_accounts(
        hospital_id: str,
        status: Optional[str] = None,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        location_id: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        user: dict = Depends(get_current_user)
    ):
        """List all staff accounts for IT management"""
        verify_it_admin(user, hospital_id)
        
        query = {"organization_id": hospital_id}
        
        if status == "active":
            query["is_active"] = True
        elif status == "inactive":
            query["is_active"] = False
        
        if role:
            query["role"] = role
        if department_id:
            query["department_id"] = department_id
        if location_id:
            query["location_id"] = location_id
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"employee_id": {"$regex": search, "$options": "i"}}
            ]
        
        total = await db["users"].count_documents(query)
        skip = (page - 1) * limit
        
        # Only return non-sensitive fields
        staff = await db["users"].find(
            query,
            {
                "_id": 0,
                "id": 1,
                "email": 1,
                "first_name": 1,
                "last_name": 1,
                "role": 1,
                "department_id": 1,
                "location_id": 1,
                "phone": 1,
                "employee_id": 1,
                "is_active": 1,
                "status": 1,
                "created_at": 1,
                "last_login": 1
            }
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Add department/location names
        for s in staff:
            if s.get("department_id"):
                dept = await db["departments"].find_one(
                    {"id": s["department_id"]}, {"_id": 0, "name": 1}
                )
                s["department_name"] = dept["name"] if dept else None
            if s.get("location_id"):
                loc = await db["hospital_locations"].find_one(
                    {"id": s["location_id"]}, {"_id": 0, "name": 1}
                )
                s["location_name"] = loc["name"] if loc else None
        
        return {
            "staff": staff,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff")
    async def create_staff_account(
        hospital_id: str,
        staff: ITStaffCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create new staff account (IT Admin only)"""
        verify_it_admin(user, hospital_id)
        
        # Check email uniqueness
        existing = await db["users"].find_one({"email": staff.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate department
        if staff.department_id:
            dept = await db["departments"].find_one({
                "id": staff.department_id, "organization_id": hospital_id
            })
            if not dept:
                raise HTTPException(status_code=404, detail="Department not found")
        
        # Validate location
        if staff.location_id:
            loc = await db["hospital_locations"].find_one({
                "id": staff.location_id, "hospital_id": hospital_id
            })
            if not loc:
                raise HTTPException(status_code=404, detail="Location not found")
        
        # Generate secure temp password
        temp_password = secrets.token_urlsafe(12)
        
        new_staff = {
            "id": str(uuid.uuid4()),
            "email": staff.email,
            "first_name": staff.first_name,
            "last_name": staff.last_name,
            "role": staff.role.value,
            "department_id": staff.department_id,
            "location_id": staff.location_id,
            "organization_id": hospital_id,
            "phone": staff.phone,
            "employee_id": staff.employee_id,
            "password": hash_password(temp_password),
            "status": "active",
            "is_active": True,
            "is_temp_password": True,
            "mfa_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"],
            "created_by_role": "it_admin"
        }
        
        await db["users"].insert_one(new_staff)
        
        # Log IT action
        await log_it_action(
            user, hospital_id, "create_staff", "user", new_staff["id"],
            {"email": staff.email, "role": staff.role.value}
        )
        
        return {
            "message": "Staff account created",
            "staff": {
                "id": new_staff["id"],
                "email": new_staff["email"],
                "name": f"{new_staff['first_name']} {new_staff['last_name']}",
                "role": new_staff["role"]
            },
            "credentials": {
                "email": staff.email,
                "temp_password": temp_password,
                "must_change_password": True
            }
        }
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff/bulk")
    async def bulk_create_staff(
        hospital_id: str,
        bulk_data: BulkStaffCreate,
        user: dict = Depends(get_current_user)
    ):
        """Bulk create staff accounts"""
        verify_it_admin(user, hospital_id)
        
        created = []
        errors = []
        
        for idx, staff in enumerate(bulk_data.staff_list):
            try:
                # Check email
                existing = await db["users"].find_one({"email": staff.email})
                if existing:
                    errors.append({"index": idx, "email": staff.email, "error": "Email exists"})
                    continue
                
                temp_password = secrets.token_urlsafe(12)
                
                new_staff = {
                    "id": str(uuid.uuid4()),
                    "email": staff.email,
                    "first_name": staff.first_name,
                    "last_name": staff.last_name,
                    "role": staff.role.value,
                    "department_id": staff.department_id,
                    "location_id": staff.location_id,
                    "organization_id": hospital_id,
                    "phone": staff.phone,
                    "employee_id": staff.employee_id,
                    "password": hash_password(temp_password),
                    "status": "active",
                    "is_active": True,
                    "is_temp_password": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": user["id"]
                }
                
                await db["users"].insert_one(new_staff)
                created.append({
                    "email": staff.email,
                    "temp_password": temp_password,
                    "role": staff.role.value
                })
                
            except Exception as e:
                errors.append({"index": idx, "email": staff.email, "error": str(e)})
        
        await log_it_action(
            user, hospital_id, "bulk_create_staff", "users", "bulk",
            {"created": len(created), "errors": len(errors)}
        )
        
        return {
            "message": f"Created {len(created)} accounts",
            "created": created,
            "errors": errors
        }
    
    @hospital_it_admin_router.get("/{hospital_id}/super-admin/staff/{staff_id}")
    async def get_staff_account(
        hospital_id: str,
        staff_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get staff account details (no patient data)"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one(
            {"id": staff_id, "organization_id": hospital_id},
            {
                "_id": 0,
                "password": 0  # Exclude password
            }
        )
        
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        # Add department/location info
        if staff.get("department_id"):
            staff["department"] = await db["departments"].find_one(
                {"id": staff["department_id"]}, {"_id": 0}
            )
        if staff.get("location_id"):
            staff["location"] = await db["hospital_locations"].find_one(
                {"id": staff["location_id"]}, {"_id": 0}
            )
        
        # Get login history (no patient activity)
        login_history = await db["it_audit_logs"].find({
            "organization_id": hospital_id,
            "resource_id": staff_id,
            "action": {"$in": ["login", "password_reset", "account_update"]}
        }).sort("timestamp", -1).limit(10).to_list(10)
        
        staff["login_history"] = login_history
        
        return staff
    
    @hospital_it_admin_router.put("/{hospital_id}/super-admin/staff/{staff_id}")
    async def update_staff_account(
        hospital_id: str,
        staff_id: str,
        updates: ITStaffUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update staff account details"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["updated_by"] = user["id"]
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": update_data}
        )
        
        await log_it_action(
            user, hospital_id, "update_staff", "user", staff_id,
            {"updates": list(update_data.keys())}
        )
        
        return {"message": "Staff account updated"}
    
    # ============ Account Activation/Deactivation ============
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff/{staff_id}/activate")
    async def activate_staff_account(
        hospital_id: str,
        staff_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Activate staff account"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "is_active": True,
                "status": "active",
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "activated_by": user["id"]
            }}
        )
        
        await log_it_action(
            user, hospital_id, "activate_account", "user", staff_id,
            {"email": staff["email"]}
        )
        
        return {"message": "Account activated"}
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff/{staff_id}/deactivate")
    async def deactivate_staff_account(
        hospital_id: str,
        staff_id: str,
        reason: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate staff account"""
        verify_it_admin(user, hospital_id)
        
        # Prevent self-deactivation
        if staff_id == user["id"]:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "is_active": False,
                "status": "inactive",
                "deactivated_at": datetime.now(timezone.utc).isoformat(),
                "deactivated_by": user["id"],
                "deactivation_reason": reason
            }}
        )
        
        await log_it_action(
            user, hospital_id, "deactivate_account", "user", staff_id,
            {"email": staff["email"], "reason": reason}
        )
        
        return {"message": "Account deactivated"}
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff/{staff_id}/suspend")
    async def suspend_staff_account(
        hospital_id: str,
        staff_id: str,
        reason: str,
        user: dict = Depends(get_current_user)
    ):
        """Suspend staff account temporarily"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "is_active": False,
                "status": "suspended",
                "suspended_at": datetime.now(timezone.utc).isoformat(),
                "suspended_by": user["id"],
                "suspension_reason": reason
            }}
        )
        
        await log_it_action(
            user, hospital_id, "suspend_account", "user", staff_id,
            {"email": staff["email"], "reason": reason}
        )
        
        return {"message": "Account suspended"}
    
    # ============ Credential Management ============
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff/{staff_id}/reset-password")
    async def reset_staff_password(
        hospital_id: str,
        staff_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Reset staff password (IT Admin only)"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        temp_password = secrets.token_urlsafe(12)
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "password": hash_password(temp_password),
                "is_temp_password": True,
                "password_reset_at": datetime.now(timezone.utc).isoformat(),
                "password_reset_by": user["id"]
            }}
        )
        
        await log_it_action(
            user, hospital_id, "reset_password", "user", staff_id,
            {"email": staff["email"]}
        )
        
        return {
            "message": "Password reset successful",
            "credentials": {
                "email": staff["email"],
                "temp_password": temp_password,
                "must_change_password": True
            }
        }
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/staff/{staff_id}/unlock")
    async def unlock_staff_account(
        hospital_id: str,
        staff_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Unlock locked staff account"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "login_attempts": 0,
                "locked_until": None,
                "unlocked_at": datetime.now(timezone.utc).isoformat(),
                "unlocked_by": user["id"]
            }}
        )
        
        await log_it_action(
            user, hospital_id, "unlock_account", "user", staff_id,
            {"email": staff["email"]}
        )
        
        return {"message": "Account unlocked"}
    
    # ============ Role & Assignment Management ============
    
    @hospital_it_admin_router.put("/{hospital_id}/super-admin/staff/{staff_id}/role")
    async def change_staff_role(
        hospital_id: str,
        staff_id: str,
        new_role: ITStaffRole,
        user: dict = Depends(get_current_user)
    ):
        """Change staff role"""
        verify_it_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        old_role = staff.get("role")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "role": new_role.value,
                "role_changed_at": datetime.now(timezone.utc).isoformat(),
                "role_changed_by": user["id"]
            }}
        )
        
        await log_it_action(
            user, hospital_id, "change_role", "user", staff_id,
            {"email": staff["email"], "old_role": old_role, "new_role": new_role.value}
        )
        
        return {"message": f"Role changed from {old_role} to {new_role.value}"}
    
    @hospital_it_admin_router.put("/{hospital_id}/super-admin/staff/{staff_id}/department")
    async def assign_staff_department(
        hospital_id: str,
        staff_id: str,
        department_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Assign staff to department"""
        verify_it_admin(user, hospital_id)
        
        # Validate department
        dept = await db["departments"].find_one({
            "id": department_id, "organization_id": hospital_id
        })
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "department_id": department_id,
                "department_assigned_at": datetime.now(timezone.utc).isoformat(),
                "department_assigned_by": user["id"]
            }}
        )
        
        await log_it_action(
            user, hospital_id, "assign_department", "user", staff_id,
            {"email": staff["email"], "department": dept["name"]}
        )
        
        return {"message": f"Assigned to {dept['name']}"}
    
    @hospital_it_admin_router.put("/{hospital_id}/super-admin/staff/{staff_id}/location")
    async def assign_staff_location(
        hospital_id: str,
        staff_id: str,
        location_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Assign staff to location"""
        verify_it_admin(user, hospital_id)
        
        # Validate location
        loc = await db["hospital_locations"].find_one({
            "id": location_id, "hospital_id": hospital_id
        })
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        await db["users"].update_one(
            {"id": staff_id},
            {"$set": {
                "location_id": location_id,
                "location_assigned_at": datetime.now(timezone.utc).isoformat(),
                "location_assigned_by": user["id"]
            }}
        )
        
        await log_it_action(
            user, hospital_id, "assign_location", "user", staff_id,
            {"email": staff["email"], "location": loc["name"]}
        )
        
        return {"message": f"Assigned to {loc['name']}"}
    
    # ============ IT Activity Log ============
    
    @hospital_it_admin_router.get("/{hospital_id}/super-admin/activity-log")
    async def get_it_activity_log(
        hospital_id: str,
        action: Optional[str] = None,
        days: int = 30,
        page: int = 1,
        limit: int = 50,
        user: dict = Depends(get_current_user)
    ):
        """Get IT admin activity log (not patient audit logs)"""
        verify_it_admin(user, hospital_id)
        
        query = {"organization_id": hospital_id}
        
        if action:
            query["action"] = action
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        query["timestamp"] = {"$gte": start_date.isoformat()}
        
        total = await db["it_audit_logs"].count_documents(query)
        skip = (page - 1) * limit
        
        logs = await db["it_audit_logs"].find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    # ============ Delete User Account ============
    
    @hospital_it_admin_router.delete("/{hospital_id}/super-admin/staff/{staff_id}")
    async def delete_staff_account(
        hospital_id: str,
        staff_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Permanently delete staff account (IT Admin only)"""
        verify_it_admin(user, hospital_id)
        
        # Prevent self-deletion
        if staff_id == user["id"]:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        staff = await db["users"].find_one({
            "id": staff_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")
        
        # Archive the user data before deletion
        archived_user = {
            **staff,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user["id"],
            "deletion_reason": "IT Admin action"
        }
        await db["deleted_users"].insert_one(archived_user)
        
        # Delete the user
        await db["users"].delete_one({"id": staff_id})
        
        # Log IT action
        await log_it_action(
            user, hospital_id, "delete_account", "user", staff_id,
            {"email": staff["email"], "role": staff.get("role")}
        )
        
        return {"message": f"Account {staff['email']} permanently deleted"}
    
    # ============ Department Management ============
    
    @hospital_it_admin_router.get("/{hospital_id}/super-admin/departments")
    async def list_departments(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """List all departments for the hospital"""
        verify_it_admin(user, hospital_id)
        
        departments = await db["departments"].find(
            {"organization_id": hospital_id},
            {"_id": 0}
        ).sort("name", 1).to_list(100)
        
        # Add staff count for each department
        for dept in departments:
            dept["staff_count"] = await db["users"].count_documents({
                "organization_id": hospital_id,
                "department_id": dept["id"],
                "is_active": True
            })
        
        return {
            "departments": departments,
            "total": len(departments)
        }
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/departments/seed")
    async def seed_default_departments(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Seed default hospital departments if none exist"""
        verify_it_admin(user, hospital_id)
        
        # Check if departments already exist
        existing_count = await db["departments"].count_documents({"organization_id": hospital_id})
        if existing_count > 0:
            return {"message": "Departments already exist", "count": existing_count}
        
        # Default hospital departments
        DEFAULT_DEPARTMENTS = [
            {"code": "ER", "name": "Emergency Department", "description": "24/7 Emergency care"},
            {"code": "OPD", "name": "Outpatient Department", "description": "Outpatient consultations"},
            {"code": "IPD", "name": "Inpatient Department", "description": "Admitted patient care"},
            {"code": "SUR", "name": "Surgery", "description": "Surgical procedures"},
            {"code": "ICU", "name": "Intensive Care Unit", "description": "Critical care"},
            {"code": "PED", "name": "Pediatrics", "description": "Children's health"},
            {"code": "OBG", "name": "Obstetrics & Gynecology", "description": "Women's health"},
            {"code": "ORTH", "name": "Orthopedics", "description": "Bone and joint care"},
            {"code": "CARD", "name": "Cardiology", "description": "Heart and cardiovascular"},
            {"code": "NEURO", "name": "Neurology", "description": "Brain and nervous system"},
            {"code": "RAD", "name": "Radiology", "description": "Medical imaging"},
            {"code": "LAB", "name": "Laboratory", "description": "Diagnostic testing"},
            {"code": "PHARM", "name": "Pharmacy", "description": "Medication dispensing"},
            {"code": "ADMIN", "name": "Administration", "description": "Hospital administration"},
            {"code": "HR", "name": "Human Resources", "description": "Staff management"},
            {"code": "FIN", "name": "Finance & Billing", "description": "Financial services"},
            {"code": "IT", "name": "Information Technology", "description": "IT support"},
            {"code": "PSYCH", "name": "Psychiatry", "description": "Mental health services"},
            {"code": "DERM", "name": "Dermatology", "description": "Skin care"},
            {"code": "ENT", "name": "ENT", "description": "Ear, nose, and throat"},
            {"code": "OPHTH", "name": "Ophthalmology", "description": "Eye care"},
            {"code": "DENT", "name": "Dental", "description": "Dental services"},
            {"code": "PHYSIO", "name": "Physiotherapy", "description": "Physical rehabilitation"},
            {"code": "NUTR", "name": "Nutrition & Dietetics", "description": "Dietary services"},
        ]
        
        created = []
        for dept in DEFAULT_DEPARTMENTS:
            dept_doc = {
                "id": str(uuid.uuid4()),
                "organization_id": hospital_id,
                "code": dept["code"],
                "name": dept["name"],
                "description": dept["description"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user["id"]
            }
            await db["departments"].insert_one(dept_doc)
            created.append(dept["name"])
        
        await log_it_action(
            user, hospital_id, "seed_departments", "departments", "bulk",
            {"count": len(created)}
        )
        
        return {
            "message": f"Created {len(created)} default departments",
            "departments": created
        }
    
    @hospital_it_admin_router.post("/{hospital_id}/super-admin/departments")
    async def create_department(
        hospital_id: str,
        code: str,
        name: str,
        description: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Create a new department"""
        verify_it_admin(user, hospital_id)
        
        # Check if code already exists
        existing = await db["departments"].find_one({
            "organization_id": hospital_id,
            "code": code.upper()
        })
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists")
        
        dept_doc = {
            "id": str(uuid.uuid4()),
            "organization_id": hospital_id,
            "code": code.upper(),
            "name": name,
            "description": description,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        await db["departments"].insert_one(dept_doc)
        
        await log_it_action(
            user, hospital_id, "create_department", "department", dept_doc["id"],
            {"code": code, "name": name}
        )
        
        return {"message": "Department created", "department": {"id": dept_doc["id"], "code": code, "name": name}}
    
    return hospital_it_admin_router


# Export
__all__ = ["hospital_it_admin_router", "create_hospital_it_admin_endpoints"]
