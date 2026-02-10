"""
Yacco Health OTP (One-Time Password) Module
==========================================
SMS-based OTP verification for staff logins on EMR and Pharmacy platforms.
Uses Arkesel SMS API for OTP delivery.
REFACTORED to use db_service_v2 for database abstraction.
"""
import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel

from db_service_v2 import get_db_service


class OTPRequest(BaseModel):
    user_id: str
    phone_number: str
    platform: str  # 'emr' or 'pharmacy'


class OTPVerifyRequest(BaseModel):
    otp_session_id: str
    otp_code: str


# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 3


def generate_otp(length: int = OTP_LENGTH) -> str:
    """Generate a numeric OTP code"""
    return ''.join(random.choices(string.digits, k=length))


async def create_otp_session(
    db,  # Legacy parameter for backwards compatibility
    user_id: str,
    phone_number: str,
    platform: str,
    user_name: str = "User"
) -> dict:
    """
    Create a new OTP session and send SMS
    Returns session info for frontend to track
    """
    from sms_notification_module import send_sms, SMSTemplates
    
    db_svc = get_db_service()
    
    # Generate OTP
    otp_code = generate_otp()
    session_id = str(uuid.uuid4())
    expiry = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Store OTP session
    otp_session = {
        "id": session_id,
        "user_id": user_id,
        "phone_number": phone_number,
        "platform": platform,
        "otp_code": otp_code,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expiry.isoformat(),
        "attempts": 0,
        "verified": False,
        "used": False
    }
    
    await db_svc.insert("otp_sessions", otp_session, generate_id=False)
    
    # Send OTP via SMS
    message = SMSTemplates.otp_verification(otp_code)
    sms_result = await send_sms(phone_number, message)
    
    # Log OTP send
    await db_svc.insert("sms_logs", {
        "phone_number": phone_number,
        "notification_type": "otp_verification",
        "success": sms_result.get("success", False),
        "platform": platform,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "session_id": session_id,
        "expires_at": expiry.isoformat(),
        "phone_masked": mask_phone_number(phone_number),
        "sms_sent": sms_result.get("success", False)
    }


async def verify_otp(
    db,  # Legacy parameter for backwards compatibility
    session_id: str,
    otp_code: str
) -> dict:
    """
    Verify OTP code for a session
    Returns verification result
    """
    db_svc = get_db_service()
    
    # Find session
    session = await db_svc.get_by_id("otp_sessions", session_id)
    
    if not session:
        return {"success": False, "error": "Invalid session"}
    
    # Check if already used
    if session.get("used"):
        return {"success": False, "error": "OTP already used"}
    
    # Check if already verified
    if session.get("verified"):
        return {"success": False, "error": "OTP already verified"}
    
    # Check expiry
    expiry = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expiry:
        return {"success": False, "error": "OTP expired"}
    
    # Check attempts
    if session.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
        return {"success": False, "error": "Maximum attempts exceeded"}
    
    # Increment attempts - use direct MongoDB for $inc
    await db_svc.collection("otp_sessions").update_one(
        {"id": session_id},
        {"$inc": {"attempts": 1}}
    )
    
    # Verify code
    if session["otp_code"] != otp_code:
        remaining = MAX_OTP_ATTEMPTS - session.get("attempts", 0) - 1
        return {
            "success": False, 
            "error": f"Invalid OTP. {remaining} attempts remaining."
        }
    
    # Mark as verified
    await db_svc.update_by_id("otp_sessions", session_id, {
        "verified": True,
        "verified_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "user_id": session["user_id"],
        "platform": session["platform"]
    }


async def mark_otp_used(db, session_id: str):
    """Mark OTP session as used after successful login"""
    db_svc = get_db_service()
    
    await db_svc.update_by_id("otp_sessions", session_id, {
        "used": True,
        "used_at": datetime.now(timezone.utc).isoformat()
    })


async def resend_otp(db, session_id: str) -> dict:
    """Resend OTP for an existing session"""
    from sms_notification_module import send_sms, SMSTemplates
    
    db_svc = get_db_service()
    
    session = await db_svc.get_by_id("otp_sessions", session_id)
    
    if not session:
        return {"success": False, "error": "Invalid session"}
    
    if session.get("used") or session.get("verified"):
        return {"success": False, "error": "Session already completed"}
    
    # Generate new OTP
    new_otp = generate_otp()
    new_expiry = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Update session
    await db_svc.update_by_id("otp_sessions", session_id, {
        "otp_code": new_otp,
        "expires_at": new_expiry.isoformat(),
        "attempts": 0,
        "resent_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send new OTP
    message = SMSTemplates.otp_verification(new_otp)
    sms_result = await send_sms(session["phone_number"], message)
    
    return {
        "success": sms_result.get("success", False),
        "expires_at": new_expiry.isoformat(),
        "phone_masked": mask_phone_number(session["phone_number"])
    }


def mask_phone_number(phone: str) -> str:
    """Mask phone number for display (show last 4 digits)"""
    if len(phone) < 4:
        return "****"
    return "*" * (len(phone) - 4) + phone[-4:]


async def cleanup_expired_sessions(db):
    """Clean up expired OTP sessions (run periodically)"""
    db_svc = get_db_service()
    
    expiry_threshold = datetime.now(timezone.utc) - timedelta(hours=1)
    result = await db_svc.delete_many("otp_sessions", {
        "expires_at": {"$lt": expiry_threshold.isoformat()},
        "used": False
    })
    return result
