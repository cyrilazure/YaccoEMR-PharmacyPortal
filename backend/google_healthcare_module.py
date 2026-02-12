"""
Google Cloud Healthcare API Integration Module for Yacco Health EMR
====================================================================
Integrates with Google Cloud Healthcare API for FHIR, HL7v2, and DICOM operations.

Features:
- FHIR resource management (Patient, Observation, Encounter, etc.)
- HL7v2 message ingestion and retrieval
- DICOM instance storage and retrieval
- Dataset and store management
"""

import os
import json
import base64
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body, File, UploadFile, Query
from pydantic import BaseModel, Field
from google.oauth2 import service_account
from googleapiclient import discovery

# Import security
from security import get_current_user, TokenPayload, require_roles, audit_log
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# ============== Configuration ==============

GOOGLE_CREDENTIALS_PATH = os.environ.get("GOOGLE_HEALTHCARE_CREDENTIALS", "/app/backend/google_healthcare_credentials.json")
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "my-second-project-36094")
HEALTHCARE_REGION = os.environ.get("HEALTHCARE_REGION", "us-central1")
HEALTHCARE_DATASET_ID = os.environ.get("HEALTHCARE_DATASET_ID", "yacco-emr-dataset")
FHIR_STORE_ID = os.environ.get("FHIR_STORE_ID", "yacco-fhir-store")
HL7V2_STORE_ID = os.environ.get("HL7V2_STORE_ID", "yacco-hl7v2-store")
DICOM_STORE_ID = os.environ.get("DICOM_STORE_ID", "yacco-dicom-store")


# ============== Healthcare API Client ==============

def get_healthcare_client():
    """Initialize and return Google Healthcare API client."""
    try:
        if os.path.exists(GOOGLE_CREDENTIALS_PATH):
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/cloud-healthcare']
            )
            return discovery.build('healthcare', 'v1', credentials=credentials)
        else:
            logger.warning("Google Healthcare credentials not found, using default credentials")
            return discovery.build('healthcare', 'v1')
    except Exception as e:
        logger.error(f"Failed to initialize Healthcare client: {e}")
        return None


# ============== Pydantic Models ==============

class FHIRResourceCreate(BaseModel):
    """Create a FHIR resource"""
    resource_type: str = "Patient"
    resource_data: Dict[str, Any]

class HL7MessageCreate(BaseModel):
    """Create an HL7v2 message"""
    message_content: str
    labels: Optional[Dict[str, str]] = None

class HealthcareConfigResponse(BaseModel):
    """Healthcare API configuration response"""
    project_id: str
    region: str
    dataset_id: str
    fhir_store_id: str
    hl7v2_store_id: str
    dicom_store_id: str
    credentials_configured: bool
    status: str


# ============== Router Setup ==============

