"""
Two-Factor Authentication (2FA) Module for Yacco EMR
TOTP-based 2FA compatible with Google Authenticator, Authy, etc.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import secrets
import base64
import hmac
import hashlib
import struct
import time
import qrcode
import io
import base64 as b64

twofa_router = APIRouter(prefix="/api/2fa", tags=["Two-Factor Authentication"])


# ============ MODELS ============

class TwoFASetupResponse(BaseModel):
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: List[str]
    manual_entry_key: str
    issuer: str
    account_name: str


class TwoFAVerifyRequest(BaseModel):
    code: str


class TwoFALoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None


class BackupCodeUseRequest(BaseModel):
    backup_code: str


# ============ TOTP IMPLEMENTATION ============

def generate_secret(length: int = 20) -> str:
    """Generate a random base32 secret for TOTP"""
    random_bytes = secrets.token_bytes(length)
    return base64.b32encode(random_bytes).decode('utf-8').rstrip('=')


def get_totp_token(secret: str, time_step: int = 30, digits: int = 6) -> str:
    """Generate current TOTP token"""
    # Decode the base32 secret
    secret_bytes = base64.b32decode(secret + '=' * (8 - len(secret) % 8))
    
    # Get current time counter
    counter = int(time.time()) // time_step
    
    # Convert counter to bytes
    counter_bytes = struct.pack('>Q', counter)
    
    # Generate HMAC-SHA1
    hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
    
    # Dynamic truncation
    offset = hmac_hash[-1] & 0x0f
    code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
    code &= 0x7fffffff
    code %= 10 ** digits
    
    return str(code).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code with time window for drift tolerance"""
    # Check current time and +/- window steps
    for offset in range(-window, window + 1):
        secret_bytes = base64.b32decode(secret + '=' * (8 - len(secret) % 8))
        counter = (int(time.time()) // 30) + offset
        counter_bytes = struct.pack('>Q', counter)
        
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        offset_byte = hmac_hash[-1] & 0x0f
        truncated = struct.unpack('>I', hmac_hash[offset_byte:offset_byte + 4])[0]
        truncated &= 0x7fffffff
        truncated %= 10 ** 6
        
        if str(truncated).zfill(6) == code:
            return True
    
    return False


def generate_backup_codes(count: int = 10) -> List[str]:
    """Generate one-time backup codes"""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = secrets.token_hex(4).upper()
        codes.append(f"{code[:4]}-{code[4:]}")
    return codes


def generate_qr_code(secret: str, email: str, issuer: str = "Yacco EMR") -> str:
    """Generate QR code for authenticator app setup"""
    # Create otpauth URI
    uri = f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = b64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


# ============ API ENDPOINTS ============

def create_2fa_endpoints(db, get_current_user, verify_password_func, create_token_func):
    """Create 2FA endpoints"""
    
    @twofa_router.get("/status")
    async def get_2fa_status(current_user: dict = Depends(get_current_user)):
        """Check if 2FA is enabled for current user"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]}, {"_id": 0})
        
        if not user_2fa:
            return {
                "enabled": False,
                "verified": False,
                "backup_codes_remaining": 0
            }
        
        backup_codes_remaining = len([c for c in user_2fa.get("backup_codes", []) if not c.get("used", False)])
        
        return {
            "enabled": user_2fa.get("enabled", False),
            "verified": user_2fa.get("verified", False),
            "backup_codes_remaining": backup_codes_remaining,
            "setup_at": user_2fa.get("setup_at"),
            "last_used": user_2fa.get("last_used")
        }
    
    @twofa_router.post("/setup", response_model=TwoFASetupResponse)
    async def setup_2fa(current_user: dict = Depends(get_current_user)):
        """Initialize 2FA setup - generates secret and QR code"""
        # Check if already set up
        existing = await db.user_2fa.find_one({"user_id": current_user["id"]})
        if existing and existing.get("enabled"):
            raise HTTPException(status_code=400, detail="2FA is already enabled. Disable it first to reconfigure.")
        
        # Generate new secret and backup codes
        secret = generate_secret()
        backup_codes = generate_backup_codes(10)
        email = current_user.get("email", "user@yacco.com")
        
        # Generate QR code
        qr_code = generate_qr_code(secret, email, "Yacco EMR")
        
        # Format secret for manual entry (groups of 4)
        manual_key = ' '.join([secret[i:i+4] for i in range(0, len(secret), 4)])
        
        # Store pending 2FA setup (not enabled until verified)
        setup_data = {
            "user_id": current_user["id"],
            "secret": secret,
            "backup_codes": [{"code": c, "used": False} for c in backup_codes],
            "enabled": False,
            "verified": False,
            "setup_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert (update if exists, insert if not)
        await db.user_2fa.update_one(
            {"user_id": current_user["id"]},
            {"$set": setup_data},
            upsert=True
        )
        
        return TwoFASetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes,
            manual_entry_key=manual_key,
            issuer="Yacco EMR",
            account_name=email
        )
    
    @twofa_router.post("/verify")
    async def verify_2fa_setup(
        request: TwoFAVerifyRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Verify TOTP code to enable 2FA"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]})
        
        if not user_2fa:
            raise HTTPException(status_code=400, detail="2FA not set up. Call /setup first.")
        
        if user_2fa.get("enabled"):
            raise HTTPException(status_code=400, detail="2FA is already enabled.")
        
        # Verify the code
        if not verify_totp(user_2fa["secret"], request.code):
            raise HTTPException(status_code=400, detail="Invalid verification code. Please try again.")
        
        # Enable 2FA
        await db.user_2fa.update_one(
            {"user_id": current_user["id"]},
            {"$set": {
                "enabled": True,
                "verified": True,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update user record to indicate 2FA is enabled
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"two_factor_enabled": True}}
        )
        
        return {
            "success": True,
            "message": "Two-factor authentication has been enabled successfully.",
            "backup_codes_count": len(user_2fa.get("backup_codes", []))
        }
    
    @twofa_router.post("/disable")
    async def disable_2fa(
        request: TwoFAVerifyRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Disable 2FA (requires current TOTP code)"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]})
        
        if not user_2fa or not user_2fa.get("enabled"):
            raise HTTPException(status_code=400, detail="2FA is not enabled.")
        
        # Verify the code before disabling
        if not verify_totp(user_2fa["secret"], request.code):
            raise HTTPException(status_code=400, detail="Invalid verification code.")
        
        # Disable 2FA
        await db.user_2fa.delete_one({"user_id": current_user["id"]})
        
        # Update user record
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {"two_factor_enabled": False}}
        )
        
        return {
            "success": True,
            "message": "Two-factor authentication has been disabled."
        }
    
    @twofa_router.post("/validate")
    async def validate_totp_code(
        request: TwoFAVerifyRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Validate a TOTP code (for sensitive operations)"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]})
        
        if not user_2fa or not user_2fa.get("enabled"):
            raise HTTPException(status_code=400, detail="2FA is not enabled for this account.")
        
        if not verify_totp(user_2fa["secret"], request.code):
            # Log failed attempt
            await db.twofa_attempts.insert_one({
                "user_id": current_user["id"],
                "success": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "totp"
            })
            raise HTTPException(status_code=400, detail="Invalid code.")
        
        # Update last used
        await db.user_2fa.update_one(
            {"user_id": current_user["id"]},
            {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"valid": True, "message": "Code verified successfully."}
    
    @twofa_router.post("/backup-codes/regenerate")
    async def regenerate_backup_codes(
        request: TwoFAVerifyRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Regenerate backup codes (requires TOTP verification)"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]})
        
        if not user_2fa or not user_2fa.get("enabled"):
            raise HTTPException(status_code=400, detail="2FA is not enabled.")
        
        # Verify TOTP first
        if not verify_totp(user_2fa["secret"], request.code):
            raise HTTPException(status_code=400, detail="Invalid verification code.")
        
        # Generate new backup codes
        new_codes = generate_backup_codes(10)
        
        await db.user_2fa.update_one(
            {"user_id": current_user["id"]},
            {"$set": {
                "backup_codes": [{"code": c, "used": False} for c in new_codes],
                "backup_codes_regenerated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "success": True,
            "backup_codes": new_codes,
            "message": "New backup codes generated. Store them securely."
        }
    
    @twofa_router.post("/backup-codes/use")
    async def use_backup_code(
        request: BackupCodeUseRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Use a backup code for authentication"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]})
        
        if not user_2fa or not user_2fa.get("enabled"):
            raise HTTPException(status_code=400, detail="2FA is not enabled.")
        
        # Find matching unused backup code
        backup_codes = user_2fa.get("backup_codes", [])
        code_found = False
        
        for bc in backup_codes:
            if bc["code"] == request.backup_code.upper().replace(" ", "") and not bc.get("used", False):
                bc["used"] = True
                bc["used_at"] = datetime.now(timezone.utc).isoformat()
                code_found = True
                break
        
        if not code_found:
            raise HTTPException(status_code=400, detail="Invalid or already used backup code.")
        
        # Update backup codes
        await db.user_2fa.update_one(
            {"user_id": current_user["id"]},
            {"$set": {"backup_codes": backup_codes}}
        )
        
        remaining = len([c for c in backup_codes if not c.get("used", False)])
        
        return {
            "success": True,
            "message": "Backup code verified.",
            "backup_codes_remaining": remaining
        }
    
    @twofa_router.get("/backup-codes/count")
    async def get_backup_codes_count(current_user: dict = Depends(get_current_user)):
        """Get count of remaining backup codes"""
        user_2fa = await db.user_2fa.find_one({"user_id": current_user["id"]})
        
        if not user_2fa:
            return {"backup_codes_remaining": 0}
        
        remaining = len([c for c in user_2fa.get("backup_codes", []) if not c.get("used", False)])
        return {"backup_codes_remaining": remaining}
    
    # Helper function for login verification
    async def verify_2fa_for_login(user_id: str, totp_code: str) -> bool:
        """Verify 2FA during login process"""
        user_2fa = await db.user_2fa.find_one({"user_id": user_id})
        
        if not user_2fa or not user_2fa.get("enabled"):
            return True  # 2FA not enabled, allow login
        
        if not totp_code:
            return False  # 2FA enabled but no code provided
        
        # Try TOTP code first
        if verify_totp(user_2fa["secret"], totp_code):
            await db.user_2fa.update_one(
                {"user_id": user_id},
                {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
            )
            return True
        
        # Try backup codes
        backup_codes = user_2fa.get("backup_codes", [])
        for bc in backup_codes:
            if bc["code"] == totp_code.upper().replace("-", "").replace(" ", "") and not bc.get("used", False):
                bc["used"] = True
                bc["used_at"] = datetime.now(timezone.utc).isoformat()
                await db.user_2fa.update_one(
                    {"user_id": user_id},
                    {"$set": {"backup_codes": backup_codes}}
                )
                return True
        
        return False
    
    async def is_2fa_required(user_id: str) -> bool:
        """Check if 2FA is required for a user"""
        user_2fa = await db.user_2fa.find_one({"user_id": user_id})
        return user_2fa is not None and user_2fa.get("enabled", False)
    
    return twofa_router, verify_2fa_for_login, is_2fa_required


# Export
__all__ = [
    'twofa_router',
    'create_2fa_endpoints',
    'generate_secret',
    'verify_totp',
    'generate_backup_codes'
]
