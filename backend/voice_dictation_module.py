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
    router = APIRouter(prefix="/api/voice-dictation", tags=["Voice Dictation"])
    
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
    
    # ============== VOICE DICTATION ANALYTICS ==============
    
    @router.get("/analytics")
    async def get_voice_dictation_analytics(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get voice dictation usage analytics for the organization."""
        allowed_roles = ["hospital_admin", "super_admin", "hospital_it_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        query = {"organization_id": org_id} if org_id else {}
        
        if date_from:
            query["timestamp"] = {"$gte": date_from}
        if date_to:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = date_to + "T23:59:59"
            else:
                query["timestamp"] = {"$lte": date_to + "T23:59:59"}
        
        # Get all logs
        logs = await db["voice_dictation_logs"].find(query, {"_id": 0}).to_list(10000)
        
        # Calculate stats
        total_transcriptions = len(logs)
        total_duration = sum(log_entry.get("duration_seconds", 0) or 0 for log_entry in logs)
        total_corrections = sum(log_entry.get("corrections_count", 0) for log_entry in logs)
        
        # Usage by role
        role_usage = {}
        for log in logs:
            role = log.get("user_role", "unknown")
            if role not in role_usage:
                role_usage[role] = {"count": 0, "duration": 0}
            role_usage[role]["count"] += 1
            role_usage[role]["duration"] += log.get("duration_seconds", 0) or 0
        
        # Usage by context
        context_usage = {}
        for log in logs:
            ctx = log.get("context", "general")
            if ctx not in context_usage:
                context_usage[ctx] = 0
            context_usage[ctx] += 1
        
        # Top users
        user_usage = {}
        for log in logs:
            uid = log.get("user_id")
            uname = log.get("user_name", "Unknown")
            if uid not in user_usage:
                user_usage[uid] = {"name": uname, "count": 0, "duration": 0}
            user_usage[uid]["count"] += 1
            user_usage[uid]["duration"] += log.get("duration_seconds", 0) or 0
        
        top_users = sorted(user_usage.values(), key=lambda x: x["count"], reverse=True)[:10]
        
        # Daily usage (last 30 days)
        from collections import defaultdict
        daily_usage = defaultdict(int)
        for log in logs:
            ts = log.get("timestamp", "")
            if ts:
                day = ts[:10]  # YYYY-MM-DD
                daily_usage[day] += 1
        
        return {
            "summary": {
                "total_transcriptions": total_transcriptions,
                "total_duration_minutes": round(total_duration / 60, 2),
                "total_corrections_made": total_corrections,
                "avg_duration_seconds": round(total_duration / total_transcriptions, 2) if total_transcriptions > 0 else 0
            },
            "usage_by_role": role_usage,
            "usage_by_context": context_usage,
            "top_users": top_users,
            "daily_usage": dict(sorted(daily_usage.items())[-30:])
        }
    
    @router.get("/audit-logs")
    async def get_voice_dictation_audit_logs(
        limit: int = 100,
        skip: int = 0,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get detailed voice dictation audit logs."""
        allowed_roles = ["hospital_admin", "super_admin", "hospital_it_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        query = {"organization_id": org_id} if org_id else {}
        
        if user_id:
            query["user_id"] = user_id
        if context:
            query["context"] = context
        
        logs = await db["voice_dictation_logs"].find(
            query, {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        total = await db["voice_dictation_logs"].count_documents(query)
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    
    # ============== AI REPORT AUTO-GENERATION ==============
    
    @router.post("/ai-expand")
    async def ai_expand_dictation(
        text: str,
        note_type: str = "progress_note",  # progress_note, soap_note, radiology_report, nursing_assessment
        context: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """
        Use AI to expand brief dictation into structured clinical notes.
        
        Note types:
        - progress_note: General clinical progress note
        - soap_note: Structured SOAP format
        - radiology_report: Structured radiology findings
        - nursing_assessment: Nursing assessment format
        """
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        try:
            from emergentintegrations.llm.openai import LlmChat
            
            # Define prompts for different note types
            system_prompts = {
                "progress_note": """You are a medical documentation assistant. Expand the brief clinical dictation into a well-structured progress note. Include:
- Chief complaint / Reason for visit
- History of present illness (HPI)
- Relevant findings
- Assessment
- Plan
Use professional medical language. Be concise but thorough.""",
                
                "soap_note": """You are a medical documentation assistant. Convert the brief dictation into a structured SOAP note format:
S (Subjective): Patient's reported symptoms and history
O (Objective): Physical exam findings, vitals, test results
A (Assessment): Diagnosis or differential diagnoses
P (Plan): Treatment plan, medications, follow-up

Use professional medical language. Be concise but thorough.""",
                
                "radiology_report": """You are a radiology report assistant. Expand the brief dictation into a structured radiology report with:
- TECHNIQUE: Imaging technique used
- COMPARISON: Prior studies if mentioned
- FINDINGS: Detailed findings organized by anatomical region
- IMPRESSION: Summary diagnosis with numbered conclusions if multiple

Use standard radiology terminology. Be precise and thorough.""",
                
                "nursing_assessment": """You are a nursing documentation assistant. Expand the brief dictation into a structured nursing assessment:
- Patient status / Chief concern
- Vital signs assessment
- System-by-system assessment
- Patient response to interventions
- Nursing diagnosis / Problems identified
- Nursing plan / Interventions

Use professional nursing terminology. Be clear and thorough."""
            }
            
            system_prompt = system_prompts.get(note_type, system_prompts["progress_note"])
            
            if context:
                system_prompt += f"\n\nAdditional context: {context}"
            
            chat = LlmChat(api_key=api_key)
            
            response = await chat.send_message(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Expand this brief dictation into a complete {note_type.replace('_', ' ')}:\n\n{text}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            expanded_text = response.choices[0].message.content
            
            # Log AI expansion
            await db["voice_dictation_logs"].insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.get("id"),
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "user_role": user.get("role"),
                "organization_id": user.get("organization_id"),
                "context": f"ai_expand_{note_type}",
                "action": "ai_expand",
                "input_length": len(text),
                "output_length": len(expanded_text),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "original_text": text,
                "expanded_text": expanded_text,
                "note_type": note_type,
                "word_count": len(expanded_text.split())
            }
            
        except ImportError:
            raise HTTPException(status_code=500, detail="AI library not installed")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI expansion failed: {str(e)}")
    
    return router
