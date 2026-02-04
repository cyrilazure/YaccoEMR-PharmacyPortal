"""
Region-Based Hospital Discovery Module for Yacco EMR (Ghana)
Supports:
- Ghana's 16 administrative regions
- Hospital discovery by region
- Multi-location hospitals
- Location-aware authentication
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
    ADMIN = "admin"  # Hospital admin
    BILLER = "biller"
    SCHEDULER = "scheduler"
    SUPER_ADMIN = "super_admin"  # Platform admin

# Role to portal mapping
ROLE_PORTAL_MAP = {
    "physician": "/physician-portal",
    "nurse": "/nurse-portal",
    "admin": "/admin-dashboard",
    "hospital_admin": "/admin-dashboard",
    "biller": "/billing",
    "scheduler": "/schedule",
    "super_admin": "/super-admin"
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
    """Hospital model with region assignment"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    region_id: str
    organization_type: str = "hospital"
    # Address
    address: str
    city: str
    phone: str
    email: EmailStr
    website: Optional[str] = None
    # Registration
    license_number: str
    ghana_health_service_id: Optional[str] = None  # GHS registration
    # Features
    has_multiple_locations: bool = False
    locations: List[HospitalLocation] = []
    # Status
    status: str = "pending"
    is_active: bool = True
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    # Stats
    total_users: int = 0
    total_patients: int = 0

class HospitalCreateGhana(BaseModel):
    """Create hospital with region"""
    name: str
    region_id: str
    address: str
    city: str
    phone: str
    email: EmailStr
    website: Optional[str] = None
    license_number: str
    ghana_health_service_id: Optional[str] = None
    # Admin contact
    admin_first_name: str
    admin_last_name: str
    admin_email: EmailStr
    admin_phone: str

class LocationLoginRequest(BaseModel):
    """Login with hospital/location context"""
    email: EmailStr
    password: str
    hospital_id: str
    location_id: Optional[str] = None  # Required if hospital has multiple locations
    totp_code: Optional[str] = None  # For 2FA

