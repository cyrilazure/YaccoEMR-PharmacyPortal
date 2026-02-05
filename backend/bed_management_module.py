"""
Bed Management & Ward Census Module for Yacco EMR
Inpatient capacity and ward operations management
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum

bed_management_router = APIRouter(prefix="/api/beds", tags=["Bed Management"])


# ============== Enums ==============

class BedStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"
    ISOLATION = "isolation"
    BLOCKED = "blocked"


class WardType(str, Enum):
    GENERAL = "general"
    ICU = "icu"
    CCU = "ccu"
    MICU = "micu"
    SICU = "sicu"
    NICU = "nicu"
    PICU = "picu"
    PEDIATRIC = "pediatric"
    MATERNITY = "maternity"
    SURGICAL = "surgical"
    ORTHOPEDIC = "orthopedic"
    ONCOLOGY = "oncology"
    PSYCHIATRIC = "psychiatric"
    EMERGENCY = "emergency"
    ISOLATION = "isolation"
    PRIVATE = "private"


class AdmissionStatus(str, Enum):
    ADMITTED = "admitted"
    TRANSFERRED = "transferred"
    DISCHARGED = "discharged"
    DECEASED = "deceased"
    LEAVE = "leave"  # On leave/pass


class BedGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    ANY = "any"


# ============== Pydantic Models ==============

class WardCreate(BaseModel):
    name: str
    ward_type: WardType
    floor: Optional[str] = None
    building: Optional[str] = None
    department_id: Optional[str] = None
    gender_restriction: BedGender = BedGender.ANY
    total_beds: int = 0
    nurse_station: Optional[str] = None
    description: Optional[str] = None


class RoomCreate(BaseModel):
    ward_id: str
    room_number: str
    room_type: str = "standard"  # standard, private, semi-private, isolation
    total_beds: int = 1
    has_bathroom: bool = True
    has_oxygen: bool = False
    has_suction: bool = False
    notes: Optional[str] = None


class BedCreate(BaseModel):
    room_id: str
    bed_number: str
    bed_type: str = "standard"  # standard, electric, bariatric, pediatric, crib
    has_monitor: bool = False
    has_ventilator: bool = False
    notes: Optional[str] = None


class AdmissionCreate(BaseModel):
    patient_id: str
    bed_id: str
    admission_type: str = "inpatient"  # inpatient, observation, day_surgery
    admitting_diagnosis: str
    admitting_physician_id: str
    admission_source: str = "emergency"  # emergency, direct, transfer, referral
    expected_los: Optional[int] = None  # Expected length of stay in days
    notes: Optional[str] = None
    isolation_required: bool = False
    isolation_type: Optional[str] = None


class TransferCreate(BaseModel):
    to_bed_id: str
    transfer_reason: str
    notes: Optional[str] = None


class DischargeCreate(BaseModel):
    discharge_disposition: str  # home, transfer, AMA, deceased, rehab, SNF
    discharge_diagnosis: str
    discharge_instructions: Optional[str] = None
    follow_up_required: bool = True
    follow_up_date: Optional[str] = None
    follow_up_provider_id: Optional[str] = None


# ============== Default Ward Templates ==============

DEFAULT_WARD_TEMPLATES = [
    {"name": "Emergency Ward", "ward_type": WardType.EMERGENCY, "floor": "Ground", "gender_restriction": BedGender.ANY},
    {"name": "General Ward - Male", "ward_type": WardType.GENERAL, "floor": "1st", "gender_restriction": BedGender.MALE},
    {"name": "General Ward - Female", "ward_type": WardType.GENERAL, "floor": "1st", "gender_restriction": BedGender.FEMALE},
    {"name": "Intensive Care Unit (ICU)", "ward_type": WardType.ICU, "floor": "2nd", "gender_restriction": BedGender.ANY},
    {"name": "Coronary Care Unit (CCU)", "ward_type": WardType.CCU, "floor": "2nd", "gender_restriction": BedGender.ANY},
    {"name": "Medical ICU (MICU)", "ward_type": WardType.MICU, "floor": "2nd", "gender_restriction": BedGender.ANY},
    {"name": "Surgical ICU (SICU)", "ward_type": WardType.SICU, "floor": "2nd", "gender_restriction": BedGender.ANY},
    {"name": "Neonatal ICU (NICU)", "ward_type": WardType.NICU, "floor": "3rd", "gender_restriction": BedGender.ANY},
    {"name": "Pediatric Ward", "ward_type": WardType.PEDIATRIC, "floor": "3rd", "gender_restriction": BedGender.ANY},
    {"name": "Maternity Ward", "ward_type": WardType.MATERNITY, "floor": "4th", "gender_restriction": BedGender.FEMALE},
    {"name": "Surgical Ward", "ward_type": WardType.SURGICAL, "floor": "4th", "gender_restriction": BedGender.ANY},
    {"name": "Orthopedic Ward", "ward_type": WardType.ORTHOPEDIC, "floor": "5th", "gender_restriction": BedGender.ANY},
    {"name": "Isolation Ward", "ward_type": WardType.ISOLATION, "floor": "6th", "gender_restriction": BedGender.ANY},
    {"name": "Private Rooms", "ward_type": WardType.PRIVATE, "floor": "7th", "gender_restriction": BedGender.ANY},
]


def create_bed_management_endpoints(db, get_current_user):
    """Create bed management API endpoints"""
    
    # ============== Ward Management ==============
    
    @bed_management_router.post("/wards/create")
    async def create_ward(
        data: WardCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new ward"""
        allowed_roles = ["bed_manager", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        ward_id = str(uuid.uuid4())
        ward_doc = {
            "id": ward_id,
            "name": data.name,
            "ward_type": data.ward_type,
            "floor": data.floor,
            "building": data.building,
            "department_id": data.department_id,
            "gender_restriction": data.gender_restriction,
            "total_beds": data.total_beds,
            "available_beds": data.total_beds,
            "occupied_beds": 0,
            "nurse_station": data.nurse_station,
            "description": data.description,
            "organization_id": user.get("organization_id"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["wards"].insert_one(ward_doc)
        ward_doc.pop("_id", None)
        return {"message": "Ward created", "ward": ward_doc}
    
    @bed_management_router.post("/wards/seed-defaults")
    async def seed_default_wards(
        user: dict = Depends(get_current_user)
    ):
        """Seed default ward templates"""
        allowed_roles = ["bed_manager", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        org_id = user.get("organization_id")
        
        # Check if wards already exist
        existing = await db["wards"].count_documents({"organization_id": org_id})
        if existing > 0:
            return {"message": f"Wards already exist ({existing} found)", "skipped": True}
        
        created = 0
        for template in DEFAULT_WARD_TEMPLATES:
            ward_id = str(uuid.uuid4())
            ward_doc = {
                "id": ward_id,
                "name": template["name"],
                "ward_type": template["ward_type"],
                "floor": template.get("floor"),
                "building": None,
                "department_id": None,
                "gender_restriction": template.get("gender_restriction", BedGender.ANY),
                "total_beds": 0,
                "available_beds": 0,
                "occupied_beds": 0,
                "nurse_station": None,
                "description": None,
                "organization_id": org_id,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db["wards"].insert_one(ward_doc)
            created += 1
        
        return {"message": f"Created {created} default wards", "count": created}
    
    @bed_management_router.get("/wards")
    async def get_wards(
        ward_type: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get all wards"""
        query = {"organization_id": user.get("organization_id"), "is_active": True}
        if ward_type:
            query["ward_type"] = ward_type
        
        wards = await db["wards"].find(query, {"_id": 0}).sort("name", 1).to_list(100)
        return {"wards": wards, "total": len(wards)}
    
    # ============== Room Management ==============
    
    @bed_management_router.post("/rooms/create")
    async def create_room(
        data: RoomCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new room"""
        allowed_roles = ["bed_manager", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify ward exists
        ward = await db["wards"].find_one({"id": data.ward_id})
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        
        room_id = str(uuid.uuid4())
        room_doc = {
            "id": room_id,
            "ward_id": data.ward_id,
            "ward_name": ward.get("name"),
            "room_number": data.room_number,
            "room_type": data.room_type,
            "total_beds": data.total_beds,
            "available_beds": data.total_beds,
            "has_bathroom": data.has_bathroom,
            "has_oxygen": data.has_oxygen,
            "has_suction": data.has_suction,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["rooms"].insert_one(room_doc)
        room_doc.pop("_id", None)
        return {"message": "Room created", "room": room_doc}
    
    @bed_management_router.get("/rooms")
    async def get_rooms(
        ward_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get rooms"""
        query = {"organization_id": user.get("organization_id"), "is_active": True}
        if ward_id:
            query["ward_id"] = ward_id
        
        rooms = await db["rooms"].find(query, {"_id": 0}).sort("room_number", 1).to_list(200)
        return {"rooms": rooms, "total": len(rooms)}
    
    # ============== Bed Management ==============
    
    @bed_management_router.post("/beds/create")
    async def create_bed(
        data: BedCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create a new bed"""
        # Allow nurses and nursing supervisors to add beds
        allowed_roles = ["bed_manager", "nurse", "nursing_supervisor", "floor_supervisor", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify room exists
        room = await db["rooms"].find_one({"id": data.room_id})
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get ward info
        ward = await db["wards"].find_one({"id": room.get("ward_id")})
        
        bed_id = str(uuid.uuid4())
        bed_doc = {
            "id": bed_id,
            "room_id": data.room_id,
            "room_number": room.get("room_number"),
            "ward_id": room.get("ward_id"),
            "ward_name": ward.get("name") if ward else None,
            "bed_number": data.bed_number,
            "bed_type": data.bed_type,
            "has_monitor": data.has_monitor,
            "has_ventilator": data.has_ventilator,
            "status": BedStatus.AVAILABLE,
            "current_patient_id": None,
            "current_admission_id": None,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["beds"].insert_one(bed_doc)
        bed_doc.pop("_id", None)
        
        # Update ward bed count
        await db["wards"].update_one(
            {"id": room.get("ward_id")},
            {"$inc": {"total_beds": 1, "available_beds": 1}}
        )
        
        return {"message": "Bed created", "bed": bed_doc}
    
    @bed_management_router.post("/beds/bulk-create")
    async def bulk_create_beds(
        ward_id: str,
        room_prefix: str = "R",
        beds_per_room: int = 4,
        num_rooms: int = 5,
        user: dict = Depends(get_current_user)
    ):
        """Bulk create rooms and beds for a ward"""
        # Allow nurses and nursing supervisors to bulk add beds
        allowed_roles = ["bed_manager", "nurse", "nursing_supervisor", "floor_supervisor", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        ward = await db["wards"].find_one({"id": ward_id})
        if not ward:
            raise HTTPException(status_code=404, detail="Ward not found")
        
        org_id = user.get("organization_id")
        rooms_created = 0
        beds_created = 0
        
        for room_num in range(1, num_rooms + 1):
            room_id = str(uuid.uuid4())
            room_number = f"{room_prefix}{room_num:02d}"
            
            room_doc = {
                "id": room_id,
                "ward_id": ward_id,
                "ward_name": ward.get("name"),
                "room_number": room_number,
                "room_type": "standard",
                "total_beds": beds_per_room,
                "available_beds": beds_per_room,
                "has_bathroom": True,
                "has_oxygen": ward.get("ward_type") in ["icu", "ccu", "micu", "sicu"],
                "has_suction": ward.get("ward_type") in ["icu", "ccu", "micu", "sicu"],
                "notes": None,
                "organization_id": org_id,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db["rooms"].insert_one(room_doc)
            rooms_created += 1
            
            for bed_num in range(1, beds_per_room + 1):
                bed_id = str(uuid.uuid4())
                bed_doc = {
                    "id": bed_id,
                    "room_id": room_id,
                    "room_number": room_number,
                    "ward_id": ward_id,
                    "ward_name": ward.get("name"),
                    "bed_number": f"{room_number}-B{bed_num}",
                    "bed_type": "standard",
                    "has_monitor": ward.get("ward_type") in ["icu", "ccu", "micu", "sicu"],
                    "has_ventilator": ward.get("ward_type") in ["icu", "micu", "sicu"],
                    "status": BedStatus.AVAILABLE,
                    "current_patient_id": None,
                    "current_admission_id": None,
                    "notes": None,
                    "organization_id": org_id,
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db["beds"].insert_one(bed_doc)
                beds_created += 1
        
        # Update ward totals
        await db["wards"].update_one(
            {"id": ward_id},
            {"$inc": {"total_beds": beds_created, "available_beds": beds_created}}
        )
        
        return {
            "message": f"Created {rooms_created} rooms with {beds_created} beds",
            "rooms_created": rooms_created,
            "beds_created": beds_created
        }
    
    @bed_management_router.get("/beds")
    async def get_beds(
        ward_id: Optional[str] = None,
        room_id: Optional[str] = None,
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get beds with optional filters"""
        query = {"organization_id": user.get("organization_id"), "is_active": True}
        if ward_id:
            query["ward_id"] = ward_id
        if room_id:
            query["room_id"] = room_id
        if status:
            query["status"] = status
        
        beds = await db["beds"].find(query, {"_id": 0}).sort("bed_number", 1).to_list(500)
        return {"beds": beds, "total": len(beds)}
    
    @bed_management_router.put("/beds/{bed_id}/status")
    async def update_bed_status(
        bed_id: str,
        status: BedStatus,
        notes: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Update bed status"""
        bed = await db["beds"].find_one({"id": bed_id})
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")
        
        old_status = bed.get("status")
        
        await db["beds"].update_one(
            {"id": bed_id},
            {"$set": {
                "status": status,
                "notes": notes,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update ward counts if needed
        if old_status == BedStatus.AVAILABLE and status != BedStatus.AVAILABLE:
            await db["wards"].update_one({"id": bed.get("ward_id")}, {"$inc": {"available_beds": -1}})
        elif old_status != BedStatus.AVAILABLE and status == BedStatus.AVAILABLE:
            await db["wards"].update_one({"id": bed.get("ward_id")}, {"$inc": {"available_beds": 1}})
        
        return {"message": "Bed status updated", "status": status}
    
    # ============== Admission Management ==============
    
    @bed_management_router.post("/admissions/create")
    async def create_admission(
        data: AdmissionCreate,
        user: dict = Depends(get_current_user)
    ):
        """Admit a patient to a bed"""
        # Allow nurses, nursing supervisors, and bed managers to admit patients
        allowed_roles = ["bed_manager", "nurse", "nursing_supervisor", "floor_supervisor", "physician", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify patient
        patient = await db["patients"].find_one({"id": data.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify bed is available
        bed = await db["beds"].find_one({"id": data.bed_id})
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")
        if bed.get("status") != BedStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail=f"Bed is not available (status: {bed.get('status')})")
        
        # Get admitting physician
        physician = await db["users"].find_one({"id": data.admitting_physician_id})
        
        admission_id = str(uuid.uuid4())
        admission_number = f"ADM-{datetime.now().strftime('%Y%m%d')}-{admission_id[:8].upper()}"
        
        admission_doc = {
            "id": admission_id,
            "admission_number": admission_number,
            "patient_id": data.patient_id,
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            "patient_mrn": patient.get("mrn"),
            "bed_id": data.bed_id,
            "bed_number": bed.get("bed_number"),
            "ward_id": bed.get("ward_id"),
            "ward_name": bed.get("ward_name"),
            "room_id": bed.get("room_id"),
            "room_number": bed.get("room_number"),
            "admission_type": data.admission_type,
            "admitting_diagnosis": data.admitting_diagnosis,
            "admitting_physician_id": data.admitting_physician_id,
            "admitting_physician": f"{physician.get('first_name', '')} {physician.get('last_name', '')}" if physician else "",
            "admission_source": data.admission_source,
            "admitted_at": datetime.now(timezone.utc).isoformat(),
            "expected_los": data.expected_los,
            "notes": data.notes,
            "isolation_required": data.isolation_required,
            "isolation_type": data.isolation_type,
            "status": AdmissionStatus.ADMITTED,
            "discharge_date": None,
            "discharge_disposition": None,
            "transfer_history": [],
            "organization_id": user.get("organization_id"),
            "created_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["admissions"].insert_one(admission_doc)
        
        # Remove _id before returning
        admission_doc.pop("_id", None)
        
        # Update bed status
        bed_status = BedStatus.ISOLATION if data.isolation_required else BedStatus.OCCUPIED
        await db["beds"].update_one(
            {"id": data.bed_id},
            {"$set": {
                "status": bed_status,
                "current_patient_id": data.patient_id,
                "current_admission_id": admission_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update ward counts
        await db["wards"].update_one(
            {"id": bed.get("ward_id")},
            {"$inc": {"available_beds": -1, "occupied_beds": 1}}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "patient_admitted",
            "resource_type": "admission",
            "resource_id": admission_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "admission_number": admission_number,
                "patient_id": data.patient_id,
                "bed_id": data.bed_id,
                "ward": bed.get("ward_name")
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Patient admitted successfully", "admission": admission_doc}
    
    @bed_management_router.post("/admissions/{admission_id}/transfer")
    async def transfer_patient(
        admission_id: str,
        data: TransferCreate,
        user: dict = Depends(get_current_user)
    ):
        """Transfer patient to a different bed"""
        admission = await db["admissions"].find_one({"id": admission_id})
        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")
        
        if admission.get("status") != AdmissionStatus.ADMITTED:
            raise HTTPException(status_code=400, detail="Patient is not currently admitted")
        
        # Verify new bed is available
        new_bed = await db["beds"].find_one({"id": data.to_bed_id})
        if not new_bed:
            raise HTTPException(status_code=404, detail="Destination bed not found")
        if new_bed.get("status") != BedStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail="Destination bed is not available")
        
        old_bed_id = admission.get("bed_id")
        old_bed = await db["beds"].find_one({"id": old_bed_id})
        
        # Create transfer record
        transfer_record = {
            "from_bed_id": old_bed_id,
            "from_bed_number": old_bed.get("bed_number") if old_bed else None,
            "from_ward_id": old_bed.get("ward_id") if old_bed else None,
            "from_ward_name": old_bed.get("ward_name") if old_bed else None,
            "to_bed_id": data.to_bed_id,
            "to_bed_number": new_bed.get("bed_number"),
            "to_ward_id": new_bed.get("ward_id"),
            "to_ward_name": new_bed.get("ward_name"),
            "transfer_reason": data.transfer_reason,
            "notes": data.notes,
            "transferred_at": datetime.now(timezone.utc).isoformat(),
            "transferred_by": f"{user.get('first_name', '')} {user.get('last_name', '')}"
        }
        
        # Update admission
        await db["admissions"].update_one(
            {"id": admission_id},
            {
                "$set": {
                    "bed_id": data.to_bed_id,
                    "bed_number": new_bed.get("bed_number"),
                    "ward_id": new_bed.get("ward_id"),
                    "ward_name": new_bed.get("ward_name"),
                    "room_id": new_bed.get("room_id"),
                    "room_number": new_bed.get("room_number"),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$push": {"transfer_history": transfer_record}
            }
        )
        
        # Free old bed
        await db["beds"].update_one(
            {"id": old_bed_id},
            {"$set": {
                "status": BedStatus.CLEANING,
                "current_patient_id": None,
                "current_admission_id": None
            }}
        )
        
        # Occupy new bed
        await db["beds"].update_one(
            {"id": data.to_bed_id},
            {"$set": {
                "status": BedStatus.OCCUPIED,
                "current_patient_id": admission.get("patient_id"),
                "current_admission_id": admission_id
            }}
        )
        
        # Update ward counts if transferring between wards
        if old_bed and old_bed.get("ward_id") != new_bed.get("ward_id"):
            await db["wards"].update_one(
                {"id": old_bed.get("ward_id")},
                {"$inc": {"occupied_beds": -1}}
            )
            await db["wards"].update_one(
                {"id": new_bed.get("ward_id")},
                {"$inc": {"occupied_beds": 1, "available_beds": -1}}
            )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "patient_transferred",
            "resource_type": "admission",
            "resource_id": admission_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": transfer_record,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Patient transferred successfully", "transfer": transfer_record}
    
    @bed_management_router.post("/admissions/{admission_id}/discharge")
    async def discharge_patient(
        admission_id: str,
        data: DischargeCreate,
        user: dict = Depends(get_current_user)
    ):
        """Discharge a patient"""
        admission = await db["admissions"].find_one({"id": admission_id})
        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")
        
        if admission.get("status") != AdmissionStatus.ADMITTED:
            raise HTTPException(status_code=400, detail="Patient is not currently admitted")
        
        # Update admission
        await db["admissions"].update_one(
            {"id": admission_id},
            {"$set": {
                "status": AdmissionStatus.DISCHARGED,
                "discharge_date": datetime.now(timezone.utc).isoformat(),
                "discharge_disposition": data.discharge_disposition,
                "discharge_diagnosis": data.discharge_diagnosis,
                "discharge_instructions": data.discharge_instructions,
                "follow_up_required": data.follow_up_required,
                "follow_up_date": data.follow_up_date,
                "follow_up_provider_id": data.follow_up_provider_id,
                "discharged_by": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Free bed
        bed_id = admission.get("bed_id")
        await db["beds"].update_one(
            {"id": bed_id},
            {"$set": {
                "status": BedStatus.CLEANING,
                "current_patient_id": None,
                "current_admission_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update ward counts
        await db["wards"].update_one(
            {"id": admission.get("ward_id")},
            {"$inc": {"occupied_beds": -1}}
        )
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "patient_discharged",
            "resource_type": "admission",
            "resource_id": admission_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "admission_number": admission.get("admission_number"),
                "patient_id": admission.get("patient_id"),
                "discharge_disposition": data.discharge_disposition
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Patient discharged successfully"}
    
    @bed_management_router.get("/admissions")
    async def get_admissions(
        status: Optional[str] = None,
        ward_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get admissions list"""
        query = {"organization_id": user.get("organization_id")}
        if status:
            query["status"] = status
        else:
            query["status"] = AdmissionStatus.ADMITTED
        if ward_id:
            query["ward_id"] = ward_id
        
        admissions = await db["admissions"].find(query, {"_id": 0}).sort("admitted_at", -1).to_list(200)
        return {"admissions": admissions, "total": len(admissions)}
    
    @bed_management_router.get("/admissions/patient/{patient_id}")
    async def get_patient_admissions(
        patient_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get admission history for a patient"""
        admissions = await db["admissions"].find({"patient_id": patient_id}, {"_id": 0}).sort("admitted_at", -1).to_list(50)
        return {"admissions": admissions, "total": len(admissions)}
    
    # ============== Census Dashboard ==============
    
    @bed_management_router.get("/census")
    async def get_ward_census(
        user: dict = Depends(get_current_user)
    ):
        """Get real-time ward census"""
        org_id = user.get("organization_id")
        
        wards = await db["wards"].find({"organization_id": org_id, "is_active": True}).to_list(50)
        beds = await db["beds"].find({"organization_id": org_id, "is_active": True}).to_list(1000)
        
        # Calculate overall stats
        total_beds = len(beds)
        occupied = len([b for b in beds if b.get("status") == BedStatus.OCCUPIED])
        available = len([b for b in beds if b.get("status") == BedStatus.AVAILABLE])
        reserved = len([b for b in beds if b.get("status") == BedStatus.RESERVED])
        cleaning = len([b for b in beds if b.get("status") == BedStatus.CLEANING])
        maintenance = len([b for b in beds if b.get("status") == BedStatus.MAINTENANCE])
        isolation = len([b for b in beds if b.get("status") == BedStatus.ISOLATION])
        
        # Calculate per-ward stats
        ward_census = []
        for ward in wards:
            ward_beds = [b for b in beds if b.get("ward_id") == ward.get("id")]
            ward_census.append({
                "ward_id": ward.get("id"),
                "ward_name": ward.get("name"),
                "ward_type": ward.get("ward_type"),
                "floor": ward.get("floor"),
                "total_beds": len(ward_beds),
                "occupied": len([b for b in ward_beds if b.get("status") == BedStatus.OCCUPIED]),
                "available": len([b for b in ward_beds if b.get("status") == BedStatus.AVAILABLE]),
                "reserved": len([b for b in ward_beds if b.get("status") == BedStatus.RESERVED]),
                "isolation": len([b for b in ward_beds if b.get("status") == BedStatus.ISOLATION]),
                "occupancy_rate": round(len([b for b in ward_beds if b.get("status") in [BedStatus.OCCUPIED, BedStatus.ISOLATION]]) / len(ward_beds) * 100, 1) if ward_beds else 0
            })
        
        # Critical care capacity
        critical_wards = ["icu", "ccu", "micu", "sicu", "nicu", "picu"]
        critical_beds = [b for b in beds if any(w.get("ward_type") in critical_wards for w in wards if w.get("id") == b.get("ward_id"))]
        
        return {
            "summary": {
                "total_beds": total_beds,
                "occupied": occupied,
                "available": available,
                "reserved": reserved,
                "cleaning": cleaning,
                "maintenance": maintenance,
                "isolation": isolation,
                "overall_occupancy": round(occupied / total_beds * 100, 1) if total_beds > 0 else 0
            },
            "critical_care": {
                "total": len(critical_beds),
                "occupied": len([b for b in critical_beds if b.get("status") == BedStatus.OCCUPIED]),
                "available": len([b for b in critical_beds if b.get("status") == BedStatus.AVAILABLE])
            },
            "wards": ward_census,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return bed_management_router
