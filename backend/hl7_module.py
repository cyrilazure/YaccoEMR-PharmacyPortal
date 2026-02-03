"""
HL7 v2 ADT (Admission/Discharge/Transfer) Module for Yacco EMR
Supports HL7 v2.x message parsing and generation for patient ADT events
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid

hl7_router = APIRouter(prefix="/api/hl7", tags=["HL7 v2 Integration"])

# ============ HL7 Message Types ============

class ADTEventType(str, Enum):
    A01 = "A01"  # Admit/Visit Notification
    A02 = "A02"  # Transfer a Patient
    A03 = "A03"  # Discharge/End Visit
    A04 = "A04"  # Register a Patient
    A05 = "A05"  # Pre-Admit a Patient
    A06 = "A06"  # Change Outpatient to Inpatient
    A07 = "A07"  # Change Inpatient to Outpatient
    A08 = "A08"  # Update Patient Information
    A11 = "A11"  # Cancel Admit
    A12 = "A12"  # Cancel Transfer
    A13 = "A13"  # Cancel Discharge

class PatientClass(str, Enum):
    INPATIENT = "I"
    OUTPATIENT = "O"
    EMERGENCY = "E"
    PREADMIT = "P"

# ============ Models ============

class HL7Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: str
    event_type: str
    sending_application: str
    sending_facility: str
    receiving_application: str
    receiving_facility: str
    message_datetime: str
    message_control_id: str
    raw_message: Optional[str] = None
    parsed_data: Optional[Dict] = None
    patient_id: Optional[str] = None
    status: str = "received"  # received, processed, error
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ADTEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: ADTEventType
    patient_id: str
    patient_name: str
    mrn: str
    patient_class: PatientClass
    admit_datetime: Optional[str] = None
    discharge_datetime: Optional[str] = None
    location: Optional[str] = None  # Ward/Room/Bed
    attending_physician: Optional[str] = None
    admitting_diagnosis: Optional[str] = None
    transfer_from: Optional[str] = None
    transfer_to: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BedAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    ward: str
    room: str
    bed: str
    status: str = "occupied"  # occupied, reserved, available
    admit_datetime: str
    expected_discharge: Optional[str] = None
    attending_physician: Optional[str] = None
    notes: Optional[str] = None

# Request Models
class AdmitPatientRequest(BaseModel):
    patient_id: str
    patient_class: PatientClass
    ward: str
    room: str
    bed: str
    attending_physician_id: Optional[str] = None
    admitting_diagnosis: Optional[str] = None

class TransferPatientRequest(BaseModel):
    patient_id: str
    from_location: str  # ward-room-bed
    to_ward: str
    to_room: str
    to_bed: str
    reason: Optional[str] = None

class DischargePatientRequest(BaseModel):
    patient_id: str
    discharge_disposition: str  # home, transfer, expired, etc.
    discharge_diagnosis: Optional[str] = None
    follow_up_instructions: Optional[str] = None

def create_hl7_endpoints(db, get_current_user):
    """Create HL7 v2 ADT endpoints"""
    
    def generate_hl7_message(
        event_type: ADTEventType,
        patient: dict,
        event_data: dict
    ) -> str:
        """Generate HL7 v2 ADT message"""
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d%H%M%S")
        msg_control_id = str(uuid.uuid4())[:10].upper()
        
        # MSH Segment
        msh = f"MSH|^~\\&|YACCO_EMR|YACCO_HOSPITAL|EXTERNAL|EXTERNAL|{timestamp}||ADT^{event_type.value}|{msg_control_id}|P|2.5"
        
        # EVN Segment
        evn = f"EVN|{event_type.value}|{timestamp}"
        
        # PID Segment
        dob = patient.get("date_of_birth", "").replace("-", "")
        gender = patient.get("gender", "U")[0].upper()
        pid = f"PID|1||{patient.get('mrn', '')}||{patient.get('last_name', '')}^{patient.get('first_name', '')}||{dob}|{gender}"
        
        # PV1 Segment
        patient_class = event_data.get("patient_class", "O")
        location = event_data.get("location", "")
        attending = event_data.get("attending_physician", "")
        admit_dt = event_data.get("admit_datetime", timestamp)
        pv1 = f"PV1|1|{patient_class}|{location}|||{attending}|||||||||||||||||||||||||||||||{admit_dt}"
        
        # Build message
        message = "\r".join([msh, evn, pid, pv1])
        return message
    
    def parse_hl7_message(raw_message: str) -> Dict:
        """Parse incoming HL7 v2 message"""
        segments = raw_message.strip().split("\r")
        parsed = {"segments": {}}
        
        for segment in segments:
            if not segment:
                continue
            fields = segment.split("|")
            segment_name = fields[0]
            parsed["segments"][segment_name] = fields
            
            if segment_name == "MSH":
                parsed["message_type"] = fields[8].split("^")[0] if len(fields) > 8 else ""
                parsed["event_type"] = fields[8].split("^")[1] if len(fields) > 8 and "^" in fields[8] else ""
                parsed["sending_app"] = fields[2] if len(fields) > 2 else ""
                parsed["sending_facility"] = fields[3] if len(fields) > 3 else ""
                parsed["message_datetime"] = fields[6] if len(fields) > 6 else ""
                parsed["message_control_id"] = fields[9] if len(fields) > 9 else ""
            
            elif segment_name == "PID":
                parsed["patient_mrn"] = fields[3] if len(fields) > 3 else ""
                name_parts = fields[5].split("^") if len(fields) > 5 else ["", ""]
                parsed["patient_last_name"] = name_parts[0]
                parsed["patient_first_name"] = name_parts[1] if len(name_parts) > 1 else ""
            
            elif segment_name == "PV1":
                parsed["patient_class"] = fields[2] if len(fields) > 2 else ""
                parsed["location"] = fields[3] if len(fields) > 3 else ""
                parsed["attending_physician"] = fields[7] if len(fields) > 7 else ""
        
        return parsed
    
    # ============ ADT Event Endpoints ============
    
    @hl7_router.post("/adt/admit")
    async def admit_patient(request: AdmitPatientRequest, current_user: dict = Depends(get_current_user)):
        """Admit a patient (generates A01 ADT event)"""
        # Get patient
        patient = await db.patients.find_one({"id": request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        location = f"{request.ward}^{request.room}^{request.bed}"
        admit_datetime = datetime.now(timezone.utc).isoformat()
        
        # Get attending physician name
        attending_name = ""
        if request.attending_physician_id:
            physician = await db.users.find_one({"id": request.attending_physician_id}, {"_id": 0})
            if physician:
                attending_name = f"Dr. {physician['first_name']} {physician['last_name']}"
        
        # Create ADT event
        event = ADTEvent(
            event_type=ADTEventType.A01,
            patient_id=request.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            mrn=patient["mrn"],
            patient_class=request.patient_class,
            admit_datetime=admit_datetime,
            location=location,
            attending_physician=attending_name,
            admitting_diagnosis=request.admitting_diagnosis
        )
        
        event_dict = event.model_dump()
        event_dict["created_at"] = event_dict["created_at"].isoformat()
        await db.adt_events.insert_one(event_dict)
        
        # Create bed assignment
        bed_assignment = BedAssignment(
            patient_id=request.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            ward=request.ward,
            room=request.room,
            bed=request.bed,
            admit_datetime=admit_datetime,
            attending_physician=attending_name
        )
        
        bed_dict = bed_assignment.model_dump()
        await db.bed_assignments.insert_one(bed_dict)
        
        # Generate HL7 message
        hl7_message = generate_hl7_message(
            ADTEventType.A01,
            patient,
            {
                "patient_class": request.patient_class.value,
                "location": location,
                "attending_physician": attending_name,
                "admit_datetime": admit_datetime.replace("-", "").replace(":", "").replace("T", "")[:14]
            }
        )
        
        # Store HL7 message
        msg_record = HL7Message(
            message_type="ADT",
            event_type="A01",
            sending_application="YACCO_EMR",
            sending_facility="YACCO_HOSPITAL",
            receiving_application="EXTERNAL",
            receiving_facility="EXTERNAL",
            message_datetime=admit_datetime,
            message_control_id=str(uuid.uuid4())[:10],
            raw_message=hl7_message,
            patient_id=request.patient_id,
            status="generated"
        )
        msg_dict = msg_record.model_dump()
        msg_dict["created_at"] = msg_dict["created_at"].isoformat()
        await db.hl7_messages.insert_one(msg_dict)
        
        return {
            "message": "Patient admitted successfully",
            "event_id": event.id,
            "bed_assignment_id": bed_assignment.id,
            "hl7_message": hl7_message
        }
    
    @hl7_router.post("/adt/transfer")
    async def transfer_patient(request: TransferPatientRequest, current_user: dict = Depends(get_current_user)):
        """Transfer a patient (generates A02 ADT event)"""
        # Get patient
        patient = await db.patients.find_one({"id": request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get current bed assignment
        current_bed = await db.bed_assignments.find_one(
            {"patient_id": request.patient_id, "status": "occupied"},
            {"_id": 0}
        )
        if not current_bed:
            raise HTTPException(status_code=400, detail="Patient not currently admitted")
        
        new_location = f"{request.to_ward}^{request.to_room}^{request.to_bed}"
        transfer_datetime = datetime.now(timezone.utc).isoformat()
        
        # Create ADT event
        event = ADTEvent(
            event_type=ADTEventType.A02,
            patient_id=request.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            mrn=patient["mrn"],
            patient_class=PatientClass.INPATIENT,
            location=new_location,
            transfer_from=request.from_location,
            transfer_to=new_location
        )
        
        event_dict = event.model_dump()
        event_dict["created_at"] = event_dict["created_at"].isoformat()
        await db.adt_events.insert_one(event_dict)
        
        # Update bed assignment
        await db.bed_assignments.update_one(
            {"patient_id": request.patient_id, "status": "occupied"},
            {"$set": {
                "ward": request.to_ward,
                "room": request.to_room,
                "bed": request.to_bed
            }}
        )
        
        return {
            "message": "Patient transferred successfully",
            "event_id": event.id,
            "from_location": request.from_location,
            "to_location": new_location
        }
    
    @hl7_router.post("/adt/discharge")
    async def discharge_patient(request: DischargePatientRequest, current_user: dict = Depends(get_current_user)):
        """Discharge a patient (generates A03 ADT event)"""
        # Get patient
        patient = await db.patients.find_one({"id": request.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get current bed assignment
        current_bed = await db.bed_assignments.find_one(
            {"patient_id": request.patient_id, "status": "occupied"},
            {"_id": 0}
        )
        
        discharge_datetime = datetime.now(timezone.utc).isoformat()
        
        # Create ADT event
        event = ADTEvent(
            event_type=ADTEventType.A03,
            patient_id=request.patient_id,
            patient_name=f"{patient['first_name']} {patient['last_name']}",
            mrn=patient["mrn"],
            patient_class=PatientClass.OUTPATIENT,
            discharge_datetime=discharge_datetime,
            location=f"{current_bed['ward']}^{current_bed['room']}^{current_bed['bed']}" if current_bed else None
        )
        
        event_dict = event.model_dump()
        event_dict["created_at"] = event_dict["created_at"].isoformat()
        event_dict["discharge_disposition"] = request.discharge_disposition
        event_dict["discharge_diagnosis"] = request.discharge_diagnosis
        event_dict["follow_up_instructions"] = request.follow_up_instructions
        await db.adt_events.insert_one(event_dict)
        
        # Free up bed
        if current_bed:
            await db.bed_assignments.update_one(
                {"patient_id": request.patient_id, "status": "occupied"},
                {"$set": {"status": "discharged", "discharge_datetime": discharge_datetime}}
            )
        
        return {
            "message": "Patient discharged successfully",
            "event_id": event.id,
            "discharge_datetime": discharge_datetime
        }
    
    # ============ Bed Management ============
    
    @hl7_router.get("/beds")
    async def get_bed_census(
        ward: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get current bed census"""
        query = {}
        if ward:
            query["ward"] = ward
        if status:
            query["status"] = status
        else:
            query["status"] = "occupied"
        
        beds = await db.bed_assignments.find(query, {"_id": 0}).to_list(500)
        return beds
    
    @hl7_router.get("/beds/available")
    async def get_available_beds(
        ward: Optional[str] = Query(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Get available beds"""
        # Get occupied beds
        query = {"status": "occupied"}
        if ward:
            query["ward"] = ward
        
        occupied = await db.bed_assignments.find(query, {"_id": 0, "ward": 1, "room": 1, "bed": 1}).to_list(500)
        occupied_set = {f"{b['ward']}-{b['room']}-{b['bed']}" for b in occupied}
        
        # Define hospital beds (in production, this would be in a config)
        all_beds = []
        wards = ["ICU", "MED-SURG", "PEDS", "OB", "PSYCH"]
        for w in wards:
            for room in range(1, 11):
                for bed in ["A", "B"]:
                    bed_id = f"{w}-{room:02d}-{bed}"
                    all_beds.append({
                        "ward": w,
                        "room": f"{room:02d}",
                        "bed": bed,
                        "available": bed_id not in occupied_set
                    })
        
        if ward:
            all_beds = [b for b in all_beds if b["ward"] == ward]
        
        return [b for b in all_beds if b["available"]]
    
    # ============ ADT Events History ============
    
    @hl7_router.get("/adt/events")
    async def get_adt_events(
        patient_id: Optional[str] = Query(None),
        event_type: Optional[str] = Query(None),
        limit: int = Query(100),
        current_user: dict = Depends(get_current_user)
    ):
        """Get ADT events history"""
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if event_type:
            query["event_type"] = event_type
        
        events = await db.adt_events.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return events
    
    # ============ HL7 Message Processing ============
    
    @hl7_router.post("/messages/receive")
    async def receive_hl7_message(raw_message: str, current_user: dict = Depends(get_current_user)):
        """Receive and process incoming HL7 message"""
        try:
            parsed = parse_hl7_message(raw_message)
            
            msg_record = HL7Message(
                message_type=parsed.get("message_type", ""),
                event_type=parsed.get("event_type", ""),
                sending_application=parsed.get("sending_app", ""),
                sending_facility=parsed.get("sending_facility", ""),
                receiving_application="YACCO_EMR",
                receiving_facility="YACCO_HOSPITAL",
                message_datetime=parsed.get("message_datetime", ""),
                message_control_id=parsed.get("message_control_id", ""),
                raw_message=raw_message,
                parsed_data=parsed,
                status="received"
            )
            
            msg_dict = msg_record.model_dump()
            msg_dict["created_at"] = msg_dict["created_at"].isoformat()
            await db.hl7_messages.insert_one(msg_dict)
            
            # Generate ACK
            ack = f"MSH|^~\\&|YACCO_EMR|YACCO_HOSPITAL|{parsed.get('sending_app', '')}|{parsed.get('sending_facility', '')}|{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}||ACK|{str(uuid.uuid4())[:10]}|P|2.5\rMSA|AA|{parsed.get('message_control_id', '')}"
            
            return {
                "status": "received",
                "message_id": msg_record.id,
                "ack": ack
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing HL7 message: {str(e)}")
    
    @hl7_router.get("/messages")
    async def get_hl7_messages(
        status: Optional[str] = Query(None),
        limit: int = Query(100),
        current_user: dict = Depends(get_current_user)
    ):
        """Get HL7 message history"""
        query = {}
        if status:
            query["status"] = status
        
        messages = await db.hl7_messages.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return messages
    
    return hl7_router
