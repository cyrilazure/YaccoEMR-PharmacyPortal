"""
Multi-Tenant Organization Module for Yacco EMR
Supports:
- Hospital/Organization management
- Self-service registration with approval workflow
- Staff account management
- Data isolation by organization
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import secrets
import string
import os

organization_router = APIRouter(prefix="/api/organizations", tags=["Organizations"])

# ============ Enums ============

class OrganizationStatus(str, Enum):
    PENDING = "pending"  # Awaiting approval
    ACTIVE = "active"    # Approved and active
    SUSPENDED = "suspended"  # Temporarily suspended
    REJECTED = "rejected"  # Registration rejected

class OrganizationType(str, Enum):
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    MEDICAL_CENTER = "medical_center"
    URGENT_CARE = "urgent_care"
    SPECIALTY_CENTER = "specialty_center"

class StaffStatus(str, Enum):
    PENDING = "pending"  # Invitation sent, not yet accepted
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

# ============ Models ============

class OrganizationCreate(BaseModel):
    name: str
    organization_type: OrganizationType = OrganizationType.HOSPITAL
    # Address
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    # Contact
    phone: str
    fax: Optional[str] = None
    email: EmailStr
    website: Optional[str] = None
    # Registration
    license_number: str
    tax_id: Optional[str] = None
    npi_number: Optional[str] = None  # National Provider Identifier
    # Admin contact (person registering)
    admin_first_name: str
    admin_last_name: str
    admin_email: EmailStr
    admin_phone: str
    admin_title: Optional[str] = "Administrator"

class Organization(OrganizationCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: OrganizationStatus = OrganizationStatus.PENDING
    logo_url: Optional[str] = None
    # Subscription/billing info
    subscription_plan: str = "standard"
    max_users: int = 50
    max_patients: int = 10000
    # Stats
    total_users: int = 0
    total_patients: int = 0
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    license_number: Optional[str] = None
    npi_number: Optional[str] = None

class StaffCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str  # physician, nurse, scheduler, hospital_admin
    department: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None  # For physicians

class StaffInvitation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    department: Optional[str] = None
    specialty: Optional[str] = None
    invitation_token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    status: InvitationStatus = InvitationStatus.PENDING
    invited_by: str
    invited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    accepted_at: Optional[datetime] = None

class StaffDirectCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    department: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    # Temporary password will be auto-generated

class AcceptInvitationRequest(BaseModel):
    token: str
    password: str

class ApproveOrganizationRequest(BaseModel):
    notes: Optional[str] = None
    subscription_plan: Optional[str] = "standard"
    max_users: Optional[int] = 50
    max_patients: Optional[int] = 10000

class RejectOrganizationRequest(BaseModel):
    reason: str

# ============ Helper Functions ============

def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# ============ API Factory ============

def create_organization_endpoints(db, get_current_user, hash_password):
    """Create organization API endpoints with database dependency"""
    
    # ============ Super Admin Endpoints ============
    
    @organization_router.get("/", response_model=dict)
    async def list_organizations(
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = Query(default=50, le=200),
        user: dict = Depends(get_current_user)
    ):
        """List all organizations (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        query = {}
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"license_number": {"$regex": search, "$options": "i"}}
            ]
        
        orgs = await db["organizations"].find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
        
        # Get counts by status
        pending_count = await db["organizations"].count_documents({"status": "pending"})
        active_count = await db["organizations"].count_documents({"status": "active"})
        
        return {
            "organizations": orgs,
            "total": len(orgs),
            "pending_count": pending_count,
            "active_count": active_count
        }
    
    @organization_router.get("/pending", response_model=dict)
    async def get_pending_organizations(user: dict = Depends(get_current_user)):
        """Get organizations pending approval (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        orgs = await db["organizations"].find(
            {"status": OrganizationStatus.PENDING.value},
            {"_id": 0}
        ).sort("created_at", 1).to_list(100)
        
        return {"organizations": orgs, "count": len(orgs)}
    
    @organization_router.post("/{org_id}/approve", response_model=dict)
    async def approve_organization(
        org_id: str,
        request: ApproveOrganizationRequest,
        user: dict = Depends(get_current_user)
    ):
        """Approve a pending organization (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        org = await db["organizations"].find_one({"id": org_id})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org.get("status") != OrganizationStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Organization is not pending approval")
        
        # Update organization status
        update_data = {
            "status": OrganizationStatus.ACTIVE.value,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user.get("id"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "subscription_plan": request.subscription_plan or "standard",
            "max_users": request.max_users or 50,
            "max_patients": request.max_patients or 10000
        }
        if request.notes:
            update_data["notes"] = request.notes
        
        await db["organizations"].update_one(
            {"id": org_id},
            {"$set": update_data}
        )
        
        # Create hospital admin account
        admin_password = generate_temp_password()
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": org.get("admin_email"),
            "password_hash": hash_password(admin_password),
            "first_name": org.get("admin_first_name"),
            "last_name": org.get("admin_last_name"),
            "role": "hospital_admin",
            "organization_id": org_id,
            "department": "Administration",
            "is_active": True,
            "is_temp_password": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if admin user already exists
        existing_user = await db["users"].find_one({"email": org.get("admin_email")})
        if not existing_user:
            await db["users"].insert_one(admin_user)
        
        return {
            "message": "Organization approved successfully",
            "organization_id": org_id,
            "admin_email": org.get("admin_email"),
            "temp_password": admin_password,
            "note": "Please share the temporary password securely with the hospital admin"
        }
    
    @organization_router.post("/{org_id}/reject", response_model=dict)
    async def reject_organization(
        org_id: str,
        request: RejectOrganizationRequest,
        user: dict = Depends(get_current_user)
    ):
        """Reject a pending organization (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        result = await db["organizations"].update_one(
            {"id": org_id, "status": OrganizationStatus.PENDING.value},
            {"$set": {
                "status": OrganizationStatus.REJECTED.value,
                "rejection_reason": request.reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found or not pending")
        
        return {"message": "Organization rejected", "reason": request.reason}
    
    @organization_router.post("/{org_id}/suspend", response_model=dict)
    async def suspend_organization(org_id: str, reason: str = None, user: dict = Depends(get_current_user)):
        """Suspend an active organization (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        result = await db["organizations"].update_one(
            {"id": org_id, "status": OrganizationStatus.ACTIVE.value},
            {"$set": {
                "status": OrganizationStatus.SUSPENDED.value,
                "notes": reason,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found or not active")
        
        return {"message": "Organization suspended"}
    
    @organization_router.post("/{org_id}/reactivate", response_model=dict)
    async def reactivate_organization(org_id: str, user: dict = Depends(get_current_user)):
        """Reactivate a suspended organization (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        result = await db["organizations"].update_one(
            {"id": org_id, "status": OrganizationStatus.SUSPENDED.value},
            {"$set": {
                "status": OrganizationStatus.ACTIVE.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found or not suspended")
        
        return {"message": "Organization reactivated"}
    
    @organization_router.post("/create-by-admin", response_model=dict)
    async def create_organization_by_admin(
        org_data: OrganizationCreate,
        auto_approve: bool = True,
        user: dict = Depends(get_current_user)
    ):
        """Create a new organization directly (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        # Check for duplicate
        existing = await db["organizations"].find_one({
            "$or": [
                {"email": org_data.email},
                {"license_number": org_data.license_number}
            ]
        })
        if existing:
            raise HTTPException(status_code=400, detail="Organization with this email or license already exists")
        
        org = Organization(**org_data.model_dump())
        if auto_approve:
            org.status = OrganizationStatus.ACTIVE
            org.approved_at = datetime.now(timezone.utc)
            org.approved_by = user.get("id")
        
        org_dict = org.model_dump()
        org_dict['created_at'] = org_dict['created_at'].isoformat()
        org_dict['updated_at'] = org_dict['updated_at'].isoformat()
        if org_dict.get('approved_at'):
            org_dict['approved_at'] = org_dict['approved_at'].isoformat()
        
        await db["organizations"].insert_one(org_dict)
        
        # Create admin account if auto-approved
        admin_password = None
        if auto_approve:
            admin_password = generate_temp_password()
            admin_user = {
                "id": str(uuid.uuid4()),
                "email": org_data.admin_email,
                "password_hash": hash_password(admin_password),
                "first_name": org_data.admin_first_name,
                "last_name": org_data.admin_last_name,
                "role": "hospital_admin",
                "organization_id": org.id,
                "department": "Administration",
                "is_active": True,
                "is_temp_password": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db["users"].insert_one(admin_user)
        
        response = {
            "message": "Organization created successfully",
            "organization": org_dict,
            "auto_approved": auto_approve
        }
        if admin_password:
            response["admin_email"] = org_data.admin_email
            response["temp_password"] = admin_password
        
        return response
    
    # ============ Self-Service Registration ============
    
    @organization_router.post("/register", response_model=dict)
    async def register_organization(org_data: OrganizationCreate):
        """Self-service organization registration (Public endpoint)"""
        # Check for duplicate
        existing = await db["organizations"].find_one({
            "$or": [
                {"email": org_data.email},
                {"license_number": org_data.license_number}
            ]
        })
        if existing:
            raise HTTPException(status_code=400, detail="Organization with this email or license already exists")
        
        org = Organization(**org_data.model_dump())
        org.status = OrganizationStatus.PENDING
        
        org_dict = org.model_dump()
        org_dict['created_at'] = org_dict['created_at'].isoformat()
        org_dict['updated_at'] = org_dict['updated_at'].isoformat()
        
        await db["organizations"].insert_one(org_dict)
        
        return {
            "message": "Registration submitted successfully",
            "organization_id": org.id,
            "status": "pending",
            "note": "Your registration is pending approval. You will receive an email once approved."
        }
    
    # ============ Organization Management (Hospital Admin) ============
    
    @organization_router.get("/my-organization", response_model=dict)
    async def get_my_organization(user: dict = Depends(get_current_user)):
        """Get current user's organization details"""
        org_id = user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        org = await db["organizations"].find_one({"id": org_id}, {"_id": 0})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get staff count
        staff_count = await db["users"].count_documents({"organization_id": org_id})
        patient_count = await db["patients"].count_documents({"organization_id": org_id})
        
        org["total_users"] = staff_count
        org["total_patients"] = patient_count
        
        return {"organization": org}
    
    @organization_router.put("/my-organization", response_model=dict)
    async def update_my_organization(
        update_data: OrganizationUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update organization details (Hospital Admin only)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        if not org_id and user.get("role") != "super_admin":
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await db["organizations"].update_one(
            {"id": org_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {"message": "Organization updated successfully"}
    
    @organization_router.get("/{org_id}", response_model=dict)
    async def get_organization(org_id: str, user: dict = Depends(get_current_user)):
        """Get organization by ID"""
        # Check access
        if user.get("role") != "super_admin" and user.get("organization_id") != org_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        org = await db["organizations"].find_one({"id": org_id}, {"_id": 0})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {"organization": org}
    
    # ============ Staff Management ============
    
    @organization_router.get("/staff", response_model=dict)
    async def list_organization_staff(
        status: Optional[str] = None,
        role: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """List all staff in the organization (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        if not org_id and user.get("role") != "super_admin":
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        query = {"organization_id": org_id}
        if status:
            query["is_active"] = status == "active"
        if role:
            query["role"] = role
        
        staff = await db["users"].find(
            query,
            {"_id": 0, "password_hash": 0}
        ).sort("created_at", -1).to_list(200)
        
        return {"staff": staff, "count": len(staff)}
    
    @organization_router.post("/staff/create", response_model=dict)
    async def create_staff_direct(
        staff_data: StaffDirectCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create staff account directly with temporary password (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Check organization limits
        org = await db["organizations"].find_one({"id": org_id})
        if org:
            current_users = await db["users"].count_documents({"organization_id": org_id})
            if current_users >= org.get("max_users", 50):
                raise HTTPException(status_code=400, detail="Organization has reached maximum user limit")
        
        # Check for duplicate email
        existing = await db["users"].find_one({"email": staff_data.email})
        if existing:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Generate temporary password
        temp_password = generate_temp_password()
        
        # Create user
        new_user = {
            "id": str(uuid.uuid4()),
            "email": staff_data.email,
            "password_hash": hash_password(temp_password),
            "first_name": staff_data.first_name,
            "last_name": staff_data.last_name,
            "role": staff_data.role,
            "organization_id": org_id,
            "department": staff_data.department,
            "specialty": staff_data.specialty,
            "phone": staff_data.phone,
            "license_number": staff_data.license_number,
            "is_active": True,
            "is_temp_password": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("id")
        }
        
        await db["users"].insert_one(new_user)
        
        # Update organization user count
        await db["organizations"].update_one(
            {"id": org_id},
            {"$inc": {"total_users": 1}}
        )
        
        return {
            "message": "Staff account created successfully",
            "user_id": new_user["id"],
            "email": staff_data.email,
            "temp_password": temp_password,
            "note": "Please share the temporary password securely with the staff member"
        }
    
    @organization_router.post("/staff/invite", response_model=dict)
    async def invite_staff(
        staff_data: StaffCreate,
        user: dict = Depends(get_current_user)
    ):
        """Send invitation to staff member (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="User is not associated with an organization")
        
        # Check for existing user or invitation
        existing_user = await db["users"].find_one({"email": staff_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        existing_invite = await db["staff_invitations"].find_one({
            "email": staff_data.email,
            "status": InvitationStatus.PENDING.value
        })
        if existing_invite:
            raise HTTPException(status_code=400, detail="Pending invitation already exists for this email")
        
        # Create invitation
        invitation = StaffInvitation(
            organization_id=org_id,
            email=staff_data.email,
            first_name=staff_data.first_name,
            last_name=staff_data.last_name,
            role=staff_data.role,
            department=staff_data.department,
            specialty=staff_data.specialty,
            invited_by=user.get("id")
        )
        
        invitation_dict = invitation.model_dump()
        invitation_dict['invited_at'] = invitation_dict['invited_at'].isoformat()
        invitation_dict['expires_at'] = invitation_dict['expires_at'].isoformat()
        
        await db["staff_invitations"].insert_one(invitation_dict)
        
        # Get organization name for email
        org = await db["organizations"].find_one({"id": org_id})
        org_name = org.get("name", "Organization") if org else "Organization"
        
        return {
            "message": "Invitation sent successfully",
            "invitation_id": invitation.id,
            "invitation_token": invitation.invitation_token,
            "invitation_link": f"/accept-invitation?token={invitation.invitation_token}",
            "expires_at": invitation_dict['expires_at'],
            "note": f"Please share the invitation link with {staff_data.first_name} {staff_data.last_name}"
        }
    
    @organization_router.post("/staff/accept-invitation", response_model=dict)
    async def accept_staff_invitation(request: AcceptInvitationRequest):
        """Accept staff invitation and create account (Public endpoint)"""
        # Find invitation
        invitation = await db["staff_invitations"].find_one({
            "invitation_token": request.token,
            "status": InvitationStatus.PENDING.value
        })
        
        if not invitation:
            raise HTTPException(status_code=404, detail="Invalid or expired invitation")
        
        # Check expiration
        expires_at = datetime.fromisoformat(invitation.get("expires_at").replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_at:
            await db["staff_invitations"].update_one(
                {"id": invitation.get("id")},
                {"$set": {"status": InvitationStatus.EXPIRED.value}}
            )
            raise HTTPException(status_code=400, detail="Invitation has expired")
        
        # Check if email already exists
        existing = await db["users"].find_one({"email": invitation.get("email")})
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user account
        new_user = {
            "id": str(uuid.uuid4()),
            "email": invitation.get("email"),
            "password_hash": hash_password(request.password),
            "first_name": invitation.get("first_name"),
            "last_name": invitation.get("last_name"),
            "role": invitation.get("role"),
            "organization_id": invitation.get("organization_id"),
            "department": invitation.get("department"),
            "specialty": invitation.get("specialty"),
            "is_active": True,
            "is_temp_password": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["users"].insert_one(new_user)
        
        # Update invitation status
        await db["staff_invitations"].update_one(
            {"id": invitation.get("id")},
            {"$set": {
                "status": InvitationStatus.ACCEPTED.value,
                "accepted_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update organization user count
        await db["organizations"].update_one(
            {"id": invitation.get("organization_id")},
            {"$inc": {"total_users": 1}}
        )
        
        return {
            "message": "Account created successfully",
            "email": new_user["email"],
            "role": new_user["role"]
        }
    
    @organization_router.get("/staff/invitations", response_model=dict)
    async def list_staff_invitations(
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """List all staff invitations (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        org_id = user.get("organization_id")
        query = {"organization_id": org_id}
        if status:
            query["status"] = status
        
        invitations = await db["staff_invitations"].find(query, {"_id": 0}).sort("invited_at", -1).to_list(100)
        
        return {"invitations": invitations}
    
    @organization_router.delete("/staff/invitations/{invitation_id}", response_model=dict)
    async def cancel_staff_invitation(invitation_id: str, user: dict = Depends(get_current_user)):
        """Cancel a pending invitation (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await db["staff_invitations"].update_one(
            {
                "id": invitation_id,
                "organization_id": user.get("organization_id"),
                "status": InvitationStatus.PENDING.value
            },
            {"$set": {"status": InvitationStatus.CANCELLED.value}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Invitation not found or already processed")
        
        return {"message": "Invitation cancelled"}
    
    @organization_router.put("/staff/{user_id}/deactivate", response_model=dict)
    async def deactivate_staff(user_id: str, user: dict = Depends(get_current_user)):
        """Deactivate a staff member (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Can't deactivate yourself
        if user_id == user.get("id"):
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
        result = await db["users"].update_one(
            {"id": user_id, "organization_id": user.get("organization_id")},
            {"$set": {"is_active": False}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        return {"message": "Staff member deactivated"}
    
    @organization_router.put("/staff/{user_id}/activate", response_model=dict)
    async def activate_staff(user_id: str, user: dict = Depends(get_current_user)):
        """Reactivate a staff member (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await db["users"].update_one(
            {"id": user_id, "organization_id": user.get("organization_id")},
            {"$set": {"is_active": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        return {"message": "Staff member activated"}
    
    @organization_router.put("/staff/{user_id}/role", response_model=dict)
    async def update_staff_role(user_id: str, new_role: str, user: dict = Depends(get_current_user)):
        """Update staff member's role (Hospital Admin)"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        valid_roles = ["physician", "nurse", "scheduler", "hospital_admin"]
        if new_role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
        
        result = await db["users"].update_one(
            {"id": user_id, "organization_id": user.get("organization_id")},
            {"$set": {"role": new_role}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Staff member not found")
        
        return {"message": f"Role updated to {new_role}"}
    
    # ============ Platform Statistics (Super Admin) ============
    
    @organization_router.get("/stats/platform", response_model=dict)
    async def get_platform_stats(user: dict = Depends(get_current_user)):
        """Get platform-wide statistics (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        total_orgs = await db["organizations"].count_documents({})
        active_orgs = await db["organizations"].count_documents({"status": "active"})
        pending_orgs = await db["organizations"].count_documents({"status": "pending"})
        total_users = await db["users"].count_documents({})
        total_patients = await db["patients"].count_documents({})
        
        return {
            "total_organizations": total_orgs,
            "active_organizations": active_orgs,
            "pending_organizations": pending_orgs,
            "total_users": total_users,
            "total_patients": total_patients
        }
    
    return organization_router
