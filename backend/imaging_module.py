"""
Imaging Module for Yacco EMR
Handles DICOM image upload, storage, and retrieval
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid
import os
import base64
import aiofiles

router = APIRouter(prefix="/api/imaging", tags=["Imaging"])

# Create uploads directory
UPLOAD_DIR = "/app/backend/uploads/dicom"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============ ENUMS ============
class ModalityType(str, Enum):
    CR = "CR"  # Computed Radiography
    CT = "CT"  # Computed Tomography
    MR = "MR"  # Magnetic Resonance
    US = "US"  # Ultrasound
    XA = "XA"  # X-Ray Angiography
    DX = "DX"  # Digital Radiography
    MG = "MG"  # Mammography
    NM = "NM"  # Nuclear Medicine
    PT = "PT"  # PET
    RF = "RF"  # Radio Fluoroscopy
    OT = "OT"  # Other

class StudyStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    CANCELLED = "cancelled"

# ============ MODELS ============
class ImagingStudyCreate(BaseModel):
    patient_id: str
    patient_name: str
    modality: ModalityType
    study_description: str
    body_part: Optional[str] = None
    referring_physician: Optional[str] = None
    clinical_history: Optional[str] = None
    order_id: Optional[str] = None

class ImagingStudyResponse(BaseModel):
    id: str
    study_instance_uid: str
    patient_id: str
    patient_name: str
    modality: str
    study_description: str
    body_part: Optional[str] = None
    study_date: str
    status: str
    referring_physician: Optional[str] = None
    clinical_history: Optional[str] = None
    num_series: int
    num_images: int
    interpretation: Optional[str] = None
    organization_id: Optional[str] = None

class ImageUpload(BaseModel):
    study_id: str
    series_description: Optional[str] = None
    instance_number: int = 1

class StudyInterpretation(BaseModel):
    findings: str
    impression: str
    recommendations: Optional[str] = None

# Sample DICOM studies for demo
SAMPLE_STUDIES = [
    {
        "modality": "CR",
        "description": "Chest X-Ray PA and Lateral",
        "body_part": "Chest",
        "sample_image": "https://raw.githubusercontent.com/cornerstonejs/cornerstoneWADOImageLoader/master/testImages/CT1_J2KR",
    },
    {
        "modality": "CT",
        "description": "CT Abdomen/Pelvis with Contrast",
        "body_part": "Abdomen",
        "sample_image": "https://raw.githubusercontent.com/cornerstonejs/cornerstoneWADOImageLoader/master/testImages/CT2_J2KR",
    },
    {
        "modality": "MR",
        "description": "MRI Brain with and without Contrast",
        "body_part": "Brain",
        "sample_image": "https://raw.githubusercontent.com/cornerstonejs/cornerstoneWADOImageLoader/master/testImages/CT1_J2KR",
    },
]


def setup_routes(db, get_current_user):
    """Setup imaging routes with database and auth dependency"""
    
    # ============ STUDY MANAGEMENT ============
    @router.post("/studies")
    async def create_imaging_study(
        study_data: ImagingStudyCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new imaging study"""
        # Generate study instance UID (simplified)
        study_uid = f"1.2.826.0.1.3680043.8.1055.1.{datetime.now().strftime('%Y%m%d%H%M%S')}.{uuid.uuid4().hex[:8]}"
        
        study_doc = {
            "id": str(uuid.uuid4()),
            "study_instance_uid": study_uid,
            "patient_id": study_data.patient_id,
            "patient_name": study_data.patient_name,
            "modality": study_data.modality,
            "study_description": study_data.study_description,
            "body_part": study_data.body_part,
            "study_date": datetime.now(timezone.utc).isoformat(),
            "status": StudyStatus.SCHEDULED,
            "referring_physician": study_data.referring_physician or f"{current_user['first_name']} {current_user['last_name']}",
            "clinical_history": study_data.clinical_history,
            "order_id": study_data.order_id,
            "num_series": 0,
            "num_images": 0,
            "series": [],
            "interpretation": None,
            "interpreted_by": None,
            "interpreted_at": None,
            "created_by": current_user["id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": current_user.get("organization_id")
        }
        
        await db.imaging_studies.insert_one(study_doc)
        
        return {
            "message": "Imaging study created",
            "study_id": study_doc["id"],
            "study_instance_uid": study_uid
        }
    
    @router.get("/studies")
    async def get_imaging_studies(
        patient_id: Optional[str] = None,
        modality: Optional[str] = None,
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get imaging studies"""
        query = {}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        if patient_id:
            query["patient_id"] = patient_id
        
        if modality:
            query["modality"] = modality
        
        if status:
            query["status"] = status
        
        studies = await db.imaging_studies.find(query, {"_id": 0, "series": 0}).sort("study_date", -1).to_list(500)
        
        return {"studies": studies, "count": len(studies)}
    
    @router.get("/studies/{study_id}")
    async def get_imaging_study(study_id: str, current_user: dict = Depends(get_current_user)):
        """Get imaging study details"""
        study = await db.imaging_studies.find_one({"id": study_id}, {"_id": 0})
        
        if not study:
            raise HTTPException(status_code=404, detail="Study not found")
        
        return study
    
    @router.get("/studies/patient/{patient_id}")
    async def get_patient_studies(patient_id: str, current_user: dict = Depends(get_current_user)):
        """Get all imaging studies for a patient"""
        query = {"patient_id": patient_id}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        studies = await db.imaging_studies.find(query, {"_id": 0}).sort("study_date", -1).to_list(100)
        
        return {"studies": studies, "count": len(studies)}
    
    # ============ IMAGE UPLOAD ============
    @router.post("/studies/{study_id}/upload")
    async def upload_dicom_image(
        study_id: str,
        file: UploadFile = File(...),
        series_description: str = Form(default="Default Series"),
        instance_number: int = Form(default=1),
        current_user: dict = Depends(get_current_user)
    ):
        """Upload a DICOM image to a study"""
        study = await db.imaging_studies.find_one({"id": study_id})
        
        if not study:
            raise HTTPException(status_code=404, detail="Study not found")
        
        # Generate series UID if new series
        series_uid = f"{study['study_instance_uid']}.1.{len(study.get('series', [])) + 1}"
        
        # Generate SOP Instance UID
        sop_uid = f"{series_uid}.{instance_number}"
        
        # Save file
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'dcm'
        filename = f"{sop_uid}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create image record
        image_doc = {
            "id": str(uuid.uuid4()),
            "sop_instance_uid": sop_uid,
            "series_instance_uid": series_uid,
            "study_id": study_id,
            "instance_number": instance_number,
            "filename": filename,
            "file_path": file_path,
            "file_size": len(content),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": current_user["id"]
        }
        
        await db.dicom_images.insert_one(image_doc)
        
        # Update study
        await db.imaging_studies.update_one(
            {"id": study_id},
            {
                "$inc": {"num_images": 1},
                "$set": {"status": StudyStatus.IN_PROGRESS}
            }
        )
        
        return {
            "message": "Image uploaded",
            "image_id": image_doc["id"],
            "sop_instance_uid": sop_uid
        }
    
    @router.get("/studies/{study_id}/images")
    async def get_study_images(study_id: str, current_user: dict = Depends(get_current_user)):
        """Get all images for a study"""
        images = await db.dicom_images.find({"study_id": study_id}, {"_id": 0}).to_list(500)
        
        return {"images": images, "count": len(images)}
    
    @router.get("/images/{image_id}/data")
    async def get_image_data(image_id: str, current_user: dict = Depends(get_current_user)):
        """Get image data for viewing"""
        image = await db.dicom_images.find_one({"id": image_id}, {"_id": 0})
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Read file and return as base64
        try:
            async with aiofiles.open(image["file_path"], 'rb') as f:
                content = await f.read()
                base64_data = base64.b64encode(content).decode('utf-8')
                
            return {
                "image_id": image_id,
                "data": base64_data,
                "content_type": "application/dicom"
            }
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Image file not found")
    
    # ============ INTERPRETATION ============
    @router.post("/studies/{study_id}/interpret")
    async def add_interpretation(
        study_id: str,
        interpretation: StudyInterpretation,
        current_user: dict = Depends(get_current_user)
    ):
        """Add radiologist interpretation to study"""
        if current_user.get("role") not in ["physician", "admin", "hospital_admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can add interpretations")
        
        interpretation_doc = {
            "findings": interpretation.findings,
            "impression": interpretation.impression,
            "recommendations": interpretation.recommendations,
            "interpreted_by": current_user["id"],
            "interpreted_by_name": f"{current_user['first_name']} {current_user['last_name']}",
            "interpreted_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = await db.imaging_studies.update_one(
            {"id": study_id},
            {
                "$set": {
                    "interpretation": interpretation_doc,
                    "status": StudyStatus.FINAL
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Study not found")
        
        return {"message": "Interpretation added"}
    
    # ============ SAMPLE DATA ============
    @router.post("/demo/create-samples")
    async def create_sample_studies(
        patient_id: str,
        patient_name: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Create sample imaging studies for demo purposes"""
        created_studies = []
        
        for sample in SAMPLE_STUDIES:
            study_uid = f"1.2.826.0.1.3680043.8.1055.1.{datetime.now().strftime('%Y%m%d%H%M%S')}.{uuid.uuid4().hex[:8]}"
            
            study_doc = {
                "id": str(uuid.uuid4()),
                "study_instance_uid": study_uid,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "modality": sample["modality"],
                "study_description": sample["description"],
                "body_part": sample["body_part"],
                "study_date": datetime.now(timezone.utc).isoformat(),
                "status": StudyStatus.COMPLETED,
                "referring_physician": f"{current_user['first_name']} {current_user['last_name']}",
                "clinical_history": "Sample study for demonstration",
                "num_series": 1,
                "num_images": 1,
                "series": [{
                    "series_uid": f"{study_uid}.1",
                    "description": "Primary Series",
                    "images": [{
                        "url": sample["sample_image"],
                        "instance_number": 1
                    }]
                }],
                "sample_image_url": sample["sample_image"],
                "interpretation": {
                    "findings": "This is a sample study for demonstration purposes. Normal findings simulated.",
                    "impression": "No significant abnormality detected (DEMO).",
                    "recommendations": "No follow-up required for demo study.",
                    "interpreted_by": current_user["id"],
                    "interpreted_by_name": f"{current_user['first_name']} {current_user['last_name']}",
                    "interpreted_at": datetime.now(timezone.utc).isoformat()
                },
                "created_by": current_user["id"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "organization_id": current_user.get("organization_id")
            }
            
            await db.imaging_studies.insert_one(study_doc)
            created_studies.append({
                "id": study_doc["id"],
                "description": sample["description"],
                "modality": sample["modality"]
            })
        
        return {
            "message": f"Created {len(created_studies)} sample studies",
            "studies": created_studies
        }
    
    # ============ MODALITIES ============
    @router.get("/modalities")
    async def get_modalities():
        """Get list of imaging modalities"""
        return {
            "modalities": [
                {"code": "CR", "name": "Computed Radiography", "description": "Digital X-ray"},
                {"code": "CT", "name": "Computed Tomography", "description": "CT scan"},
                {"code": "MR", "name": "Magnetic Resonance", "description": "MRI"},
                {"code": "US", "name": "Ultrasound", "description": "Sonography"},
                {"code": "DX", "name": "Digital Radiography", "description": "Digital X-ray"},
                {"code": "MG", "name": "Mammography", "description": "Breast imaging"},
                {"code": "NM", "name": "Nuclear Medicine", "description": "Nuclear imaging"},
                {"code": "PT", "name": "PET", "description": "Positron Emission Tomography"},
                {"code": "XA", "name": "X-Ray Angiography", "description": "Vascular imaging"},
            ]
        }
    
    return router
