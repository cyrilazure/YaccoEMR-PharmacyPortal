from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import hashlib
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Yacco Health API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

# Ghana Regions
GHANA_REGIONS = [
    {"id": "greater-accra", "name": "Greater Accra", "capital": "Accra"},
    {"id": "ashanti", "name": "Ashanti", "capital": "Kumasi"},
    {"id": "central", "name": "Central", "capital": "Cape Coast"},
    {"id": "eastern", "name": "Eastern", "capital": "Koforidua"},
    {"id": "western", "name": "Western", "capital": "Sekondi-Takoradi"},
    {"id": "western-north", "name": "Western North", "capital": "Sefwi Wiawso"},
    {"id": "volta", "name": "Volta", "capital": "Ho"},
    {"id": "oti", "name": "Oti", "capital": "Dambai"},
    {"id": "northern", "name": "Northern", "capital": "Tamale"},
    {"id": "savannah", "name": "Savannah", "capital": "Damongo"},
    {"id": "north-east", "name": "North East", "capital": "Nalerigu"},
    {"id": "upper-east", "name": "Upper East", "capital": "Bolgatanga"},
    {"id": "upper-west", "name": "Upper West", "capital": "Wa"},
    {"id": "bono", "name": "Bono", "capital": "Sunyani"},
    {"id": "bono-east", "name": "Bono East", "capital": "Techiman"},
    {"id": "ahafo", "name": "Ahafo", "capital": "Goaso"},
]

FACILITY_TYPES = ["teaching_hospital", "regional_hospital", "district_hospital", "clinic", "chps_compound", "pharmacy"]
USER_ROLES = ["it_admin", "facility_admin", "physician", "nurse", "pharmacist", "dispenser", "scheduler"]

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str
    facility_id: Optional[str] = None
    region_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    facility_id: Optional[str] = None
    region_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FacilityBase(BaseModel):
    name: str
    facility_type: str
    region_id: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool = True
    nhis_registered: bool = False

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    facility_type: Optional[str] = None
    region_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    nhis_registered: Optional[bool] = None

