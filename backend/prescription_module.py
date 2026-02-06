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


# ============== Ghana Pharmacies Database ==============
GHANA_PHARMACIES = [
    # Accra Region
    {"id": "pharm-001", "name": "Ernest Chemist - Accra Mall", "location": "Accra Mall, Tetteh Quarshie", "region": "Greater Accra", "phone": "0302123456"},
    {"id": "pharm-002", "name": "Ernest Chemist - Osu Oxford Street", "location": "Oxford Street, Osu", "region": "Greater Accra", "phone": "0302234567"},
    {"id": "pharm-003", "name": "mPharma - Airport", "location": "Airport Residential Area", "region": "Greater Accra", "phone": "0302345678"},
    {"id": "pharm-004", "name": "Kinapharma - Spintex", "location": "Spintex Road", "region": "Greater Accra", "phone": "0302456789"},
    {"id": "pharm-005", "name": "Entrance Pharmacy - Ridge", "location": "Ridge Hospital Area", "region": "Greater Accra", "phone": "0302567890"},
    {"id": "pharm-006", "name": "Starcare Pharmacy - Tema", "location": "Community 1, Tema", "region": "Greater Accra", "phone": "0303678901"},
    {"id": "pharm-007", "name": "Tobinco Pharmacy - Madina", "location": "Madina Market", "region": "Greater Accra", "phone": "0302789012"},
    {"id": "pharm-008", "name": "Letap Pharmaceuticals - Kaneshie", "location": "Kaneshie Market Road", "region": "Greater Accra", "phone": "0302890123"},
    {"id": "pharm-009", "name": "Care Pharmacy - East Legon", "location": "East Legon", "region": "Greater Accra", "phone": "0302901234"},
    {"id": "pharm-010", "name": "Pharmacy Council Pharmacy - Adabraka", "location": "Adabraka", "region": "Greater Accra", "phone": "0302012345"},
    
    # Kumasi - Ashanti Region
    {"id": "pharm-011", "name": "Ernest Chemist - Adum", "location": "Adum, Kumasi", "region": "Ashanti", "phone": "0322123456"},
    {"id": "pharm-012", "name": "mPharma - KNUST", "location": "KNUST Campus", "region": "Ashanti", "phone": "0322234567"},
    {"id": "pharm-013", "name": "Kinapharma - Bantama", "location": "Bantama High Street", "region": "Ashanti", "phone": "0322345678"},
    {"id": "pharm-014", "name": "Tobinco Pharmacy - Asafo", "location": "Asafo Market", "region": "Ashanti", "phone": "0322456789"},
    
    # Takoradi - Western Region
    {"id": "pharm-015", "name": "Ernest Chemist - Takoradi Market Circle", "location": "Market Circle", "region": "Western", "phone": "0312123456"},
    {"id": "pharm-016", "name": "Harbour Pharmacy - Takoradi", "location": "Harbour Area", "region": "Western", "phone": "0312234567"},
    
    # Tamale - Northern Region
    {"id": "pharm-017", "name": "Tamale Central Pharmacy", "location": "Tamale Central Hospital", "region": "Northern", "phone": "0372123456"},
    {"id": "pharm-018", "name": "Northern Star Pharmacy", "location": "Tamale Main Market", "region": "Northern", "phone": "0372234567"},
    
    # Cape Coast - Central Region
    {"id": "pharm-019", "name": "Cape Coast Teaching Hospital Pharmacy", "location": "Cape Coast Teaching Hospital", "region": "Central", "phone": "0332123456"},
    {"id": "pharm-020", "name": "Coastline Pharmacy", "location": "Cape Coast Commercial Area", "region": "Central", "phone": "0332234567"},
    
    # Other Major Pharmacies (National Chains)
    {"id": "pharm-021", "name": "Ernest Chemist - Head Office", "location": "Ring Road, Accra", "region": "Greater Accra", "phone": "0302999000"},
    {"id": "pharm-022", "name": "mPharma - Dzorwulu", "location": "Dzorwulu, Accra", "region": "Greater Accra", "phone": "0302999111"},
    {"id": "pharm-023", "name": "Kinapharma - Achimota", "location": "Achimota Mall", "region": "Greater Accra", "phone": "0302999222"},
    {"id": "pharm-024", "name": "Letap Pharmaceuticals - Spintex", "location": "Spintex Road", "region": "Greater Accra", "phone": "0302999333"},
    {"id": "pharm-025", "name": "Entrance Pharmacy - 37 Military Hospital", "location": "37 Military Hospital", "region": "Greater Accra", "phone": "0302999444"},
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
    
    @prescription_router.get("/pharmacies/ghana")
    async def get_ghana_pharmacies(region: Optional[str] = None):
        """Get list of pharmacies in Ghana"""
        if region:
            pharmacies = [p for p in GHANA_PHARMACIES if p["region"] == region]
        else:
            pharmacies = GHANA_PHARMACIES
        
        return {"pharmacies": pharmacies, "total": len(pharmacies)}
    
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
            "priority": data.priority.value if hasattr(data.priority, 'value') else data.priority,
            "pharmacy_id": data.pharmacy_id,
            "send_to_external": data.send_to_external,
            "status": PrescriptionStatus.PENDING_VERIFICATION.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "dispensed_at": None,
            "dispensed_by": None,
            "pharmacist_notes": None,
            "expiry_date": None  # Typically 1 year for most prescriptions
        }
        
        await db["prescriptions"].insert_one(prescription_doc)
        
        # Remove _id if it was added by MongoDB
        if "_id" in prescription_doc:
            del prescription_doc["_id"]
        
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
        
        prescriptions = await db["prescriptions"].find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
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
                PrescriptionStatus.PENDING_VERIFICATION.value,
                PrescriptionStatus.APPROVED.value,
                PrescriptionStatus.PARTIALLY_DISPENSED.value
            ]}
        
        prescriptions = await db["prescriptions"].find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
        
        # Group by status
        stats = {
            "pending": len([p for p in prescriptions if p["status"] == PrescriptionStatus.PENDING_VERIFICATION.value]),
            "approved": len([p for p in prescriptions if p["status"] == PrescriptionStatus.APPROVED.value]),
            "dispensed": len([p for p in prescriptions if p["status"] == PrescriptionStatus.DISPENSED.value]),
            "ready": len([p for p in prescriptions if p["status"] == PrescriptionStatus.READY_FOR_PICKUP.value])
        }
        
        return {"prescriptions": prescriptions, "stats": stats, "total": len(prescriptions)}
    
    @prescription_router.put("/{prescription_id}/status")
    async def update_prescription_status(
        prescription_id: str,
        data: PrescriptionUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update prescription status (pharmacy workflow)"""
        prescription = await db["prescriptions"].find_one({"id": prescription_id}, {"_id": 0})
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if data.status:
            status_value = data.status.value if hasattr(data.status, 'value') else data.status
            update_data["status"] = status_value
            
            if data.status == PrescriptionStatus.DISPENSED or status_value == "dispensed":
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
            "details": {"new_status": str(data.status), "rx_number": prescription.get("rx_number")},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Prescription updated", "status": str(data.status)}
    
    @prescription_router.post("/{prescription_id}/renew")
    async def renew_prescription(
        prescription_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Renew an existing prescription"""
        if user.get("role") not in ["physician", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can renew prescriptions")
        
        original = await db["prescriptions"].find_one({"id": prescription_id}, {"_id": 0})
        if not original:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        new_id = str(uuid.uuid4())
        new_rx_number = f"RX-{datetime.now().strftime('%Y%m%d')}-{new_id[:8].upper()}"
        
        renewed_prescription = {
            **original,
            "id": new_id,
            "rx_number": new_rx_number,
            "status": PrescriptionStatus.PENDING_VERIFICATION.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "renewed_from": prescription_id,
            "dispensed_at": None,
            "dispensed_by": None,
            "pharmacist_notes": None
        }
        
        await db["prescriptions"].insert_one(renewed_prescription)
        
        # Remove _id if it was added
        if "_id" in renewed_prescription:
            del renewed_prescription["_id"]
        
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
                "status": PrescriptionStatus.CANCELLED.value,
                "discontinued_at": datetime.now(timezone.utc).isoformat(),
                "discontinued_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "discontinue_reason": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Prescription discontinued"}
    
    # ============== E-PRESCRIPTION ROUTING ==============
    
    @prescription_router.post("/{prescription_id}/send-to-pharmacy")
    async def send_prescription_to_pharmacy(
        prescription_id: str,
        pharmacy_id: str,
        notes: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Route an e-prescription to an external pharmacy"""
        if user.get("role") not in ["physician", "nurse", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized to route prescriptions")
        
        prescription = await db["prescriptions"].find_one({"id": prescription_id}, {"_id": 0})
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Import pharmacy network to validate pharmacy
        from pharmacy_network_module import SEED_PHARMACIES
        
        pharmacy = None
        for p in SEED_PHARMACIES:
            if p.get("id") == pharmacy_id:
                pharmacy = p
                break
        
        if not pharmacy:
            raise HTTPException(status_code=404, detail="Pharmacy not found in network")
        
        # Create routing record
        routing_id = str(uuid.uuid4())
        routing_record = {
            "id": routing_id,
            "prescription_id": prescription_id,
            "rx_number": prescription.get("rx_number"),
            "pharmacy_id": pharmacy_id,
            "pharmacy_name": pharmacy.get("name"),
            "pharmacy_address": pharmacy.get("address"),
            "pharmacy_city": pharmacy.get("city"),
            "pharmacy_phone": pharmacy.get("phone"),
            "patient_id": prescription.get("patient_id"),
            "patient_name": prescription.get("patient_name"),
            "sent_by_id": user.get("id"),
            "sent_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "notes": notes,
            "status": "sent",  # sent, received, accepted, rejected, filled
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "received_at": None,
            "accepted_at": None,
            "filled_at": None,
            "rejection_reason": None
        }
        
        await db["prescription_routings"].insert_one(routing_record)
        
        # Remove _id if added
        if "_id" in routing_record:
            del routing_record["_id"]
        
        # Update prescription with routing info
        await db["prescriptions"].update_one(
            {"id": prescription_id},
            {"$set": {
                "pharmacy_id": pharmacy_id,
                "pharmacy_name": pharmacy.get("name"),
                "send_to_external": True,
                "routing_id": routing_id,
                "routing_status": "sent",
                "status": PrescriptionStatus.APPROVED.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "prescription_routed",
            "resource_type": "prescription",
            "resource_id": prescription_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "rx_number": prescription.get("rx_number"),
                "pharmacy_id": pharmacy_id,
                "pharmacy_name": pharmacy.get("name"),
                "routing_id": routing_id
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": f"Prescription sent to {pharmacy.get('name')}",
            "routing_id": routing_id,
            "pharmacy": {
                "id": pharmacy_id,
                "name": pharmacy.get("name"),
                "address": pharmacy.get("address"),
                "phone": pharmacy.get("phone")
            }
        }
    
    @prescription_router.get("/routing/{routing_id}/status")
    async def get_routing_status(
        routing_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get the status of a routed prescription"""
        routing = await db["prescription_routings"].find_one({"id": routing_id}, {"_id": 0})
        if not routing:
            raise HTTPException(status_code=404, detail="Routing record not found")
        
        return routing
    
    @prescription_router.get("/patient/{patient_id}/routed")
    async def get_patient_routed_prescriptions(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get all routed prescriptions for a patient"""
        routings = await db["prescription_routings"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("sent_at", -1).to_list(100)
        
        return {"routings": routings, "total": len(routings)}
    
    @prescription_router.put("/routing/{routing_id}/accept")
    async def accept_routed_prescription(
        routing_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Pharmacy accepts a routed prescription"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Pharmacy access required")
        
        routing = await db["prescription_routings"].find_one({"id": routing_id})
        if not routing:
            raise HTTPException(status_code=404, detail="Routing record not found")
        
        await db["prescription_routings"].update_one(
            {"id": routing_id},
            {"$set": {
                "status": "accepted",
                "accepted_at": datetime.now(timezone.utc).isoformat(),
                "accepted_by_id": user.get("id"),
                "accepted_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}"
            }}
        )
        
        # Update original prescription
        if routing.get("prescription_id"):
            await db["prescriptions"].update_one(
                {"id": routing["prescription_id"]},
                {"$set": {
                    "routing_status": "accepted",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"message": "Prescription accepted", "routing_id": routing_id}
    
    @prescription_router.put("/routing/{routing_id}/reject")
    async def reject_routed_prescription(
        routing_id: str,
        reason: str = "Unable to fulfill",
        user: dict = Depends(get_current_user)
    ):
        """Pharmacy rejects a routed prescription"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Pharmacy access required")
        
        routing = await db["prescription_routings"].find_one({"id": routing_id})
        if not routing:
            raise HTTPException(status_code=404, detail="Routing record not found")
        
        await db["prescription_routings"].update_one(
            {"id": routing_id},
            {"$set": {
                "status": "rejected",
                "rejected_at": datetime.now(timezone.utc).isoformat(),
                "rejection_reason": reason,
                "rejected_by_id": user.get("id"),
                "rejected_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}"
            }}
        )
        
        # Update original prescription
        if routing.get("prescription_id"):
            await db["prescriptions"].update_one(
                {"id": routing["prescription_id"]},
                {"$set": {
                    "routing_status": "rejected",
                    "routing_rejection_reason": reason,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"message": "Prescription rejected", "reason": reason}
    
    @prescription_router.put("/routing/{routing_id}/fill")
    async def mark_prescription_filled(
        routing_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Mark a routed prescription as filled"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Pharmacy access required")
        
        routing = await db["prescription_routings"].find_one({"id": routing_id})
        if not routing:
            raise HTTPException(status_code=404, detail="Routing record not found")
        
        await db["prescription_routings"].update_one(
            {"id": routing_id},
            {"$set": {
                "status": "filled",
                "filled_at": datetime.now(timezone.utc).isoformat(),
                "filled_by_id": user.get("id"),
                "filled_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}"
            }}
        )
        
        # Update original prescription
        if routing.get("prescription_id"):
            await db["prescriptions"].update_one(
                {"id": routing["prescription_id"]},
                {"$set": {
                    "routing_status": "filled",
                    "status": PrescriptionStatus.DISPENSED.value,
                    "dispensed_at": datetime.now(timezone.utc).isoformat(),
                    "dispensed_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"message": "Prescription marked as filled", "routing_id": routing_id}
    
    @prescription_router.get("/tracking/{rx_number}")
    async def track_prescription(rx_number: str):
        """Track a prescription by RX number (public endpoint for patients)"""
        prescription = await db["prescriptions"].find_one(
            {"rx_number": rx_number},
            {"_id": 0, "clinical_notes": 0}  # Exclude sensitive info
        )
        
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Get routing info if exists
        routing = None
        if prescription.get("routing_id"):
            routing = await db["prescription_routings"].find_one(
                {"id": prescription["routing_id"]},
                {"_id": 0}
            )
        
        # Build status timeline
        timeline = [
            {
                "status": "created",
                "timestamp": prescription.get("created_at"),
                "description": "Prescription created"
            }
        ]
        
        if routing:
            if routing.get("sent_at"):
                timeline.append({
                    "status": "sent",
                    "timestamp": routing["sent_at"],
                    "description": f"Sent to {routing.get('pharmacy_name')}"
                })
            if routing.get("accepted_at"):
                timeline.append({
                    "status": "accepted",
                    "timestamp": routing["accepted_at"],
                    "description": "Pharmacy accepted"
                })
            if routing.get("rejected_at"):
                timeline.append({
                    "status": "rejected",
                    "timestamp": routing["rejected_at"],
                    "description": f"Rejected: {routing.get('rejection_reason')}"
                })
            if routing.get("filled_at"):
                timeline.append({
                    "status": "filled",
                    "timestamp": routing["filled_at"],
                    "description": "Ready for pickup"
                })
        
        return {
            "rx_number": rx_number,
            "status": prescription.get("status"),
            "routing_status": prescription.get("routing_status"),
            "pharmacy_name": prescription.get("pharmacy_name"),
            "created_at": prescription.get("created_at"),
            "timeline": sorted(timeline, key=lambda x: x["timestamp"] if x["timestamp"] else ""),
            "medications": [
                {"name": m.get("medication_name"), "dosage": m.get("dosage"), "quantity": m.get("quantity")}
                for m in prescription.get("medications", [])
            ]
        }
    
    return prescription_router
