"""
Medical Records Sharing Module for Yacco EMR
Handles inter-hospital physician search, records requests, consent management, and notifications
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import os
import aiofiles
import base64

router = APIRouter(prefix="/api/records-sharing", tags=["Records Sharing"])

# Create uploads directory for consent forms
CONSENT_UPLOAD_DIR = "/app/backend/uploads/consent_forms"
os.makedirs(CONSENT_UPLOAD_DIR, exist_ok=True)

# ============ ENUMS ============
class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class NotificationType(str, Enum):
    RECORDS_REQUEST = "records_request"
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    ACCESS_GRANTED = "access_granted"
    ACCESS_EXPIRING = "access_expiring"

# ============ MODELS ============
class PhysicianSearchResult(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    specialty: Optional[str] = None
    department: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    hospital_name: Optional[str] = None

class RecordsRequestCreate(BaseModel):
    target_physician_id: str  # Physician who has the records
    patient_id: str
    patient_name: str
    reason: str  # Clinical reason for request
    urgency: str = "routine"  # routine, urgent, emergency
    requested_records: List[str] = ["all"]  # Types of records: all, vitals, medications, notes, labs, imaging
    consent_signed: bool = True
    consent_date: Optional[str] = None

class RecordsRequestResponse(BaseModel):
    id: str
    request_number: str
    requesting_physician_id: str
    requesting_physician_name: str
    requesting_organization: str
    target_physician_id: str
    target_physician_name: str
    target_organization: str
    patient_id: str
    patient_name: str
    reason: str
    urgency: str
    requested_records: List[str]
    consent_form_url: Optional[str] = None
    status: str
    created_at: str
    responded_at: Optional[str] = None
    response_notes: Optional[str] = None
    access_expires_at: Optional[str] = None

class RequestResponse(BaseModel):
    approved: bool
    notes: Optional[str] = None
    access_duration_days: int = 30  # How long the requesting physician can access records

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    related_request_id: Optional[str] = None
    read: bool
    created_at: str


def setup_routes(db, get_current_user):
    """Setup records sharing routes with database and auth dependency"""
    
    # ============ PHYSICIAN DIRECTORY ============
    @router.get("/physicians/search")
    async def search_physicians(
        query: Optional[str] = None,
        specialty: Optional[str] = None,
        organization_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Search for physicians across all organizations"""
        search_query = {"role": {"$in": ["physician", "hospital_admin"]}}
        
        if query:
            search_query["$or"] = [
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"specialty": {"$regex": query, "$options": "i"}}
            ]
        
        if specialty:
            search_query["specialty"] = {"$regex": specialty, "$options": "i"}
        
        if organization_id:
            search_query["organization_id"] = organization_id
        
        # Exclude current user from results
        search_query["id"] = {"$ne": current_user["id"]}
        
        physicians = await db.users.find(
            search_query,
            {"_id": 0, "password": 0}
        ).to_list(100)
        
        # Enrich with organization names
        results = []
        for physician in physicians:
            org_name = "Independent"
            hospital_name = None
            
            if physician.get("organization_id"):
                org = await db.organizations.find_one(
                    {"id": physician["organization_id"]},
                    {"_id": 0, "name": 1}
                )
                if org:
                    org_name = org.get("name", "Unknown Hospital")
                    hospital_name = org_name
            
            results.append({
                "id": physician["id"],
                "first_name": physician["first_name"],
                "last_name": physician["last_name"],
                "email": physician["email"],
                "specialty": physician.get("specialty"),
                "department": physician.get("department"),
                "organization_id": physician.get("organization_id"),
                "organization_name": org_name,
                "hospital_name": hospital_name
            })
        
        return {"physicians": results, "count": len(results)}
    
    @router.get("/physicians/{physician_id}")
    async def get_physician_profile(
        physician_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get detailed physician profile"""
        physician = await db.users.find_one(
            {"id": physician_id, "role": {"$in": ["physician", "hospital_admin"]}},
            {"_id": 0, "password": 0}
        )
        
        if not physician:
            raise HTTPException(status_code=404, detail="Physician not found")
        
        # Get organization info
        org_info = None
        if physician.get("organization_id"):
            org = await db.organizations.find_one(
                {"id": physician["organization_id"]},
                {"_id": 0}
            )
            if org:
                org_info = {
                    "id": org["id"],
                    "name": org.get("name"),
                    "address": org.get("address"),
                    "city": org.get("city"),
                    "state": org.get("state")
                }
        
        return {
            **physician,
            "organization": org_info
        }
    
    # ============ RECORDS REQUESTS ============
    @router.post("/requests")
    async def create_records_request(
        request_data: RecordsRequestCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a request for patient medical records"""
        if current_user.get("role") not in ["physician", "hospital_admin"]:
            raise HTTPException(status_code=403, detail="Only physicians can request records")
        
        # Verify target physician exists
        target_physician = await db.users.find_one(
            {"id": request_data.target_physician_id, "role": {"$in": ["physician", "hospital_admin"]}},
            {"_id": 0, "password": 0}
        )
        
        if not target_physician:
            raise HTTPException(status_code=404, detail="Target physician not found")
        
        # Get organization names
        requesting_org_name = "Independent"
        target_org_name = "Independent"
        
        if current_user.get("organization_id"):
            org = await db.organizations.find_one({"id": current_user["organization_id"]})
            if org:
                requesting_org_name = org.get("name", "Unknown")
        
        if target_physician.get("organization_id"):
            org = await db.organizations.find_one({"id": target_physician["organization_id"]})
            if org:
                target_org_name = org.get("name", "Unknown")
        
        # Generate request number
        req_count = await db.records_requests.count_documents({})
        request_number = f"RR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{req_count + 1:05d}"
        
        request_doc = {
            "id": str(uuid.uuid4()),
            "request_number": request_number,
            "requesting_physician_id": current_user["id"],
            "requesting_physician_name": f"{current_user['first_name']} {current_user['last_name']}",
            "requesting_organization_id": current_user.get("organization_id"),
            "requesting_organization": requesting_org_name,
            "target_physician_id": request_data.target_physician_id,
            "target_physician_name": f"{target_physician['first_name']} {target_physician['last_name']}",
            "target_organization_id": target_physician.get("organization_id"),
            "target_organization": target_org_name,
            "patient_id": request_data.patient_id,
            "patient_name": request_data.patient_name,
            "reason": request_data.reason,
            "urgency": request_data.urgency,
            "requested_records": request_data.requested_records,
            "consent_signed": request_data.consent_signed,
            "consent_date": request_data.consent_date or datetime.now(timezone.utc).isoformat(),
            "consent_form_url": None,
            "status": RequestStatus.PENDING,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "responded_at": None,
            "response_notes": None,
            "access_expires_at": None
        }
        
        await db.records_requests.insert_one(request_doc)
        
        # Create notification for target physician
        notification_doc = {
            "id": str(uuid.uuid4()),
            "user_id": target_physician["id"],
            "type": NotificationType.RECORDS_REQUEST,
            "title": "New Medical Records Request",
            "message": f"Dr. {current_user['first_name']} {current_user['last_name']} from {requesting_org_name} is requesting access to patient {request_data.patient_name}'s medical records.",
            "related_request_id": request_doc["id"],
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.notifications.insert_one(notification_doc)
        
        return {
            "message": "Records request submitted successfully",
            "request_id": request_doc["id"],
            "request_number": request_number,
            "status": RequestStatus.PENDING
        }
    
    @router.post("/requests/{request_id}/consent-form")
    async def upload_consent_form(
        request_id: str,
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
    ):
        """Upload signed patient consent form"""
        request = await db.records_requests.find_one({"id": request_id})
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request["requesting_physician_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Save file
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        filename = f"consent_{request_id}.{file_extension}"
        file_path = os.path.join(CONSENT_UPLOAD_DIR, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Update request
        await db.records_requests.update_one(
            {"id": request_id},
            {"$set": {"consent_form_url": f"/api/records-sharing/consent/{request_id}"}}
        )
        
        return {"message": "Consent form uploaded", "url": f"/api/records-sharing/consent/{request_id}"}
    
    @router.get("/consent/{request_id}")
    async def get_consent_form(
        request_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get uploaded consent form"""
        request = await db.records_requests.find_one({"id": request_id})
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Check authorization
        if current_user["id"] not in [request["requesting_physician_id"], request["target_physician_id"]]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Find consent file
        for ext in ['pdf', 'png', 'jpg', 'jpeg']:
            file_path = os.path.join(CONSENT_UPLOAD_DIR, f"consent_{request_id}.{ext}")
            if os.path.exists(file_path):
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                    return {
                        "filename": f"consent_{request_id}.{ext}",
                        "content": base64.b64encode(content).decode('utf-8'),
                        "content_type": f"application/{ext}" if ext == 'pdf' else f"image/{ext}"
                    }
        
        raise HTTPException(status_code=404, detail="Consent form not found")
    
    @router.get("/requests/incoming")
    async def get_incoming_requests(
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get incoming records requests (requests TO the current physician)"""
        query = {"target_physician_id": current_user["id"]}
        
        if status:
            query["status"] = status
        
        requests = await db.records_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return {"requests": requests, "count": len(requests)}
    
    @router.get("/requests/outgoing")
    async def get_outgoing_requests(
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get outgoing records requests (requests FROM the current physician)"""
        query = {"requesting_physician_id": current_user["id"]}
        
        if status:
            query["status"] = status
        
        requests = await db.records_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return {"requests": requests, "count": len(requests)}
    
    @router.get("/requests/{request_id}")
    async def get_request_details(
        request_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get detailed request information"""
        request = await db.records_requests.find_one({"id": request_id}, {"_id": 0})
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Check authorization
        if current_user["id"] not in [request["requesting_physician_id"], request["target_physician_id"]]:
            if current_user.get("role") != "super_admin":
                raise HTTPException(status_code=403, detail="Not authorized")
        
        return request
    
    @router.post("/requests/{request_id}/respond")
    async def respond_to_request(
        request_id: str,
        response: RequestResponse,
        current_user: dict = Depends(get_current_user)
    ):
        """Approve or reject a records request"""
        request = await db.records_requests.find_one({"id": request_id})
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request["target_physician_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Only the target physician can respond")
        
        if request["status"] != RequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request already processed")
        
        # Calculate access expiration if approved
        access_expires_at = None
        if response.approved:
            access_expires_at = (datetime.now(timezone.utc) + timedelta(days=response.access_duration_days)).isoformat()
        
        # Update request
        update_data = {
            "status": RequestStatus.APPROVED if response.approved else RequestStatus.REJECTED,
            "responded_at": datetime.now(timezone.utc).isoformat(),
            "response_notes": response.notes,
            "access_expires_at": access_expires_at
        }
        
        await db.records_requests.update_one(
            {"id": request_id},
            {"$set": update_data}
        )
        
        # Create notification for requesting physician
        if response.approved:
            notification_doc = {
                "id": str(uuid.uuid4()),
                "user_id": request["requesting_physician_id"],
                "type": NotificationType.REQUEST_APPROVED,
                "title": "Records Request Approved",
                "message": f"Dr. {current_user['first_name']} {current_user['last_name']} has approved your request for {request['patient_name']}'s medical records. Access granted for {response.access_duration_days} days.",
                "related_request_id": request_id,
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            notification_doc = {
                "id": str(uuid.uuid4()),
                "user_id": request["requesting_physician_id"],
                "type": NotificationType.REQUEST_REJECTED,
                "title": "Records Request Declined",
                "message": f"Dr. {current_user['first_name']} {current_user['last_name']} has declined your request for {request['patient_name']}'s medical records.{' Reason: ' + response.notes if response.notes else ''}",
                "related_request_id": request_id,
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        
        await db.notifications.insert_one(notification_doc)
        
        # If approved, create access grant record
        if response.approved:
            access_grant = {
                "id": str(uuid.uuid4()),
                "request_id": request_id,
                "patient_id": request["patient_id"],
                "granting_physician_id": current_user["id"],
                "granting_organization_id": current_user.get("organization_id"),
                "granted_physician_id": request["requesting_physician_id"],
                "granted_organization_id": request.get("requesting_organization_id"),
                "records_types": request["requested_records"],
                "granted_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": access_expires_at,
                "active": True
            }
            await db.access_grants.insert_one(access_grant)
        
        return {
            "message": f"Request {'approved' if response.approved else 'rejected'}",
            "status": RequestStatus.APPROVED if response.approved else RequestStatus.REJECTED,
            "access_expires_at": access_expires_at
        }
    
    @router.post("/requests/{request_id}/cancel")
    async def cancel_request(
        request_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Cancel a pending records request"""
        request = await db.records_requests.find_one({"id": request_id})
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request["requesting_physician_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Only the requesting physician can cancel")
        
        if request["status"] != RequestStatus.PENDING:
            raise HTTPException(status_code=400, detail="Only pending requests can be cancelled")
        
        await db.records_requests.update_one(
            {"id": request_id},
            {"$set": {"status": RequestStatus.CANCELLED}}
        )
        
        return {"message": "Request cancelled"}
    
    # ============ SHARED RECORDS ACCESS ============
    @router.get("/shared-records/{patient_id}")
    async def get_shared_patient_records(
        patient_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get patient records that have been shared with the current physician"""
        # Check if there's an active access grant
        access_grant = await db.access_grants.find_one({
            "patient_id": patient_id,
            "granted_physician_id": current_user["id"],
            "active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
        })
        
        if not access_grant:
            raise HTTPException(status_code=403, detail="No active access to this patient's records")
        
        # Get patient info from the granting organization
        patient = await db.patients.find_one(
            {"id": patient_id, "organization_id": access_grant["granting_organization_id"]},
            {"_id": 0}
        )
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient records not found")
        
        records = {"patient": patient}
        records_types = access_grant.get("records_types", ["all"])
        
        # Fetch requested record types
        if "all" in records_types or "vitals" in records_types:
            records["vitals"] = await db.vitals.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).sort("recorded_at", -1).to_list(50)
        
        if "all" in records_types or "problems" in records_types:
            records["problems"] = await db.problems.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).to_list(100)
        
        if "all" in records_types or "medications" in records_types:
            records["medications"] = await db.medications.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).to_list(100)
        
        if "all" in records_types or "allergies" in records_types:
            records["allergies"] = await db.allergies.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).to_list(100)
        
        if "all" in records_types or "notes" in records_types:
            records["notes"] = await db.notes.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).sort("created_at", -1).to_list(50)
        
        if "all" in records_types or "labs" in records_types:
            records["lab_results"] = await db.lab_results.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).sort("resulted_at", -1).to_list(50)
        
        if "all" in records_types or "imaging" in records_types:
            records["imaging_studies"] = await db.imaging_studies.find(
                {"patient_id": patient_id, "organization_id": access_grant["granting_organization_id"]},
                {"_id": 0}
            ).sort("study_date", -1).to_list(50)
        
        # Add access info
        records["access_info"] = {
            "granted_at": access_grant["granted_at"],
            "expires_at": access_grant["expires_at"],
            "records_types": records_types
        }
        
        return records
    
    @router.get("/my-access-grants")
    async def get_my_access_grants(
        current_user: dict = Depends(get_current_user)
    ):
        """Get all active access grants for the current physician"""
        grants = await db.access_grants.find(
            {
                "granted_physician_id": current_user["id"],
                "active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
            },
            {"_id": 0}
        ).to_list(100)
        
        # Enrich with patient and physician info
        enriched_grants = []
        for grant in grants:
            # Get patient info
            patient = await db.patients.find_one({"id": grant["patient_id"]}, {"_id": 0, "first_name": 1, "last_name": 1, "mrn": 1})
            
            # Get granting physician info
            granting_physician = await db.users.find_one({"id": grant["granting_physician_id"]}, {"_id": 0, "first_name": 1, "last_name": 1})
            
            # Get organization name
            org = await db.organizations.find_one({"id": grant["granting_organization_id"]}, {"_id": 0, "name": 1})
            
            enriched_grants.append({
                **grant,
                "patient_name": f"{patient['first_name']} {patient['last_name']}" if patient else "Unknown",
                "patient_mrn": patient.get("mrn") if patient else None,
                "granting_physician_name": f"{granting_physician['first_name']} {granting_physician['last_name']}" if granting_physician else "Unknown",
                "granting_organization_name": org.get("name") if org else "Unknown"
            })
        
        return {"access_grants": enriched_grants, "count": len(enriched_grants)}
    
    # ============ NOTIFICATIONS ============
    @router.get("/notifications")
    async def get_notifications(
        unread_only: bool = False,
        current_user: dict = Depends(get_current_user)
    ):
        """Get notifications for the current user"""
        query = {"user_id": current_user["id"]}
        
        if unread_only:
            query["read"] = False
        
        notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        unread_count = await db.notifications.count_documents({
            "user_id": current_user["id"],
            "read": False
        })
        
        return {
            "notifications": notifications,
            "count": len(notifications),
            "unread_count": unread_count
        }
    
    @router.put("/notifications/{notification_id}/read")
    async def mark_notification_read(
        notification_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Mark a notification as read"""
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": current_user["id"]},
            {"$set": {"read": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
    
    @router.put("/notifications/read-all")
    async def mark_all_notifications_read(
        current_user: dict = Depends(get_current_user)
    ):
        """Mark all notifications as read"""
        await db.notifications.update_many(
            {"user_id": current_user["id"], "read": False},
            {"$set": {"read": True}}
        )
        
        return {"message": "All notifications marked as read"}
    
    # ============ STATISTICS ============
    @router.get("/stats")
    async def get_sharing_stats(
        current_user: dict = Depends(get_current_user)
    ):
        """Get records sharing statistics"""
        # Incoming requests
        incoming_total = await db.records_requests.count_documents({"target_physician_id": current_user["id"]})
        incoming_pending = await db.records_requests.count_documents({"target_physician_id": current_user["id"], "status": RequestStatus.PENDING})
        incoming_approved = await db.records_requests.count_documents({"target_physician_id": current_user["id"], "status": RequestStatus.APPROVED})
        
        # Outgoing requests
        outgoing_total = await db.records_requests.count_documents({"requesting_physician_id": current_user["id"]})
        outgoing_pending = await db.records_requests.count_documents({"requesting_physician_id": current_user["id"], "status": RequestStatus.PENDING})
        outgoing_approved = await db.records_requests.count_documents({"requesting_physician_id": current_user["id"], "status": RequestStatus.APPROVED})
        
        # Active access grants
        active_grants = await db.access_grants.count_documents({
            "granted_physician_id": current_user["id"],
            "active": True,
            "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
        })
        
        # Unread notifications
        unread_notifications = await db.notifications.count_documents({
            "user_id": current_user["id"],
            "read": False
        })
        
        return {
            "incoming_requests": {
                "total": incoming_total,
                "pending": incoming_pending,
                "approved": incoming_approved
            },
            "outgoing_requests": {
                "total": outgoing_total,
                "pending": outgoing_pending,
                "approved": outgoing_approved
            },
            "active_access_grants": active_grants,
            "unread_notifications": unread_notifications
        }
    
    return router
