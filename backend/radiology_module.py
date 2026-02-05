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


class RadiologyResultCreate(BaseModel):
    order_id: str
    findings: str
    impression: str
    recommendations: Optional[str] = None
    critical_finding: bool = False
    images_available: bool = True
    pacs_link: Optional[str] = None
    dicom_study_uid: Optional[str] = None


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
        result = await db["radiology_results"].find_one({"id": result_id})
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        
        # Get associated order
        order = await db["radiology_orders"].find_one({"id": result.get("order_id")})
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
    
    return radiology_router
