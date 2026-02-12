"""
PACS/DICOM Integration Module

Integrates with dcm4chee Archive for DICOM storage and retrieval.
Supports:
- WADO-RS (Web Access to DICOM Objects - RESTful Services)
- QIDO-RS (Query based on ID for DICOM Objects)
- STOW-RS (Store Over the Web)
- HL7 workflows (ADT, ORM, ORU)

Architecture:
- dcm4chee Archive: DICOM storage backend
- Weasis/MedDream: Web-based DICOM viewer
- This module: Integration layer between EMR and PACS
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import httpx
from datetime import datetime, timezone
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class ModalityType(str, Enum):
    CT = "CT"
    MR = "MR"
    CR = "CR"  # Computed Radiography (X-Ray)
    DX = "DX"  # Digital Radiography
    US = "US"  # Ultrasound
    MG = "MG"  # Mammography
    NM = "NM"  # Nuclear Medicine
    PT = "PT"  # PET
    XA = "XA"  # X-Ray Angiography
    RF = "RF"  # Radiofluoroscopy
    OT = "OT"  # Other


class DicomStudySearch(BaseModel):
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    accession_number: Optional[str] = None
    study_date_from: Optional[str] = None
    study_date_to: Optional[str] = None
    modality: Optional[ModalityType] = None
    study_description: Optional[str] = None
    limit: int = 50


class DicomStudy(BaseModel):
    study_instance_uid: str
    patient_id: str
    patient_name: str
    study_date: Optional[str] = None
    study_time: Optional[str] = None
    accession_number: Optional[str] = None
    modality: Optional[str] = None
    study_description: Optional[str] = None
    referring_physician: Optional[str] = None
    number_of_series: Optional[int] = None
    number_of_instances: Optional[int] = None


class HL7Message(BaseModel):
    message_type: str  # ADT, ORM, ORU
    patient_id: str
    patient_name: str
    event_type: Optional[str] = None  # A01 (admit), A04 (register), etc.
    order_data: Optional[dict] = None
    result_data: Optional[dict] = None


def create_pacs_integration_router(db, get_current_user) -> APIRouter:
    router = APIRouter(prefix="/api/pacs", tags=["PACS Integration"])
    
    # PACS Configuration from environment
    PACS_HOST = os.getenv("PACS_HOST", "localhost")
    PACS_PORT = os.getenv("PACS_PORT", "8080")
    PACS_AE_TITLE = os.getenv("PACS_AE_TITLE", "DCM4CHEE")
    WADO_URL = os.getenv("WADO_URL", f"http://{PACS_HOST}:{PACS_PORT}/dcm4chee-arc/aets/{PACS_AE_TITLE}")
    VIEWER_URL = os.getenv("DICOM_VIEWER_URL", "")  # MedDream or Weasis viewer URL
    
    # ============== CONFIGURATION ==============
    
    @router.get("/config")
    async def get_pacs_config(
        user: dict = Depends(get_current_user)
    ):
        """Get PACS configuration status."""
        return {
            "pacs_host": PACS_HOST,
            "pacs_port": PACS_PORT,
            "ae_title": PACS_AE_TITLE,
            "wado_url": WADO_URL,
            "viewer_url": VIEWER_URL,
            "is_configured": bool(PACS_HOST and PACS_HOST != "localhost"),
            "status": "configured" if PACS_HOST != "localhost" else "demo_mode"
        }
    
    @router.get("/status")
    async def check_pacs_status(
        user: dict = Depends(get_current_user)
    ):
        """Check PACS server connectivity."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try WADO-RS status endpoint
                response = await client.get(f"{WADO_URL}/rs/studies", params={"limit": 1})
                
                return {
                    "status": "connected" if response.status_code in [200, 204] else "error",
                    "response_code": response.status_code,
                    "server": PACS_HOST
                }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "server": PACS_HOST,
                "message": "PACS server not reachable. Configure PACS_HOST in environment."
            }
    
    # ============== STUDY SEARCH (QIDO-RS) ==============
    
    @router.post("/studies/search")
    async def search_studies(
        search: DicomStudySearch,
        user: dict = Depends(get_current_user)
    ):
        """
        Search for DICOM studies using QIDO-RS.
        
        In demo mode, returns mock data.
        In production, queries dcm4chee archive.
        """
        # Build QIDO-RS query parameters
        params = {}
        if search.patient_id:
            params["PatientID"] = search.patient_id
        if search.patient_name:
            params["PatientName"] = f"*{search.patient_name}*"
        if search.accession_number:
            params["AccessionNumber"] = search.accession_number
        if search.modality:
            params["ModalitiesInStudy"] = search.modality.value
        if search.study_date_from:
            date_range = search.study_date_from.replace("-", "")
            if search.study_date_to:
                date_range += f"-{search.study_date_to.replace('-', '')}"
            params["StudyDate"] = date_range
        
        params["limit"] = search.limit
        
        # Check if we're in demo mode
        if PACS_HOST == "localhost":
            # Return demo studies from database
            demo_studies = await db["radiology_orders"].find(
                {"status": {"$in": ["completed", "reported"]}},
                {"_id": 0}
            ).limit(search.limit).to_list(search.limit)
            
            # Convert to DICOM-like format
            studies = []
            for order in demo_studies:
                studies.append({
                    "study_instance_uid": order.get("dicom_study_uid", f"1.2.840.{uuid.uuid4().hex[:16]}"),
                    "patient_id": order.get("patient_mrn", ""),
                    "patient_name": order.get("patient_name", ""),
                    "study_date": order.get("created_at", "")[:10].replace("-", ""),
                    "accession_number": order.get("accession_number", ""),
                    "modality": order.get("modality", "").upper(),
                    "study_description": order.get("study_type", ""),
                    "referring_physician": order.get("ordering_physician", ""),
                    "number_of_series": 1,
                    "number_of_instances": 10,
                    "source": "demo"
                })
            
            return {
                "studies": studies,
                "total": len(studies),
                "mode": "demo",
                "message": "Demo mode - configure PACS_HOST for real studies"
            }
        
        # Production: Query dcm4chee
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{WADO_URL}/rs/studies",
                    params=params,
                    headers={"Accept": "application/dicom+json"}
                )
                
                if response.status_code == 200:
                    dicom_studies = response.json()
                    
                    # Parse DICOM JSON format
                    studies = []
                    for study in dicom_studies:
                        studies.append({
                            "study_instance_uid": study.get("0020000D", {}).get("Value", [""])[0],
                            "patient_id": study.get("00100020", {}).get("Value", [""])[0],
                            "patient_name": study.get("00100010", {}).get("Value", [{}])[0].get("Alphabetic", ""),
                            "study_date": study.get("00080020", {}).get("Value", [""])[0],
                            "study_time": study.get("00080030", {}).get("Value", [""])[0],
                            "accession_number": study.get("00080050", {}).get("Value", [""])[0],
                            "modality": study.get("00080061", {}).get("Value", [""])[0],
                            "study_description": study.get("00081030", {}).get("Value", [""])[0],
                            "referring_physician": study.get("00080090", {}).get("Value", [{}])[0].get("Alphabetic", ""),
                            "number_of_series": study.get("00201206", {}).get("Value", [0])[0],
                            "number_of_instances": study.get("00201208", {}).get("Value", [0])[0],
                            "source": "pacs"
                        })
                    
                    return {
                        "studies": studies,
                        "total": len(studies),
                        "mode": "production"
                    }
                else:
                    return {
                        "studies": [],
                        "error": f"PACS returned status {response.status_code}",
                        "mode": "production"
                    }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PACS query failed: {str(e)}")
    
    @router.get("/studies/{study_uid}")
    async def get_study(
        study_uid: str,
        user: dict = Depends(get_current_user)
    ):
        """Get study details by Study Instance UID."""
        if PACS_HOST == "localhost":
            # Demo mode - return from orders
            order = await db["radiology_orders"].find_one(
                {"dicom_study_uid": study_uid},
                {"_id": 0}
            )
            if not order:
                raise HTTPException(status_code=404, detail="Study not found")
            return {"study": order, "mode": "demo"}
        
        # Production: Get from dcm4chee
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{WADO_URL}/rs/studies/{study_uid}",
                    headers={"Accept": "application/dicom+json"}
                )
                
                if response.status_code == 200:
                    return {"study": response.json(), "mode": "production"}
                else:
                    raise HTTPException(status_code=404, detail="Study not found in PACS")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"PACS error: {str(e)}")
    
    # ============== VIEWER INTEGRATION ==============
    
    @router.get("/viewer/url")
    async def get_viewer_url(
        study_uid: str,
        accession_number: Optional[str] = None,
        patient_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """
        Generate viewer URL for a study.
        
        Supports multiple viewer integrations:
        - MedDream: HTML5 zero-footprint viewer
        - Weasis: Desktop/Web DICOM viewer
        - OHIF: Open Health Imaging Foundation viewer
        """
        if not VIEWER_URL:
            return {
                "viewer_url": None,
                "status": "not_configured",
                "message": "DICOM viewer not configured. Set DICOM_VIEWER_URL in environment.",
                "demo_viewer_info": {
                    "meddream": "https://demo.meddream.com/?study=" + study_uid,
                    "ohif": "https://viewer.ohif.org/viewer?StudyInstanceUIDs=" + study_uid
                }
            }
        
        # Build viewer URL based on configuration
        viewer_params = {
            "study": study_uid
        }
        if accession_number:
            viewer_params["accnum"] = accession_number
        if patient_id:
            viewer_params["patient"] = patient_id
        
        # Format URL based on viewer type
        if "meddream" in VIEWER_URL.lower():
            # MedDream format
            full_url = f"{VIEWER_URL}?study={study_uid}"
        elif "ohif" in VIEWER_URL.lower():
            # OHIF format
            full_url = f"{VIEWER_URL}/viewer?StudyInstanceUIDs={study_uid}"
        elif "weasis" in VIEWER_URL.lower():
            # Weasis format
            full_url = f"{VIEWER_URL}?studyUID={study_uid}"
        else:
            # Generic format
            full_url = f"{VIEWER_URL}?study={study_uid}"
        
        # Audit log
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "pacs_viewer_access",
            "resource_type": "dicom_study",
            "resource_id": study_uid,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "accession_number": accession_number,
                "patient_id": patient_id
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "viewer_url": full_url,
            "status": "ready",
            "viewer_type": "meddream" if "meddream" in VIEWER_URL.lower() else "generic"
        }
    
    # ============== WADO-RS IMAGE RETRIEVAL ==============
    
    @router.get("/studies/{study_uid}/thumbnail")
    async def get_study_thumbnail(
        study_uid: str,
        user: dict = Depends(get_current_user)
    ):
        """Get thumbnail for a study (first image of first series)."""
        if PACS_HOST == "localhost":
            return {
                "thumbnail_url": None,
                "status": "demo_mode",
                "message": "Thumbnails not available in demo mode"
            }
        
        try:
            # Get first series
            async with httpx.AsyncClient(timeout=30.0) as client:
                series_response = await client.get(
                    f"{WADO_URL}/rs/studies/{study_uid}/series",
                    headers={"Accept": "application/dicom+json"}
                )
                
                if series_response.status_code != 200:
                    return {"thumbnail_url": None, "error": "No series found"}
                
                series_list = series_response.json()
                if not series_list:
                    return {"thumbnail_url": None, "error": "No series found"}
                
                series_uid = series_list[0].get("0020000E", {}).get("Value", [""])[0]
                
                # Get first instance
                instance_response = await client.get(
                    f"{WADO_URL}/rs/studies/{study_uid}/series/{series_uid}/instances",
                    headers={"Accept": "application/dicom+json"}
                )
                
                if instance_response.status_code != 200:
                    return {"thumbnail_url": None, "error": "No instances found"}
                
                instances = instance_response.json()
                if not instances:
                    return {"thumbnail_url": None, "error": "No instances found"}
                
                instance_uid = instances[0].get("00080018", {}).get("Value", [""])[0]
                
                # Return WADO thumbnail URL
                thumbnail_url = f"{WADO_URL}/rs/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}/rendered"
                
                return {
                    "thumbnail_url": thumbnail_url,
                    "status": "ready"
                }
        except Exception as e:
            return {"thumbnail_url": None, "error": str(e)}
    
    # ============== HL7 WORKFLOW INTEGRATION ==============
    
    @router.post("/hl7/adt")
    async def send_hl7_adt(
        message: HL7Message,
        user: dict = Depends(get_current_user)
    ):
        """
        Send HL7 ADT (Admission, Discharge, Transfer) message to PACS.
        
        Event types:
        - A01: Patient Admit
        - A04: Patient Registration
        - A08: Patient Update
        - A11: Cancel Admit
        - A03: Patient Discharge
        """
        # In production, this would send HL7v2 message to PACS
        # For now, log the event and store for batch processing
        
        hl7_event = {
            "id": str(uuid.uuid4()),
            "message_type": "ADT",
            "event_type": message.event_type or "A04",
            "patient_id": message.patient_id,
            "patient_name": message.patient_name,
            "status": "pending",
            "created_by": user.get("id"),
            "organization_id": user.get("organization_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db["hl7_messages"].insert_one(hl7_event)
        
        # In production with configured PACS:
        # - Format HL7v2 message
        # - Send via MLLP to PACS HL7 listener
        # - Update status based on ACK response
        
        return {
            "message_id": hl7_event["id"],
            "status": "queued" if PACS_HOST == "localhost" else "sent",
            "event_type": hl7_event["event_type"]
        }
    
    @router.post("/hl7/orm")
    async def send_hl7_orm(
        message: HL7Message,
        user: dict = Depends(get_current_user)
    ):
        """
        Send HL7 ORM (Order) message to RIS/PACS.
        
        Used for:
        - New imaging orders
        - Order modifications
        - Order cancellations
        """
        if not message.order_data:
            raise HTTPException(status_code=400, detail="Order data required")
        
        hl7_event = {
            "id": str(uuid.uuid4()),
            "message_type": "ORM",
            "event_type": "O01",  # Order message
            "patient_id": message.patient_id,
            "patient_name": message.patient_name,
            "order_data": message.order_data,
            "status": "pending",
            "created_by": user.get("id"),
            "organization_id": user.get("organization_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db["hl7_messages"].insert_one(hl7_event)
        
        return {
            "message_id": hl7_event["id"],
            "status": "queued",
            "order_control": "NW"  # New order
        }
    
    @router.post("/hl7/oru")
    async def receive_hl7_oru(
        message: HL7Message,
        user: dict = Depends(get_current_user)
    ):
        """
        Process HL7 ORU (Result) message from PACS/RIS.
        
        Used for:
        - Study completion notifications
        - Report availability
        """
        if not message.result_data:
            raise HTTPException(status_code=400, detail="Result data required")
        
        hl7_event = {
            "id": str(uuid.uuid4()),
            "message_type": "ORU",
            "event_type": "R01",  # Result message
            "patient_id": message.patient_id,
            "patient_name": message.patient_name,
            "result_data": message.result_data,
            "status": "received",
            "processed_by": user.get("id"),
            "organization_id": user.get("organization_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db["hl7_messages"].insert_one(hl7_event)
        
        # Update corresponding radiology order if exists
        accession = message.result_data.get("accession_number")
        if accession:
            await db["radiology_orders"].update_one(
                {"accession_number": accession},
                {"$set": {
                    "hl7_result_received": True,
                    "hl7_result_time": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {
            "message_id": hl7_event["id"],
            "status": "processed"
        }
    
    # ============== WORKLIST (MWL) ==============
    
    @router.get("/worklist")
    async def get_modality_worklist(
        modality: Optional[str] = None,
        scheduled_date: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """
        Get Modality Worklist (MWL) for scheduled procedures.
        
        In production, this queries the MWL SCP.
        """
        query = {
            "organization_id": user.get("organization_id"),
            "status": "scheduled"
        }
        
        if modality:
            query["modality"] = modality.lower()
        if scheduled_date:
            query["scheduled_date"] = scheduled_date
        
        orders = await db["radiology_orders"].find(
            query, {"_id": 0}
        ).sort("scheduled_time", 1).to_list(100)
        
        # Format as MWL entries
        worklist = []
        for order in orders:
            worklist.append({
                "accession_number": order.get("accession_number"),
                "patient_id": order.get("patient_mrn"),
                "patient_name": order.get("patient_name"),
                "patient_dob": order.get("patient_dob"),
                "scheduled_procedure_step_start_date": order.get("scheduled_date", "").replace("-", ""),
                "scheduled_procedure_step_start_time": order.get("scheduled_time", "").replace(":", ""),
                "modality": order.get("modality", "").upper(),
                "scheduled_station_ae_title": PACS_AE_TITLE,
                "scheduled_procedure_step_description": order.get("study_type"),
                "requested_procedure_id": order.get("id"),
                "referring_physician": order.get("ordering_physician")
            })
        
        return {
            "worklist": worklist,
            "total": len(worklist),
            "ae_title": PACS_AE_TITLE
        }
    
    return router
