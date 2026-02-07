"""
Radiology Orders & Results Module for Yacco EMR
Digital imaging orders and result routing
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum

radiology_router = APIRouter(prefix="/api/radiology", tags=["Radiology"])


# ============== Enums ==============

class ImagingModality(str, Enum):
    XRAY = "xray"
    CT = "ct"
    MRI = "mri"
    ULTRASOUND = "ultrasound"
    MAMMOGRAPHY = "mammography"
    FLUOROSCOPY = "fluoroscopy"
    NUCLEAR = "nuclear"
    PET = "pet"


class RadiologyOrderStatus(str, Enum):
    ORDERED = "ordered"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REPORTED = "reported"
    CANCELLED = "cancelled"


class RadiologyPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"
    EMERGENCY = "emergency"


# ============== Pydantic Models ==============

class RadiologyOrderCreate(BaseModel):
    patient_id: str
    modality: ImagingModality
    study_type: str  # e.g., "Chest PA/Lateral", "CT Abdomen with Contrast"
    body_part: str
    laterality: Optional[str] = "bilateral"  # left, right, bilateral
    clinical_indication: str
    relevant_history: Optional[str] = None
    priority: RadiologyPriority = RadiologyPriority.ROUTINE
    contrast_required: bool = False
    special_instructions: Optional[str] = None
    scheduled_date: Optional[str] = None


class ReportStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    FINALIZED = "finalized"
    ADDENDUM = "addendum"


class RadiologyResultCreate(BaseModel):
    order_id: str
    findings: str
    impression: str
    recommendations: Optional[str] = None
    critical_finding: bool = False
    images_available: bool = True
    pacs_link: Optional[str] = None
    dicom_study_uid: Optional[str] = None


class StructuredReportCreate(BaseModel):
    """Structured radiology report with sections"""
    order_id: str
    # Study Info
    study_quality: Optional[str] = "diagnostic"  # diagnostic, limited, non-diagnostic
    comparison_studies: Optional[str] = None
    technique: Optional[str] = None
    # Clinical
    clinical_indication: Optional[str] = None
    clinical_history: Optional[str] = None
    # Findings (can be structured by body system/region)
    findings_sections: Optional[List[dict]] = None  # [{section: "Chest", findings: "..."}]
    findings_text: str  # Plain text findings
    # Impression
    impression: str
    differential_diagnosis: Optional[List[str]] = None
    # Recommendations
    recommendations: Optional[str] = None
    follow_up: Optional[str] = None
    # Flags
    critical_finding: bool = False
    critical_finding_details: Optional[str] = None
    # Status
    status: ReportStatus = ReportStatus.DRAFT


class RadiologyNoteCreate(BaseModel):
    """Radiologist notes (addendums, procedure notes, etc.)"""
    order_id: Optional[str] = None
    report_id: Optional[str] = None
    patient_id: str
    note_type: str  # addendum, procedure_note, progress_note, communication
    content: str
    urgency: Optional[str] = "routine"  # routine, urgent, critical


class RadiologyOrderUpdate(BaseModel):
    status: Optional[RadiologyOrderStatus] = None
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    technologist_notes: Optional[str] = None
    room: Optional[str] = None


# ============== Imaging Study Types ==============

IMAGING_STUDY_TYPES = {
    ImagingModality.XRAY: [
        {"code": "XR-CHEST-PA", "name": "Chest X-Ray PA", "body_part": "Chest"},
        {"code": "XR-CHEST-LAT", "name": "Chest X-Ray PA/Lateral", "body_part": "Chest"},
        {"code": "XR-ABD", "name": "Abdominal X-Ray", "body_part": "Abdomen"},
        {"code": "XR-KUB", "name": "KUB (Kidneys, Ureters, Bladder)", "body_part": "Abdomen"},
        {"code": "XR-SPINE-C", "name": "Cervical Spine X-Ray", "body_part": "Spine"},
        {"code": "XR-SPINE-L", "name": "Lumbar Spine X-Ray", "body_part": "Spine"},
        {"code": "XR-HAND", "name": "Hand X-Ray", "body_part": "Hand"},
        {"code": "XR-FOOT", "name": "Foot X-Ray", "body_part": "Foot"},
        {"code": "XR-KNEE", "name": "Knee X-Ray", "body_part": "Knee"},
        {"code": "XR-HIP", "name": "Hip X-Ray", "body_part": "Hip"},
        {"code": "XR-SHOULDER", "name": "Shoulder X-Ray", "body_part": "Shoulder"},
        {"code": "XR-SKULL", "name": "Skull X-Ray", "body_part": "Head"},
    ],
    ImagingModality.CT: [
        {"code": "CT-HEAD", "name": "CT Head without Contrast", "body_part": "Head", "contrast": False},
        {"code": "CT-HEAD-C", "name": "CT Head with Contrast", "body_part": "Head", "contrast": True},
        {"code": "CT-CHEST", "name": "CT Chest without Contrast", "body_part": "Chest", "contrast": False},
        {"code": "CT-CHEST-C", "name": "CT Chest with Contrast", "body_part": "Chest", "contrast": True},
        {"code": "CT-ABD-PEL", "name": "CT Abdomen/Pelvis without Contrast", "body_part": "Abdomen", "contrast": False},
        {"code": "CT-ABD-PEL-C", "name": "CT Abdomen/Pelvis with Contrast", "body_part": "Abdomen", "contrast": True},
        {"code": "CT-ANGIO", "name": "CT Angiography", "body_part": "Vessels", "contrast": True},
        {"code": "CT-SPINE", "name": "CT Spine", "body_part": "Spine", "contrast": False},
    ],
    ImagingModality.MRI: [
        {"code": "MRI-BRAIN", "name": "MRI Brain without Contrast", "body_part": "Head", "contrast": False},
        {"code": "MRI-BRAIN-C", "name": "MRI Brain with Contrast", "body_part": "Head", "contrast": True},
        {"code": "MRI-SPINE-C", "name": "MRI Cervical Spine", "body_part": "Spine", "contrast": False},
        {"code": "MRI-SPINE-L", "name": "MRI Lumbar Spine", "body_part": "Spine", "contrast": False},
        {"code": "MRI-KNEE", "name": "MRI Knee", "body_part": "Knee", "contrast": False},
        {"code": "MRI-SHOULDER", "name": "MRI Shoulder", "body_part": "Shoulder", "contrast": False},
        {"code": "MRI-ABD", "name": "MRI Abdomen", "body_part": "Abdomen", "contrast": False},
        {"code": "MRI-CARDIAC", "name": "Cardiac MRI", "body_part": "Heart", "contrast": True},
    ],
    ImagingModality.ULTRASOUND: [
        {"code": "US-ABD", "name": "Abdominal Ultrasound", "body_part": "Abdomen"},
        {"code": "US-PELVIS", "name": "Pelvic Ultrasound", "body_part": "Pelvis"},
        {"code": "US-OB", "name": "Obstetric Ultrasound", "body_part": "Pelvis"},
        {"code": "US-THYROID", "name": "Thyroid Ultrasound", "body_part": "Neck"},
        {"code": "US-BREAST", "name": "Breast Ultrasound", "body_part": "Breast"},
        {"code": "US-RENAL", "name": "Renal Ultrasound", "body_part": "Kidneys"},
        {"code": "US-DOPPLER", "name": "Doppler Ultrasound", "body_part": "Vessels"},
        {"code": "US-ECHO", "name": "Echocardiogram", "body_part": "Heart"},
    ],
    ImagingModality.MAMMOGRAPHY: [
        {"code": "MAM-SCREEN", "name": "Screening Mammogram", "body_part": "Breast"},
        {"code": "MAM-DIAG", "name": "Diagnostic Mammogram", "body_part": "Breast"},
    ],
}


def create_radiology_endpoints(db, get_current_user):
    """Create radiology API endpoints"""
    
    @radiology_router.get("/study-types")
    async def get_study_types(modality: Optional[str] = None):
        """Get available imaging study types"""
        if modality:
            return IMAGING_STUDY_TYPES.get(ImagingModality(modality), [])
        return IMAGING_STUDY_TYPES
    
    @radiology_router.get("/modalities")
    async def get_modalities():
        """Get available imaging modalities"""
        return [{"value": m.value, "name": m.name} for m in ImagingModality]
    
    @radiology_router.post("/orders/create")
    async def create_radiology_order(
        data: RadiologyOrderCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new radiology order"""
        allowed_roles = ["physician", "nurse", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to create radiology orders")
        
        # Verify patient
        patient = await db["patients"].find_one({"id": data.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        order_id = str(uuid.uuid4())
        accession_number = f"RAD-{datetime.now().strftime('%Y%m%d')}-{order_id[:8].upper()}"
        
        order_doc = {
            "id": order_id,
            "accession_number": accession_number,
            "patient_id": data.patient_id,
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            "patient_mrn": patient.get("mrn"),
            "patient_dob": patient.get("date_of_birth"),
            "modality": data.modality,
            "study_type": data.study_type,
            "body_part": data.body_part,
            "laterality": data.laterality,
            "clinical_indication": data.clinical_indication,
            "relevant_history": data.relevant_history,
            "priority": data.priority,
            "contrast_required": data.contrast_required,
            "special_instructions": data.special_instructions,
            "scheduled_date": data.scheduled_date,
            "scheduled_time": None,
            "room": None,
            "status": RadiologyOrderStatus.ORDERED,
            "ordering_physician_id": user.get("id"),
            "ordering_physician": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "technologist_notes": None,
            "performed_by": None,
            "performed_at": None,
            "result_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["radiology_orders"].insert_one(order_doc)
        order_doc.pop("_id", None)
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "radiology_order_created",
            "resource_type": "radiology_order",
            "resource_id": order_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"accession_number": accession_number, "modality": data.modality, "study_type": data.study_type},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Radiology order created", "order": order_doc}
    
    @radiology_router.get("/orders/queue")
    async def get_radiology_queue(
        status: Optional[str] = None,
        modality: Optional[str] = None,
        priority: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get radiology orders queue (for radiology department)"""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        else:
            # Default: show active orders
            query["status"] = {"$in": [
                RadiologyOrderStatus.ORDERED,
                RadiologyOrderStatus.SCHEDULED,
                RadiologyOrderStatus.IN_PROGRESS
            ]}
        
        if modality:
            query["modality"] = modality
        if priority:
            query["priority"] = priority
        
        orders = await db["radiology_orders"].find(query, {"_id": 0}).sort([
            ("priority", -1),  # STAT first
            ("created_at", 1)  # Then by order time
        ]).to_list(200)
        
        # Stats
        all_orders = await db["radiology_orders"].find({"organization_id": user.get("organization_id")}, {"_id": 0}).to_list(500)
        stats = {
            "total": len(all_orders),
            "ordered": len([o for o in all_orders if o["status"] == RadiologyOrderStatus.ORDERED]),
            "scheduled": len([o for o in all_orders if o["status"] == RadiologyOrderStatus.SCHEDULED]),
            "in_progress": len([o for o in all_orders if o["status"] == RadiologyOrderStatus.IN_PROGRESS]),
            "completed": len([o for o in all_orders if o["status"] == RadiologyOrderStatus.COMPLETED]),
            "reported": len([o for o in all_orders if o["status"] == RadiologyOrderStatus.REPORTED]),
            "stat_pending": len([o for o in all_orders if o["status"] in [RadiologyOrderStatus.ORDERED, RadiologyOrderStatus.SCHEDULED] and o["priority"] == RadiologyPriority.STAT])
        }
        
        return {"orders": orders, "stats": stats}
    
    @radiology_router.get("/orders/patient/{patient_id}")
    async def get_patient_radiology_orders(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get radiology orders for a patient"""
        orders = await db["radiology_orders"].find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        # Get results for completed orders
        for order in orders:
            if order.get("result_id"):
                result = await db["radiology_results"].find_one({"id": order["result_id"]}, {"_id": 0})
                order["result"] = result
        
        return {"orders": orders, "total": len(orders)}
    
    @radiology_router.put("/orders/{order_id}")
    async def update_radiology_order(
        order_id: str,
        data: RadiologyOrderUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update radiology order (schedule, status update)"""
        order = await db["radiology_orders"].find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if data.status:
            update_data["status"] = data.status
            if data.status == RadiologyOrderStatus.IN_PROGRESS:
                update_data["performed_at"] = datetime.now(timezone.utc).isoformat()
                update_data["performed_by"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        
        if data.scheduled_date:
            update_data["scheduled_date"] = data.scheduled_date
        if data.scheduled_time:
            update_data["scheduled_time"] = data.scheduled_time
        if data.room:
            update_data["room"] = data.room
        if data.technologist_notes:
            update_data["technologist_notes"] = data.technologist_notes
        
        await db["radiology_orders"].update_one({"id": order_id}, {"$set": update_data})
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": f"radiology_order_{data.status}" if data.status else "radiology_order_updated",
            "resource_type": "radiology_order",
            "resource_id": order_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"accession_number": order.get("accession_number")},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Order updated", "status": data.status}
    
    @radiology_router.post("/results/create")
    async def create_radiology_result(
        data: RadiologyResultCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create/upload radiology result (radiologist report)"""
        # Only radiologists can create official reports
        allowed_roles = ["radiologist", "physician", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Only radiologists can create official radiology reports")
        
        # Get order
        order = await db["radiology_orders"].find_one({"id": data.order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Radiology order not found")
        
        result_id = str(uuid.uuid4())
        
        result_doc = {
            "id": result_id,
            "order_id": data.order_id,
            "accession_number": order.get("accession_number"),
            "patient_id": order.get("patient_id"),
            "patient_name": order.get("patient_name"),
            "modality": order.get("modality"),
            "study_type": order.get("study_type"),
            "findings": data.findings,
            "impression": data.impression,
            "recommendations": data.recommendations,
            "critical_finding": data.critical_finding,
            "images_available": data.images_available,
            "pacs_link": data.pacs_link,
            "dicom_study_uid": data.dicom_study_uid,
            "radiologist_id": user.get("id"),
            "radiologist_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "reported_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["radiology_results"].insert_one(result_doc)
        result_doc.pop("_id", None)
        
        # Update order status and link result
        await db["radiology_orders"].update_one(
            {"id": data.order_id},
            {"$set": {
                "status": RadiologyOrderStatus.REPORTED,
                "result_id": result_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Create notification for ordering physician
        await db["notifications"].insert_one({
            "id": str(uuid.uuid4()),
            "type": "radiology_result",
            "title": "Radiology Result Available",
            "message": f"{'⚠️ CRITICAL: ' if data.critical_finding else ''}{order.get('study_type')} results for {order.get('patient_name')} are now available",
            "recipient_id": order.get("ordering_physician_id"),
            "resource_type": "radiology_result",
            "resource_id": result_id,
            "patient_id": order.get("patient_id"),
            "priority": "high" if data.critical_finding else "normal",
            "read": False,
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "radiology_result_created",
            "resource_type": "radiology_result",
            "resource_id": result_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "accession_number": order.get("accession_number"),
                "critical_finding": data.critical_finding
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Radiology result created", "result": result_doc}
    
    @radiology_router.get("/results/{result_id}")
    async def get_radiology_result(
        result_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get radiology result details"""
        result = await db["radiology_results"].find_one({"id": result_id}, {"_id": 0})
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Get associated order
        order = await db["radiology_orders"].find_one({"id": result.get("order_id")}, {"_id": 0})
        result["order"] = order
        
        return result
    
    @radiology_router.get("/results/patient/{patient_id}")
    async def get_patient_radiology_results(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get all radiology results for a patient"""
        results = await db["radiology_results"].find({"patient_id": patient_id}, {"_id": 0}).sort("reported_at", -1).to_list(100)
        return {"results": results, "total": len(results)}
    
    # ============== RADIOLOGIST DASHBOARD ==============
    
    @radiology_router.get("/dashboard/radiologist")
    async def get_radiologist_dashboard(
        user: dict = Depends(get_current_user)
    ):
        """Get radiologist-specific dashboard with worklist and stats"""
        org_id = user.get("organization_id")
        user_id = user.get("id")
        
        # Get assigned studies (assigned to this radiologist)
        assigned_orders = await db["radiology_orders"].find({
            "organization_id": org_id,
            "assigned_radiologist_id": user_id,
            "status": {"$in": ["completed", "under_review"]}
        }, {"_id": 0}).sort([("priority", -1), ("created_at", 1)]).to_list(100)
        
        # Get unassigned completed studies (available for review)
        unassigned_orders = await db["radiology_orders"].find({
            "organization_id": org_id,
            "assigned_radiologist_id": None,
            "status": "completed"
        }, {"_id": 0}).sort([("priority", -1), ("created_at", 1)]).to_list(100)
        
        # Get STAT studies requiring attention
        stat_studies = await db["radiology_orders"].find({
            "organization_id": org_id,
            "priority": {"$in": ["stat", "emergency"]},
            "status": {"$in": ["ordered", "scheduled", "in_progress", "completed"]}
        }, {"_id": 0}).sort("created_at", 1).to_list(50)
        
        # Get recently finalized reports by this radiologist (from radiology_reports collection)
        my_reports = await db["radiology_reports"].find({
            "radiologist_id": user_id
        }, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
        
        # Get critical findings requiring communication (from radiology_reports collection)
        critical_findings = await db["radiology_reports"].find({
            "organization_id": org_id,
            "critical_finding": True,
            "critical_communicated": {"$ne": True}
        }, {"_id": 0}).sort("created_at", -1).to_list(20)
        
        # Stats
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        all_orders = await db["radiology_orders"].find({"organization_id": org_id}, {"status": 1, "priority": 1}).to_list(1000)
        my_daily_reports = await db["radiology_reports"].count_documents({
            "radiologist_id": user_id,
            "created_at": {"$regex": f"^{today}"}
        })
        
        stats = {
            "pending_review": len([o for o in all_orders if o["status"] == "completed"]),
            "under_review": len([o for o in all_orders if o.get("status") == "under_review"]),
            "stat_pending": len([o for o in all_orders if o.get("priority") in ["stat", "emergency"] and o["status"] not in ["reported", "cancelled"]]),
            "my_assigned": len(assigned_orders),
            "my_reports_today": my_daily_reports,
            "critical_pending": len(critical_findings),
            "total_queue": len([o for o in all_orders if o["status"] not in ["reported", "cancelled"]])
        }
        
        return {
            "assigned_studies": assigned_orders,
            "unassigned_studies": unassigned_orders,
            "stat_studies": stat_studies,
            "my_recent_reports": my_reports,
            "critical_findings": critical_findings,
            "stats": stats
        }
    
    @radiology_router.post("/orders/{order_id}/assign")
    async def assign_order_to_radiologist(
        order_id: str,
        radiologist_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Assign a study to a radiologist for review"""
        order = await db["radiology_orders"].find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # If no radiologist specified, assign to current user
        target_radiologist = radiologist_id or user.get("id")
        
        # Get radiologist info
        radiologist = await db["users"].find_one({"id": target_radiologist}, {"_id": 0, "password": 0})
        if not radiologist:
            raise HTTPException(status_code=404, detail="Radiologist not found")
        
        await db["radiology_orders"].update_one(
            {"id": order_id},
            {"$set": {
                "assigned_radiologist_id": target_radiologist,
                "assigned_radiologist_name": f"{radiologist.get('first_name', '')} {radiologist.get('last_name', '')}",
                "assigned_at": datetime.now(timezone.utc).isoformat(),
                "status": "under_review" if order["status"] == "completed" else order["status"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "radiology_order_assigned",
            "resource_type": "radiology_order",
            "resource_id": order_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "accession_number": order.get("accession_number"),
                "assigned_to": target_radiologist,
                "assigned_to_name": f"{radiologist.get('first_name', '')} {radiologist.get('last_name', '')}"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Study assigned", "assigned_to": f"{radiologist.get('first_name', '')} {radiologist.get('last_name', '')}"}
    
    # ============== STRUCTURED REPORTING ==============
    
    @radiology_router.post("/reports/create")
    async def create_structured_report(
        data: StructuredReportCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a structured radiology report"""
        allowed_roles = ["radiologist", "physician", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Only radiologists can create reports")
        
        order = await db["radiology_orders"].find_one({"id": data.order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Radiology order not found")
        
        report_id = str(uuid.uuid4())
        
        report_doc = {
            "id": report_id,
            "order_id": data.order_id,
            "accession_number": order.get("accession_number"),
            "patient_id": order.get("patient_id"),
            "patient_name": order.get("patient_name"),
            "patient_mrn": order.get("patient_mrn"),
            "modality": order.get("modality"),
            "study_type": order.get("study_type"),
            "body_part": order.get("body_part"),
            # Study info
            "study_quality": data.study_quality,
            "comparison_studies": data.comparison_studies,
            "technique": data.technique,
            # Clinical
            "clinical_indication": data.clinical_indication or order.get("clinical_indication"),
            "clinical_history": data.clinical_history or order.get("relevant_history"),
            # Findings
            "findings_sections": data.findings_sections,
            "findings_text": data.findings_text,
            # Impression
            "impression": data.impression,
            "differential_diagnosis": data.differential_diagnosis,
            # Recommendations
            "recommendations": data.recommendations,
            "follow_up": data.follow_up,
            # Critical
            "critical_finding": data.critical_finding,
            "critical_finding_details": data.critical_finding_details,
            "critical_communicated": False,
            "critical_communicated_to": None,
            "critical_communicated_at": None,
            # Status
            "status": data.status,
            # Author
            "radiologist_id": user.get("id"),
            "radiologist_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "finalized_at": datetime.now(timezone.utc).isoformat() if data.status == ReportStatus.FINALIZED else None
        }
        
        await db["radiology_reports"].insert_one(report_doc)
        report_doc.pop("_id", None)
        
        # Update order status if report is finalized
        if data.status == ReportStatus.FINALIZED:
            await db["radiology_orders"].update_one(
                {"id": data.order_id},
                {"$set": {
                    "status": RadiologyOrderStatus.REPORTED,
                    "report_id": report_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Create notification for ordering physician
            await db["notifications"].insert_one({
                "id": str(uuid.uuid4()),
                "type": "radiology_report_finalized",
                "title": f"{'⚠️ CRITICAL: ' if data.critical_finding else ''}Radiology Report Ready",
                "message": f"{order.get('study_type')} results for {order.get('patient_name')} - Report finalized by Dr. {user.get('last_name')}",
                "recipient_id": order.get("ordering_physician_id"),
                "resource_type": "radiology_report",
                "resource_id": report_id,
                "patient_id": order.get("patient_id"),
                "priority": "critical" if data.critical_finding else "normal",
                "read": False,
                "organization_id": user.get("organization_id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": f"radiology_report_{data.status}",
            "resource_type": "radiology_report",
            "resource_id": report_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "accession_number": order.get("accession_number"),
                "status": data.status,
                "critical_finding": data.critical_finding
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Report created", "report": report_doc}
    
    @radiology_router.put("/reports/{report_id}")
    async def update_report(
        report_id: str,
        data: StructuredReportCreate,
        user: dict = Depends(get_current_user)
    ):
        """Update an existing report (only if draft or by the author)"""
        report = await db["radiology_reports"].find_one({"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Only author can edit, or admin
        if report.get("radiologist_id") != user.get("id") and user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only the report author can edit")
        
        # Cannot edit finalized reports
        if report.get("status") == "finalized" and data.status != ReportStatus.ADDENDUM:
            raise HTTPException(status_code=400, detail="Cannot edit finalized reports. Create an addendum instead.")
        
        update_data = {
            "study_quality": data.study_quality,
            "comparison_studies": data.comparison_studies,
            "technique": data.technique,
            "clinical_indication": data.clinical_indication,
            "clinical_history": data.clinical_history,
            "findings_sections": data.findings_sections,
            "findings_text": data.findings_text,
            "impression": data.impression,
            "differential_diagnosis": data.differential_diagnosis,
            "recommendations": data.recommendations,
            "follow_up": data.follow_up,
            "critical_finding": data.critical_finding,
            "critical_finding_details": data.critical_finding_details,
            "status": data.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if data.status == ReportStatus.FINALIZED and not report.get("finalized_at"):
            update_data["finalized_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update order status
            await db["radiology_orders"].update_one(
                {"id": report.get("order_id")},
                {"$set": {
                    "status": RadiologyOrderStatus.REPORTED,
                    "report_id": report_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        await db["radiology_reports"].update_one({"id": report_id}, {"$set": update_data})
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "radiology_report_updated",
            "resource_type": "radiology_report",
            "resource_id": report_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"new_status": data.status},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Report updated"}
    
    @radiology_router.post("/reports/{report_id}/finalize")
    async def finalize_report(
        report_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Finalize and sign a radiology report"""
        report = await db["radiology_reports"].find_one({"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if report.get("radiologist_id") != user.get("id"):
            raise HTTPException(status_code=403, detail="Only the author can finalize")
        
        if report.get("status") == "finalized":
            raise HTTPException(status_code=400, detail="Report already finalized")
        
        await db["radiology_reports"].update_one(
            {"id": report_id},
            {"$set": {
                "status": "finalized",
                "finalized_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update order status
        order = await db["radiology_orders"].find_one({"id": report.get("order_id")})
        if order:
            await db["radiology_orders"].update_one(
                {"id": order["id"]},
                {"$set": {
                    "status": RadiologyOrderStatus.REPORTED,
                    "report_id": report_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Notification to ordering physician
            await db["notifications"].insert_one({
                "id": str(uuid.uuid4()),
                "type": "radiology_report_finalized",
                "title": f"{'⚠️ CRITICAL: ' if report.get('critical_finding') else ''}Radiology Report Finalized",
                "message": f"{order.get('study_type')} results for {order.get('patient_name')} are ready",
                "recipient_id": order.get("ordering_physician_id"),
                "resource_type": "radiology_report",
                "resource_id": report_id,
                "patient_id": order.get("patient_id"),
                "priority": "critical" if report.get("critical_finding") else "normal",
                "read": False,
                "organization_id": user.get("organization_id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return {"message": "Report finalized and signed"}
    
    @radiology_router.get("/reports/{report_id}")
    async def get_report(
        report_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get a radiology report"""
        report = await db["radiology_reports"].find_one({"id": report_id}, {"_id": 0})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Get associated order
        order = await db["radiology_orders"].find_one({"id": report.get("order_id")}, {"_id": 0})
        report["order"] = order
        
        # Get any notes/addendums
        notes = await db["radiology_notes"].find({"report_id": report_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
        report["notes"] = notes
        
        return report
    
    @radiology_router.get("/reports/patient/{patient_id}")
    async def get_patient_reports(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get all radiology reports for a patient"""
        reports = await db["radiology_reports"].find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return {"reports": reports, "total": len(reports)}
    
    # ============== RADIOLOGIST NOTES ==============
    
    @radiology_router.post("/notes/create")
    async def create_radiology_note(
        data: RadiologyNoteCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a radiologist note (addendum, procedure note, etc.)"""
        allowed_roles = ["radiologist", "physician", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to create radiology notes")
        
        note_id = str(uuid.uuid4())
        
        note_doc = {
            "id": note_id,
            "order_id": data.order_id,
            "report_id": data.report_id,
            "patient_id": data.patient_id,
            "note_type": data.note_type,
            "content": data.content,
            "urgency": data.urgency,
            "author_id": user.get("id"),
            "author_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "author_role": user.get("role"),
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["radiology_notes"].insert_one(note_doc)
        note_doc.pop("_id", None)
        
        # If this is an addendum to a finalized report, notify ordering physician
        if data.note_type == "addendum" and data.report_id:
            report = await db["radiology_reports"].find_one({"id": data.report_id})
            if report:
                order = await db["radiology_orders"].find_one({"id": report.get("order_id")})
                if order:
                    await db["notifications"].insert_one({
                        "id": str(uuid.uuid4()),
                        "type": "radiology_addendum",
                        "title": "Radiology Report Addendum",
                        "message": f"An addendum has been added to {order.get('study_type')} report for {order.get('patient_name')}",
                        "recipient_id": order.get("ordering_physician_id"),
                        "resource_type": "radiology_note",
                        "resource_id": note_id,
                        "patient_id": data.patient_id,
                        "priority": "high" if data.urgency == "critical" else "normal",
                        "read": False,
                        "organization_id": user.get("organization_id"),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
        
        return {"message": "Note created", "note": note_doc}
    
    @radiology_router.get("/notes/patient/{patient_id}")
    async def get_patient_radiology_notes(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get all radiology notes for a patient"""
        notes = await db["radiology_notes"].find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return {"notes": notes, "total": len(notes)}
    
    # ============== CRITICAL FINDINGS WORKFLOW ==============
    
    @radiology_router.post("/reports/{report_id}/communicate-critical")
    async def communicate_critical_finding(
        report_id: str,
        communicated_to: str,  # Name or ID of person communicated to
        communication_method: str = "verbal",  # verbal, phone, page, in_person
        notes: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Document communication of critical finding"""
        report = await db["radiology_reports"].find_one({"id": report_id})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        if not report.get("critical_finding"):
            raise HTTPException(status_code=400, detail="This report does not have a critical finding")
        
        await db["radiology_reports"].update_one(
            {"id": report_id},
            {"$set": {
                "critical_communicated": True,
                "critical_communicated_to": communicated_to,
                "critical_communicated_at": datetime.now(timezone.utc).isoformat(),
                "critical_communication_method": communication_method,
                "critical_communication_notes": notes,
                "critical_communicated_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Audit log for compliance
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "critical_finding_communicated",
            "resource_type": "radiology_report",
            "resource_id": report_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "accession_number": report.get("accession_number"),
                "communicated_to": communicated_to,
                "method": communication_method,
                "patient_id": report.get("patient_id")
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Critical finding communication documented"}
    
    # ============== ORDER STATUS TIMELINE ==============
    
    @radiology_router.get("/orders/{order_id}/timeline")
    async def get_order_timeline(
        order_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get status timeline for a radiology order"""
        order = await db["radiology_orders"].find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get audit logs for this order
        audit_logs = await db["audit_logs"].find({
            "resource_id": order_id,
            "resource_type": "radiology_order"
        }, {"_id": 0}).sort("timestamp", 1).to_list(100)
        
        # Build timeline
        timeline = [
            {
                "status": "ordered",
                "timestamp": order.get("created_at"),
                "user": order.get("ordering_physician"),
                "details": f"Order placed for {order.get('study_type')}"
            }
        ]
        
        # Add events from audit logs
        for log in audit_logs:
            action = log.get("action", "")
            if "scheduled" in action:
                timeline.append({
                    "status": "scheduled",
                    "timestamp": log.get("timestamp"),
                    "user": log.get("user_name"),
                    "details": f"Scheduled for {order.get('scheduled_date')} {order.get('scheduled_time', '')}"
                })
            elif "in_progress" in action:
                timeline.append({
                    "status": "in_progress",
                    "timestamp": log.get("timestamp"),
                    "user": log.get("user_name"),
                    "details": "Study started"
                })
            elif "completed" in action:
                timeline.append({
                    "status": "completed",
                    "timestamp": log.get("timestamp"),
                    "user": log.get("user_name"),
                    "details": "Study completed, awaiting interpretation"
                })
            elif "assigned" in action:
                timeline.append({
                    "status": "under_review",
                    "timestamp": log.get("timestamp"),
                    "user": log.get("user_name"),
                    "details": f"Assigned to {log.get('details', {}).get('assigned_to_name', 'radiologist')}"
                })
        
        # Add report info if exists
        if order.get("report_id"):
            report = await db["radiology_reports"].find_one({"id": order["report_id"]}, {"_id": 0})
            if report:
                timeline.append({
                    "status": "reported",
                    "timestamp": report.get("finalized_at") or report.get("created_at"),
                    "user": report.get("radiologist_name"),
                    "details": f"Report {'finalized' if report.get('status') == 'finalized' else 'created'}"
                })
        
        return {"order": order, "timeline": timeline}
    
    # ============== WORKLIST FILTERS ==============
    
    @radiology_router.get("/worklist")
    async def get_radiologist_worklist(
        status: Optional[str] = None,
        modality: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_me: bool = False,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get radiologist worklist with advanced filters"""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        else:
            # Default: show studies ready for review
            query["status"] = {"$in": ["completed", "under_review"]}
        
        if modality:
            query["modality"] = modality
        
        if priority:
            query["priority"] = priority
        
        if assigned_to_me:
            query["assigned_radiologist_id"] = user.get("id")
        
        if date_from:
            query["created_at"] = {"$gte": date_from}
        if date_to:
            if "created_at" in query:
                query["created_at"]["$lte"] = date_to + "T23:59:59"
            else:
                query["created_at"] = {"$lte": date_to + "T23:59:59"}
        
        orders = await db["radiology_orders"].find(query, {"_id": 0}).sort([
            ("priority", -1),
            ("created_at", 1)
        ]).to_list(200)
        
        return {"worklist": orders, "total": len(orders)}
    
    return radiology_router
