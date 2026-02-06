"""
NHIS (National Health Insurance Scheme) Pharmacy Claims Integration Module
Handles NHIS member verification, pharmacy claims submission, and reimbursement tracking
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from enum import Enum

nhis_router = APIRouter(prefix="/api/nhis", tags=["NHIS Claims"])


# ============== Enums ==============

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_APPROVED = "partially_approved"
    PAID = "paid"
    APPEALED = "appealed"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING_RENEWAL = "pending_renewal"


class ClaimType(str, Enum):
    PHARMACY = "pharmacy"
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    MATERNITY = "maternity"
    EMERGENCY = "emergency"


# ============== Pydantic Models ==============

class NHISMemberVerification(BaseModel):
    membership_id: str
    date_of_birth: Optional[str] = None


class NHISMemberResponse(BaseModel):
    membership_id: str
    full_name: str
    date_of_birth: str
    gender: str
    status: MembershipStatus
    expiry_date: str
    coverage_type: str
    region: str
    district: str
    verified: bool
    message: str


class NHISClaimItem(BaseModel):
    item_code: str
    item_name: str
    quantity: int
    unit_price: float
    total_price: float
    nhis_price: Optional[float] = None  # NHIS approved price
    is_covered: bool = True


class NHISPharmacyClaimCreate(BaseModel):
    patient_id: str
    patient_name: str
    membership_id: str
    prescription_id: Optional[str] = None
    diagnosis_codes: List[str]
    claim_items: List[NHISClaimItem]
    prescription_date: str
    dispensing_date: str
    prescriber_name: str
    prescriber_license: Optional[str] = None
    notes: Optional[str] = None


class NHISClaimUpdate(BaseModel):
    status: ClaimStatus
    nhis_reference: Optional[str] = None
    approved_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    reviewer_notes: Optional[str] = None


# ============== NHIS Tariff Database (Ghana NHIS Drug Tariff) ==============

NHIS_DRUG_TARIFF = {
    # Antimalarials
    "ARTEM-LUM-20/120": {"name": "Artemether-Lumefantrine 20/120mg", "nhis_price": 12.50, "covered": True},
    "ARTEM-LUM-80/480": {"name": "Artemether-Lumefantrine 80/480mg", "nhis_price": 18.00, "covered": True},
    "ARTESUNATE-60": {"name": "Artesunate 60mg Injection", "nhis_price": 25.00, "covered": True},
    
    # Antibiotics
    "AMOX-500-CAP": {"name": "Amoxicillin 500mg Capsule", "nhis_price": 0.45, "covered": True},
    "AMOX-CLAV-625": {"name": "Amoxicillin-Clavulanate 625mg", "nhis_price": 2.50, "covered": True},
    "CIPROFLOX-500": {"name": "Ciprofloxacin 500mg", "nhis_price": 0.80, "covered": True},
    "AZITHRO-500": {"name": "Azithromycin 500mg", "nhis_price": 3.50, "covered": True},
    "METRO-400": {"name": "Metronidazole 400mg", "nhis_price": 0.25, "covered": True},
    
    # Cardiovascular
    "AMLODIP-5": {"name": "Amlodipine 5mg", "nhis_price": 0.35, "covered": True},
    "AMLODIP-10": {"name": "Amlodipine 10mg", "nhis_price": 0.45, "covered": True},
    "LISINOPRIL-10": {"name": "Lisinopril 10mg", "nhis_price": 0.40, "covered": True},
    "LOSARTAN-50": {"name": "Losartan 50mg", "nhis_price": 0.55, "covered": True},
    "ATORVAST-20": {"name": "Atorvastatin 20mg", "nhis_price": 1.20, "covered": True},
    "FURO-40": {"name": "Furosemide 40mg", "nhis_price": 0.20, "covered": True},
    
    # Diabetes
    "METFORM-500": {"name": "Metformin 500mg", "nhis_price": 0.15, "covered": True},
    "METFORM-850": {"name": "Metformin 850mg", "nhis_price": 0.20, "covered": True},
    "GLIBEN-5": {"name": "Glibenclamide 5mg", "nhis_price": 0.10, "covered": True},
    "INSULIN-NPH": {"name": "Insulin NPH 100IU/mL", "nhis_price": 35.00, "covered": True},
    
    # Analgesics
    "PARACET-500": {"name": "Paracetamol 500mg", "nhis_price": 0.05, "covered": True},
    "IBUPROF-400": {"name": "Ibuprofen 400mg", "nhis_price": 0.10, "covered": True},
    "DICLOF-50": {"name": "Diclofenac 50mg", "nhis_price": 0.15, "covered": True},
    
    # Respiratory
    "SALBUTAM-INH": {"name": "Salbutamol Inhaler 100mcg", "nhis_price": 15.00, "covered": True},
    "PREDNIS-5": {"name": "Prednisolone 5mg", "nhis_price": 0.08, "covered": True},
    
    # GI
    "OMEPRAZ-20": {"name": "Omeprazole 20mg", "nhis_price": 0.60, "covered": True},
    "RABEPRAZ-20": {"name": "Rabeprazole 20mg", "nhis_price": 0.80, "covered": True},
    "ORS-PKT": {"name": "ORS Packet", "nhis_price": 0.50, "covered": True},
    
    # Vitamins & Supplements
    "FOLIC-5": {"name": "Folic Acid 5mg", "nhis_price": 0.05, "covered": True},
    "FERROUS-200": {"name": "Ferrous Sulphate 200mg", "nhis_price": 0.05, "covered": True},
    "VIT-B-COMP": {"name": "Vitamin B Complex", "nhis_price": 0.08, "covered": True},
    
    # Non-covered items (example)
    "SILDENAFIL-50": {"name": "Sildenafil 50mg", "nhis_price": None, "covered": False},
    "COSMETIC-CREAM": {"name": "Cosmetic Preparations", "nhis_price": None, "covered": False},
}

# Simulated NHIS Member Database
SAMPLE_NHIS_MEMBERS = {
    "NHIS-2024-001234": {
        "membership_id": "NHIS-2024-001234",
        "full_name": "Kofi Mensah Asante",
        "date_of_birth": "1985-03-15",
        "gender": "Male",
        "status": MembershipStatus.ACTIVE,
        "expiry_date": "2025-12-31",
        "coverage_type": "Premium",
        "region": "Greater Accra",
        "district": "Accra Metropolitan"
    },
    "NHIS-2023-005678": {
        "membership_id": "NHIS-2023-005678",
        "full_name": "Ama Serwaa Boateng",
        "date_of_birth": "1990-07-22",
        "gender": "Female",
        "status": MembershipStatus.ACTIVE,
        "expiry_date": "2025-06-30",
        "coverage_type": "Standard",
        "region": "Ashanti",
        "district": "Kumasi Metropolitan"
    },
    "NHIS-2022-009012": {
        "membership_id": "NHIS-2022-009012",
        "full_name": "Kwame Owusu Darko",
        "date_of_birth": "1978-11-08",
        "gender": "Male",
        "status": MembershipStatus.EXPIRED,
        "expiry_date": "2024-03-31",
        "coverage_type": "Standard",
        "region": "Western",
        "district": "Sekondi-Takoradi"
    },
    "NHIS-2024-003456": {
        "membership_id": "NHIS-2024-003456",
        "full_name": "Akua Amponsah",
        "date_of_birth": "1995-01-20",
        "gender": "Female",
        "status": MembershipStatus.ACTIVE,
        "expiry_date": "2026-01-31",
        "coverage_type": "Premium",
        "region": "Central",
        "district": "Cape Coast Metropolitan"
    }
}


def create_nhis_endpoints(db, get_current_user):
    """Create NHIS claims API endpoints"""
    
    # ============== Member Verification ==============
    
    @nhis_router.post("/verify-member")
    async def verify_nhis_member(
        data: NHISMemberVerification,
        user: dict = Depends(get_current_user)
    ):
        """Verify NHIS membership status"""
        # In production, this would call the actual NHIS verification API
        # For now, using mock data
        
        member = SAMPLE_NHIS_MEMBERS.get(data.membership_id)
        
        if not member:
            return {
                "membership_id": data.membership_id,
                "full_name": "",
                "date_of_birth": "",
                "gender": "",
                "status": "not_found",
                "expiry_date": "",
                "coverage_type": "",
                "region": "",
                "district": "",
                "verified": False,
                "message": "NHIS membership not found. Please verify the membership ID."
            }
        
        # Check if expired
        is_active = member["status"] == MembershipStatus.ACTIVE
        
        return {
            **member,
            "status": member["status"].value if hasattr(member["status"], "value") else member["status"],
            "verified": is_active,
            "message": "Member verified successfully" if is_active else f"Membership is {member['status'].value if hasattr(member['status'], 'value') else member['status']}"
        }
    
    @nhis_router.get("/member/{membership_id}")
    async def get_member_details(
        membership_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get NHIS member details"""
        member = SAMPLE_NHIS_MEMBERS.get(membership_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        result = {**member}
        result["status"] = result["status"].value if hasattr(result["status"], "value") else result["status"]
        return result
    
    # ============== Drug Tariff Lookup ==============
    
    @nhis_router.get("/tariff")
    async def get_drug_tariff(
        search: Optional[str] = Query(None, description="Search by drug name or code"),
        covered_only: bool = Query(False, description="Show only covered drugs")
    ):
        """Get NHIS drug tariff list"""
        results = []
        
        for code, drug in NHIS_DRUG_TARIFF.items():
            if covered_only and not drug["covered"]:
                continue
            
            if search:
                if search.lower() not in code.lower() and search.lower() not in drug["name"].lower():
                    continue
            
            results.append({
                "code": code,
                "name": drug["name"],
                "nhis_price": drug["nhis_price"],
                "covered": drug["covered"]
            })
        
        return {"drugs": results, "total": len(results)}
    
    @nhis_router.get("/tariff/{drug_code}")
    async def get_drug_tariff_details(drug_code: str):
        """Get NHIS tariff price for a specific drug"""
        drug = NHIS_DRUG_TARIFF.get(drug_code)
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found in NHIS tariff")
        
        return {
            "code": drug_code,
            "name": drug["name"],
            "nhis_price": drug["nhis_price"],
            "covered": drug["covered"]
        }
    
    # ============== Claims Management ==============
    
    @nhis_router.post("/claims/pharmacy")
    async def create_pharmacy_claim(
        data: NHISPharmacyClaimCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create NHIS pharmacy claim"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "biller", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to create claims")
        
        # Verify NHIS membership
        member = SAMPLE_NHIS_MEMBERS.get(data.membership_id)
        if not member:
            raise HTTPException(status_code=400, detail="Invalid NHIS membership ID")
        
        if member["status"] != MembershipStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"NHIS membership is {member['status'].value}")
        
        # Calculate totals
        total_claimed = sum(item.total_price for item in data.claim_items)
        total_nhis_approved = sum(
            (item.nhis_price or NHIS_DRUG_TARIFF.get(item.item_code, {}).get("nhis_price", 0)) * item.quantity 
            for item in data.claim_items if item.is_covered
        )
        
        claim_id = str(uuid.uuid4())
        claim_number = f"NHIS-CLM-{datetime.now().strftime('%Y%m%d')}-{claim_id[:8].upper()}"
        
        claim_doc = {
            "id": claim_id,
            "claim_number": claim_number,
            "claim_type": ClaimType.PHARMACY.value,
            "patient_id": data.patient_id,
            "patient_name": data.patient_name,
            "membership_id": data.membership_id,
            "member_name": member["full_name"],
            "prescription_id": data.prescription_id,
            "diagnosis_codes": data.diagnosis_codes,
            "claim_items": [item.dict() for item in data.claim_items],
            "prescription_date": data.prescription_date,
            "dispensing_date": data.dispensing_date,
            "prescriber_name": data.prescriber_name,
            "prescriber_license": data.prescriber_license,
            "total_claimed": total_claimed,
            "total_nhis_approved": total_nhis_approved,
            "patient_copay": max(0, total_claimed - total_nhis_approved),
            "status": ClaimStatus.DRAFT.value,
            "nhis_reference": None,
            "submission_date": None,
            "approval_date": None,
            "payment_date": None,
            "rejection_reason": None,
            "reviewer_notes": None,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "created_by_id": user.get("id"),
            "created_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["nhis_claims"].insert_one(claim_doc)
        
        # Remove _id
        if "_id" in claim_doc:
            del claim_doc["_id"]
        
        return {
            "message": "NHIS claim created",
            "claim": claim_doc,
            "summary": {
                "total_claimed": total_claimed,
                "nhis_covers": total_nhis_approved,
                "patient_pays": max(0, total_claimed - total_nhis_approved)
            }
        }
    
    @nhis_router.get("/claims")
    async def get_claims(
        status: Optional[str] = None,
        claim_type: Optional[str] = None,
        membership_id: Optional[str] = None,
        from_date: Optional[str] = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: dict = Depends(get_current_user)
    ):
        """Get NHIS claims"""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        if claim_type:
            query["claim_type"] = claim_type
        if membership_id:
            query["membership_id"] = membership_id
        if from_date:
            query["created_at"] = {"$gte": from_date}
        
        claims = await db["nhis_claims"].find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        total = await db["nhis_claims"].count_documents(query)
        
        return {"claims": claims, "total": total, "limit": limit, "offset": offset}
    
    @nhis_router.get("/claims/{claim_id}")
    async def get_claim_details(
        claim_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get claim details"""
        claim = await db["nhis_claims"].find_one({"id": claim_id}, {"_id": 0})
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        return claim
    
    @nhis_router.post("/claims/{claim_id}/submit")
    async def submit_claim(
        claim_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Submit claim to NHIS for processing"""
        claim = await db["nhis_claims"].find_one({"id": claim_id})
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if claim["status"] != ClaimStatus.DRAFT.value:
            raise HTTPException(status_code=400, detail="Only draft claims can be submitted")
        
        # Generate NHIS reference (in production, this would come from NHIS API)
        nhis_ref = f"NHIA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{claim_id[:6].upper()}"
        
        await db["nhis_claims"].update_one(
            {"id": claim_id},
            {"$set": {
                "status": ClaimStatus.SUBMITTED.value,
                "nhis_reference": nhis_ref,
                "submission_date": datetime.now(timezone.utc).isoformat(),
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
            "details": {"claim_number": claim["claim_number"], "nhis_reference": nhis_ref},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Claim submitted to NHIS", "nhis_reference": nhis_ref}
    
    @nhis_router.put("/claims/{claim_id}/status")
    async def update_claim_status(
        claim_id: str,
        data: NHISClaimUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update claim status (for admin/NHIS response simulation)"""
        allowed_roles = ["hospital_admin", "biller", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        update_data = {
            "status": data.status.value if hasattr(data.status, "value") else data.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if data.nhis_reference:
            update_data["nhis_reference"] = data.nhis_reference
        if data.approved_amount is not None:
            update_data["approved_amount"] = data.approved_amount
        if data.rejection_reason:
            update_data["rejection_reason"] = data.rejection_reason
        if data.reviewer_notes:
            update_data["reviewer_notes"] = data.reviewer_notes
        
        if data.status == ClaimStatus.APPROVED:
            update_data["approval_date"] = datetime.now(timezone.utc).isoformat()
        elif data.status == ClaimStatus.PAID:
            update_data["payment_date"] = datetime.now(timezone.utc).isoformat()
        
        await db["nhis_claims"].update_one({"id": claim_id}, {"$set": update_data})
        
        return {"message": f"Claim status updated to {data.status}"}
    
    # ============== Dashboard & Reports ==============
    
    @nhis_router.get("/dashboard")
    async def get_nhis_dashboard(user: dict = Depends(get_current_user)):
        """Get NHIS claims dashboard"""
        org_id = user.get("organization_id")
        
        # Get all claims for organization
        all_claims = await db["nhis_claims"].find({"organization_id": org_id}, {"_id": 0}).to_list(1000)
        
        # Calculate stats
        total_claims = len(all_claims)
        draft_claims = len([c for c in all_claims if c["status"] == ClaimStatus.DRAFT.value])
        submitted_claims = len([c for c in all_claims if c["status"] == ClaimStatus.SUBMITTED.value])
        approved_claims = len([c for c in all_claims if c["status"] == ClaimStatus.APPROVED.value])
        rejected_claims = len([c for c in all_claims if c["status"] == ClaimStatus.REJECTED.value])
        paid_claims = len([c for c in all_claims if c["status"] == ClaimStatus.PAID.value])
        
        total_claimed = sum(c.get("total_claimed", 0) for c in all_claims)
        total_approved = sum(c.get("approved_amount", c.get("total_nhis_approved", 0)) for c in all_claims if c["status"] in [ClaimStatus.APPROVED.value, ClaimStatus.PAID.value])
        total_paid = sum(c.get("approved_amount", c.get("total_nhis_approved", 0)) for c in all_claims if c["status"] == ClaimStatus.PAID.value)
        
        # Monthly breakdown (current month)
        current_month = datetime.now().strftime("%Y-%m")
        monthly_claims = [c for c in all_claims if c.get("created_at", "").startswith(current_month)]
        
        return {
            "summary": {
                "total_claims": total_claims,
                "by_status": {
                    "draft": draft_claims,
                    "submitted": submitted_claims,
                    "approved": approved_claims,
                    "rejected": rejected_claims,
                    "paid": paid_claims
                }
            },
            "financials": {
                "total_claimed": round(total_claimed, 2),
                "total_approved": round(total_approved, 2),
                "total_paid": round(total_paid, 2),
                "pending_payment": round(total_approved - total_paid, 2)
            },
            "current_month": {
                "claims_submitted": len(monthly_claims),
                "amount_claimed": round(sum(c.get("total_claimed", 0) for c in monthly_claims), 2)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @nhis_router.get("/reports/claims-summary")
    async def get_claims_summary_report(
        from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
        to_date: str = Query(..., description="End date (YYYY-MM-DD)"),
        user: dict = Depends(get_current_user)
    ):
        """Generate claims summary report"""
        query = {
            "organization_id": user.get("organization_id"),
            "created_at": {"$gte": from_date, "$lte": to_date + "T23:59:59"}
        }
        
        claims = await db["nhis_claims"].find(query, {"_id": 0}).to_list(1000)
        
        # Group by status
        by_status = {}
        for claim in claims:
            status = claim.get("status", "unknown")
            if status not in by_status:
                by_status[status] = {"count": 0, "amount": 0}
            by_status[status]["count"] += 1
            by_status[status]["amount"] += claim.get("total_claimed", 0)
        
        return {
            "period": {"from": from_date, "to": to_date},
            "total_claims": len(claims),
            "total_amount": round(sum(c.get("total_claimed", 0) for c in claims), 2),
            "by_status": by_status,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    return nhis_router
