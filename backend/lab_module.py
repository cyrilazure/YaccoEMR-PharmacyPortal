"""
Lab Results Module for Yacco EMR
Supports:
- Lab order management
- Simulated/Demo lab result generation
- HL7 v2 ORU^R01 message parsing
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import random
import re

lab_router = APIRouter(prefix="/api/lab", tags=["Lab Results"])

# ============ Lab Test Definitions ============

# Reference ranges for common lab tests
LAB_TEST_DEFINITIONS = {
    # Complete Blood Count (CBC)
    "WBC": {"name": "White Blood Cell Count", "unit": "K/uL", "low": 4.5, "high": 11.0, "category": "CBC"},
    "RBC": {"name": "Red Blood Cell Count", "unit": "M/uL", "low": 4.5, "high": 5.5, "category": "CBC"},
    "HGB": {"name": "Hemoglobin", "unit": "g/dL", "low": 12.0, "high": 17.5, "category": "CBC"},
    "HCT": {"name": "Hematocrit", "unit": "%", "low": 36.0, "high": 50.0, "category": "CBC"},
    "MCV": {"name": "Mean Corpuscular Volume", "unit": "fL", "low": 80.0, "high": 100.0, "category": "CBC"},
    "MCH": {"name": "Mean Corpuscular Hemoglobin", "unit": "pg", "low": 27.0, "high": 33.0, "category": "CBC"},
    "MCHC": {"name": "Mean Corpuscular Hemoglobin Concentration", "unit": "g/dL", "low": 32.0, "high": 36.0, "category": "CBC"},
    "PLT": {"name": "Platelet Count", "unit": "K/uL", "low": 150.0, "high": 400.0, "category": "CBC"},
    
    # Comprehensive Metabolic Panel (CMP)
    "GLU": {"name": "Glucose", "unit": "mg/dL", "low": 70.0, "high": 100.0, "category": "CMP"},
    "BUN": {"name": "Blood Urea Nitrogen", "unit": "mg/dL", "low": 7.0, "high": 20.0, "category": "CMP"},
    "CREAT": {"name": "Creatinine", "unit": "mg/dL", "low": 0.6, "high": 1.2, "category": "CMP"},
    "NA": {"name": "Sodium", "unit": "mEq/L", "low": 136.0, "high": 145.0, "category": "CMP"},
    "K": {"name": "Potassium", "unit": "mEq/L", "low": 3.5, "high": 5.0, "category": "CMP"},
    "CL": {"name": "Chloride", "unit": "mEq/L", "low": 98.0, "high": 106.0, "category": "CMP"},
    "CO2": {"name": "Carbon Dioxide", "unit": "mEq/L", "low": 23.0, "high": 29.0, "category": "CMP"},
    "CA": {"name": "Calcium", "unit": "mg/dL", "low": 8.5, "high": 10.5, "category": "CMP"},
    "TBIL": {"name": "Total Bilirubin", "unit": "mg/dL", "low": 0.1, "high": 1.2, "category": "CMP"},
    "ALK": {"name": "Alkaline Phosphatase", "unit": "U/L", "low": 44.0, "high": 147.0, "category": "CMP"},
    "AST": {"name": "Aspartate Aminotransferase", "unit": "U/L", "low": 10.0, "high": 40.0, "category": "CMP"},
    "ALT": {"name": "Alanine Aminotransferase", "unit": "U/L", "low": 7.0, "high": 56.0, "category": "CMP"},
    "ALB": {"name": "Albumin", "unit": "g/dL", "low": 3.5, "high": 5.0, "category": "CMP"},
    "TP": {"name": "Total Protein", "unit": "g/dL", "low": 6.0, "high": 8.3, "category": "CMP"},
    "EGFR": {"name": "Estimated GFR", "unit": "mL/min/1.73m²", "low": 90.0, "high": 120.0, "category": "CMP"},
    
    # Lipid Panel
    "CHOL": {"name": "Total Cholesterol", "unit": "mg/dL", "low": 0.0, "high": 200.0, "category": "LIPID"},
    "TRIG": {"name": "Triglycerides", "unit": "mg/dL", "low": 0.0, "high": 150.0, "category": "LIPID"},
    "HDL": {"name": "HDL Cholesterol", "unit": "mg/dL", "low": 40.0, "high": 60.0, "category": "LIPID"},
    "LDL": {"name": "LDL Cholesterol", "unit": "mg/dL", "low": 0.0, "high": 100.0, "category": "LIPID"},
    "VLDL": {"name": "VLDL Cholesterol", "unit": "mg/dL", "low": 5.0, "high": 40.0, "category": "LIPID"},
    
    # Thyroid Panel
    "TSH": {"name": "Thyroid Stimulating Hormone", "unit": "mIU/L", "low": 0.4, "high": 4.0, "category": "THYROID"},
    "T4": {"name": "Thyroxine (T4)", "unit": "ug/dL", "low": 4.5, "high": 12.0, "category": "THYROID"},
    "T3": {"name": "Triiodothyronine (T3)", "unit": "ng/dL", "low": 80.0, "high": 200.0, "category": "THYROID"},
    "FT4": {"name": "Free T4", "unit": "ng/dL", "low": 0.8, "high": 1.8, "category": "THYROID"},
    
    # Coagulation
    "PT": {"name": "Prothrombin Time", "unit": "seconds", "low": 11.0, "high": 13.5, "category": "COAG"},
    "INR": {"name": "International Normalized Ratio", "unit": "", "low": 0.9, "high": 1.1, "category": "COAG"},
    "PTT": {"name": "Partial Thromboplastin Time", "unit": "seconds", "low": 25.0, "high": 35.0, "category": "COAG"},
    
    # Hemoglobin A1C
    "HBA1C": {"name": "Hemoglobin A1C", "unit": "%", "low": 4.0, "high": 5.6, "category": "DIABETES"},
    
    # Cardiac Markers
    "TROP": {"name": "Troponin I", "unit": "ng/mL", "low": 0.0, "high": 0.04, "category": "CARDIAC"},
    "BNP": {"name": "B-Type Natriuretic Peptide", "unit": "pg/mL", "low": 0.0, "high": 100.0, "category": "CARDIAC"},
    
    # Urinalysis
    "UA_PH": {"name": "Urine pH", "unit": "", "low": 4.5, "high": 8.0, "category": "UA"},
    "UA_SG": {"name": "Specific Gravity", "unit": "", "low": 1.005, "high": 1.030, "category": "UA"},
    "UA_PRO": {"name": "Urine Protein", "unit": "", "low": 0.0, "high": 0.0, "category": "UA"},
    "UA_GLU": {"name": "Urine Glucose", "unit": "", "low": 0.0, "high": 0.0, "category": "UA"},
}

# Lab order panels
LAB_PANELS = {
    "CBC": ["WBC", "RBC", "HGB", "HCT", "MCV", "MCH", "MCHC", "PLT"],
    "CMP": ["GLU", "BUN", "CREAT", "NA", "K", "CL", "CO2", "CA", "TBIL", "ALK", "AST", "ALT", "ALB", "TP", "EGFR"],
    "BMP": ["GLU", "BUN", "CREAT", "NA", "K", "CL", "CO2", "CA"],
    "LIPID": ["CHOL", "TRIG", "HDL", "LDL", "VLDL"],
    "THYROID": ["TSH", "T4", "T3", "FT4"],
    "COAG": ["PT", "INR", "PTT"],
    "CARDIAC": ["TROP", "BNP"],
    "UA": ["UA_PH", "UA_SG", "UA_PRO", "UA_GLU"],
    "HBA1C": ["HBA1C"],
}

# ============ Enums ============

class LabOrderStatus(str, Enum):
    ORDERED = "ordered"
    COLLECTED = "collected"
    IN_PROGRESS = "in_progress"
    RESULTED = "resulted"
    CANCELLED = "cancelled"

class ResultFlag(str, Enum):
    NORMAL = "N"
    LOW = "L"
    HIGH = "H"
    CRITICAL_LOW = "LL"
    CRITICAL_HIGH = "HH"
    ABNORMAL = "A"

# ============ Models ============

class LabOrderCreate(BaseModel):
    patient_id: str
    patient_name: str
    ordering_provider_id: str
    ordering_provider_name: str
    panel_code: str  # CBC, CMP, LIPID, etc.
    panel_name: str
    priority: str = "routine"  # routine, stat, urgent
    clinical_notes: Optional[str] = None
    diagnosis: Optional[str] = None
    fasting_required: bool = False

class LabOrder(LabOrderCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    accession_number: str = Field(default_factory=lambda: f"LAB{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}")
    status: LabOrderStatus = LabOrderStatus.ORDERED
    ordered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    collected_at: Optional[datetime] = None
    resulted_at: Optional[datetime] = None
    test_codes: List[str] = []

class LabResultValue(BaseModel):
    test_code: str
    test_name: str
    value: float
    unit: str
    reference_low: float
    reference_high: float
    flag: ResultFlag
    notes: Optional[str] = None

class LabResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    accession_number: str
    patient_id: str
    patient_name: str
    panel_code: str
    panel_name: str
    results: List[LabResultValue]
    performing_lab: str = "Yacco Clinical Laboratory"
    resulted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_by: Optional[str] = None
    notes: Optional[str] = None
    is_final: bool = True

class HL7ORUMessage(BaseModel):
    raw_message: str
    sending_application: Optional[str] = None
    sending_facility: Optional[str] = None

class HL7ParsedResult(BaseModel):
    message_id: str
    patient_id: str
    patient_name: str
    accession_number: str
    results: List[LabResultValue]
    observation_datetime: str
    performing_lab: str
    status: str

# ============ Helper Functions ============

def generate_result_value(test_code: str, scenario: str = "normal") -> float:
    """Generate a realistic lab value based on scenario"""
    test_def = LAB_TEST_DEFINITIONS.get(test_code)
    if not test_def:
        return 0.0
    
    low = test_def["low"]
    high = test_def["high"]
    mid = (low + high) / 2
    range_width = high - low
    
    if scenario == "normal":
        # 70% of values within middle 50% of range
        return round(random.uniform(low + range_width * 0.25, high - range_width * 0.25), 2)
    elif scenario == "borderline_high":
        return round(random.uniform(high - range_width * 0.1, high + range_width * 0.2), 2)
    elif scenario == "borderline_low":
        return round(random.uniform(low - range_width * 0.2, low + range_width * 0.1), 2)
    elif scenario == "abnormal_high":
        return round(random.uniform(high * 1.2, high * 1.8), 2)
    elif scenario == "abnormal_low":
        return round(random.uniform(low * 0.4, low * 0.8), 2)
    else:
        return round(random.uniform(low, high), 2)

def get_result_flag(value: float, low: float, high: float) -> ResultFlag:
    """Determine result flag based on value and reference range"""
    if value < low * 0.5:
        return ResultFlag.CRITICAL_LOW
    elif value < low:
        return ResultFlag.LOW
    elif value > high * 1.5:
        return ResultFlag.CRITICAL_HIGH
    elif value > high:
        return ResultFlag.HIGH
    else:
        return ResultFlag.NORMAL

def parse_hl7_oru_message(raw_message: str) -> Optional[HL7ParsedResult]:
    """
    Parse HL7 v2 ORU^R01 message (Observation Result)
    
    Sample ORU^R01 message structure:
    MSH|^~\&|LAB_SYSTEM|LAB_FACILITY|EMR|HOSPITAL|20240115120000||ORU^R01|MSG001|P|2.5.1
    PID|1||12345^^^HOSP^MR||DOE^JOHN^A||19800101|M
    OBR|1|ORD001|ACC001|CBC^Complete Blood Count|||20240115100000
    OBX|1|NM|WBC^White Blood Cell Count||7.5|K/uL|4.5-11.0|N|||F
    OBX|2|NM|RBC^Red Blood Cell Count||4.8|M/uL|4.5-5.5|N|||F
    """
    try:
        lines = raw_message.strip().split('\n')
        segments = {}
        obx_segments = []
        
        for line in lines:
            fields = line.split('|')
            segment_type = fields[0]
            
            if segment_type == 'MSH':
                segments['MSH'] = fields
            elif segment_type == 'PID':
                segments['PID'] = fields
            elif segment_type == 'OBR':
                segments['OBR'] = fields
            elif segment_type == 'OBX':
                obx_segments.append(fields)
        
        if not segments.get('MSH') or not segments.get('PID') or not segments.get('OBR'):
            return None
        
        # Parse patient info from PID
        pid = segments['PID']
        patient_id = pid[3].split('^')[0] if len(pid) > 3 else "UNKNOWN"
        patient_name_parts = pid[5].split('^') if len(pid) > 5 else ["UNKNOWN"]
        patient_name = f"{patient_name_parts[1] if len(patient_name_parts) > 1 else ''} {patient_name_parts[0]}".strip()
        
        # Parse order info from OBR
        obr = segments['OBR']
        accession_number = obr[3] if len(obr) > 3 else f"ACC{uuid.uuid4().hex[:8].upper()}"
        observation_datetime = obr[7] if len(obr) > 7 else datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Parse MSH for lab info
        msh = segments['MSH']
        performing_lab = msh[4] if len(msh) > 4 else "External Laboratory"
        message_id = msh[10] if len(msh) > 10 else str(uuid.uuid4())
        
        # Parse results from OBX segments
        results = []
        for obx in obx_segments:
            if len(obx) < 6:
                continue
            
            test_info = obx[3].split('^')
            test_code = test_info[0]
            test_name = test_info[1] if len(test_info) > 1 else test_code
            
            try:
                value = float(obx[5]) if obx[5] else 0.0
            except ValueError:
                continue
            
            unit = obx[6] if len(obx) > 6 else ""
            
            # Parse reference range
            ref_range = obx[7] if len(obx) > 7 else ""
            ref_parts = ref_range.split('-')
            ref_low = float(ref_parts[0]) if len(ref_parts) > 0 and ref_parts[0] else 0.0
            ref_high = float(ref_parts[1]) if len(ref_parts) > 1 else ref_low * 2
            
            flag_str = obx[8] if len(obx) > 8 else "N"
            flag_map = {"N": ResultFlag.NORMAL, "L": ResultFlag.LOW, "H": ResultFlag.HIGH, 
                       "LL": ResultFlag.CRITICAL_LOW, "HH": ResultFlag.CRITICAL_HIGH, "A": ResultFlag.ABNORMAL}
            flag = flag_map.get(flag_str, ResultFlag.NORMAL)
            
            results.append(LabResultValue(
                test_code=test_code,
                test_name=test_name,
                value=value,
                unit=unit,
                reference_low=ref_low,
                reference_high=ref_high,
                flag=flag
            ))
        
        return HL7ParsedResult(
            message_id=message_id,
            patient_id=patient_id,
            patient_name=patient_name,
            accession_number=accession_number,
            results=results,
            observation_datetime=observation_datetime,
            performing_lab=performing_lab,
            status="final"
        )
    
    except Exception as e:
        print(f"Error parsing HL7 ORU message: {e}")
        return None

def generate_hl7_ack(message_id: str, status: str = "AA") -> str:
    """Generate HL7 ACK message"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    ack_id = f"ACK{uuid.uuid4().hex[:8].upper()}"
    
    return f"""MSH|^~\\&|YACCO_EMR|HOSPITAL|LAB_SYSTEM|LAB_FACILITY|{timestamp}||ACK|{ack_id}|P|2.5.1
MSA|{status}|{message_id}|Message Accepted"""

