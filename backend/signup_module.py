"""
Signup & Onboarding Module
Provides public-facing signup and account creation:
- Hospital registration (with verification)
- Provider signup (invite-based)
- Account verification workflow
- Approval workflow
- Secure onboarding
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import secrets
import bcrypt
import os
import re

signup_router = APIRouter(prefix="/api/signup", tags=["Signup & Onboarding"])

# ============ Enums ============

class SignupType(str, Enum):
    HOSPITAL = "hospital"
    PROVIDER = "provider"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

# ============ Models ============

class HospitalSignupRequest(BaseModel):
    """Hospital registration request"""
    # Hospital Info
    hospital_name: str = Field(..., min_length=3, max_length=200)
    region_id: str
    address: str
    city: str
    phone: str
    hospital_email: EmailStr
    website: Optional[str] = None
    license_number: str
    ghana_health_service_id: Optional[str] = None
    
    # Admin Contact
    admin_first_name: str
    admin_last_name: str
    admin_email: EmailStr
    admin_phone: str
    admin_title: Optional[str] = "Hospital Administrator"
    
    # Verification
    accept_terms: bool
    
    @validator('accept_terms')
    def must_accept_terms(cls, v):
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v

class ProviderSignupRequest(BaseModel):
    """Individual provider signup (invite-based)"""
    invite_code: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: str
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    password: str = Field(..., min_length=8)
    confirm_password: str
    accept_terms: bool
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class VerificationRequest(BaseModel):
    token: str

class ApprovalDecision(BaseModel):
    approved: bool
    reason: Optional[str] = None
    notes: Optional[str] = None

# ============ API Factory ============

def create_signup_endpoints(db, hash_password, get_current_user):
    """Create signup API endpoints"""
    
    # ============ Public Endpoints ============
    
    @signup_router.post("/hospital", response_model=dict)
    async def register_hospital(
        request: HospitalSignupRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Public hospital registration.
        Creates pending hospital and admin account.
        Requires verification and approval.
        """
        # Check if hospital email already exists
        existing_hospital = await db["hospitals"].find_one({
            "$or": [
                {"email": request.hospital_email},
                {"license_number": request.license_number}
            ]
        })
        if existing_hospital:
            raise HTTPException(
                status_code=400,
                detail="Hospital with this email or license number already registered"
            )
        
        # Check if admin email exists
        existing_admin = await db["users"].find_one({"email": request.admin_email})
        if existing_admin:
            raise HTTPException(status_code=400, detail="Admin email already registered")
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=48)
        
        # Create hospital registration (pending)
        registration_id = str(uuid.uuid4())
        hospital_id = str(uuid.uuid4())
        admin_id = str(uuid.uuid4())
        
        registration = {
            "id": registration_id,
            "type": "hospital",
            "hospital_id": hospital_id,
            "admin_id": admin_id,
            
            # Hospital data
            "hospital_data": {
                "id": hospital_id,
                "name": request.hospital_name,
                "region_id": request.region_id,
                "address": request.address,
                "city": request.city,
                "phone": request.phone,
                "email": request.hospital_email,
                "website": request.website,
                "license_number": request.license_number,
                "ghana_health_service_id": request.ghana_health_service_id
            },
            
            # Admin data
            "admin_data": {
                "id": admin_id,
                "email": request.admin_email,
                "first_name": request.admin_first_name,
                "last_name": request.admin_last_name,
                "phone": request.admin_phone,
                "title": request.admin_title
            },
            
            # Status
            "status": "pending_verification",
            "verification_token": verification_token,
            "token_expiry": token_expiry.isoformat(),
            "email_verified": False,
            
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "ip_address": None
        }
        
        await db["signup_registrations"].insert_one(registration)
        
        # Create verification record
        await db["verification_tokens"].insert_one({
            "id": str(uuid.uuid4()),
            "token": verification_token,
            "type": "email_verification",
            "registration_id": registration_id,
            "email": request.admin_email,
            "expires_at": token_expiry.isoformat(),
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # TODO: Send verification email in background
        # background_tasks.add_task(send_verification_email, request.admin_email, verification_token)
        
        return {
            "message": "Registration submitted successfully",
            "registration_id": registration_id,
            "next_steps": [
                "Check your email for verification link",
                "Verify your email within 48 hours",
                "Wait for platform approval (1-2 business days)"
            ],
            "verification_email_sent_to": request.admin_email,
            # For development - remove in production
            "dev_verification_token": verification_token
        }
    
    @signup_router.post("/verify-email", response_model=dict)
    async def verify_email(request: VerificationRequest):
        """Verify email with token"""
        # Find token
        token_doc = await db["verification_tokens"].find_one({
            "token": request.token,
            "type": "email_verification",
            "used": False
        })
        
        if not token_doc:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Check expiry
        if datetime.now(timezone.utc).isoformat() > token_doc["expires_at"]:
            raise HTTPException(status_code=400, detail="Verification token expired")
        
        # Update token as used
        await db["verification_tokens"].update_one(
            {"id": token_doc["id"]},
            {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Update registration status
        await db["signup_registrations"].update_one(
            {"id": token_doc["registration_id"]},
            {"$set": {
                "status": "pending_approval",
                "email_verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "message": "Email verified successfully",
            "status": "pending_approval",
            "next_steps": [
                "Your registration is now under review",
                "You will receive an email once approved",
                "This typically takes 1-2 business days"
            ]
        }
    
    @signup_router.get("/status/{registration_id}", response_model=dict)
    async def check_registration_status(registration_id: str):
        """Check registration status"""
        registration = await db["signup_registrations"].find_one(
            {"id": registration_id},
            {"_id": 0, "verification_token": 0}
        )
        
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        status_messages = {
            "pending_verification": "Awaiting email verification",
            "pending_approval": "Under review by platform administrators",
            "approved": "Approved - check email for login credentials",
            "rejected": "Registration rejected"
        }
        
        return {
            "registration_id": registration_id,
            "status": registration["status"],
            "status_message": status_messages.get(registration["status"], "Unknown"),
            "email_verified": registration.get("email_verified", False),
            "created_at": registration["created_at"],
            "rejection_reason": registration.get("rejection_reason")
        }
    
    @signup_router.post("/provider", response_model=dict)
    async def register_provider(
        request: ProviderSignupRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Individual provider registration via invite code.
        Requires valid invite from hospital admin.
        """
        # Validate invite code
        invite = await db["provider_invites"].find_one({
            "code": request.invite_code,
            "used": False
        })
        
        if not invite:
            raise HTTPException(status_code=400, detail="Invalid or expired invite code")
        
        # Check expiry
        if invite.get("expires_at") and datetime.now(timezone.utc).isoformat() > invite["expires_at"]:
            raise HTTPException(status_code=400, detail="Invite code has expired")
        
        # Check email matches invite
        if invite.get("email") and invite["email"] != request.email:
            raise HTTPException(status_code=400, detail="Email does not match invite")
        
        # Check email not already registered
        existing = await db["users"].find_one({"email": request.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user account
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone": request.phone,
            "role": invite.get("role", "physician"),
            "specialty": request.specialty,
            "license_number": request.license_number,
            "organization_id": invite["organization_id"],
            "department_id": invite.get("department_id"),
            "location_id": invite.get("location_id"),
            "password": hash_password(request.password),
            "status": "active",
            "is_active": True,
            "is_temp_password": False,
            "invited_by": invite.get("created_by"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["users"].insert_one(user)
        
        # Mark invite as used
        await db["provider_invites"].update_one(
            {"id": invite["id"]},
            {"$set": {
                "used": True,
                "used_at": datetime.now(timezone.utc).isoformat(),
                "used_by": user_id
            }}
        )
        
        # Update hospital user count
        await db["hospitals"].update_one(
            {"id": invite["organization_id"]},
            {"$inc": {"total_users": 1}}
        )
        
        return {
            "message": "Account created successfully",
            "user_id": user_id,
            "email": request.email,
            "role": user["role"],
            "next_steps": [
                "You can now login with your credentials",
                "Access your hospital at /login"
            ]
        }
    
    @signup_router.post("/resend-verification", response_model=dict)
    async def resend_verification_email(email: EmailStr = Query(...)):
        """Resend verification email"""
        registration = await db["signup_registrations"].find_one({
            "admin_data.email": email,
            "status": "pending_verification"
        })
        
        if not registration:
            raise HTTPException(
                status_code=404,
                detail="No pending registration found for this email"
            )
        
        # Generate new token
        new_token = secrets.token_urlsafe(32)
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=48)
        
        # Update registration
        await db["signup_registrations"].update_one(
            {"id": registration["id"]},
            {"$set": {
                "verification_token": new_token,
                "token_expiry": token_expiry.isoformat()
            }}
        )
        
        # Create new verification token record
        await db["verification_tokens"].insert_one({
            "id": str(uuid.uuid4()),
            "token": new_token,
            "type": "email_verification",
            "registration_id": registration["id"],
            "email": email,
            "expires_at": token_expiry.isoformat(),
            "used": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": "Verification email resent",
            "email": email,
            "dev_verification_token": new_token  # Remove in production
        }
    
    # ============ Admin Endpoints (Super Admin Only) ============
    
    @signup_router.get("/admin/pending", response_model=dict)
    async def list_pending_registrations(
        status: Optional[str] = "pending_approval",
        user: dict = Depends(get_current_user)
    ):
        """List pending registrations (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        query = {}
        if status:
            query["status"] = status
        
        registrations = await db["signup_registrations"].find(
            query,
            {"_id": 0, "verification_token": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "registrations": registrations,
            "total": len(registrations)
        }
    
    @signup_router.post("/admin/approve/{registration_id}", response_model=dict)
    async def approve_registration(
        registration_id: str,
        decision: ApprovalDecision,
        user: dict = Depends(get_current_user)
    ):
        """Approve or reject registration (Super Admin only)"""
        if user.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Super Admin access required")
        
        registration = await db["signup_registrations"].find_one({"id": registration_id})
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")
        
        if registration["status"] not in ["pending_approval", "pending_verification"]:
            raise HTTPException(
                status_code=400,
                detail=f"Registration already {registration['status']}"
            )
        
        if not decision.approved:
            # Reject registration
            await db["signup_registrations"].update_one(
                {"id": registration_id},
                {"$set": {
                    "status": "rejected",
                    "rejection_reason": decision.reason,
                    "rejection_notes": decision.notes,
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "rejected_by": user["id"]
                }}
            )
            return {"message": "Registration rejected", "status": "rejected"}
        
        # Approve registration - create hospital and admin
        hospital_data = registration["hospital_data"]
        admin_data = registration["admin_data"]
        
        # Generate admin password
        temp_password = secrets.token_urlsafe(12)
        
        # Create hospital
        hospital = {
            **hospital_data,
            "organization_type": "hospital",
            "status": "active",
            "is_active": True,
            "total_users": 1,
            "total_patients": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": user["id"]
        }
        await db["hospitals"].insert_one(hospital)
        
        # Create main location
        main_location = {
            "id": str(uuid.uuid4()),
            "hospital_id": hospital_data["id"],
            "name": f"{hospital_data['name']} - Main",
            "location_type": "main_hospital",
            "address": hospital_data["address"],
            "city": hospital_data["city"],
            "phone": hospital_data["phone"],
            "email": hospital_data["email"],
            "is_active": True,
            "user_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["hospital_locations"].insert_one(main_location)
        
        # Create admin user
        admin_user = {
            **admin_data,
            "role": "hospital_admin",
            "department": "Administration",
            "organization_id": hospital_data["id"],
            "location_id": main_location["id"],
            "password": hash_password(temp_password),
            "status": "active",
            "is_active": True,
            "is_temp_password": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db["users"].insert_one(admin_user)
        
        # Update registration
        await db["signup_registrations"].update_one(
            {"id": registration_id},
            {"$set": {
                "status": "approved",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": user["id"],
                "approval_notes": decision.notes
            }}
        )
        
        # Update region hospital count
        await db["regions"].update_one(
            {"id": hospital_data["region_id"]},
            {"$inc": {"hospital_count": 1}}
        )
        
        # Log action
        await db["audit_logs"].insert_one({
            "id": str(uuid.uuid4()),
            "action": "approve_registration",
            "user_id": user["id"],
            "user_email": user.get("email"),
            "resource_type": "registration",
            "resource_id": registration_id,
            "details": {
                "hospital_name": hospital_data["name"],
                "admin_email": admin_data["email"]
            },
            "severity": "high",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "message": "Registration approved",
            "status": "approved",
            "hospital": {
                "id": hospital_data["id"],
                "name": hospital_data["name"]
            },
            "admin": {
                "id": admin_data["id"],
                "email": admin_data["email"],
                "temp_password": temp_password
            },
            "location": {
                "id": main_location["id"],
                "name": main_location["name"]
            }
        }
    
    # ============ Provider Invite Management ============
    
    @signup_router.post("/admin/invite-provider", response_model=dict)
    async def create_provider_invite(
        hospital_id: str,
        email: EmailStr,
        role: str = "physician",
        department_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Create provider invite (Hospital Admin)"""
        # Verify permissions
        if user.get("role") == "super_admin":
            pass
        elif user.get("role") in ["hospital_admin", "admin"]:
            if user.get("organization_id") != hospital_id:
                raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        else:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Check email not already registered
        existing = await db["users"].find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate invite code
        invite_code = secrets.token_urlsafe(16)
        
        invite = {
            "id": str(uuid.uuid4()),
            "code": invite_code,
            "email": email,
            "role": role,
            "organization_id": hospital_id,
            "department_id": department_id,
            "location_id": user.get("location_id"),
            "used": False,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_by": user["id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["provider_invites"].insert_one(invite)
        
        return {
            "message": "Invite created",
            "invite_code": invite_code,
            "email": email,
            "signup_url": f"/signup/provider?code={invite_code}",
            "expires_in_days": 7
        }
    
    return signup_router


# Export
__all__ = ["signup_router", "create_signup_endpoints"]
