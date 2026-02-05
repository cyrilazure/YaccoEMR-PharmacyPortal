"""
NHIS Claims & Billing Module for Yacco EMR
Ghana National Health Insurance Scheme Integration
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum

nhis_router = APIRouter(prefix="/api/nhis", tags=["NHIS Claims & Billing"])


# ============== Enums ==============

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    APPEALED = "appealed"


class ServiceType(str, Enum):
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    MATERNITY = "maternity"
    SURGICAL = "surgical"
    DIAGNOSTIC = "diagnostic"


# ============== Pydantic Models ==============

class NHISMembershipVerify(BaseModel):
    nhis_id: str
    patient_name: Optional[str] = None
    date_of_birth: Optional[str] = None


class ClaimLineItem(BaseModel):
    service_code: str
    service_description: str
    quantity: int = 1
    unit_price: float
    total_price: float
    service_date: str
    diagnosis_code: Optional[str] = None
    notes: Optional[str] = None


class ClaimCreate(BaseModel):
    patient_id: str
    nhis_id: str
    encounter_id: Optional[str] = None
    service_type: ServiceType
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    primary_diagnosis: str
    secondary_diagnoses: List[str] = []
    procedure_codes: List[str] = []
    line_items: List[ClaimLineItem]
    total_amount: float
    co_payment_amount: float = 0
    notes: Optional[str] = None


class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    reviewer_notes: Optional[str] = None
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None


# ============== NHIS Tariff Codes (Ghana Standard) ==============

NHIS_TARIFF_CODES = [
    # Outpatient Services
    {"code": "OPD001", "description": "General Consultation", "category": "consultation", "price": 15.00},
    {"code": "OPD002", "description": "Specialist Consultation", "category": "consultation", "price": 25.00},
    {"code": "OPD003", "description": "Follow-up Visit", "category": "consultation", "price": 10.00},
    
    # Laboratory Services
    {"code": "LAB001", "description": "Full Blood Count", "category": "laboratory", "price": 20.00},
    {"code": "LAB002", "description": "Blood Glucose (Random)", "category": "laboratory", "price": 8.00},
    {"code": "LAB003", "description": "Blood Glucose (Fasting)", "category": "laboratory", "price": 10.00},
    {"code": "LAB004", "description": "Malaria RDT", "category": "laboratory", "price": 5.00},
    {"code": "LAB005", "description": "Urinalysis", "category": "laboratory", "price": 8.00},
    {"code": "LAB006", "description": "Liver Function Test", "category": "laboratory", "price": 35.00},
    {"code": "LAB007", "description": "Renal Function Test", "category": "laboratory", "price": 30.00},
    {"code": "LAB008", "description": "Lipid Profile", "category": "laboratory", "price": 40.00},
    {"code": "LAB009", "description": "HbA1c", "category": "laboratory", "price": 45.00},
    {"code": "LAB010", "description": "HIV Screening", "category": "laboratory", "price": 15.00},
    
    # Imaging Services
    {"code": "IMG001", "description": "Chest X-Ray", "category": "imaging", "price": 40.00},
    {"code": "IMG002", "description": "Abdominal X-Ray", "category": "imaging", "price": 45.00},
    {"code": "IMG003", "description": "Abdominal Ultrasound", "category": "imaging", "price": 60.00},
    {"code": "IMG004", "description": "Pelvic Ultrasound", "category": "imaging", "price": 55.00},
    {"code": "IMG005", "description": "CT Scan - Head", "category": "imaging", "price": 350.00},
    {"code": "IMG006", "description": "CT Scan - Abdomen", "category": "imaging", "price": 400.00},
    {"code": "IMG007", "description": "MRI - Brain", "category": "imaging", "price": 600.00},
    
    # Procedures
    {"code": "PRC001", "description": "Wound Dressing - Simple", "category": "procedure", "price": 15.00},
    {"code": "PRC002", "description": "Wound Dressing - Complex", "category": "procedure", "price": 30.00},
    {"code": "PRC003", "description": "IV Cannulation", "category": "procedure", "price": 10.00},
    {"code": "PRC004", "description": "Catheterization", "category": "procedure", "price": 25.00},
    {"code": "PRC005", "description": "Suturing - Minor", "category": "procedure", "price": 50.00},
    {"code": "PRC006", "description": "Incision & Drainage", "category": "procedure", "price": 80.00},
    
    # Medications (Common)
    {"code": "MED001", "description": "Paracetamol 500mg (10 tabs)", "category": "medication", "price": 2.00},
    {"code": "MED002", "description": "Amoxicillin 500mg (21 caps)", "category": "medication", "price": 8.00},
    {"code": "MED003", "description": "Artemether-Lumefantrine", "category": "medication", "price": 12.00},
    {"code": "MED004", "description": "Metformin 500mg (30 tabs)", "category": "medication", "price": 6.00},
    {"code": "MED005", "description": "Amlodipine 5mg (30 tabs)", "category": "medication", "price": 10.00},
    
    # Inpatient Services
    {"code": "INP001", "description": "General Ward - Per Day", "category": "inpatient", "price": 50.00},
    {"code": "INP002", "description": "ICU - Per Day", "category": "inpatient", "price": 200.00},
    {"code": "INP003", "description": "Private Room - Per Day", "category": "inpatient", "price": 150.00},
    {"code": "INP004", "description": "Nursing Care - Per Day", "category": "inpatient", "price": 30.00},
    
    # Surgical Services
    {"code": "SRG001", "description": "Minor Surgery", "category": "surgical", "price": 200.00},
    {"code": "SRG002", "description": "Intermediate Surgery", "category": "surgical", "price": 500.00},
    {"code": "SRG003", "description": "Major Surgery", "category": "surgical", "price": 1000.00},
    {"code": "SRG004", "description": "Cesarean Section", "category": "surgical", "price": 800.00},
    
    # Maternity Services
    {"code": "MAT001", "description": "Antenatal Visit", "category": "maternity", "price": 15.00},
    {"code": "MAT002", "description": "Normal Delivery", "category": "maternity", "price": 300.00},
    {"code": "MAT003", "description": "Postnatal Care", "category": "maternity", "price": 20.00},
]

# ICD-10 Diagnosis Codes (Common in Ghana)
ICD10_CODES = [
    {"code": "A09", "description": "Infectious gastroenteritis and colitis"},
    {"code": "B50", "description": "Plasmodium falciparum malaria"},
    {"code": "B54", "description": "Unspecified malaria"},
    {"code": "E11", "description": "Type 2 diabetes mellitus"},
    {"code": "I10", "description": "Essential (primary) hypertension"},
    {"code": "J06", "description": "Acute upper respiratory infections"},
    {"code": "J18", "description": "Pneumonia"},
    {"code": "K29", "description": "Gastritis and duodenitis"},
    {"code": "N39", "description": "Urinary tract infection"},
    {"code": "O80", "description": "Single spontaneous delivery"},
    {"code": "O82", "description": "Encounter for cesarean delivery"},
    {"code": "R50", "description": "Fever of other and unknown origin"},
]


def create_nhis_endpoints(db, get_current_user):
    """Create NHIS claims API endpoints"""
    
    @nhis_router.get("/tariff-codes")
    async def get_tariff_codes(category: Optional[str] = None):
        """Get NHIS tariff codes"""
        if category:
            return [t for t in NHIS_TARIFF_CODES if t["category"] == category]
        return NHIS_TARIFF_CODES
    
    @nhis_router.get("/diagnosis-codes")
    async def get_diagnosis_codes(search: Optional[str] = None):
        """Get ICD-10 diagnosis codes"""
        if search:
            search_lower = search.lower()
            return [c for c in ICD10_CODES if search_lower in c["code"].lower() or search_lower in c["description"].lower()]
        return ICD10_CODES
    
    @nhis_router.post("/verify-membership")
    async def verify_nhis_membership(
        data: NHISMembershipVerify,
        user: dict = Depends(get_current_user)
    ):
        """Verify NHIS membership status (Mock - Real API integration needed)"""
        # In production, this would call Ghana NHIS API
        # For now, we simulate verification
        
        # Check if patient exists with this NHIS ID
        patient = await db["patients"].find_one({"nhis_id": data.nhis_id})
        
        # Mock verification response
        is_valid = data.nhis_id.startswith("NHIS") or len(data.nhis_id) >= 10
        
        return {
            "nhis_id": data.nhis_id,
            "is_valid": is_valid,
            "membership_status": "active" if is_valid else "invalid",
            "expiry_date": "2026-12-31" if is_valid else None,
            "member_name": patient.get("first_name", "") + " " + patient.get("last_name", "") if patient else data.patient_name,
            "scheme_type": "Premium" if is_valid else None,
            "coverage_level": "Full" if is_valid else None,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "note": "MOCK VERIFICATION - Connect to NHIS API for production"
        }
    
    @nhis_router.post("/claims/create")
    async def create_claim(
        data: ClaimCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new NHIS claim"""
        allowed_roles = ["biller", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Billing access required")
        
        # Verify patient
        patient = await db["patients"].find_one({"id": data.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        claim_id = str(uuid.uuid4())
        claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{claim_id[:8].upper()}"
        
        claim_doc = {
            "id": claim_id,
            "claim_number": claim_number,
            "patient_id": data.patient_id,
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            "patient_mrn": patient.get("mrn"),
            "nhis_id": data.nhis_id,
            "encounter_id": data.encounter_id,
            "service_type": data.service_type,
            "admission_date": data.admission_date,
            "discharge_date": data.discharge_date,
            "primary_diagnosis": data.primary_diagnosis,
            "secondary_diagnoses": data.secondary_diagnoses,
            "procedure_codes": data.procedure_codes,
            "line_items": [item.dict() for item in data.line_items],
            "total_amount": data.total_amount,
            "co_payment_amount": data.co_payment_amount,
            "approved_amount": None,
            "notes": data.notes,
            "status": ClaimStatus.DRAFT,
            "submitted_by": None,
            "submitted_at": None,
            "reviewer_notes": None,
            "rejection_reason": None,
            "organization_id": user.get("organization_id"),
            "created_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["nhis_claims"].insert_one(claim_doc)
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "nhis_claim_created",
            "resource_type": "nhis_claim",
            "resource_id": claim_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"claim_number": claim_number, "total_amount": data.total_amount},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Claim created successfully", "claim": claim_doc}
    
    @nhis_router.post("/claims/{claim_id}/submit")
    async def submit_claim(
        claim_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Submit claim to NHIS for review"""
        claim = await db["nhis_claims"].find_one({"id": claim_id})
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if claim["status"] != ClaimStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Only draft claims can be submitted")
        
        await db["nhis_claims"].update_one(
            {"id": claim_id},
            {"$set": {
                "status": ClaimStatus.SUBMITTED,
                "submitted_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "nhis_claim_submitted",
            "resource_type": "nhis_claim",
            "resource_id": claim_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"claim_number": claim.get("claim_number")},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Claim submitted successfully", "status": ClaimStatus.SUBMITTED}
    
    @nhis_router.put("/claims/{claim_id}/status")
    async def update_claim_status(
        claim_id: str,
        data: ClaimUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update claim status (for processing workflow)"""
        claim = await db["nhis_claims"].find_one({"id": claim_id})
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if data.status:
            update_data["status"] = data.status
        if data.reviewer_notes:
            update_data["reviewer_notes"] = data.reviewer_notes
        if data.approved_amount is not None:
            update_data["approved_amount"] = data.approved_amount
        if data.rejection_reason:
            update_data["rejection_reason"] = data.rejection_reason
        
        await db["nhis_claims"].update_one({"id": claim_id}, {"$set": update_data})
        
        return {"message": "Claim updated", "status": data.status}
    
    @nhis_router.get("/claims")
    async def get_claims(
        status: Optional[str] = None,
        patient_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get NHIS claims list"""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        if patient_id:
            query["patient_id"] = patient_id
        
        claims = await db["nhis_claims"].find(query).sort("created_at", -1).to_list(500)
        
        # Calculate stats
        stats = {
            "total_claims": len(claims),
            "draft": len([c for c in claims if c["status"] == ClaimStatus.DRAFT]),
            "submitted": len([c for c in claims if c["status"] == ClaimStatus.SUBMITTED]),
            "under_review": len([c for c in claims if c["status"] == ClaimStatus.UNDER_REVIEW]),
            "approved": len([c for c in claims if c["status"] == ClaimStatus.APPROVED]),
            "rejected": len([c for c in claims if c["status"] == ClaimStatus.REJECTED]),
            "paid": len([c for c in claims if c["status"] == ClaimStatus.PAID]),
            "total_amount": sum(c.get("total_amount", 0) for c in claims),
            "approved_amount": sum(c.get("approved_amount", 0) or 0 for c in claims if c["status"] in [ClaimStatus.APPROVED, ClaimStatus.PAID])
        }
        
        return {"claims": claims, "stats": stats}
    
    @nhis_router.get("/claims/{claim_id}")
    async def get_claim_details(
        claim_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get detailed claim information"""
        claim = await db["nhis_claims"].find_one({"id": claim_id})
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        return claim
    
    @nhis_router.get("/patient/{patient_id}/billing-summary")
    async def get_patient_billing_summary(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get billing summary for a patient"""
        claims = await db["nhis_claims"].find({"patient_id": patient_id}).to_list(100)
        
        return {
            "patient_id": patient_id,
            "total_claims": len(claims),
            "total_billed": sum(c.get("total_amount", 0) for c in claims),
            "total_approved": sum(c.get("approved_amount", 0) or 0 for c in claims),
            "total_co_payments": sum(c.get("co_payment_amount", 0) for c in claims),
            "pending_claims": len([c for c in claims if c["status"] in [ClaimStatus.DRAFT, ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW]]),
            "claims": claims
        }
    
    return nhis_router
