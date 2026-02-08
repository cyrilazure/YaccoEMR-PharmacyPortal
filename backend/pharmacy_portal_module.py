"""
Ghana National Pharmacy Portal Module
====================================
Standalone pharmacy authentication and management system.
Separate from hospital EMR - pharmacy-specific operations only.

Features:
- Independent pharmacy authentication
- Pharmacy IT Admin portal for staff management
- Drug inventory management
- e-Prescription receiving & dispensing
- Sales to hospitals & individuals
- NHIS claim routing
- Automated stock reorder system
"""

import uuid
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from enum import Enum
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

pharmacy_portal_router = APIRouter(prefix="/api/pharmacy-portal", tags=["Pharmacy Portal"])

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "pharmacy-portal-secret-key")
JWT_ALGORITHM = "HS256"


# ============== Enums ==============

class PharmacyStaffRole(str, Enum):
    PHARMACY_OWNER = "pharmacy_owner"
    PHARMACY_IT_ADMIN = "pharmacy_it_admin"
    SUPERINTENDENT_PHARMACIST = "superintendent_pharmacist"
    PHARMACIST = "pharmacist"
    PHARMACY_TECHNICIAN = "pharmacy_technician"
    PHARMACY_ASSISTANT = "pharmacy_assistant"
    CASHIER = "cashier"
    INVENTORY_MANAGER = "inventory_manager"
    DELIVERY_STAFF = "delivery_staff"


class PharmacyDepartment(str, Enum):
    DISPENSARY = "dispensary"
    INVENTORY = "inventory"
    PROCUREMENT = "procurement"
    SALES = "sales"
    DELIVERY = "delivery"
    ADMINISTRATION = "administration"
    COMPOUNDING = "compounding"
    CLINICAL_SERVICES = "clinical_services"


class PharmacyRegistrationStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class DrugCategory(str, Enum):
    PRESCRIPTION_ONLY = "prescription_only"
    OVER_THE_COUNTER = "over_the_counter"
    CONTROLLED_SUBSTANCE = "controlled_substance"
    PHARMACY_ONLY = "pharmacy_only"
    GENERAL_SALE = "general_sale"


