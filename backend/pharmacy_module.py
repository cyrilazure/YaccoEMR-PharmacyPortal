"""
Pharmacy Portal Module for Yacco EMR
Handles pharmacy registration, inventory management, and prescription fulfillment
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid
import bcrypt

router = APIRouter(prefix="/api/pharmacy", tags=["Pharmacy"])

# ============ ENUMS ============
class PharmacyStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

class PrescriptionStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    READY = "ready"
    DISPENSED = "dispensed"
    CANCELLED = "cancelled"

# ============ MODELS ============
class PharmacyRegister(BaseModel):
    name: str
    license_number: str
    email: EmailStr
    password: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    operating_hours: Optional[str] = "9:00 AM - 9:00 PM"
    accepts_insurance: bool = True
    delivery_available: bool = False

class PharmacyResponse(BaseModel):
    id: str
    name: str
    license_number: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    operating_hours: str
    accepts_insurance: bool
    delivery_available: bool
    status: str
    created_at: str
    medication_count: Optional[int] = 0

class PharmacyLogin(BaseModel):
    email: EmailStr
    password: str

class MedicationInventory(BaseModel):
    medication_name: str
    generic_name: Optional[str] = None
    ndc_code: Optional[str] = None  # National Drug Code
    dosage_form: str  # tablet, capsule, liquid, etc.
    strength: str  # e.g., "500mg", "10mg/5ml"
    quantity_in_stock: int
    unit_price: float
    manufacturer: Optional[str] = None
    requires_prescription: bool = True
    controlled_substance: bool = False
    schedule: Optional[str] = None  # Schedule II, III, IV, V

class MedicationInventoryResponse(MedicationInventory):
    id: str
    pharmacy_id: str
    last_updated: str

class PrescriptionCreate(BaseModel):
    patient_id: str
    patient_name: str
    medication_name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    quantity: int
    refills: int = 0
    instructions: Optional[str] = None
    diagnosis: Optional[str] = None
    pharmacy_id: str

class PrescriptionResponse(BaseModel):
    id: str
    prescription_number: str
    patient_id: str
    patient_name: str
    prescriber_id: str
    prescriber_name: str
    medication_name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    quantity: int
    refills: int
    refills_remaining: int
    instructions: Optional[str] = None
    diagnosis: Optional[str] = None
    pharmacy_id: str
    pharmacy_name: Optional[str] = None
    status: str
    prescribed_at: str
    filled_at: Optional[str] = None
    organization_id: Optional[str] = None

# ============ DRUG DATABASE ============
# Common medications database for quick lookup
DRUG_DATABASE = [
    # Pain & Inflammation
    {"name": "Acetaminophen", "generic": "Acetaminophen", "category": "Analgesic", "forms": ["tablet", "capsule", "liquid"], "strengths": ["325mg", "500mg", "650mg"], "controlled": False},
    {"name": "Ibuprofen", "generic": "Ibuprofen", "category": "NSAID", "forms": ["tablet", "capsule", "liquid"], "strengths": ["200mg", "400mg", "600mg", "800mg"], "controlled": False},
    {"name": "Naproxen", "generic": "Naproxen", "category": "NSAID", "forms": ["tablet"], "strengths": ["250mg", "500mg"], "controlled": False},
    {"name": "Tramadol", "generic": "Tramadol HCl", "category": "Opioid Analgesic", "forms": ["tablet", "capsule"], "strengths": ["50mg", "100mg"], "controlled": True, "schedule": "IV"},
    {"name": "Hydrocodone/APAP", "generic": "Hydrocodone/Acetaminophen", "category": "Opioid Analgesic", "forms": ["tablet"], "strengths": ["5/325mg", "7.5/325mg", "10/325mg"], "controlled": True, "schedule": "II"},
    
    # Antibiotics
    {"name": "Amoxicillin", "generic": "Amoxicillin", "category": "Antibiotic", "forms": ["capsule", "liquid"], "strengths": ["250mg", "500mg", "875mg"], "controlled": False},
    {"name": "Azithromycin", "generic": "Azithromycin", "category": "Antibiotic", "forms": ["tablet", "liquid"], "strengths": ["250mg", "500mg"], "controlled": False},
    {"name": "Ciprofloxacin", "generic": "Ciprofloxacin", "category": "Antibiotic", "forms": ["tablet"], "strengths": ["250mg", "500mg", "750mg"], "controlled": False},
    {"name": "Doxycycline", "generic": "Doxycycline Hyclate", "category": "Antibiotic", "forms": ["capsule", "tablet"], "strengths": ["50mg", "100mg"], "controlled": False},
    {"name": "Metronidazole", "generic": "Metronidazole", "category": "Antibiotic", "forms": ["tablet"], "strengths": ["250mg", "500mg"], "controlled": False},
    
    # Cardiovascular
    {"name": "Lisinopril", "generic": "Lisinopril", "category": "ACE Inhibitor", "forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg", "40mg"], "controlled": False},
    {"name": "Amlodipine", "generic": "Amlodipine Besylate", "category": "Calcium Channel Blocker", "forms": ["tablet"], "strengths": ["2.5mg", "5mg", "10mg"], "controlled": False},
    {"name": "Metoprolol", "generic": "Metoprolol Succinate", "category": "Beta Blocker", "forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg", "200mg"], "controlled": False},
    {"name": "Atorvastatin", "generic": "Atorvastatin Calcium", "category": "Statin", "forms": ["tablet"], "strengths": ["10mg", "20mg", "40mg", "80mg"], "controlled": False},
    {"name": "Losartan", "generic": "Losartan Potassium", "category": "ARB", "forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"], "controlled": False},
    
    # Diabetes
    {"name": "Metformin", "generic": "Metformin HCl", "category": "Antidiabetic", "forms": ["tablet"], "strengths": ["500mg", "850mg", "1000mg"], "controlled": False},
    {"name": "Glipizide", "generic": "Glipizide", "category": "Sulfonylurea", "forms": ["tablet"], "strengths": ["5mg", "10mg"], "controlled": False},
    {"name": "Insulin Glargine", "generic": "Insulin Glargine", "category": "Insulin", "forms": ["injection"], "strengths": ["100 units/mL"], "controlled": False},
    
    # Mental Health
    {"name": "Sertraline", "generic": "Sertraline HCl", "category": "SSRI", "forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"], "controlled": False},
    {"name": "Escitalopram", "generic": "Escitalopram Oxalate", "category": "SSRI", "forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg"], "controlled": False},
    {"name": "Fluoxetine", "generic": "Fluoxetine HCl", "category": "SSRI", "forms": ["capsule", "liquid"], "strengths": ["10mg", "20mg", "40mg"], "controlled": False},
    {"name": "Alprazolam", "generic": "Alprazolam", "category": "Benzodiazepine", "forms": ["tablet"], "strengths": ["0.25mg", "0.5mg", "1mg", "2mg"], "controlled": True, "schedule": "IV"},
    {"name": "Lorazepam", "generic": "Lorazepam", "category": "Benzodiazepine", "forms": ["tablet"], "strengths": ["0.5mg", "1mg", "2mg"], "controlled": True, "schedule": "IV"},
    
    # Respiratory
    {"name": "Albuterol", "generic": "Albuterol Sulfate", "category": "Bronchodilator", "forms": ["inhaler", "nebulizer"], "strengths": ["90mcg/actuation", "2.5mg/3mL"], "controlled": False},
    {"name": "Fluticasone", "generic": "Fluticasone Propionate", "category": "Corticosteroid", "forms": ["inhaler", "nasal spray"], "strengths": ["50mcg", "110mcg", "220mcg"], "controlled": False},
    {"name": "Montelukast", "generic": "Montelukast Sodium", "category": "Leukotriene Inhibitor", "forms": ["tablet", "chewable"], "strengths": ["4mg", "5mg", "10mg"], "controlled": False},
    
    # Gastrointestinal
    {"name": "Omeprazole", "generic": "Omeprazole", "category": "PPI", "forms": ["capsule"], "strengths": ["20mg", "40mg"], "controlled": False},
    {"name": "Pantoprazole", "generic": "Pantoprazole Sodium", "category": "PPI", "forms": ["tablet"], "strengths": ["20mg", "40mg"], "controlled": False},
    {"name": "Ondansetron", "generic": "Ondansetron", "category": "Antiemetic", "forms": ["tablet", "ODT"], "strengths": ["4mg", "8mg"], "controlled": False},
    
    # Thyroid
    {"name": "Levothyroxine", "generic": "Levothyroxine Sodium", "category": "Thyroid Hormone", "forms": ["tablet"], "strengths": ["25mcg", "50mcg", "75mcg", "100mcg", "125mcg", "150mcg"], "controlled": False},
    
    # Allergy
    {"name": "Cetirizine", "generic": "Cetirizine HCl", "category": "Antihistamine", "forms": ["tablet", "liquid"], "strengths": ["5mg", "10mg"], "controlled": False},
    {"name": "Loratadine", "generic": "Loratadine", "category": "Antihistamine", "forms": ["tablet"], "strengths": ["10mg"], "controlled": False},
    {"name": "Prednisone", "generic": "Prednisone", "category": "Corticosteroid", "forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg", "50mg"], "controlled": False},
]

# Dosage frequencies
FREQUENCIES = [
    {"code": "QD", "description": "Once daily"},
    {"code": "BID", "description": "Twice daily"},
    {"code": "TID", "description": "Three times daily"},
    {"code": "QID", "description": "Four times daily"},
    {"code": "Q4H", "description": "Every 4 hours"},
    {"code": "Q6H", "description": "Every 6 hours"},
    {"code": "Q8H", "description": "Every 8 hours"},
    {"code": "Q12H", "description": "Every 12 hours"},
    {"code": "PRN", "description": "As needed"},
    {"code": "HS", "description": "At bedtime"},
    {"code": "AC", "description": "Before meals"},
    {"code": "PC", "description": "After meals"},
    {"code": "STAT", "description": "Immediately"},
    {"code": "QOD", "description": "Every other day"},
    {"code": "QW", "description": "Once weekly"},
]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def setup_routes(db, get_current_user):
    """Setup pharmacy routes with database and auth dependency"""
    
    # ============ DRUG DATABASE ROUTES ============
    @router.get("/drugs")
    async def get_drug_database(
        search: Optional[str] = None,
        category: Optional[str] = None
    ):
        """Get list of available drugs from database"""
        drugs = DRUG_DATABASE.copy()
        
        if search:
            search_lower = search.lower()
            drugs = [d for d in drugs if search_lower in d["name"].lower() or search_lower in d["generic"].lower()]
        
        if category:
            drugs = [d for d in drugs if d["category"].lower() == category.lower()]
        
        return {"drugs": drugs, "total": len(drugs)}
    
    @router.get("/drugs/categories")
    async def get_drug_categories():
        """Get list of drug categories"""
        categories = list(set(d["category"] for d in DRUG_DATABASE))
        return {"categories": sorted(categories)}
    
    @router.get("/frequencies")
    async def get_dosage_frequencies():
        """Get list of dosage frequencies"""
        return {"frequencies": FREQUENCIES}
    
    # ============ PHARMACY REGISTRATION & AUTH ============
    @router.post("/register")
    async def register_pharmacy(pharmacy_data: PharmacyRegister):
        """Register a new pharmacy - requires approval"""
        # Check if pharmacy already exists
        existing = await db.pharmacies.find_one({"email": pharmacy_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_license = await db.pharmacies.find_one({"license_number": pharmacy_data.license_number})
        if existing_license:
            raise HTTPException(status_code=400, detail="License number already registered")
        
        pharmacy_id = str(uuid.uuid4())
        pharmacy_doc = {
            "id": pharmacy_id,
            "name": pharmacy_data.name,
            "license_number": pharmacy_data.license_number,
            "email": pharmacy_data.email,
            "password": hash_password(pharmacy_data.password),
            "phone": pharmacy_data.phone,
            "address": pharmacy_data.address,
            "city": pharmacy_data.city,
            "state": pharmacy_data.state,
            "zip_code": pharmacy_data.zip_code,
            "operating_hours": pharmacy_data.operating_hours,
            "accepts_insurance": pharmacy_data.accepts_insurance,
            "delivery_available": pharmacy_data.delivery_available,
            "status": PharmacyStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": None
        }
        
        await db.pharmacies.insert_one(pharmacy_doc)
        
        return {
            "message": "Pharmacy registration submitted. Pending approval.",
            "pharmacy_id": pharmacy_id,
            "status": PharmacyStatus.PENDING
        }
    
    @router.post("/login")
    async def pharmacy_login(login_data: PharmacyLogin):
        """Pharmacy login"""
        pharmacy = await db.pharmacies.find_one({"email": login_data.email}, {"_id": 0})
        
        if not pharmacy:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(login_data.password, pharmacy["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if pharmacy["status"] != PharmacyStatus.APPROVED:
            raise HTTPException(status_code=403, detail=f"Pharmacy account is {pharmacy['status']}")
        
        import jwt
        import os
        
        JWT_SECRET = os.environ.get('JWT_SECRET', 'yacco-emr-secret-key-2024')
        token = jwt.encode({
            "pharmacy_id": pharmacy["id"],
            "email": pharmacy["email"],
            "name": pharmacy["name"],
            "type": "pharmacy",
            "exp": datetime.now(timezone.utc).timestamp() + (24 * 60 * 60)
        }, JWT_SECRET, algorithm="HS256")
        
        return {
            "token": token,
            "pharmacy": {
                "id": pharmacy["id"],
                "name": pharmacy["name"],
                "email": pharmacy["email"],
                "status": pharmacy["status"]
            }
        }
    
    # ============ PHARMACY MANAGEMENT (Super Admin) ============
    @router.get("/pending")
    async def get_pending_pharmacies(current_user: dict = Depends(get_current_user)):
        """Get pending pharmacy registrations (Super Admin only)"""
        if current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super admin access required")
        
        pharmacies = await db.pharmacies.find(
            {"status": PharmacyStatus.PENDING},
            {"_id": 0, "password": 0}
        ).to_list(100)
        
        return {"pharmacies": pharmacies, "count": len(pharmacies)}
    
    @router.post("/{pharmacy_id}/approve")
    async def approve_pharmacy(pharmacy_id: str, current_user: dict = Depends(get_current_user)):
        """Approve a pharmacy registration"""
        if current_user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super admin access required")
        
        result = await db.pharmacies.update_one(
            {"id": pharmacy_id},
            {"$set": {
                "status": PharmacyStatus.APPROVED,
                "approved_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
        
        return {"message": "Pharmacy approved successfully"}
    
    @router.get("/all")
    async def get_all_pharmacies(
        status: Optional[str] = None,
        city: Optional[str] = None
    ):
        """Get all approved pharmacies (public endpoint for prescribing)"""
        query = {"status": PharmacyStatus.APPROVED}
        
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        
        pharmacies = await db.pharmacies.find(
            query,
            {"_id": 0, "password": 0}
        ).to_list(500)
        
        # Add medication count for each pharmacy
        for pharmacy in pharmacies:
            med_count = await db.pharmacy_inventory.count_documents({"pharmacy_id": pharmacy["id"]})
            pharmacy["medication_count"] = med_count
        
        return {"pharmacies": pharmacies, "count": len(pharmacies)}
    
    # ============ INVENTORY MANAGEMENT ============
    @router.post("/inventory")
    async def add_medication_to_inventory(
        medication: MedicationInventory,
        pharmacy_id: str,  # From pharmacy token
    ):
        """Add medication to pharmacy inventory"""
        # Verify pharmacy exists and is approved
        pharmacy = await db.pharmacies.find_one({"id": pharmacy_id, "status": PharmacyStatus.APPROVED})
        if not pharmacy:
            raise HTTPException(status_code=404, detail="Pharmacy not found or not approved")
        
        # Check if medication already in inventory
        existing = await db.pharmacy_inventory.find_one({
            "pharmacy_id": pharmacy_id,
            "medication_name": medication.medication_name,
            "strength": medication.strength
        })
        
        if existing:
            # Update quantity instead
            await db.pharmacy_inventory.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "quantity_in_stock": medication.quantity_in_stock,
                    "unit_price": medication.unit_price,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {"message": "Inventory updated", "id": existing["id"]}
        
        inventory_id = str(uuid.uuid4())
        inventory_doc = {
            "id": inventory_id,
            "pharmacy_id": pharmacy_id,
            **medication.model_dump(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        await db.pharmacy_inventory.insert_one(inventory_doc)
        
        return {"message": "Medication added to inventory", "id": inventory_id}
    
    @router.get("/inventory/{pharmacy_id}")
    async def get_pharmacy_inventory(pharmacy_id: str, search: Optional[str] = None):
        """Get pharmacy inventory"""
        query = {"pharmacy_id": pharmacy_id}
        
        if search:
            query["$or"] = [
                {"medication_name": {"$regex": search, "$options": "i"}},
                {"generic_name": {"$regex": search, "$options": "i"}}
            ]
        
        inventory = await db.pharmacy_inventory.find(query, {"_id": 0}).to_list(1000)
        
        return {"inventory": inventory, "count": len(inventory)}
    
    @router.put("/inventory/{inventory_id}")
    async def update_inventory_item(
        inventory_id: str,
        quantity: int,
        unit_price: Optional[float] = None
    ):
        """Update inventory quantity/price"""
        update_data = {
            "quantity_in_stock": quantity,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        if unit_price is not None:
            update_data["unit_price"] = unit_price
        
        result = await db.pharmacy_inventory.update_one(
            {"id": inventory_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return {"message": "Inventory updated"}
    
    @router.delete("/inventory/{inventory_id}")
    async def delete_inventory_item(inventory_id: str):
        """Remove medication from inventory"""
        result = await db.pharmacy_inventory.delete_one({"id": inventory_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        return {"message": "Inventory item deleted"}
    
    # ============ FIND PHARMACIES BY MEDICATION ============
    @router.get("/search/by-medication")
    async def find_pharmacies_by_medication(
        medication_name: str,
        city: Optional[str] = None,
        min_quantity: int = 1
    ):
        """Find pharmacies that have a specific medication in stock"""
        # Find inventory items matching the medication
        query = {
            "medication_name": {"$regex": medication_name, "$options": "i"},
            "quantity_in_stock": {"$gte": min_quantity}
        }
        
        inventory_items = await db.pharmacy_inventory.find(query, {"_id": 0}).to_list(500)
        
        # Get unique pharmacy IDs
        pharmacy_ids = list(set(item["pharmacy_id"] for item in inventory_items))
        
        # Get pharmacy details
        pharmacy_query = {
            "id": {"$in": pharmacy_ids},
            "status": PharmacyStatus.APPROVED
        }
        
        if city:
            pharmacy_query["city"] = {"$regex": city, "$options": "i"}
        
        pharmacies = await db.pharmacies.find(pharmacy_query, {"_id": 0, "password": 0}).to_list(100)
        
        # Add inventory info for each pharmacy
        result = []
        for pharmacy in pharmacies:
            matching_inventory = [i for i in inventory_items if i["pharmacy_id"] == pharmacy["id"]]
            result.append({
                **pharmacy,
                "available_medications": matching_inventory
            })
        
        return {"pharmacies": result, "count": len(result)}
    
    # ============ PRESCRIPTIONS ============
    @router.post("/prescriptions")
    async def create_prescription(
        prescription: PrescriptionCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create and send a prescription to pharmacy"""
        if current_user.get("role") not in ["physician", "admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can create prescriptions")
        
        # Verify pharmacy exists
        pharmacy = await db.pharmacies.find_one({"id": prescription.pharmacy_id, "status": PharmacyStatus.APPROVED})
        if not pharmacy:
            raise HTTPException(status_code=404, detail="Pharmacy not found or not approved")
        
        # Generate prescription number
        rx_count = await db.prescriptions.count_documents({})
        rx_number = f"RX-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{rx_count + 1:05d}"
        
        prescription_doc = {
            "id": str(uuid.uuid4()),
            "prescription_number": rx_number,
            "patient_id": prescription.patient_id,
            "patient_name": prescription.patient_name,
            "prescriber_id": current_user["id"],
            "prescriber_name": f"{current_user['first_name']} {current_user['last_name']}",
            "medication_name": prescription.medication_name,
            "generic_name": prescription.generic_name,
            "dosage": prescription.dosage,
            "frequency": prescription.frequency,
            "quantity": prescription.quantity,
            "refills": prescription.refills,
            "refills_remaining": prescription.refills,
            "instructions": prescription.instructions,
            "diagnosis": prescription.diagnosis,
            "pharmacy_id": prescription.pharmacy_id,
            "pharmacy_name": pharmacy["name"],
            "status": PrescriptionStatus.SENT,
            "prescribed_at": datetime.now(timezone.utc).isoformat(),
            "filled_at": None,
            "organization_id": current_user.get("organization_id")
        }
        
        await db.prescriptions.insert_one(prescription_doc)
        
        # Also create an order record for the EMR
        order_doc = {
            "id": str(uuid.uuid4()),
            "type": "medication",
            "patient_id": prescription.patient_id,
            "description": f"E-Prescription: {prescription.medication_name} {prescription.dosage}",
            "status": "in_progress",
            "priority": "routine",
            "ordered_by": current_user["id"],
            "ordered_by_name": f"{current_user['first_name']} {current_user['last_name']}",
            "prescription_id": prescription_doc["id"],
            "prescription_number": rx_number,
            "organization_id": current_user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": None
        }
        await db.orders.insert_one(order_doc)
        
        return {
            "message": "Prescription sent to pharmacy",
            "prescription_number": rx_number,
            "prescription_id": prescription_doc["id"],
            "pharmacy_name": pharmacy["name"]
        }
    
    @router.get("/prescriptions/patient/{patient_id}")
    async def get_patient_prescriptions(
        patient_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get prescriptions for a patient"""
        query = {"patient_id": patient_id}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        prescriptions = await db.prescriptions.find(query, {"_id": 0}).sort("prescribed_at", -1).to_list(100)
        
        return {"prescriptions": prescriptions, "count": len(prescriptions)}
    
    @router.get("/prescriptions/pharmacy/{pharmacy_id}")
    async def get_pharmacy_prescriptions(
        pharmacy_id: str,
        status: Optional[str] = None
    ):
        """Get prescriptions received by a pharmacy"""
        query = {"pharmacy_id": pharmacy_id}
        
        if status:
            query["status"] = status
        
        prescriptions = await db.prescriptions.find(query, {"_id": 0}).sort("prescribed_at", -1).to_list(100)
        
        return {"prescriptions": prescriptions, "count": len(prescriptions)}
    
    @router.put("/prescriptions/{prescription_id}/status")
    async def update_prescription_status(
        prescription_id: str,
        status: PrescriptionStatus
    ):
        """Update prescription status (for pharmacy use)"""
        update_data = {"status": status}
        
        if status == PrescriptionStatus.DISPENSED:
            update_data["filled_at"] = datetime.now(timezone.utc).isoformat()
            
            # Decrease refills remaining
            prescription = await db.prescriptions.find_one({"id": prescription_id})
            if prescription and prescription["refills_remaining"] > 0:
                update_data["refills_remaining"] = prescription["refills_remaining"] - 1
        
        result = await db.prescriptions.update_one(
            {"id": prescription_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        # Update order status if linked
        if status == PrescriptionStatus.DISPENSED:
            await db.orders.update_one(
                {"prescription_id": prescription_id},
                {"$set": {"status": "completed"}}
            )
        
        return {"message": f"Prescription status updated to {status}"}
    
    return router
