"""
Interventional Radiology (IR) Module

Supports interventional radiology procedures including:
- Pre-procedure assessments
- Procedure scheduling and tracking
- Intra-procedure documentation
- Post-procedure notes and follow-up
- Sedation monitoring
- Consent management
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, timezone
from enum import Enum


class IRProcedureType(str, Enum):
    ANGIOGRAPHY = "angiography"
    ANGIOPLASTY = "angioplasty"
    BIOPSY = "biopsy"
    DRAINAGE = "drainage"
    EMBOLIZATION = "embolization"
    ABLATION = "ablation"
    STENT_PLACEMENT = "stent_placement"
    THROMBOLYSIS = "thrombolysis"
    VERTEBROPLASTY = "vertebroplasty"
    PORT_PLACEMENT = "port_placement"
    LINE_PLACEMENT = "line_placement"
    NEPHROSTOMY = "nephrostomy"
    CHOLECYSTOSTOMY = "cholecystostomy"
    OTHER = "other"


class IRProcedureStatus(str, Enum):
    SCHEDULED = "scheduled"
    PRE_PROCEDURE = "pre_procedure"
    IN_PROGRESS = "in_progress"
    RECOVERY = "recovery"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SedationLevel(str, Enum):
    NONE = "none"
    MINIMAL = "minimal"
    MODERATE = "moderate"
    DEEP = "deep"
    GENERAL = "general"


class IRProcedureCreate(BaseModel):
    patient_id: str
    patient_name: str
    patient_mrn: str
    procedure_type: IRProcedureType
    procedure_description: str
    indication: str
    laterality: Optional[str] = "bilateral"
    scheduled_date: str
    scheduled_time: str
    estimated_duration_minutes: int = 60
    sedation_required: SedationLevel = SedationLevel.MODERATE
    contrast_required: bool = False
    special_equipment: Optional[List[str]] = None
    attending_physician_id: str
    attending_physician_name: str
    notes: Optional[str] = None


class PreProcedureAssessment(BaseModel):
    procedure_id: str
    allergies_reviewed: bool = False
    allergies_notes: Optional[str] = None
    medications_reviewed: bool = False
    anticoagulants: Optional[List[str]] = None
    anticoagulant_held: bool = False
    last_dose_date: Optional[str] = None
    labs_reviewed: bool = False
    inr: Optional[float] = None
    platelets: Optional[int] = None
    creatinine: Optional[float] = None
    egfr: Optional[float] = None
    consent_obtained: bool = False
    consent_date: Optional[str] = None
    consent_by: Optional[str] = None
    npo_status: bool = False
    npo_since: Optional[str] = None
    iv_access: bool = False
    iv_gauge: Optional[str] = None
    assessment_notes: Optional[str] = None


class IntraProcedureNote(BaseModel):
    procedure_id: str
    access_site: str
    access_method: str  # micropuncture, direct puncture, cutdown
    anesthesia_type: SedationLevel
    contrast_used: Optional[str] = None
    contrast_volume_ml: Optional[int] = None
    fluoroscopy_time_minutes: Optional[float] = None
    radiation_dose_mgy: Optional[float] = None
    devices_used: Optional[List[str]] = None
    findings: str
    intervention_performed: str
    complications: Optional[str] = None
    estimated_blood_loss_ml: Optional[int] = None
    specimens_collected: Optional[List[str]] = None
    intra_procedure_images: Optional[int] = None


class PostProcedureNote(BaseModel):
    procedure_id: str
    procedure_end_time: str
    recovery_start_time: str
    access_site_status: str  # hemostasis achieved, closure device, manual pressure
    vital_signs_stable: bool = True
    pain_score: Optional[int] = None
    complications: Optional[str] = None
    discharge_criteria_met: bool = False
    discharge_instructions_given: bool = False
    follow_up_scheduled: bool = False
    follow_up_date: Optional[str] = None
    post_procedure_notes: str


class SedationMonitoring(BaseModel):
    procedure_id: str
    timestamp: str
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    respiratory_rate: int
    oxygen_saturation: int
    sedation_level: str  # alert, drowsy, responsive to verbal, responsive to pain, unresponsive
    medications_given: Optional[List[dict]] = None  # [{name, dose, route, time}]
    notes: Optional[str] = None


def create_ir_module_router(db, get_current_user) -> APIRouter:
    router = APIRouter(prefix="/api/interventional-radiology", tags=["Interventional Radiology"])
    
    # ============== PROCEDURE MANAGEMENT ==============
    
    @router.post("/procedures/create")
    async def create_ir_procedure(
        data: IRProcedureCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new interventional radiology procedure."""
        allowed_roles = ["physician", "radiologist", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        procedure_id = str(uuid.uuid4())
        case_number = f"IR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        
        procedure_doc = {
            "id": procedure_id,
            "case_number": case_number,
            "patient_id": data.patient_id,
            "patient_name": data.patient_name,
            "patient_mrn": data.patient_mrn,
            "procedure_type": data.procedure_type,
            "procedure_description": data.procedure_description,
            "indication": data.indication,
            "laterality": data.laterality,
            "scheduled_date": data.scheduled_date,
            "scheduled_time": data.scheduled_time,
            "estimated_duration_minutes": data.estimated_duration_minutes,
            "sedation_required": data.sedation_required,
            "contrast_required": data.contrast_required,
            "special_equipment": data.special_equipment or [],
            "attending_physician_id": data.attending_physician_id,
            "attending_physician_name": data.attending_physician_name,
            "notes": data.notes,
            "status": IRProcedureStatus.SCHEDULED,
            "organization_id": user.get("organization_id"),
            "created_by": user.get("id"),
            "created_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["ir_procedures"].insert_one(procedure_doc)
        procedure_doc.pop("_id", None)
        
        return {"message": "Procedure scheduled", "procedure": procedure_doc}
    
    @router.get("/procedures")
    async def get_ir_procedures(
        status: Optional[str] = None,
        date: Optional[str] = None,
        physician_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get interventional radiology procedures."""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        if date:
            query["scheduled_date"] = date
        if physician_id:
            query["attending_physician_id"] = physician_id
        
        procedures = await db["ir_procedures"].find(
            query, {"_id": 0}
        ).sort([("scheduled_date", 1), ("scheduled_time", 1)]).to_list(100)
        
        return {"procedures": procedures, "total": len(procedures)}
    
    @router.get("/procedures/{procedure_id}")
    async def get_ir_procedure(
        procedure_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get detailed IR procedure information."""
        procedure = await db["ir_procedures"].find_one({"id": procedure_id}, {"_id": 0})
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        # Get related documents
        pre_assessment = await db["ir_pre_assessments"].find_one(
            {"procedure_id": procedure_id}, {"_id": 0}
        )
        intra_note = await db["ir_intra_notes"].find_one(
            {"procedure_id": procedure_id}, {"_id": 0}
        )
        post_note = await db["ir_post_notes"].find_one(
            {"procedure_id": procedure_id}, {"_id": 0}
        )
        sedation_records = await db["ir_sedation_monitoring"].find(
            {"procedure_id": procedure_id}, {"_id": 0}
        ).sort("timestamp", 1).to_list(100)
        
        return {
            "procedure": procedure,
            "pre_assessment": pre_assessment,
            "intra_procedure_note": intra_note,
            "post_procedure_note": post_note,
            "sedation_records": sedation_records
        }
    
    @router.put("/procedures/{procedure_id}/status")
    async def update_procedure_status(
        procedure_id: str,
        status: IRProcedureStatus,
        user: dict = Depends(get_current_user)
    ):
        """Update procedure status."""
        procedure = await db["ir_procedures"].find_one({"id": procedure_id})
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add timestamps for specific status changes
        if status == IRProcedureStatus.IN_PROGRESS:
            update_data["procedure_start_time"] = datetime.now(timezone.utc).isoformat()
        elif status == IRProcedureStatus.COMPLETED:
            update_data["procedure_end_time"] = datetime.now(timezone.utc).isoformat()
        
        await db["ir_procedures"].update_one(
            {"id": procedure_id},
            {"$set": update_data}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": f"ir_procedure_status_changed_to_{status}",
            "resource_type": "ir_procedure",
            "resource_id": procedure_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"case_number": procedure.get("case_number"), "new_status": status},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": f"Procedure status updated to {status}"}
    
    # ============== PRE-PROCEDURE ASSESSMENT ==============
    
    @router.post("/pre-assessment/create")
    async def create_pre_assessment(
        data: PreProcedureAssessment,
        user: dict = Depends(get_current_user)
    ):
        """Create pre-procedure assessment."""
        procedure = await db["ir_procedures"].find_one({"id": data.procedure_id})
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        assessment_id = str(uuid.uuid4())
        
        assessment_doc = {
            "id": assessment_id,
            "procedure_id": data.procedure_id,
            "patient_id": procedure.get("patient_id"),
            "allergies_reviewed": data.allergies_reviewed,
            "allergies_notes": data.allergies_notes,
            "medications_reviewed": data.medications_reviewed,
            "anticoagulants": data.anticoagulants,
            "anticoagulant_held": data.anticoagulant_held,
            "last_dose_date": data.last_dose_date,
            "labs_reviewed": data.labs_reviewed,
            "inr": data.inr,
            "platelets": data.platelets,
            "creatinine": data.creatinine,
            "egfr": data.egfr,
            "consent_obtained": data.consent_obtained,
            "consent_date": data.consent_date,
            "consent_by": data.consent_by,
            "npo_status": data.npo_status,
            "npo_since": data.npo_since,
            "iv_access": data.iv_access,
            "iv_gauge": data.iv_gauge,
            "assessment_notes": data.assessment_notes,
            "assessed_by": user.get("id"),
            "assessed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["ir_pre_assessments"].insert_one(assessment_doc)
        assessment_doc.pop("_id", None)
        
        # Update procedure status
        await db["ir_procedures"].update_one(
            {"id": data.procedure_id},
            {"$set": {
                "status": IRProcedureStatus.PRE_PROCEDURE,
                "pre_assessment_completed": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Pre-procedure assessment saved", "assessment": assessment_doc}
    
    # ============== INTRA-PROCEDURE DOCUMENTATION ==============
    
    @router.post("/intra-procedure/create")
    async def create_intra_procedure_note(
        data: IntraProcedureNote,
        user: dict = Depends(get_current_user)
    ):
        """Create intra-procedure documentation."""
        procedure = await db["ir_procedures"].find_one({"id": data.procedure_id})
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        note_id = str(uuid.uuid4())
        
        note_doc = {
            "id": note_id,
            "procedure_id": data.procedure_id,
            "patient_id": procedure.get("patient_id"),
            "access_site": data.access_site,
            "access_method": data.access_method,
            "anesthesia_type": data.anesthesia_type,
            "contrast_used": data.contrast_used,
            "contrast_volume_ml": data.contrast_volume_ml,
            "fluoroscopy_time_minutes": data.fluoroscopy_time_minutes,
            "radiation_dose_mgy": data.radiation_dose_mgy,
            "devices_used": data.devices_used or [],
            "findings": data.findings,
            "intervention_performed": data.intervention_performed,
            "complications": data.complications,
            "estimated_blood_loss_ml": data.estimated_blood_loss_ml,
            "specimens_collected": data.specimens_collected or [],
            "intra_procedure_images": data.intra_procedure_images,
            "documented_by": user.get("id"),
            "documented_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["ir_intra_notes"].insert_one(note_doc)
        note_doc.pop("_id", None)
        
        return {"message": "Intra-procedure note saved", "note": note_doc}
    
    # ============== POST-PROCEDURE DOCUMENTATION ==============
    
    @router.post("/post-procedure/create")
    async def create_post_procedure_note(
        data: PostProcedureNote,
        user: dict = Depends(get_current_user)
    ):
        """Create post-procedure documentation."""
        procedure = await db["ir_procedures"].find_one({"id": data.procedure_id})
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        note_id = str(uuid.uuid4())
        
        note_doc = {
            "id": note_id,
            "procedure_id": data.procedure_id,
            "patient_id": procedure.get("patient_id"),
            "procedure_end_time": data.procedure_end_time,
            "recovery_start_time": data.recovery_start_time,
            "access_site_status": data.access_site_status,
            "vital_signs_stable": data.vital_signs_stable,
            "pain_score": data.pain_score,
            "complications": data.complications,
            "discharge_criteria_met": data.discharge_criteria_met,
            "discharge_instructions_given": data.discharge_instructions_given,
            "follow_up_scheduled": data.follow_up_scheduled,
            "follow_up_date": data.follow_up_date,
            "post_procedure_notes": data.post_procedure_notes,
            "documented_by": user.get("id"),
            "documented_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["ir_post_notes"].insert_one(note_doc)
        note_doc.pop("_id", None)
        
        # Update procedure status
        await db["ir_procedures"].update_one(
            {"id": data.procedure_id},
            {"$set": {
                "status": IRProcedureStatus.COMPLETED if data.discharge_criteria_met else IRProcedureStatus.RECOVERY,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Post-procedure note saved", "note": note_doc}
    
    # ============== SEDATION MONITORING ==============
    
    @router.post("/sedation/record")
    async def record_sedation_vitals(
        data: SedationMonitoring,
        user: dict = Depends(get_current_user)
    ):
        """Record sedation monitoring vitals."""
        procedure = await db["ir_procedures"].find_one({"id": data.procedure_id})
        if not procedure:
            raise HTTPException(status_code=404, detail="Procedure not found")
        
        record_id = str(uuid.uuid4())
        
        record_doc = {
            "id": record_id,
            "procedure_id": data.procedure_id,
            "timestamp": data.timestamp,
            "heart_rate": data.heart_rate,
            "blood_pressure_systolic": data.blood_pressure_systolic,
            "blood_pressure_diastolic": data.blood_pressure_diastolic,
            "respiratory_rate": data.respiratory_rate,
            "oxygen_saturation": data.oxygen_saturation,
            "sedation_level": data.sedation_level,
            "medications_given": data.medications_given or [],
            "notes": data.notes,
            "recorded_by": user.get("id"),
            "recorded_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["ir_sedation_monitoring"].insert_one(record_doc)
        record_doc.pop("_id", None)
        
        return {"message": "Vitals recorded", "record": record_doc}
    
    @router.get("/sedation/{procedure_id}")
    async def get_sedation_records(
        procedure_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get all sedation monitoring records for a procedure."""
        records = await db["ir_sedation_monitoring"].find(
            {"procedure_id": procedure_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(500)
        
        return {"records": records, "total": len(records)}
    
    # ============== DASHBOARD ==============
    
    @router.get("/dashboard")
    async def get_ir_dashboard(
        user: dict = Depends(get_current_user)
    ):
        """Get IR department dashboard."""
        org_id = user.get("organization_id")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Today's schedule
        today_procedures = await db["ir_procedures"].find({
            "organization_id": org_id,
            "scheduled_date": today
        }, {"_id": 0}).sort("scheduled_time", 1).to_list(50)
        
        # Counts by status
        all_procedures = await db["ir_procedures"].find(
            {"organization_id": org_id},
            {"status": 1}
        ).to_list(1000)
        
        status_counts = {}
        for p in all_procedures:
            status = p.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # In progress
        in_progress = await db["ir_procedures"].find({
            "organization_id": org_id,
            "status": IRProcedureStatus.IN_PROGRESS
        }, {"_id": 0}).to_list(10)
        
        # Recovery
        in_recovery = await db["ir_procedures"].find({
            "organization_id": org_id,
            "status": IRProcedureStatus.RECOVERY
        }, {"_id": 0}).to_list(10)
        
        return {
            "today_schedule": today_procedures,
            "today_count": len(today_procedures),
            "status_counts": status_counts,
            "in_progress": in_progress,
            "in_recovery": in_recovery
        }
    
    return router
