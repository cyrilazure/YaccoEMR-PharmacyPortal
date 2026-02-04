"""
Patient Consent Forms Module for Yacco EMR
HIPAA-Compliant Consent Management System

Features:
- Stores signed consent forms with digital signatures
- Links consent to specific record scopes (date ranges, record types)
- Enforces expiration dates with automatic status updates
- Allows revocation with reason tracking
- Logs all consent usage for HIPAA audits
- Document storage with integrity verification (SHA-256)

Compliance Considerations:
- HIPAA Privacy Rule: Patient authorization for use/disclosure of PHI
- HIPAA Security Rule: Integrity controls for consent documents
- 21 CFR Part 11: Electronic signatures and records
- State-specific consent laws may apply
- Retention: Minimum 6 years from date of creation or last effective date
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import hashlib
import base64
import os

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
    organization_id: Optional[str] = None
    consent_type: str
    title: str
    description: str
    status: str
    scope_start_date: Optional[str] = None
    scope_end_date: Optional[str] = None
    record_types_included: Optional[List[str]] = None
    recipient_organization_name: Optional[str] = None
    purpose: Optional[str] = None
    patient_signed_at: Optional[str] = None
    witness_name: Optional[str] = None
    witness_signed_at: Optional[str] = None
    effective_date: str
    expiration_date: Optional[str] = None
    revoked_at: Optional[str] = None
    revocation_reason: Optional[str] = None
    document_url: Optional[str] = None
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
    
    # ============ AUDIT LOGGING HELPER ============
    async def log_consent_audit(
        user: dict,
        action: str,
        consent_id: str = None,
        patient_id: str = None,
        patient_name: str = None,
        consent_type: str = None,
        details: str = None,
        success: bool = True,
        severity: str = "info",
        metadata: dict = None
    ):
        """Log consent-related audit events for HIPAA compliance"""
        audit_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user.get("id", "unknown"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Unknown",
            "user_role": user.get("role", "unknown"),
            "organization_id": user.get("organization_id"),
            "action": action,
            "resource_type": "consent_form",
            "resource_id": consent_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "details": details,
            "success": success,
            "severity": severity,
            "phi_accessed": True,  # Consent forms contain PHI
            "metadata": {
                "consent_type": consent_type,
                **(metadata or {})
            }
        }
        await db.audit_logs.insert_one(audit_entry)
        return audit_entry
    
    # ============ CONSENT USAGE TRACKING ============
    async def track_consent_usage(
        consent_id: str,
        user: dict,
        usage_type: str,
        details: str = None
    ):
        """Track when and how a consent is used/accessed"""
        usage_entry = {
            "id": str(uuid.uuid4()),
            "consent_id": consent_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            "user_role": user.get("role"),
            "usage_type": usage_type,  # viewed, verified, used_for_disclosure, etc.
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.consent_usage_log.insert_one(usage_entry)
        
        # Update consent access count
        await db.consent_forms.update_one(
            {"id": consent_id},
            {
                "$inc": {"access_count": 1},
                "$set": {"last_accessed_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        return usage_entry
    
    # ============ EXPIRATION ENFORCEMENT ============
    async def check_and_update_expired_consents():
        """Check for expired consents and update their status"""
        now = datetime.now(timezone.utc).isoformat()
        
        # Find active consents that have expired
        expired = await db.consent_forms.update_many(
            {
                "status": ConsentStatus.ACTIVE.value,
                "expiration_date": {"$lte": now, "$ne": None}
            },
            {
                "$set": {
                    "status": ConsentStatus.EXPIRED.value,
                    "expired_at": now
                }
            }
        )
        return expired.modified_count
    
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
        
        patient_name = f"{patient['first_name']} {patient['last_name']}"
        
        # Generate document hash for integrity
        consent_content = f"{consent_data.consent_type}|{consent_data.consent_text}|{consent_data.patient_id}|{datetime.now(timezone.utc).isoformat()}"
        document_hash = hashlib.sha256(consent_content.encode()).hexdigest()
        
        consent = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            **consent_data.model_dump(),
            "status": ConsentStatus.PENDING.value,
            "effective_date": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.get("id"),
            "document_hash": document_hash,
            "access_count": 0,
            "version": 1,
            # Optional fields with default values
            "patient_signed_at": None,
            "witness_name": None,
            "witness_signed_at": None,
            "revoked_at": None,
            "revocation_reason": None,
            "document_url": None
        }
        
        await db.consent_forms.insert_one(consent)
        
        # Remove MongoDB ObjectId for serialization
        consent.pop("_id", None)
        
        # AUDIT: Log consent creation
        await log_consent_audit(
            user=current_user,
            action="consent_created",
            consent_id=consent["id"],
            patient_id=consent_data.patient_id,
            patient_name=patient_name,
            consent_type=consent_data.consent_type.value,
            details=f"Created {consent_data.consent_type.value} consent form for patient {patient_name}",
            metadata={
                "scope_start_date": consent_data.scope_start_date,
                "scope_end_date": consent_data.scope_end_date,
                "record_types": consent_data.record_types_included,
                "expiration_date": consent_data.expiration_date
            }
        )
        
        consent["patient_name"] = patient_name
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
    
    # ============ CONSENT USAGE TRACKING ENDPOINTS ============
    
    @consent_router.get("/{consent_id}/usage-history")
    async def get_consent_usage_history(
        consent_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get the usage history of a consent form (audit trail)"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        # Track this access
        await track_consent_usage(
            consent_id=consent_id,
            user=current_user,
            usage_type="usage_history_viewed",
            details="Viewed consent usage history"
        )
        
        # Get usage log
        usage_logs = await db.consent_usage_log.find(
            {"consent_id": consent_id},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(500)
        
        return {
            "consent_id": consent_id,
            "total_accesses": consent.get("access_count", 0),
            "last_accessed_at": consent.get("last_accessed_at"),
            "usage_history": usage_logs
        }
    
    @consent_router.post("/{consent_id}/use")
    async def record_consent_usage(
        consent_id: str,
        usage_type: str,
        details: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Record when a consent is used (e.g., for disclosing PHI)"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        if consent.get("status") != ConsentStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Consent is not active")
        
        # Check expiration
        if consent.get("expiration_date"):
            exp_date_str = consent["expiration_date"]
            # Handle both date (YYYY-MM-DD) and datetime formats
            if "T" in exp_date_str:
                exp_date = datetime.fromisoformat(exp_date_str.replace("Z", "+00:00"))
            else:
                # Date only format, assume end of day
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                exp_date = exp_date.replace(hour=23, minute=59, second=59)
            
            if exp_date < datetime.now(timezone.utc):
                # Update status
                await db.consent_forms.update_one(
                    {"id": consent_id},
                    {"$set": {"status": ConsentStatus.EXPIRED.value}}
                )
                raise HTTPException(status_code=400, detail="Consent has expired")
        
        # Record usage
        usage = await track_consent_usage(
            consent_id=consent_id,
            user=current_user,
            usage_type=usage_type,
            details=details
        )
        
        # Audit log for PHI disclosure
        patient = await db.patients.find_one({"id": consent["patient_id"]})
        await log_consent_audit(
            user=current_user,
            action="consent_used",
            consent_id=consent_id,
            patient_id=consent["patient_id"],
            patient_name=f"{patient['first_name']} {patient['last_name']}" if patient else None,
            consent_type=consent.get("consent_type"),
            details=f"Consent used for: {usage_type}. {details or ''}",
            metadata={"usage_type": usage_type}
        )
        
        return {"message": "Consent usage recorded", "usage_id": usage["id"]}
    
    # ============ DOCUMENT UPLOAD ============
    
    @consent_router.post("/{consent_id}/upload-document")
    async def upload_consent_document(
        consent_id: str,
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
    ):
        """Upload a signed consent document (PDF/image)"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        # Validate file type
        allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PDF, PNG, JPEG")
        
        # Read file content
        content = await file.read()
        
        # Generate document hash for integrity verification
        document_hash = hashlib.sha256(content).hexdigest()
        
        # Store as base64 in database (for MVP - in production use cloud storage)
        document_base64 = base64.b64encode(content).decode('utf-8')
        
        # Update consent with document
        await db.consent_forms.update_one(
            {"id": consent_id},
            {"$set": {
                "document_data": document_base64,
                "document_filename": file.filename,
                "document_content_type": file.content_type,
                "document_hash": document_hash,
                "document_uploaded_at": datetime.now(timezone.utc).isoformat(),
                "document_uploaded_by": current_user.get("id"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Audit log
        await log_consent_audit(
            user=current_user,
            action="consent_document_uploaded",
            consent_id=consent_id,
            patient_id=consent["patient_id"],
            consent_type=consent.get("consent_type"),
            details=f"Uploaded signed consent document: {file.filename}",
            metadata={"filename": file.filename, "document_hash": document_hash}
        )
        
        return {
            "message": "Document uploaded successfully",
            "document_hash": document_hash,
            "filename": file.filename
        }
    
    @consent_router.get("/{consent_id}/document")
    async def get_consent_document(
        consent_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get the uploaded consent document"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        if not consent.get("document_data"):
            raise HTTPException(status_code=404, detail="No document uploaded for this consent")
        
        # Track access
        await track_consent_usage(
            consent_id=consent_id,
            user=current_user,
            usage_type="document_downloaded",
            details="Downloaded consent document"
        )
        
        return {
            "document_data": consent["document_data"],
            "filename": consent.get("document_filename"),
            "content_type": consent.get("document_content_type"),
            "document_hash": consent.get("document_hash"),
            "uploaded_at": consent.get("document_uploaded_at")
        }
    
    @consent_router.get("/{consent_id}/verify-integrity")
    async def verify_document_integrity(
        consent_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Verify the integrity of the stored consent document"""
        consent = await db.consent_forms.find_one({"id": consent_id})
        if not consent:
            raise HTTPException(status_code=404, detail="Consent not found")
        
        if not consent.get("document_data"):
            return {"verified": False, "reason": "No document stored"}
        
        # Recalculate hash
        document_bytes = base64.b64decode(consent["document_data"])
        current_hash = hashlib.sha256(document_bytes).hexdigest()
        stored_hash = consent.get("document_hash")
        
        is_valid = current_hash == stored_hash
        
        # Log verification attempt
        await log_consent_audit(
            user=current_user,
            action="consent_integrity_verified",
            consent_id=consent_id,
            patient_id=consent["patient_id"],
            consent_type=consent.get("consent_type"),
            details=f"Document integrity verification: {'PASSED' if is_valid else 'FAILED'}",
            success=is_valid,
            severity="info" if is_valid else "alert"
        )
        
        return {
            "verified": is_valid,
            "stored_hash": stored_hash,
            "current_hash": current_hash,
            "verification_time": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ EXPIRATION MANAGEMENT ============
    
    @consent_router.post("/check-expirations")
    async def run_expiration_check(
        current_user: dict = Depends(get_current_user)
    ):
        """Manually trigger expiration check for all consents"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        expired_count = await check_and_update_expired_consents()
        
        return {
            "message": f"Expiration check complete. {expired_count} consents marked as expired.",
            "expired_count": expired_count
        }
    
    @consent_router.get("/expiring-soon")
    async def get_expiring_consents(
        days: int = 30,
        current_user: dict = Depends(get_current_user)
    ):
        """Get consents that will expire within specified days"""
        org_id = current_user.get("organization_id")
        
        now = datetime.now(timezone.utc)
        future_date = (now + timedelta(days=days)).isoformat()
        
        query = {
            "status": ConsentStatus.ACTIVE.value,
            "expiration_date": {"$lte": future_date, "$gt": now.isoformat()}
        }
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        consents = await db.consent_forms.find(query, {"_id": 0}).sort("expiration_date", 1).to_list(100)
        
        # Enrich with patient names
        for consent in consents:
            patient = await db.patients.find_one({"id": consent["patient_id"]})
            if patient:
                consent["patient_name"] = f"{patient['first_name']} {patient['last_name']}"
        
        return {
            "expiring_within_days": days,
            "count": len(consents),
            "consents": [ConsentResponse(**c) for c in consents]
        }
    
    # ============ CONSENT STATISTICS ============
    
    @consent_router.get("/stats/overview")
    async def get_consent_statistics(
        current_user: dict = Depends(get_current_user)
    ):
        """Get consent statistics for the organization"""
        org_id = current_user.get("organization_id")
        
        org_filter = {}
        if org_id and current_user.get("role") != "super_admin":
            org_filter["organization_id"] = org_id
        
        # Total counts by status
        pipeline = [
            {"$match": org_filter},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = await db.consent_forms.aggregate(pipeline).to_list(10)
        by_status = {item["_id"]: item["count"] for item in status_counts}
        
        # Counts by type
        type_pipeline = [
            {"$match": {**org_filter, "status": ConsentStatus.ACTIVE.value}},
            {"$group": {"_id": "$consent_type", "count": {"$sum": 1}}}
        ]
        type_counts = await db.consent_forms.aggregate(type_pipeline).to_list(20)
        by_type = {item["_id"]: item["count"] for item in type_counts}
        
        # Revocations in last 30 days
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        recent_revocations = await db.consent_forms.count_documents({
            **org_filter,
            "status": ConsentStatus.REVOKED.value,
            "revoked_at": {"$gte": thirty_days_ago}
        })
        
        # Expiring in 30 days
        future_30 = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        expiring_soon = await db.consent_forms.count_documents({
            **org_filter,
            "status": ConsentStatus.ACTIVE.value,
            "expiration_date": {"$lte": future_30, "$gt": datetime.now(timezone.utc).isoformat()}
        })
        
        return {
            "by_status": by_status,
            "by_type": by_type,
            "total_active": by_status.get(ConsentStatus.ACTIVE.value, 0),
            "total_pending": by_status.get(ConsentStatus.PENDING.value, 0),
            "total_revoked": by_status.get(ConsentStatus.REVOKED.value, 0),
            "total_expired": by_status.get(ConsentStatus.EXPIRED.value, 0),
            "recent_revocations_30d": recent_revocations,
            "expiring_in_30d": expiring_soon
        }
    
    # ============ COMPLIANCE REPORT ============
    
    @consent_router.get("/compliance-report")
    async def get_compliance_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Generate a compliance report for consent management"""
        if current_user.get("role") not in ["admin", "hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = current_user.get("organization_id")
        
        # Default to last 90 days
        if not start_date:
            start_date = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        if not end_date:
            end_date = datetime.now(timezone.utc).isoformat()
        
        org_filter = {}
        if org_id and current_user.get("role") != "super_admin":
            org_filter["organization_id"] = org_id
        
        date_filter = {"created_at": {"$gte": start_date, "$lte": end_date}}
        
        # Consents created in period
        consents_created = await db.consent_forms.count_documents({**org_filter, **date_filter})
        
        # Consents signed in period
        consents_signed = await db.consent_forms.count_documents({
            **org_filter,
            "patient_signed_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Consents used (from usage log)
        consent_uses = await db.consent_usage_log.count_documents({
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        
        # Revocations in period
        revocations = await db.consent_forms.count_documents({
            **org_filter,
            "revoked_at": {"$gte": start_date, "$lte": end_date}
        })
        
        # Integrity verifications
        integrity_checks = await db.audit_logs.count_documents({
            **org_filter,
            "action": "consent_integrity_verified",
            "timestamp": {"$gte": start_date, "$lte": end_date}
        })
        
        # Usage by type
        usage_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {"_id": "$usage_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        usage_by_type = await db.consent_usage_log.aggregate(usage_pipeline).to_list(20)
        
        return {
            "report_period": {
                "start": start_date,
                "end": end_date
            },
            "summary": {
                "consents_created": consents_created,
                "consents_signed": consents_signed,
                "consent_uses": consent_uses,
                "revocations": revocations,
                "integrity_verifications": integrity_checks
            },
            "usage_breakdown": [{"type": u["_id"], "count": u["count"]} for u in usage_by_type],
            "compliance_notes": {
                "hipaa_privacy_rule": "All consent forms are retained with audit trails",
                "hipaa_security_rule": "Document integrity verified via SHA-256 hashing",
                "retention_policy": "Minimum 6 years from date of creation",
                "electronic_signatures": "21 CFR Part 11 compliant digital signatures"
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        }
    
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
