"""
Nursing Supervisor/Floor Supervisor Portal Module
- Assign patients and tasks to nurses
- Read nurses' reports at end of shifts
- Read-only rights for most operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

nursing_supervisor_router = APIRouter(prefix="/api/nursing-supervisor", tags=["nursing-supervisor"])


# ============ Models ============

class PatientAssignmentBySuper(BaseModel):
    """Assignment created by supervisor"""
    patient_id: str
    nurse_id: str
    shift_type: Optional[str] = None
    department_id: Optional[str] = None
    room_bed: Optional[str] = None
    acuity_level: int = 2
    notes: Optional[str] = None


class TaskAssignmentBySuper(BaseModel):
    """Task assigned by supervisor"""
    patient_id: str
    nurse_id: str
    task_type: str
    description: str
    priority: str = "routine"
    due_time: Optional[str] = None
    notes: Optional[str] = None


class ReportReview(BaseModel):
    """Review notes from supervisor"""
    review_notes: str


# ============ Endpoints ============

def create_nursing_supervisor_endpoints(db, get_current_user):
    """Create nursing supervisor endpoints"""
    
    def require_supervisor_role(user: dict) -> dict:
        """Verify user has supervisor role"""
        allowed_roles = ["nursing_supervisor", "floor_supervisor", "hospital_admin", "super_admin", "admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Nursing supervisor access required")
        return user
    
    # ============ Dashboard ============
    
    @nursing_supervisor_router.get("/dashboard")
    async def get_supervisor_dashboard(
        current_user: dict = Depends(get_current_user)
    ):
        """Get supervisor dashboard overview"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Count nurses on shift
        active_shifts = await db.nurse_shifts.count_documents({
            "organization_id": org_id,
            "is_active": True
        })
        
        # Count total nurses
        total_nurses = await db.users.count_documents({
            "organization_id": org_id,
            "role": "nurse",
            "is_active": True
        })
        
        # Count patients with nurse assignments
        total_assignments = await db.nurse_assignments.count_documents({
            "organization_id": org_id,
            "is_active": True
        })
        
        # Get unassigned patients (admitted but no active nurse assignment)
        # This is simplified - in real app would check admission status
        admitted_patients = await db.patients.count_documents({
            "organization_id": org_id
        })
        
        # Count pending reports
        pending_reports = await db.nurse_reports.count_documents({
            "organization_id": org_id,
            "status": "submitted"
        })
        
        # Get today's shift reports
        today = datetime.now(timezone.utc).date()
        today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        
        today_reports = await db.nurse_reports.count_documents({
            "organization_id": org_id,
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        return {
            "nurses_on_shift": active_shifts,
            "total_nurses": total_nurses,
            "active_assignments": total_assignments,
            "total_patients": admitted_patients,
            "pending_reports_for_review": pending_reports,
            "today_reports": today_reports,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ Nurse Management (Read-Only) ============
    
    @nursing_supervisor_router.get("/nurses")
    async def list_nurses(
        on_shift_only: bool = False,
        department_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List all nurses (read-only)"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        query = {
            "organization_id": org_id,
            "role": "nurse",
            "is_active": True
        }
        if department_id:
            query["department_id"] = department_id
        
        nurses = await db.users.find(
            query,
            {"_id": 0, "password_hash": 0, "password": 0}
        ).to_list(100)
        
        # Enrich with shift info
        for nurse in nurses:
            active_shift = await db.nurse_shifts.find_one({
                "nurse_id": nurse["id"],
                "is_active": True
            }, {"_id": 0})
            nurse["active_shift"] = active_shift
            
            # Get patient count
            patient_count = await db.nurse_assignments.count_documents({
                "nurse_id": nurse["id"],
                "is_active": True
            })
            nurse["patient_count"] = patient_count
        
        if on_shift_only:
            nurses = [n for n in nurses if n.get("active_shift")]
        
        return {
            "nurses": nurses,
            "total": len(nurses)
        }
    
    @nursing_supervisor_router.get("/nurses/{nurse_id}/workload")
    async def get_nurse_workload(
        nurse_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get detailed workload for a specific nurse"""
        require_supervisor_role(current_user)
        
        # Get nurse info
        nurse = await db.users.find_one(
            {"id": nurse_id, "role": "nurse"},
            {"_id": 0, "password_hash": 0, "password": 0}
        )
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found")
        
        # Get active shift
        active_shift = await db.nurse_shifts.find_one({
            "nurse_id": nurse_id,
            "is_active": True
        }, {"_id": 0})
        
        # Get assigned patients
        assignments = await db.nurse_assignments.find(
            {"nurse_id": nurse_id, "is_active": True},
            {"_id": 0}
        ).to_list(50)
        
        # Get pending tasks
        pending_tasks = await db.nurse_tasks.count_documents({
            "nurse_id": nurse_id,
            "status": {"$in": ["pending", "in_progress"]}
        })
        
        # Get overdue tasks
        now = datetime.now(timezone.utc).isoformat()
        overdue_tasks = await db.nurse_tasks.count_documents({
            "nurse_id": nurse_id,
            "status": "pending",
            "due_time": {"$lt": now}
        })
        
        return {
            "nurse": nurse,
            "active_shift": active_shift,
            "patient_count": len(assignments),
            "assignments": assignments,
            "pending_tasks": pending_tasks,
            "overdue_tasks": overdue_tasks
        }
    
    # ============ Patient Assignments (Supervisor Can Assign) ============
    
    @nursing_supervisor_router.post("/assign-patient")
    async def assign_patient_to_nurse(
        assignment: PatientAssignmentBySuper,
        current_user: dict = Depends(get_current_user)
    ):
        """Assign a patient to a nurse"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Verify patient exists
        patient = await db.patients.find_one({"id": assignment.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify nurse exists and is active
        nurse = await db.users.find_one({
            "id": assignment.nurse_id,
            "role": "nurse",
            "is_active": True
        }, {"_id": 0})
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found or inactive")
        
        # Check if already assigned
        existing = await db.nurse_assignments.find_one({
            "patient_id": assignment.patient_id,
            "nurse_id": assignment.nurse_id,
            "is_active": True
        })
        if existing:
            raise HTTPException(status_code=400, detail="Patient already assigned to this nurse")
        
        now = datetime.now(timezone.utc)
        assignment_doc = {
            "id": str(uuid.uuid4()),
            "patient_id": assignment.patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "patient_mrn": patient.get("mrn", ""),
            "nurse_id": assignment.nurse_id,
            "nurse_name": f"{nurse['first_name']} {nurse['last_name']}",
            "organization_id": org_id or "",
            "shift_type": assignment.shift_type,
            "department_id": assignment.department_id,
            "room_bed": assignment.room_bed,
            "acuity_level": assignment.acuity_level,
            "is_primary": True,
            "is_active": True,
            "assigned_at": now.isoformat(),
            "assigned_by": f"{current_user['first_name']} {current_user['last_name']}",
            "assigned_by_id": current_user["id"],
            "notes": assignment.notes
        }
        
        await db.nurse_assignments.insert_one(assignment_doc)
        
        # Create notification for the nurse
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": assignment.nurse_id,
            "type": "patient_assigned",
            "title": "New Patient Assignment",
            "message": f"Supervisor assigned: {patient['first_name']} {patient['last_name']} (MRN: {patient.get('mrn', 'N/A')})",
            "priority": "normal",
            "is_read": False,
            "created_at": now.isoformat()
        }
        await db.notifications.insert_one(notification)
        
        return {
            "message": "Patient assigned successfully",
            "assignment_id": assignment_doc["id"]
        }
    
    @nursing_supervisor_router.delete("/unassign-patient/{assignment_id}")
    async def unassign_patient(
        assignment_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Remove a patient assignment"""
        require_supervisor_role(current_user)
        
        assignment = await db.nurse_assignments.find_one({"id": assignment_id, "is_active": True})
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        await db.nurse_assignments.update_one(
            {"id": assignment_id},
            {"$set": {
                "is_active": False,
                "unassigned_at": datetime.now(timezone.utc).isoformat(),
                "unassigned_by": current_user["id"]
            }}
        )
        
        return {"message": "Patient unassigned"}
    
    @nursing_supervisor_router.get("/unassigned-patients")
    async def get_unassigned_patients(
        current_user: dict = Depends(get_current_user)
    ):
        """Get patients without nurse assignments"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Get all patients
        patients = await db.patients.find(
            {"organization_id": org_id} if org_id else {},
            {"_id": 0}
        ).to_list(500)
        
        # Get assigned patient IDs
        assigned = await db.nurse_assignments.distinct(
            "patient_id",
            {"organization_id": org_id, "is_active": True} if org_id else {"is_active": True}
        )
        
        unassigned = [p for p in patients if p["id"] not in assigned]
        
        return {
            "patients": unassigned,
            "total": len(unassigned)
        }
    
    # ============ Task Assignments (Supervisor Can Assign) ============
    
    @nursing_supervisor_router.post("/assign-task")
    async def assign_task_to_nurse(
        task: TaskAssignmentBySuper,
        current_user: dict = Depends(get_current_user)
    ):
        """Assign a task to a nurse"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        # Verify patient exists
        patient = await db.patients.find_one({"id": task.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify nurse exists
        nurse = await db.users.find_one({
            "id": task.nurse_id,
            "role": "nurse",
            "is_active": True
        })
        if not nurse:
            raise HTTPException(status_code=404, detail="Nurse not found")
        
        now = datetime.now(timezone.utc)
        due_time = task.due_time or (now + timedelta(hours=1)).isoformat()
        
        task_doc = {
            "id": str(uuid.uuid4()),
            "patient_id": task.patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "patient_mrn": patient.get("mrn", ""),
            "nurse_id": task.nurse_id,
            "organization_id": org_id or "",
            "task_type": task.task_type,
            "description": task.description,
            "priority": task.priority,
            "status": "pending",
            "due_time": due_time,
            "notes": task.notes,
            "created_at": now.isoformat(),
            "created_by": f"{current_user['first_name']} {current_user['last_name']}",
            "created_by_role": "supervisor"
        }
        
        await db.nurse_tasks.insert_one(task_doc)
        
        # Notify nurse
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": task.nurse_id,
            "type": "new_task",
            "title": f"New Task: {task.task_type.replace('_', ' ').title()}",
            "message": f"For patient: {patient['first_name']} {patient['last_name']}",
            "priority": task.priority,
            "is_read": False,
            "created_at": now.isoformat()
        }
        await db.notifications.insert_one(notification)
        
        return {
            "message": "Task assigned",
            "task_id": task_doc["id"]
        }
    
    # ============ Nurse Reports (Read-Only for Supervisor) ============
    
    @nursing_supervisor_router.get("/reports")
    async def list_nurse_reports(
        status: Optional[str] = None,
        nurse_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        current_user: dict = Depends(get_current_user)
    ):
        """List all nurse reports (read-only)"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        query = {}
        if org_id:
            query["organization_id"] = org_id
        if status:
            query["status"] = status
        if nurse_id:
            query["nurse_id"] = nurse_id
        if date_from:
            query["created_at"] = {"$gte": date_from}
        if date_to:
            if "created_at" in query:
                query["created_at"]["$lte"] = date_to
            else:
                query["created_at"] = {"$lte": date_to}
        
        total = await db.nurse_reports.count_documents(query)
        skip = (page - 1) * limit
        
        reports = await db.nurse_reports.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "reports": reports,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    @nursing_supervisor_router.get("/reports/{report_id}")
    async def get_report_detail(
        report_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get detailed view of a nurse report"""
        require_supervisor_role(current_user)
        
        report = await db.nurse_reports.find_one(
            {"id": report_id},
            {"_id": 0}
        )
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
    
    @nursing_supervisor_router.post("/reports/{report_id}/review")
    async def review_report(
        report_id: str,
        review: ReportReview,
        current_user: dict = Depends(get_current_user)
    ):
        """Mark a report as reviewed with notes"""
        require_supervisor_role(current_user)
        
        report = await db.nurse_reports.find_one({"id": report_id, "status": "submitted"})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found or not submitted")
        
        await db.nurse_reports.update_one(
            {"id": report_id},
            {"$set": {
                "status": "reviewed",
                "reviewed_by": current_user["id"],
                "reviewed_by_name": f"{current_user['first_name']} {current_user['last_name']}",
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "review_notes": review.review_notes
            }}
        )
        
        # Notify the nurse
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": report["nurse_id"],
            "type": "report_reviewed",
            "title": "Report Reviewed",
            "message": f"Your shift report has been reviewed by supervisor",
            "priority": "normal",
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
        
        return {"message": "Report marked as reviewed"}
    
    # ============ Shift Overview (Read-Only) ============
    
    @nursing_supervisor_router.get("/shifts/current")
    async def get_current_shift_overview(
        current_user: dict = Depends(get_current_user)
    ):
        """Get overview of all current active shifts"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        
        query = {"is_active": True}
        if org_id:
            query["organization_id"] = org_id
        
        active_shifts = await db.nurse_shifts.find(
            query, {"_id": 0}
        ).to_list(100)
        
        # Enrich with patient counts
        for shift in active_shifts:
            patient_count = await db.nurse_assignments.count_documents({
                "nurse_id": shift["nurse_id"],
                "is_active": True
            })
            shift["patient_count"] = patient_count
        
        return {
            "active_shifts": active_shifts,
            "total_on_shift": len(active_shifts)
        }
    
    @nursing_supervisor_router.get("/shifts/history")
    async def get_shift_history(
        nurse_id: Optional[str] = None,
        days: int = 7,
        page: int = 1,
        limit: int = 50,
        current_user: dict = Depends(get_current_user)
    ):
        """Get shift history for review"""
        require_supervisor_role(current_user)
        
        org_id = current_user.get("organization_id")
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = {
            "is_active": False,
            "clock_out_time": {"$gte": start_date.isoformat()}
        }
        if org_id:
            query["organization_id"] = org_id
        if nurse_id:
            query["nurse_id"] = nurse_id
        
        total = await db.nurse_shifts.count_documents(query)
        skip = (page - 1) * limit
        
        shifts = await db.nurse_shifts.find(
            query, {"_id": 0}
        ).sort("clock_out_time", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "shifts": shifts,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    return nursing_supervisor_router


__all__ = ["nursing_supervisor_router", "create_nursing_supervisor_endpoints"]
