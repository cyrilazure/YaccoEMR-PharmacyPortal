"""
Department Management Module for Yacco EMR
Supports hospital departments and units with hierarchical structure
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

department_router = APIRouter(prefix="/api/departments", tags=["Departments"])


# ============ Enums ============

class DepartmentType(str, Enum):
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    ICU = "icu"
    NICU = "nicu"
    PICU = "picu"
    CCU = "ccu"
    SURGERY = "surgery"
    PEDIATRICS = "pediatrics"
    OBSTETRICS = "obstetrics"
    GYNECOLOGY = "gynecology"
    CARDIOLOGY = "cardiology"
    ONCOLOGY = "oncology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    RADIOLOGY = "radiology"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    PATHOLOGY = "pathology"
    PSYCHIATRY = "psychiatry"
    DERMATOLOGY = "dermatology"
    OPHTHALMOLOGY = "ophthalmology"
    ENT = "ent"
    UROLOGY = "urology"
    NEPHROLOGY = "nephrology"
    PULMONOLOGY = "pulmonology"
    GASTROENTEROLOGY = "gastroenterology"
    ENDOCRINOLOGY = "endocrinology"
    RHEUMATOLOGY = "rheumatology"
    INFECTIOUS_DISEASE = "infectious_disease"
    REHABILITATION = "rehabilitation"
    PHYSICAL_THERAPY = "physical_therapy"
    ADMINISTRATION = "administration"
    BILLING = "billing"
    MEDICAL_RECORDS = "medical_records"
    OTHER = "other"


# ============ Models ============

class DepartmentCreate(BaseModel):
    name: str
    code: str
    department_type: DepartmentType
    description: Optional[str] = None
    parent_department_id: Optional[str] = None
    phone: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    bed_count: Optional[int] = None
    max_patients: Optional[int] = None
    is_24_7: bool = False
    operating_hours: Optional[Dict[str, str]] = None
    head_user_id: Optional[str] = None
    cost_center_code: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department_type: Optional[DepartmentType] = None
    description: Optional[str] = None
    parent_department_id: Optional[str] = None
    phone: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    bed_count: Optional[int] = None
    max_patients: Optional[int] = None
    is_24_7: Optional[bool] = None
    operating_hours: Optional[Dict[str, str]] = None
    head_user_id: Optional[str] = None
    cost_center_code: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    code: str
    department_type: str
    description: Optional[str]
    parent_department_id: Optional[str]
    phone: Optional[str]
    extension: Optional[str]
    email: Optional[str]
    location: Optional[str]
    bed_count: Optional[int]
    max_patients: Optional[int]
    is_24_7: bool
    operating_hours: Optional[Dict[str, str]]
    head_user_id: Optional[str]
    head_user_name: Optional[str] = None
    cost_center_code: Optional[str]
    is_active: bool
    staff_count: int = 0
    created_at: str
    updated_at: str


class DepartmentStatsResponse(BaseModel):
    total_departments: int
    active_departments: int
    total_staff: int
    total_beds: int
    departments_by_type: Dict[str, int]


# ============ Endpoints ============

def create_department_endpoints(db, get_current_user):
    """Create department management endpoints"""
    
    @department_router.get("/types")
    async def get_department_types():
        """Get list of all department types"""
        return [
            {"value": dt.value, "name": dt.name.replace("_", " ").title()}
            for dt in DepartmentType
        ]
    
    @department_router.post("", response_model=DepartmentResponse)
    async def create_department(
        department_data: DepartmentCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new department (Hospital Admin only)"""
        if current_user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Hospital admin access required")
        
        org_id = current_user.get("organization_id")
        if not org_id and current_user.get("role") != "super_admin":
            raise HTTPException(status_code=400, detail="Organization ID required")
        
        # Check for duplicate code
        existing = await db.departments.find_one({
            "organization_id": org_id,
            "code": department_data.code
        })
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists")
        
        # Create department
        department = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            **department_data.model_dump(),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get("id")
        }
        
        await db.departments.insert_one(department)
        
        # Update organization stats
        await db.organizations.update_one(
            {"id": org_id},
            {"$inc": {"total_departments": 1}}
        )
        
        return DepartmentResponse(**department)
    
    @department_router.get("", response_model=List[DepartmentResponse])
    async def get_departments(
        department_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        parent_id: Optional[str] = None,
        search: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all departments for the organization"""
        org_id = current_user.get("organization_id")
        
        query = {}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        if department_type:
            query["department_type"] = department_type
        if is_active is not None:
            query["is_active"] = is_active
        if parent_id:
            query["parent_department_id"] = parent_id
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"code": {"$regex": search, "$options": "i"}}
            ]
        
        departments = await db.departments.find(query, {"_id": 0}).to_list(500)
        
        # Enrich with staff count and head user name
        for dept in departments:
            staff_count = await db.users.count_documents({
                "department_id": dept["id"],
                "is_active": True
            })
            dept["staff_count"] = staff_count
            
            if dept.get("head_user_id"):
                head_user = await db.users.find_one(
                    {"id": dept["head_user_id"]},
                    {"_id": 0, "first_name": 1, "last_name": 1}
                )
                if head_user:
                    dept["head_user_name"] = f"{head_user['first_name']} {head_user['last_name']}"
        
        return [DepartmentResponse(**d) for d in departments]
    
    @department_router.get("/hierarchy")
    async def get_department_hierarchy(
        current_user: dict = Depends(get_current_user)
    ):
        """Get departments in hierarchical structure"""
        org_id = current_user.get("organization_id")
        
        query = {"is_active": True}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        departments = await db.departments.find(query, {"_id": 0}).to_list(500)
        
        # Build hierarchy
        dept_map = {d["id"]: {**d, "children": []} for d in departments}
        root_departments = []
        
        for dept in departments:
            if dept.get("parent_department_id"):
                parent = dept_map.get(dept["parent_department_id"])
                if parent:
                    parent["children"].append(dept_map[dept["id"]])
            else:
                root_departments.append(dept_map[dept["id"]])
        
        return root_departments
    
    @department_router.get("/stats", response_model=DepartmentStatsResponse)
    async def get_department_stats(
        current_user: dict = Depends(get_current_user)
    ):
        """Get department statistics"""
        org_id = current_user.get("organization_id")
        
        query = {}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        total = await db.departments.count_documents(query)
        active = await db.departments.count_documents({**query, "is_active": True})
        
        # Staff count
        staff_query = {}
        if org_id:
            staff_query["organization_id"] = org_id
        total_staff = await db.users.count_documents({**staff_query, "department_id": {"$exists": True, "$ne": None}})
        
        # Total beds
        pipeline = [
            {"$match": {**query, "bed_count": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": None, "total_beds": {"$sum": "$bed_count"}}}
        ]
        beds_result = await db.departments.aggregate(pipeline).to_list(1)
        total_beds = beds_result[0]["total_beds"] if beds_result else 0
        
        # By type
        type_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$department_type", "count": {"$sum": 1}}}
        ]
        type_results = await db.departments.aggregate(type_pipeline).to_list(50)
        departments_by_type = {r["_id"]: r["count"] for r in type_results}
        
        return DepartmentStatsResponse(
            total_departments=total,
            active_departments=active,
            total_staff=total_staff,
            total_beds=total_beds,
            departments_by_type=departments_by_type
        )
    
    @department_router.get("/{department_id}", response_model=DepartmentResponse)
    async def get_department(
        department_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get a specific department"""
        query = {"id": department_id}
        org_id = current_user.get("organization_id")
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        department = await db.departments.find_one(query, {"_id": 0})
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Add staff count
        staff_count = await db.users.count_documents({
            "department_id": department_id,
            "is_active": True
        })
        department["staff_count"] = staff_count
        
        # Add head user name
        if department.get("head_user_id"):
            head_user = await db.users.find_one(
                {"id": department["head_user_id"]},
                {"_id": 0, "first_name": 1, "last_name": 1}
            )
            if head_user:
                department["head_user_name"] = f"{head_user['first_name']} {head_user['last_name']}"
        
        return DepartmentResponse(**department)
    
    @department_router.put("/{department_id}", response_model=DepartmentResponse)
    async def update_department(
        department_id: str,
        update_data: DepartmentUpdate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update a department (Hospital Admin only)"""
        if current_user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Hospital admin access required")
        
        query = {"id": department_id}
        org_id = current_user.get("organization_id")
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        department = await db.departments.find_one(query)
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Check for duplicate code if changing
        if update_data.code and update_data.code != department.get("code"):
            existing = await db.departments.find_one({
                "organization_id": org_id,
                "code": update_data.code,
                "id": {"$ne": department_id}
            })
            if existing:
                raise HTTPException(status_code=400, detail="Department code already exists")
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_dict["updated_by"] = current_user.get("id")
        
        await db.departments.update_one(
            {"id": department_id},
            {"$set": update_dict}
        )
        
        updated = await db.departments.find_one({"id": department_id}, {"_id": 0})
        return DepartmentResponse(**updated)
    
    @department_router.delete("/{department_id}")
    async def delete_department(
        department_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Deactivate a department (Hospital Admin only)"""
        if current_user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Hospital admin access required")
        
        query = {"id": department_id}
        org_id = current_user.get("organization_id")
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        department = await db.departments.find_one(query)
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Check if department has staff
        staff_count = await db.users.count_documents({"department_id": department_id})
        if staff_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete department with {staff_count} assigned staff. Reassign staff first."
            )
        
        # Check for child departments
        children = await db.departments.count_documents({"parent_department_id": department_id})
        if children > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete department with {children} sub-departments. Remove sub-departments first."
            )
        
        # Soft delete (deactivate)
        await db.departments.update_one(
            {"id": department_id},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": current_user.get("id")
            }}
        )
        
        # Update organization stats
        await db.organizations.update_one(
            {"id": org_id},
            {"$inc": {"total_departments": -1}}
        )
        
        return {"message": "Department deactivated successfully"}
    
    @department_router.get("/{department_id}/staff")
    async def get_department_staff(
        department_id: str,
        role: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get staff assigned to a department"""
        query = {"department_id": department_id, "is_active": True}
        
        if role:
            query["role"] = role
        
        staff = await db.users.find(
            query, 
            {"_id": 0, "password": 0, "password_hash": 0}
        ).to_list(500)
        
        return staff
    
    @department_router.post("/{department_id}/assign-staff")
    async def assign_staff_to_department(
        department_id: str,
        user_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Assign a staff member to a department"""
        if current_user.get("role") not in ["hospital_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Verify department exists
        department = await db.departments.find_one({"id": department_id})
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Verify user exists
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user's department
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "department_id": department_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": f"User assigned to {department['name']} department"}
    
    return department_router


# Export
__all__ = [
    'department_router',
    'create_department_endpoints',
    'DepartmentType',
    'DepartmentCreate',
    'DepartmentUpdate',
    'DepartmentResponse'
]
