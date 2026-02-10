"""
Patient Referral System Module for Yacco Health EMR
====================================================
Enables physicians to refer patients to other hospitals and transfer health records.

Features:
- Create patient referrals with clinical summary
- Search and select destination hospitals
- Include/exclude specific health records
- Track referral status (pending, sent, received, accepted, completed)
- Notify receiving hospital via SMS/email
- View referral history for patients
"""

import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from enum import Enum
import logging

# Import security
from security import get_current_user, TokenPayload, require_roles, audit_log

logger = logging.getLogger(__name__)


# ============== Enums ==============

class ReferralType(str, Enum):
    STANDARD = "standard"
    EMERGENCY = "emergency"
    SPECIALIST = "specialist"
    SECOND_OPINION = "second_opinion"
    TRANSFER = "transfer"


class ReferralPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENT = "emergent"
    STAT = "stat"


class ReferralStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============== Pydantic Models ==============

class ReferralCreate(BaseModel):
    """Create a new patient referral"""
    patient_id: str
    
    # Destination
    destination_organization_id: Optional[str] = None
    destination_hospital_name: str
    destination_hospital_address: Optional[str] = None
    destination_department: Optional[str] = None
    receiving_physician_id: Optional[str] = None
    receiving_physician_name: Optional[str] = None
    
    # Referral details
    referral_type: ReferralType = ReferralType.STANDARD
    priority: ReferralPriority = ReferralPriority.ROUTINE
    reason: str
    clinical_summary: str
    diagnosis: Optional[str] = None
    icd_codes: Optional[List[str]] = None
    
    # Records to include
    include_medical_history: bool = True
    include_lab_results: bool = True
    include_imaging: bool = True
    include_prescriptions: bool = True
    
    # Notes
    referral_notes: Optional[str] = None


class ReferralUpdate(BaseModel):
    """Update referral status"""
    status: Optional[ReferralStatus] = None
    receiving_notes: Optional[str] = None
    receiving_physician_id: Optional[str] = None
    receiving_physician_name: Optional[str] = None


class ReferralResponse(BaseModel):
    """Referral response model"""
    id: str
    referral_number: str
    patient_id: str
    patient_name: str
    patient_mrn: Optional[str] = None
    
    source_hospital_name: str
    referring_physician_name: str
    
    destination_hospital_name: str
    destination_department: Optional[str] = None
    receiving_physician_name: Optional[str] = None
    
    referral_type: str
    priority: str
    reason: str
    clinical_summary: str
    diagnosis: Optional[str] = None
    
    status: str
    created_at: str
    sent_at: Optional[str] = None
    received_at: Optional[str] = None
    accepted_at: Optional[str] = None
    completed_at: Optional[str] = None


class HospitalSearchResult(BaseModel):
    """Hospital search result for referral destination"""
    id: str
    name: str
    organization_type: str
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    phone: Optional[str] = None
    departments: Optional[List[str]] = None


# ============== Module Factory ==============

