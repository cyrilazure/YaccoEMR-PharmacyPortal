"""
Voice Dictation Module
Provides speech-to-text transcription using OpenAI Whisper
with medical terminology correction support.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import tempfile
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Medical terminology dictionary for common corrections
MEDICAL_TERMS = {
    # Common misheard medical terms
    "hypertension": ["high pertension", "hyper tension", "high tension"],
    "pneumonia": ["new monia", "numonia", "pneumoni"],
    "cardiomegaly": ["cardio megaly", "cardiac megaly"],
    "hepatomegaly": ["hepato megaly", "liver megaly"],
    "splenomegaly": ["spleno megaly", "spleen megaly"],
    "tachycardia": ["tacky cardia", "tachy cardia"],
    "bradycardia": ["brady cardia", "slow cardia"],
    "arrhythmia": ["a rythymia", "irregular rhythm"],
    "atherosclerosis": ["athero sclerosis", "artery sclerosis"],
    "myocardial infarction": ["my cardial infarction", "heart attack"],
    "cerebrovascular": ["cerebro vascular", "brain vascular"],
    "hemorrhage": ["hemmorage", "hemerage", "bleeding"],
    "edema": ["a dema", "swelling"],
    "effusion": ["a fusion", "fluid collection"],
    "consolidation": ["consolodation", "lung consolidation"],
    "atelectasis": ["atelectisis", "lung collapse"],
    "pneumothorax": ["new mo thorax", "collapsed lung"],
    "hemothorax": ["hemo thorax", "blood in chest"],
    "carcinoma": ["carsonoma", "cancer"],
    "metastasis": ["metastisis", "spread"],
    "lymphadenopathy": ["lymph adenopathy", "swollen nodes"],
    "cholecystitis": ["cole cystitis", "gallbladder inflammation"],
    "appendicitis": ["appendisitis", "appendix inflammation"],
    "diverticulitis": ["diverticulitis", "colon inflammation"],
    "osteoarthritis": ["osteo arthritis", "joint arthritis"],
    "rheumatoid": ["room a toid", "rhumatoid"],
    "diabetes mellitus": ["diabetis", "sugar disease"],
    "hypoglycemia": ["hypo glycemia", "low sugar"],
    "hyperglycemia": ["hyper glycemia", "high sugar"],
    "hyperlipidemia": ["hyper lipidemia", "high cholesterol"],
    "hypothyroidism": ["hypo thyroidism", "low thyroid"],
    "hyperthyroidism": ["hyper thyroidism", "high thyroid"],
    "anemia": ["a nemia", "low blood"],
    "leukocytosis": ["leuko cytosis", "high white cells"],
    "thrombocytopenia": ["thrombo cyto penia", "low platelets"],
    # Radiology-specific terms
    "radiolucent": ["radio lucent", "dark area"],
    "radiopaque": ["radio opaque", "white area"],
    "calcification": ["calcifiation", "calcium deposit"],
    "ossification": ["ossifiation", "bone formation"],
    "lucency": ["loosency", "dark spot"],
    "opacity": ["opasity", "white spot"],
    "infiltrate": ["infilitrate", "lung marking"],
    "nodule": ["nodul", "small mass"],
    "mass effect": ["mass affect", "pushing"],
    "midline shift": ["mid line shift", "brain shift"],
    "herniation": ["hernation", "bulging"],
    "stenosis": ["stenoses", "narrowing"],
    "aneurysm": ["anurism", "bulge"],
    "dissection": ["disection", "tear"],
    "thrombosis": ["thromboses", "clot"],
    "embolism": ["embolizm", "blockage"],
    "ischemia": ["iskemia", "poor blood flow"],
    "infarct": ["infark", "dead tissue"],
    "necrosis": ["nekrosis", "tissue death"],
    "fibrosis": ["fibroses", "scarring"],
    "cirrhosis": ["sirosis", "liver scarring"],
}

# Common medical abbreviations that should be expanded or kept
MEDICAL_ABBREVIATIONS = {
    "CT": "CT scan",
    "MRI": "MRI",
    "X-ray": "X-ray",
    "EKG": "EKG",
    "ECG": "ECG",
    "BP": "blood pressure",
    "HR": "heart rate",
    "RR": "respiratory rate",
    "SpO2": "oxygen saturation",
    "BUN": "BUN",
    "Cr": "creatinine",
    "Hgb": "hemoglobin",
    "Hct": "hematocrit",
    "WBC": "white blood cell count",
    "RBC": "red blood cell count",
    "PLT": "platelet count",
    "PT": "prothrombin time",
    "INR": "INR",
    "BMP": "basic metabolic panel",
    "CBC": "complete blood count",
    "LFT": "liver function tests",
    "TSH": "thyroid stimulating hormone",
    "A1c": "hemoglobin A1c",
    "PRN": "as needed",
    "BID": "twice daily",
    "TID": "three times daily",
    "QID": "four times daily",
    "PO": "by mouth",
    "IV": "intravenous",
    "IM": "intramuscular",
    "SC": "subcutaneous",
    "STAT": "immediately",
}


class TranscriptionResponse(BaseModel):
    text: str
    corrected_text: str
    corrections_made: List[dict]
    duration_seconds: Optional[float] = None


class MedicalCorrectionRequest(BaseModel):
    text: str
    context: Optional[str] = "general"  # general, radiology, nursing, clinical


def create_voice_dictation_router(db, get_current_user) -> APIRouter:
    router = APIRouter(prefix="/voice-dictation", tags=["Voice Dictation"])
    
    def correct_medical_terminology(text: str, context: str = "general") -> tuple:
        """Apply medical terminology corrections to transcribed text."""
        corrected = text
        corrections = []
        
        # Convert to lowercase for matching
        text_lower = text.lower()
        
        # Apply corrections from dictionary
        for correct_term, incorrect_variants in MEDICAL_TERMS.items():
            for variant in incorrect_variants:
                if variant.lower() in text_lower:
                    # Find and replace (case-insensitive)
                    import re
                    pattern = re.compile(re.escape(variant), re.IGNORECASE)
                    if pattern.search(corrected):
                        corrected = pattern.sub(correct_term, corrected)
                        corrections.append({
                            "original": variant,
                            "corrected": correct_term,
                            "type": "medical_term"
                        })
        
        return corrected, corrections
    
    @router.post("/transcribe", response_model=TranscriptionResponse)
    async def transcribe_audio(
        audio: UploadFile = File(...),
        context: str = Form(default="general"),
        language: str = Form(default="en"),
        user: dict = Depends(get_current_user)
    ):
        """
        Transcribe audio using OpenAI Whisper with medical terminology correction.
        
        Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
        Max file size: 25MB
        
        Context options: general, radiology, nursing, clinical
        """
        # Validate file format
        allowed_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        file_ext = audio.filename.split(".")[-1].lower() if audio.filename else ""
        
        if file_ext not in allowed_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported audio format. Allowed: {', '.join(allowed_formats)}"
            )
        
        # Check file size (25MB limit)
        content = await audio.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 25MB limit"
            )
        
        # Get API key
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="Speech-to-text service not configured"
            )
        
        try:
            from emergentintegrations.llm.openai import OpenAISpeechToText
            
            # Create context-specific prompt for better accuracy
            context_prompts = {
                "radiology": "This is a radiology report dictation. Medical imaging terms like CT, MRI, X-ray, consolidation, effusion, mass, nodule, calcification, opacity are common.",
                "nursing": "This is a nursing assessment dictation. Terms like vital signs, blood pressure, medication administration, patient condition are common.",
                "clinical": "This is a clinical note dictation. Terms like diagnosis, symptoms, treatment plan, medications, follow-up are common.",
                "general": "This is a medical dictation. Common medical terminology may be used."
            }
            
            prompt = context_prompts.get(context, context_prompts["general"])
            
            # Initialize STT
            stt = OpenAISpeechToText(api_key=api_key)
            
            # Save to temp file for processing
            with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Transcribe
                with open(tmp_path, "rb") as audio_file:
                    response = await stt.transcribe(
                        file=audio_file,
                        model="whisper-1",
                        response_format="verbose_json",
                        language=language,
                        prompt=prompt,
                        temperature=0.0
                    )
                
                raw_text = response.text
                duration = getattr(response, 'duration', None)
                
            finally:
                # Cleanup temp file
                os.unlink(tmp_path)
            
            # Apply medical terminology corrections
            corrected_text, corrections = correct_medical_terminology(raw_text, context)
            
            # Log transcription for audit
            await db["voice_dictation_logs"].insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.get("id"),
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "user_role": user.get("role"),
                "organization_id": user.get("organization_id"),
                "context": context,
                "language": language,
                "duration_seconds": duration,
                "corrections_count": len(corrections),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return TranscriptionResponse(
                text=raw_text,
                corrected_text=corrected_text,
                corrections_made=corrections,
                duration_seconds=duration
            )
            
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Speech-to-text library not installed"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(e)}"
            )
    
    @router.post("/correct-terminology")
    async def correct_terminology(
        request: MedicalCorrectionRequest,
        user: dict = Depends(get_current_user)
    ):
        """
        Apply medical terminology corrections to existing text.
        Useful for correcting browser-based speech recognition results.
        """
        corrected_text, corrections = correct_medical_terminology(request.text, request.context)
        
        return {
            "original_text": request.text,
            "corrected_text": corrected_text,
            "corrections_made": corrections
        }
    
    @router.get("/medical-terms")
    async def get_medical_terms(
        user: dict = Depends(get_current_user)
    ):
        """Get list of supported medical terms for autocorrection."""
        return {
            "terms_count": len(MEDICAL_TERMS),
            "abbreviations_count": len(MEDICAL_ABBREVIATIONS),
            "categories": ["cardiology", "pulmonology", "radiology", "general", "medications"]
        }
    
    return router
