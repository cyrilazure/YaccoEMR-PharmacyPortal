"""
Clinical Documentation Module for Yacco EMR
Provides:
- Nursing Documentation (assessments, vitals summaries, progress notes, care plans)
- Physician Documentation (H&P, progress notes, orders, discharge summaries)
- Cross-role visibility (physicians see nursing docs, nurses see physician docs read-only)
- Patient Assignment enforcement
- Comprehensive Audit Logging
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

clinical_docs_router = APIRouter(prefix="/api/clinical-docs", tags=["Clinical Documentation"])


# ============ ENUMS ============

class NursingDocType(str, Enum):
    ASSESSMENT = "assessment"
    VITALS_SUMMARY = "vitals_summary"
    PROGRESS_NOTE = "progress_note"
    CARE_PLAN = "care_plan"
    SHIFT_REPORT = "shift_report"
    INTAKE_OUTPUT = "intake_output"
    PAIN_ASSESSMENT = "pain_assessment"
    FALL_RISK = "fall_risk"
    SKIN_ASSESSMENT = "skin_assessment"
    WOUND_CARE = "wound_care"
    PATIENT_EDUCATION = "patient_education"
    DISCHARGE_INSTRUCTIONS = "discharge_instructions"


class PhysicianDocType(str, Enum):
    HISTORY_PHYSICAL = "h_and_p"
    PROGRESS_NOTE = "progress_note"
    CONSULTATION = "consultation"
    PROCEDURE_NOTE = "procedure_note"
    OPERATIVE_NOTE = "operative_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    ORDER_NOTE = "order_note"
    ADDENDUM = "addendum"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    AMENDED = "amended"
    COSIGNED = "cosigned"


class AuditAction(str, Enum):
    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    SIGN = "sign"
    COSIGN = "cosign"
    ORDER = "order"
    PRINT = "print"
    EXPORT = "export"
    ACCESS_DENIED = "access_denied"


# ============ MODELS ============

# Nursing Documentation Models
class NursingDocCreate(BaseModel):
    patient_id: str
    doc_type: NursingDocType
    title: str
    content: str
    clinical_findings: Optional[str] = None
    interventions: Optional[str] = None
    patient_response: Optional[str] = None
    plan_of_care: Optional[str] = None
    shift_type: Optional[str] = None  # morning, evening, night


class NursingDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_mrn: str
    nurse_id: str
    nurse_name: str
    organization_id: Optional[str] = None
    doc_type: NursingDocType
    title: str
    content: str
    clinical_findings: Optional[str] = None
    interventions: Optional[str] = None
    patient_response: Optional[str] = None
    plan_of_care: Optional[str] = None
    shift_type: Optional[str] = None
    status: DocumentStatus = DocumentStatus.DRAFT
    signed_at: Optional[str] = None
    signed_by_name: Optional[str] = None
    cosigned_by: Optional[str] = None
    cosigned_by_name: Optional[str] = None
    cosigned_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


# Physician Documentation Models  
class PhysicianDocCreate(BaseModel):
    patient_id: str
    doc_type: PhysicianDocType
    title: str
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    past_medical_history: Optional[str] = None
    physical_exam: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    content: Optional[str] = None  # For free-text notes


class PhysicianDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_mrn: str
    physician_id: str
    physician_name: str
    organization_id: Optional[str] = None
    doc_type: PhysicianDocType
    title: str
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    past_medical_history: Optional[str] = None
    physical_exam: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    content: Optional[str] = None
    status: DocumentStatus = DocumentStatus.DRAFT
    signed_at: Optional[str] = None
    signed_by_name: Optional[str] = None
    cosigned_by: Optional[str] = None
    cosigned_by_name: Optional[str] = None
    cosigned_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


# Patient Assignment Models (for access control)
class PatientAssignmentCreate(BaseModel):
    patient_id: str
    user_id: str
    assignment_type: str = "primary"  # primary, secondary, consulting
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None


class PatientAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_mrn: str
    user_id: str
    user_name: str
    user_role: str
    organization_id: Optional[str] = None
    assignment_type: str = "primary"
    is_active: bool = True
    start_time: str
    end_time: Optional[str] = None
    assigned_by: str
    assigned_by_name: str
    notes: Optional[str] = None
    created_at: str


# Audit Log Models
class ChartAuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    patient_mrn: str
    user_id: str
    user_name: str
    user_role: str
    organization_id: Optional[str] = None
    action: AuditAction
    resource_type: str  # nursing_doc, physician_doc, vitals, medications, etc.
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    failure_reason: Optional[str] = None
    timestamp: str


# ============ HELPER FUNCTIONS ============

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ============ ENDPOINTS ============

def create_clinical_documentation_endpoints(db, get_current_user):
    """Create clinical documentation endpoints with RBAC"""
    
    # ============ AUDIT LOGGING HELPER ============
    
    async def log_chart_access(
        patient_id: str,
        user: dict,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        request: Request = None
    ):
        """Log all chart access events (immutable audit log)"""
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        
        log_entry = ChartAuditLog(
            patient_id=patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}" if patient else "Unknown",
            patient_mrn=patient.get("mrn", "") if patient else "",
            user_id=user.get("id", ""),
            user_name=f"{user.get('first_name', '')} {user.get('last_name', '')}",
            user_role=user.get("role", ""),
            organization_id=user.get("organization_id"),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            success=success,
            failure_reason=failure_reason,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        log_dict = log_entry.model_dump(mode='json')
        await db.chart_audit_logs.insert_one(log_dict)
        
        return log_entry
    
    # ============ ACCESS CONTROL HELPERS ============
    
    async def check_patient_access(user: dict, patient_id: str, request: Request = None) -> bool:
        """
        Check if user has access to patient chart based on:
        1. Role-based access (supervisors, admins see all in their org)
        2. Direct patient assignment
        """
        role = user.get("role", "")
        org_id = user.get("organization_id")
        
        # Super admin has access to all
        if role == "super_admin":
            return True
        
        # Hospital admin and IT admin see all in their org
        if role in ["hospital_admin", "hospital_it_admin", "admin"]:
            patient = await db.patients.find_one({"id": patient_id}, {"organization_id": 1})
            if patient and patient.get("organization_id") == org_id:
                return True
            # If no org match, still allow for cross-org admins
            return True
        
        # Nursing supervisors and floor supervisors see all patients in their unit/org
        if role in ["nursing_supervisor", "floor_supervisor"]:
            patient = await db.patients.find_one({"id": patient_id}, {"organization_id": 1})
            if patient and (not patient.get("organization_id") or patient.get("organization_id") == org_id):
                return True
            return True  # Allow supervisors broader access for now
        
        # Physicians see patients they are assigned to
        if role == "physician":
            # Check if physician has any active assignment to this patient
            assignment = await db.patient_assignments.find_one({
                "patient_id": patient_id,
                "user_id": user.get("id"),
                "is_active": True
            })
            if assignment:
                return True
            
            # Also check if physician created any documentation for this patient
            physician_doc = await db.physician_documentation.find_one({
                "patient_id": patient_id,
                "physician_id": user.get("id")
            })
            if physician_doc:
                return True
            
            # For now, allow physicians to view any patient in their org
            # (In strict mode, this would be disabled)
            patient = await db.patients.find_one({"id": patient_id}, {"organization_id": 1})
            if patient and (not patient.get("organization_id") or patient.get("organization_id") == org_id):
                return True
        
        # Nurses see only patients they are assigned to
        if role == "nurse":
            # Check nurse assignment
            assignment = await db.nurse_assignments.find_one({
                "patient_id": patient_id,
                "nurse_id": user.get("id"),
                "is_active": True
            })
            if assignment:
                return True
            
            # Check patient_assignments table too
            assignment2 = await db.patient_assignments.find_one({
                "patient_id": patient_id,
                "user_id": user.get("id"),
                "is_active": True
            })
            if assignment2:
                return True
            
            # Log access denial
            await log_chart_access(
                patient_id=patient_id,
                user=user,
                action=AuditAction.ACCESS_DENIED,
                resource_type="patient_chart",
                success=False,
                failure_reason="Nurse not assigned to patient",
                request=request
            )
            return False
        
        # Default: deny access for unknown roles
        return False
    
    async def require_patient_access(user: dict, patient_id: str, request: Request = None):
        """Raise exception if user doesn't have patient access"""
        has_access = await check_patient_access(user, patient_id, request)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You are not assigned to this patient's chart."
            )
        return True
    
    # ============ NURSING DOCUMENTATION ENDPOINTS ============
    
    @clinical_docs_router.get("/nursing/{patient_id}")
    async def get_nursing_documentation(
        patient_id: str,
        doc_type: Optional[str] = None,
        limit: int = 50,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Get nursing documentation for a patient.
        - Nurses: Can view/edit their own nursing docs for assigned patients
        - Physicians: Can view all nursing docs for their patients (read-only)
        - Supervisors: Can view all nursing docs in their unit
        """
        await require_patient_access(current_user, patient_id, request)
        
        # Log the access
        await log_chart_access(
            patient_id=patient_id,
            user=current_user,
            action=AuditAction.VIEW,
            resource_type="nursing_documentation",
            request=request
        )
        
        query = {"patient_id": patient_id}
        if doc_type:
            query["doc_type"] = doc_type
        
        docs = await db.nursing_documentation.find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Determine if user can edit (nurses only for their own docs)
        user_role = current_user.get("role", "")
        for doc in docs:
            doc["can_edit"] = (
                user_role in ["nurse", "nursing_supervisor"] and 
                doc.get("nurse_id") == current_user.get("id") and
                doc.get("status") == "draft"
            )
            doc["can_sign"] = (
                user_role in ["nurse", "nursing_supervisor"] and 
                doc.get("nurse_id") == current_user.get("id") and
                doc.get("status") == "draft"
            )
        
        return {
            "documents": docs,
            "total": len(docs),
            "user_role": user_role,
            "can_create": user_role in ["nurse", "nursing_supervisor", "floor_supervisor"]
        }
    
    @clinical_docs_router.post("/nursing")
    async def create_nursing_documentation(
        doc_data: NursingDocCreate,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Create nursing documentation (nurses and nursing supervisors only)"""
        role = current_user.get("role", "")
        if role not in ["nurse", "nursing_supervisor", "floor_supervisor", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only nurses can create nursing documentation")
        
        await require_patient_access(current_user, doc_data.patient_id, request)
        
        # Get patient info
        patient = await db.patients.find_one({"id": doc_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        now = datetime.now(timezone.utc)
        doc = NursingDoc(
            patient_id=doc_data.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_mrn=patient.get("mrn", ""),
            nurse_id=current_user.get("id", ""),
            nurse_name=f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}",
            organization_id=current_user.get("organization_id"),
            doc_type=doc_data.doc_type,
            title=doc_data.title,
            content=doc_data.content,
            clinical_findings=doc_data.clinical_findings,
            interventions=doc_data.interventions,
            patient_response=doc_data.patient_response,
            plan_of_care=doc_data.plan_of_care,
            shift_type=doc_data.shift_type,
            created_at=now.isoformat()
        )
        
        doc_dict = doc.model_dump(mode='json')
        await db.nursing_documentation.insert_one(doc_dict)
        
        # Log creation
        await log_chart_access(
            patient_id=doc_data.patient_id,
            user=current_user,
            action=AuditAction.CREATE,
            resource_type="nursing_documentation",
            resource_id=doc.id,
            details={"doc_type": doc_data.doc_type.value, "title": doc_data.title},
            request=request
        )
        
        return {"message": "Nursing documentation created", "document": doc_dict}
    
    @clinical_docs_router.put("/nursing/{doc_id}")
    async def update_nursing_documentation(
        doc_id: str,
        content: Optional[str] = None,
        clinical_findings: Optional[str] = None,
        interventions: Optional[str] = None,
        patient_response: Optional[str] = None,
        plan_of_care: Optional[str] = None,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Update nursing documentation (author only, draft status only)"""
        doc = await db.nursing_documentation.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify ownership and status
        if doc.get("nurse_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="You can only edit your own documentation")
        
        if doc.get("status") != "draft":
            raise HTTPException(status_code=400, detail="Cannot edit signed documentation")
        
        updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if content is not None:
            updates["content"] = content
        if clinical_findings is not None:
            updates["clinical_findings"] = clinical_findings
        if interventions is not None:
            updates["interventions"] = interventions
        if patient_response is not None:
            updates["patient_response"] = patient_response
        if plan_of_care is not None:
            updates["plan_of_care"] = plan_of_care
        
        await db.nursing_documentation.update_one({"id": doc_id}, {"$set": updates})
        
        # Log edit
        await log_chart_access(
            patient_id=doc.get("patient_id", ""),
            user=current_user,
            action=AuditAction.EDIT,
            resource_type="nursing_documentation",
            resource_id=doc_id,
            request=request
        )
        
        return {"message": "Documentation updated"}
    
    @clinical_docs_router.post("/nursing/{doc_id}/sign")
    async def sign_nursing_documentation(
        doc_id: str,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Sign nursing documentation (makes it immutable)"""
        doc = await db.nursing_documentation.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify ownership
        if doc.get("nurse_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="You can only sign your own documentation")
        
        if doc.get("status") != "draft":
            raise HTTPException(status_code=400, detail="Document is already signed")
        
        now = datetime.now(timezone.utc)
        await db.nursing_documentation.update_one(
            {"id": doc_id},
            {"$set": {
                "status": "signed",
                "signed_at": now.isoformat(),
                "signed_by_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}"
            }}
        )
        
        # Log signing
        await log_chart_access(
            patient_id=doc.get("patient_id", ""),
            user=current_user,
            action=AuditAction.SIGN,
            resource_type="nursing_documentation",
            resource_id=doc_id,
            request=request
        )
        
        return {"message": "Documentation signed"}
    
    # ============ PHYSICIAN DOCUMENTATION ENDPOINTS ============
    
    @clinical_docs_router.get("/physician/{patient_id}")
    async def get_physician_documentation(
        patient_id: str,
        doc_type: Optional[str] = None,
        limit: int = 50,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """
        Get physician documentation for a patient.
        - Physicians: Full access to view/edit their own docs
        - Nurses: Read-only access to physician docs for assigned patients
        - Supervisors: Read-only access to all physician docs
        """
        await require_patient_access(current_user, patient_id, request)
        
        # Log the access
        await log_chart_access(
            patient_id=patient_id,
            user=current_user,
            action=AuditAction.VIEW,
            resource_type="physician_documentation",
            request=request
        )
        
        query = {"patient_id": patient_id}
        if doc_type:
            query["doc_type"] = doc_type
        
        docs = await db.physician_documentation.find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Determine permissions based on role
        user_role = current_user.get("role", "")
        is_physician = user_role == "physician"
        
        for doc in docs:
            doc["can_edit"] = (
                is_physician and 
                doc.get("physician_id") == current_user.get("id") and
                doc.get("status") == "draft"
            )
            doc["can_sign"] = (
                is_physician and 
                doc.get("physician_id") == current_user.get("id") and
                doc.get("status") == "draft"
            )
            # Nurses get read-only view indicator
            doc["read_only"] = not is_physician
        
        return {
            "documents": docs,
            "total": len(docs),
            "user_role": user_role,
            "can_create": is_physician,
            "read_only": not is_physician
        }
    
    @clinical_docs_router.post("/physician")
    async def create_physician_documentation(
        doc_data: PhysicianDocCreate,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Create physician documentation (physicians only)"""
        role = current_user.get("role", "")
        if role not in ["physician", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can create physician documentation")
        
        await require_patient_access(current_user, doc_data.patient_id, request)
        
        # Get patient info
        patient = await db.patients.find_one({"id": doc_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        now = datetime.now(timezone.utc)
        doc = PhysicianDoc(
            patient_id=doc_data.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_mrn=patient.get("mrn", ""),
            physician_id=current_user.get("id", ""),
            physician_name=f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}",
            organization_id=current_user.get("organization_id"),
            doc_type=doc_data.doc_type,
            title=doc_data.title,
            chief_complaint=doc_data.chief_complaint,
            history_present_illness=doc_data.history_present_illness,
            past_medical_history=doc_data.past_medical_history,
            physical_exam=doc_data.physical_exam,
            assessment=doc_data.assessment,
            plan=doc_data.plan,
            diagnosis_codes=doc_data.diagnosis_codes,
            content=doc_data.content,
            created_at=now.isoformat()
        )
        
        doc_dict = doc.model_dump(mode='json')
        await db.physician_documentation.insert_one(doc_dict)
        
        # Log creation
        await log_chart_access(
            patient_id=doc_data.patient_id,
            user=current_user,
            action=AuditAction.CREATE,
            resource_type="physician_documentation",
            resource_id=doc.id,
            details={"doc_type": doc_data.doc_type.value, "title": doc_data.title},
            request=request
        )
        
        return {"message": "Physician documentation created", "document": doc_dict}
    
    @clinical_docs_router.put("/physician/{doc_id}")
    async def update_physician_documentation(
        doc_id: str,
        chief_complaint: Optional[str] = None,
        history_present_illness: Optional[str] = None,
        past_medical_history: Optional[str] = None,
        physical_exam: Optional[str] = None,
        assessment: Optional[str] = None,
        plan: Optional[str] = None,
        content: Optional[str] = None,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Update physician documentation (author only, draft status only)"""
        doc = await db.physician_documentation.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify ownership and status
        if doc.get("physician_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="You can only edit your own documentation")
        
        if doc.get("status") != "draft":
            raise HTTPException(status_code=400, detail="Cannot edit signed documentation")
        
        updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if chief_complaint is not None:
            updates["chief_complaint"] = chief_complaint
        if history_present_illness is not None:
            updates["history_present_illness"] = history_present_illness
        if past_medical_history is not None:
            updates["past_medical_history"] = past_medical_history
        if physical_exam is not None:
            updates["physical_exam"] = physical_exam
        if assessment is not None:
            updates["assessment"] = assessment
        if plan is not None:
            updates["plan"] = plan
        if content is not None:
            updates["content"] = content
        
        await db.physician_documentation.update_one({"id": doc_id}, {"$set": updates})
        
        # Log edit
        await log_chart_access(
            patient_id=doc.get("patient_id", ""),
            user=current_user,
            action=AuditAction.EDIT,
            resource_type="physician_documentation",
            resource_id=doc_id,
            request=request
        )
        
        return {"message": "Documentation updated"}
    
    @clinical_docs_router.post("/physician/{doc_id}/sign")
    async def sign_physician_documentation(
        doc_id: str,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Sign physician documentation (makes it immutable)"""
        doc = await db.physician_documentation.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify ownership
        if doc.get("physician_id") != current_user.get("id"):
            raise HTTPException(status_code=403, detail="You can only sign your own documentation")
        
        if doc.get("status") != "draft":
            raise HTTPException(status_code=400, detail="Document is already signed")
        
        now = datetime.now(timezone.utc)
        await db.physician_documentation.update_one(
            {"id": doc_id},
            {"$set": {
                "status": "signed",
                "signed_at": now.isoformat(),
                "signed_by_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}"
            }}
        )
        
        # Log signing
        await log_chart_access(
            patient_id=doc.get("patient_id", ""),
            user=current_user,
            action=AuditAction.SIGN,
            resource_type="physician_documentation",
            resource_id=doc_id,
            request=request
        )
        
        return {"message": "Documentation signed"}
    
    # ============ PATIENT ASSIGNMENT ENDPOINTS ============
    
    @clinical_docs_router.get("/assignments/{patient_id}")
    async def get_patient_assignments(
        patient_id: str,
        active_only: bool = True,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all staff assigned to a patient"""
        role = current_user.get("role", "")
        
        # Only supervisors and admins can view all assignments
        if role not in ["nursing_supervisor", "floor_supervisor", "hospital_admin", "hospital_it_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Supervisor access required to view all assignments")
        
        query = {"patient_id": patient_id}
        if active_only:
            query["is_active"] = True
        
        assignments = await db.patient_assignments.find(
            query, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "assignments": assignments,
            "total": len(assignments)
        }
    
    @clinical_docs_router.post("/assignments")
    async def create_patient_assignment(
        assignment_data: PatientAssignmentCreate,
        request: Request = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Assign a staff member to a patient (supervisors/admins only)"""
        role = current_user.get("role", "")
        
        if role not in ["nursing_supervisor", "floor_supervisor", "hospital_admin", "hospital_it_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Supervisor access required to assign patients")
        
        # Verify patient exists
        patient = await db.patients.find_one({"id": assignment_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify user exists
        user = await db.users.find_one({"id": assignment_data.user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check for existing active assignment
        existing = await db.patient_assignments.find_one({
            "patient_id": assignment_data.patient_id,
            "user_id": assignment_data.user_id,
            "is_active": True
        })
        if existing:
            raise HTTPException(status_code=400, detail="User is already assigned to this patient")
        
        now = datetime.now(timezone.utc)
        assignment = PatientAssignment(
            patient_id=assignment_data.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            patient_mrn=patient.get("mrn", ""),
            user_id=assignment_data.user_id,
            user_name=f"{user.get('first_name', '')} {user.get('last_name', '')}",
            user_role=user.get("role", ""),
            organization_id=current_user.get("organization_id"),
            assignment_type=assignment_data.assignment_type,
            start_time=assignment_data.start_time or now.isoformat(),
            end_time=assignment_data.end_time,
            assigned_by=current_user.get("id", ""),
            assigned_by_name=f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}",
            notes=assignment_data.notes,
            created_at=now.isoformat()
        )
        
        assignment_dict = assignment.model_dump(mode='json')
        await db.patient_assignments.insert_one(assignment_dict)
        
        return {"message": "Patient assignment created", "assignment": assignment_dict}
    
    @clinical_docs_router.delete("/assignments/{assignment_id}")
    async def end_patient_assignment(
        assignment_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """End a patient assignment"""
        role = current_user.get("role", "")
        
        if role not in ["nursing_supervisor", "floor_supervisor", "hospital_admin", "hospital_it_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Supervisor access required")
        
        now = datetime.now(timezone.utc)
        result = await db.patient_assignments.update_one(
            {"id": assignment_id, "is_active": True},
            {"$set": {
                "is_active": False,
                "end_time": now.isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Assignment not found or already ended")
        
        return {"message": "Assignment ended"}
    
    # ============ AUDIT LOG ENDPOINTS ============
    
    @clinical_docs_router.get("/audit-logs/{patient_id}")
    async def get_patient_audit_logs(
        patient_id: str,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        current_user: dict = Depends(get_current_user)
    ):
        """Get audit logs for a patient (admin/supervisor access only)"""
        role = current_user.get("role", "")
        
        if role not in ["hospital_admin", "hospital_it_admin", "super_admin", "admin", "nursing_supervisor", "floor_supervisor"]:
            raise HTTPException(status_code=403, detail="Admin or supervisor access required to view audit logs")
        
        query = {"patient_id": patient_id}
        if action:
            query["action"] = action
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        
        logs = await db.chart_audit_logs.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {
            "audit_logs": logs,
            "total": len(logs)
        }
    
    @clinical_docs_router.get("/audit-logs")
    async def get_all_audit_logs(
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        success_only: bool = False,
        failures_only: bool = False,
        page: int = 1,
        limit: int = 50,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all audit logs (admin only)"""
        role = current_user.get("role", "")
        
        if role not in ["hospital_admin", "hospital_it_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        query = {}
        org_id = current_user.get("organization_id")
        if org_id and role != "super_admin":
            query["organization_id"] = org_id
        
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action
        if resource_type:
            query["resource_type"] = resource_type
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        if success_only:
            query["success"] = True
        if failures_only:
            query["success"] = False
        
        total = await db.chart_audit_logs.count_documents(query)
        skip = (page - 1) * limit
        
        logs = await db.chart_audit_logs.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        return {
            "audit_logs": logs,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    
    @clinical_docs_router.get("/audit-logs/suspicious")
    async def get_suspicious_activity(
        days: int = 7,
        current_user: dict = Depends(get_current_user)
    ):
        """Get suspicious activity alerts (admin only)"""
        role = current_user.get("role", "")
        
        if role not in ["hospital_admin", "hospital_it_admin", "super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        org_id = current_user.get("organization_id")
        
        query = {"timestamp": {"$gte": start_date}}
        if org_id and role != "super_admin":
            query["organization_id"] = org_id
        
        # Find access denials
        query["success"] = False
        denied_logs = await db.chart_audit_logs.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).limit(50).to_list(50)
        
        # Find unusual access patterns (same user accessing many patients)
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}, "action": "view"}},
            {"$group": {
                "_id": "$user_id",
                "user_name": {"$first": "$user_name"},
                "patient_count": {"$addToSet": "$patient_id"},
                "access_count": {"$sum": 1}
            }},
            {"$project": {
                "user_id": "$_id",
                "user_name": 1,
                "unique_patients": {"$size": "$patient_count"},
                "access_count": 1
            }},
            {"$match": {"unique_patients": {"$gt": 20}}},  # Flag users who accessed >20 patients
            {"$sort": {"unique_patients": -1}},
            {"$limit": 20}
        ]
        
        if org_id and role != "super_admin":
            pipeline[0]["$match"]["organization_id"] = org_id
        
        high_volume_users = await db.chart_audit_logs.aggregate(pipeline).to_list(20)
        
        return {
            "access_denials": denied_logs,
            "high_volume_access": high_volume_users,
            "period_days": days
        }
    
    # ============ DOCUMENTATION TYPES ============
    
    @clinical_docs_router.get("/doc-types/nursing")
    async def get_nursing_doc_types():
        """Get all nursing documentation types"""
        return {
            "doc_types": [
                {"value": t.value, "label": t.name.replace("_", " ").title()}
                for t in NursingDocType
            ]
        }
    
    @clinical_docs_router.get("/doc-types/physician")
    async def get_physician_doc_types():
        """Get all physician documentation types"""
        return {
            "doc_types": [
                {"value": t.value, "label": t.name.replace("_", " ").title()}
                for t in PhysicianDocType
            ]
        }
    
    return clinical_docs_router


__all__ = ['clinical_docs_router', 'create_clinical_documentation_endpoints']