class LocationLoginResponse(BaseModel):
    token: str
    user: dict
    hospital: dict
    location: Optional[dict] = None
    redirect_to: str  # Role-based portal redirect

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
    
    # JWT Configuration
    JWT_SECRET = "yacco-emr-secret-key-2024"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def create_location_token(user: dict, hospital: dict, location: dict = None) -> str:
        """Create JWT token with region/hospital/location context"""
        payload = {
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "region_id": hospital.get("region_id"),
            "hospital_id": hospital["id"],
            "hospital_name": hospital["name"],
            "location_id": location["id"] if location else None,
            "location_name": location["name"] if location else None,
            "organization_id": hospital["id"],  # For backward compatibility
            "permissions": user.get("permissions", []),
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.now(timezone.utc),
            "iss": "yacco-emr-ghana"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # ============ Public Discovery Endpoints ============
    
    @region_router.get("/", response_model=dict)
    async def list_regions():
        """
        List all Ghana regions (PUBLIC - no auth required)
        Used for the region selection dropdown on landing page
        """
        # Get regions from database or use default
        db_regions = await db["regions"].find({"is_active": True}, {"_id": 0}).to_list(100)
        
        if not db_regions:
            # Seed default Ghana regions if not exist
            for region in GHANA_REGIONS:
                region_doc = {
                    **region,
                    "is_active": True,
                    "hospital_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db["regions"].update_one(
                    {"id": region["id"]},
                    {"$setOnInsert": region_doc},
                    upsert=True
                )
            db_regions = GHANA_REGIONS
        
        # Get hospital counts per region
        regions_with_counts = []
        for region in db_regions:
            count = await db["hospitals"].count_documents({
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
        region = await db["regions"].find_one({"id": region_id}, {"_id": 0})
        if not region:
            # Check if it's a default region
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
        """
        List all active hospitals in a region (PUBLIC)
        Used after user selects a region
        """
        # Validate region exists
        region = next((r for r in GHANA_REGIONS if r["id"] == region_id), None)
        if not region:
            db_region = await db["regions"].find_one({"id": region_id})
            if not db_region:
                raise HTTPException(status_code=404, detail="Region not found")
            region = db_region
        
        # Build query
        query = {
            "region_id": region_id,
            "status": "active"
        }
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"city": {"$regex": search, "$options": "i"}}
            ]
        
        if city:
            query["city"] = {"$regex": city, "$options": "i"}
        
        hospitals = await db["hospitals"].find(
            query,
            {"_id": 0, "admin_password": 0}
        ).sort("name", 1).to_list(200)
        
        # For each hospital, indicate if it has multiple locations
        for hospital in hospitals:
            location_count = await db["hospital_locations"].count_documents({
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
        hospital = await db["hospitals"].find_one(
            {"id": hospital_id},
            {"_id": 0, "admin_password": 0}
        )
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Get locations
        locations = await db["hospital_locations"].find(
            {"hospital_id": hospital_id, "is_active": True},
            {"_id": 0}
        ).sort("name", 1).to_list(50)
        
        hospital["locations"] = locations
        hospital["location_count"] = len(locations)
        hospital["has_multiple_locations"] = len(locations) > 1
        
        return hospital
    
    @region_router.get("/hospitals/{hospital_id}/locations", response_model=dict)
    async def list_hospital_locations(hospital_id: str):
        """
        List all locations for a hospital (PUBLIC)
        Used when hospital has multiple locations
        """
        hospital = await db["hospitals"].find_one(
            {"id": hospital_id},
            {"_id": 0, "name": 1, "id": 1}
        )
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        locations = await db["hospital_locations"].find(
            {"hospital_id": hospital_id, "is_active": True},
            {"_id": 0}
        ).sort("name", 1).to_list(50)
        
        return {
            "hospital": hospital,
            "locations": locations,
            "total": len(locations)
        }
    
    # ============ Location-Aware Authentication ============
    
    @region_router.post("/auth/login", response_model=dict)
    async def location_login(request: LocationLoginRequest):
        """
        Authenticate user with hospital/location context
        Returns JWT with region, hospital, location, and role
        Includes redirect URL based on role
        """
        # Get hospital
        hospital = await db["hospitals"].find_one(
            {"id": request.hospital_id},
            {"_id": 0}
        )
        
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        if hospital.get("status") != "active":
            raise HTTPException(
                status_code=403,
                detail="Hospital is not active. Please contact support."
            )
        
        # Check if hospital has multiple locations
        location = None
        location_count = await db["hospital_locations"].count_documents({
            "hospital_id": request.hospital_id,
            "is_active": True
        })
        
        if location_count > 1:
            # Location selection required
            if not request.location_id:
                raise HTTPException(
                    status_code=400,
                    detail="This hospital has multiple locations. Please select a location."
                )
            
            location = await db["hospital_locations"].find_one(
                {"id": request.location_id, "hospital_id": request.hospital_id},
                {"_id": 0}
            )
            
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")
        elif location_count == 1:
            # Single location - auto-select
            location = await db["hospital_locations"].find_one(
                {"hospital_id": request.hospital_id, "is_active": True},
                {"_id": 0}
            )
        
        # Find user
        user = await db["users"].find_one({
            "email": request.email,
            "organization_id": request.hospital_id
        }, {"_id": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(request.password, user.get("password", "")):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=403,
                detail="Your account is inactive. Please contact your administrator."
            )
        
        # Check location assignment (if user has specific location)
        if location and user.get("location_id"):
            if user["location_id"] != location["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="You are not authorized to access this location."
                )
        
        # Handle 2FA if enabled
        user_2fa = await db["user_2fa"].find_one({"user_id": user["id"]})
        if user_2fa and user_2fa.get("enabled"):
            if not request.totp_code:
                raise HTTPException(
                    status_code=403,
                    detail="2FA_REQUIRED",
                    headers={"X-2FA-Required": "true"}
                )
            
            # Verify 2FA code
            from twofa_module import verify_totp
            if not verify_totp(user_2fa["secret"], request.totp_code):
                raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
        # Create token
        token = create_location_token(user, hospital, location)
        
        # Determine redirect based on role
        role = user.get("role", "physician")
        redirect_to = ROLE_PORTAL_MAP.get(role, "/dashboard")
        
        # Log login
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
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
        
        # Prepare response
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
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        # Check if region exists
        existing = await db["regions"].find_one({"id": region_data.id})
        if existing:
            raise HTTPException(status_code=400, detail="Region already exists")
        
        region = {
            **region_data.model_dump(),
            "is_active": True,
            "hospital_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user["id"]
        }
        
        await db["regions"].insert_one(region)
        if "_id" in region:
            del region["_id"]
        
        return {"message": "Region created", "region": region}
    
    @region_router.put("/admin/regions/{region_id}", response_model=dict)
    async def update_region(
        region_id: str,
        updates: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update a region (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await db["regions"].update_one(
            {"id": region_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Region not found")
        
        return {"message": "Region updated"}
    
    @region_router.delete("/admin/regions/{region_id}", response_model=dict)
    async def delete_region(
        region_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate a region (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        # Check if region has hospitals
        hospital_count = await db["hospitals"].count_documents({"region_id": region_id})
        if hospital_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete region with {hospital_count} hospitals. Reassign hospitals first."
            )
        
        await db["regions"].update_one(
            {"id": region_id},
            {"$set": {"is_active": False, "deactivated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": "Region deactivated"}
    
    # ============ Super Admin - Hospital Management ============
    
    @region_router.post("/admin/hospitals", response_model=dict)
    async def create_hospital(
        hospital_data: HospitalCreateGhana,
        user: dict = Depends(get_current_user)
    ):
        """Create a new hospital under a region (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        # Validate region
        region = next((r for r in GHANA_REGIONS if r["id"] == hospital_data.region_id), None)
        if not region:
            db_region = await db["regions"].find_one({"id": hospital_data.region_id})
            if not db_region:
                raise HTTPException(status_code=404, detail="Region not found")
        
        hospital_id = str(uuid.uuid4())
        
        # Create hospital
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
            "status": "active",  # Direct creation by super admin
            "is_active": True,
            "has_multiple_locations": False,
            "total_users": 1,  # Admin user
            "total_patients": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"]
        }
        
        # Create default main location
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
        
        # Create admin user
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
        
        # Insert all
        await db["hospitals"].insert_one(hospital)
        await db["hospital_locations"].insert_one(main_location)
        await db["users"].insert_one(admin_user)
        
        # Update region hospital count
        await db["regions"].update_one(
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
            }
        }
    
    @region_router.put("/admin/hospitals/{hospital_id}/region", response_model=dict)
    async def assign_hospital_to_region(
        hospital_id: str,
        region_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Reassign a hospital to a different region (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        # Get hospital
        hospital = await db["hospitals"].find_one({"id": hospital_id})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        old_region_id = hospital.get("region_id")
        
        # Update hospital
        await db["hospitals"].update_one(
            {"id": hospital_id},
            {"$set": {
                "region_id": region_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update region counts
        if old_region_id:
            await db["regions"].update_one(
                {"id": old_region_id},
                {"$inc": {"hospital_count": -1}}
            )
        
        await db["regions"].update_one(
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
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        query = {}
        if region_id:
            query["region_id"] = region_id
        if status:
            query["status"] = status
        
        hospitals = await db["hospitals"].find(
            query,
            {"_id": 0, "admin_password": 0}
        ).sort([("region_id", 1), ("name", 1)]).to_list(500)
        
        # Group by region
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
    
    # ============ Hospital Admin - Location Management ============
    
    @region_router.post("/hospitals/{hospital_id}/locations", response_model=dict)
    async def add_hospital_location(
        hospital_id: str,
        location_data: AddLocationRequest,
        user: dict = Depends(get_current_user)
    ):
        """Add a new location/branch to a hospital (Hospital Admin)"""
        # Check permissions
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Verify hospital access
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        # Get hospital
        hospital = await db["hospitals"].find_one({"id": hospital_id})
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
        
        await db["hospital_locations"].insert_one(location)
        
        # Update hospital has_multiple_locations flag
        location_count = await db["hospital_locations"].count_documents({
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        await db["hospitals"].update_one(
            {"id": hospital_id},
            {"$set": {
                "has_multiple_locations": location_count > 1,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if "_id" in location:
            del location["_id"]
        
        return {"message": "Location added", "location": location}
    
    @region_router.put("/hospitals/{hospital_id}/locations/{location_id}", response_model=dict)
    async def update_hospital_location(
        hospital_id: str,
        location_id: str,
        updates: dict,
        user: dict = Depends(get_current_user)
    ):
        """Update a hospital location (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db["hospital_locations"].update_one(
            {"id": location_id, "hospital_id": hospital_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return {"message": "Location updated"}
    
    @region_router.delete("/hospitals/{hospital_id}/locations/{location_id}", response_model=dict)
    async def deactivate_hospital_location(
        hospital_id: str,
        location_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Deactivate a hospital location (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        # Check if it's the last active location
        active_count = await db["hospital_locations"].count_documents({
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        if active_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the last location. Hospital must have at least one active location."
            )
        
        await db["hospital_locations"].update_one(
            {"id": location_id, "hospital_id": hospital_id},
            {"$set": {
                "is_active": False,
                "deactivated_at": datetime.now(timezone.utc).isoformat(),
                "deactivated_by": user["id"]
            }}
        )
        
        # Update has_multiple_locations
        new_count = await db["hospital_locations"].count_documents({
            "hospital_id": hospital_id,
            "is_active": True
        })
        
        await db["hospitals"].update_one(
            {"id": hospital_id},
            {"$set": {"has_multiple_locations": new_count > 1}}
        )
        
        return {"message": "Location deactivated"}
    
    # ============ Hospital Admin - Staff Management ============
    
    @region_router.post("/hospitals/{hospital_id}/staff", response_model=dict)
    async def create_staff_with_location(
        hospital_id: str,
        staff_data: dict,
        user: dict = Depends(get_current_user)
    ):
        """Create staff user with location assignment (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        
        # Check email uniqueness
        existing = await db["users"].find_one({"email": staff_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate location if provided
        location_id = staff_data.get("location_id")
        if location_id:
            location = await db["hospital_locations"].find_one({
                "id": location_id,
                "hospital_id": hospital_id
            })
            if not location:
                raise HTTPException(status_code=404, detail="Location not found")
        
        # Generate temp password
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
        
        await db["users"].insert_one(staff_user)
        
        # Update counts
        await db["hospitals"].update_one(
            {"id": hospital_id},
            {"$inc": {"total_users": 1}}
        )
        
        if location_id:
            await db["hospital_locations"].update_one(
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
        if user.get("role") not in ["hospital_admin", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get staff user
        staff = await db["users"].find_one({"id": user_id})
        if not staff:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify hospital access
        hospital_id = staff.get("organization_id")
        if user.get("role") != "super_admin" and user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this user")
        
        # Validate location
        location = await db["hospital_locations"].find_one({
            "id": location_id,
            "hospital_id": hospital_id
        })
        if not location:
            raise HTTPException(status_code=404, detail="Location not found in this hospital")
        
        # Update old location count
        old_location_id = staff.get("location_id")
        if old_location_id and old_location_id != location_id:
            await db["hospital_locations"].update_one(
                {"id": old_location_id},
                {"$inc": {"user_count": -1}}
            )
        
        # Update staff
        await db["users"].update_one(
            {"id": user_id},
            {"$set": {
                "location_id": location_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update new location count
        if old_location_id != location_id:
            await db["hospital_locations"].update_one(
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
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        # Count by region
        region_stats = []
        for region in GHANA_REGIONS:
            hospital_count = await db["hospitals"].count_documents({
                "region_id": region["id"],
                "status": "active"
            })
            user_count = await db["users"].aggregate([
                {"$lookup": {
                    "from": "hospitals",
                    "localField": "organization_id",
                    "foreignField": "id",
                    "as": "hospital"
                }},
                {"$unwind": {"path": "$hospital", "preserveNullAndEmptyArrays": True}},
                {"$match": {"hospital.region_id": region["id"]}},
                {"$count": "total"}
            ]).to_list(1)
            
            region_stats.append({
                **region,
                "hospital_count": hospital_count,
                "user_count": user_count[0]["total"] if user_count else 0
            })
        
        # Overall stats
        total_hospitals = await db["hospitals"].count_documents({"status": "active"})
        total_users = await db["users"].count_documents({"is_active": True})
        total_locations = await db["hospital_locations"].count_documents({"is_active": True})
        pending_hospitals = await db["hospitals"].count_documents({"status": "pending"})
        
        # Role distribution
        role_dist = await db["users"].aggregate([
            {"$match": {"is_active": True}},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]).to_list(20)
        
        return {
            "regions": region_stats,
            "totals": {
                "hospitals": total_hospitals,
                "users": total_users,
                "locations": total_locations,
                "pending_hospitals": pending_hospitals
            },
            "role_distribution": {r["_id"]: r["count"] for r in role_dist},
            "country": "Ghana",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return region_router


# Export router
__all__ = ["region_router", "create_region_endpoints", "GHANA_REGIONS", "ROLE_PORTAL_MAP"]