# ============ API Factory ============

def create_lab_endpoints(db, get_current_user):
    """Create lab API endpoints with database dependency"""
    
    @lab_router.post("/orders", response_model=dict)
    async def create_lab_order(order: LabOrderCreate, user: dict = Depends(get_current_user)):
        """Create a new lab order"""
        # Get test codes for the panel
        test_codes = LAB_PANELS.get(order.panel_code.upper(), [])
        
        lab_order = LabOrder(
            **order.model_dump(),
            test_codes=test_codes
        )
        
        order_dict = lab_order.model_dump()
        order_dict['ordered_at'] = order_dict['ordered_at'].isoformat()
        
        await db["lab_orders"].insert_one(order_dict)
        
        return {"message": "Lab order created", "order": order_dict}
    
    @lab_router.get("/orders/{patient_id}", response_model=dict)
    async def get_patient_lab_orders(patient_id: str, status: Optional[str] = None, user: dict = Depends(get_current_user)):
        """Get all lab orders for a patient"""
        query = {"patient_id": patient_id}
        if status:
            query["status"] = status
        
        orders = await db["lab_orders"].find(query, {"_id": 0}).sort("ordered_at", -1).to_list(100)
        return {"orders": orders}
    
    @lab_router.get("/orders", response_model=dict)
    async def get_all_lab_orders(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = Query(default=50, le=200),
        user: dict = Depends(get_current_user)
    ):
        """Get all lab orders with optional filters"""
        query = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        
        orders = await db["lab_orders"].find(query, {"_id": 0}).sort("ordered_at", -1).to_list(limit)
        return {"orders": orders}
    
    @lab_router.put("/orders/{order_id}/status", response_model=dict)
    async def update_lab_order_status(order_id: str, status: LabOrderStatus, user: dict = Depends(get_current_user)):
        """Update lab order status"""
        update_data = {"status": status.value}
        
        if status == LabOrderStatus.COLLECTED:
            update_data["collected_at"] = datetime.now(timezone.utc).isoformat()
        elif status == LabOrderStatus.RESULTED:
            update_data["resulted_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db["lab_orders"].update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Lab order not found")
        
        return {"message": f"Lab order status updated to {status.value}"}
    
    @lab_router.post("/results/simulate/{order_id}", response_model=dict)
    async def simulate_lab_results(
        order_id: str, 
        scenario: str = Query(default="normal", description="Result scenario: normal, borderline_high, borderline_low, abnormal_high, abnormal_low, mixed"),
        user: dict = Depends(get_current_user)
    ):
        """Generate simulated lab results for an order (Demo Mode)"""
        # Get the lab order
        order = await db["lab_orders"].find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Lab order not found")
        
        # Generate results
        results = []
        test_codes = order.get("test_codes", LAB_PANELS.get(order.get("panel_code", "CBC").upper(), ["WBC"]))
        
        for test_code in test_codes:
            test_def = LAB_TEST_DEFINITIONS.get(test_code)
            if not test_def:
                continue
            
            # For mixed scenario, randomly pick a scenario for each test
            test_scenario = scenario
            if scenario == "mixed":
                test_scenario = random.choice(["normal", "normal", "normal", "borderline_high", "borderline_low", "abnormal_high"])
            
            value = generate_result_value(test_code, test_scenario)
            flag = get_result_flag(value, test_def["low"], test_def["high"])
            
            results.append(LabResultValue(
                test_code=test_code,
                test_name=test_def["name"],
                value=value,
                unit=test_def["unit"],
                reference_low=test_def["low"],
                reference_high=test_def["high"],
                flag=flag
            ))
        
        # Create lab result document
        lab_result = LabResult(
            order_id=order_id,
            accession_number=order.get("accession_number", f"LAB{uuid.uuid4().hex[:8].upper()}"),
            patient_id=order.get("patient_id"),
            patient_name=order.get("patient_name"),
            panel_code=order.get("panel_code"),
            panel_name=order.get("panel_name"),
            results=results,
            notes=f"Simulated results - {scenario} scenario"
        )
        
        result_dict = lab_result.model_dump()
        result_dict['resulted_at'] = result_dict['resulted_at'].isoformat()
        result_dict['results'] = [r.model_dump() for r in results]
        
        await db["lab_results"].insert_one(result_dict)
        
        # Update order status
        await db["lab_orders"].update_one(
            {"id": order_id},
            {"$set": {
                "status": LabOrderStatus.RESULTED.value,
                "resulted_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Lab results generated", "result": result_dict}
    
    @lab_router.get("/results/{patient_id}", response_model=dict)
    async def get_patient_lab_results(patient_id: str, panel_code: Optional[str] = None, user: dict = Depends(get_current_user)):
        """Get all lab results for a patient"""
        query = {"patient_id": patient_id}
        if panel_code:
            query["panel_code"] = panel_code.upper()
        
        results = await db["lab_results"].find(query, {"_id": 0}).sort("resulted_at", -1).to_list(100)
        return {"results": results}
    
    @lab_router.get("/results/order/{order_id}", response_model=dict)
    async def get_lab_result_by_order(order_id: str, user: dict = Depends(get_current_user)):
        """Get lab result for a specific order"""
        result = await db["lab_results"].find_one({"order_id": order_id}, {"_id": 0})
        if not result:
            raise HTTPException(status_code=404, detail="Lab result not found")
        return {"result": result}
    
    @lab_router.post("/hl7/oru", response_model=dict)
    async def receive_hl7_oru_message(message: HL7ORUMessage, user: dict = Depends(get_current_user)):
        """
        Receive and parse HL7 v2 ORU^R01 message (Lab Results)
        
        ORU^R01 - Observation Result / Unsolicited Transmission
        This is the standard HL7 message type for lab results.
        """
        parsed = parse_hl7_oru_message(message.raw_message)
        
        if not parsed:
            ack = generate_hl7_ack("UNKNOWN", "AE")  # Application Error
            raise HTTPException(status_code=400, detail={
                "error": "Failed to parse HL7 ORU message",
                "ack": ack
            })
        
        # Store the parsed message
        hl7_doc = {
            "id": str(uuid.uuid4()),
            "message_type": "ORU^R01",
            "message_id": parsed.message_id,
            "raw_message": message.raw_message,
            "sending_application": message.sending_application,
            "sending_facility": message.sending_facility,
            "parsed_data": parsed.model_dump(),
            "received_at": datetime.now(timezone.utc).isoformat(),
            "status": "processed"
        }
        await db["hl7_messages"].insert_one(hl7_doc)
        
        # Try to match with existing order or create new result
        # First, try to find patient
        patient = await db["patients"].find_one({"mrn": parsed.patient_id}, {"_id": 0})
        if not patient:
            # Try by ID
            patient = await db["patients"].find_one({"id": parsed.patient_id}, {"_id": 0})
        
        patient_id = patient.get("id") if patient else parsed.patient_id
        patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() if patient else parsed.patient_name
        
        # Create lab result from HL7 message
        lab_result = {
            "id": str(uuid.uuid4()),
            "order_id": None,  # External result - no matching order
            "accession_number": parsed.accession_number,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "panel_code": "EXTERNAL",
            "panel_name": "External Lab Result",
            "results": [r.model_dump() for r in parsed.results],
            "performing_lab": parsed.performing_lab,
            "resulted_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Received via HL7 ORU^R01 from {parsed.performing_lab}",
            "is_final": True,
            "source": "HL7"
        }
        
        await db["lab_results"].insert_one(lab_result)
        
        # Generate ACK
        ack = generate_hl7_ack(parsed.message_id, "AA")  # Application Accept
        
        return {
            "message": "HL7 ORU message processed successfully",
            "result_id": lab_result["id"],
            "patient_matched": patient is not None,
            "tests_received": len(parsed.results),
            "ack": ack
        }
    
    @lab_router.get("/panels", response_model=dict)
    async def get_available_lab_panels(user: dict = Depends(get_current_user)):
        """Get list of available lab panels"""
        panels = []
        for code, tests in LAB_PANELS.items():
            test_details = []
            for test_code in tests:
                test_def = LAB_TEST_DEFINITIONS.get(test_code)
                if test_def:
                    test_details.append({
                        "code": test_code,
                        "name": test_def["name"],
                        "unit": test_def["unit"]
                    })
            
            panels.append({
                "code": code,
                "name": get_panel_name(code),
                "tests": test_details,
                "test_count": len(tests)
            })
        
        return {"panels": panels}
    
    @lab_router.get("/test-definitions", response_model=dict)
    async def get_lab_test_definitions(category: Optional[str] = None, user: dict = Depends(get_current_user)):
        """Get lab test definitions and reference ranges"""
        if category:
            tests = {k: v for k, v in LAB_TEST_DEFINITIONS.items() if v.get("category") == category.upper()}
        else:
            tests = LAB_TEST_DEFINITIONS
        
        return {"tests": tests}
    
    return lab_router

def get_panel_name(code: str) -> str:
    """Get human-readable panel name"""
    names = {
        "CBC": "Complete Blood Count",
        "CMP": "Comprehensive Metabolic Panel",
        "BMP": "Basic Metabolic Panel",
        "LIPID": "Lipid Panel",
        "THYROID": "Thyroid Panel",
        "COAG": "Coagulation Panel",
        "CARDIAC": "Cardiac Markers",
        "UA": "Urinalysis",
        "HBA1C": "Hemoglobin A1C"
    }
    return names.get(code, code)
