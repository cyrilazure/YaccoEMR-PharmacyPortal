"""
Hospital Admin Portal Module
Provides comprehensive hospital administration capabilities:
- User management (CRUD for all staff types)
- Department/Unit management
- Password reset & MFA configuration
- Hospital-level audit logs
- Location management
- Role assignments
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import secrets
import bcrypt
import os

hospital_admin_router = APIRouter(prefix="/api/hospital", tags=["Hospital Admin"])

# ============ Enums ============

class StaffRole(str, Enum):
    PHYSICIAN = "physician"
    NURSE = "nurse"
    SCHEDULER = "scheduler"
    BILLER = "biller"
    HOSPITAL_ADMIN = "hospital_admin"
    DEPARTMENT_HEAD = "department_head"
    RECEPTIONIST = "receptionist"
    LAB_TECH = "lab_tech"
    PHARMACIST = "pharmacist"

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class DepartmentType(str, Enum):
    CLINICAL = "clinical"
    ADMINISTRATIVE = "administrative"
    SUPPORT = "support"
    DIAGNOSTIC = "diagnostic"

# ============ Models ============

class StaffCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: StaffRole
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    send_welcome_email: bool = True

class StaffUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[StaffRole] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    is_active: Optional[bool] = None

class DepartmentCreate(BaseModel):
    name: str
    code: str
    department_type: DepartmentType = DepartmentType.CLINICAL
    description: Optional[str] = None
    location_id: Optional[str] = None
    head_user_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class UnitCreate(BaseModel):
    name: str
    code: str
    department_id: str
    description: Optional[str] = None
    bed_count: Optional[int] = None
    floor: Optional[str] = None

class PasswordResetRequest(BaseModel):
    user_id: str
    send_email: bool = True

class MFAConfigRequest(BaseModel):
    user_id: str
    require_mfa: bool

# ============ API Factory ============

def create_hospital_admin_endpoints(db, get_current_user, hash_password):
    """Create hospital admin API endpoints"""
    
    JWT_SECRET = os.environ.get('JWT_SECRET', 'yacco-emr-secret-key-2024')
    
    def verify_hospital_admin(user: dict, hospital_id: str):
        """Verify user is admin for this hospital"""
        if user.get("role") == "super_admin":
            return True
        if user.get("role") not in ["hospital_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Hospital Admin access required")
        if user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        return True
    
    async def log_admin_action(user: dict, hospital_id: str, action: str, resource_type: str, 
                               resource_id: str, details: dict = None):
        """Log administrative action for audit"""
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": action,
            "user_id": user["id"],
            "user_email": user.get("email"),
            "organization_id": hospital_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": None,
            "severity": "medium",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # ============ Hospital Dashboard Stats ============
    
    @hospital_admin_router.get("/{hospital_id}/admin/dashboard")
    async def get_hospital_admin_dashboard(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get hospital admin dashboard overview"""
        verify_hospital_admin(user, hospital_id)
        
        # Get hospital info
        hospital = await db["hospitals"].find_one({"id": hospital_id}, {"_id": 0})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Get counts
        total_users = await db["users"].count_documents({
            "organization_id": hospital_id, "is_active": True
        })
        total_departments = await db["departments"].count_documents({
            "organization_id": hospital_id, "is_active": True
        })
        total_locations = await db["hospital_locations"].count_documents({
            "hospital_id": hospital_id, "is_active": True
        })
        pending_users = await db["users"].count_documents({
            "organization_id": hospital_id, "status": "pending"
        })
        
        # Get users by role
        role_distribution = await db["users"].aggregate([
            {"$match": {"organization_id": hospital_id, "is_active": True}},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]).to_list(20)
        
        # Get recent activity
        recent_logins = await db["audit_logs"].find({
            "organization_id": hospital_id,
            "action": "login"
        }).sort("timestamp", -1).limit(10).to_list(10)
        
        # Get departments
        departments = await db["departments"].find({
            "organization_id": hospital_id, "is_active": True
        }, {"_id": 0}).to_list(50)
        
        return {
            "hospital": {
                "id": hospital["id"],
                "name": hospital["name"],
                "region_id": hospital.get("region_id"),
                "city": hospital.get("city"),
                "status": hospital.get("status")
            },
            "stats": {
                "total_users": total_users,
                "total_departments": total_departments,
                "total_locations": total_locations,
                "pending_users": pending_users
            },
            "role_distribution": {r["_id"]: r["count"] for r in role_distribution},
            "departments": departments,
            "recent_activity": recent_logins
        }
    
    # ============ User Management ============
    
    @hospital_admin_router.get("/{hospital_id}/admin/users")
    async def list_hospital_users(
        hospital_id: str,
        role: Optional[str] = None,
        department_id: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        user: dict = Depends(get_current_user)
    ):
        """List all users in the hospital with filters"""
        verify_hospital_admin(user, hospital_id)
        
        query = {"organization_id": hospital_id}
        
        if role:
            query["role"] = role
        if department_id:
            query["department_id"] = department_id
        if location_id:
            query["location_id"] = location_id
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}}
            ]
        
        total = await db["users"].count_documents(query)
        skip = (page - 1) * limit
        
        users = await db["users"].find(
            query, 
            {"_id": 0, "password": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Enrich with department names
        for u in users:
            if u.get("department_id"):
                dept = await db["departments"].find_one(
                    {"id": u["department_id"]}, {"_id": 0, "name": 1}
                )
                u["department_name"] = dept["name"] if dept else None
            if u.get("location_id"):
                loc = await db["hospital_locations"].find_one(
                    {"id": u["location_id"]}, {"_id": 0, "name": 1}
                )
                u["location_name"] = loc["name"] if loc else None
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    @hospital_admin_router.post("/{hospital_id}/admin/users")
    async def create_hospital_user(
        hospital_id: str,
        staff: StaffCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new staff user"""
        verify_hospital_admin(user, hospital_id)
        
        # Check email uniqueness
        existing = await db["users"].find_one({"email": staff.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate department if provided
        if staff.department_id:
            dept = await db["departments"].find_one({
                "id": staff.department_id, "organization_id": hospital_id
            })
            if not dept:
                raise HTTPException(status_code=404, detail="Department not found")
        
        # Validate location if provided
        if staff.location_id:
            loc = await db["hospital_locations"].find_one({
                "id": staff.location_id, "hospital_id": hospital_id
            })
            if not loc:
                raise HTTPException(status_code=404, detail="Location not found")
        
        # Generate temp password
        temp_password = secrets.token_urlsafe(12)
        
        new_user = {
            "id": str(uuid.uuid4()),
            "email": staff.email,
            "first_name": staff.first_name,
            "last_name": staff.last_name,
            "role": staff.role.value,
            "department_id": staff.department_id,
            "location_id": staff.location_id,
            "organization_id": hospital_id,
            "phone": staff.phone,
            "specialty": staff.specialty,
            "license_number": staff.license_number,
            "password": hash_password(temp_password),
            "status": "active",
            "is_active": True,
            "is_temp_password": True,
            "mfa_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        
        await db["users"].insert_one(new_user)
        
        # Log action
        await log_admin_action(
            user, hospital_id, "create_user", "user", new_user["id"],
            {"email": staff.email, "role": staff.role.value}
        )
        
        # Update counts
        await db["hospitals"].update_one(
            {"id": hospital_id}, {"$inc": {"total_users": 1}}
        )
        
        return {
            "message": "User created successfully",
            "user": {
                "id": new_user["id"],
                "email": new_user["email"],
                "name": f"{new_user['first_name']} {new_user['last_name']}",
                "role": new_user["role"]
            },
            "credentials": {
                "temp_password": temp_password,
                "must_change": True
            }
        }
    
    @hospital_admin_router.get("/{hospital_id}/admin/users/{user_id}")
    async def get_hospital_user(
        hospital_id: str,
        user_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get detailed user information"""
        verify_hospital_admin(user, hospital_id)
        
        staff = await db["users"].find_one(
            {"id": user_id, "organization_id": hospital_id},
            {"_id": 0, "password": 0}
        )
        
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get department and location names
        if staff.get("department_id"):
            dept = await db["departments"].find_one({"id": staff["department_id"]})
            staff["department"] = dept
        if staff.get("location_id"):
            loc = await db["hospital_locations"].find_one({"id": staff["location_id"]})
            staff["location"] = loc
        
        # Get recent activity
        activity = await db["audit_logs"].find({
            "user_id": user_id
        }).sort("timestamp", -1).limit(20).to_list(20)
        staff["recent_activity"] = activity
        
        return staff
    
    @hospital_admin_router.put("/{hospital_id}/admin/users/{user_id}")
    async def update_hospital_user(
        hospital_id: str,
        user_id: str,
        updates: StaffUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update user information"""
        verify_hospital_admin(user, hospital_id)
        
        # Verify user exists
        staff = await db["users"].find_one({
            "id": user_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update dict
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["updated_by"] = user["id"]
        
        await db["users"].update_one(
            {"id": user_id}, {"$set": update_data}
        )
        
        # Log action
        await log_admin_action(
            user, hospital_id, "update_user", "user", user_id,
            {"updates": list(update_data.keys())}
        )
        
        return {"message": "User updated successfully"}
    
    @hospital_admin_router.delete("/{hospital_id}/admin/users/{user_id}")
    async def deactivate_hospital_user(
        hospital_id: str,
        user_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate a user (soft delete)"""
        verify_hospital_admin(user, hospital_id)
        
        # Prevent self-deactivation
        if user_id == user["id"]:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
        staff = await db["users"].find_one({
            "id": user_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db["users"].update_one(
            {"id": user_id},
            {"$set": {
                "is_active": False,
                "status": "inactive",
                "deactivated_at": datetime.now(timezone.utc).isoformat(),
                "deactivated_by": user["id"]
            }}
        )
        
        # Log action
        await log_admin_action(
            user, hospital_id, "deactivate_user", "user", user_id,
            {"email": staff["email"]}
        )
        
        return {"message": "User deactivated"}
    
    @hospital_admin_router.post("/{hospital_id}/admin/users/{user_id}/reactivate")
    async def reactivate_hospital_user(
        hospital_id: str,
        user_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Reactivate a deactivated user"""
        verify_hospital_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": user_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db["users"].update_one(
            {"id": user_id},
            {"$set": {
                "is_active": True,
                "status": "active",
                "reactivated_at": datetime.now(timezone.utc).isoformat(),
                "reactivated_by": user["id"]
            }}
        )
        
        await log_admin_action(
            user, hospital_id, "reactivate_user", "user", user_id,
            {"email": staff["email"]}
        )
        
        return {"message": "User reactivated"}
    
    # ============ Password & Security Management ============
    
    @hospital_admin_router.post("/{hospital_id}/admin/users/{user_id}/reset-password")
    async def reset_user_password(
        hospital_id: str,
        user_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Reset user password and generate temporary password"""
        verify_hospital_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": user_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        temp_password = secrets.token_urlsafe(12)
        
        await db["users"].update_one(
            {"id": user_id},
            {"$set": {
                "password": hash_password(temp_password),
                "is_temp_password": True,
                "password_reset_at": datetime.now(timezone.utc).isoformat(),
                "password_reset_by": user["id"]
            }}
        )
        
        await log_admin_action(
            user, hospital_id, "reset_password", "user", user_id,
            {"email": staff["email"]}
        )
        
        return {
            "message": "Password reset successfully",
            "temp_password": temp_password,
            "note": "User must change password on next login"
        }
    
    @hospital_admin_router.post("/{hospital_id}/admin/users/{user_id}/mfa")
    async def configure_user_mfa(
        hospital_id: str,
        user_id: str,
        require_mfa: bool = Body(..., embed=True),
        user: dict = Depends(get_current_user)
    ):
        """Enable or require MFA for a user"""
        verify_hospital_admin(user, hospital_id)
        
        staff = await db["users"].find_one({
            "id": user_id, "organization_id": hospital_id
        })
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db["users"].update_one(
            {"id": user_id},
            {"$set": {"mfa_required": require_mfa}}
        )
        
        await log_admin_action(
            user, hospital_id, "configure_mfa", "user", user_id,
            {"mfa_required": require_mfa}
        )
        
        return {"message": f"MFA {'required' if require_mfa else 'optional'} for user"}
    
    # ============ Department Management ============
    
    @hospital_admin_router.get("/{hospital_id}/admin/departments")
    async def list_departments(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """List all departments"""
        verify_hospital_admin(user, hospital_id)
        
        departments = await db["departments"].find(
            {"organization_id": hospital_id},
            {"_id": 0}
        ).sort("name", 1).to_list(100)
        
        # Get user counts per department
        for dept in departments:
            dept["user_count"] = await db["users"].count_documents({
                "organization_id": hospital_id,
                "department_id": dept["id"],
                "is_active": True
            })
            # Get department head
            if dept.get("head_user_id"):
                head = await db["users"].find_one(
                    {"id": dept["head_user_id"]},
                    {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
                )
                dept["head"] = head
        
        return {"departments": departments, "total": len(departments)}
    
    @hospital_admin_router.post("/{hospital_id}/admin/departments")
    async def create_department(
        hospital_id: str,
        dept: DepartmentCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new department"""
        verify_hospital_admin(user, hospital_id)
        
        # Check code uniqueness
        existing = await db["departments"].find_one({
            "organization_id": hospital_id, "code": dept.code
        })
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists")
        
        new_dept = {
            "id": str(uuid.uuid4()),
            "organization_id": hospital_id,
            **dept.model_dump(),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        
        await db["departments"].insert_one(new_dept)
        
        await log_admin_action(
            user, hospital_id, "create_department", "department", new_dept["id"],
            {"name": dept.name, "code": dept.code}
        )
        
        if "_id" in new_dept:
            del new_dept["_id"]
        return {"message": "Department created", "department": new_dept}
    
    @hospital_admin_router.put("/{hospital_id}/admin/departments/{dept_id}")
    async def update_department(
        hospital_id: str,
        dept_id: str,
        updates: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update department"""
        verify_hospital_admin(user, hospital_id)
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db["departments"].update_one(
            {"id": dept_id, "organization_id": hospital_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Department not found")
        
        await log_admin_action(
            user, hospital_id, "update_department", "department", dept_id,
            {"updates": list(updates.keys())}
        )
        
        return {"message": "Department updated"}
    
    @hospital_admin_router.delete("/{hospital_id}/admin/departments/{dept_id}")
    async def deactivate_department(
        hospital_id: str,
        dept_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate department"""
        verify_hospital_admin(user, hospital_id)
        
        # Check if department has users
        user_count = await db["users"].count_documents({
            "department_id": dept_id, "is_active": True
        })
        if user_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot deactivate department with {user_count} active users"
            )
        
        await db["departments"].update_one(
            {"id": dept_id, "organization_id": hospital_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        await log_admin_action(
            user, hospital_id, "deactivate_department", "department", dept_id, {}
        )
        
        return {"message": "Department deactivated"}
    
    # ============ Unit Management ============
    
    @hospital_admin_router.get("/{hospital_id}/admin/units")
    async def list_units(
        hospital_id: str,
        department_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """List all units"""
        verify_hospital_admin(user, hospital_id)
        
        query = {"organization_id": hospital_id}
        if department_id:
            query["department_id"] = department_id
        
        units = await db["units"].find(query, {"_id": 0}).sort("name", 1).to_list(200)
        
        return {"units": units, "total": len(units)}
    
    @hospital_admin_router.post("/{hospital_id}/admin/units")
    async def create_unit(
        hospital_id: str,
        unit: UnitCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new unit"""
        verify_hospital_admin(user, hospital_id)
        
        # Validate department
        dept = await db["departments"].find_one({
            "id": unit.department_id, "organization_id": hospital_id
        })
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        
        new_unit = {
            "id": str(uuid.uuid4()),
            "organization_id": hospital_id,
            **unit.model_dump(),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["units"].insert_one(new_unit)
        
        await log_admin_action(
            user, hospital_id, "create_unit", "unit", new_unit["id"],
            {"name": unit.name, "department_id": unit.department_id}
        )
        
        return {"message": "Unit created", "unit": new_unit}
    
    # ============ Audit Logs ============
    
    @hospital_admin_router.get("/{hospital_id}/admin/audit-logs")
    async def get_hospital_audit_logs(
        hospital_id: str,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        days: int = 30,
        page: int = 1,
        limit: int = 50,
        user: dict = Depends(get_current_user)
    ):
        """Get hospital-level audit logs"""
        verify_hospital_admin(user, hospital_id)
        
        query = {"organization_id": hospital_id}
        
        # Filter by date
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        query["timestamp"] = {"$gte": start_date.isoformat()}
        
        if action:
            query["action"] = action
        if user_id:
            query["user_id"] = user_id
        if resource_type:
            query["resource_type"] = resource_type
        
        total = await db["audit_logs"].count_documents(query)
        skip = (page - 1) * limit
        
        logs = await db["audit_logs"].find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    # ============ Hospital Settings ============
    
    @hospital_admin_router.get("/{hospital_id}/admin/settings")
    async def get_hospital_settings(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get hospital settings"""
        verify_hospital_admin(user, hospital_id)
        
        hospital = await db["hospitals"].find_one(
            {"id": hospital_id},
            {"_id": 0, "admin_password": 0}
        )
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Get locations
        locations = await db["hospital_locations"].find(
            {"hospital_id": hospital_id},
            {"_id": 0}
        ).to_list(50)
        
        hospital["locations"] = locations
        
        return hospital
    
    @hospital_admin_router.put("/{hospital_id}/admin/settings")
    async def update_hospital_settings(
        hospital_id: str,
        updates: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update hospital settings"""
        verify_hospital_admin(user, hospital_id)
        
        # Prevent updating sensitive fields
        protected = ["id", "status", "created_at", "approved_at"]
        for field in protected:
            updates.pop(field, None)
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        updates["updated_by"] = user["id"]
        
        await db["hospitals"].update_one(
            {"id": hospital_id},
            {"$set": updates}
        )
        
        await log_admin_action(
            user, hospital_id, "update_settings", "hospital", hospital_id,
            {"updates": list(updates.keys())}
        )
        
        return {"message": "Settings updated"}
    
    return hospital_admin_router


# Export
__all__ = ["hospital_admin_router", "create_hospital_admin_endpoints"]
