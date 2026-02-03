"""
Clinical Decision Support Module for Yacco EMR
Handles drug interactions, allergy alerts, and clinical warnings
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum

router = APIRouter(prefix="/api/cds", tags=["Clinical Decision Support"])

# ============ ENUMS ============
class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertType(str, Enum):
    DRUG_INTERACTION = "drug_interaction"
    ALLERGY = "allergy"
    DUPLICATE_THERAPY = "duplicate_therapy"
    CONTRAINDICATION = "contraindication"
    DOSE_ALERT = "dose_alert"
    AGE_ALERT = "age_alert"
    RENAL_DOSING = "renal_dosing"

# ============ MODELS ============
class DrugInteractionCheck(BaseModel):
    medications: List[str]
    new_medication: str

class AllergyCheck(BaseModel):
    patient_allergies: List[str]
    medication: str

class ClinicalAlert(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    recommendations: List[str]
    medication_involved: Optional[str] = None
    interacting_medication: Optional[str] = None

# ============ DRUG INTERACTION DATABASE ============
# Simplified drug interaction database
DRUG_INTERACTIONS = {
    # Serious interactions
    ("warfarin", "aspirin"): {
        "severity": AlertSeverity.CRITICAL,
        "description": "Increased risk of bleeding. Concomitant use significantly increases the risk of major bleeding events.",
        "recommendations": ["Consider alternative antiplatelet if possible", "Monitor INR closely", "Watch for signs of bleeding"]
    },
    ("warfarin", "ibuprofen"): {
        "severity": AlertSeverity.CRITICAL,
        "description": "NSAIDs increase bleeding risk with warfarin and may increase INR.",
        "recommendations": ["Avoid combination if possible", "Use acetaminophen for pain instead", "Monitor INR frequently"]
    },
    ("metformin", "contrast"): {
        "severity": AlertSeverity.WARNING,
        "description": "Risk of lactic acidosis with IV contrast. Hold metformin before and after contrast procedures.",
        "recommendations": ["Hold metformin 48 hours before contrast", "Resume after renal function confirmed stable"]
    },
    ("lisinopril", "potassium"): {
        "severity": AlertSeverity.WARNING,
        "description": "ACE inhibitors can increase potassium levels. Risk of hyperkalemia with potassium supplementation.",
        "recommendations": ["Monitor serum potassium", "Avoid potassium supplements unless indicated", "Check renal function"]
    },
    ("simvastatin", "amlodipine"): {
        "severity": AlertSeverity.WARNING,
        "description": "Amlodipine increases simvastatin levels. Maximum simvastatin dose with amlodipine is 20mg.",
        "recommendations": ["Limit simvastatin to 20mg daily", "Consider alternative statin", "Monitor for muscle pain"]
    },
    ("ciprofloxacin", "theophylline"): {
        "severity": AlertSeverity.CRITICAL,
        "description": "Ciprofloxacin significantly increases theophylline levels, risk of toxicity.",
        "recommendations": ["Reduce theophylline dose by 50%", "Monitor theophylline levels", "Consider alternative antibiotic"]
    },
    ("methotrexate", "nsaids"): {
        "severity": AlertSeverity.CRITICAL,
        "description": "NSAIDs decrease methotrexate clearance, increasing toxicity risk.",
        "recommendations": ["Avoid NSAIDs with methotrexate", "Use acetaminophen for pain", "Monitor for bone marrow suppression"]
    },
    ("ssri", "maoi"): {
        "severity": AlertSeverity.CRITICAL,
        "description": "Life-threatening serotonin syndrome risk. Combination is contraindicated.",
        "recommendations": ["CONTRAINDICATED - Do not combine", "Allow 14-day washout between medications"]
    },
    ("digoxin", "amiodarone"): {
        "severity": AlertSeverity.WARNING,
        "description": "Amiodarone increases digoxin levels by 70-100%.",
        "recommendations": ["Reduce digoxin dose by 50%", "Monitor digoxin levels", "Watch for signs of toxicity"]
    },
    ("clopidogrel", "omeprazole"): {
        "severity": AlertSeverity.WARNING,
        "description": "Omeprazole may reduce clopidogrel effectiveness by inhibiting CYP2C19.",
        "recommendations": ["Consider pantoprazole instead", "Monitor for cardiovascular events"]
    },
}

# Drug class mappings for interaction checking
DRUG_CLASSES = {
    "nsaids": ["ibuprofen", "naproxen", "meloxicam", "diclofenac", "celecoxib", "ketorolac"],
    "ssri": ["sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram"],
    "maoi": ["phenelzine", "tranylcypromine", "selegiline", "isocarboxazid"],
    "ace_inhibitor": ["lisinopril", "enalapril", "ramipril", "captopril", "benazepril"],
    "arb": ["losartan", "valsartan", "irbesartan", "olmesartan", "candesartan"],
    "statin": ["atorvastatin", "simvastatin", "rosuvastatin", "pravastatin", "lovastatin"],
    "benzodiazepine": ["alprazolam", "lorazepam", "diazepam", "clonazepam"],
    "opioid": ["tramadol", "hydrocodone", "oxycodone", "morphine", "fentanyl"],
    "anticoagulant": ["warfarin", "heparin", "enoxaparin", "rivaroxaban", "apixaban"],
    "fluoroquinolone": ["ciprofloxacin", "levofloxacin", "moxifloxacin"],
}

# Allergy cross-reactivity database
ALLERGY_CROSS_REACTIVITY = {
    "penicillin": {
        "cross_reactive": ["amoxicillin", "ampicillin", "piperacillin", "amoxicillin-clavulanate"],
        "possible_cross": ["cephalosporins"],  # ~1-2% cross-reactivity
        "safe_alternatives": ["azithromycin", "doxycycline", "fluoroquinolones"]
    },
    "sulfa": {
        "cross_reactive": ["sulfamethoxazole", "trimethoprim-sulfamethoxazole", "sulfasalazine"],
        "possible_cross": ["thiazide diuretics", "furosemide", "celecoxib"],
        "safe_alternatives": ["other antibiotic classes"]
    },
    "aspirin": {
        "cross_reactive": ["nsaids", "ibuprofen", "naproxen"],
        "possible_cross": [],
        "safe_alternatives": ["acetaminophen", "tramadol"]
    },
    "codeine": {
        "cross_reactive": ["morphine", "hydrocodone", "oxycodone"],
        "possible_cross": ["tramadol"],
        "safe_alternatives": ["nsaids", "acetaminophen"]
    },
    "iodine": {
        "cross_reactive": [],
        "possible_cross": ["iv contrast"],
        "safe_alternatives": []
    },
}


def setup_routes(db, get_current_user):
    """Setup CDS routes with database and auth dependency"""
    
    def normalize_drug_name(name: str) -> str:
        """Normalize drug name for comparison"""
        return name.lower().strip().replace("-", "").replace(" ", "")
    
    def get_drug_class(drug_name: str) -> Optional[str]:
        """Get the drug class for a medication"""
        normalized = normalize_drug_name(drug_name)
        for drug_class, members in DRUG_CLASSES.items():
            if any(normalize_drug_name(m) in normalized or normalized in normalize_drug_name(m) for m in members):
                return drug_class
        return None
    
    def check_interaction(drug1: str, drug2: str) -> Optional[dict]:
        """Check for interaction between two drugs"""
        d1_norm = normalize_drug_name(drug1)
        d2_norm = normalize_drug_name(drug2)
        
        # Direct match
        for (med1, med2), interaction in DRUG_INTERACTIONS.items():
            if (d1_norm in med1 or med1 in d1_norm) and (d2_norm in med2 or med2 in d2_norm):
                return {"drugs": (drug1, drug2), **interaction}
            if (d2_norm in med1 or med1 in d2_norm) and (d1_norm in med2 or med2 in d1_norm):
                return {"drugs": (drug1, drug2), **interaction}
        
        # Class-based check
        d1_class = get_drug_class(drug1)
        d2_class = get_drug_class(drug2)
        
        for (med1, med2), interaction in DRUG_INTERACTIONS.items():
            if d1_class and d2_class:
                if (d1_class == med1 or d1_class in med1) and (d2_class == med2 or d2_class in med2):
                    return {"drugs": (drug1, drug2), **interaction}
        
        return None
    
    # ============ DRUG INTERACTION CHECKING ============
    @router.post("/check-interactions")
    async def check_drug_interactions(request: DrugInteractionCheck):
        """Check for drug interactions between current medications and a new one"""
        alerts = []
        new_drug_norm = normalize_drug_name(request.new_medication)
        
        for current_med in request.medications:
            interaction = check_interaction(current_med, request.new_medication)
            
            if interaction:
                alert = ClinicalAlert(
                    alert_type=AlertType.DRUG_INTERACTION,
                    severity=interaction["severity"],
                    title=f"Drug Interaction: {current_med} + {request.new_medication}",
                    description=interaction["description"],
                    recommendations=interaction["recommendations"],
                    medication_involved=request.new_medication,
                    interacting_medication=current_med
                )
                alerts.append(alert.model_dump())
        
        # Check for duplicate therapy
        new_class = get_drug_class(request.new_medication)
        if new_class:
            for current_med in request.medications:
                current_class = get_drug_class(current_med)
                if current_class == new_class and normalize_drug_name(current_med) != new_drug_norm:
                    alert = ClinicalAlert(
                        alert_type=AlertType.DUPLICATE_THERAPY,
                        severity=AlertSeverity.WARNING,
                        title=f"Duplicate Therapy: {new_class.replace('_', ' ').title()}",
                        description=f"Patient is already on {current_med} ({current_class}). Adding {request.new_medication} may result in duplicate therapy.",
                        recommendations=["Review necessity of both medications", "Consider discontinuing one", "Monitor for additive effects"],
                        medication_involved=request.new_medication,
                        interacting_medication=current_med
                    )
                    alerts.append(alert.model_dump())
        
        return {
            "has_alerts": len(alerts) > 0,
            "alert_count": len(alerts),
            "critical_count": len([a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]),
            "alerts": alerts
        }
    
    # ============ ALLERGY CHECKING ============
    @router.post("/check-allergy")
    async def check_allergy_interaction(request: AllergyCheck):
        """Check if a medication is contraindicated due to patient allergies"""
        alerts = []
        med_norm = normalize_drug_name(request.medication)
        
        for allergy in request.patient_allergies:
            allergy_norm = normalize_drug_name(allergy)
            
            # Direct match
            if allergy_norm in med_norm or med_norm in allergy_norm:
                alert = ClinicalAlert(
                    alert_type=AlertType.ALLERGY,
                    severity=AlertSeverity.CRITICAL,
                    title=f"ALLERGY ALERT: {request.medication}",
                    description=f"Patient has documented allergy to {allergy}. {request.medication} is contraindicated.",
                    recommendations=["DO NOT prescribe this medication", "Document allergy verification", "Consider safe alternatives"],
                    medication_involved=request.medication
                )
                alerts.append(alert.model_dump())
                continue
            
            # Cross-reactivity check
            if allergy_norm in ALLERGY_CROSS_REACTIVITY:
                cross_info = ALLERGY_CROSS_REACTIVITY[allergy_norm]
                
                # Check cross-reactive medications
                for cross_drug in cross_info.get("cross_reactive", []):
                    if normalize_drug_name(cross_drug) in med_norm or med_norm in normalize_drug_name(cross_drug):
                        alert = ClinicalAlert(
                            alert_type=AlertType.ALLERGY,
                            severity=AlertSeverity.CRITICAL,
                            title=f"Cross-Reactivity Alert: {allergy} Allergy",
                            description=f"Patient allergic to {allergy}. {request.medication} has cross-reactivity and is contraindicated.",
                            recommendations=[
                                "DO NOT prescribe - high cross-reactivity risk",
                                f"Safe alternatives: {', '.join(cross_info.get('safe_alternatives', ['consult pharmacist']))}"
                            ],
                            medication_involved=request.medication
                        )
                        alerts.append(alert.model_dump())
                
                # Check possible cross-reactivity (warning level)
                for possible in cross_info.get("possible_cross", []):
                    if normalize_drug_name(possible) in med_norm or med_norm in normalize_drug_name(possible):
                        alert = ClinicalAlert(
                            alert_type=AlertType.ALLERGY,
                            severity=AlertSeverity.WARNING,
                            title=f"Possible Cross-Reactivity: {allergy} Allergy",
                            description=f"Patient allergic to {allergy}. {request.medication} may have low cross-reactivity risk (~1-2%).",
                            recommendations=[
                                "Use with caution",
                                "Consider skin testing if available",
                                "Monitor closely for allergic reaction",
                                "Have epinephrine available"
                            ],
                            medication_involved=request.medication
                        )
                        alerts.append(alert.model_dump())
        
        return {
            "has_alerts": len(alerts) > 0,
            "alert_count": len(alerts),
            "critical_count": len([a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]),
            "alerts": alerts,
            "safe_to_prescribe": len([a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]) == 0
        }
    
    # ============ COMPREHENSIVE CHECK ============
    @router.post("/comprehensive-check")
    async def comprehensive_clinical_check(
        patient_id: str,
        new_medication: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Perform comprehensive clinical decision support check for a patient"""
        # Get patient data
        patient = await db.patients.find_one({"id": patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get current medications
        medications = await db.medications.find(
            {"patient_id": patient_id, "status": "active"},
            {"_id": 0}
        ).to_list(100)
        
        current_meds = [m["name"] for m in medications]
        
        # Get allergies
        allergies = await db.allergies.find({"patient_id": patient_id}, {"_id": 0}).to_list(50)
        patient_allergies = [a["allergen"] for a in allergies]
        
        all_alerts = []
        
        # Drug interaction check
        if current_meds:
            interaction_request = DrugInteractionCheck(
                medications=current_meds,
                new_medication=new_medication
            )
            interaction_result = await check_drug_interactions(interaction_request)
            all_alerts.extend(interaction_result["alerts"])
        
        # Allergy check
        if patient_allergies:
            allergy_request = AllergyCheck(
                patient_allergies=patient_allergies,
                medication=new_medication
            )
            allergy_result = await check_allergy_interaction(allergy_request)
            all_alerts.extend(allergy_result["alerts"])
        
        # Age-based alerts (example)
        if patient.get("date_of_birth"):
            try:
                from datetime import datetime
                dob = datetime.fromisoformat(patient["date_of_birth"].replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - dob).days // 365
                
                # Elderly patient check for certain medications
                if age >= 65:
                    high_risk_elderly = ["benzodiazepine", "opioid", "anticholinergic"]
                    med_class = get_drug_class(new_medication)
                    
                    if med_class in high_risk_elderly:
                        alert = ClinicalAlert(
                            alert_type=AlertType.AGE_ALERT,
                            severity=AlertSeverity.WARNING,
                            title=f"Beers Criteria Alert: {new_medication}",
                            description=f"Patient is {age} years old. {new_medication} is potentially inappropriate for elderly patients (Beers Criteria).",
                            recommendations=[
                                "Consider lower dose if necessary",
                                "Evaluate safer alternatives",
                                "Monitor for falls, confusion, sedation"
                            ],
                            medication_involved=new_medication
                        )
                        all_alerts.append(alert.model_dump())
            except:
                pass  # Skip if DOB parsing fails
        
        # Sort alerts by severity
        severity_order = {AlertSeverity.CRITICAL: 0, AlertSeverity.WARNING: 1, AlertSeverity.INFO: 2}
        all_alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return {
            "patient_id": patient_id,
            "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            "medication_checked": new_medication,
            "current_medications": current_meds,
            "known_allergies": patient_allergies,
            "has_alerts": len(all_alerts) > 0,
            "alert_count": len(all_alerts),
            "critical_count": len([a for a in all_alerts if a["severity"] == AlertSeverity.CRITICAL]),
            "alerts": all_alerts,
            "safe_to_prescribe": len([a for a in all_alerts if a["severity"] == AlertSeverity.CRITICAL]) == 0,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ UTILITY ENDPOINTS ============
    @router.get("/drug-classes")
    async def get_drug_classes():
        """Get list of drug classes"""
        return {
            "drug_classes": [
                {"class": key, "examples": value[:3]}
                for key, value in DRUG_CLASSES.items()
            ]
        }
    
    @router.get("/common-allergies")
    async def get_common_allergies():
        """Get list of common allergies with cross-reactivity info"""
        return {
            "allergies": [
                {
                    "allergen": key,
                    "cross_reactive_count": len(value.get("cross_reactive", [])),
                    "safe_alternatives": value.get("safe_alternatives", [])
                }
                for key, value in ALLERGY_CROSS_REACTIVITY.items()
            ]
        }
    
    return router