def create_referral_router(db) -> APIRouter:
    """Create the referral router with database dependency"""
    
    router = APIRouter(prefix="/api/referrals", tags=["Patient Referrals"])
    
    # Try to use PostgreSQL if available
    USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'
    
    # ============== Helper Functions ==============
    
    def generate_referral_number() -> str:
        """Generate a unique referral number"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:6].upper()
        return f"REF-{timestamp}-{unique_id}"
    
    async def get_patient_details(patient_id: str) -> dict:
        """Get patient details for referral"""
        patient = await db["patients"].find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    
    async def get_organization_details(org_id: str) -> dict:
        """Get organization details"""
        org = await db["organizations"].find_one({"id": org_id}, {"_id": 0})
        return org or {}
    
    async def get_patient_records(patient_id: str, include_flags: dict) -> dict:
        """Gather patient records for transfer"""
        records = {}
        
        if include_flags.get("include_medical_history", True):
            history = await db["patient_medical_history"].find(
                {"patient_id": patient_id}, {"_id": 0}
            ).to_list(100)
            records["medical_history"] = history
        
        if include_flags.get("include_lab_results", True):
            labs = await db["lab_results"].find(
                {"patient_id": patient_id}, {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            records["lab_results"] = labs
        
        if include_flags.get("include_imaging", True):
            imaging = await db["radiology_orders"].find(
                {"patient_id": patient_id}, {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            records["imaging"] = imaging
        
        if include_flags.get("include_prescriptions", True):
            prescriptions = await db["prescriptions"].find(
                {"patient_id": patient_id}, {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            records["prescriptions"] = prescriptions
        
        # Get allergies
        allergies = await db["allergies"].find(
            {"patient_id": patient_id}, {"_id": 0}
        ).to_list(50)
        records["allergies"] = allergies
        
        # Get vitals (recent)
        vitals = await db["vitals"].find(
            {"patient_id": patient_id}, {"_id": 0}
        ).sort("recorded_at", -1).to_list(10)
        records["recent_vitals"] = vitals
        
        return records
    
    async def send_referral_notification(referral: dict):
        """Send notification to destination hospital"""
        try:
            from sms_notification_module import SMSNotifier
            sms_notifier = SMSNotifier(db)
            
            # Get destination hospital contact
            if referral.get("destination_organization_id"):
                dest_org = await get_organization_details(referral["destination_organization_id"])
                phone = dest_org.get("phone")
                
                if phone:
                    message = (
                        f"New Patient Referral: {referral['patient_name']} "
                        f"from {referral['source_hospital_name']}. "
                        f"Priority: {referral['priority'].upper()}. "
                        f"Reason: {referral['reason'][:100]}... "
                        f"Ref#: {referral['referral_number']}"
                    )
                    await sms_notifier.send_sms(phone, message, "patient_referral")
        except Exception as e:
            logger.error(f"Failed to send referral notification: {e}")
    
    # ============== Endpoints ==============
    
    @router.post("/", response_model=dict)
    @audit_log("REFERRAL", "CREATE", "patient_referral")
    async def create_referral(
        referral_data: ReferralCreate,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        Create a new patient referral.
        Only physicians and authorized staff can create referrals.
        """
        # Verify user has permission
        allowed_roles = ['physician', 'nurse', 'nursing_supervisor', 'hospital_admin', 'super_admin']
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Only physicians and authorized staff can create referrals"
            )
        
        # Get patient details
        patient = await get_patient_details(referral_data.patient_id)
        
        # Get source organization details
        source_org = await get_organization_details(current_user.organization_id)
        
        # Get referring physician details
        referring_user = await db["users"].find_one(
            {"id": current_user.user_id}, {"_id": 0}
        )
        
        # Generate referral number
        referral_number = generate_referral_number()
        now = datetime.now(timezone.utc)
        
        # Create referral document
        referral = {
            "id": str(uuid.uuid4()),
            "referral_number": referral_number,
            
            # Patient Info
            "patient_id": patient["id"],
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip(),
            "patient_mrn": patient.get("mrn"),
            "patient_dob": patient.get("date_of_birth"),
            "patient_phone": patient.get("phone"),
            
            # Source Hospital
            "source_organization_id": current_user.organization_id,
            "source_hospital_name": source_org.get("name", "Unknown Hospital"),
            "referring_physician_id": current_user.user_id,
            "referring_physician_name": f"{referring_user.get('first_name', '')} {referring_user.get('last_name', '')}".strip() if referring_user else "Unknown",
            
            # Destination Hospital
            "destination_organization_id": referral_data.destination_organization_id,
            "destination_hospital_name": referral_data.destination_hospital_name,
            "destination_hospital_address": referral_data.destination_hospital_address,
            "destination_department": referral_data.destination_department,
            "receiving_physician_id": referral_data.receiving_physician_id,
            "receiving_physician_name": referral_data.receiving_physician_name,
            
            # Referral Details
            "referral_type": referral_data.referral_type.value,
            "priority": referral_data.priority.value,
            "reason": referral_data.reason,
            "clinical_summary": referral_data.clinical_summary,
            "diagnosis": referral_data.diagnosis,
            "icd_codes": referral_data.icd_codes,
            
            # Records to include
            "include_medical_history": referral_data.include_medical_history,
            "include_lab_results": referral_data.include_lab_results,
            "include_imaging": referral_data.include_imaging,
            "include_prescriptions": referral_data.include_prescriptions,
            
            # Gather and attach records
            "attached_records": await get_patient_records(patient["id"], {
                "include_medical_history": referral_data.include_medical_history,
                "include_lab_results": referral_data.include_lab_results,
                "include_imaging": referral_data.include_imaging,
                "include_prescriptions": referral_data.include_prescriptions,
            }),
            
            # Status
            "status": ReferralStatus.PENDING.value,
            
            # Timestamps
            "created_at": now.isoformat(),
            "sent_at": now.isoformat(),  # Auto-send on creation
            
            # Notes
            "referral_notes": referral_data.referral_notes,
        }
        
        # Save to database
        await db["patient_referrals"].insert_one(referral)
        referral.pop("_id", None)
        
        # Send notification to destination hospital
        await send_referral_notification(referral)
        
        logger.info(f"Referral created: {referral_number} for patient {patient['id']}")
        
        return {
            "success": True,
            "message": "Referral created and sent successfully",
            "referral": {
                "id": referral["id"],
                "referral_number": referral["referral_number"],
                "patient_name": referral["patient_name"],
                "destination_hospital": referral["destination_hospital_name"],
                "status": referral["status"],
                "created_at": referral["created_at"]
            }
        }
    
    @router.get("/", response_model=dict)
    async def list_referrals(
        status: Optional[str] = None,
        direction: str = Query("outgoing", enum=["outgoing", "incoming", "all"]),
        patient_id: Optional[str] = None,
        limit: int = Query(50, le=200),
        skip: int = 0,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        List referrals for the current organization.
        - outgoing: Referrals sent from this hospital
        - incoming: Referrals received by this hospital
        - all: Both outgoing and incoming
        """
        query = {}
        
        # Filter by direction
        if direction == "outgoing":
            query["source_organization_id"] = current_user.organization_id
        elif direction == "incoming":
            query["destination_organization_id"] = current_user.organization_id
        else:
            query["$or"] = [
                {"source_organization_id": current_user.organization_id},
                {"destination_organization_id": current_user.organization_id}
            ]
        
        # Filter by status
        if status:
            query["status"] = status
        
        # Filter by patient
        if patient_id:
            query["patient_id"] = patient_id
        
        # Get referrals
        referrals = await db["patient_referrals"].find(
            query, {"_id": 0, "attached_records": 0}  # Exclude large records field
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await db["patient_referrals"].count_documents(query)
        
        # Get counts by status
        pending_count = await db["patient_referrals"].count_documents({
            **query, "status": "pending"
        })
        received_count = await db["patient_referrals"].count_documents({
            **query, "status": "received"
        })
        
        return {
            "referrals": referrals,
            "total": total,
            "pending_count": pending_count,
            "received_count": received_count,
            "limit": limit,
            "skip": skip
        }
    
    @router.get("/{referral_id}", response_model=dict)
    async def get_referral(
        referral_id: str,
        include_records: bool = False,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get a specific referral by ID"""
        projection = {"_id": 0}
        if not include_records:
            projection["attached_records"] = 0
        
        referral = await db["patient_referrals"].find_one(
            {"id": referral_id},
            projection
        )
        
        if not referral:
            raise HTTPException(status_code=404, detail="Referral not found")
        
        # Verify access
        if (referral.get("source_organization_id") != current_user.organization_id and
            referral.get("destination_organization_id") != current_user.organization_id and
            current_user.role not in ['super_admin', 'platform_owner']):
            raise HTTPException(status_code=403, detail="Access denied to this referral")
        
        return {"referral": referral}
    
    @router.put("/{referral_id}/status", response_model=dict)
    @audit_log("REFERRAL", "UPDATE_STATUS", "patient_referral")
    async def update_referral_status(
        referral_id: str,
        update_data: ReferralUpdate,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        Update referral status.
        - Receiving hospital can mark as: received, accepted, declined, completed
        - Source hospital can mark as: cancelled
        """
        referral = await db["patient_referrals"].find_one({"id": referral_id}, {"_id": 0})
        
        if not referral:
            raise HTTPException(status_code=404, detail="Referral not found")
        
        now = datetime.now(timezone.utc)
        updates = {"updated_at": now.isoformat()}
        
        # Determine who is updating
        is_source = referral.get("source_organization_id") == current_user.organization_id
        is_destination = referral.get("destination_organization_id") == current_user.organization_id
        
        if update_data.status:
            new_status = update_data.status.value
            current_status = referral.get("status")
            
            # Validate status transitions
            if is_source:
                if new_status == "cancelled" and current_status in ["pending", "sent"]:
                    updates["status"] = new_status
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Source hospital can only cancel pending/sent referrals"
                    )
            elif is_destination:
                valid_transitions = {
                    "sent": ["received"],
                    "pending": ["received"],
                    "received": ["accepted", "declined"],
                    "accepted": ["completed"]
                }
                if new_status in valid_transitions.get(current_status, []):
                    updates["status"] = new_status
                    
                    # Set timestamp based on status
                    if new_status == "received":
                        updates["received_at"] = now.isoformat()
                    elif new_status == "accepted":
                        updates["accepted_at"] = now.isoformat()
                        updates["receiving_physician_id"] = current_user.user_id
                    elif new_status == "completed":
                        updates["completed_at"] = now.isoformat()
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status transition from {current_status} to {new_status}"
                    )
            else:
                raise HTTPException(status_code=403, detail="Not authorized to update this referral")
        
        # Update notes
        if update_data.receiving_notes:
            updates["receiving_notes"] = update_data.receiving_notes
        
        if update_data.receiving_physician_name:
            updates["receiving_physician_name"] = update_data.receiving_physician_name
        
        # Perform update
        await db["patient_referrals"].update_one(
            {"id": referral_id},
            {"$set": updates}
        )
        
        return {
            "success": True,
            "message": f"Referral status updated to {updates.get('status', 'unchanged')}",
            "referral_id": referral_id
        }
    
    @router.get("/patient/{patient_id}/history", response_model=dict)
    async def get_patient_referral_history(
        patient_id: str,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get all referrals for a specific patient"""
        referrals = await db["patient_referrals"].find(
            {"patient_id": patient_id},
            {"_id": 0, "attached_records": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "patient_id": patient_id,
            "referrals": referrals,
            "total": len(referrals)
        }
    
    @router.get("/search/hospitals", response_model=dict)
    async def search_hospitals_for_referral(
        query: str = Query(..., min_length=2),
        region: Optional[str] = None,
        limit: int = 20,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        Search for hospitals to refer patients to.
        Excludes the current user's organization.
        """
        search_query = {
            "status": "active",
            "id": {"$ne": current_user.organization_id},
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"city": {"$regex": query, "$options": "i"}}
            ]
        }
        
        if region:
            search_query["state"] = {"$regex": region, "$options": "i"}
        
        hospitals = await db["organizations"].find(
            search_query,
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "organization_type": 1,
                "address_line1": 1,
                "city": 1,
                "state": 1,
                "phone": 1
            }
        ).limit(limit).to_list(limit)
        
        # Get departments for each hospital
        for hospital in hospitals:
            departments = await db["departments"].find(
                {"organization_id": hospital["id"], "is_active": True},
                {"_id": 0, "name": 1}
            ).to_list(50)
            hospital["departments"] = [d["name"] for d in departments]
            hospital["address"] = hospital.pop("address_line1", None)
            hospital["region"] = hospital.pop("state", None)
        
        return {
            "hospitals": hospitals,
            "total": len(hospitals)
        }
    
    @router.get("/stats/summary", response_model=dict)
    async def get_referral_stats(
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get referral statistics for the current organization"""
        org_id = current_user.organization_id
        
        # Outgoing stats
        outgoing_total = await db["patient_referrals"].count_documents({
            "source_organization_id": org_id
        })
        outgoing_pending = await db["patient_referrals"].count_documents({
            "source_organization_id": org_id,
            "status": {"$in": ["pending", "sent"]}
        })
        outgoing_completed = await db["patient_referrals"].count_documents({
            "source_organization_id": org_id,
            "status": "completed"
        })
        
        # Incoming stats
        incoming_total = await db["patient_referrals"].count_documents({
            "destination_organization_id": org_id
        })
        incoming_pending = await db["patient_referrals"].count_documents({
            "destination_organization_id": org_id,
            "status": {"$in": ["sent", "received"]}
        })
        incoming_accepted = await db["patient_referrals"].count_documents({
            "destination_organization_id": org_id,
            "status": {"$in": ["accepted", "completed"]}
        })
        
        return {
            "outgoing": {
                "total": outgoing_total,
                "pending": outgoing_pending,
                "completed": outgoing_completed
            },
            "incoming": {
                "total": incoming_total,
                "pending": incoming_pending,
                "accepted": incoming_accepted
            }
        }
    
    return router


# Create default router for import
referral_router = APIRouter(prefix="/api/referrals", tags=["Patient Referrals"])
