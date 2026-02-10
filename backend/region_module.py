"""
Region-Based Hospital Discovery Module for Yacco EMR (Ghana)
REFACTORED to use db_service_v2 for database abstraction.

Supports:
- Ghana's 16 administrative regions
- Hospital discovery by region
- Multi-location hospitals
- Location-aware authentication with OTP
- Role-based redirection
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import secrets
import bcrypt
import jwt

# Import OTP module
from otp_module import create_otp_session, verify_otp, mask_phone_number
from db_service_v2 import get_db_service

region_router = APIRouter(prefix="/api/regions", tags=["Regions & Discovery"])

# ============ Ghana Regions ============

GHANA_REGIONS = [
    {"id": "greater-accra", "name": "Greater Accra Region", "capital": "Accra", "code": "GA"},
    {"id": "ashanti", "name": "Ashanti Region", "capital": "Kumasi", "code": "AS"},
    {"id": "eastern", "name": "Eastern Region", "capital": "Koforidua", "code": "ER"},
    {"id": "western", "name": "Western Region", "capital": "Sekondi-Takoradi", "code": "WR"},
    {"id": "central", "name": "Central Region", "capital": "Cape Coast", "code": "CR"},
    {"id": "northern", "name": "Northern Region", "capital": "Tamale", "code": "NR"},
    {"id": "volta", "name": "Volta Region", "capital": "Ho", "code": "VR"},
    {"id": "upper-east", "name": "Upper East Region", "capital": "Bolgatanga", "code": "UE"},
    {"id": "upper-west", "name": "Upper West Region", "capital": "Wa", "code": "UW"},
    {"id": "bono", "name": "Bono Region", "capital": "Sunyani", "code": "BO"},
    {"id": "bono-east", "name": "Bono East Region", "capital": "Techiman", "code": "BE"},
    {"id": "ahafo", "name": "Ahafo Region", "capital": "Goaso", "code": "AH"},
    {"id": "western-north", "name": "Western North Region", "capital": "Sefwi Wiawso", "code": "WN"},
    {"id": "oti", "name": "Oti Region", "capital": "Dambai", "code": "OT"},
    {"id": "north-east", "name": "North East Region", "capital": "Nalerigu", "code": "NE"},
    {"id": "savannah", "name": "Savannah Region", "capital": "Damongo", "code": "SV"},
]

# ============ Default Hospital Departments ============

DEFAULT_HOSPITAL_DEPARTMENTS = [
    {"name": "Emergency Department", "code": "ED", "department_type": "clinical", "description": "24/7 emergency and trauma care"},
    {"name": "Intensive Care Unit (ICU)", "code": "ICU", "department_type": "clinical", "description": "Critical care for severely ill patients"},
    {"name": "Medical ICU (MICU)", "code": "MICU", "department_type": "clinical", "description": "Medical intensive care unit"},
    {"name": "Coronary Care Unit (CCU)", "code": "CCU", "department_type": "clinical", "description": "Cardiac intensive care"},
    {"name": "Neonatal ICU (NICU)", "code": "NICU", "department_type": "clinical", "description": "Intensive care for newborns"},
    {"name": "Pediatric ICU (PICU)", "code": "PICU", "department_type": "clinical", "description": "Intensive care for children"},
    {"name": "Surgical ICU (SICU)", "code": "SICU", "department_type": "clinical", "description": "Post-surgical intensive care"},
    {"name": "Inpatient Ward", "code": "INP", "department_type": "clinical", "description": "General inpatient care"},
    {"name": "Outpatient Department (OPD)", "code": "OPD", "department_type": "clinical", "description": "Outpatient consultations and follow-ups"},
    {"name": "Surgery Department", "code": "SURG", "department_type": "clinical", "description": "Surgical procedures and operations"},
    {"name": "Obstetrics & Gynecology", "code": "OBGYN", "department_type": "clinical", "description": "Women's health and maternity care"},
    {"name": "Pediatrics", "code": "PED", "department_type": "clinical", "description": "Children's healthcare"},
    {"name": "Internal Medicine", "code": "IM", "department_type": "clinical", "description": "Adult internal medicine"},
    {"name": "Cardiology", "code": "CARD", "department_type": "clinical", "description": "Heart and cardiovascular care"},
    {"name": "Neurology", "code": "NEURO", "department_type": "clinical", "description": "Brain and nervous system care"},
    {"name": "Orthopedics", "code": "ORTHO", "department_type": "clinical", "description": "Bone and joint care"},
    {"name": "Radiology", "code": "RAD", "department_type": "diagnostic", "description": "Medical imaging services"},
    {"name": "Laboratory", "code": "LAB", "department_type": "diagnostic", "description": "Clinical laboratory services"},
    {"name": "Pharmacy", "code": "PHARM", "department_type": "support", "description": "Medication dispensing and management"},
    {"name": "Physiotherapy", "code": "PT", "department_type": "clinical", "description": "Physical rehabilitation services"},
    {"name": "Dental", "code": "DENT", "department_type": "clinical", "description": "Dental care services"},
    {"name": "Ophthalmology", "code": "OPH", "department_type": "clinical", "description": "Eye care services"},
    {"name": "ENT (Ear, Nose, Throat)", "code": "ENT", "department_type": "clinical", "description": "Ear, nose, and throat care"},
    {"name": "Psychiatry", "code": "PSY", "department_type": "clinical", "description": "Mental health services"},
    {"name": "Administration", "code": "ADMIN", "department_type": "administrative", "description": "Hospital administration"},
    {"name": "Medical Records", "code": "MR", "department_type": "administrative", "description": "Patient records management"},
    {"name": "Billing & Finance", "code": "FIN", "department_type": "administrative", "description": "Financial services and billing"},
]


async def seed_hospital_departments(hospital_id: str) -> int:
    """Auto-seed default departments for a new hospital"""
    db_svc = get_db_service()
    departments_created = 0
    
    for dept in DEFAULT_HOSPITAL_DEPARTMENTS:
        dept_doc = {
            "id": str(uuid.uuid4()),
            "organization_id": hospital_id,
            "name": dept["name"],
            "code": dept["code"],
            "department_type": dept["department_type"],
            "description": dept["description"],
            "is_active": True,
            "staff_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db_svc.insert("departments", dept_doc, generate_id=False)
        departments_created += 1
    
    return departments_created


# ============ Enums ============

class LocationType(str, Enum):
    MAIN_HOSPITAL = "main_hospital"
    BRANCH = "branch"
    CLINIC = "clinic"
    SATELLITE = "satellite"
    EMERGENCY_CENTER = "emergency_center"

class UserRoleGhana(str, Enum):
    PHYSICIAN = "physician"
    NURSE = "nurse"
    ADMIN = "admin"
    BILLER = "biller"
    SCHEDULER = "scheduler"
    SUPER_ADMIN = "super_admin"

# Role to portal mapping
ROLE_PORTAL_MAP = {
    "physician": "/dashboard",
    "nurse": "/nurse-station",
    "nursing_supervisor": "/nursing-supervisor",
    "floor_supervisor": "/nursing-supervisor",
    "admin": "/admin-dashboard",
    "hospital_admin": "/admin-dashboard",
    "hospital_it_admin": "/it-admin",
    "facility_admin": "/facility-admin",
    "biller": "/billing",
    "scheduler": "/scheduling",
    "pharmacist": "/pharmacy",
    "pharmacy_tech": "/pharmacy",
    "radiologist": "/radiology",
    "radiology_staff": "/radiology",
    "bed_manager": "/bed-management",
    "records_officer": "/records",
    "super_admin": "/platform/super-admin"
}

# ============ Models ============

class RegionCreate(BaseModel):
    id: str
    name: str
    capital: str
    code: str

class Region(RegionCreate):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    hospital_count: int = 0

class HospitalLocationCreate(BaseModel):
    name: str
    location_type: LocationType = LocationType.BRANCH
    address: str
    city: str
    phone: str
    email: Optional[EmailStr] = None
    operating_hours: Optional[str] = "8:00 AM - 6:00 PM"
    services: List[str] = []
    is_24_hour: bool = False
    has_emergency: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class HospitalLocation(HospitalLocationCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hospital_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_count: int = 0

class HospitalWithRegion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    region_id: str
    organization_type: str = "hospital"
    address: str
    city: str
    phone: str
    email: EmailStr
    website: Optional[str] = None
    license_number: str
    ghana_health_service_id: Optional[str] = None
    has_multiple_locations: bool = False
    locations: List[HospitalLocation] = []
    status: str = "pending"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    total_users: int = 0
    total_patients: int = 0

class HospitalCreateGhana(BaseModel):
    name: str
    region_id: str
    address: str
    city: str
    phone: str
    email: EmailStr
    website: Optional[str] = None
    license_number: str
    ghana_health_service_id: Optional[str] = None
    admin_first_name: str
    admin_last_name: str
    admin_email: EmailStr
    admin_phone: str

class LocationLoginRequest(BaseModel):
    email: EmailStr
    password: str
    hospital_id: str
    location_id: Optional[str] = None
    totp_code: Optional[str] = None

class LocationLoginInitRequest(BaseModel):
    email: EmailStr
    password: str
    hospital_id: str
    location_id: Optional[str] = None

class LocationLoginPhoneRequest(BaseModel):
    user_id: str
    phone_number: str
    hospital_id: str
    location_id: Optional[str] = None

class LocationLoginVerifyRequest(BaseModel):
    otp_session_id: str
    otp_code: str

class LocationLoginResponse(BaseModel):
    token: str
    user: dict
    hospital: dict
    location: Optional[dict] = None
    redirect_to: str

class AddLocationRequest(BaseModel):
    name: str
    location_type: LocationType = LocationType.BRANCH
    address: str
    city: str
    phone: str
    email: Optional[EmailStr] = None
    operating_hours: Optional[str] = "8:00 AM - 6:00 PM"
    services: List[str] = []
    is_24_hour: bool = False
    has_emergency: bool = False

# ============ API Factory ============

def create_region_endpoints(db, get_current_user, hash_password):
    """Create region API endpoints with database dependency"""
    
    import os
    JWT_SECRET = os.environ.get('JWT_SECRET', 'yacco-emr-secret-key-2024')
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def create_location_token(user: dict, hospital: dict, location: dict = None) -> str:
        payload = {
            "user_id": user["id"],
            "role": user["role"],
            "region_id": hospital.get("region_id"),
            "hospital_id": hospital["id"],
            "location_id": location["id"] if location else None,
            "organization_id": hospital["id"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # ============ Public Discovery Endpoints ============
    
    @region_router.get("/", response_model=dict)
    async def list_regions():
        """List all Ghana regions (PUBLIC - no auth required)"""
        db_svc = get_db_service()
        
        db_regions = await db_svc.find("regions", {"is_active": True}, limit=100)
        
        if not db_regions:
            for region in GHANA_REGIONS:
                region_doc = {
                    **region,
                    "is_active": True,
                    "hospital_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db_svc.collection("regions").update_one(
                    {"id": region["id"]},
                    {"$setOnInsert": region_doc},
                    upsert=True
                )
            db_regions = GHANA_REGIONS
        
        regions_with_counts = []
        for region in db_regions:
            count = await db_svc.count("hospitals", {
                "region_id": region["id"],
                "status": "active"
            })
            region_data = dict(region)
            region_data["hospital_count"] = count
            regions_with_counts.append(region_data)
        
        return {
            "regions": regions_with_counts,
            "total": len(regions_with_counts),
            "country": "Ghana"
        }
    
    @region_router.get("/{region_id}", response_model=dict)
    async def get_region(region_id: str):
        """Get region details (PUBLIC)"""
        db_svc = get_db_service()
        
        region = await db_svc.find_one("regions", {"id": region_id})
        if not region:
            default = next((r for r in GHANA_REGIONS if r["id"] == region_id), None)
            if default:
                return default
            raise HTTPException(status_code=404, detail="Region not found")
        return region
    
    @region_router.get("/{region_id}/hospitals", response_model=dict)
    async def list_hospitals_by_region(
        region_id: str,
        search: Optional[str] = None,
        city: Optional[str] = None
    ):
        """List all active hospitals in a region (PUBLIC)"""
        db_svc = get_db_service()
        
        region = next((r for r in GHANA_REGIONS if r["id"] == region_id), None)
        if not region:
            db_region = await db_svc.find_one("regions", {"id": region_id})
            if not db_region:
                raise HTTPException(status_code=404, detail="Region not found")
            region = db_region
        
        query = {"region_id": region_id, "status": "active"}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"city": {"$regex": search, "$options": "i"}}
            ]
        
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        
        hospitals = await db_svc.find(
            "hospitals", query,
            projection={"admin_password": 0},
            sort=[("name", 1)],
            limit=200
        )
        
        for hospital in hospitals:
            location_count = await db_svc.count("hospital_locations", {
                "hospital_id": hospital["id"],
                "is_active": True
            })
            hospital["location_count"] = location_count
            hospital["has_multiple_locations"] = location_count > 1
        
        return {
            "region": region,
            "hospitals": hospitals,
            "total": len(hospitals)
        }
    
    @region_router.get("/hospitals/{hospital_id}", response_model=dict)
    async def get_hospital_details(hospital_id: str):
        """Get hospital details including locations (PUBLIC)"""
        db_svc = get_db_service()
        
        hospital = await db_svc.find_one(
            "hospitals", {"id": hospital_id},
            projection={"admin_password": 0}
        )
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        locations = await db_svc.find(
            "hospital_locations",
            {"hospital_id": hospital_id, "is_active": True},
            sort=[("name", 1)],
            limit=50
        )
        
        hospital["locations"] = locations
        hospital["location_count"] = len(locations)
        hospital["has_multiple_locations"] = len(locations) > 1
        
        return hospital
    
    @region_router.get("/hospitals/{hospital_id}/locations", response_model=dict)
    async def list_hospital_locations(hospital_id: str):
        """List all locations for a hospital (PUBLIC)"""
        db_svc = get_db_service()
        
        hospital = await db_svc.find_one(
            "hospitals", {"id": hospital_id},
            projection={"name": 1, "id": 1}
        )
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        locations = await db_svc.find(
            "hospital_locations",
            {"hospital_id": hospital_id, "is_active": True},
            sort=[("name", 1)],
            limit=50
        )
        
        return {
            "hospital": hospital,
            "locations": locations,
            "total": len(locations)
        }
    
    # ============ Location-Aware Authentication with OTP ============
    
    # OTP Configuration
    OTP_ENABLED = os.environ.get('OTP_ENABLED', 'true').lower() == 'true'
    
    @region_router.post("/auth/login/init", response_model=dict)
    async def location_login_init(request: LocationLoginInitRequest):
        """Initialize OTP login flow with hospital/location context"""
        db_svc = get_db_service()
        
        hospital = await db_svc.find_one("hospitals", {"id": request.hospital_id})
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        if hospital.get("status") != "active":
            raise HTTPException(status_code=403, detail="Hospital is not active. Please contact support.")
        
        location = None
        location_count = await db_svc.count("hospital_locations", {
            "hospital_id": request.hospital_id,
            "is_active": True
        })
        
        if location_count > 1 and request.location_id:
            location = await db_svc.find_one("hospital_locations", {
                "id": request.location_id,
                "hospital_id": request.hospital_id
            })
        elif location_count == 1:
            location = await db_svc.find_one("hospital_locations", {
                "hospital_id": request.hospital_id,
                "is_active": True
            })
        
        user = await db_svc.find_one("users", {
            "email": request.email,
            "organization_id": request.hospital_id
        })
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        stored_password = user.get("password_hash") or user.get("password", "")
        if not stored_password or not verify_password(request.password, stored_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Your account is inactive. Please contact your administrator.")
        
        # If OTP is disabled, return token directly
        if not OTP_ENABLED:
            token = create_location_token(user, hospital, location)
            role = user.get("role", "physician")
            redirect_to = ROLE_PORTAL_MAP.get(role, "/dashboard")
            
            user_response = {
                "id": user["id"],
                "email": user["email"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": user.get("role"),
                "department": user.get("department"),
                "specialty": user.get("specialty"),
                "organization_id": user.get("organization_id") or hospital["id"],
                "is_active": user.get("is_active", True)
            }
            
            hospital_response = {
                "id": hospital["id"],
                "name": hospital["name"],
                "region_id": hospital.get("region_id"),
                "city": hospital.get("city")
            }
            
            location_response = None
            if location:
                location_response = {
                    "id": location["id"],
                    "name": location["name"],
                    "type": location.get("type"),
                    "address": location.get("address")
                }
            
            return {
                "otp_required": False,
                "token": token,
                "user": user_response,
                "hospital": hospital_response,
                "location": location_response,
                "redirect_to": redirect_to
            }
        
        phone = user.get("phone")
        if not phone or phone.strip() == "":
            return {
                "otp_required": True,
                "phone_required": True,
                "user_id": user["id"],
                "hospital_id": request.hospital_id,
                "location_id": request.location_id,
                "message": "Please enter your phone number to receive OTP"
            }
        
        user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "User"
        otp_session = await create_otp_session(db, user["id"], phone, "emr", user_name)
        
        return {
            "otp_required": True,
            "phone_required": False,
            "otp_session_id": otp_session["session_id"],
            "phone_masked": otp_session.get("phone_masked", mask_phone_number(phone)),
            "hospital_id": request.hospital_id,
            "location_id": request.location_id,
            "expires_at": otp_session["expires_at"],
            "sms_sent": otp_session.get("sms_sent", True),
            "message": "OTP sent to your registered phone number"
        }
    
    @region_router.post("/auth/login/submit-phone", response_model=dict)
    async def location_login_submit_phone(request: LocationLoginPhoneRequest):
        """Step 2: Submit phone number and send OTP"""
        db_svc = get_db_service()
        
        user = await db_svc.get_by_id("users", request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db_svc.update_by_id("users", request.user_id, {"phone": request.phone_number})
        
        user = await db_svc.get_by_id("users", request.user_id)
        user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() if user else "User"
        otp_session = await create_otp_session(db, request.user_id, request.phone_number, "emr", user_name)
        
        return {
            "otp_session_id": otp_session["session_id"],
            "phone_masked": otp_session.get("phone_masked", mask_phone_number(request.phone_number)),
            "hospital_id": request.hospital_id,
            "location_id": request.location_id,
            "expires_at": otp_session["expires_at"],
            "sms_sent": otp_session.get("sms_sent", True),
            "message": "OTP sent to your phone number"
        }
    
    @region_router.post("/auth/login/verify", response_model=dict)
    async def location_login_verify(request: LocationLoginVerifyRequest):
        """Step 3: Verify OTP and complete login"""
        db_svc = get_db_service()
        
        otp_result = await verify_otp(db, request.otp_session_id, request.otp_code)
        if not otp_result.get("success"):
            raise HTTPException(status_code=401, detail=otp_result.get("error", "Invalid OTP"))
        
        user = await db_svc.get_by_id("users", otp_result["user_id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        hospital = await db_svc.find_one("hospitals", {"id": user.get("organization_id")})
        
        location = None
        if user.get("location_id"):
            location = await db_svc.get_by_id("hospital_locations", user["location_id"])
        elif hospital:
            location_count = await db_svc.count("hospital_locations", {
                "hospital_id": hospital["id"],
                "is_active": True
            })
            if location_count == 1:
                location = await db_svc.find_one("hospital_locations", {
                    "hospital_id": hospital["id"],
                    "is_active": True
                })
        
        token = create_location_token(user, hospital, location)
        
        role = user.get("role", "physician")
        redirect_to = ROLE_PORTAL_MAP.get(role, "/dashboard")
        
        user_response = {
            "id": user["id"],
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": user.get("role"),
            "department": user.get("department"),
            "specialty": user.get("specialty"),
            "is_active": user.get("is_active", True)
        }
        
        hospital_response = None
        if hospital:
            hospital_response = {
                "id": hospital["id"],
                "name": hospital["name"],
                "region_id": hospital.get("region_id"),
                "city": hospital.get("city")
            }
        
        location_response = None
        if location:
            location_response = {
                "id": location["id"],
                "name": location["name"],
                "type": location.get("type"),
                "address": location.get("address")
            }
        
        return {
            "token": token,
            "user": user_response,
            "hospital": hospital_response,
            "location": location_response,
            "redirect_to": redirect_to
        }
    
    # ============ Legacy Location-Aware Authentication (without OTP) ============
    
    @region_router.post("/auth/login", response_model=dict)
    async def location_login(request: LocationLoginRequest):
        """Authenticate user with hospital/location context"""
        db_svc = get_db_service()
        
        hospital = await db_svc.find_one("hospitals", {"id": request.hospital_id})
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        if hospital.get("status") != "active":
            raise HTTPException(status_code=403, detail="Hospital is not active. Please contact support.")
        
        location = None
        location_count = await db_svc.count("hospital_locations", {
            "hospital_id": request.hospital_id,
            "is_active": True
        })
        
        if location_count > 1:
            if not request.location_id:
                raise HTTPException(status_code=400, detail="This hospital has multiple locations. Please select a location.")
            
            location = await db_svc.find_one("hospital_locations", {
                "id": request.location_id,
                "hospital_id": request.hospital_id
            })
            
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")
        elif location_count == 1:
            location = await db_svc.find_one("hospital_locations", {
                "hospital_id": request.hospital_id,
                "is_active": True
            })
        
        user = await db_svc.find_one("users", {
            "email": request.email,
            "organization_id": request.hospital_id
        })
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        stored_password = user.get("password_hash") or user.get("password", "")
        if not stored_password or not verify_password(request.password, stored_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Your account is inactive. Please contact your administrator.")
        
        if location and user.get("location_id"):
            if user["location_id"] != location["id"]:
                raise HTTPException(status_code=403, detail="You are not authorized to access this location.")
        
        user_2fa = await db_svc.find_one("user_2fa", {"user_id": user["id"]})
        if user_2fa and user_2fa.get("enabled"):
            if not request.totp_code:
                raise HTTPException(status_code=403, detail="2FA_REQUIRED", headers={"X-2FA-Required": "true"})
            
            from twofa_module import verify_totp
            if not verify_totp(user_2fa["secret"], request.totp_code):
                raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
        token = create_location_token(user, hospital, location)
        
        role = user.get("role", "physician")
        redirect_to = ROLE_PORTAL_MAP.get(role, "/dashboard")
        
        await db_svc.insert("audit_logs", {
            "action": "login",
            "user_id": user["id"],
            "user_email": user["email"],
            "resource_type": "authentication",
            "resource_id": user["id"],
            "hospital_id": hospital["id"],
            "location_id": location["id"] if location else None,
            "region_id": hospital.get("region_id"),
            "ip_address": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "method": "location_login",
                "hospital_name": hospital["name"],
                "location_name": location["name"] if location else None
            }
        })
        
        user_response = {
            "id": user["id"],
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": user.get("role"),
            "department": user.get("department"),
            "specialty": user.get("specialty"),
            "is_active": user.get("is_active", True)
        }
        
        hospital_response = {
            "id": hospital["id"],
            "name": hospital["name"],
            "region_id": hospital.get("region_id"),
            "city": hospital.get("city")
        }
        
        return {
            "token": token,
            "user": user_response,
            "hospital": hospital_response,
            "location": location,
            "redirect_to": redirect_to,
            "message": f"Welcome to {hospital['name']}"
        }
    
    @region_router.get("/auth/redirect-url", response_model=dict)
    async def get_redirect_url(user: dict = Depends(get_current_user)):
        """Get the appropriate portal redirect URL based on user role"""
        role = user.get("role", "physician")
        redirect_to = ROLE_PORTAL_MAP.get(role, "/dashboard")
        
        return {
            "role": role,
            "redirect_to": redirect_to,
            "portals": ROLE_PORTAL_MAP
        }
    
    # ============ Super Admin - Region Management ============
    
    @region_router.post("/admin/regions", response_model=dict)
    async def create_region(
        region_data: RegionCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new region (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        existing = await db_svc.find_one("regions", {"id": region_data.id})
        if existing:
            raise HTTPException(status_code=400, detail="Region already exists")
        
        region = {
            **region_data.model_dump(),
            "is_active": True,
            "hospital_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        
        await db_svc.insert("regions", region, generate_id=False)
        
        return {"message": "Region created", "region": region}
    
    @region_router.put("/admin/regions/{region_id}", response_model=dict)
    async def update_region(
        region_id: str,
        updates: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update a region (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await db_svc.update("regions", {"id": region_id}, updates)
        
        if not result:
            raise HTTPException(status_code=404, detail="Region not found")
        
        return {"message": "Region updated"}
    
    @region_router.delete("/admin/regions/{region_id}", response_model=dict)
    async def delete_region(
        region_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate a region (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital_count = await db_svc.count("hospitals", {"region_id": region_id})
        if hospital_count > 0:
            raise HTTPException(status_code=400, detail=f"Cannot delete region with {hospital_count} hospitals. Reassign hospitals first.")
        
        await db_svc.update("regions", {"id": region_id}, {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Region deactivated"}
    
    # ============ Super Admin - Hospital Management ============
    
    @region_router.post("/admin/hospitals", response_model=dict)
    async def create_hospital(
        hospital_data: HospitalCreateGhana,
        user: dict = Depends(get_current_user)
    ):
        """Create a new hospital under a region (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        region = next((r for r in GHANA_REGIONS if r["id"] == hospital_data.region_id), None)
        if not region:
            db_region = await db_svc.find_one("regions", {"id": hospital_data.region_id})
            if not db_region:
                raise HTTPException(status_code=404, detail="Region not found")
        
        hospital_id = str(uuid.uuid4())
        
        hospital = {
            "id": hospital_id,
            "name": hospital_data.name,
            "region_id": hospital_data.region_id,
            "organization_type": "hospital",
            "address": hospital_data.address,
            "city": hospital_data.city,
            "phone": hospital_data.phone,
            "email": hospital_data.email,
            "website": hospital_data.website,
            "license_number": hospital_data.license_number,
            "ghana_health_service_id": hospital_data.ghana_health_service_id,
            "status": "active",
            "is_active": True,
            "has_multiple_locations": False,
            "total_users": 1,
            "total_patients": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"]
        }
        
        main_location = {
            "id": str(uuid.uuid4()),
            "hospital_id": hospital_id,
            "name": f"{hospital_data.name} - Main",
            "location_type": "main_hospital",
            "address": hospital_data.address,
            "city": hospital_data.city,
            "phone": hospital_data.phone,
            "email": hospital_data.email,
            "is_active": True,
            "is_24_hour": False,
            "has_emergency": False,
            "services": [],
            "operating_hours": "8:00 AM - 6:00 PM",
            "user_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        admin_id = str(uuid.uuid4())
        temp_password = secrets.token_urlsafe(12)
        admin_user = {
            "id": admin_id,
            "email": hospital_data.admin_email,
            "first_name": hospital_data.admin_first_name,
            "last_name": hospital_data.admin_last_name,
            "role": "hospital_admin",
            "department": "Administration",
            "organization_id": hospital_id,
            "location_id": main_location["id"],
            "password": hash_password(temp_password),
            "is_active": True,
            "is_temp_password": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db_svc.insert("hospitals", hospital, generate_id=False)
        await db_svc.insert("hospital_locations", main_location, generate_id=False)
        await db_svc.insert("users", admin_user, generate_id=False)
        
        departments_created = await seed_hospital_departments(hospital_id)
        
        await db_svc.collection("regions").update_one(
            {"id": hospital_data.region_id},
            {"$inc": {"hospital_count": 1}}
        )
        
        return {
            "message": "Hospital created successfully",
            "hospital": {
                "id": hospital_id,
                "name": hospital_data.name,
                "region_id": hospital_data.region_id
            },
            "location": {
                "id": main_location["id"],
                "name": main_location["name"]
            },
            "admin": {
                "id": admin_id,
                "email": hospital_data.admin_email,
                "temp_password": temp_password,
                "note": "Please change password on first login"
            },
            "departments": {
                "count": departments_created,
                "message": f"{departments_created} default departments created automatically"
            }
        }
    
    @region_router.put("/admin/hospitals/{hospital_id}/region", response_model=dict)
    async def assign_hospital_to_region(
        hospital_id: str,
        region_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Reassign a hospital to a different region (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        old_region_id = hospital.get("region_id")
        
        await db_svc.update_by_id("hospitals", hospital_id, {
            "region_id": region_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        if old_region_id:
            await db_svc.collection("regions").update_one(
                {"id": old_region_id},
                {"$inc": {"hospital_count": -1}}
            )
        
        await db_svc.collection("regions").update_one(
            {"id": region_id},
            {"$inc": {"hospital_count": 1}}
        )
        
        return {"message": f"Hospital reassigned to region {region_id}"}
    
    @region_router.get("/admin/hospitals/all", response_model=dict)
    async def list_all_hospitals(
        region_id: Optional[str] = None,
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """List all hospitals across all regions (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        query = {}
        if region_id:
            query["region_id"] = region_id
        if status:
            query["status"] = status
        
        hospitals = await db_svc.find(
            "hospitals", query,
            projection={"admin_password": 0},
            sort=[("region_id", 1), ("name", 1)],
            limit=500
        )
        
        by_region = {}
        for hospital in hospitals:
            rid = hospital.get("region_id", "unassigned")
            if rid not in by_region:
                by_region[rid] = []
            by_region[rid].append(hospital)
        
        return {
            "hospitals": hospitals,
            "total": len(hospitals),
            "by_region": by_region
        }
    
    @region_router.post("/admin/hospitals/{hospital_id}/staff", response_model=dict)
    async def create_hospital_staff_as_super_admin(
        hospital_id: str,
        staff_data: dict,
        user: dict = Depends(get_current_user)
    ):
        """Create a staff account for any hospital (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        existing = await db_svc.find_one("users", {"email": staff_data.get("email")})
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        temp_password = secrets.token_urlsafe(12)
        
        staff_id = str(uuid.uuid4())
        staff_user = {
            "id": staff_id,
            "email": staff_data.get("email"),
            "password": hash_password(temp_password),
            "first_name": staff_data.get("first_name"),
            "last_name": staff_data.get("last_name"),
            "phone": staff_data.get("phone"),
            "role": staff_data.get("role", "physician"),
            "organization_id": hospital_id,
            "hospital_id": hospital_id,
            "region_id": hospital.get("region_id"),
            "department_id": staff_data.get("department_id"),
            "employee_id": staff_data.get("employee_id"),
            "is_active": True,
            "email_verified": False,
            "mfa_enabled": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"],
            "created_by_super_admin": True
        }
        
        await db_svc.insert("users", staff_user, generate_id=False)
        
        await db_svc.collection("hospitals").update_one(
            {"id": hospital_id},
            {"$inc": {"user_count": 1}}
        )
        
        await db_svc.insert("audit_logs", {
            "event_type": "staff_created_by_super_admin",
            "user_id": user["id"],
            "target_user_id": staff_id,
            "hospital_id": hospital_id,
            "details": {
                "staff_email": staff_data.get("email"),
                "staff_role": staff_data.get("role"),
                "staff_name": f"{staff_data.get('first_name')} {staff_data.get('last_name')}"
            },
            "ip_address": "system",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": "Staff account created successfully",
            "user": {
                "id": staff_id,
                "email": staff_user["email"],
                "first_name": staff_user["first_name"],
                "last_name": staff_user["last_name"],
                "role": staff_user["role"]
            },
            "hospital": {
                "id": hospital_id,
                "name": hospital.get("name")
            },
            "temp_password": temp_password,
            "note": "User should change password on first login"
        }
    
    @region_router.post("/admin/hospitals/{hospital_id}/seed-departments", response_model=dict)
    async def seed_departments_for_hospital(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Seed default departments for an existing hospital (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        existing_count = await db_svc.count("departments", {"organization_id": hospital_id})
        if existing_count > 0:
            return {
                "message": f"Hospital already has {existing_count} departments",
                "existing_count": existing_count,
                "skipped": True
            }
        
        departments_created = await seed_hospital_departments(hospital_id)
        
        return {
            "message": f"Successfully created {departments_created} default departments",
            "hospital_id": hospital_id,
            "hospital_name": hospital.get("name"),
            "departments_created": departments_created
        }
    
    @region_router.delete("/admin/hospitals/{hospital_id}", response_model=dict)
    async def delete_hospital(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Delete (soft-delete/deactivate) a hospital (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        user_count = await db_svc.count("users", {"organization_id": hospital_id})
        patient_count = await db_svc.count("patients", {"organization_id": hospital_id})
        
        await db_svc.update_by_id("hospitals", hospital_id, {
            "status": "deleted",
            "is_active": False,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by": user["id"]
        })
        
        await db_svc.update_many("users", {"organization_id": hospital_id}, {
            "is_active": False,
            "deactivated_reason": "hospital_deleted"
        })
        
        await db_svc.insert("audit_logs", {
            "event_type": "hospital_deleted",
            "user_id": user["id"],
            "hospital_id": hospital_id,
            "details": {
                "hospital_name": hospital.get("name"),
                "region_id": hospital.get("region_id"),
                "user_count": user_count,
                "patient_count": patient_count,
                "action": "soft_delete"
            },
            "ip_address": "system",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": f"Hospital '{hospital.get('name')}' has been deactivated",
            "hospital_id": hospital_id,
            "affected_users": user_count,
            "affected_patients": patient_count,
            "note": "This is a soft delete. Data is preserved but inaccessible."
        }
    
    @region_router.put("/admin/hospitals/{hospital_id}/status", response_model=dict)
    async def update_hospital_status(
        hospital_id: str,
        status_data: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update hospital status (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        new_status = status_data.get("status", "active")
        valid_statuses = ["active", "suspended", "inactive", "pending"]
        
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        is_active = new_status == "active"
        await db_svc.update_by_id("hospitals", hospital_id, {
            "status": new_status,
            "is_active": is_active,
            "status_updated_at": datetime.now(timezone.utc).isoformat(),
            "status_updated_by": user["id"]
        })
        
        if not is_active:
            await db_svc.update_many("users", {"organization_id": hospital_id}, {
                "login_disabled": True,
                "login_disabled_reason": f"hospital_{new_status}"
            })
        else:
            await db_svc.collection("users").update_many(
                {"organization_id": hospital_id, "login_disabled_reason": {"$regex": "^hospital_"}},
                {"$set": {"login_disabled": False}, "$unset": {"login_disabled_reason": ""}}
            )
        
        await db_svc.insert("audit_logs", {
            "event_type": "hospital_status_changed",
            "user_id": user["id"],
            "hospital_id": hospital_id,
            "details": {
                "hospital_name": hospital.get("name"),
                "old_status": hospital.get("status", "unknown"),
                "new_status": new_status
            },
            "ip_address": "system",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": f"Hospital status changed to '{new_status}'",
            "hospital_id": hospital_id,
            "status": new_status,
            "is_active": is_active
        }
    
    # ============ Hospital Admin - Location Management ============
    
    @region_router.post("/hospitals/{hospital_id}/locations", response_model=dict)
    async def add_hospital_location(
        hospital_id: str,
        location_data: AddLocationRequest,
        user: dict = Depends(get_current_user)
    ):
        """Add a new location/branch to a hospital (Hospital Admin)"""
        db_svc = get_db_service()
        
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        location = {
            "id": str(uuid.uuid4()),
            "hospital_id": hospital_id,
            **location_data.model_dump(),
            "is_active": True,
            "user_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        
        await db_svc.insert("hospital_locations", location, generate_id=False)
        
        location_count = await db_svc.count("hospital_locations", {
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        await db_svc.update_by_id("hospitals", hospital_id, {
            "has_multiple_locations": location_count > 1,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Location added", "location": location}
    
    @region_router.put("/hospitals/{hospital_id}/locations/{location_id}", response_model=dict)
    async def update_hospital_location(
        hospital_id: str,
        location_id: str,
        updates: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update a hospital location (Hospital Admin)"""
        db_svc = get_db_service()
        
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db_svc.update("hospital_locations", {"id": location_id, "hospital_id": hospital_id}, updates)
        
        if not result:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {"message": "Location updated"}
    
    @region_router.delete("/hospitals/{hospital_id}/locations/{location_id}", response_model=dict)
    async def deactivate_hospital_location(
        hospital_id: str,
        location_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate a hospital location (Hospital Admin)"""
        db_svc = get_db_service()
        
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        active_count = await db_svc.count("hospital_locations", {
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        if active_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot deactivate the last location. Hospital must have at least one active location.")
        
        await db_svc.update("hospital_locations", {"id": location_id, "hospital_id": hospital_id}, {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
            "deactivated_by": user["id"]
        })
        
        new_count = await db_svc.count("hospital_locations", {
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        await db_svc.update_by_id("hospitals", hospital_id, {"has_multiple_locations": new_count > 1})
        
        return {"message": "Location deactivated"}
    
    # ============ Hospital Admin - Staff Management ============
    
    @region_router.post("/hospitals/{hospital_id}/staff", response_model=dict)
    async def create_staff_with_location(
        hospital_id: str,
        staff_data: dict,
        user: dict = Depends(get_current_user)
    ):
        """Create staff user with location assignment (Hospital Admin)"""
        db_svc = get_db_service()
        
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        existing = await db_svc.find_one("users", {"email": staff_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        location_id = staff_data.get("location_id")
        if location_id:
            location = await db_svc.find_one("hospital_locations", {
                "id": location_id,
                "hospital_id": hospital_id
            })
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")
        
        temp_password = secrets.token_urlsafe(12)
        
        staff_user = {
            "id": str(uuid.uuid4()),
            "email": staff_data["email"],
            "first_name": staff_data["first_name"],
            "last_name": staff_data["last_name"],
            "role": staff_data.get("role", "physician"),
            "department": staff_data.get("department"),
            "specialty": staff_data.get("specialty"),
            "organization_id": hospital_id,
            "location_id": location_id,
            "password": hash_password(temp_password),
            "is_active": True,
            "is_temp_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        
        await db_svc.insert("users", staff_user, generate_id=False)
        
        await db_svc.collection("hospitals").update_one(
            {"id": hospital_id},
            {"$inc": {"total_users": 1}}
        )
        
        if location_id:
            await db_svc.collection("hospital_locations").update_one(
                {"id": location_id},
                {"$inc": {"user_count": 1}}
            )
        
        return {
            "message": "Staff user created",
            "user": {
                "id": staff_user["id"],
                "email": staff_user["email"],
                "name": f"{staff_user['first_name']} {staff_user['last_name']}",
                "role": staff_user["role"],
                "location_id": location_id
            },
            "temp_password": temp_password,
            "note": "Please share temp password securely. User must change on first login."
        }
    
    @region_router.put("/staff/{user_id}/location", response_model=dict)
    async def assign_staff_to_location(
        user_id: str,
        location_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Assign or reassign staff to a location (Hospital Admin)"""
        db_svc = get_db_service()
        
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        staff = await db_svc.get_by_id("users", user_id)
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        hospital_id = staff.get("organization_id")
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this user")
        
        location = await db_svc.find_one("hospital_locations", {
            "id": location_id,
            "hospital_id": hospital_id
        })
        if not location:
            raise HTTPException(status_code=404, detail="Location not found in this hospital")
        
        old_location_id = staff.get("location_id")
        if old_location_id and old_location_id != location_id:
            await db_svc.collection("hospital_locations").update_one(
                {"id": old_location_id},
                {"$inc": {"user_count": -1}}
            )
        
        await db_svc.update_by_id("users", user_id, {
            "location_id": location_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        if old_location_id != location_id:
            await db_svc.collection("hospital_locations").update_one(
                {"id": location_id},
                {"$inc": {"user_count": 1}}
            )
        
        return {
            "message": f"Staff assigned to location: {location['name']}",
            "user_id": user_id,
            "location_id": location_id
        }
    
    # ============ Statistics & Overview ============
    
    @region_router.get("/admin/overview", response_model=dict)
    async def get_platform_overview(user: dict = Depends(get_current_user)):
        """Get platform-wide overview (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        region_stats = []
        for region in GHANA_REGIONS:
            hospital_count = await db_svc.count("hospitals", {
                "region_id": region["id"],
                "status": "active"
            })
            # Use direct MongoDB for aggregation
            user_count_cursor = db_svc.collection("users").aggregate([
                {"$lookup": {
                    "from": "hospitals",
                    "localField": "organization_id",
                    "foreignField": "id",
                    "as": "hospital"
                }},
                {"$unwind": {"path": "$hospital", "preserveNullAndEmptyArrays": True}},
                {"$match": {"hospital.region_id": region["id"]}},
                {"$count": "total"}
            ])
            user_count_result = await user_count_cursor.to_list(1)
            
            region_stats.append({
                **region,
                "hospital_count": hospital_count,
                "user_count": user_count_result[0]["total"] if user_count_result else 0
            })
        
        total_hospitals = await db_svc.count("hospitals", {"status": "active"})
        total_users = await db_svc.count("users", {"is_active": True})
        total_locations = await db_svc.count("hospital_locations", {"is_active": True})
        pending_hospitals = await db_svc.count("hospitals", {"status": "pending"})
        
        # Use direct MongoDB for aggregation that needs _id in grouping
        role_dist_cursor = db_svc.collection("users").aggregate([
            {"$match": {"is_active": True}},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ])
        role_dist = await role_dist_cursor.to_list(50)
        
        return {
            "regions": region_stats,
            "totals": {
                "hospitals": total_hospitals,
                "users": total_users,
                "locations": total_locations,
                "pending_hospitals": pending_hospitals
            },
            "role_distribution": {r["_id"]: r["count"] for r in role_dist if r.get("_id")},
            "country": "Ghana",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ Super Admin - Impersonation ============
    
    @region_router.post("/admin/login-as-hospital/{hospital_id}", response_model=dict)
    async def login_as_hospital(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Super Admin can login as any hospital admin"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital = await db_svc.get_by_id("hospitals", hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        admin_user = await db_svc.find_one("users", {
            "organization_id": hospital_id,
            "role": "hospital_admin"
        })
        
        if not admin_user:
            raise HTTPException(status_code=404, detail="Hospital admin not found")
        
        main_location = await db_svc.find_one("hospital_locations", {
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        payload = {
            "user_id": admin_user["id"],
            "role": "hospital_admin",
            "region_id": hospital.get("region_id"),
            "hospital_id": hospital_id,
            "location_id": main_location["id"] if main_location else None,
            "organization_id": hospital_id,
            "impersonated_by": user["id"],
            "impersonated_by_email": user.get("email"),
            "is_impersonation": True,
            "exp": datetime.now(timezone.utc) + timedelta(hours=4)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        await db_svc.insert("audit_logs", {
            "action": "impersonate_hospital",
            "user_id": user["id"],
            "user_email": user.get("email"),
            "resource_type": "hospital",
            "resource_id": hospital_id,
            "details": {
                "hospital_name": hospital["name"],
                "impersonated_user": admin_user["email"],
                "reason": "Super Admin access"
            },
            "severity": "high",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "token": token,
            "message": f"Now logged in as {hospital['name']} admin",
            "hospital": {
                "id": hospital_id,
                "name": hospital["name"],
                "region_id": hospital.get("region_id"),
                "city": hospital.get("city")
            },
            "user": {
                "id": admin_user["id"],
                "email": admin_user["email"],
                "first_name": admin_user.get("first_name", ""),
                "last_name": admin_user.get("last_name", ""),
                "role": "hospital_admin"
            },
            "location": main_location,
            "impersonation": {
                "is_impersonation": True,
                "super_admin_id": user["id"],
                "super_admin_email": user.get("email"),
                "expires_in_hours": 4
            },
            "redirect_to": "/admin-dashboard"
        }
    
    @region_router.get("/admin/hospital-admins", response_model=dict)
    async def list_hospital_admins(
        region_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """List all hospitals with their admin credentials (Super Admin only)"""
        db_svc = get_db_service()
        
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        hospital_query = {"status": "active"}
        if region_id:
            hospital_query["region_id"] = region_id
        
        hospitals = await db_svc.find("hospitals", hospital_query, limit=200)
        
        result = []
        for hospital in hospitals:
            admin = await db_svc.find_one("users", {
                "organization_id": hospital["id"],
                "role": "hospital_admin"
            }, projection={"password": 0})
            
            location_count = await db_svc.count("hospital_locations", {
                "hospital_id": hospital["id"],
                "is_active": True
            })
            
            user_count = await db_svc.count("users", {
                "organization_id": hospital["id"],
                "is_active": True
            })
            
            result.append({
                "hospital": {
                    "id": hospital["id"],
                    "name": hospital["name"],
                    "region_id": hospital.get("region_id"),
                    "city": hospital.get("city"),
                    "status": hospital.get("status"),
                    "location_count": location_count,
                    "user_count": user_count
                },
                "admin": {
                    "id": admin["id"] if admin else None,
                    "email": admin["email"] if admin else None,
                    "name": f"{admin.get('first_name', '')} {admin.get('last_name', '')}" if admin else None
                } if admin else None
            })
        
        return {
            "hospitals": result,
            "total": len(result)
        }
    
    return region_router


# Export router
__all__ = ["region_router", "create_region_endpoints", "GHANA_REGIONS", "ROLE_PORTAL_MAP"]
