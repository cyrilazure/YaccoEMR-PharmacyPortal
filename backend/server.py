from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
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
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'yacco-emr-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="Yacco EMR API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ ENUMS ============
class UserRole(str, Enum):
    PHYSICIAN = "physician"
    NURSE = "nurse"
    SCHEDULER = "scheduler"
    ADMIN = "admin"

class OrderType(str, Enum):
    LAB = "lab"
    IMAGING = "imaging"
    MEDICATION = "medication"

class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

# ============ MODELS ============

# User Models
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    department: Optional[str] = None
    specialty: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class UserResponse(UserBase):
    id: str
    created_at: str
    is_active: bool

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

# Patient Models
class PatientCreate(BaseModel):
    mrn: Optional[str] = None  # Medical Record Number
    first_name: str
    last_name: str
    date_of_birth: str
    gender: Gender
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None

class Patient(PatientCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mrn: str = Field(default_factory=lambda: f"MRN{str(uuid.uuid4())[:8].upper()}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatientResponse(BaseModel):
    id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    created_at: str
    updated_at: str

# Vitals Model
class VitalsCreate(BaseModel):
    patient_id: str
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    notes: Optional[str] = None

class Vitals(VitalsCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recorded_by: str = ""
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Problem/Diagnosis Model
class ProblemCreate(BaseModel):
    patient_id: str
    icd_code: Optional[str] = None
    description: str
    onset_date: Optional[str] = None
    status: str = "active"  # active, resolved, chronic
    notes: Optional[str] = None

class Problem(ProblemCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Medication Model
class MedicationCreate(BaseModel):
    patient_id: str
    name: str
    dosage: str
    frequency: str
    route: str  # oral, IV, topical, etc.
    prescriber: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "active"  # active, discontinued, completed
    notes: Optional[str] = None

class Medication(MedicationCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Allergy Model
class AllergyCreate(BaseModel):
    patient_id: str
    allergen: str
    reaction: str
    severity: str  # mild, moderate, severe
    notes: Optional[str] = None

class Allergy(AllergyCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Clinical Note Model
class ClinicalNoteCreate(BaseModel):
    patient_id: str
    note_type: str  # progress_note, h_and_p, discharge_summary, etc.
    chief_complaint: Optional[str] = None
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    content: Optional[str] = None  # For free-text notes

class ClinicalNote(ClinicalNoteCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_id: str = ""
    author_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signed: bool = False

# Order Model
class OrderCreate(BaseModel):
    patient_id: str
    order_type: OrderType
    description: str
    priority: str = "routine"  # stat, urgent, routine
    instructions: Optional[str] = None
    diagnosis: Optional[str] = None

class Order(OrderCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: OrderStatus = OrderStatus.PENDING
    ordered_by: str = ""
    ordered_by_name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    result: Optional[str] = None

# Appointment Model
class AppointmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    appointment_type: str  # new_patient, follow_up, procedure, etc.
    date: str
    start_time: str
    end_time: str
    reason: Optional[str] = None
    notes: Optional[str] = None

class Appointment(AppointmentCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# AI Documentation Request
class AIDocumentationRequest(BaseModel):
    patient_id: str
    note_type: str
    context: Optional[str] = None
    symptoms: Optional[str] = None
    findings: Optional[str] = None

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=LoginResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(**user_data.model_dump(exclude={"password"}))
    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    token = create_token(user.id, user.role.value)
    
    return LoginResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            department=user.department,
            specialty=user.specialty,
            created_at=user_dict["created_at"],
            is_active=user.is_active
        )
    )

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["role"])
    return LoginResponse(
        token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            role=user["role"],
            department=user.get("department"),
            specialty=user.get("specialty"),
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ USER ROUTES ============

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

# ============ PATIENT ROUTES ============

@api_router.post("/patients", response_model=PatientResponse)
async def create_patient(patient_data: PatientCreate, current_user: dict = Depends(get_current_user)):
    # Convert PatientCreate to dict and exclude None mrn
    patient_dict = patient_data.model_dump()
    if patient_dict.get('mrn') is None:
        patient_dict.pop('mrn', None)
    
    patient = Patient(**patient_dict)
    patient_dict = patient.model_dump()
    patient_dict["created_at"] = patient_dict["created_at"].isoformat()
    patient_dict["updated_at"] = patient_dict["updated_at"].isoformat()
    await db.patients.insert_one(patient_dict)
    return PatientResponse(**patient_dict)

@api_router.get("/patients", response_model=List[PatientResponse])
async def get_patients(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if search:
        query = {
            "$or": [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"mrn": {"$regex": search, "$options": "i"}}
            ]
        }
    patients = await db.patients.find(query, {"_id": 0}).to_list(1000)
    return [PatientResponse(**p) for p in patients]

@api_router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str, current_user: dict = Depends(get_current_user)):
    patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse(**patient)

@api_router.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: str, patient_data: PatientCreate, current_user: dict = Depends(get_current_user)):
    patient = await db.patients.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = patient_data.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.patients.update_one({"id": patient_id}, {"$set": update_data})
    
    updated = await db.patients.find_one({"id": patient_id}, {"_id": 0})
    return PatientResponse(**updated)

# ============ VITALS ROUTES ============

@api_router.post("/vitals")
async def create_vitals(vitals_data: VitalsCreate, current_user: dict = Depends(get_current_user)):
    vitals = Vitals(**vitals_data.model_dump())
    vitals.recorded_by = current_user["id"]
    vitals_dict = vitals.model_dump()
    vitals_dict["recorded_at"] = vitals_dict["recorded_at"].isoformat()
    await db.vitals.insert_one(vitals_dict)
    return {**vitals_dict, "_id": None}

@api_router.get("/vitals/{patient_id}")
async def get_patient_vitals(patient_id: str, current_user: dict = Depends(get_current_user)):
    vitals = await db.vitals.find({"patient_id": patient_id}, {"_id": 0}).sort("recorded_at", -1).to_list(100)
    return vitals

# ============ PROBLEMS ROUTES ============

@api_router.post("/problems")
async def create_problem(problem_data: ProblemCreate, current_user: dict = Depends(get_current_user)):
    problem = Problem(**problem_data.model_dump())
    problem.created_by = current_user["id"]
    problem_dict = problem.model_dump()
    problem_dict["created_at"] = problem_dict["created_at"].isoformat()
    await db.problems.insert_one(problem_dict)
    return {**problem_dict, "_id": None}

@api_router.get("/problems/{patient_id}")
async def get_patient_problems(patient_id: str, current_user: dict = Depends(get_current_user)):
    problems = await db.problems.find({"patient_id": patient_id}, {"_id": 0}).to_list(100)
    return problems

@api_router.put("/problems/{problem_id}")
async def update_problem(problem_id: str, problem_data: ProblemCreate, current_user: dict = Depends(get_current_user)):
    await db.problems.update_one({"id": problem_id}, {"$set": problem_data.model_dump()})
    updated = await db.problems.find_one({"id": problem_id}, {"_id": 0})
    return updated

# ============ MEDICATIONS ROUTES ============

@api_router.post("/medications")
async def create_medication(med_data: MedicationCreate, current_user: dict = Depends(get_current_user)):
    medication = Medication(**med_data.model_dump())
    medication.created_by = current_user["id"]
    med_dict = medication.model_dump()
    med_dict["created_at"] = med_dict["created_at"].isoformat()
    await db.medications.insert_one(med_dict)
    return {**med_dict, "_id": None}

@api_router.get("/medications/{patient_id}")
async def get_patient_medications(patient_id: str, current_user: dict = Depends(get_current_user)):
    meds = await db.medications.find({"patient_id": patient_id}, {"_id": 0}).to_list(100)
    return meds

@api_router.put("/medications/{medication_id}")
async def update_medication(medication_id: str, med_data: MedicationCreate, current_user: dict = Depends(get_current_user)):
    await db.medications.update_one({"id": medication_id}, {"$set": med_data.model_dump()})
    updated = await db.medications.find_one({"id": medication_id}, {"_id": 0})
    return updated

# ============ ALLERGIES ROUTES ============

@api_router.post("/allergies")
async def create_allergy(allergy_data: AllergyCreate, current_user: dict = Depends(get_current_user)):
    allergy = Allergy(**allergy_data.model_dump())
    allergy.created_by = current_user["id"]
    allergy_dict = allergy.model_dump()
    allergy_dict["created_at"] = allergy_dict["created_at"].isoformat()
    await db.allergies.insert_one(allergy_dict)
    return {**allergy_dict, "_id": None}

@api_router.get("/allergies/{patient_id}")
async def get_patient_allergies(patient_id: str, current_user: dict = Depends(get_current_user)):
    allergies = await db.allergies.find({"patient_id": patient_id}, {"_id": 0}).to_list(100)
    return allergies

# ============ CLINICAL NOTES ROUTES ============

@api_router.post("/notes")
async def create_note(note_data: ClinicalNoteCreate, current_user: dict = Depends(get_current_user)):
    note = ClinicalNote(**note_data.model_dump())
    note.author_id = current_user["id"]
    note.author_name = f"{current_user['first_name']} {current_user['last_name']}"
    note_dict = note.model_dump()
    note_dict["created_at"] = note_dict["created_at"].isoformat()
    note_dict["updated_at"] = note_dict["updated_at"].isoformat()
    await db.clinical_notes.insert_one(note_dict)
    return {**note_dict, "_id": None}

@api_router.get("/notes/{patient_id}")
async def get_patient_notes(patient_id: str, current_user: dict = Depends(get_current_user)):
    notes = await db.clinical_notes.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notes

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, note_data: ClinicalNoteCreate, current_user: dict = Depends(get_current_user)):
    update_dict = note_data.model_dump()
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.clinical_notes.update_one({"id": note_id}, {"$set": update_dict})
    updated = await db.clinical_notes.find_one({"id": note_id}, {"_id": 0})
    return updated

@api_router.post("/notes/{note_id}/sign")
async def sign_note(note_id: str, current_user: dict = Depends(get_current_user)):
    await db.clinical_notes.update_one({"id": note_id}, {"$set": {"signed": True}})
    return {"message": "Note signed successfully"}

# ============ ORDERS ROUTES ============

@api_router.post("/orders")
async def create_order(order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
    order = Order(**order_data.model_dump())
    order.ordered_by = current_user["id"]
    order.ordered_by_name = f"{current_user['first_name']} {current_user['last_name']}"
    order_dict = order.model_dump()
    order_dict["created_at"] = order_dict["created_at"].isoformat()
    order_dict["completed_at"] = None
    await db.orders.insert_one(order_dict)
    return {**order_dict, "_id": None}

@api_router.get("/orders")
async def get_orders(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if patient_id:
        query["patient_id"] = patient_id
    if status:
        query["status"] = status
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus, current_user: dict = Depends(get_current_user)):
    update = {"status": status.value}
    if status == OrderStatus.COMPLETED:
        update["completed_at"] = datetime.now(timezone.utc).isoformat()
    await db.orders.update_one({"id": order_id}, {"$set": update})
    updated = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return updated

@api_router.put("/orders/{order_id}/result")
async def add_order_result(order_id: str, result: str, current_user: dict = Depends(get_current_user)):
    await db.orders.update_one({"id": order_id}, {"$set": {"result": result, "status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}})
    updated = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return updated

# ============ APPOINTMENTS ROUTES ============

@api_router.post("/appointments")
async def create_appointment(appt_data: AppointmentCreate, current_user: dict = Depends(get_current_user)):
    appt = Appointment(**appt_data.model_dump())
    appt.created_by = current_user["id"]
    appt_dict = appt.model_dump()
    appt_dict["created_at"] = appt_dict["created_at"].isoformat()
    await db.appointments.insert_one(appt_dict)
    return {**appt_dict, "_id": None}

@api_router.get("/appointments")
async def get_appointments(
    date: Optional[str] = None,
    provider_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if date:
        query["date"] = date
    if provider_id:
        query["provider_id"] = provider_id
    if patient_id:
        query["patient_id"] = patient_id
    appointments = await db.appointments.find(query, {"_id": 0}).sort("date", 1).to_list(1000)
    return appointments

@api_router.put("/appointments/{appt_id}/status")
async def update_appointment_status(appt_id: str, status: AppointmentStatus, current_user: dict = Depends(get_current_user)):
    await db.appointments.update_one({"id": appt_id}, {"$set": {"status": status.value}})
    updated = await db.appointments.find_one({"id": appt_id}, {"_id": 0})
    return updated

# ============ AI DOCUMENTATION ROUTE ============

@api_router.post("/ai/generate-note")
async def generate_ai_note(request: AIDocumentationRequest, current_user: dict = Depends(get_current_user)):
    """Generate AI-assisted clinical documentation using GPT-5.2"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Get patient info for context
        patient = await db.patients.find_one({"id": request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Build the prompt based on note type
        system_message = """You are a medical documentation assistant helping healthcare providers create clinical notes. 
        Generate professional, accurate, and compliant medical documentation based on the information provided.
        Use standard medical terminology and SOAP format when appropriate.
        Be concise but thorough. Do not make up any clinical findings that were not provided."""
        
        prompt = f"""Generate a {request.note_type} for the following patient:
        
Patient: {patient['first_name']} {patient['last_name']}
DOB: {patient['date_of_birth']}
Gender: {patient['gender']}

"""
        if request.symptoms:
            prompt += f"Symptoms/Chief Complaint: {request.symptoms}\n"
        if request.findings:
            prompt += f"Clinical Findings: {request.findings}\n"
        if request.context:
            prompt += f"Additional Context: {request.context}\n"
        
        prompt += "\nPlease generate a professional clinical note with appropriate sections (Subjective, Objective, Assessment, Plan) based on the information provided."
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"yacco-{current_user['id']}-{request.patient_id}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return {"generated_note": response, "note_type": request.note_type}
        
    except ImportError:
        raise HTTPException(status_code=500, detail="AI service not available")
    except Exception as e:
        logger.error(f"AI generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# ============ DASHBOARD STATS ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics based on user role"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    total_patients = await db.patients.count_documents({})
    today_appointments = await db.appointments.count_documents({"date": today})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    recent_notes = await db.clinical_notes.count_documents({})
    
    # Get upcoming appointments
    upcoming = await db.appointments.find(
        {"date": {"$gte": today}, "status": "scheduled"},
        {"_id": 0}
    ).sort("date", 1).limit(5).to_list(5)
    
    # Enrich with patient names
    for appt in upcoming:
        patient = await db.patients.find_one({"id": appt["patient_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
        if patient:
            appt["patient_name"] = f"{patient['first_name']} {patient['last_name']}"
    
    return {
        "total_patients": total_patients,
        "today_appointments": today_appointments,
        "pending_orders": pending_orders,
        "recent_notes": recent_notes,
        "upcoming_appointments": upcoming
    }

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "Yacco EMR API", "version": "1.0.0", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router and middleware
app.include_router(api_router)

# Include FHIR routes
from fhir_routes import fhir_router, create_fhir_endpoints
fhir_api_router = create_fhir_endpoints(db)
app.include_router(fhir_router)

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