def create_google_healthcare_router(db_client: AsyncIOMotorClient):
    """Create and return the Google Healthcare API router."""
    
    router = APIRouter(prefix="/api/google-healthcare", tags=["Google Healthcare API"])
    
    @router.get("/config")
    async def get_healthcare_config(
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get current Healthcare API configuration."""
        credentials_exist = os.path.exists(GOOGLE_CREDENTIALS_PATH)
        client = get_healthcare_client()
        
        return {
            "project_id": GOOGLE_PROJECT_ID,
            "region": HEALTHCARE_REGION,
            "dataset_id": HEALTHCARE_DATASET_ID,
            "fhir_store_id": FHIR_STORE_ID,
            "hl7v2_store_id": HL7V2_STORE_ID,
            "dicom_store_id": DICOM_STORE_ID,
            "credentials_configured": credentials_exist,
            "client_initialized": client is not None,
            "status": "ready" if credentials_exist and client else "not_configured"
        }
    
    @router.post("/datasets/create")
    async def create_healthcare_dataset(
        dataset_id: str = Query(default=HEALTHCARE_DATASET_ID),
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "super_admin"))
    ):
        """Create a Healthcare API dataset."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            parent = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}"
            
            # Check if dataset exists
            try:
                client.projects().locations().datasets().get(
                    name=f"{parent}/datasets/{dataset_id}"
                ).execute()
                return {"message": f"Dataset {dataset_id} already exists", "dataset_id": dataset_id}
            except Exception:
                pass
            
            # Create dataset
            body = {}
            result = client.projects().locations().datasets().create(
                parent=parent,
                body=body,
                datasetId=dataset_id
            ).execute()
            
            await audit_log(
                db_client,
                current_user.user_id,
                "healthcare_dataset_created",
                {"dataset_id": dataset_id},
                current_user.organization_id
            )
            
            logger.info(f"Created Healthcare dataset: {dataset_id}")
            return {"message": "Dataset created successfully", "dataset_id": dataset_id, "result": result}
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.post("/fhir-store/create")
    async def create_fhir_store(
        store_id: str = Query(default=FHIR_STORE_ID),
        fhir_version: str = Query(default="R4"),
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "super_admin"))
    ):
        """Create a FHIR data store."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            parent = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}"
            
            body = {
                "version": fhir_version
            }
            
            result = client.projects().locations().datasets().fhirStores().create(
                parent=parent,
                body=body,
                fhirStoreId=store_id
            ).execute()
            
            await audit_log(
                db_client,
                current_user.user_id,
                "fhir_store_created",
                {"store_id": store_id, "version": fhir_version},
                current_user.organization_id
            )
            
            logger.info(f"Created FHIR store: {store_id}")
            return {"message": "FHIR store created successfully", "store_id": store_id, "result": result}
            
        except Exception as e:
            logger.error(f"Failed to create FHIR store: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.post("/fhir/patients")
    async def create_fhir_patient(
        patient_data: Dict[str, Any] = Body(...),
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "physician", "nurse", "receptionist", "hospital_admin"))
    ):
        """Create a FHIR Patient resource."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            # Ensure resource type
            patient_data["resourceType"] = "Patient"
            
            fhir_store_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/fhirStores/{FHIR_STORE_ID}"
            
            result = client.projects().locations().datasets().fhirStores().fhir().create(
                parent=fhir_store_path,
                type="Patient",
                body=patient_data
            ).execute()
            
            await audit_log(
                db_client,
                current_user.user_id,
                "fhir_patient_created",
                {"patient_id": result.get("id")},
                current_user.organization_id
            )
            
            logger.info(f"Created FHIR Patient: {result.get('id')}")
            return {"success": True, "patient": result}
            
        except Exception as e:
            logger.error(f"Failed to create FHIR patient: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/fhir/patients/{patient_id}")
    async def get_fhir_patient(
        patient_id: str,
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "physician", "nurse", "nursing_supervisor", "floor_supervisor", "hospital_admin"))
    ):
        """Retrieve a FHIR Patient resource."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            resource_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/fhirStores/{FHIR_STORE_ID}/fhir/Patient/{patient_id}"
            
            result = client.projects().locations().datasets().fhirStores().fhir().read(
                name=resource_path
            ).execute()
            
            return {"success": True, "patient": result}
            
        except Exception as e:
            logger.error(f"Failed to retrieve FHIR patient: {e}")
            raise HTTPException(status_code=404, detail=str(e))
    
    @router.get("/fhir/patients")
    async def search_fhir_patients(
        name: Optional[str] = None,
        birthdate: Optional[str] = None,
        identifier: Optional[str] = None,
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "physician", "nurse", "nursing_supervisor", "floor_supervisor", "hospital_admin"))
    ):
        """Search for FHIR Patient resources."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            fhir_store_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/fhirStores/{FHIR_STORE_ID}"
            
            # Build query parameters
            query_params = {}
            if name:
                query_params["name"] = name
            if birthdate:
                query_params["birthdate"] = birthdate
            if identifier:
                query_params["identifier"] = identifier
            
            result = client.projects().locations().datasets().fhirStores().fhir().search(
                parent=fhir_store_path,
                body={"resourceType": "Patient", **query_params}
            ).execute()
            
            return {"success": True, "results": result}
            
        except Exception as e:
            logger.error(f"Failed to search FHIR patients: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.post("/hl7v2/messages/ingest")
    async def ingest_hl7v2_message(
        message: HL7MessageCreate,
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "hospital_admin"))
    ):
        """Ingest an HL7v2 message."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            hl7v2_store_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/hl7V2Stores/{HL7V2_STORE_ID}"
            
            # Base64 encode the message
            encoded_message = base64.b64encode(message.message_content.encode()).decode()
            
            body = {
                "message": {
                    "data": encoded_message
                }
            }
            
            if message.labels:
                body["message"]["labels"] = message.labels
            
            result = client.projects().locations().datasets().hl7V2Stores().messages().ingest(
                parent=hl7v2_store_path,
                body=body
            ).execute()
            
            await audit_log(
                db_client,
                current_user.user_id,
                "hl7v2_message_ingested",
                {"message_id": result.get("hl7Ack")},
                current_user.organization_id
            )
            
            logger.info(f"Ingested HL7v2 message")
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"Failed to ingest HL7v2 message: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/hl7v2/messages")
    async def list_hl7v2_messages(
        limit: int = Query(default=50, le=100),
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "hospital_admin"))
    ):
        """List HL7v2 messages."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            hl7v2_store_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/hl7V2Stores/{HL7V2_STORE_ID}"
            
            result = client.projects().locations().datasets().hl7V2Stores().messages().list(
                parent=hl7v2_store_path,
                pageSize=limit
            ).execute()
            
            messages = result.get("hl7V2Messages", [])
            return {
                "success": True,
                "total": len(messages),
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Failed to list HL7v2 messages: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.post("/dicom/instances/store")
    async def store_dicom_instance(
        file: UploadFile = File(...),
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "physician", "hospital_admin"))
    ):
        """Store a DICOM instance."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            # Read file content
            content = await file.read()
            
            dicom_store_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/dicomStores/{DICOM_STORE_ID}"
            
            result = client.projects().locations().datasets().dicomStores().storeInstances(
                parent=dicom_store_path,
                dicomWebPath="studies",
                body=content
            ).execute()
            
            await audit_log(
                db_client,
                current_user.user_id,
                "dicom_instance_stored",
                {"filename": file.filename},
                current_user.organization_id
            )
            
            logger.info(f"Stored DICOM instance: {file.filename}")
            return {"success": True, "filename": file.filename, "result": result}
            
        except Exception as e:
            logger.error(f"Failed to store DICOM instance: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/dicom/instances")
    async def search_dicom_instances(
        study_instance_uid: Optional[str] = None,
        current_user: TokenPayload = Depends(require_roles("hospital_it_admin", "physician", "hospital_admin"))
    ):
        """Search for DICOM instances."""
        try:
            client = get_healthcare_client()
            if not client:
                raise HTTPException(status_code=503, detail="Healthcare client not initialized")
            
            dicom_store_path = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}/datasets/{HEALTHCARE_DATASET_ID}/dicomStores/{DICOM_STORE_ID}"
            
            dicom_web_path = "instances"
            if study_instance_uid:
                dicom_web_path = f"studies/{study_instance_uid}/instances"
            
            result = client.projects().locations().datasets().dicomStores().searchForInstances(
                parent=dicom_store_path,
                dicomWebPath=dicom_web_path
            ).execute()
            
            return {"success": True, "instances": result}
            
        except Exception as e:
            logger.error(f"Failed to search DICOM instances: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @router.get("/status")
    async def get_healthcare_status(
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get Healthcare API connection status."""
        try:
            client = get_healthcare_client()
            
            if not client:
                return {
                    "status": "error",
                    "message": "Healthcare client not initialized",
                    "credentials_found": os.path.exists(GOOGLE_CREDENTIALS_PATH)
                }
            
            # Try to list datasets to verify connection
            parent = f"projects/{GOOGLE_PROJECT_ID}/locations/{HEALTHCARE_REGION}"
            try:
                result = client.projects().locations().datasets().list(
                    parent=parent
                ).execute()
                
                datasets = result.get("datasets", [])
                return {
                    "status": "connected",
                    "project_id": GOOGLE_PROJECT_ID,
                    "region": HEALTHCARE_REGION,
                    "datasets_count": len(datasets),
                    "datasets": [d.get("name", "").split("/")[-1] for d in datasets]
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to connect to Healthcare API: {str(e)}",
                    "credentials_found": os.path.exists(GOOGLE_CREDENTIALS_PATH)
                }
                
        except Exception as e:
            logger.error(f"Failed to get healthcare status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    return router


# ============== Module Export ==============

google_healthcare_router = APIRouter(prefix="/api/google-healthcare", tags=["Google Healthcare API"])
