"""
Patient Consent Forms Module for Yacco EMR
HIPAA-Compliant Consent Management System

Supports:
- Multiple consent types (treatment, HIPAA, records release, etc.)
- Digital signatures
- Consent tracking and revocation
- Document storage
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import hashlib

consent_router = APIRouter(prefix="/api/consents", tags=["Consent Forms"])


# ============ Enums ============

class ConsentType(str, Enum):
    TREATMENT = "treatment"
    HIPAA = "hipaa"
    RECORDS_RELEASE = "records_release"
    PROCEDURE = "procedure"
    RESEARCH = "research"
    TELEHEALTH = "telehealth"
    MEDICATION = "medication"
    PHOTOGRAPHY = "photography"
    FINANCIAL = "financial"
    ADVANCE_DIRECTIVE = "advance_directive"
    MINOR_TREATMENT = "minor_treatment"


class ConsentStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ============ Models ============

class ConsentCreate(BaseModel):
    patient_id: str
    consent_type: ConsentType
    title: str
    description: str
    consent_text: str
    # For records release
    scope_start_date: Optional[str] = None
    scope_end_date: Optional[str] = None
    record_types_included: Optional[List[str]] = None
    recipient_organization_id: Optional[str] = None
    recipient_organization_name: Optional[str] = None
    purpose: Optional[str] = None
    # Expiration
    expiration_date: Optional[str] = None
    # Related request
    related_request_id: Optional[str] = None


class ConsentSign(BaseModel):
    patient_signature: str  # Base64 encoded signature image
    guardian_name: Optional[str] = None
    guardian_relationship: Optional[str] = None
    guardian_signature: Optional[str] = None


class ConsentRevoke(BaseModel):
    reason: str


class ConsentResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    organization_id: str
    consent_type: str
    title: str
    description: str
    status: str
    scope_start_date: Optional[str]
    scope_end_date: Optional[str]
    record_types_included: Optional[List[str]]
    recipient_organization_name: Optional[str]
    purpose: Optional[str]
    patient_signed_at: Optional[str]
    witness_name: Optional[str]
    witness_signed_at: Optional[str]
    effective_date: str
    expiration_date: Optional[str]
    revoked_at: Optional[str]
    revocation_reason: Optional[str]
    document_url: Optional[str]
    created_at: str


class ConsentTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consent_type: ConsentType
    name: str
    title: str
    description: str
    consent_text: str
    is_active: bool = True
    organization_id: Optional[str] = None  # None = system template


# ============ Consent Text Templates ============

CONSENT_TEMPLATES = {
    ConsentType.TREATMENT: {
        "title": "Consent for Treatment",
        "description": "General consent to receive medical treatment",
        "consent_text": """
I, the undersigned patient (or authorized representative), hereby consent to medical treatment 
by the physicians and staff at this healthcare facility. I understand that:

1. The practice of medicine is not an exact science and no guarantees have been made to me 
   regarding the outcome of treatments or procedures.

2. I have had the opportunity to discuss my condition and treatment options with my healthcare 
   provider and to ask questions.

3. I authorize the healthcare team to perform diagnostic procedures, administer medications, 
   and provide treatment as deemed necessary for my care.

4. I understand that I may refuse any treatment and that such refusal may have consequences 
   to my health that have been explained to me.

5. I authorize the release of medical information necessary for billing and insurance purposes.

This consent remains in effect until revoked in writing.
"""
    },
    ConsentType.HIPAA: {
        "title": "HIPAA Privacy Notice Acknowledgment",
        "description": "Acknowledgment of receipt of HIPAA privacy practices notice",
        "consent_text": """
NOTICE OF PRIVACY PRACTICES ACKNOWLEDGMENT

I acknowledge that I have received a copy of this organization's Notice of Privacy Practices.

I understand that:

1. My protected health information (PHI) may be used and disclosed for treatment, payment, 
   and healthcare operations.

2. I have the right to request restrictions on certain uses and disclosures of my PHI.

3. I have the right to receive confidential communications of my PHI.

4. I have the right to inspect and copy my PHI.

5. I have the right to request amendments to my PHI.

6. I have the right to receive an accounting of disclosures of my PHI.

7. I have the right to a paper copy of the Notice of Privacy Practices.

8. I may revoke any authorization I provide, except to the extent action has already been taken.

By signing below, I acknowledge receipt of the Notice of Privacy Practices.
"""
    },
    ConsentType.RECORDS_RELEASE: {
        "title": "Authorization for Release of Medical Records",
        "description": "Authorization to release protected health information to specified recipients",
        "consent_text": """
AUTHORIZATION FOR RELEASE OF PROTECTED HEALTH INFORMATION

I authorize the release of my protected health information as specified below:

INFORMATION TO BE RELEASED:
The health information to be released includes records from the date range and categories 
specified in this authorization.

PURPOSE:
This information is being released for the purpose stated in this authorization.

RECIPIENT:
The information will be released to the healthcare provider or organization specified.

I understand that:

1. I may revoke this authorization at any time by submitting a written request, except to 
   the extent that action has already been taken in reliance on this authorization.