class DosageForm(str, Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    SUSPENSION = "suspension"
    INJECTION = "injection"
    CREAM = "cream"
    OINTMENT = "ointment"
    GEL = "gel"
    DROPS = "drops"
    INHALER = "inhaler"
    SUPPOSITORY = "suppository"
    PATCH = "patch"
    POWDER = "powder"
    SOLUTION = "solution"
    SPRAY = "spray"
    LOTION = "lotion"


class SaleType(str, Enum):
    RETAIL = "retail"  # Individual customer
    WHOLESALE = "wholesale"  # To other pharmacies
    HOSPITAL = "hospital"  # To hospitals
    NHIS = "nhis"  # NHIS covered
    INSURANCE = "insurance"  # Private insurance


# ============== Pydantic Models ==============

class PharmacyRegistration(BaseModel):
    pharmacy_name: str
    license_number: str
    region: str
    district: str
    town: str
    address: str
    gps_address: Optional[str] = None
    phone: str
    email: EmailStr
    superintendent_pharmacist_name: str
    superintendent_license_number: str
    ownership_type: str = "retail"
    operating_hours: str = "Mon-Sat 8AM-8PM"
    password: str
    has_nhis_accreditation: bool = False


class PharmacyStaffCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    role: PharmacyStaffRole
    department: PharmacyDepartment
    license_number: Optional[str] = None  # For pharmacists


class PharmacyStaffResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    role: PharmacyStaffRole
    department: PharmacyDepartment
    pharmacy_id: str
    pharmacy_name: str
    is_active: bool
    created_at: str


class PharmacyLogin(BaseModel):
    email: EmailStr
    password: str


class DrugCreate(BaseModel):
    generic_name: str
    brand_name: Optional[str] = None
    manufacturer: str
    strength: str
    dosage_form: DosageForm
    category: DrugCategory
    unit_price: float
    pack_size: int = 1
    reorder_level: int = 10
    description: Optional[str] = None
    side_effects: Optional[str] = None
    contraindications: Optional[str] = None
    storage_conditions: Optional[str] = None


class InventoryItem(BaseModel):
    drug_id: str
    batch_number: str
    quantity: int
    cost_price: float
    selling_price: float
    expiry_date: str
    supplier: Optional[str] = None


class SaleCreate(BaseModel):
    items: List[Dict[str, Any]]  # [{drug_id, quantity, unit_price, discount}]
    sale_type: SaleType
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    hospital_id: Optional[str] = None
    prescription_id: Optional[str] = None
    nhis_member_id: Optional[str] = None
    payment_method: str = "cash"
    notes: Optional[str] = None


class InsuranceClaimCreate(BaseModel):
    sale_id: str
    insurance_provider: str  # "NHIS" or private insurer name
    member_id: str
    member_name: str
    claim_amount: float
    items: List[Dict[str, Any]]


# ============== Helper Functions ==============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_pharmacy_token(user_data: dict, expires_hours: int = 24) -> str:
    payload = {
        **user_data,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        "iat": datetime.now(timezone.utc),
        "type": "pharmacy_portal"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ============== Module Factory ==============

def create_pharmacy_portal_router(db) -> APIRouter:
    router = APIRouter(prefix="/api/pharmacy-portal", tags=["Pharmacy Portal"])
    
    # ============== Authentication Dependency ==============
    
    async def get_current_pharmacy_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Verify pharmacy portal JWT token"""
        try:
            token = credentials.credentials
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            if payload.get("type") != "pharmacy_portal":
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            user_id = payload.get("user_id")
            user = await db["pharmacy_staff"].find_one({"id": user_id}, {"_id": 0})
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            if not user.get("is_active"):
                raise HTTPException(status_code=401, detail="Account deactivated")
            
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def require_roles(*roles: PharmacyStaffRole):
        """Decorator to require specific pharmacy roles"""
        async def role_checker(user: dict = Depends(get_current_pharmacy_user)):
            if user.get("role") not in [r.value for r in roles]:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Required roles: {[r.value for r in roles]}"
                )
            return user
        return role_checker
    
    # ============== PUBLIC ENDPOINTS (No Auth) ==============
    
    @router.get("/public/regions")
    async def get_regions_with_pharmacy_counts():
        """Get all Ghana regions with pharmacy counts - PUBLIC"""
        regions = [
            "Greater Accra", "Ashanti", "Central", "Eastern", "Western",
            "Western North", "Volta", "Oti", "Northern", "Savannah",
            "North East", "Upper East", "Upper West", "Bono", "Bono East", "Ahafo"
        ]
        
        result = []
        for region in regions:
            count = await db["pharmacies"].count_documents({"region": region})
            result.append({
                "region": region,
                "pharmacy_count": count,
                "region_code": region.lower().replace(" ", "_")
            })
        
        return {"regions": result, "total_pharmacies": sum(r["pharmacy_count"] for r in result)}
    
    @router.get("/public/pharmacies")
    async def search_pharmacies_public(
        region: Optional[str] = None,
        district: Optional[str] = None,
        search: Optional[str] = None,
        license_number: Optional[str] = None,
        has_nhis: Optional[bool] = None,
        has_24hr: Optional[bool] = None,
        ownership_type: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ):
        """Search pharmacies - PUBLIC endpoint"""
        query = {"status": {"$in": ["active", "approved"]}}
        
        if region:
            query["region"] = {"$regex": region, "$options": "i"}
        if district:
            query["district"] = {"$regex": district, "$options": "i"}
        if license_number:
            query["license_number"] = {"$regex": license_number, "$options": "i"}
        if has_nhis is not None:
            query["has_nhis"] = has_nhis
        if has_24hr is not None:
            query["has_24hr_service"] = has_24hr
        if ownership_type:
            query["ownership_type"] = ownership_type
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"city": {"$regex": search, "$options": "i"}},
                {"town": {"$regex": search, "$options": "i"}},
                {"address": {"$regex": search, "$options": "i"}}
            ]
        
        pharmacies = await db["pharmacies"].find(
            query, 
            {"_id": 0, "password": 0}
        ).sort("name", 1).skip(skip).limit(limit).to_list(limit)
        
        total = await db["pharmacies"].count_documents(query)
        
        return {
            "pharmacies": pharmacies,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    
    @router.get("/public/pharmacies/{pharmacy_id}")
    async def get_pharmacy_profile_public(pharmacy_id: str):
        """Get pharmacy profile - PUBLIC"""
        pharmacy = await db["pharmacies"].find_one(
            {"id": pharmacy_id},
            {"_id": 0, "password": 0}
        )
        
        if not pharmacy:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
        
        # Get services offered
        services = await db["pharmacy_services"].find(
            {"pharmacy_id": pharmacy_id},
            {"_id": 0}
        ).to_list(50)
        
        return {
            "pharmacy": pharmacy,
            "services": services
        }
    
    # ============== PHARMACY REGISTRATION ==============
    
    @router.post("/register")
    async def register_pharmacy(registration: PharmacyRegistration):
        """Register a new pharmacy - requires approval"""
        
        # Check if license number already registered
        existing = await db["pharmacies"].find_one({
            "$or": [
                {"license_number": registration.license_number},
                {"email": registration.email}
            ]
        })
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Pharmacy with this license number or email already exists"
            )
        
        pharmacy_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Create pharmacy record
        pharmacy = {
            "id": pharmacy_id,
            "name": registration.pharmacy_name,
            "license_number": registration.license_number,
            "region": registration.region,
            "district": registration.district,
            "town": registration.town,
            "city": registration.town,  # Alias
            "address": registration.address,
            "gps_address": registration.gps_address,
            "phone": registration.phone,
            "email": registration.email,
            "superintendent_pharmacist_name": registration.superintendent_pharmacist_name,
            "superintendent_license_number": registration.superintendent_license_number,
            "ownership_type": registration.ownership_type,
            "operating_hours": registration.operating_hours,
            "has_nhis": registration.has_nhis_accreditation,
            "has_nhis_accreditation": registration.has_nhis_accreditation,
            "has_24hr_service": False,
            "has_delivery": False,
            "status": PharmacyRegistrationStatus.PENDING.value,
            "registration_status": PharmacyRegistrationStatus.PENDING.value,
            "created_at": now,
            "updated_at": now
        }
        
        await db["pharmacies"].insert_one(pharmacy)
        
        # Create superintendent pharmacist as first staff (IT Admin)
        staff_id = str(uuid.uuid4())
        superintendent = {
            "id": staff_id,
            "pharmacy_id": pharmacy_id,
            "pharmacy_name": registration.pharmacy_name,
            "email": registration.email,
            "password": hash_password(registration.password),
            "first_name": registration.superintendent_pharmacist_name.split()[0],
            "last_name": " ".join(registration.superintendent_pharmacist_name.split()[1:]) or "Pharmacist",
            "phone": registration.phone,
            "role": PharmacyStaffRole.PHARMACY_IT_ADMIN.value,
            "department": PharmacyDepartment.ADMINISTRATION.value,
            "license_number": registration.superintendent_license_number,
            "is_active": True,
            "is_superintendent": True,
            "created_at": now
        }
        
        await db["pharmacy_staff"].insert_one(superintendent)
        
        # Create audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "pharmacy_registration",
            "details": f"New pharmacy registered: {registration.pharmacy_name}",
            "performed_by": staff_id,
            "timestamp": now
        })
        
        return {
            "message": "Pharmacy registration submitted successfully",
            "pharmacy_id": pharmacy_id,
            "status": "pending",
            "note": "Your registration is pending approval. You will be notified once approved."
        }
    
    # ============== PHARMACY AUTHENTICATION ==============
    
    @router.post("/auth/login")
    async def pharmacy_login(credentials: PharmacyLogin):
        """Pharmacy staff login"""
        user = await db["pharmacy_staff"].find_one({"email": credentials.email})
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(credentials.password, user.get("password", "")):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.get("is_active"):
            raise HTTPException(status_code=401, detail="Account deactivated")
        
        # Check pharmacy status
        pharmacy = await db["pharmacies"].find_one({"id": user.get("pharmacy_id")})
        if not pharmacy:
            raise HTTPException(status_code=401, detail="Pharmacy not found")
        
        if pharmacy.get("status") not in ["active", "approved"]:
            raise HTTPException(
                status_code=401,
                detail=f"Pharmacy registration status: {pharmacy.get('status')}. Please wait for approval."
            )
        
        # Create token
        token = create_pharmacy_token({
            "user_id": user["id"],
            "pharmacy_id": user["pharmacy_id"],
            "role": user["role"],
            "email": user["email"]
        })
        
        # Update last login
        await db["pharmacy_staff"].update_one(
            {"id": user["id"]},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
                "department": user.get("department"),
                "pharmacy_id": user["pharmacy_id"],
                "pharmacy_name": user.get("pharmacy_name")
            },
            "pharmacy": {
                "id": pharmacy["id"],
                "name": pharmacy["name"],
                "region": pharmacy.get("region"),
                "status": pharmacy.get("status")
            }
        }
    
    @router.get("/auth/me")
    async def get_current_user_info(user: dict = Depends(get_current_pharmacy_user)):
        """Get current logged-in pharmacy user info"""
        pharmacy = await db["pharmacies"].find_one(
            {"id": user.get("pharmacy_id")},
            {"_id": 0, "password": 0}
        )
        
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"],
                "department": user.get("department"),
                "pharmacy_id": user["pharmacy_id"]
            },
            "pharmacy": pharmacy
        }
    
    # ============== PHARMACY IT ADMIN - STAFF MANAGEMENT ==============
    
    @router.post("/admin/staff")
    async def create_pharmacy_staff(
        staff: PharmacyStaffCreate,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER
        ))
    ):
        """Create new pharmacy staff member"""
        pharmacy_id = user.get("pharmacy_id")
        
        # Check if email exists
        existing = await db["pharmacy_staff"].find_one({"email": staff.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        pharmacy = await db["pharmacies"].find_one({"id": pharmacy_id})
        
        staff_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Default password is phone number
        default_password = staff.phone.replace("+", "").replace(" ", "")[-8:]
        
        new_staff = {
            "id": staff_id,
            "pharmacy_id": pharmacy_id,
            "pharmacy_name": pharmacy.get("name"),
            "email": staff.email,
            "password": hash_password(default_password),
            "first_name": staff.first_name,
            "last_name": staff.last_name,
            "phone": staff.phone,
            "role": staff.role.value,
            "department": staff.department.value,
            "license_number": staff.license_number,
            "is_active": True,
            "is_temp_password": True,
            "created_at": now,
            "created_by": user["id"]
        }
        
        await db["pharmacy_staff"].insert_one(new_staff)
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "staff_created",
            "details": f"New staff created: {staff.first_name} {staff.last_name} ({staff.role.value})",
            "performed_by": user["id"],
            "timestamp": now
        })
        
        return {
            "message": "Staff member created successfully",
            "staff_id": staff_id,
            "default_password": default_password,
            "note": "Please share the temporary password with the staff member securely"
        }
    
    @router.get("/admin/staff")
    async def list_pharmacy_staff(
        department: Optional[str] = None,
        role: Optional[str] = None,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """List all pharmacy staff"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id}
        if department:
            query["department"] = department
        if role:
            query["role"] = role
        
        staff = await db["pharmacy_staff"].find(
            query,
            {"_id": 0, "password": 0}
        ).to_list(100)
        
        return {"staff": staff, "total": len(staff)}
    
    @router.put("/admin/staff/{staff_id}/status")
    async def update_staff_status(
        staff_id: str,
        is_active: bool,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER
        ))
    ):
        """Activate or deactivate staff member"""
        pharmacy_id = user.get("pharmacy_id")
        
        result = await db["pharmacy_staff"].update_one(
            {"id": staff_id, "pharmacy_id": pharmacy_id},
            {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        return {"message": f"Staff member {'activated' if is_active else 'deactivated'}"}
    
    @router.get("/admin/departments")
    async def get_pharmacy_departments(user: dict = Depends(get_current_pharmacy_user)):
        """Get all pharmacy department types"""
        return {
            "departments": [
                {"code": d.value, "name": d.value.replace("_", " ").title()}
                for d in PharmacyDepartment
            ]
        }
    
    @router.get("/admin/roles")
    async def get_pharmacy_roles(user: dict = Depends(get_current_pharmacy_user)):
        """Get all pharmacy staff roles"""
        return {
            "roles": [
                {"code": r.value, "name": r.value.replace("_", " ").title()}
                for r in PharmacyStaffRole
            ]
        }
    
    # ============== DRUG CATALOG MANAGEMENT ==============
    
    @router.post("/drugs")
    async def add_drug_to_catalog(
        drug: DrugCreate,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.INVENTORY_MANAGER
        ))
    ):
        """Add a new drug to the pharmacy catalog"""
        pharmacy_id = user.get("pharmacy_id")
        
        drug_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        drug_record = {
            "id": drug_id,
            "pharmacy_id": pharmacy_id,
            **drug.dict(),
            "current_stock": 0,
            "is_active": True,
            "created_at": now,
            "created_by": user["id"]
        }
        
        await db["pharmacy_drugs"].insert_one(drug_record)
        
        return {"message": "Drug added to catalog", "drug_id": drug_id}
    
    @router.get("/drugs")
    async def list_pharmacy_drugs(
        search: Optional[str] = None,
        category: Optional[str] = None,
        low_stock: bool = False,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """List drugs in pharmacy catalog"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id, "is_active": True}
        
        if search:
            query["$or"] = [
                {"generic_name": {"$regex": search, "$options": "i"}},
                {"brand_name": {"$regex": search, "$options": "i"}},
                {"manufacturer": {"$regex": search, "$options": "i"}}
            ]
        if category:
            query["category"] = category
        if low_stock:
            query["$expr"] = {"$lte": ["$current_stock", "$reorder_level"]}
        
        drugs = await db["pharmacy_drugs"].find(query, {"_id": 0}).to_list(500)
        
        return {"drugs": drugs, "total": len(drugs)}
    
    # ============== INVENTORY MANAGEMENT ==============
    
    @router.post("/inventory/receive")
    async def receive_inventory(
        item: InventoryItem,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.INVENTORY_MANAGER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.PHARMACY_IT_ADMIN
        ))
    ):
        """Receive new inventory stock"""
        pharmacy_id = user.get("pharmacy_id")
        
        # Verify drug exists
        drug = await db["pharmacy_drugs"].find_one({
            "id": item.drug_id,
            "pharmacy_id": pharmacy_id
        })
        
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found in catalog")
        
        inventory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        inventory_record = {
            "id": inventory_id,
            "pharmacy_id": pharmacy_id,
            "drug_id": item.drug_id,
            "drug_name": drug.get("generic_name"),
            "brand_name": drug.get("brand_name"),
            "batch_number": item.batch_number,
            "quantity_received": item.quantity,
            "quantity_remaining": item.quantity,
            "cost_price": item.cost_price,
            "selling_price": item.selling_price,
            "expiry_date": item.expiry_date,
            "supplier": item.supplier,
            "received_at": now,
            "received_by": user["id"]
        }
        
        await db["pharmacy_inventory"].insert_one(inventory_record)
        
        # Update drug stock
        await db["pharmacy_drugs"].update_one(
            {"id": item.drug_id},
            {"$inc": {"current_stock": item.quantity}}
        )
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "inventory_received",
            "details": f"Received {item.quantity} units of {drug.get('generic_name')} (Batch: {item.batch_number})",
            "performed_by": user["id"],
            "timestamp": now
        })
        
        return {"message": "Inventory received successfully", "inventory_id": inventory_id}
    
    @router.get("/inventory")
    async def get_inventory(
        low_stock: bool = False,
        expiring_soon: bool = False,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get current inventory with optional filters"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id, "quantity_remaining": {"$gt": 0}}
        
        if expiring_soon:
            # Items expiring within 90 days
            ninety_days = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()[:10]
            query["expiry_date"] = {"$lte": ninety_days}
        
        inventory = await db["pharmacy_inventory"].find(query, {"_id": 0}).to_list(500)
        
        # Get low stock items
        if low_stock:
            low_stock_drugs = await db["pharmacy_drugs"].find(
                {
                    "pharmacy_id": pharmacy_id,
                    "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
                },
                {"_id": 0}
            ).to_list(100)
            return {"inventory": inventory, "low_stock_items": low_stock_drugs}
        
        return {"inventory": inventory, "total": len(inventory)}
    
    @router.get("/inventory/alerts")
    async def get_inventory_alerts(user: dict = Depends(get_current_pharmacy_user)):
        """Get inventory alerts (low stock, expiring soon)"""
        pharmacy_id = user.get("pharmacy_id")
        
        # Low stock
        low_stock = await db["pharmacy_drugs"].find(
            {
                "pharmacy_id": pharmacy_id,
                "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
            },
            {"_id": 0}
        ).to_list(100)
        
        # Expiring within 90 days
        ninety_days = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()[:10]
        expiring = await db["pharmacy_inventory"].find(
            {
                "pharmacy_id": pharmacy_id,
                "quantity_remaining": {"$gt": 0},
                "expiry_date": {"$lte": ninety_days}
            },
            {"_id": 0}
        ).to_list(100)
        
        # Expired items
        today = datetime.now(timezone.utc).isoformat()[:10]
        expired = await db["pharmacy_inventory"].find(
            {
                "pharmacy_id": pharmacy_id,
                "quantity_remaining": {"$gt": 0},
                "expiry_date": {"$lt": today}
            },
            {"_id": 0}
        ).to_list(100)
        
        return {
            "low_stock": low_stock,
            "low_stock_count": len(low_stock),
            "expiring_soon": expiring,
            "expiring_soon_count": len(expiring),
            "expired": expired,
            "expired_count": len(expired)
        }
    
    # ============== SALES ==============
    
    @router.post("/sales")
    async def create_sale(
        sale: SaleCreate,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.PHARMACY_TECHNICIAN,
            PharmacyStaffRole.CASHIER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Create a new sale/dispensing record"""
        pharmacy_id = user.get("pharmacy_id")
        
        sale_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        total_amount = 0
        sale_items = []
        
        for item in sale.items:
            drug = await db["pharmacy_drugs"].find_one({
                "id": item["drug_id"],
                "pharmacy_id": pharmacy_id
            })
            
            if not drug:
                raise HTTPException(status_code=404, detail=f"Drug {item['drug_id']} not found")
            
            if drug.get("current_stock", 0) < item["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {drug.get('generic_name')}"
                )
            
            item_total = item["quantity"] * item.get("unit_price", drug.get("unit_price", 0))
            discount = item.get("discount", 0)
            item_total -= discount
            total_amount += item_total
            
            sale_items.append({
                "drug_id": item["drug_id"],
                "drug_name": drug.get("generic_name"),
                "brand_name": drug.get("brand_name"),
                "quantity": item["quantity"],
                "unit_price": item.get("unit_price", drug.get("unit_price", 0)),
                "discount": discount,
                "total": item_total
            })
            
            # Deduct from inventory (FIFO - oldest batch first)
            remaining_qty = item["quantity"]
            inventory_batches = await db["pharmacy_inventory"].find(
                {
                    "pharmacy_id": pharmacy_id,
                    "drug_id": item["drug_id"],
                    "quantity_remaining": {"$gt": 0}
                }
            ).sort("expiry_date", 1).to_list(10)
            
            for batch in inventory_batches:
                if remaining_qty <= 0:
                    break
                deduct = min(remaining_qty, batch["quantity_remaining"])
                await db["pharmacy_inventory"].update_one(
                    {"id": batch["id"]},
                    {"$inc": {"quantity_remaining": -deduct}}
                )
                remaining_qty -= deduct
            
            # Update drug stock
            await db["pharmacy_drugs"].update_one(
                {"id": item["drug_id"]},
                {"$inc": {"current_stock": -item["quantity"]}}
            )
        
        # Create sale record
        sale_record = {
            "id": sale_id,
            "pharmacy_id": pharmacy_id,
            "sale_type": sale.sale_type.value,
            "items": sale_items,
            "total_amount": total_amount,
            "customer_name": sale.customer_name,
            "customer_phone": sale.customer_phone,
            "hospital_id": sale.hospital_id,
            "prescription_id": sale.prescription_id,
            "nhis_member_id": sale.nhis_member_id,
            "payment_method": sale.payment_method,
            "payment_status": "paid" if sale.payment_method != "credit" else "pending",
            "notes": sale.notes,
            "created_at": now,
            "created_by": user["id"],
            "cashier_name": f"{user.get('first_name')} {user.get('last_name')}"
        }
        
        await db["pharmacy_sales"].insert_one(sale_record)
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "sale_created",
            "details": f"Sale #{sale_id[:8]} - {len(sale_items)} items, Total: {total_amount}",
            "performed_by": user["id"],
            "timestamp": now
        })
        
        return {
            "message": "Sale completed successfully",
            "sale_id": sale_id,
            "total_amount": total_amount,
            "items_count": len(sale_items)
        }
    
    @router.get("/sales")
    async def get_sales(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sale_type: Optional[str] = None,
        limit: int = 50,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get sales history"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id}
        
        if start_date:
            query["created_at"] = {"$gte": start_date}
        if end_date:
            query.setdefault("created_at", {})["$lte"] = end_date
        if sale_type:
            query["sale_type"] = sale_type
        
        sales = await db["pharmacy_sales"].find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        # Calculate totals
        total_revenue = sum(s.get("total_amount", 0) for s in sales)
        
        return {
            "sales": sales,
            "total": len(sales),
            "total_revenue": total_revenue
        }
    
    # ============== E-PRESCRIPTION RECEIVING ==============
    
    @router.get("/prescriptions/incoming")
    async def get_incoming_prescriptions(
        status: Optional[str] = None,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get e-prescriptions routed to this pharmacy"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id}
        if status:
            query["status"] = status
        
        prescriptions = await db["prescription_routing"].find(
            query, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {"prescriptions": prescriptions, "total": len(prescriptions)}
    
    @router.put("/prescriptions/{routing_id}/accept")
    async def accept_prescription(
        routing_id: str,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Accept an incoming e-prescription"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        result = await db["prescription_routing"].update_one(
            {"id": routing_id, "pharmacy_id": pharmacy_id},
            {
                "$set": {
                    "status": "accepted",
                    "accepted_at": now,
                    "accepted_by": user["id"]
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return {"message": "Prescription accepted"}
    
    @router.put("/prescriptions/{routing_id}/dispense")
    async def dispense_prescription(
        routing_id: str,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Mark prescription as dispensed"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        result = await db["prescription_routing"].update_one(
            {"id": routing_id, "pharmacy_id": pharmacy_id},
            {
                "$set": {
                    "status": "dispensed",
                    "dispensed_at": now,
                    "dispensed_by": user["id"]
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return {"message": "Prescription marked as dispensed"}
    
    # ============== INSURANCE CLAIMS ==============
    
    @router.post("/insurance/claims")
    async def submit_insurance_claim(
        claim: InsuranceClaimCreate,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.PHARMACY_IT_ADMIN
        ))
    ):
        """Submit an insurance claim (NHIS or private)"""
        pharmacy_id = user.get("pharmacy_id")
        pharmacy = await db["pharmacies"].find_one({"id": pharmacy_id})
        
        claim_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        claim_record = {
            "id": claim_id,
            "pharmacy_id": pharmacy_id,
            "pharmacy_name": pharmacy.get("name"),
            "sale_id": claim.sale_id,
            "insurance_provider": claim.insurance_provider,
            "member_id": claim.member_id,
            "member_name": claim.member_name,
            "claim_amount": claim.claim_amount,
            "items": claim.items,
            "status": "submitted",
            "submitted_at": now,
            "submitted_by": user["id"]
        }
        
        await db["pharmacy_insurance_claims"].insert_one(claim_record)
        
        return {
            "message": "Insurance claim submitted",
            "claim_id": claim_id,
            "status": "submitted"
        }
    
    @router.get("/insurance/claims")
    async def get_insurance_claims(
        status: Optional[str] = None,
        provider: Optional[str] = None,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get insurance claims"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id}
        if status:
            query["status"] = status
        if provider:
            query["insurance_provider"] = provider
        
        claims = await db["pharmacy_insurance_claims"].find(
            query, {"_id": 0}
        ).sort("submitted_at", -1).to_list(100)
        
        return {"claims": claims, "total": len(claims)}
    
    # ============== DASHBOARD & ANALYTICS ==============
    
    @router.get("/dashboard")
    async def get_pharmacy_dashboard(user: dict = Depends(get_current_pharmacy_user)):
        """Get pharmacy dashboard data"""
        pharmacy_id = user.get("pharmacy_id")
        today = datetime.now(timezone.utc).isoformat()[:10]
        
        # Today's sales
        today_sales = await db["pharmacy_sales"].find(
            {"pharmacy_id": pharmacy_id, "created_at": {"$gte": today}}
        ).to_list(100)
        
        today_revenue = sum(s.get("total_amount", 0) for s in today_sales)
        
        # Pending prescriptions
        pending_rx = await db["prescription_routing"].count_documents({
            "pharmacy_id": pharmacy_id,
            "status": "sent"
        })
        
        # Low stock count
        low_stock = await db["pharmacy_drugs"].count_documents({
            "pharmacy_id": pharmacy_id,
            "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
        })
        
        # Expiring soon (30 days)
        thirty_days = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        expiring = await db["pharmacy_inventory"].count_documents({
            "pharmacy_id": pharmacy_id,
            "quantity_remaining": {"$gt": 0},
            "expiry_date": {"$lte": thirty_days}
        })
        
        # Total drugs in catalog
        total_drugs = await db["pharmacy_drugs"].count_documents({
            "pharmacy_id": pharmacy_id,
            "is_active": True
        })
        
        # Pending insurance claims
        pending_claims = await db["pharmacy_insurance_claims"].count_documents({
            "pharmacy_id": pharmacy_id,
            "status": "submitted"
        })
        
        return {
            "today_sales_count": len(today_sales),
            "today_revenue": today_revenue,
            "pending_prescriptions": pending_rx,
            "low_stock_count": low_stock,
            "expiring_soon_count": expiring,
            "total_drugs": total_drugs,
            "pending_insurance_claims": pending_claims
        }
    
    # ============== AUDIT LOGS ==============
    
    @router.get("/audit-logs")
    async def get_audit_logs(
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        limit: int = 100,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Get pharmacy audit logs"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id}
        if action:
            query["action"] = action
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        
        logs = await db["pharmacy_audit_logs"].find(
            query, {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"logs": logs, "total": len(logs)}
    
    # ============== REORDER SYSTEM ==============
    
    @router.get("/reorder/suggestions")
    async def get_reorder_suggestions(user: dict = Depends(get_current_pharmacy_user)):
        """Get automatic reorder suggestions based on stock levels"""
        pharmacy_id = user.get("pharmacy_id")
        
        # Get items below reorder level
        low_stock_drugs = await db["pharmacy_drugs"].find(
            {
                "pharmacy_id": pharmacy_id,
                "$expr": {"$lte": ["$current_stock", "$reorder_level"]}
            },
            {"_id": 0}
        ).to_list(100)
        
        suggestions = []
        for drug in low_stock_drugs:
            # Suggest ordering enough to meet 2x reorder level
            suggested_qty = (drug.get("reorder_level", 10) * 2) - drug.get("current_stock", 0)
            suggestions.append({
                "drug_id": drug["id"],
                "drug_name": drug.get("generic_name"),
                "brand_name": drug.get("brand_name"),
                "current_stock": drug.get("current_stock", 0),
                "reorder_level": drug.get("reorder_level", 10),
                "suggested_quantity": max(suggested_qty, drug.get("pack_size", 1)),
                "estimated_cost": suggested_qty * drug.get("unit_price", 0),
                "priority": "high" if drug.get("current_stock", 0) == 0 else "medium"
            })
        
        return {
            "suggestions": sorted(suggestions, key=lambda x: x["priority"]),
            "total_items": len(suggestions)
        }
    
    @router.post("/reorder/create-order")
    async def create_purchase_order(
        items: List[Dict[str, Any]] = Body(...),
        supplier: str = Body(...),
        user: dict = Depends(require_roles(
            PharmacyStaffRole.INVENTORY_MANAGER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.PHARMACY_IT_ADMIN
        ))
    ):
        """Create a purchase order from reorder suggestions"""
        pharmacy_id = user.get("pharmacy_id")
        
        order_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        total_amount = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in items)
        
        purchase_order = {
            "id": order_id,
            "pharmacy_id": pharmacy_id,
            "supplier": supplier,
            "items": items,
            "total_amount": total_amount,
            "status": "pending",
            "created_at": now,
            "created_by": user["id"]
        }
        
        await db["pharmacy_purchase_orders"].insert_one(purchase_order)
        
        return {
            "message": "Purchase order created",
            "order_id": order_id,
            "total_amount": total_amount
        }
    
    # ============== GLOBAL MEDICATION DATABASE ==============
    
    @router.get("/medications/search")
    async def search_global_medications(
        query: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Search the global medication database"""
        from medication_database import search_medications, get_medication_categories
        
        results = search_medications(query or "", category, limit)
        
        # Format results
        medications = []
        for med in results:
            medications.append({
                "generic_name": med["generic_name"],
                "brand_names": med.get("brand_names", []),
                "category": med.get("category", ""),
                "dosage_forms": med.get("dosage_forms", []),
                "strengths": med.get("strengths", [])
            })
        
        return {
            "medications": medications,
            "total": len(medications),
            "categories": get_medication_categories() if not category else None
        }
    
    @router.get("/medications/categories")
    async def get_medication_categories_list(user: dict = Depends(get_current_pharmacy_user)):
        """Get all medication categories"""
        from medication_database import get_medication_categories
        
        categories = get_medication_categories()
        
        return {
            "categories": [
                {"code": cat, "name": cat.replace("_", " ").title()}
                for cat in categories
            ]
        }
    
    @router.post("/drugs/seed")
    async def seed_drugs_from_database(
        body: Optional[Dict[str, Any]] = Body(default={}),
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Seed drugs from global medication database into pharmacy catalog"""
        from medication_database import get_all_medications, get_medications_by_category
        
        categories = body.get("categories") if body else None
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        # Get medications to seed
        if categories:
            medications = []
            for cat in categories:
                medications.extend(get_medications_by_category(cat))
        else:
            medications = get_all_medications()
        
        added_count = 0
        skipped_count = 0
        
        for med in medications:
            # Check if drug already exists
            existing = await db["pharmacy_drugs"].find_one({
                "pharmacy_id": pharmacy_id,
                "generic_name": med["generic_name"]
            })
            
            if existing:
                skipped_count += 1
                continue
            
            # Map category to drug category enum
            category_map = {
                "opioid_analgesic": "controlled_substance",
                "psychiatric_benzodiazepine": "controlled_substance",
                "anesthetic_general": "prescription_only",
                "anesthetic_local": "prescription_only",
                "antibiotic": "prescription_only",
                "antiviral_arv": "prescription_only",
                "antitubercular": "prescription_only",
                "hormone": "prescription_only",
                "contraceptive": "prescription_only",
            }
            
            drug_category = "pharmacy_only"
            for key, val in category_map.items():
                if key in med.get("category", ""):
                    drug_category = val
                    break
            
            if "analgesic" in med.get("category", "") and "opioid" not in med.get("category", ""):
                drug_category = "over_the_counter"
            if "vitamin" in med.get("category", "") or "mineral" in med.get("category", ""):
                drug_category = "general_sale"
            if "antihistamine" in med.get("category", ""):
                drug_category = "pharmacy_only"
            
            # Create drug record
            drug_id = str(uuid.uuid4())
            primary_form = med.get("dosage_forms", ["tablet"])[0]
            primary_strength = med.get("strengths", [""])[0]
            
            drug_record = {
                "id": drug_id,
                "pharmacy_id": pharmacy_id,
                "generic_name": med["generic_name"],
                "brand_name": med.get("brand_names", [""])[0] if med.get("brand_names") else "",
                "brand_names": med.get("brand_names", []),
                "manufacturer": "Various",
                "strength": primary_strength,
                "all_strengths": med.get("strengths", []),
                "dosage_form": primary_form,
                "all_dosage_forms": med.get("dosage_forms", []),
                "category": drug_category,
                "therapeutic_category": med.get("category", ""),
                "unit_price": 0.0,  # To be set by pharmacy
                "pack_size": 1,
                "reorder_level": 10,
                "current_stock": 0,
                "is_active": True,
                "created_at": now,
                "created_by": user["id"]
            }
            
            await db["pharmacy_drugs"].insert_one(drug_record)
            added_count += 1
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "drugs_seeded",
            "details": f"Seeded {added_count} drugs from global database (skipped {skipped_count} existing)",
            "performed_by": user["id"],
            "timestamp": now
        })
        
        return {
            "message": "Drug catalog seeded successfully",
            "added": added_count,
            "skipped": skipped_count,
            "total_in_catalog": await db["pharmacy_drugs"].count_documents({"pharmacy_id": pharmacy_id})
        }
    
    # ============== UPDATE DRUG PRICES ==============
    
    @router.put("/drugs/{drug_id}")
    async def update_drug(
        drug_id: str,
        unit_price: Optional[float] = Body(None),
        reorder_level: Optional[int] = Body(None),
        pack_size: Optional[int] = Body(None),
        is_active: Optional[bool] = Body(None),
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.INVENTORY_MANAGER
        ))
    ):
        """Update drug information (pricing, reorder levels)"""
        pharmacy_id = user.get("pharmacy_id")
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if unit_price is not None:
            update_data["unit_price"] = unit_price
        if reorder_level is not None:
            update_data["reorder_level"] = reorder_level
        if pack_size is not None:
            update_data["pack_size"] = pack_size
        if is_active is not None:
            update_data["is_active"] = is_active
        
        result = await db["pharmacy_drugs"].update_one(
            {"id": drug_id, "pharmacy_id": pharmacy_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Drug not found")
        
        return {"message": "Drug updated successfully"}
    
    # ============== BATCH PRICE UPDATE ==============
    
    @router.post("/drugs/batch-update-prices")
    async def batch_update_drug_prices(
        updates: List[Dict[str, Any]] = Body(...),  # [{drug_id, unit_price, reorder_level}]
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.INVENTORY_MANAGER
        ))
    ):
        """Batch update drug prices"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        updated = 0
        for update in updates:
            result = await db["pharmacy_drugs"].update_one(
                {"id": update.get("drug_id"), "pharmacy_id": pharmacy_id},
                {"$set": {
                    "unit_price": update.get("unit_price", 0),
                    "reorder_level": update.get("reorder_level", 10),
                    "updated_at": now
                }}
            )
            if result.modified_count > 0:
                updated += 1
        
        return {"message": f"Updated {updated} drugs", "updated": updated}
    
    # ============== PHARMACY APPROVAL (Platform Admin) ==============
    
    @router.put("/admin/pharmacies/{pharmacy_id}/approve")
    async def approve_pharmacy(
        pharmacy_id: str,
        status: str = Body(..., embed=True),  # "approved" or "rejected"
        notes: Optional[str] = Body(None, embed=True)
    ):
        """Approve or reject pharmacy registration (Platform Admin only)"""
        # This would require platform admin auth - simplified for now
        
        if status not in ["approved", "rejected", "active"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        result = await db["pharmacies"].update_one(
            {"id": pharmacy_id},
            {"$set": {
                "status": status,
                "registration_status": status,
                "approval_notes": notes,
                "approved_at": datetime.now(timezone.utc).isoformat() if status == "approved" else None
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Pharmacy not found")
        
        return {"message": f"Pharmacy {status}"}
    
    @router.get("/admin/pharmacies/pending")
    async def list_pending_pharmacies():
        """List pharmacies pending approval"""
        pharmacies = await db["pharmacies"].find(
            {"status": {"$in": ["pending", "under_review"]}},
            {"_id": 0, "password": 0}
        ).to_list(100)
        
        return {"pharmacies": pharmacies, "total": len(pharmacies)}
    
    # ============== PHASE 3: HOSPITAL-PHARMACY CONNECTION ==============
    
    # ============== E-PRESCRIPTION FROM HOSPITAL TO PHARMACY ==============
    
    @router.post("/eprescription/receive")
    async def receive_hospital_prescription(
        prescription_id: str = Body(...),
        rx_number: str = Body(...),
        patient_name: str = Body(...),
        patient_phone: Optional[str] = Body(None),
        prescriber_name: str = Body(...),
        hospital_name: str = Body(...),
        hospital_id: Optional[str] = Body(None),
        medications: List[Dict[str, Any]] = Body(...),
        diagnosis: Optional[str] = Body(None),
        clinical_notes: Optional[str] = Body(None),
        priority: str = Body("routine"),
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Receive an e-prescription routed from a hospital EMR"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        # Check if prescription already exists
        existing = await db["pharmacy_prescriptions"].find_one({
            "prescription_id": prescription_id,
            "pharmacy_id": pharmacy_id
        })
        
        if existing:
            return {"message": "Prescription already received", "status": "duplicate"}
        
        # Create pharmacy prescription record
        rx_id = str(uuid.uuid4())
        prescription_record = {
            "id": rx_id,
            "pharmacy_id": pharmacy_id,
            "prescription_id": prescription_id,
            "rx_number": rx_number,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "prescriber_name": prescriber_name,
            "hospital_name": hospital_name,
            "hospital_id": hospital_id,
            "medications": medications,
            "diagnosis": diagnosis,
            "clinical_notes": clinical_notes,
            "priority": priority,
            "status": "received",  # received, processing, ready, dispensed, cancelled
            "received_at": now,
            "accepted_at": None,
            "dispensed_at": None,
            "dispensed_by": None,
            "created_at": now
        }
        
        await db["pharmacy_prescriptions"].insert_one(prescription_record)
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "prescription_received",
            "entity_type": "prescription",
            "entity_id": rx_id,
            "details": {
                "rx_number": rx_number,
                "patient_name": patient_name,
                "hospital_name": hospital_name,
                "medication_count": len(medications)
            },
            "performed_by": user["id"],
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "timestamp": now
        })
        
        return {
            "message": "Prescription received successfully",
            "prescription_id": rx_id,
            "rx_number": rx_number,
            "status": "received"
        }
    
    @router.put("/eprescription/{rx_id}/accept")
    async def accept_eprescription(
        rx_id: str,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.PHARMACY_IT_ADMIN
        ))
    ):
        """Accept a received e-prescription for processing"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        result = await db["pharmacy_prescriptions"].update_one(
            {"id": rx_id, "pharmacy_id": pharmacy_id, "status": "received"},
            {"$set": {
                "status": "processing",
                "accepted_at": now,
                "accepted_by": user["id"]
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found or already processed")
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "prescription_accepted",
            "entity_type": "prescription",
            "entity_id": rx_id,
            "performed_by": user["id"],
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "timestamp": now
        })
        
        return {"message": "Prescription accepted for processing", "status": "processing"}
    
    @router.put("/eprescription/{rx_id}/ready")
    async def mark_prescription_ready(
        rx_id: str,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.PHARMACY_TECHNICIAN
        ))
    ):
        """Mark prescription as ready for pickup/delivery"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        result = await db["pharmacy_prescriptions"].update_one(
            {"id": rx_id, "pharmacy_id": pharmacy_id, "status": "processing"},
            {"$set": {
                "status": "ready",
                "ready_at": now,
                "ready_by": user["id"]
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Prescription not found or not in processing state")
        
        return {"message": "Prescription ready for pickup", "status": "ready"}
    
    @router.put("/eprescription/{rx_id}/dispense")
    async def dispense_eprescription(
        rx_id: str,
        dispensing_notes: Optional[str] = Body(None),
        user: dict = Depends(require_roles(
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.PHARMACIST,
            PharmacyStaffRole.PHARMACY_TECHNICIAN
        ))
    ):
        """Complete dispensing of a prescription"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        # Get prescription
        prescription = await db["pharmacy_prescriptions"].find_one({
            "id": rx_id,
            "pharmacy_id": pharmacy_id
        })
        
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        if prescription.get("status") not in ["processing", "ready"]:
            raise HTTPException(status_code=400, detail="Prescription must be in processing or ready state")
        
        # Update prescription
        result = await db["pharmacy_prescriptions"].update_one(
            {"id": rx_id, "pharmacy_id": pharmacy_id},
            {"$set": {
                "status": "dispensed",
                "dispensed_at": now,
                "dispensed_by": user["id"],
                "dispensed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "dispensing_notes": dispensing_notes
            }}
        )
        
        # Deduct inventory (FIFO)
        for med in prescription.get("medications", []):
            drug_name = med.get("medication_name", "").lower()
            quantity = med.get("quantity", 1)
            
            # Find matching drug in catalog
            drug = await db["pharmacy_drugs"].find_one({
                "pharmacy_id": pharmacy_id,
                "generic_name": {"$regex": drug_name, "$options": "i"}
            })
            
            if drug:
                # Deduct from inventory batches (FIFO - oldest first)
                remaining_qty = quantity
                batches = await db["pharmacy_inventory"].find({
                    "drug_id": drug["id"],
                    "pharmacy_id": pharmacy_id,
                    "quantity_remaining": {"$gt": 0}
                }).sort("expiry_date", 1).to_list(10)
                
                for batch in batches:
                    if remaining_qty <= 0:
                        break
                    
                    deduct = min(batch["quantity_remaining"], remaining_qty)
                    await db["pharmacy_inventory"].update_one(
                        {"id": batch["id"]},
                        {"$inc": {"quantity_remaining": -deduct}}
                    )
                    remaining_qty -= deduct
                
                # Update drug stock count
                await db["pharmacy_drugs"].update_one(
                    {"id": drug["id"]},
                    {"$inc": {"current_stock": -quantity}}
                )
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "prescription_dispensed",
            "entity_type": "prescription",
            "entity_id": rx_id,
            "details": {
                "rx_number": prescription.get("rx_number"),
                "patient_name": prescription.get("patient_name"),
                "medication_count": len(prescription.get("medications", []))
            },
            "performed_by": user["id"],
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "timestamp": now
        })
        
        return {"message": "Prescription dispensed successfully", "status": "dispensed"}
    
    # ============== SUPPLY REQUEST SYSTEM ==============
    
    @router.post("/supply-requests/create")
    async def create_supply_request(
        target_pharmacy_id: str = Body(...),
        items: List[Dict[str, Any]] = Body(...),  # [{drug_name, quantity, urgency}]
        notes: Optional[str] = Body(None),
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.INVENTORY_MANAGER
        ))
    ):
        """Create a supply request to another pharmacy in the network"""
        requesting_pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        # Validate target pharmacy exists
        target_pharmacy = await db["pharmacies"].find_one({"id": target_pharmacy_id})
        if not target_pharmacy:
            raise HTTPException(status_code=404, detail="Target pharmacy not found")
        
        # Get requesting pharmacy info
        requesting_pharmacy = await db["pharmacies"].find_one({"id": requesting_pharmacy_id})
        
        request_id = str(uuid.uuid4())
        supply_request = {
            "id": request_id,
            "requesting_pharmacy_id": requesting_pharmacy_id,
            "requesting_pharmacy_name": requesting_pharmacy.get("name") if requesting_pharmacy else "Unknown",
            "target_pharmacy_id": target_pharmacy_id,
            "target_pharmacy_name": target_pharmacy.get("name"),
            "items": items,
            "notes": notes,
            "status": "pending",  # pending, accepted, partially_accepted, rejected, fulfilled, cancelled
            "created_by": user["id"],
            "created_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": now,
            "updated_at": now,
            "response": None,
            "response_notes": None,
            "responded_at": None,
            "fulfilled_at": None
        }
        
        await db["pharmacy_supply_requests"].insert_one(supply_request)
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": requesting_pharmacy_id,
            "action": "supply_request_created",
            "entity_type": "supply_request",
            "entity_id": request_id,
            "details": {
                "target_pharmacy": target_pharmacy.get("name"),
                "item_count": len(items),
                "total_quantity": sum(item.get("quantity", 0) for item in items)
            },
            "performed_by": user["id"],
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "timestamp": now
        })
        
        return {
            "message": "Supply request created",
            "request_id": request_id,
            "target_pharmacy": target_pharmacy.get("name")
        }
    
    @router.get("/supply-requests/outgoing")
    async def get_outgoing_supply_requests(
        status: Optional[str] = None,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get supply requests sent by this pharmacy"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"requesting_pharmacy_id": pharmacy_id}
        if status:
            query["status"] = status
        
        requests = await db["pharmacy_supply_requests"].find(
            query, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {"requests": requests, "total": len(requests)}
    
    @router.get("/supply-requests/incoming")
    async def get_incoming_supply_requests(
        status: Optional[str] = None,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get supply requests received by this pharmacy"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"target_pharmacy_id": pharmacy_id}
        if status:
            query["status"] = status
        else:
            query["status"] = {"$in": ["pending", "accepted", "partially_accepted"]}
        
        requests = await db["pharmacy_supply_requests"].find(
            query, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {"requests": requests, "total": len(requests)}
    
    @router.put("/supply-requests/{request_id}/respond")
    async def respond_to_supply_request(
        request_id: str,
        response: str = Body(...),  # accepted, partially_accepted, rejected
        response_notes: Optional[str] = Body(None),
        available_items: Optional[List[Dict[str, Any]]] = Body(None),  # [{drug_name, available_quantity}]
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.INVENTORY_MANAGER
        ))
    ):
        """Respond to an incoming supply request"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        if response not in ["accepted", "partially_accepted", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid response")
        
        supply_request = await db["pharmacy_supply_requests"].find_one({
            "id": request_id,
            "target_pharmacy_id": pharmacy_id
        })
        
        if not supply_request:
            raise HTTPException(status_code=404, detail="Supply request not found")
        
        if supply_request.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Request already responded to")
        
        update_data = {
            "status": response,
            "response": response,
            "response_notes": response_notes,
            "responded_at": now,
            "responded_by": user["id"],
            "responded_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "updated_at": now
        }
        
        if available_items:
            update_data["available_items"] = available_items
        
        await db["pharmacy_supply_requests"].update_one(
            {"id": request_id},
            {"$set": update_data}
        )
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": f"supply_request_{response}",
            "entity_type": "supply_request",
            "entity_id": request_id,
            "details": {
                "requesting_pharmacy": supply_request.get("requesting_pharmacy_name"),
                "response": response
            },
            "performed_by": user["id"],
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "timestamp": now
        })
        
        return {"message": f"Request {response}", "status": response}
    
    @router.put("/supply-requests/{request_id}/fulfill")
    async def fulfill_supply_request(
        request_id: str,
        delivery_method: str = Body("pickup"),  # pickup, delivery
        delivery_notes: Optional[str] = Body(None),
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST,
            PharmacyStaffRole.INVENTORY_MANAGER,
            PharmacyStaffRole.DELIVERY_STAFF
        ))
    ):
        """Mark a supply request as fulfilled"""
        pharmacy_id = user.get("pharmacy_id")
        now = datetime.now(timezone.utc).isoformat()
        
        supply_request = await db["pharmacy_supply_requests"].find_one({
            "id": request_id,
            "target_pharmacy_id": pharmacy_id
        })
        
        if not supply_request:
            raise HTTPException(status_code=404, detail="Supply request not found")
        
        if supply_request.get("status") not in ["accepted", "partially_accepted"]:
            raise HTTPException(status_code=400, detail="Request must be accepted first")
        
        await db["pharmacy_supply_requests"].update_one(
            {"id": request_id},
            {"$set": {
                "status": "fulfilled",
                "fulfilled_at": now,
                "fulfilled_by": user["id"],
                "delivery_method": delivery_method,
                "delivery_notes": delivery_notes,
                "updated_at": now
            }}
        )
        
        # Audit log
        await db["pharmacy_audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "pharmacy_id": pharmacy_id,
            "action": "supply_request_fulfilled",
            "entity_type": "supply_request",
            "entity_id": request_id,
            "details": {
                "requesting_pharmacy": supply_request.get("requesting_pharmacy_name"),
                "delivery_method": delivery_method
            },
            "performed_by": user["id"],
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "timestamp": now
        })
        
        return {"message": "Supply request fulfilled", "status": "fulfilled"}
    
    # ============== AUDIT LOG VIEWING ==============
    
    @router.get("/audit-logs")
    async def get_audit_logs(
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Get audit logs for the pharmacy"""
        pharmacy_id = user.get("pharmacy_id")
        
        query = {"pharmacy_id": pharmacy_id}
        
        if action:
            query["action"] = action
        if entity_type:
            query["entity_type"] = entity_type
        if start_date:
            query["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_date
            else:
                query["timestamp"] = {"$lte": end_date}
        
        logs = await db["pharmacy_audit_logs"].find(
            query, {"_id": 0}
        ).sort("timestamp", -1).to_list(limit)
        
        return {"logs": logs, "total": len(logs)}
    
    @router.get("/audit-logs/summary")
    async def get_audit_logs_summary(
        days: int = 7,
        user: dict = Depends(require_roles(
            PharmacyStaffRole.PHARMACY_IT_ADMIN,
            PharmacyStaffRole.PHARMACY_OWNER,
            PharmacyStaffRole.SUPERINTENDENT_PHARMACIST
        ))
    ):
        """Get summary of audit activities"""
        pharmacy_id = user.get("pharmacy_id")
        
        from datetime import timedelta
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Count by action type
        pipeline = [
            {"$match": {"pharmacy_id": pharmacy_id, "timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        action_counts = await db["pharmacy_audit_logs"].aggregate(pipeline).to_list(50)
        
        # Count by entity type
        entity_pipeline = [
            {"$match": {"pharmacy_id": pharmacy_id, "timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        entity_counts = await db["pharmacy_audit_logs"].aggregate(entity_pipeline).to_list(20)
        
        # Count by user
        user_pipeline = [
            {"$match": {"pharmacy_id": pharmacy_id, "timestamp": {"$gte": start_date}}},
            {"$group": {"_id": "$performed_by_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        user_counts = await db["pharmacy_audit_logs"].aggregate(user_pipeline).to_list(10)
        
        total_logs = await db["pharmacy_audit_logs"].count_documents({
            "pharmacy_id": pharmacy_id,
            "timestamp": {"$gte": start_date}
        })
        
        return {
            "period_days": days,
            "total_activities": total_logs,
            "by_action": [{"action": a["_id"], "count": a["count"]} for a in action_counts],
            "by_entity": [{"entity": e["_id"], "count": e["count"]} for e in entity_counts],
            "by_user": [{"user": u["_id"], "count": u["count"]} for u in user_counts]
        }
    
    # ============== HOSPITAL PHARMACY NETWORK DIRECTORY ==============
    
    @router.get("/network/pharmacies")
    async def get_pharmacy_network(
        region: Optional[str] = None,
        has_nhis: Optional[bool] = None,
        is_24hr: Optional[bool] = None,
        query: Optional[str] = None,
        user: dict = Depends(get_current_pharmacy_user)
    ):
        """Get list of pharmacies in the network for supply requests"""
        pharmacy_id = user.get("pharmacy_id")
        
        filter_query = {"status": "approved"}
        
        # Exclude own pharmacy
        filter_query["id"] = {"$ne": pharmacy_id}
        
        if region:
            filter_query["region"] = region
        if has_nhis:
            filter_query["has_nhis_accreditation"] = True
        if is_24hr:
            filter_query["has_24hr_service"] = True
        if query:
            filter_query["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"town": {"$regex": query, "$options": "i"}},
                {"district": {"$regex": query, "$options": "i"}}
            ]
        
        pharmacies = await db["pharmacies"].find(
            filter_query,
            {"_id": 0, "password": 0, "user_id": 0}
        ).to_list(100)
        
        return {"pharmacies": pharmacies, "total": len(pharmacies)}
    
    return router
