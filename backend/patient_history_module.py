"""
Patient History Module for Yacco Health EMR
============================================
Provides comprehensive view of a patient's medical history including:
- Chronic conditions (diabetes, hypertension, etc.)
- Past diagnoses and procedures
- Medication history
- Vital signs trends
- Lab results history
- Imaging history
- Allergies
- Family history
- Timeline of all medical events
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from enum import Enum
import logging

from security import get_current_user, TokenPayload, audit_log

logger = logging.getLogger(__name__)


# ============== Enums ==============

class ConditionType(str, Enum):
    CHRONIC = "chronic"
    ACUTE = "acute"
    SURGICAL = "surgical"
    ALLERGY = "allergy"
    FAMILY_HISTORY = "family_history"
    SOCIAL_HISTORY = "social_history"


class ConditionStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MANAGED = "managed"
    IN_REMISSION = "in_remission"


# ============== Pydantic Models ==============

class MedicalConditionCreate(BaseModel):
    """Create a medical condition entry"""
    condition_type: ConditionType
    condition_name: str
    icd_code: Optional[str] = None
    description: Optional[str] = None
    onset_date: Optional[str] = None
    severity: Optional[str] = None
    current_treatment: Optional[str] = None
    medications: Optional[List[str]] = None
    family_member_relationship: Optional[str] = None  # For family history
    notes: Optional[str] = None


class MedicalConditionUpdate(BaseModel):
    """Update a medical condition"""
    status: Optional[ConditionStatus] = None
    resolved_date: Optional[str] = None
    severity: Optional[str] = None
    current_treatment: Optional[str] = None
    medications: Optional[List[str]] = None
    notes: Optional[str] = None


class VitalTrend(BaseModel):
    """Vital sign trend data"""
    date: str
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None


# ============== Module Factory ==============

def create_patient_history_router(db) -> APIRouter:
    """Create the patient history router with database dependency"""
    
    router = APIRouter(prefix="/api/patients", tags=["Patient History"])
    
    # ============== Helper Functions ==============
    
    async def get_patient(patient_id: str) -> dict:
        """Get patient details"""
        patient = await db["patients"].find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    
    async def verify_patient_access(patient_id: str, user: TokenPayload) -> dict:
        """Verify user has access to patient data"""
        patient = await get_patient(patient_id)
        
        # Check organization match (except for super_admin/platform_owner)
        if user.role not in ['super_admin', 'platform_owner']:
            if patient.get('organization_id') != user.organization_id:
                raise HTTPException(status_code=403, detail="Access denied to this patient")
        
        return patient
    
    # ============== Comprehensive History Endpoint ==============
    
    @router.get("/{patient_id}/history", response_model=dict)
    async def get_patient_history(
        patient_id: str,
        include_vitals: bool = True,
        include_labs: bool = True,
        include_imaging: bool = True,
        include_prescriptions: bool = True,
        include_encounters: bool = True,
        days_back: int = Query(365, description="How many days of history to fetch"),
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        Get comprehensive patient history including all medical data.
        Returns a complete view of the patient's medical history.
        """
        patient = await verify_patient_access(patient_id, current_user)
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        cutoff_str = cutoff_date.isoformat()
        
        history = {
            "patient": {
                "id": patient["id"],
                "mrn": patient.get("mrn"),
                "name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip(),
                "date_of_birth": patient.get("date_of_birth"),
                "gender": patient.get("gender"),
                "blood_type": patient.get("blood_type"),
                "phone": patient.get("phone"),
                "emergency_contact": patient.get("emergency_contact")
            },
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Get chronic conditions and medical history
        conditions = await db["patient_medical_history"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("onset_date", -1).to_list(100)
        
        # Categorize conditions
        chronic_conditions = [c for c in conditions if c.get("condition_type") == "chronic"]
        past_diagnoses = [c for c in conditions if c.get("condition_type") in ["acute", "surgical"]]
        family_history = [c for c in conditions if c.get("condition_type") == "family_history"]
        social_history = [c for c in conditions if c.get("condition_type") == "social_history"]
        
        history["chronic_conditions"] = chronic_conditions
        history["past_diagnoses"] = past_diagnoses
        history["family_history"] = family_history
        history["social_history"] = social_history
        
        # Get allergies
        allergies = await db["allergies"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).to_list(50)
        history["allergies"] = allergies
        
        # Get current medications
        medications = await db["medications"].find(
            {"patient_id": patient_id, "status": "active"},
            {"_id": 0}
        ).to_list(100)
        history["current_medications"] = medications
        
        # Get vital signs (trending data)
        if include_vitals:
            vitals = await db["vitals"].find(
                {"patient_id": patient_id},
                {"_id": 0}
            ).sort("recorded_at", -1).to_list(50)
            history["vitals"] = vitals
            
            # Calculate vital trends (averages for charts)
            if vitals:
                history["vital_trends"] = calculate_vital_trends(vitals)
        
        # Get lab results
        if include_labs:
            labs = await db["lab_results"].find(
                {"patient_id": patient_id},
                {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            history["lab_results"] = labs
        
        # Get imaging studies
        if include_imaging:
            imaging = await db["radiology_orders"].find(
                {"patient_id": patient_id},
                {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            history["imaging_studies"] = imaging
        
        # Get prescription history
        if include_prescriptions:
            prescriptions = await db["prescriptions"].find(
                {"patient_id": patient_id},
                {"_id": 0}
            ).sort("created_at", -1).to_list(100)
            history["prescriptions"] = prescriptions
        
        # Get clinical notes / encounters
        if include_encounters:
            notes = await db["clinical_notes"].find(
                {"patient_id": patient_id},
                {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            history["clinical_notes"] = notes
        
        # Get problems list
        problems = await db["problems"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        history["problems"] = problems
        
        # Calculate summary statistics
        history["summary"] = {
            "total_chronic_conditions": len(chronic_conditions),
            "active_conditions": len([c for c in chronic_conditions if c.get("status") == "active"]),
            "total_allergies": len(allergies),
            "current_medications_count": len(medications),
            "total_lab_tests": len(history.get("lab_results", [])),
            "total_imaging_studies": len(history.get("imaging_studies", [])),
            "total_prescriptions": len(history.get("prescriptions", []))
        }
        
        return history
    
    # ============== Medical Conditions ==============
    
    @router.get("/{patient_id}/conditions", response_model=dict)
    async def get_patient_conditions(
        patient_id: str,
        condition_type: Optional[str] = None,
        status: Optional[str] = None,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get patient's medical conditions"""
        await verify_patient_access(patient_id, current_user)
        
        query = {"patient_id": patient_id}
        if condition_type:
            query["condition_type"] = condition_type
        if status:
            query["status"] = status
        
        conditions = await db["patient_medical_history"].find(
            query, {"_id": 0}
        ).sort("onset_date", -1).to_list(100)
        
        return {
            "patient_id": patient_id,
            "conditions": conditions,
            "total": len(conditions)
        }
    
    @router.post("/{patient_id}/conditions", response_model=dict)
    @audit_log("PATIENT_HISTORY", "ADD_CONDITION", "patient_medical_history")
    async def add_patient_condition(
        patient_id: str,
        condition: MedicalConditionCreate,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Add a new medical condition to patient history"""
        patient = await verify_patient_access(patient_id, current_user)
        
        now = datetime.now(timezone.utc)
        
        condition_doc = {
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "organization_id": current_user.organization_id,
            "condition_type": condition.condition_type.value,
            "condition_name": condition.condition_name,
            "icd_code": condition.icd_code,
            "description": condition.description,
            "onset_date": condition.onset_date,
            "severity": condition.severity,
            "status": "active",
            "current_treatment": condition.current_treatment,
            "medications": condition.medications,
            "family_member_relationship": condition.family_member_relationship,
            "notes": condition.notes,
            "recorded_by": current_user.user_id,
            "recorded_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await db["patient_medical_history"].insert_one(condition_doc)
        condition_doc.pop("_id", None)
        
        logger.info(f"Added condition {condition.condition_name} for patient {patient_id}")
        
        return {
            "success": True,
            "message": "Medical condition added successfully",
            "condition": condition_doc
        }
    
    @router.put("/{patient_id}/conditions/{condition_id}", response_model=dict)
    @audit_log("PATIENT_HISTORY", "UPDATE_CONDITION", "patient_medical_history")
    async def update_patient_condition(
        patient_id: str,
        condition_id: str,
        update: MedicalConditionUpdate,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Update a medical condition"""
        await verify_patient_access(patient_id, current_user)
        
        # Verify condition exists
        condition = await db["patient_medical_history"].find_one({
            "id": condition_id,
            "patient_id": patient_id
        })
        
        if not condition:
            raise HTTPException(status_code=404, detail="Condition not found")
        
        updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if update.status:
            updates["status"] = update.status.value
        if update.resolved_date:
            updates["resolved_date"] = update.resolved_date
        if update.severity:
            updates["severity"] = update.severity
        if update.current_treatment:
            updates["current_treatment"] = update.current_treatment
        if update.medications:
            updates["medications"] = update.medications
        if update.notes:
            updates["notes"] = update.notes
        
        await db["patient_medical_history"].update_one(
            {"id": condition_id},
            {"$set": updates}
        )
        
        return {
            "success": True,
            "message": "Condition updated successfully",
            "condition_id": condition_id
        }
    
    # ============== Vital Signs ==============
    
    @router.get("/{patient_id}/vitals", response_model=dict)
    async def get_patient_vitals(
        patient_id: str,
        limit: int = Query(50, le=200),
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get patient's vital signs history"""
        await verify_patient_access(patient_id, current_user)
        
        vitals = await db["vitals"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).sort("recorded_at", -1).to_list(limit)
        
        # Calculate trends
        trends = calculate_vital_trends(vitals) if vitals else {}
        
        return {
            "patient_id": patient_id,
            "vitals": vitals,
            "trends": trends,
            "total": len(vitals)
        }
    
    @router.get("/{patient_id}/vitals/latest", response_model=dict)
    async def get_latest_vitals(
        patient_id: str,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get patient's most recent vital signs"""
        await verify_patient_access(patient_id, current_user)
        
        vital = await db["vitals"].find_one(
            {"patient_id": patient_id},
            {"_id": 0},
            sort=[("recorded_at", -1)]
        )
        
        return {
            "patient_id": patient_id,
            "vitals": vital
        }
    
    # ============== Timeline ==============
    
    @router.get("/{patient_id}/timeline", response_model=dict)
    async def get_patient_timeline(
        patient_id: str,
        days_back: int = Query(90, description="Days of history"),
        limit: int = Query(100, le=500),
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        Get a unified timeline of all patient events.
        Combines conditions, vitals, labs, prescriptions, notes into a single timeline.
        """
        await verify_patient_access(patient_id, current_user)
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        timeline_events = []
        
        # Get conditions
        conditions = await db["patient_medical_history"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).to_list(100)
        
        for c in conditions:
            timeline_events.append({
                "type": "condition",
                "subtype": c.get("condition_type"),
                "date": c.get("recorded_at") or c.get("onset_date"),
                "title": c.get("condition_name"),
                "description": c.get("description"),
                "status": c.get("status"),
                "severity": c.get("severity"),
                "id": c.get("id")
            })
        
        # Get prescriptions
        prescriptions = await db["prescriptions"].find(
            {"patient_id": patient_id},
            {"_id": 0, "medications": 1, "created_at": 1, "id": 1, "status": 1}
        ).to_list(100)
        
        for p in prescriptions:
            meds = p.get("medications", [])
            med_names = [m.get("name", "Unknown") for m in meds[:3]] if isinstance(meds, list) else []
            timeline_events.append({
                "type": "prescription",
                "date": p.get("created_at"),
                "title": f"Prescription: {', '.join(med_names)}" if med_names else "Prescription",
                "description": f"{len(meds)} medication(s) prescribed",
                "status": p.get("status"),
                "id": p.get("id")
            })
        
        # Get lab results
        labs = await db["lab_results"].find(
            {"patient_id": patient_id},
            {"_id": 0, "created_at": 1, "id": 1, "status": 1}
        ).to_list(50)
        
        for l in labs:
            timeline_events.append({
                "type": "lab_result",
                "date": l.get("created_at"),
                "title": "Lab Results",
                "status": l.get("status"),
                "id": l.get("id")
            })
        
        # Get imaging
        imaging = await db["radiology_orders"].find(
            {"patient_id": patient_id},
            {"_id": 0, "study_type": 1, "modality": 1, "created_at": 1, "id": 1, "status": 1}
        ).to_list(50)
        
        for i in imaging:
            timeline_events.append({
                "type": "imaging",
                "date": i.get("created_at"),
                "title": f"{i.get('modality', 'Imaging')}: {i.get('study_type', 'Study')}",
                "status": i.get("status"),
                "id": i.get("id")
            })
        
        # Get clinical notes
        notes = await db["clinical_notes"].find(
            {"patient_id": patient_id},
            {"_id": 0, "note_type": 1, "title": 1, "created_at": 1, "id": 1, "author_name": 1}
        ).to_list(50)
        
        for n in notes:
            timeline_events.append({
                "type": "clinical_note",
                "subtype": n.get("note_type"),
                "date": n.get("created_at"),
                "title": n.get("title") or f"{n.get('note_type', 'Clinical')} Note",
                "description": f"By {n.get('author_name', 'Unknown')}",
                "id": n.get("id")
            })
        
        # Sort by date (newest first)
        timeline_events.sort(
            key=lambda x: x.get("date") or "1970-01-01",
            reverse=True
        )
        
        return {
            "patient_id": patient_id,
            "timeline": timeline_events[:limit],
            "total_events": len(timeline_events)
        }
    
    # ============== Allergies ==============
    
    @router.get("/{patient_id}/allergies", response_model=dict)
    async def get_patient_allergies(
        patient_id: str,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get patient's allergies"""
        await verify_patient_access(patient_id, current_user)
        
        allergies = await db["allergies"].find(
            {"patient_id": patient_id},
            {"_id": 0}
        ).to_list(100)
        
        return {
            "patient_id": patient_id,
            "allergies": allergies,
            "total": len(allergies)
        }
    
    # ============== Problems List ==============
    
    @router.get("/{patient_id}/problems", response_model=dict)
    async def get_patient_problems(
        patient_id: str,
        status: Optional[str] = None,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get patient's problems list"""
        await verify_patient_access(patient_id, current_user)
        
        query = {"patient_id": patient_id}
        if status:
            query["status"] = status
        
        problems = await db["problems"].find(
            query, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "patient_id": patient_id,
            "problems": problems,
            "active_count": len([p for p in problems if p.get("status") == "active"]),
            "total": len(problems)
        }
    
    return router


def calculate_vital_trends(vitals: List[dict]) -> dict:
    """Calculate vital sign trends and averages"""
    if not vitals:
        return {}
    
    trends = {
        "blood_pressure": [],
        "heart_rate": [],
        "temperature": [],
        "oxygen_saturation": [],
        "weight": []
    }
    
    # Collect data points
    bp_systolic = []
    bp_diastolic = []
    hr_values = []
    temp_values = []
    spo2_values = []
    weight_values = []
    
    for v in vitals:
        if v.get("blood_pressure_systolic"):
            bp_systolic.append(v["blood_pressure_systolic"])
        if v.get("blood_pressure_diastolic"):
            bp_diastolic.append(v["blood_pressure_diastolic"])
        if v.get("heart_rate"):
            hr_values.append(v["heart_rate"])
        if v.get("temperature"):
            temp_values.append(v["temperature"])
        if v.get("oxygen_saturation"):
            spo2_values.append(v["oxygen_saturation"])
        if v.get("weight"):
            weight_values.append(v["weight"])
        
        # Add to trend data
        trends["blood_pressure"].append({
            "date": v.get("recorded_at"),
            "systolic": v.get("blood_pressure_systolic"),
            "diastolic": v.get("blood_pressure_diastolic")
        })
        trends["heart_rate"].append({
            "date": v.get("recorded_at"),
            "value": v.get("heart_rate")
        })
        trends["temperature"].append({
            "date": v.get("recorded_at"),
            "value": v.get("temperature")
        })
        trends["oxygen_saturation"].append({
            "date": v.get("recorded_at"),
            "value": v.get("oxygen_saturation")
        })
        trends["weight"].append({
            "date": v.get("recorded_at"),
            "value": v.get("weight")
        })
    
    # Calculate averages and ranges
    averages = {}
    
    if bp_systolic:
        averages["blood_pressure"] = {
            "avg_systolic": round(sum(bp_systolic) / len(bp_systolic)),
            "avg_diastolic": round(sum(bp_diastolic) / len(bp_diastolic)) if bp_diastolic else None,
            "min_systolic": min(bp_systolic),
            "max_systolic": max(bp_systolic)
        }
    
    if hr_values:
        averages["heart_rate"] = {
            "average": round(sum(hr_values) / len(hr_values)),
            "min": min(hr_values),
            "max": max(hr_values)
        }
    
    if temp_values:
        averages["temperature"] = {
            "average": round(sum(temp_values) / len(temp_values), 1),
            "min": min(temp_values),
            "max": max(temp_values)
        }
    
    if spo2_values:
        averages["oxygen_saturation"] = {
            "average": round(sum(spo2_values) / len(spo2_values), 1),
            "min": min(spo2_values),
            "max": max(spo2_values)
        }
    
    if weight_values:
        averages["weight"] = {
            "current": weight_values[0],
            "previous": weight_values[-1] if len(weight_values) > 1 else None,
            "change": round(weight_values[0] - weight_values[-1], 1) if len(weight_values) > 1 else 0
        }
    
    return {
        "trends": trends,
        "averages": averages,
        "data_points": len(vitals)
    }


# Create default router for import
patient_history_router = APIRouter(prefix="/api/patients", tags=["Patient History"])
