"""
Clinical Features Module for Yacco EMR
Includes Drug Interaction Alerts, Flowsheets, E-Prescribing, and SmartSets
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

clinical_router = APIRouter(prefix="/api/clinical", tags=["Clinical Features"])

# ============ Drug Interaction Database (Simplified) ============

DRUG_INTERACTIONS = {
    ("warfarin", "aspirin"): {"severity": "high", "description": "Increased risk of bleeding"},
    ("warfarin", "ibuprofen"): {"severity": "high", "description": "Increased risk of bleeding"},
    ("metformin", "contrast dye"): {"severity": "moderate", "description": "Risk of lactic acidosis"},
    ("lisinopril", "potassium"): {"severity": "moderate", "description": "Risk of hyperkalemia"},
    ("ssri", "maoi"): {"severity": "high", "description": "Risk of serotonin syndrome"},
    ("simvastatin", "grapefruit"): {"severity": "moderate", "description": "Increased statin levels"},
    ("digoxin", "amiodarone"): {"severity": "high", "description": "Increased digoxin toxicity"},
    ("methotrexate", "nsaid"): {"severity": "high", "description": "Increased methotrexate toxicity"},
    ("lithium", "nsaid"): {"severity": "moderate", "description": "Increased lithium levels"},
    ("clopidogrel", "omeprazole"): {"severity": "moderate", "description": "Reduced clopidogrel effectiveness"},
}

# Drug classes for interaction checking
DRUG_CLASSES = {
    "aspirin": ["nsaid", "antiplatelet"],
    "ibuprofen": ["nsaid"],
    "naproxen": ["nsaid"],
    "warfarin": ["anticoagulant"],
    "heparin": ["anticoagulant"],
    "metformin": ["antidiabetic"],
    "lisinopril": ["ace_inhibitor"],
    "enalapril": ["ace_inhibitor"],
    "fluoxetine": ["ssri"],
    "sertraline": ["ssri"],
    "phenelzine": ["maoi"],
}

# ============ Models ============

class DrugInteraction(BaseModel):
    drug1: str
    drug2: str
    severity: str  # high, moderate, low
    description: str
    recommendation: Optional[str] = None

class Flowsheet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    flowsheet_type: str  # vitals, intake_output, pain, neuro, etc.
    date: str
    entries: List[Dict] = []
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FlowsheetEntry(BaseModel):
    time: str
    parameter: str
    value: str
    unit: Optional[str] = None
    notes: Optional[str] = None

class Prescription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    medication_name: str
    strength: str
    dosage_form: str  # tablet, capsule, liquid, etc.
    quantity: int
    refills: int = 0
    sig: str  # Directions
    prescriber_id: str
    prescriber_name: str
    prescriber_npi: Optional[str] = None
    pharmacy_name: Optional[str] = None
    pharmacy_ncpdp: Optional[str] = None  # National Council for Prescription Drug Programs ID
    pharmacy_address: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    status: str = "pending"  # pending, sent, filled, cancelled
    daw: bool = False  # Dispense As Written
    diagnosis_code: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None

class SmartSet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    specialty: Optional[str] = None
    diagnosis_codes: List[str] = []
    orders: List[Dict] = []  # Pre-configured orders
    medications: List[Dict] = []  # Pre-configured medications
    documentation_templates: List[Dict] = []
    is_active: bool = True
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request Models
class CheckInteractionsRequest(BaseModel):
    patient_id: str
    new_medication: str

class CreatePrescriptionRequest(BaseModel):
    patient_id: str
    medication_name: str
    strength: str
    dosage_form: str
    quantity: int
    refills: int = 0
    sig: str
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    daw: bool = False
    diagnosis_code: Optional[str] = None
    notes: Optional[str] = None

class FlowsheetEntryRequest(BaseModel):
    time: str
    parameter: str
    value: str
    unit: Optional[str] = None
    notes: Optional[str] = None

def create_clinical_endpoints(db, get_current_user):
    """Create clinical feature endpoints"""
    
    def check_drug_interaction(drug1: str, drug2: str) -> Optional[DrugInteraction]:
        """Check for interaction between two drugs"""
        d1_lower = drug1.lower()
        d2_lower = drug2.lower()
        
        # Direct match
        key1 = (d1_lower, d2_lower)
        key2 = (d2_lower, d1_lower)
        
        if key1 in DRUG_INTERACTIONS:
            info = DRUG_INTERACTIONS[key1]
            return DrugInteraction(
                drug1=drug1,
                drug2=drug2,
                severity=info["severity"],
                description=info["description"]
            )
        if key2 in DRUG_INTERACTIONS:
            info = DRUG_INTERACTIONS[key2]
            return DrugInteraction(
                drug1=drug1,
                drug2=drug2,
                severity=info["severity"],
                description=info["description"]
            )
        
        # Check by drug class
        d1_classes = DRUG_CLASSES.get(d1_lower, [])
        d2_classes = DRUG_CLASSES.get(d2_lower, [])
        
        for c1 in d1_classes:
            for c2 in d2_classes:
                key1 = (c1, c2)
                key2 = (c2, c1)
                if key1 in DRUG_INTERACTIONS:
                    info = DRUG_INTERACTIONS[key1]
                    return DrugInteraction(
                        drug1=drug1,
                        drug2=drug2,
                        severity=info["severity"],
                        description=info["description"]
                    )
                if key2 in DRUG_INTERACTIONS:
                    info = DRUG_INTERACTIONS[key2]
                    return DrugInteraction(
                        drug1=drug1,
                        drug2=drug2,
                        severity=info["severity"],
                        description=info["description"]
                    )
        
        return None
    
    # ============ Drug Interaction Alerts ============
    
    @clinical_router.post("/interactions/check", response_model=List[DrugInteraction])
    async def check_interactions(
        request: CheckInteractionsRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Check for drug interactions with patient's current medications"""
        # Get patient's current medications
        current_meds = await db.medications.find(
            {"patient_id": request.patient_id, "status": "active"},
            {"_id": 0}
        ).to_list(100)
        
        interactions = []
        new_med = request.new_medication.lower()
        
        for med in current_meds:
            interaction = check_drug_interaction(request.new_medication, med["name"])
            if interaction:
                interactions.append(interaction)
        
        # Also check allergies
        allergies = await db.allergies.find(
            {"patient_id": request.patient_id},
            {"_id": 0}
        ).to_list(50)
        
        for allergy in allergies:
            if allergy["allergen"].lower() in new_med or new_med in allergy["allergen"].lower():
                interactions.append(DrugInteraction(
                    drug1=request.new_medication,
                    drug2=allergy["allergen"],
                    severity="high",
                    description=f"Patient has documented allergy: {allergy['reaction']}"
                ))
        
        return interactions
    
    @clinical_router.get("/interactions/database")
    async def get_interaction_database(current_user: dict = Depends(get_current_user)):
        """Get list of known drug interactions"""
        interactions = []
        for (drug1, drug2), info in DRUG_INTERACTIONS.items():
            interactions.append({
                "drug1": drug1,
                "drug2": drug2,
                "severity": info["severity"],
                "description": info["description"]
            })
        return interactions
    
    # ============ Flowsheets ============
    
    @clinical_router.post("/flowsheets")
    async def create_flowsheet(
        patient_id: str,
        flowsheet_type: str,
        date: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new flowsheet"""
        flowsheet = Flowsheet(
            patient_id=patient_id,
            flowsheet_type=flowsheet_type,
            date=date,
            created_by=current_user["id"]
        )
        
        fs_dict = flowsheet.model_dump()
        fs_dict["created_at"] = fs_dict["created_at"].isoformat()
        await db.flowsheets.insert_one(fs_dict)
        
        return {"message": "Flowsheet created", "flowsheet_id": flowsheet.id}
    
    @clinical_router.get("/flowsheets/{patient_id}")
    async def get_patient_flowsheets(
        patient_id: str,
        flowsheet_type: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get patient's flowsheets"""
        query = {"patient_id": patient_id}
        if flowsheet_type:
            query["flowsheet_type"] = flowsheet_type
        
        flowsheets = await db.flowsheets.find(query, {"_id": 0}).sort("date", -1).to_list(100)
        return flowsheets
    
    @clinical_router.post("/flowsheets/{flowsheet_id}/entries")
    async def add_flowsheet_entry(
        flowsheet_id: str,
        entry: FlowsheetEntryRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Add entry to flowsheet"""
        entry_dict = entry.model_dump()
        entry_dict["recorded_by"] = current_user["id"]
        entry_dict["recorded_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.flowsheets.update_one(
            {"id": flowsheet_id},
            {"$push": {"entries": entry_dict}}
        )
        
        return {"message": "Entry added to flowsheet"}
    
    @clinical_router.get("/flowsheets/templates")
    async def get_flowsheet_templates(current_user: dict = Depends(get_current_user)):
        """Get available flowsheet templates"""
        templates = [
            {
                "type": "vitals",
                "name": "Vital Signs",
                "parameters": ["Blood Pressure", "Heart Rate", "Respiratory Rate", "Temperature", "SpO2", "Pain Level"]
            },
            {
                "type": "intake_output",
                "name": "Intake & Output",
                "parameters": ["PO Intake", "IV Intake", "Urine Output", "Drain Output", "Emesis"]
            },
            {
                "type": "neuro",
                "name": "Neurological Assessment",
                "parameters": ["GCS Eye", "GCS Verbal", "GCS Motor", "Pupil Size L", "Pupil Size R", "Pupil Reaction L", "Pupil Reaction R"]
            },
            {
                "type": "pain",
                "name": "Pain Assessment",
                "parameters": ["Pain Score", "Location", "Quality", "Duration", "Intervention", "Re-assessment"]
            },
            {
                "type": "blood_glucose",
                "name": "Blood Glucose Log",
                "parameters": ["Blood Glucose", "Insulin Dose", "Insulin Type", "Meal Status"]
            }
        ]
        return templates
    
    # ============ E-Prescribing ============
    
    @clinical_router.post("/prescriptions")
    async def create_prescription(
        request: CreatePrescriptionRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Create and send an electronic prescription"""
        if current_user["role"] not in ["physician"]:
            raise HTTPException(status_code=403, detail="Only physicians can prescribe")
        
        # Get patient info
        patient = await db.patients.find_one({"id": request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check for drug interactions
        current_meds = await db.medications.find(
            {"patient_id": request.patient_id, "status": "active"},
            {"_id": 0}
        ).to_list(100)
        
        interactions = []
        for med in current_meds:
            interaction = check_drug_interaction(request.medication_name, med["name"])
            if interaction and interaction.severity == "high":
                interactions.append(interaction)
        
        # Create prescription
        prescription = Prescription(
            patient_id=request.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            medication_name=request.medication_name,
            strength=request.strength,
            dosage_form=request.dosage_form,
            quantity=request.quantity,
            refills=request.refills,
            sig=request.sig,
            prescriber_id=current_user["id"],
            prescriber_name=f"Dr. {current_user['first_name']} {current_user['last_name']}",
            pharmacy_name=request.pharmacy_name,
            pharmacy_phone=request.pharmacy_phone,
            daw=request.daw,
            diagnosis_code=request.diagnosis_code,
            notes=request.notes
        )
        
        rx_dict = prescription.model_dump()
        rx_dict["created_at"] = rx_dict["created_at"].isoformat()
        await db.prescriptions.insert_one(rx_dict)
        
        # Also add to patient's medication list
        med_data = {
            "id": str(uuid.uuid4()),
            "patient_id": request.patient_id,
            "name": request.medication_name,
            "dosage": request.strength,
            "frequency": request.sig,
            "route": request.dosage_form,
            "prescriber": prescription.prescriber_name,
            "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status": "active",
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.medications.insert_one(med_data)
        
        return {
            "message": "Prescription created",
            "prescription_id": prescription.id,
            "interactions": [i.model_dump() for i in interactions] if interactions else [],
            "warning": "High severity drug interactions detected!" if interactions else None
        }
    
    @clinical_router.get("/prescriptions/{patient_id}")
    async def get_patient_prescriptions(
        patient_id: str,
        status: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get patient's prescriptions"""
        query = {"patient_id": patient_id}
        if status:
            query["status"] = status
        
        prescriptions = await db.prescriptions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        return prescriptions
    
    @clinical_router.post("/prescriptions/{prescription_id}/send")
    async def send_prescription(
        prescription_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Send prescription to pharmacy (simulated)"""
        prescription = await db.prescriptions.find_one({"id": prescription_id}, {"_id": 0})
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # In production, this would integrate with SureScripts or similar e-prescribing network
        sent_at = datetime.now(timezone.utc).isoformat()
        await db.prescriptions.update_one(
            {"id": prescription_id},
            {"$set": {"status": "sent", "sent_at": sent_at}}
        )
        
        return {
            "message": "Prescription sent to pharmacy",
            "sent_at": sent_at,
            "pharmacy": prescription.get("pharmacy_name", "Default Pharmacy")
        }
    
    @clinical_router.post("/prescriptions/{prescription_id}/cancel")
    async def cancel_prescription(
        prescription_id: str,
        reason: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Cancel a prescription"""
        await db.prescriptions.update_one(
            {"id": prescription_id},
            {"$set": {"status": "cancelled", "cancel_reason": reason}}
        )
        return {"message": "Prescription cancelled"}
    
    # ============ SmartSets (Order Sets) ============
    
    @clinical_router.post("/smartsets")
    async def create_smartset(
        name: str,
        description: Optional[str] = None,
        specialty: Optional[str] = None,
        orders: List[Dict] = [],
        medications: List[Dict] = [],
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new SmartSet (order set template)"""
        smartset = SmartSet(
            name=name,
            description=description,
            specialty=specialty,
            orders=orders,
            medications=medications,
            created_by=current_user["id"]
        )
        
        ss_dict = smartset.model_dump()
        ss_dict["created_at"] = ss_dict["created_at"].isoformat()
        await db.smartsets.insert_one(ss_dict)
        
        return {"message": "SmartSet created", "smartset_id": smartset.id}
    
    @clinical_router.get("/smartsets")
    async def get_smartsets(
        specialty: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get available SmartSets"""
        query = {"is_active": True}
        if specialty:
            query["specialty"] = specialty
        
        smartsets = await db.smartsets.find(query, {"_id": 0}).to_list(100)
        return smartsets
    
    @clinical_router.post("/smartsets/{smartset_id}/apply")
    async def apply_smartset(
        smartset_id: str,
        patient_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Apply a SmartSet to a patient"""
        smartset = await db.smartsets.find_one({"id": smartset_id}, {"_id": 0})
        if not smartset:
            raise HTTPException(status_code=404, detail="SmartSet not found")
        
        created_orders = []
        created_meds = []
        
        # Create orders from SmartSet
        for order_template in smartset.get("orders", []):
            order_data = {
                "id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "order_type": order_template.get("order_type", "lab"),
                "description": order_template.get("description", ""),
                "priority": order_template.get("priority", "routine"),
                "instructions": order_template.get("instructions"),
                "status": "pending",
                "ordered_by": current_user["id"],
                "ordered_by_name": f"{current_user['first_name']} {current_user['last_name']}",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.orders.insert_one(order_data)
            created_orders.append(order_data["id"])
        
        return {
            "message": f"SmartSet '{smartset['name']}' applied",
            "created_orders": created_orders,
            "created_medications": created_meds
        }
    
    # Initialize some default SmartSets
    @clinical_router.post("/smartsets/seed")
    async def seed_smartsets(current_user: dict = Depends(get_current_user)):
        """Seed default SmartSets"""
        default_sets = [
            {
                "id": str(uuid.uuid4()),
                "name": "Admission Orders - General",
                "description": "Standard admission orders for general medicine",
                "specialty": "Internal Medicine",
                "orders": [
                    {"order_type": "lab", "description": "CBC with Differential", "priority": "routine"},
                    {"order_type": "lab", "description": "BMP (Basic Metabolic Panel)", "priority": "routine"},
                    {"order_type": "lab", "description": "Urinalysis", "priority": "routine"},
                    {"order_type": "imaging", "description": "Chest X-Ray PA/Lateral", "priority": "routine"},
                ],
                "medications": [],
                "is_active": True,
                "created_by": current_user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Chest Pain Workup",
                "description": "Orders for acute chest pain evaluation",
                "specialty": "Cardiology",
                "orders": [
                    {"order_type": "lab", "description": "Troponin I - Serial (0, 3, 6 hr)", "priority": "stat"},
                    {"order_type": "lab", "description": "BNP", "priority": "stat"},
                    {"order_type": "lab", "description": "D-Dimer", "priority": "stat"},
                    {"order_type": "imaging", "description": "EKG - 12 Lead", "priority": "stat"},
                    {"order_type": "imaging", "description": "Chest X-Ray", "priority": "urgent"},
                ],
                "medications": [],
                "is_active": True,
                "created_by": current_user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Diabetic Management",
                "description": "Orders for diabetic patient management",
                "specialty": "Endocrinology",
                "orders": [
                    {"order_type": "lab", "description": "HbA1c", "priority": "routine"},
                    {"order_type": "lab", "description": "Fasting Glucose", "priority": "routine"},
                    {"order_type": "lab", "description": "Lipid Panel", "priority": "routine"},
                    {"order_type": "lab", "description": "BMP", "priority": "routine"},
                    {"order_type": "lab", "description": "Microalbumin/Creatinine Ratio", "priority": "routine"},
                ],
                "medications": [],
                "is_active": True,
                "created_by": current_user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        for ss in default_sets:
            existing = await db.smartsets.find_one({"name": ss["name"]})
            if not existing:
                await db.smartsets.insert_one(ss)
        
        return {"message": "Default SmartSets seeded", "count": len(default_sets)}
    
    return clinical_router
