"""
MyChart Patient Portal Module for Yacco EMR
Patient-facing portal for health records, appointments, messaging, and refills
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import jwt
import bcrypt

mychart_router = APIRouter(prefix="/api/mychart", tags=["MyChart Portal"])

# ============ Models ============

class PatientPortalUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    email_verified: bool = False

class PortalMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    subject: str
    body: str
    is_from_patient: bool
    is_read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parent_message_id: Optional[str] = None

class RefillRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    medication_id: str
    medication_name: str
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    notes: Optional[str] = None
    status: str = "pending"  # pending, approved, denied
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None

class TelehealthVisit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    provider_id: str
    appointment_id: Optional[str] = None
    scheduled_time: str
    duration_minutes: int = 15
    visit_type: str  # video, phone
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request/Response Models
class PortalLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PortalRegisterRequest(BaseModel):
    patient_id: str
    email: EmailStr
    password: str
    date_of_birth: str  # For verification

class SendMessageRequest(BaseModel):
    subject: str
    body: str
    provider_id: Optional[str] = None

class RequestRefillRequest(BaseModel):
    medication_id: str
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None
    notes: Optional[str] = None

class ScheduleTelehealthRequest(BaseModel):
    provider_id: str
    date: str
    time: str
    visit_type: str = "video"
    reason: Optional[str] = None

def create_mychart_endpoints(db, JWT_SECRET, JWT_ALGORITHM):
    """Create MyChart portal endpoints"""
    
    security = HTTPBearer()
    
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    
    def create_portal_token(user_id: str, patient_id: str) -> str:
        payload = {
            "user_id": user_id,
            "patient_id": patient_id,
            "portal": "mychart",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    async def get_portal_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        try:
            token = credentials.credentials
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("portal") != "mychart":
                raise HTTPException(status_code=401, detail="Invalid portal token")
            user = await db.portal_users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # ============ Authentication ============
    
    @mychart_router.post("/register")
    async def portal_register(request: PortalRegisterRequest):
        """Register for MyChart portal"""
        # Verify patient exists
        patient = await db.patients.find_one({"id": request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify DOB matches
        if patient["date_of_birth"] != request.date_of_birth:
            raise HTTPException(status_code=400, detail="Date of birth does not match records")
        
        # Check if already registered
        existing = await db.portal_users.find_one({"patient_id": request.patient_id})
        if existing:
            raise HTTPException(status_code=400, detail="Patient already registered for portal")
        
        # Create portal user
        user = PatientPortalUser(
            patient_id=request.patient_id,
            email=request.email,
            first_name=patient["first_name"],
            last_name=patient["last_name"]
        )
        user_dict = user.model_dump()
        user_dict["password"] = hash_password(request.password)
        user_dict["created_at"] = user_dict["created_at"].isoformat()
        
        await db.portal_users.insert_one(user_dict)
        
        token = create_portal_token(user.id, request.patient_id)
        return {
            "token": token,
            "user": {
                "id": user.id,
                "patient_id": user.patient_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    
    @mychart_router.post("/login")
    async def portal_login(request: PortalLoginRequest):
        """Login to MyChart portal"""
        user = await db.portal_users.find_one({"email": request.email}, {"_id": 0})
        if not user or not verify_password(request.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_portal_token(user["id"], user["patient_id"])
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "patient_id": user["patient_id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            }
        }
    
    # ============ Health Records ============
    
    @mychart_router.get("/records")
    async def get_health_records(portal_user: dict = Depends(get_portal_user)):
        """Get patient's health records summary"""
        patient_id = portal_user["patient_id"]
        
        # Get patient info
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        
        # Get recent data
        vitals = await db.vitals.find({"patient_id": patient_id}, {"_id": 0}).sort("recorded_at", -1).limit(10).to_list(10)
        problems = await db.problems.find({"patient_id": patient_id}, {"_id": 0}).to_list(50)
        medications = await db.medications.find({"patient_id": patient_id, "status": "active"}, {"_id": 0}).to_list(50)
        allergies = await db.allergies.find({"patient_id": patient_id}, {"_id": 0}).to_list(50)
        
        return {
            "patient": patient,
            "vitals": vitals,
            "problems": problems,
            "medications": medications,
            "allergies": allergies
        }
    
    @mychart_router.get("/results")
    async def get_lab_results(portal_user: dict = Depends(get_portal_user)):
        """Get patient's lab results"""
        patient_id = portal_user["patient_id"]
        
        orders = await db.orders.find(
            {"patient_id": patient_id, "order_type": "lab", "status": "completed"},
            {"_id": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        return orders
    
    # ============ Appointments ============
    
    @mychart_router.get("/appointments")
    async def get_patient_appointments(portal_user: dict = Depends(get_portal_user)):
        """Get patient's appointments"""
        patient_id = portal_user["patient_id"]
        
        appointments = await db.appointments.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("date", -1).limit(50).to_list(50)
        
        # Enrich with provider names
        for appt in appointments:
            if appt.get("provider_id"):
                provider = await db.users.find_one({"id": appt["provider_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
                if provider:
                    appt["provider_name"] = f"Dr. {provider['first_name']} {provider['last_name']}"
        
        return appointments
    
    @mychart_router.post("/appointments/request")
    async def request_appointment(
        provider_id: str,
        preferred_date: str,
        reason: str,
        portal_user: dict = Depends(get_portal_user)
    ):
        """Request a new appointment"""
        patient_id = portal_user["patient_id"]
        
        request_data = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "patient_name": f"{portal_user['first_name']} {portal_user['last_name']}",
            "provider_id": provider_id,
            "preferred_date": preferred_date,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.appointment_requests.insert_one(request_data)
        return {"message": "Appointment request submitted", "request_id": request_data["id"]}
    
    # ============ Messaging ============
    
    @mychart_router.get("/messages")
    async def get_messages(portal_user: dict = Depends(get_portal_user)):
        """Get patient's messages"""
        patient_id = portal_user["patient_id"]
        
        messages = await db.portal_messages.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(100).to_list(100)
        
        return messages
    
    @mychart_router.post("/messages")
    async def send_message(request: SendMessageRequest, portal_user: dict = Depends(get_portal_user)):
        """Send a message to care team"""
        patient_id = portal_user["patient_id"]
        
        message = PortalMessage(
            patient_id=patient_id,
            patient_name=f"{portal_user['first_name']} {portal_user['last_name']}",
            provider_id=request.provider_id,
            subject=request.subject,
            body=request.body,
            is_from_patient=True
        )
        
        msg_dict = message.model_dump()
        msg_dict["created_at"] = msg_dict["created_at"].isoformat()
        
        await db.portal_messages.insert_one(msg_dict)
        return {"message": "Message sent", "message_id": message.id}
    
    @mychart_router.put("/messages/{message_id}/read")
    async def mark_message_read(message_id: str, portal_user: dict = Depends(get_portal_user)):
        """Mark a message as read"""
        await db.portal_messages.update_one(
            {"id": message_id, "patient_id": portal_user["patient_id"]},
            {"$set": {"is_read": True}}
        )
        return {"message": "Message marked as read"}
    
    # ============ Prescription Refills ============
    
    @mychart_router.get("/refills")
    async def get_refill_requests(portal_user: dict = Depends(get_portal_user)):
        """Get patient's refill requests"""
        patient_id = portal_user["patient_id"]
        
        refills = await db.refill_requests.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        return refills
    
    @mychart_router.post("/refills")
    async def request_refill(request: RequestRefillRequest, portal_user: dict = Depends(get_portal_user)):
        """Request a prescription refill"""
        patient_id = portal_user["patient_id"]
        
        # Verify medication belongs to patient
        medication = await db.medications.find_one(
            {"id": request.medication_id, "patient_id": patient_id},
            {"_id": 0}
        )
        if not medication:
            raise HTTPException(status_code=404, detail="Medication not found")
        
        refill = RefillRequest(
            patient_id=patient_id,
            medication_id=request.medication_id,
            medication_name=medication["name"],
            pharmacy_name=request.pharmacy_name,
            pharmacy_phone=request.pharmacy_phone,
            notes=request.notes
        )
        
        refill_dict = refill.model_dump()
        refill_dict["created_at"] = refill_dict["created_at"].isoformat()
        
        await db.refill_requests.insert_one(refill_dict)
        return {"message": "Refill request submitted", "request_id": refill.id}
    
    # ============ Telehealth ============
    
    @mychart_router.get("/telehealth")
    async def get_telehealth_visits(portal_user: dict = Depends(get_portal_user)):
        """Get patient's telehealth visits"""
        patient_id = portal_user["patient_id"]
        
        visits = await db.telehealth_visits.find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("scheduled_time", -1).limit(50).to_list(50)
        
        return visits
    
    @mychart_router.post("/telehealth/schedule")
    async def schedule_telehealth(request: ScheduleTelehealthRequest, portal_user: dict = Depends(get_portal_user)):
        """Schedule a telehealth visit"""
        patient_id = portal_user["patient_id"]
        
        # Generate meeting link (in production, integrate with video service)
        meeting_id = str(uuid.uuid4())[:8]
        meeting_link = f"https://yacco-telehealth.com/visit/{meeting_id}"
        
        visit = TelehealthVisit(
            patient_id=patient_id,
            provider_id=request.provider_id,
            scheduled_time=f"{request.date}T{request.time}:00",
            visit_type=request.visit_type,
            meeting_link=meeting_link,
            notes=request.reason
        )
        
        visit_dict = visit.model_dump()
        visit_dict["created_at"] = visit_dict["created_at"].isoformat()
        
        await db.telehealth_visits.insert_one(visit_dict)
        
        return {
            "message": "Telehealth visit scheduled",
            "visit_id": visit.id,
            "meeting_link": meeting_link
        }
    
    # ============ Providers List ============
    
    @mychart_router.get("/providers")
    async def get_providers(portal_user: dict = Depends(get_portal_user)):
        """Get list of providers for messaging/scheduling"""
        providers = await db.users.find(
            {"role": "physician"},
            {"_id": 0, "password": 0}
        ).to_list(100)
        
        return [
            {
                "id": p["id"],
                "name": f"Dr. {p['first_name']} {p['last_name']}",
                "specialty": p.get("specialty"),
                "department": p.get("department")
            }
            for p in providers
        ]
    
    return mychart_router, get_portal_user
