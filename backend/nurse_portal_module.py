"""
Nurse Portal Module for Yacco EMR
Comprehensive nurse workflow management with:
- Patient assignments
- Shift-based visibility
- Task management
- Medication administration record (MAR)
- Role-limited access controls
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta, time
from enum import Enum
import uuid

nurse_router = APIRouter(prefix="/api/nurse", tags=["Nurse Portal"])


# ============ Enums ============

class ShiftType(str, Enum):
    MORNING = "morning"      # 7:00 AM - 3:00 PM
    EVENING = "evening"      # 3:00 PM - 11:00 PM
    NIGHT = "night"          # 11:00 PM - 7:00 AM
    DAY_12 = "day_12"        # 7:00 AM - 7:00 PM (12-hour day)
    NIGHT_12 = "night_12"    # 7:00 PM - 7:00 AM (12-hour night)


class TaskType(str, Enum):
    VITALS_DUE = "vitals_due"
    MEDICATION_DUE = "medication_due"
    ASSESSMENT_DUE = "assessment_due"
    ORDER_ACKNOWLEDGEMENT = "order_acknowledgement"
    WOUND_CARE = "wound_care"
    PATIENT_EDUCATION = "patient_education"
    DISCHARGE_PREP = "discharge_prep"
    LAB_COLLECTION = "lab_collection"
    IV_CHECK = "iv_check"
    PAIN_ASSESSMENT = "pain_assessment"
    FALL_RISK_ASSESSMENT = "fall_risk_assessment"
    INTAKE_OUTPUT = "intake_output"
    CUSTOM = "custom"


class TaskPriority(str, Enum):
    STAT = "stat"            # Immediate
    URGENT = "urgent"        # Within 30 minutes
    HIGH = "high"            # Within 1 hour
    ROUTINE = "routine"      # Within shift
    LOW = "low"              # When possible


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class MARStatus(str, Enum):
    SCHEDULED = "scheduled"
    GIVEN = "given"
    HELD = "held"
    REFUSED = "refused"
    NOT_GIVEN = "not_given"
    SELF_ADMINISTERED = "self_administered"


# ============ Models ============

class ShiftDefinition(BaseModel):
    shift_type: ShiftType
    name: str
    start_hour: int
    start_minute: int = 0
    end_hour: int
    end_minute: int = 0
    duration_hours: int


class ShiftClockIn(BaseModel):
    shift_type: ShiftType
    department_id: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class ShiftRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nurse_id: str
    nurse_name: str
    organization_id: str
    shift_type: ShiftType
    department_id: Optional[str] = None
    unit: Optional[str] = None
    clock_in_time: str
    clock_out_time: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None
    handoff_notes: Optional[str] = None
    patient_count: int = 0


class PatientAssignmentCreate(BaseModel):
    patient_id: str
    nurse_id: str
    shift_type: Optional[ShiftType] = None
    department_id: Optional[str] = None
    notes: Optional[str] = None
    is_primary: bool = True


class PatientAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_mrn: str
    nurse_id: str
    nurse_name: str
    organization_id: str
    shift_type: Optional[ShiftType] = None
    department_id: Optional[str] = None
    room_bed: Optional[str] = None
    acuity_level: int = 2  # 1-5, higher = sicker
    is_primary: bool = True
    is_active: bool = True
    assigned_at: str
    assigned_by: str
    notes: Optional[str] = None


class TaskCreate(BaseModel):
    patient_id: str
    task_type: TaskType
    description: str
    priority: TaskPriority = TaskPriority.ROUTINE
    due_time: Optional[str] = None
    notes: Optional[str] = None
    related_order_id: Optional[str] = None
    related_medication_id: Optional[str] = None


class NurseTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_mrn: str
    room_bed: Optional[str] = None
    nurse_id: str
    organization_id: str
    task_type: TaskType
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    due_time: str
    completed_time: Optional[str] = None
    completed_by: Optional[str] = None
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    related_order_id: Optional[str] = None
    related_medication_id: Optional[str] = None
    created_at: str
    created_by: str


class MAREntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    medication_id: str
    medication_name: str
    dosage: str
    route: str
    frequency: str
    scheduled_time: str
    status: MARStatus = MARStatus.SCHEDULED
    actual_time: Optional[str] = None
    administered_by: Optional[str] = None
    administered_by_name: Optional[str] = None
    witness_id: Optional[str] = None
    witness_name: Optional[str] = None
    notes: Optional[str] = None
    held_reason: Optional[str] = None
    refused_reason: Optional[str] = None
    organization_id: str
    created_at: str


class MARAdminister(BaseModel):
    mar_entry_id: str
    status: MARStatus
    notes: Optional[str] = None
    held_reason: Optional[str] = None
    refused_reason: Optional[str] = None
    witness_id: Optional[str] = None  # For controlled substances


class HandoffNotes(BaseModel):
    patient_id: str
    notes: str
    critical_info: Optional[str] = None
    pending_tasks: Optional[List[str]] = None
    abnormal_findings: Optional[str] = None


# ============ Shift Definitions ============

SHIFT_DEFINITIONS: Dict[ShiftType, ShiftDefinition] = {
    ShiftType.MORNING: ShiftDefinition(
        shift_type=ShiftType.MORNING,
        name="Morning Shift (7AM-3PM)",
        start_hour=7, end_hour=15, duration_hours=8
    ),
    ShiftType.EVENING: ShiftDefinition(
        shift_type=ShiftType.EVENING,
        name="Evening Shift (3PM-11PM)",
        start_hour=15, end_hour=23, duration_hours=8
    ),
    ShiftType.NIGHT: ShiftDefinition(
        shift_type=ShiftType.NIGHT,
        name="Night Shift (11PM-7AM)",
        start_hour=23, end_hour=7, duration_hours=8
    ),
    ShiftType.DAY_12: ShiftDefinition(
        shift_type=ShiftType.DAY_12,
        name="12-Hour Day Shift (7AM-7PM)",
        start_hour=7, end_hour=19, duration_hours=12
    ),
    ShiftType.NIGHT_12: ShiftDefinition(
        shift_type=ShiftType.NIGHT_12,
        name="12-Hour Night Shift (7PM-7AM)",
        start_hour=19, end_hour=7, duration_hours=12
    ),
}


# ============ Permission Definitions ============

NURSE_PERMISSIONS = {
    "allowed": [
        "patient:view",
        "patient:update",
        "vitals:view",
        "vitals:create",
        "note:view",
        "note:create",
        "note:update",
        "medication:view",
        "medication:administer",
        "order:view",
        "order:update_status",
        "lab:order_view",
        "lab:result_view",
        "imaging:view",
        "appointment:view",
        "telehealth:join",
        "cds:view",
        "report:view",
        "user:view",
    ],
    "denied": [
        "patient:create",
        "patient:delete",
        "medication:prescribe",
        "order:create",
        "order:cancel",
        "order:add_result",
        "lab:order_create",
        "lab:result_add",
        "imaging:order_create",
        "imaging:interpret",
        "appointment:create",
        "appointment:update",
        "appointment:cancel",
        "telehealth:create",
        "telehealth:manage",
        "prescription:create",
        "billing:create",
        "billing:update",
        "user:create",
        "user:update",
        "user:deactivate",
        "audit:view",
        "audit:export",
        "organization:update",
        "organization:manage",
        "cds:override",
        "system:config",
        "system:backup",
    ]
}


# ============ Helper Functions ============

def get_current_shift_type() -> ShiftType:
    """Determine current shift based on current time"""
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    
    if 7 <= current_hour < 15:
        return ShiftType.MORNING
    elif 15 <= current_hour < 23:
        return ShiftType.EVENING
    else:
        return ShiftType.NIGHT


def is_within_shift(shift_type: ShiftType, check_time: datetime = None) -> bool:
    """Check if a time falls within a shift"""
    if check_time is None:
        check_time = datetime.now(timezone.utc)
    
    hour = check_time.hour
    shift_def = SHIFT_DEFINITIONS[shift_type]
    
    if shift_def.start_hour < shift_def.end_hour:
        return shift_def.start_hour <= hour < shift_def.end_hour
    else:  # Night shift crosses midnight
        return hour >= shift_def.start_hour or hour < shift_def.end_hour


# ============ Endpoints ============

def create_nurse_portal_endpoints(db, get_current_user):
    """Create nurse portal endpoints with database and auth dependency"""
    
    def require_nurse_role(user: dict) -> dict:
        """Verify user has nurse role"""
        if user.get("role") not in ["nurse", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Nurse access required")
        return user
    
    def require_charge_nurse_or_admin(user: dict) -> dict:
        """Verify user can manage assignments"""
        # In real implementation, would check for charge nurse flag
        if user.get("role") not in ["nurse", "hospital_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Charge nurse or admin access required")
        return user
    
    # ============ Shift Endpoints ============
    
    @nurse_router.get("/shifts")
    async def get_shift_definitions():
        """Get all shift type definitions"""
        return [
            {
                "shift_type": s.shift_type.value,
                "name": s.name,
                "start_hour": s.start_hour,
                "end_hour": s.end_hour,
                "duration_hours": s.duration_hours
            }
            for s in SHIFT_DEFINITIONS.values()
        ]
    
    @nurse_router.get("/current-shift")
    async def get_current_shift(current_user: dict = Depends(get_current_user)):
        """Get current user's active shift"""
        require_nurse_role(current_user)
        
        # Find active shift record for this nurse
        active_shift = await db.nurse_shifts.find_one({
            "nurse_id": current_user["id"],
            "is_active": True
        }, {"_id": 0})
        
        current_shift_type = get_current_shift_type()
        
        return {
            "current_time_shift": current_shift_type.value,
            "active_shift": active_shift,
            "shift_info": {
                "shift_type": current_shift_type.value,
                "name": SHIFT_DEFINITIONS[current_shift_type].name,
                "start_hour": SHIFT_DEFINITIONS[current_shift_type].start_hour,
                "end_hour": SHIFT_DEFINITIONS[current_shift_type].end_hour
            }
        }
    
    @nurse_router.post("/shifts/clock-in")
    async def clock_in_shift(
        shift_data: ShiftClockIn,
        current_user: dict = Depends(get_current_user)
    ):
        """Clock in to a shift"""
        require_nurse_role(current_user)
        
        # Check if already clocked in
        existing_shift = await db.nurse_shifts.find_one({
            "nurse_id": current_user["id"],
            "is_active": True
        })
        
        if existing_shift:
            raise HTTPException(
                status_code=400, 
                detail="Already clocked in. Please clock out first."
            )
        
        now = datetime.now(timezone.utc)
        shift_record = ShiftRecord(
            nurse_id=current_user["id"],
            nurse_name=f"{current_user['first_name']} {current_user['last_name']}",
            organization_id=current_user.get("organization_id", ""),
            shift_type=shift_data.shift_type,
            department_id=shift_data.department_id,
            unit=shift_data.unit,
            clock_in_time=now.isoformat(),
            notes=shift_data.notes
        )
        
        shift_dict = shift_record.model_dump(mode='json')  # Convert enums to values
        await db.nurse_shifts.insert_one(shift_dict)
        if "_id" in shift_dict: del shift_dict["_id"]
        
        return {
            "message": "Successfully clocked in",
            "shift": shift_dict
        }
    
    @nurse_router.post("/shifts/clock-out")
    async def clock_out_shift(
        handoff_notes: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Clock out of current shift"""
        require_nurse_role(current_user)
        
        # Find active shift
        active_shift = await db.nurse_shifts.find_one({
            "nurse_id": current_user["id"],
            "is_active": True
        })
        
        if not active_shift:
            raise HTTPException(status_code=400, detail="No active shift found")
        
        now = datetime.now(timezone.utc)
        
        # Calculate patient count
        patient_count = await db.nurse_assignments.count_documents({
            "nurse_id": current_user["id"],
            "is_active": True
        })
        
        await db.nurse_shifts.update_one(
            {"id": active_shift["id"]},
            {"$set": {
                "clock_out_time": now.isoformat(),
                "is_active": False,
                "handoff_notes": handoff_notes,
                "patient_count": patient_count
            }}
        )
        
        return {
            "message": "Successfully clocked out",
            "shift_duration": "Shift ended",
            "patient_count": patient_count
        }
    
    @nurse_router.get("/shifts/handoff-notes")
    async def get_handoff_notes(
        department_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get handoff notes from previous shift"""
        require_nurse_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Get recent completed shifts with handoff notes
        query = {
            "organization_id": org_id,
            "is_active": False,
            "handoff_notes": {"$ne": None}
        }
        if department_id:
            query["department_id"] = department_id
        
        recent_shifts = await db.nurse_shifts.find(
            query,
            {"_id": 0}
        ).sort("clock_out_time", -1).limit(10).to_list(10)
        
        return {
            "handoff_notes": recent_shifts
        }
    
    # ============ Patient Assignment Endpoints ============
    
    @nurse_router.get("/my-patients")
    async def get_my_patients(
        shift_only: bool = True,
        include_vitals: bool = True,
        current_user: dict = Depends(get_current_user)
    ):
        """Get patients assigned to current nurse"""
        require_nurse_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Get assignments for this nurse
        query = {
            "nurse_id": current_user["id"],
            "is_active": True
        }
        if org_id:
            query["organization_id"] = org_id
        
        assignments = await db.nurse_assignments.find(
            query,
            {"_id": 0}
        ).to_list(100)
        
        # Enrich with latest patient data and vitals
        enriched_patients = []
        for assignment in assignments:
            patient = await db.patients.find_one(
                {"id": assignment["patient_id"]},
                {"_id": 0}
            )
            if patient:
                # Get latest vitals if requested
                latest_vitals = None
                if include_vitals:
                    vitals = await db.vitals.find(
                        {"patient_id": assignment["patient_id"]}
                    ).sort("recorded_at", -1).limit(1).to_list(1)
                    if vitals:
                        latest_vitals = vitals[0]
                        if "_id" in latest_vitals: del latest_vitals["_id"]
                
                # Get pending tasks count
                pending_tasks = await db.nurse_tasks.count_documents({
                    "patient_id": assignment["patient_id"],
                    "nurse_id": current_user["id"],
                    "status": {"$in": ["pending", "in_progress"]}
                })
                
                # Get pending medications count
                pending_meds = await db.medications.count_documents({
                    "patient_id": assignment["patient_id"],
                    "status": "active"
                })
                
                enriched_patients.append({
                    "assignment": assignment,
                    "patient": patient,
                    "latest_vitals": latest_vitals,
                    "pending_tasks_count": pending_tasks,
                    "active_medications_count": pending_meds,
                    "acuity_level": assignment.get("acuity_level", 2)
                })
        
        # Sort by acuity (higher first) then by name
        enriched_patients.sort(key=lambda x: (-x.get("acuity_level", 2), x["patient"]["last_name"]))
        
        return {
            "patients": enriched_patients,
            "total_count": len(enriched_patients),
            "current_shift": get_current_shift_type().value
        }
    
    @nurse_router.post("/assign-patient")
    async def assign_patient(
        assignment_data: PatientAssignmentCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Assign a patient to a nurse (charge nurse/admin only)"""
        require_charge_nurse_or_admin(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Verify patient exists
        patient = await db.patients.find_one({"id": assignment_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify nurse exists
        nurse = await db.users.find_one({
            "id": assignment_data.nurse_id,
            "role": "nurse"
        }, {"_id": 0})
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found")
        
        # Check if already assigned
        existing = await db.nurse_assignments.find_one({
            "patient_id": assignment_data.patient_id,
            "nurse_id": assignment_data.nurse_id,
            "is_active": True
        })
        if existing:
            raise HTTPException(status_code=400, detail="Patient already assigned to this nurse")
        
        # Create assignment
        now = datetime.now(timezone.utc)
        assignment = PatientAssignment(
            patient_id=assignment_data.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_mrn=patient.get("mrn", ""),
            nurse_id=assignment_data.nurse_id,
            nurse_name=f"{nurse['first_name']} {nurse['last_name']}",
            organization_id=org_id or "",
            shift_type=assignment_data.shift_type or get_current_shift_type(),
            department_id=assignment_data.department_id,
            is_primary=assignment_data.is_primary,
            assigned_at=now.isoformat(),
            assigned_by=f"{current_user['first_name']} {current_user['last_name']}",
            notes=assignment_data.notes
        )
        
        assignment_dict = assignment.model_dump(mode='json')
        await db.nurse_assignments.insert_one(assignment_dict)
        if "_id" in assignment_dict: del assignment_dict["_id"]
        
        # Create notification for the nurse
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": assignment_data.nurse_id,
            "type": "patient_assigned",
            "title": "New Patient Assignment",
            "message": f"You have been assigned to {patient['first_name']} {patient['last_name']} (MRN: {patient.get('mrn', 'N/A')})",
            "priority": "normal",
            "is_read": False,
            "created_at": now.isoformat()
        }
        await db.notifications.insert_one(notification)
        
        return {
            "message": "Patient assigned successfully",
            "assignment": assignment_dict
        }
    
    @nurse_router.delete("/unassign-patient/{patient_id}")
    async def unassign_patient(
        patient_id: str,
        nurse_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Unassign a patient from a nurse"""
        require_charge_nurse_or_admin(current_user)
        
        query = {
            "patient_id": patient_id,
            "is_active": True
        }
        if nurse_id:
            query["nurse_id"] = nurse_id
        else:
            query["nurse_id"] = current_user["id"]
        
        result = await db.nurse_assignments.update_one(
            query,
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return {"message": "Patient unassigned successfully"}
    
    @nurse_router.get("/patient-load")
    async def get_patient_load(
        department_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get patient load statistics for current shift"""
        require_nurse_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Count assignments per nurse
        pipeline = [
            {"$match": {
                "organization_id": org_id,
                "is_active": True
            }},
            {"$group": {
                "_id": "$nurse_id",
                "nurse_name": {"$first": "$nurse_name"},
                "patient_count": {"$sum": 1},
                "high_acuity_count": {
                    "$sum": {"$cond": [{"$gte": ["$acuity_level", 4]}, 1, 0]}
                }
            }},
            {"$sort": {"patient_count": -1}}
        ]
        
        if department_id:
            pipeline[0]["$match"]["department_id"] = department_id
        
        load_stats = await db.nurse_assignments.aggregate(pipeline).to_list(100)
        
        # Get current user's load
        my_load = await db.nurse_assignments.count_documents({
            "nurse_id": current_user["id"],
            "is_active": True
        })
        
        return {
            "my_patient_count": my_load,
            "staff_load": load_stats,
            "current_shift": get_current_shift_type().value
        }
    
    # ============ Task Management Endpoints ============
    
    @nurse_router.get("/tasks")
    async def get_nurse_tasks(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        patient_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get tasks for current nurse"""
        require_nurse_role(current_user)
        
        query = {
            "nurse_id": current_user["id"],
        }
        
        if status:
            query["status"] = status
        else:
            query["status"] = {"$in": ["pending", "in_progress"]}
        
        if priority:
            query["priority"] = priority
        
        if patient_id:
            query["patient_id"] = patient_id
        
        tasks = await db.nurse_tasks.find(query, {"_id": 0}).sort([
            ("priority", 1),  # STAT first
            ("due_time", 1)
        ]).to_list(200)
        
        # Group by priority
        priority_order = ["stat", "urgent", "high", "routine", "low"]
        grouped = {p: [] for p in priority_order}
        for task in tasks:
            p = task.get("priority", "routine")
            if p in grouped:
                grouped[p].append(task)
        
        return {
            "tasks": tasks,
            "by_priority": grouped,
            "total_count": len(tasks)
        }
    
    @nurse_router.get("/tasks/due")
    async def get_due_tasks(
        current_user: dict = Depends(get_current_user)
    ):
        """Get tasks due now or overdue"""
        require_nurse_role(current_user)
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Get overdue or due within next 30 minutes
        due_window = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        
        tasks = await db.nurse_tasks.find({
            "nurse_id": current_user["id"],
            "status": {"$in": ["pending", "in_progress"]},
            "due_time": {"$lte": due_window}
        }, {"_id": 0}).sort("due_time", 1).to_list(50)
        
        # Separate overdue vs upcoming
        overdue = []
        upcoming = []
        for task in tasks:
            if task["due_time"] < now:
                overdue.append(task)
            else:
                upcoming.append(task)
        
        return {
            "overdue": overdue,
            "upcoming_30min": upcoming,
            "total_due": len(tasks)
        }
    
    @nurse_router.post("/tasks")
    async def create_task(
        task_data: TaskCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new nursing task"""
        require_nurse_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Verify patient exists
        patient = await db.patients.find_one({"id": task_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        now = datetime.now(timezone.utc)
        due_time = task_data.due_time or now.isoformat()
        
        task = NurseTask(
            patient_id=task_data.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_mrn=patient.get("mrn", ""),
            nurse_id=current_user["id"],
            organization_id=org_id or "",
            task_type=task_data.task_type,
            description=task_data.description,
            priority=task_data.priority,
            due_time=due_time,
            notes=task_data.notes,
            related_order_id=task_data.related_order_id,
            related_medication_id=task_data.related_medication_id,
            created_at=now.isoformat(),
            created_by=f"{current_user['first_name']} {current_user['last_name']}"
        )
        
        task_dict = task.model_dump(mode='json')
        await db.nurse_tasks.insert_one(task_dict)
        if "_id" in task_dict: del task_dict["_id"]
        
        return task_dict
    
    @nurse_router.post("/tasks/{task_id}/complete")
    async def complete_task(
        task_id: str,
        completion_notes: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Mark a task as completed"""
        require_nurse_role(current_user)
        
        now = datetime.now(timezone.utc)
        
        result = await db.nurse_tasks.update_one(
            {"id": task_id, "nurse_id": current_user["id"]},
            {"$set": {
                "status": TaskStatus.COMPLETED.value,
                "completed_time": now.isoformat(),
                "completed_by": f"{current_user['first_name']} {current_user['last_name']}",
                "completion_notes": completion_notes
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Task not found or not assigned to you")
        
        return {"message": "Task completed successfully"}
    
    @nurse_router.post("/tasks/{task_id}/defer")
    async def defer_task(
        task_id: str,
        new_due_time: str,
        reason: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Defer a task to a later time"""
        require_nurse_role(current_user)
        
        result = await db.nurse_tasks.update_one(
            {"id": task_id, "nurse_id": current_user["id"]},
            {"$set": {
                "status": TaskStatus.DEFERRED.value,
                "due_time": new_due_time,
                "notes": f"Deferred: {reason}"
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Task not found or not assigned to you")
        
        return {"message": "Task deferred successfully"}
    
    # ============ Medication Administration Record (MAR) Endpoints ============
    
    @nurse_router.get("/mar/{patient_id}")
    async def get_mar(
        patient_id: str,
        date: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get Medication Administration Record for a patient"""
        require_nurse_role(current_user)
        
        # Verify nurse is assigned to this patient or is admin
        if current_user.get("role") == "nurse":
            assignment = await db.nurse_assignments.find_one({
                "patient_id": patient_id,
                "nurse_id": current_user["id"],
                "is_active": True
            })
            if not assignment:
                raise HTTPException(
                    status_code=403, 
                    detail="Access restricted: You are not assigned to this patient"
                )
        
        # Get active medications for patient
        medications = await db.medications.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).to_list(50)
        
        # Get MAR entries for today (or specified date)
        if date:
            target_date = date
        else:
            target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        mar_entries = await db.mar_entries.find({
            "patient_id": patient_id,
            "scheduled_time": {"$regex": f"^{target_date}"}
        }, {"_id": 0}).sort("scheduled_time", 1).to_list(200)
        
        # Get patient info
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        
        return {
            "patient": patient,
            "date": target_date,
            "medications": medications,
            "mar_entries": mar_entries,
            "summary": {
                "total_scheduled": len(mar_entries),
                "given": len([e for e in mar_entries if e.get("status") == "given"]),
                "pending": len([e for e in mar_entries if e.get("status") == "scheduled"]),
                "held": len([e for e in mar_entries if e.get("status") == "held"]),
                "refused": len([e for e in mar_entries if e.get("status") == "refused"])
            }
        }
    
    @nurse_router.post("/mar/administer")
    async def administer_medication(
        mar_data: MARAdminister,
        current_user: dict = Depends(get_current_user)
    ):
        """Record medication administration"""
        require_nurse_role(current_user)
        
        # Find the MAR entry
        mar_entry = await db.mar_entries.find_one({"id": mar_data.mar_entry_id}, {"_id": 0})
        if not mar_entry:
            raise HTTPException(status_code=404, detail="MAR entry not found")
        
        # Verify nurse is assigned to this patient
        if current_user.get("role") == "nurse":
            assignment = await db.nurse_assignments.find_one({
                "patient_id": mar_entry["patient_id"],
                "nurse_id": current_user["id"],
                "is_active": True
            })
            if not assignment:
                raise HTTPException(
                    status_code=403, 
                    detail="Access restricted: You are not assigned to this patient"
                )
        
        now = datetime.now(timezone.utc)
        
        update_data = {
            "status": mar_data.status.value,
            "actual_time": now.isoformat(),
            "administered_by": current_user["id"],
            "administered_by_name": f"{current_user['first_name']} {current_user['last_name']}",
            "notes": mar_data.notes
        }
        
        if mar_data.status == MARStatus.HELD:
            update_data["held_reason"] = mar_data.held_reason
        elif mar_data.status == MARStatus.REFUSED:
            update_data["refused_reason"] = mar_data.refused_reason
        
        if mar_data.witness_id:
            witness = await db.users.find_one({"id": mar_data.witness_id}, {"_id": 0})
            if witness:
                update_data["witness_id"] = mar_data.witness_id
                update_data["witness_name"] = f"{witness['first_name']} {witness['last_name']}"
        
        await db.mar_entries.update_one(
            {"id": mar_data.mar_entry_id},
            {"$set": update_data}
        )
        
        return {
            "message": f"Medication marked as {mar_data.status.value}",
            "entry_id": mar_data.mar_entry_id
        }
    
    @nurse_router.get("/mar/due")
    async def get_medications_due(
        window_minutes: int = 30,
        current_user: dict = Depends(get_current_user)
    ):
        """Get medications due for administration within time window"""
        require_nurse_role(current_user)
        
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(minutes=window_minutes)
        
        # Get assigned patient IDs
        assignments = await db.nurse_assignments.find({
            "nurse_id": current_user["id"],
            "is_active": True
        }, {"patient_id": 1}).to_list(100)
        
        patient_ids = [a["patient_id"] for a in assignments]
        
        if not patient_ids:
            return {"medications_due": [], "total": 0}
        
        # Find MAR entries due within window
        mar_entries = await db.mar_entries.find({
            "patient_id": {"$in": patient_ids},
            "status": "scheduled",
            "scheduled_time": {
                "$lte": window_end.isoformat(),
                "$gte": (now - timedelta(hours=2)).isoformat()  # Include 2 hours past due
            }
        }, {"_id": 0}).sort("scheduled_time", 1).to_list(100)
        
        # Separate overdue vs upcoming
        overdue = []
        upcoming = []
        now_iso = now.isoformat()
        
        for entry in mar_entries:
            if entry["scheduled_time"] < now_iso:
                entry["is_overdue"] = True
                overdue.append(entry)
            else:
                entry["is_overdue"] = False
                upcoming.append(entry)
        
        return {
            "overdue": overdue,
            "upcoming": upcoming,
            "total": len(mar_entries)
        }
    
    @nurse_router.post("/mar/generate-schedule")
    async def generate_mar_schedule(
        patient_id: str,
        date: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Generate MAR schedule for a patient based on active medications"""
        require_nurse_role(current_user)
        
        org_id = current_user.get("organization_id")
        target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Get active medications
        medications = await db.medications.find({
            "patient_id": patient_id,
            "status": "active"
        }, {"_id": 0}).to_list(50)
        
        if not medications:
            return {"message": "No active medications found", "entries_created": 0}
        
        # Frequency to times mapping
        frequency_times = {
            "daily": ["09:00"],
            "bid": ["09:00", "21:00"],
            "tid": ["08:00", "14:00", "20:00"],
            "qid": ["08:00", "12:00", "16:00", "20:00"],
            "q4h": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
            "q6h": ["00:00", "06:00", "12:00", "18:00"],
            "q8h": ["00:00", "08:00", "16:00"],
            "q12h": ["08:00", "20:00"],
            "prn": [],  # As needed - no scheduled times
            "once": ["09:00"],
            "weekly": ["09:00"],  # Only on specific days
            "monthly": ["09:00"]  # Only on specific days
        }
        
        entries_created = 0
        now = datetime.now(timezone.utc)
        
        for med in medications:
            freq = med.get("frequency", "daily").lower().replace(" ", "").replace("-", "")
            times = frequency_times.get(freq, ["09:00"])
            
            for time_str in times:
                scheduled_time = f"{target_date}T{time_str}:00+00:00"
                
                # Check if entry already exists
                existing = await db.mar_entries.find_one({
                    "patient_id": patient_id,
                    "medication_id": med["id"],
                    "scheduled_time": scheduled_time
                })
                
                if not existing:
                    entry = MAREntry(
                        patient_id=patient_id,
                        medication_id=med["id"],
                        medication_name=med["name"],
                        dosage=med.get("dosage", ""),
                        route=med.get("route", "oral"),
                        frequency=med.get("frequency", "daily"),
                        scheduled_time=scheduled_time,
                        organization_id=org_id or "",
                        created_at=now.isoformat()
                    )
                    entry_dict = entry.model_dump(mode='json')
                    await db.mar_entries.insert_one(entry_dict)
                    entries_created += 1
        
        return {
            "message": f"MAR schedule generated for {target_date}",
            "entries_created": entries_created
        }
    
    # ============ Permission Check Endpoints ============
    
    @nurse_router.get("/permissions")
    async def get_nurse_permissions(current_user: dict = Depends(get_current_user)):
        """Get nurse-specific permissions"""
        require_nurse_role(current_user)
        
        return {
            "role": current_user.get("role"),
            "allowed_actions": NURSE_PERMISSIONS["allowed"],
            "denied_actions": NURSE_PERMISSIONS["denied"],
            "restrictions": [
                "Cannot prescribe medications - view and administer only",
                "Cannot create orders - view and update status only",
                "Cannot create lab orders - view results only",
                "Cannot interpret imaging - view only",
                "Cannot create or manage appointments",
                "Cannot access billing creation",
                "Cannot access audit logs",
                "Can only view assigned patients (when enforced)"
            ]
        }
    
    @nurse_router.get("/permissions/check/{permission}")
    async def check_permission(
        permission: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Check if a specific permission is allowed for nurse role"""
        require_nurse_role(current_user)
        
        is_allowed = permission in NURSE_PERMISSIONS["allowed"]
        is_denied = permission in NURSE_PERMISSIONS["denied"]
        
        return {
            "permission": permission,
            "allowed": is_allowed,
            "denied": is_denied,
            "message": "Allowed" if is_allowed else ("Explicitly denied" if is_denied else "Not defined")
        }
    
    # ============ Dashboard Stats Endpoints ============
    
    @nurse_router.get("/dashboard/stats")
    async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
        """Get comprehensive dashboard statistics for nurse"""
        require_nurse_role(current_user)
        
        nurse_id = current_user["id"]
        
        # Patient count
        patient_count = await db.nurse_assignments.count_documents({
            "nurse_id": nurse_id,
            "is_active": True
        })
        
        # Pending tasks
        pending_tasks = await db.nurse_tasks.count_documents({
            "nurse_id": nurse_id,
            "status": {"$in": ["pending", "in_progress"]}
        })
        
        # Tasks by priority
        stat_tasks = await db.nurse_tasks.count_documents({
            "nurse_id": nurse_id,
            "status": {"$in": ["pending", "in_progress"]},
            "priority": "stat"
        })
        
        urgent_tasks = await db.nurse_tasks.count_documents({
            "nurse_id": nurse_id,
            "status": {"$in": ["pending", "in_progress"]},
            "priority": "urgent"
        })
        
        # Get assigned patients for medication count
        assignments = await db.nurse_assignments.find({
            "nurse_id": nurse_id,
            "is_active": True
        }, {"patient_id": 1}).to_list(100)
        
        patient_ids = [a["patient_id"] for a in assignments]
        
        # Medications due (from MAR entries)
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(minutes=60)
        
        meds_due = 0
        if patient_ids:
            meds_due = await db.mar_entries.count_documents({
                "patient_id": {"$in": patient_ids},
                "status": "scheduled",
                "scheduled_time": {"$lte": window_end.isoformat()}
            })
        
        # Vitals due (simplified - based on last vitals time)
        vitals_due = 0
        for pid in patient_ids:
            last_vitals = await db.vitals.find_one(
                {"patient_id": pid},
                {"recorded_at": 1}
            )
            if not last_vitals:
                vitals_due += 1
            else:
                # If last vitals > 4 hours ago, count as due
                last_time = last_vitals.get("recorded_at", "")
                if isinstance(last_time, str) and last_time:
                    try:
                        last_dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                        if (now - last_dt).total_seconds() > 4 * 3600:
                            vitals_due += 1
                    except:
                        vitals_due += 1
        
        # Active shift
        active_shift = await db.nurse_shifts.find_one({
            "nurse_id": nurse_id,
            "is_active": True
        }, {"_id": 0})
        
        # Unread notifications
        unread_notifications = await db.notifications.count_documents({
            "user_id": nurse_id,
            "is_read": False
        })
        
        return {
            "patient_count": patient_count,
            "pending_tasks": pending_tasks,
            "stat_tasks": stat_tasks,
            "urgent_tasks": urgent_tasks,
            "medications_due": meds_due,
            "vitals_due": vitals_due,
            "unread_notifications": unread_notifications,
            "current_shift": get_current_shift_type().value,
            "active_shift": active_shift,
            "last_updated": now.isoformat()
        }
    
    # ============ Quick Actions Endpoints ============
    
    @nurse_router.post("/quick-vitals")
    async def quick_record_vitals(
        patient_id: str,
        blood_pressure_systolic: Optional[int] = None,
        blood_pressure_diastolic: Optional[int] = None,
        heart_rate: Optional[int] = None,
        respiratory_rate: Optional[int] = None,
        temperature: Optional[float] = None,
        oxygen_saturation: Optional[int] = None,
        pain_level: Optional[int] = None,
        notes: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Quick endpoint to record patient vitals"""
        require_nurse_role(current_user)
        
        # Verify assignment
        if current_user.get("role") == "nurse":
            assignment = await db.nurse_assignments.find_one({
                "patient_id": patient_id,
                "nurse_id": current_user["id"],
                "is_active": True
            })
            if not assignment:
                raise HTTPException(
                    status_code=403, 
                    detail="Access restricted: You are not assigned to this patient"
                )
        
        org_id = current_user.get("organization_id")
        now = datetime.now(timezone.utc)
        
        vitals = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "organization_id": org_id,
            "blood_pressure_systolic": blood_pressure_systolic,
            "blood_pressure_diastolic": blood_pressure_diastolic,
            "heart_rate": heart_rate,
            "respiratory_rate": respiratory_rate,
            "temperature": temperature,
            "oxygen_saturation": oxygen_saturation,
            "pain_level": pain_level,
            "notes": notes,
            "recorded_by": current_user["id"],
            "recorded_by_name": f"{current_user['first_name']} {current_user['last_name']}",
            "recorded_at": now.isoformat()
        }
        
        # Remove None values
        vitals = {k: v for k, v in vitals.items() if v is not None}
        
        await db.vitals.insert_one(vitals)
        if "_id" in vitals: del vitals["_id"]
        
        # Complete any pending vitals tasks for this patient
        await db.nurse_tasks.update_many(
            {
                "patient_id": patient_id,
                "nurse_id": current_user["id"],
                "task_type": "vitals_due",
                "status": "pending"
            },
            {"$set": {
                "status": "completed",
                "completed_time": now.isoformat(),
                "completed_by": f"{current_user['first_name']} {current_user['last_name']}"
            }}
        )
        
        return {
            "message": "Vitals recorded successfully",
            "vitals": vitals
        }
    
    @nurse_router.get("/task-types")
    async def get_task_types():
        """Get available task types"""
        return [
            {"value": t.value, "name": t.name.replace("_", " ").title()}
            for t in TaskType
        ]
    
    @nurse_router.get("/task-priorities")
    async def get_task_priorities():
        """Get task priority levels"""
        return [
            {"value": TaskPriority.STAT.value, "name": "STAT (Immediate)", "color": "red"},
            {"value": TaskPriority.URGENT.value, "name": "Urgent (30 min)", "color": "orange"},
            {"value": TaskPriority.HIGH.value, "name": "High (1 hour)", "color": "yellow"},
            {"value": TaskPriority.ROUTINE.value, "name": "Routine", "color": "blue"},
            {"value": TaskPriority.LOW.value, "name": "Low", "color": "gray"}
        ]
    
    return nurse_router