class Facility(FacilityBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict

class StatsResponse(BaseModel):
    total_users: int
    total_facilities: int
    total_pharmacies: int
    active_users: int
    regions_covered: int

# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def generate_token() -> str:
    return secrets.token_urlsafe(32)

# Simple in-memory token store (for demo - use Redis in production)
active_tokens = {}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    if token not in active_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = active_tokens[token]
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

async def require_it_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "it_admin":
        raise HTTPException(status_code=403, detail="IT Admin access required")
    return user

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Yacco Health API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Auth Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = await db.users.find_one({"email": request.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    token = generate_token()
    active_tokens[token] = user["id"]
    
    # Remove password hash from response
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    
    return LoginResponse(token=token, user=user_response)

@api_router.post("/auth/logout")
async def logout(user: dict = Depends(get_current_user)):
    # Find and remove the token
    token_to_remove = None
    for token, user_id in active_tokens.items():
        if user_id == user["id"]:
            token_to_remove = token
            break
    if token_to_remove:
        del active_tokens[token_to_remove]
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

# Region Routes
@api_router.get("/regions")
async def get_regions():
    return GHANA_REGIONS

# User Routes (IT Admin only)
@api_router.get("/users", response_model=List[dict])
async def get_users(
    role: Optional[str] = None,
    region_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(require_it_admin)
):
    query = {}
    if role:
        query["role"] = role
    if region_id:
        query["region_id"] = region_id
    if is_active is not None:
        query["is_active"] = is_active
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.get("/users/{user_id}")
async def get_user(user_id: str, admin: dict = Depends(require_it_admin)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.post("/users", response_model=dict)
async def create_user(user_data: UserCreate, admin: dict = Depends(require_it_admin)):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role
    if user_data.role not in USER_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {USER_ROLES}")
    
    # Create user
    user = User(**user_data.model_dump(exclude={"password"}))
    user_dict = user.model_dump()
    user_dict["password_hash"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Return without password hash
    del user_dict["password_hash"]
    return user_dict

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, update_data: UserUpdate, admin: dict = Depends(require_it_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"id": user_id}, {"$set": update_dict})
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return updated_user

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_it_admin)):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# Facility Routes
@api_router.get("/facilities", response_model=List[dict])
async def get_facilities(
    facility_type: Optional[str] = None,
    region_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(require_it_admin)
):
    query = {}
    if facility_type:
        query["facility_type"] = facility_type
    if region_id:
        query["region_id"] = region_id
    if is_active is not None:
        query["is_active"] = is_active
    
    facilities = await db.facilities.find(query, {"_id": 0}).to_list(1000)
    return facilities

@api_router.get("/facilities/{facility_id}")
async def get_facility(facility_id: str, admin: dict = Depends(require_it_admin)):
    facility = await db.facilities.find_one({"id": facility_id}, {"_id": 0})
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@api_router.post("/facilities", response_model=dict)
async def create_facility(facility_data: FacilityCreate, admin: dict = Depends(require_it_admin)):
    # Validate facility type
    if facility_data.facility_type not in FACILITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid facility type. Must be one of: {FACILITY_TYPES}")
    
    # Validate region
    valid_regions = [r["id"] for r in GHANA_REGIONS]
    if facility_data.region_id not in valid_regions:
        raise HTTPException(status_code=400, detail="Invalid region")
    
    facility = Facility(**facility_data.model_dump())
    facility_dict = facility.model_dump()
    
    await db.facilities.insert_one(facility_dict)
    return facility_dict

@api_router.put("/facilities/{facility_id}")
async def update_facility(facility_id: str, update_data: FacilityUpdate, admin: dict = Depends(require_it_admin)):
    facility = await db.facilities.find_one({"id": facility_id})
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.facilities.update_one({"id": facility_id}, {"$set": update_dict})
    
    updated_facility = await db.facilities.find_one({"id": facility_id}, {"_id": 0})
    return updated_facility

@api_router.delete("/facilities/{facility_id}")
async def delete_facility(facility_id: str, admin: dict = Depends(require_it_admin)):
    result = await db.facilities.delete_one({"id": facility_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Facility not found")
    return {"message": "Facility deleted successfully"}

# Stats Route
@api_router.get("/stats", response_model=StatsResponse)
async def get_stats(admin: dict = Depends(require_it_admin)):
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    total_facilities = await db.facilities.count_documents({})
    total_pharmacies = await db.facilities.count_documents({"facility_type": "pharmacy"})
    
    # Count unique regions with facilities
    pipeline = [
        {"$group": {"_id": "$region_id"}},
        {"$count": "count"}
    ]
    regions_result = await db.facilities.aggregate(pipeline).to_list(1)
    regions_covered = regions_result[0]["count"] if regions_result else 0
    
    return StatsResponse(
        total_users=total_users,
        total_facilities=total_facilities,
        total_pharmacies=total_pharmacies,
        active_users=active_users,
        regions_covered=regions_covered
    )

# Seed Data Route (for initial setup)
@api_router.post("/seed")
async def seed_data():
    # Check if already seeded
    admin_exists = await db.users.find_one({"email": "admin@yacco.health"})
    if admin_exists:
        return {"message": "Data already seeded"}
    
    # Create IT Admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": "admin@yacco.health",
        "name": "System Administrator",
        "role": "it_admin",
        "phone": "+233301234567",
        "is_active": True,
        "password_hash": hash_password("admin123"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_user)
    
    # Create sample facilities
    sample_facilities = [
        {
            "id": str(uuid.uuid4()),
            "name": "Korle Bu Teaching Hospital",
            "facility_type": "teaching_hospital",
            "region_id": "greater-accra",
            "address": "Guggisberg Avenue, Accra",
            "phone": "+233302665401",
            "email": "info@kbth.gov.gh",
            "is_active": True,
            "nhis_registered": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Komfo Anokye Teaching Hospital",
            "facility_type": "teaching_hospital",
            "region_id": "ashanti",
            "address": "Okomfo Anokye Road, Kumasi",
            "phone": "+233322022301",
            "email": "info@kath.gov.gh",
            "is_active": True,
            "nhis_registered": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Cape Coast Teaching Hospital",
            "facility_type": "teaching_hospital",
            "region_id": "central",
            "address": "Cape Coast",
            "phone": "+233332132701",
            "email": "info@ccth.gov.gh",
            "is_active": True,
            "nhis_registered": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Yacco Pharmacy - Accra Central",
            "facility_type": "pharmacy",
            "region_id": "greater-accra",
            "address": "Oxford Street, Osu, Accra",
            "phone": "+233244123456",
            "email": "accra@yaccopharm.com",
            "is_active": True,
            "nhis_registered": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Yacco Pharmacy - Kumasi",
            "facility_type": "pharmacy",
            "region_id": "ashanti",
            "address": "Adum, Kumasi",
            "phone": "+233244789012",
            "email": "kumasi@yaccopharm.com",
            "is_active": True,
            "nhis_registered": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.facilities.insert_many(sample_facilities)
    
    # Create sample users
    sample_users = [
        {
            "id": str(uuid.uuid4()),
            "email": "dr.mensah@kbth.gov.gh",
            "name": "Dr. Kwame Mensah",
            "role": "physician",
            "region_id": "greater-accra",
            "phone": "+233244111222",
            "is_active": True,
            "password_hash": hash_password("doctor123"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "nurse.ama@kath.gov.gh",
            "name": "Ama Serwaa",
            "role": "nurse",
            "region_id": "ashanti",
            "phone": "+233244333444",
            "is_active": True,
            "password_hash": hash_password("nurse123"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "pharm.kofi@yaccopharm.com",
            "name": "Kofi Asante",
            "role": "pharmacist",
            "region_id": "greater-accra",
            "phone": "+233244555666",
            "is_active": True,
            "password_hash": hash_password("pharm123"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.users.insert_many(sample_users)
    
    return {"message": "Seed data created successfully", "admin_email": "admin@yacco.health", "admin_password": "admin123"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