2. Information disclosed pursuant to this authorization may be subject to re-disclosure by 
   the recipient and may no longer be protected by federal privacy regulations.

3. This authorization will expire on the date specified or one year from the date of 
   signature if no expiration date is specified.

4. I am entitled to a copy of this authorization.

5. My treatment, payment, enrollment, or eligibility for benefits will not be conditioned 
   on signing this authorization.
"""
    },
    ConsentType.TELEHEALTH: {
        "title": "Telehealth Informed Consent",
        "description": "Consent for receiving healthcare services via telemedicine",
        "consent_text": """
TELEHEALTH INFORMED CONSENT

I understand and consent to participating in telehealth services. I acknowledge that:

1. Telehealth involves the use of electronic communications to enable healthcare providers 
   to share individual patient medical information for the purpose of improving patient care.

2. The laws that protect privacy and the confidentiality of medical information also apply 
   to telehealth.

3. I understand that telehealth may involve electronic communication of my personal medical 
   information to other healthcare providers.

4. I have the right to withhold or withdraw my consent to the use of telehealth during my 
   care at any time without affecting my right to future care or treatment.

5. I understand that there are potential risks to this technology, including interruptions, 
   unauthorized access, and technical difficulties.

6. I understand that my healthcare provider may determine that the services delivered via 
   telehealth are not appropriate for some or all of my needs.

7. I agree to not record any telehealth sessions without written consent from my provider.

