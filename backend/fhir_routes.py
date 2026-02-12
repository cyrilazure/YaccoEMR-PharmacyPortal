"""
FHIR R4 API Endpoints for Yacco EMR
Implements standard FHIR resources for healthcare interoperability
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

fhir_router = APIRouter(prefix="/api/fhir", tags=["FHIR R4"])

# ============ FHIR Resource Models ============

class FHIRIdentifier(BaseModel):
    system: str
    value: str

class FHIRCodeableConcept(BaseModel):
    coding: List[dict] = []
    text: Optional[str] = None

class FHIRReference(BaseModel):
    reference: str
    display: Optional[str] = None

class FHIRHumanName(BaseModel):
    use: str = "official"
    family: str
    given: List[str] = []

class FHIRContactPoint(BaseModel):
    system: str  # phone, email
    value: str
    use: str = "home"

class FHIRAddress(BaseModel):
    use: str = "home"
    line: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: str = "US"

# FHIR Patient Resource
class FHIRPatient(BaseModel):
    resourceType: str = "Patient"
    id: str
    identifier: List[FHIRIdentifier] = []
    active: bool = True
    name: List[FHIRHumanName] = []
    telecom: List[FHIRContactPoint] = []
    gender: str
    birthDate: str
    address: List[FHIRAddress] = []

# FHIR Observation Resource (Vitals)
class FHIRObservation(BaseModel):
    resourceType: str = "Observation"
    id: str
    status: str = "final"
    category: List[FHIRCodeableConcept] = []
    code: FHIRCodeableConcept
    subject: FHIRReference
    effectiveDateTime: str
    valueQuantity: Optional[dict] = None
    component: List[dict] = []

# FHIR Condition Resource (Problems)
class FHIRCondition(BaseModel):
    resourceType: str = "Condition"
    id: str
    clinicalStatus: FHIRCodeableConcept
    verificationStatus: FHIRCodeableConcept
    category: List[FHIRCodeableConcept] = []
    code: FHIRCodeableConcept
    subject: FHIRReference
    onsetDateTime: Optional[str] = None
    recordedDate: str

# FHIR MedicationRequest Resource
class FHIRMedicationRequest(BaseModel):
    resourceType: str = "MedicationRequest"
    id: str
    status: str
    intent: str = "order"
    medicationCodeableConcept: FHIRCodeableConcept
    subject: FHIRReference
    authoredOn: str
    dosageInstruction: List[dict] = []

# FHIR AllergyIntolerance Resource
class FHIRAllergyIntolerance(BaseModel):
    resourceType: str = "AllergyIntolerance"
    id: str
    clinicalStatus: FHIRCodeableConcept
    verificationStatus: FHIRCodeableConcept
    type: str = "allergy"
    category: List[str] = []
    criticality: str
    code: FHIRCodeableConcept
    patient: FHIRReference
    reaction: List[dict] = []

# FHIR Appointment Resource
class FHIRAppointment(BaseModel):
    resourceType: str = "Appointment"
    id: str
    status: str
    serviceType: List[FHIRCodeableConcept] = []
    start: str
    end: str
    participant: List[dict] = []
    reasonCode: List[FHIRCodeableConcept] = []

# FHIR ServiceRequest Resource (Orders)
class FHIRServiceRequest(BaseModel):
    resourceType: str = "ServiceRequest"
    id: str
    status: str
    intent: str = "order"
    category: List[FHIRCodeableConcept] = []
    priority: str
    code: FHIRCodeableConcept
    subject: FHIRReference
    authoredOn: str
    requester: Optional[FHIRReference] = None

# FHIR Bundle for search results
class FHIRBundle(BaseModel):
    resourceType: str = "Bundle"
    id: str
    type: str = "searchset"
    total: int
    entry: List[dict] = []

# ============ Conversion Helpers ============

def patient_to_fhir(patient: dict) -> FHIRPatient:
    """Convert internal patient to FHIR Patient resource"""
    telecom = []
    if patient.get("phone"):
        telecom.append(FHIRContactPoint(system="phone", value=patient["phone"]))
    if patient.get("email"):
        telecom.append(FHIRContactPoint(system="email", value=patient["email"]))
    
    address = []
    if patient.get("address"):
        address.append(FHIRAddress(line=[patient["address"]]))
    
    return FHIRPatient(
        id=patient["id"],
        identifier=[FHIRIdentifier(system="urn:yacco:mrn", value=patient["mrn"])],
        name=[FHIRHumanName(
            family=patient["last_name"],
            given=[patient["first_name"]]
        )],
        telecom=telecom,
        gender=patient["gender"],
        birthDate=patient["date_of_birth"],
        address=address
    )

def vitals_to_fhir_observation(vitals: dict, patient_id: str) -> FHIRObservation:
    """Convert vitals to FHIR Observation resource"""
    components = []
    
    if vitals.get("blood_pressure_systolic"):
        components.append({
            "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]},
            "valueQuantity": {"value": vitals["blood_pressure_systolic"], "unit": "mmHg", "system": "http://unitsofmeasure.org"}
        })
    if vitals.get("blood_pressure_diastolic"):
        components.append({
            "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic blood pressure"}]},
            "valueQuantity": {"value": vitals["blood_pressure_diastolic"], "unit": "mmHg", "system": "http://unitsofmeasure.org"}
        })
    if vitals.get("heart_rate"):
        components.append({
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
            "valueQuantity": {"value": vitals["heart_rate"], "unit": "/min", "system": "http://unitsofmeasure.org"}
        })
    if vitals.get("temperature"):
        components.append({
            "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}]},
            "valueQuantity": {"value": vitals["temperature"], "unit": "degF", "system": "http://unitsofmeasure.org"}
        })
    if vitals.get("oxygen_saturation"):
        components.append({
            "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6", "display": "Oxygen saturation"}]},
            "valueQuantity": {"value": vitals["oxygen_saturation"], "unit": "%", "system": "http://unitsofmeasure.org"}
        })
    
    return FHIRObservation(
        id=vitals["id"],
        category=[FHIRCodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}],
            text="Vital Signs"
        )],
        code=FHIRCodeableConcept(
            coding=[{"system": "http://loinc.org", "code": "85353-1", "display": "Vital signs panel"}],
            text="Vital Signs Panel"
        ),
        subject=FHIRReference(reference=f"Patient/{patient_id}"),
        effectiveDateTime=vitals["recorded_at"],
        component=components
    )

def problem_to_fhir_condition(problem: dict, patient_id: str) -> FHIRCondition:
    """Convert problem to FHIR Condition resource"""
    status_map = {
        "active": "active",
        "resolved": "resolved",
        "chronic": "active"
    }
    
    return FHIRCondition(
        id=problem["id"],
        clinicalStatus=FHIRCodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": status_map.get(problem["status"], "active")}]
        ),
        verificationStatus=FHIRCodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
        ),
        category=[FHIRCodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "problem-list-item"}]
        )],
        code=FHIRCodeableConcept(
            coding=[{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": problem.get("icd_code", ""), "display": problem["description"]}] if problem.get("icd_code") else [],
            text=problem["description"]
        ),
        subject=FHIRReference(reference=f"Patient/{patient_id}"),
        onsetDateTime=problem.get("onset_date"),
        recordedDate=problem["created_at"]
    )

def medication_to_fhir(med: dict, patient_id: str) -> FHIRMedicationRequest:
    """Convert medication to FHIR MedicationRequest resource"""
    status_map = {
        "active": "active",
        "discontinued": "stopped",
        "completed": "completed"
    }
    
    return FHIRMedicationRequest(
        id=med["id"],
        status=status_map.get(med["status"], "active"),
        medicationCodeableConcept=FHIRCodeableConcept(text=med["name"]),
        subject=FHIRReference(reference=f"Patient/{patient_id}"),
        authoredOn=med["created_at"],
        dosageInstruction=[{
            "text": f"{med['dosage']} {med['frequency']} via {med['route']}"
        }]
    )

def allergy_to_fhir(allergy: dict, patient_id: str) -> FHIRAllergyIntolerance:
    """Convert allergy to FHIR AllergyIntolerance resource"""
    criticality_map = {
        "mild": "low",
        "moderate": "low",
        "severe": "high"
    }
    
    return FHIRAllergyIntolerance(
        id=allergy["id"],
        clinicalStatus=FHIRCodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
        ),
        verificationStatus=FHIRCodeableConcept(
            coding=[{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "code": "confirmed"}]
        ),
        category=["medication"],
        criticality=criticality_map.get(allergy["severity"], "low"),
        code=FHIRCodeableConcept(text=allergy["allergen"]),
        patient=FHIRReference(reference=f"Patient/{patient_id}"),
        reaction=[{
            "manifestation": [{"text": allergy["reaction"]}],
            "severity": allergy["severity"]
        }]
    )

def order_to_fhir_service_request(order: dict) -> FHIRServiceRequest:
    """Convert order to FHIR ServiceRequest resource"""
    status_map = {
        "pending": "active",
        "in_progress": "active",
        "completed": "completed",
        "cancelled": "revoked"
    }
    priority_map = {
        "stat": "stat",
        "urgent": "urgent",
        "routine": "routine"
    }
    category_map = {
        "lab": {"system": "http://snomed.info/sct", "code": "108252007", "display": "Laboratory procedure"},
        "imaging": {"system": "http://snomed.info/sct", "code": "363679005", "display": "Imaging"},
        "medication": {"system": "http://snomed.info/sct", "code": "182832007", "display": "Medication procedure"}
    }
    
    return FHIRServiceRequest(
        id=order["id"],
        status=status_map.get(order["status"], "active"),
        category=[FHIRCodeableConcept(coding=[category_map.get(order["order_type"], {})])],
        priority=priority_map.get(order["priority"], "routine"),
        code=FHIRCodeableConcept(text=order["description"]),
        subject=FHIRReference(reference=f"Patient/{order['patient_id']}"),
        authoredOn=order["created_at"],
        requester=FHIRReference(reference=f"Practitioner/{order['ordered_by']}", display=order.get("ordered_by_name"))
    )

def appointment_to_fhir(appt: dict, patient_name: str = None, provider_name: str = None) -> FHIRAppointment:
    """Convert appointment to FHIR Appointment resource"""
    status_map = {
        "scheduled": "booked",
        "checked_in": "arrived",
        "in_progress": "fulfilled",
        "completed": "fulfilled",
        "cancelled": "cancelled",
        "no_show": "noshow"
    }
    
    participants = [
        {
            "actor": {"reference": f"Patient/{appt['patient_id']}", "display": patient_name},
            "status": "accepted"
        }
    ]
    if appt.get("provider_id"):
        participants.append({
            "actor": {"reference": f"Practitioner/{appt['provider_id']}", "display": provider_name},
            "status": "accepted"
        })
    
    return FHIRAppointment(
        id=appt["id"],
        status=status_map.get(appt["status"], "booked"),
        serviceType=[FHIRCodeableConcept(text=appt["appointment_type"])],
        start=f"{appt['date']}T{appt['start_time']}:00",
        end=f"{appt['date']}T{appt['end_time']}:00",
        participant=participants,
        reasonCode=[FHIRCodeableConcept(text=appt.get("reason"))] if appt.get("reason") else []
    )

# ============ FHIR Capability Statement ============

@fhir_router.get("/metadata")
async def get_capability_statement():
    """FHIR Capability Statement - describes server capabilities"""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.now(timezone.utc).isoformat(),
        "kind": "instance",
        "software": {
            "name": "Yacco EMR",
            "version": "1.0.0"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {"type": "Patient", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "Observation", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "Condition", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "MedicationRequest", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "AllergyIntolerance", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "Appointment", "interaction": [{"code": "read"}, {"code": "search-type"}]},
                {"type": "ServiceRequest", "interaction": [{"code": "read"}, {"code": "search-type"}]}
            ]
        }]
    }

def create_fhir_endpoints(db):
    """Create FHIR endpoints with database access"""
    
    # ============ Patient Endpoints ============
    
    @fhir_router.get("/Patient", response_model=FHIRBundle)
    async def search_patients(
        name: Optional[str] = Query(None),
        identifier: Optional[str] = Query(None),
        _count: int = Query(100, alias="_count")
    ):
        """Search for Patient resources"""
        query = {}
        if name:
            query["$or"] = [
                {"first_name": {"$regex": name, "$options": "i"}},
                {"last_name": {"$regex": name, "$options": "i"}}
            ]
        if identifier:
            query["mrn"] = identifier
        
        patients = await db.patients.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for p in patients:
            fhir_patient = patient_to_fhir(p)
            entries.append({
                "resource": fhir_patient.model_dump(),
                "fullUrl": f"Patient/{p['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/Patient/{patient_id}", response_model=FHIRPatient)
    async def get_patient(patient_id: str):
        """Get a single Patient resource by ID"""
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient_to_fhir(patient)
    
    # ============ Observation Endpoints ============
    
    @fhir_router.get("/Observation", response_model=FHIRBundle)
    async def search_observations(
        patient: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        _count: int = Query(100, alias="_count")
    ):
        """Search for Observation resources (vitals)"""
        query = {}
        if patient:
            # Extract patient ID from reference (Patient/xxx)
            patient_id = patient.replace("Patient/", "")
            query["patient_id"] = patient_id
        
        vitals = await db.vitals.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for v in vitals:
            fhir_obs = vitals_to_fhir_observation(v, v["patient_id"])
            entries.append({
                "resource": fhir_obs.model_dump(),
                "fullUrl": f"Observation/{v['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/Observation/{observation_id}", response_model=FHIRObservation)
    async def get_observation(observation_id: str):
        """Get a single Observation resource by ID"""
        vitals = await db.vitals.find_one({"id": observation_id}, {"_id": 0})
        if not vitals:
            raise HTTPException(status_code=404, detail="Observation not found")
        return vitals_to_fhir_observation(vitals, vitals["patient_id"])
    
    # ============ Condition Endpoints ============
    
    @fhir_router.get("/Condition", response_model=FHIRBundle)
    async def search_conditions(
        patient: Optional[str] = Query(None),
        clinical_status: Optional[str] = Query(None, alias="clinical-status"),
        _count: int = Query(100, alias="_count")
    ):
        """Search for Condition resources (problems)"""
        query = {}
        if patient:
            patient_id = patient.replace("Patient/", "")
            query["patient_id"] = patient_id
        if clinical_status:
            query["status"] = clinical_status
        
        problems = await db.problems.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for p in problems:
            fhir_condition = problem_to_fhir_condition(p, p["patient_id"])
            entries.append({
                "resource": fhir_condition.model_dump(),
                "fullUrl": f"Condition/{p['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/Condition/{condition_id}", response_model=FHIRCondition)
    async def get_condition(condition_id: str):
        """Get a single Condition resource by ID"""
        problem = await db.problems.find_one({"id": condition_id}, {"_id": 0})
        if not problem:
            raise HTTPException(status_code=404, detail="Condition not found")
        return problem_to_fhir_condition(problem, problem["patient_id"])
    
    # ============ MedicationRequest Endpoints ============
    
    @fhir_router.get("/MedicationRequest", response_model=FHIRBundle)
    async def search_medication_requests(
        patient: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        _count: int = Query(100, alias="_count")
    ):
        """Search for MedicationRequest resources"""
        query = {}
        if patient:
            patient_id = patient.replace("Patient/", "")
            query["patient_id"] = patient_id
        if status:
            query["status"] = status
        
        meds = await db.medications.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for m in meds:
            fhir_med = medication_to_fhir(m, m["patient_id"])
            entries.append({
                "resource": fhir_med.model_dump(),
                "fullUrl": f"MedicationRequest/{m['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/MedicationRequest/{medication_id}", response_model=FHIRMedicationRequest)
    async def get_medication_request(medication_id: str):
        """Get a single MedicationRequest resource by ID"""
        med = await db.medications.find_one({"id": medication_id}, {"_id": 0})
        if not med:
            raise HTTPException(status_code=404, detail="MedicationRequest not found")
        return medication_to_fhir(med, med["patient_id"])
    
    # ============ AllergyIntolerance Endpoints ============
    
    @fhir_router.get("/AllergyIntolerance", response_model=FHIRBundle)
    async def search_allergies(
        patient: Optional[str] = Query(None),
        _count: int = Query(100, alias="_count")
    ):
        """Search for AllergyIntolerance resources"""
        query = {}
        if patient:
            patient_id = patient.replace("Patient/", "")
            query["patient_id"] = patient_id
        
        allergies = await db.allergies.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for a in allergies:
            fhir_allergy = allergy_to_fhir(a, a["patient_id"])
            entries.append({
                "resource": fhir_allergy.model_dump(),
                "fullUrl": f"AllergyIntolerance/{a['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/AllergyIntolerance/{allergy_id}", response_model=FHIRAllergyIntolerance)
    async def get_allergy(allergy_id: str):
        """Get a single AllergyIntolerance resource by ID"""
        allergy = await db.allergies.find_one({"id": allergy_id}, {"_id": 0})
        if not allergy:
            raise HTTPException(status_code=404, detail="AllergyIntolerance not found")
        return allergy_to_fhir(allergy, allergy["patient_id"])
    
    # ============ ServiceRequest Endpoints ============
    
    @fhir_router.get("/ServiceRequest", response_model=FHIRBundle)
    async def search_service_requests(
        patient: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        _count: int = Query(100, alias="_count")
    ):
        """Search for ServiceRequest resources (orders)"""
        query = {}
        if patient:
            patient_id = patient.replace("Patient/", "")
            query["patient_id"] = patient_id
        if status:
            query["status"] = status
        if category:
            query["order_type"] = category
        
        orders = await db.orders.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for o in orders:
            fhir_order = order_to_fhir_service_request(o)
            entries.append({
                "resource": fhir_order.model_dump(),
                "fullUrl": f"ServiceRequest/{o['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/ServiceRequest/{order_id}", response_model=FHIRServiceRequest)
    async def get_service_request(order_id: str):
        """Get a single ServiceRequest resource by ID"""
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="ServiceRequest not found")
        return order_to_fhir_service_request(order)
    
    # ============ Appointment Endpoints ============
    
    @fhir_router.get("/Appointment", response_model=FHIRBundle)
    async def search_appointments(
        patient: Optional[str] = Query(None),
        date: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        _count: int = Query(100, alias="_count")
    ):
        """Search for Appointment resources"""
        query = {}
        if patient:
            patient_id = patient.replace("Patient/", "")
            query["patient_id"] = patient_id
        if date:
            query["date"] = date
        if status:
            query["status"] = status
        
        appointments = await db.appointments.find(query, {"_id": 0}).limit(_count).to_list(_count)
        
        entries = []
        for a in appointments:
            fhir_appt = appointment_to_fhir(a)
            entries.append({
                "resource": fhir_appt.model_dump(),
                "fullUrl": f"Appointment/{a['id']}"
            })
        
        return FHIRBundle(
            id=str(uuid.uuid4()),
            total=len(entries),
            entry=entries
        )
    
    @fhir_router.get("/Appointment/{appointment_id}", response_model=FHIRAppointment)
    async def get_appointment(appointment_id: str):
        """Get a single Appointment resource by ID"""
        appt = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appointment_to_fhir(appt)
    
    return fhir_router
