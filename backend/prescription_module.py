"""
e-Prescribing Module for Yacco EMR
Handles electronic prescriptions with safety controls
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum

prescription_router = APIRouter(prefix="/api/prescriptions", tags=["e-Prescribing"])


# ============== Enums ==============

class PrescriptionStatus(str, Enum):
    DRAFT = "draft"
    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    DISPENSED = "dispensed"
    PARTIALLY_DISPENSED = "partially_dispensed"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PrescriptionPriority(str, Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"


# ============== Pydantic Models ==============

class MedicationItem(BaseModel):
    medication_name: str
    generic_name: Optional[str] = None
    dosage: str
    dosage_unit: str = "mg"
    frequency: str  # e.g., "BID", "TID", "QID", "PRN"
    route: str = "oral"  # oral, IV, IM, topical, etc.
    duration_value: int = 7
    duration_unit: str = "days"
    quantity: int = 1
    refills: int = 0
    prn_instructions: Optional[str] = None
    special_instructions: Optional[str] = None


class PrescriptionCreate(BaseModel):
    patient_id: str
    medications: List[MedicationItem]
    diagnosis: Optional[str] = None
    clinical_notes: Optional[str] = None
    priority: PrescriptionPriority = PrescriptionPriority.ROUTINE
    pharmacy_id: Optional[str] = None  # If sending to specific pharmacy
    send_to_external: bool = False


class PrescriptionUpdate(BaseModel):
    status: Optional[PrescriptionStatus] = None
    pharmacist_notes: Optional[str] = None
    dispensed_by: Optional[str] = None
    dispensed_at: Optional[str] = None


class DrugInteractionCheck(BaseModel):
    patient_id: str
    new_medication: str
    current_medications: List[str] = []


# ============== Drug Database (Mock - Replace with real API) ==============

DRUG_DATABASE = [
    {"name": "Amoxicillin", "generic": "Amoxicillin", "class": "Antibiotic", "forms": ["capsule", "suspension"], "strengths": ["250mg", "500mg"]},
    {"name": "Metformin", "generic": "Metformin HCl", "class": "Antidiabetic", "forms": ["tablet"], "strengths": ["500mg", "850mg", "1000mg"]},
    {"name": "Lisinopril", "generic": "Lisinopril", "class": "ACE Inhibitor", "forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg"]},
    {"name": "Amlodipine", "generic": "Amlodipine Besylate", "class": "Calcium Channel Blocker", "forms": ["tablet"], "strengths": ["5mg", "10mg"]},
    {"name": "Omeprazole", "generic": "Omeprazole", "class": "Proton Pump Inhibitor", "forms": ["capsule"], "strengths": ["20mg", "40mg"]},
    {"name": "Paracetamol", "generic": "Acetaminophen", "class": "Analgesic", "forms": ["tablet", "syrup"], "strengths": ["500mg", "1000mg"]},
    {"name": "Ibuprofen", "generic": "Ibuprofen", "class": "NSAID", "forms": ["tablet"], "strengths": ["200mg", "400mg", "600mg"]},
    {"name": "Ciprofloxacin", "generic": "Ciprofloxacin", "class": "Antibiotic", "forms": ["tablet"], "strengths": ["250mg", "500mg"]},
    {"name": "Atorvastatin", "generic": "Atorvastatin Calcium", "class": "Statin", "forms": ["tablet"], "strengths": ["10mg", "20mg", "40mg"]},
    {"name": "Metoprolol", "generic": "Metoprolol Tartrate", "class": "Beta Blocker", "forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"name": "Azithromycin", "generic": "Azithromycin", "class": "Antibiotic", "forms": ["tablet", "suspension"], "strengths": ["250mg", "500mg"]},
    {"name": "Prednisone", "generic": "Prednisone", "class": "Corticosteroid", "forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg"]},
    {"name": "Losartan", "generic": "Losartan Potassium", "class": "ARB", "forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"name": "Furosemide", "generic": "Furosemide", "class": "Loop Diuretic", "forms": ["tablet"], "strengths": ["20mg", "40mg", "80mg"]},
    {"name": "Clopidogrel", "generic": "Clopidogrel Bisulfate", "class": "Antiplatelet", "forms": ["tablet"], "strengths": ["75mg"]},
    {"name": "Insulin Glargine", "generic": "Insulin Glargine", "class": "Insulin", "forms": ["injection"], "strengths": ["100 units/mL"]},
    {"name": "Salbutamol", "generic": "Albuterol", "class": "Bronchodilator", "forms": ["inhaler", "nebulizer"], "strengths": ["100mcg/puff"]},
    {"name": "Tramadol", "generic": "Tramadol HCl", "class": "Opioid Analgesic", "forms": ["capsule"], "strengths": ["50mg", "100mg"]},
    {"name": "Diazepam", "generic": "Diazepam", "class": "Benzodiazepine", "forms": ["tablet"], "strengths": ["2mg", "5mg", "10mg"]},
    {"name": "Chloroquine", "generic": "Chloroquine Phosphate", "class": "Antimalarial", "forms": ["tablet"], "strengths": ["250mg"]},
    {"name": "Artemether-Lumefantrine", "generic": "Artemether-Lumefantrine", "class": "Antimalarial", "forms": ["tablet"], "strengths": ["20mg/120mg"]},
]

# Drug interactions (simplified - real system would use comprehensive database)
DRUG_INTERACTIONS = {
    "Warfarin": ["Aspirin", "Ibuprofen", "Naproxen"],
    "Metformin": ["Contrast Dye"],
    "Lisinopril": ["Potassium Supplements", "Spironolactone"],
    "Ciprofloxacin": ["Antacids", "Iron Supplements"],
    "Tramadol": ["SSRIs", "MAOIs"],
}

# Allergy cross-reactions
ALLERGY_CROSS_REACTIONS = {
    "Penicillin": ["Amoxicillin", "Ampicillin", "Cephalosporins"],
    "Sulfa": ["Sulfamethoxazole", "Sulfasalazine"],
    "NSAIDs": ["Ibuprofen", "Naproxen", "Aspirin"],
}


def create_prescription_endpoints(db, get_current_user):
    """Create prescription API endpoints with database injection"""
    
    @prescription_router.get("/drugs/search")
    async def search_drugs(query: str = "", limit: int = 20):
        """Search drug database"""
        if not query:
            return DRUG_DATABASE[:limit]
        
        query_lower = query.lower()
        results = [
            drug for drug in DRUG_DATABASE
            if query_lower in drug["name"].lower() or query_lower in drug["generic"].lower()
        ]
        return results[:limit]
    
    @prescription_router.get("/drugs/database")
    async def get_drug_database():
        """Get full drug database"""
        return {"drugs": DRUG_DATABASE, "total": len(DRUG_DATABASE)}
    
    @prescription_router.post("/check-interactions")
    async def check_drug_interactions(
        data: DrugInteractionCheck,
        user: dict = Depends(get_current_user)
    ):
        """Check for drug-drug interactions and allergy alerts"""
        warnings = []
        
        # Check drug-drug interactions
        new_med_lower = data.new_medication.lower()
        for med in data.current_medications:
            med_lower = med.lower()
            for drug, interactions in DRUG_INTERACTIONS.items():
                if drug.lower() in new_med_lower or drug.lower() in med_lower:
                    for interaction in interactions:
                        if interaction.lower() in new_med_lower or interaction.lower() in med_lower:
                            warnings.append({
                                "type": "drug_interaction",
                                "severity": "high",
                                "message": f"Potential interaction between {data.new_medication} and {med}"
                            })
        
        # Get patient allergies
        patient = await db["patients"].find_one({"id": data.patient_id})
        if patient and patient.get("allergies"):
            for allergy in patient.get("allergies", []):
                allergy_lower = allergy.lower()
                # Check cross-reactions
                for allergen, reactions in ALLERGY_CROSS_REACTIONS.items():
                    if allergen.lower() in allergy_lower:
                        for reaction in reactions:
                            if reaction.lower() in new_med_lower:
                                warnings.append({
                                    "type": "allergy_alert",
                                    "severity": "critical",
                                    "message": f"Patient allergic to {allergy}. {data.new_medication} may cause reaction."
                                })
        
        # Check for duplicates
        for med in data.current_medications:
            if med.lower() == new_med_lower:
                warnings.append({
                    "type": "duplicate_therapy",
                    "severity": "medium",
                    "message": f"Duplicate therapy warning: {data.new_medication} already prescribed"
                })
        
        return {
            "safe": len([w for w in warnings if w["severity"] in ["critical", "high"]]) == 0,
            "warnings": warnings,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    @prescription_router.post("/create")
    async def create_prescription(
        data: PrescriptionCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new electronic prescription"""
        allowed_roles = ["physician", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Only physicians can create prescriptions")
        
        # Verify patient exists
        patient = await db["patients"].find_one({"id": data.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        prescription_id = str(uuid.uuid4())
        rx_number = f"RX-{datetime.now().strftime('%Y%m%d')}-{prescription_id[:8].upper()}"
        
        prescription_doc = {
            "id": prescription_id,
            "rx_number": rx_number,
            "patient_id": data.patient_id,
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            "patient_mrn": patient.get("mrn"),
            "prescriber_id": user.get("id"),
            "prescriber_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "prescriber_license": user.get("license_number", ""),
            "organization_id": user.get("organization_id"),
            "medications": [med.dict() for med in data.medications],
            "diagnosis": data.diagnosis,
            "clinical_notes": data.clinical_notes,
            "priority": data.priority,
            "pharmacy_id": data.pharmacy_id,
            "send_to_external": data.send_to_external,
            "status": PrescriptionStatus.PENDING_VERIFICATION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "dispensed_at": None,
            "dispensed_by": None,
            "pharmacist_notes": None,
            "expiry_date": None  # Typically 1 year for most prescriptions
        }
        
        await db["prescriptions"].insert_one(prescription_doc)
        
        # Create audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "prescription_created",
            "resource_type": "prescription",
            "resource_id": prescription_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"rx_number": rx_number, "patient_id": data.patient_id, "medication_count": len(data.medications)},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": "Prescription created successfully",
            "prescription": prescription_doc
        }
    
    @prescription_router.get("/patient/{patient_id}")
    async def get_patient_prescriptions(
        patient_id: str,
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get prescriptions for a patient"""
        query = {"patient_id": patient_id}
        if status:
            query["status"] = status
        
        prescriptions = await db["prescriptions"].find(query).sort("created_at", -1).to_list(100)
        return {"prescriptions": prescriptions, "total": len(prescriptions)}
    
    @prescription_router.get("/pharmacy/queue")
    async def get_pharmacy_queue(
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get prescription queue for pharmacy"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Pharmacy access required")
        
        query = {"organization_id": user.get("organization_id")}
        if status:
            query["status"] = status
        else:
            # Default: show pending and approved prescriptions
            query["status"] = {"$in": [
                PrescriptionStatus.PENDING_VERIFICATION,
                PrescriptionStatus.APPROVED,
                PrescriptionStatus.PARTIALLY_DISPENSED
            ]}
        
        prescriptions = await db["prescriptions"].find(query).sort("created_at", -1).to_list(200)
        
        # Group by status
        stats = {
            "pending": len([p for p in prescriptions if p["status"] == PrescriptionStatus.PENDING_VERIFICATION]),
            "approved": len([p for p in prescriptions if p["status"] == PrescriptionStatus.APPROVED]),
            "dispensed": len([p for p in prescriptions if p["status"] == PrescriptionStatus.DISPENSED]),
            "ready": len([p for p in prescriptions if p["status"] == PrescriptionStatus.READY_FOR_PICKUP])
        }
        
        return {"prescriptions": prescriptions, "stats": stats, "total": len(prescriptions)}
    
    @prescription_router.put("/{prescription_id}/status")
    async def update_prescription_status(
        prescription_id: str,
        data: PrescriptionUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update prescription status (pharmacy workflow)"""
        prescription = await db["prescriptions"].find_one({"id": prescription_id})
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if data.status:
            update_data["status"] = data.status
            
            if data.status == PrescriptionStatus.DISPENSED:
                update_data["dispensed_at"] = datetime.now(timezone.utc).isoformat()
                update_data["dispensed_by"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        
        if data.pharmacist_notes:
            update_data["pharmacist_notes"] = data.pharmacist_notes
        
        await db["prescriptions"].update_one(
            {"id": prescription_id},
            {"$set": update_data}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": f"prescription_{data.status}" if data.status else "prescription_updated",
            "resource_type": "prescription",
            "resource_id": prescription_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {"new_status": data.status, "rx_number": prescription.get("rx_number")},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Prescription updated", "status": data.status}
    
    @prescription_router.post("/{prescription_id}/renew")
    async def renew_prescription(
        prescription_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Renew an existing prescription"""
        if user.get("role") not in ["physician", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can renew prescriptions")
        
        original = await db["prescriptions"].find_one({"id": prescription_id})
        if not original:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        new_id = str(uuid.uuid4())
        new_rx_number = f"RX-{datetime.now().strftime('%Y%m%d')}-{new_id[:8].upper()}"
        
        renewed_prescription = {
            **original,
            "id": new_id,
            "rx_number": new_rx_number,
            "status": PrescriptionStatus.PENDING_VERIFICATION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "renewed_from": prescription_id,
            "dispensed_at": None,
            "dispensed_by": None,
            "pharmacist_notes": None
        }
        del renewed_prescription["_id"]
        
        await db["prescriptions"].insert_one(renewed_prescription)
        
        return {"message": "Prescription renewed", "new_prescription": renewed_prescription}
    
    @prescription_router.post("/{prescription_id}/discontinue")
    async def discontinue_prescription(
        prescription_id: str,
        reason: str = "Clinical decision",
        user: dict = Depends(get_current_user)
    ):
        """Discontinue a prescription"""
        if user.get("role") not in ["physician", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can discontinue prescriptions")
        
        await db["prescriptions"].update_one(
            {"id": prescription_id},
            {"$set": {
                "status": PrescriptionStatus.CANCELLED,
                "discontinued_at": datetime.now(timezone.utc).isoformat(),
                "discontinued_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "discontinue_reason": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Prescription discontinued"}
    
    return prescription_router