8. I am responsible for providing accurate information about my health and medical history.
"""
    }
}


# ============ Endpoints ============

def create_consent_endpoints(db, get_current_user):
    """Create consent form management endpoints"""
    
    @consent_router.get("/templates")
    async def get_consent_templates(
        consent_type: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get available consent templates"""
        templates = []
        
        for ctype, template in CONSENT_TEMPLATES.items():
            if consent_type and ctype.value != consent_type:
                continue
            templates.append({
                "consent_type": ctype.value,
                "name": ctype.value.replace("_", " ").title(),
                **template
            })
        
        # Get organization-specific templates
        org_id = current_user.get("organization_id")
        if org_id:
            org_templates = await db.consent_templates.find(
                {"organization_id": org_id, "is_active": True},
                {"_id": 0}
            ).to_list(50)
            templates.extend(org_templates)
        
        return templates
    
    @consent_router.get("/types")
    async def get_consent_types():
        """Get list of all consent types"""
        return [
            {"value": ct.value, "name": ct.value.replace("_", " ").title()}
            for ct in ConsentType
        ]
    
    @consent_router.post("", response_model=ConsentResponse)
    async def create_consent(
        consent_data: ConsentCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new consent form (pending signature)"""
        org_id = current_user.get("organization_id")
        
        # Verify patient exists
        patient = await db.patients.find_one({"id": consent_data.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        consent = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            **consent_data.model_dump(),
            "status": ConsentStatus.PENDING.value,
            "effective_date": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get("id")
        }
        
        await db.consent_forms.insert_one(consent)
        
        consent["patient_name"] = f"{patient['first_name']} {patient['last_name']}"
        return ConsentResponse(**consent)
    
    @consent_router.get("", response_model=List[ConsentResponse])
    async def get_consents(
        patient_id: Optional[str] = None,
        consent_type: Optional[str] = None,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get consent forms"""
        org_id = current_user.get("organization_id")
        
        query = {}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        if patient_id:
            query["patient_id"] = patient_id
        if consent_type:
            query["consent_type"] = consent_type
        if status:
            query["status"] = status
        
        consents = await db.consent_forms.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
        
        # Enrich with patient names
        for consent in consents:
            patient = await db.patients.find_one(
                {"id": consent["patient_id"]},
                {"_id": 0, "first_name": 1, "last_name": 1}
            )
            if patient:
                consent["patient_name"] = f"{patient['first_name']} {patient['last_name']}"
        
        return [ConsentResponse(**c) for c in consents]
    
    @consent_router.get("/patient/{patient_id}", response_model=List[ConsentResponse])
    async def get_patient_consents(
        patient_id: str,
        active_only: bool = False,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all consents for a patient"""
        query = {"patient_id": patient_id}
        
        if active_only:
            query["status"] = ConsentStatus.ACTIVE.value
        
        consents = await db.consent_forms.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        # Get patient name
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0, "first_name": 1, "last_name": 1})
        patient_name = f"{patient['first_name']} {patient['last_name']}" if patient else None
        
        for consent in consents:
            consent["patient_name"] = patient_name
        
        return [ConsentResponse(**c) for c in consents]
    
    @consent_router.get("/{consent_id}", response_model=ConsentResponse)
    async def get_consent(
        consent_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get a specific consent form"""
        consent = await db.consent_forms.find_one({"id": consent_id}, {"_id": 0})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent form not found")
        
        patient = await db.patients.find_one(
            {"id": consent["patient_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if patient:
            consent["patient_name"] = f"{patient['first_name']} {patient['last_name']}"
        
        return ConsentResponse(**consent)
    
    @consent_router.post("/{consent_id}/sign")
    async def sign_consent(
        consent_id: str,
        sign_data: ConsentSign,
        current_user: dict = Depends(get_current_user)
    ):
        """Sign a consent form"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent form not found")
        
        if consent.get("status") != ConsentStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Consent form is not pending signature")
        
        update_data = {
            "patient_signature": sign_data.patient_signature,
            "patient_signed_at": datetime.now(timezone.utc).isoformat(),
            "status": ConsentStatus.ACTIVE.value,
            "witness_id": current_user.get("id"),
            "witness_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
            "witness_signed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if sign_data.guardian_name:
            update_data["guardian_name"] = sign_data.guardian_name
            update_data["guardian_relationship"] = sign_data.guardian_relationship
            update_data["guardian_signature"] = sign_data.guardian_signature
        
        await db.consent_forms.update_one(
            {"id": consent_id},
            {"$set": update_data}
        )
        
        # Log audit event
        patient = await db.patients.find_one({"id": consent["patient_id"]})
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.get("id"),
            "user_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
            "user_role": current_user.get("role"),
            "action": "consent_given",
            "resource_type": "consent_form",
            "resource_id": consent_id,
            "patient_id": consent["patient_id"],
            "patient_name": f"{patient['first_name']} {patient['last_name']}" if patient else None,
            "organization_id": consent.get("organization_id"),
            "details": f"Patient signed {consent.get('consent_type')} consent form",
            "success": True,
            "severity": "info"
        })
        
        return {"message": "Consent form signed successfully", "status": "active"}
    
    @consent_router.post("/{consent_id}/revoke")
    async def revoke_consent(
        consent_id: str,
        revoke_data: ConsentRevoke,
        current_user: dict = Depends(get_current_user)
    ):
        """Revoke an active consent"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent form not found")
        
        if consent.get("status") != ConsentStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Only active consents can be revoked")
        
        update_data = {
            "status": ConsentStatus.REVOKED.value,
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "revoked_by": current_user.get("id"),
            "revocation_reason": revoke_data.reason,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.consent_forms.update_one(
            {"id": consent_id},
            {"$set": update_data}
        )
        
        # Log audit event
        patient = await db.patients.find_one({"id": consent["patient_id"]})
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.get("id"),
            "user_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
            "user_role": current_user.get("role"),
            "action": "consent_revoked",
            "resource_type": "consent_form",
            "resource_id": consent_id,
            "patient_id": consent["patient_id"],
            "patient_name": f"{patient['first_name']} {patient['last_name']}" if patient else None,
            "organization_id": consent.get("organization_id"),
            "details": f"Patient revoked {consent.get('consent_type')} consent: {revoke_data.reason}",
            "success": True,
            "severity": "warning"
        })
        
        return {"message": "Consent revoked successfully", "status": "revoked"}
    
    @consent_router.get("/{consent_id}/verify")
    async def verify_consent(
        consent_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Verify if a consent is valid and active"""
        consent = await db.consent_forms.find_one({"id": consent_id}, {"_id": 0})
        if not consent:
            return {"valid": False, "reason": "Consent not found"}
        
        # Check status
        if consent.get("status") != ConsentStatus.ACTIVE.value:
            return {"valid": False, "reason": f"Consent status is {consent.get('status')}"}
        
        # Check expiration
        if consent.get("expiration_date"):
            exp_date = datetime.fromisoformat(consent["expiration_date"].replace("Z", "+00:00"))
            if exp_date < datetime.now(timezone.utc):
                # Update status to expired
                await db.consent_forms.update_one(
                    {"id": consent_id},
                    {"$set": {"status": ConsentStatus.EXPIRED.value}}
                )
                return {"valid": False, "reason": "Consent has expired"}
        
        return {
            "valid": True,
            "consent_type": consent.get("consent_type"),
            "patient_id": consent.get("patient_id"),
            "signed_at": consent.get("patient_signed_at"),
            "expires_at": consent.get("expiration_date")
        }
    
    @consent_router.get("/check/{patient_id}/{consent_type}")
    async def check_patient_consent(
        patient_id: str,
        consent_type: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Check if patient has active consent of a specific type"""
        consent = await db.consent_forms.find_one({
            "patient_id": patient_id,
            "consent_type": consent_type,
            "status": ConsentStatus.ACTIVE.value
        }, {"_id": 0})
        
        if consent:
            # Check expiration
            if consent.get("expiration_date"):
                exp_date = datetime.fromisoformat(consent["expiration_date"].replace("Z", "+00:00"))
                if exp_date < datetime.now(timezone.utc):
                    return {"has_consent": False, "reason": "Consent expired"}
            
            return {
                "has_consent": True,
                "consent_id": consent["id"],
                "signed_at": consent.get("patient_signed_at"),
                "expires_at": consent.get("expiration_date")
            }
        
        return {"has_consent": False, "reason": "No active consent found"}
    
    return consent_router


# Export
__all__ = [
    'consent_router',
    'create_consent_endpoints',
    'ConsentType',
    'ConsentStatus',
    'ConsentCreate',
    'ConsentResponse',
    'CONSENT_TEMPLATES'
]
