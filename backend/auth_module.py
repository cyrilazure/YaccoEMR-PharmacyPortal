"""
Enhanced JWT Authentication Module for Yacco EMR
HIPAA-Compliant Healthcare Authentication System

Features:
- Username/password login with secure hashing
- Role-Based Access Control (RBAC)
- Group-based permissions
- Organization isolation (multi-tenancy)
- Time-limited access tokens with refresh
- MFA-ready architecture (TOTP)
- Session management
- Audit logging for all auth events
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import jwt
import bcrypt
import secrets
import hashlib
import os

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


# ============================================================================
# CONFIGURATION
# ============================================================================

class AuthConfig:
    """Authentication configuration - Healthcare best practices"""
    
    # JWT Settings
    JWT_SECRET: str = os.environ.get('JWT_SECRET', secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    
    # Token Lifetimes (Healthcare requires shorter sessions)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30      # 30 minutes for access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7         # 7 days for refresh token
    SESSION_TIMEOUT_MINUTES: int = 30          # Auto-logout after inactivity
    
    # Security Settings
    PASSWORD_MIN_LENGTH: int = 12              # HIPAA recommends 12+ chars
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_HISTORY_COUNT: int = 12           # Can't reuse last 12 passwords
    
    # Lockout Policy
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # MFA Settings
    MFA_REQUIRED_FOR_ROLES: List[str] = ["super_admin", "hospital_admin"]
    MFA_ISSUER: str = "Yacco EMR"
    
    # Session Settings
    SINGLE_SESSION_PER_USER: bool = False      # Allow multiple sessions
    MAX_SESSIONS_PER_USER: int = 5


# ============================================================================
# TOKEN STRUCTURE AND CLAIMS
# ============================================================================

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


class JWTClaims(BaseModel):
    """
    JWT Token Claims Structure
    
    Standard Claims (RFC 7519):
    - iss: Issuer
    - sub: Subject (user_id)
    - aud: Audience
    - exp: Expiration Time
    - nbf: Not Before
    - iat: Issued At
    - jti: JWT ID (unique token identifier)
    
    Custom Claims for EMR:
    - role: User's role
    - org_id: Organization ID (multi-tenancy)
    - dept_id: Department ID
    - permissions: List of granted permissions
    - groups: Group memberships
    - token_type: Type of token (access/refresh)
    - session_id: Session identifier
    - mfa_verified: Whether MFA was verified
    """
    # Standard Claims
    iss: str = "yacco-emr"                     # Issuer
    sub: str                                    # Subject (user_id)
    aud: str = "yacco-emr-api"                 # Audience
    exp: datetime                              # Expiration
    nbf: datetime                              # Not Before
    iat: datetime                              # Issued At
    jti: str                                   # JWT ID
    
    # Custom Claims
    role: str                                  # User role
    org_id: Optional[str] = None              # Organization ID
    dept_id: Optional[str] = None             # Department ID
    permissions: List[str] = []               # Direct permissions
    groups: List[str] = []                    # Group memberships
    token_type: TokenType = TokenType.ACCESS
    session_id: str                           # Session tracking
    mfa_verified: bool = False                # MFA status
    
    # Security metadata
    ip_hash: Optional[str] = None             # Hashed IP for binding
    device_id: Optional[str] = None           # Device fingerprint


# ============================================================================
# GROUP-BASED PERMISSIONS
# ============================================================================

class PermissionGroup(str, Enum):
    """Permission groups for easier management"""
    CLINICAL_FULL = "clinical_full"           # All clinical permissions
    CLINICAL_READ = "clinical_read"           # Read-only clinical
    ADMIN_FULL = "admin_full"                 # All admin permissions
    BILLING_FULL = "billing_full"             # All billing permissions
    SCHEDULING = "scheduling"                  # Scheduling permissions
    LAB_MANAGEMENT = "lab_management"          # Lab module permissions
    PHARMACY = "pharmacy"                      # Pharmacy permissions
    RECORDS_MANAGEMENT = "records_management"  # Records sharing permissions


# Group to permissions mapping
GROUP_PERMISSIONS: Dict[str, Set[str]] = {
    PermissionGroup.CLINICAL_FULL: {
        "patient:view", "patient:create", "patient:update",
        "note:view", "note:create", "note:update", "note:sign",
        "vitals:view", "vitals:create",
        "medication:view", "medication:prescribe", "medication:update",
        "order:view", "order:create", "order:update_status", "order:cancel",
        "lab:order_create", "lab:order_view", "lab:result_view",
        "imaging:order_create", "imaging:view", "imaging:interpret",
        "prescription:create", "prescription:view",
    },
    PermissionGroup.CLINICAL_READ: {
        "patient:view", "note:view", "vitals:view", "medication:view",
        "order:view", "lab:order_view", "lab:result_view", "imaging:view",
        "prescription:view",
    },
    PermissionGroup.ADMIN_FULL: {
        "user:view", "user:create", "user:update", "user:deactivate",
        "organization:view", "organization:update",
        "audit:view", "audit:export",
        "report:view", "report:create", "report:export",
    },
    PermissionGroup.BILLING_FULL: {
        "billing:view", "billing:create", "billing:update",
        "patient:view", "appointment:view",
    },
    PermissionGroup.SCHEDULING: {
        "appointment:view", "appointment:create", "appointment:update", "appointment:cancel",
        "patient:view", "patient:create",
        "user:view",
    },
    PermissionGroup.LAB_MANAGEMENT: {
        "lab:order_create", "lab:order_view", "lab:result_view", "lab:result_add",
        "patient:view", "order:view",
    },
    PermissionGroup.PHARMACY: {
        "prescription:view", "prescription:dispense",
        "medication:view", "medication:administer",
        "patient:view",
    },
    PermissionGroup.RECORDS_MANAGEMENT: {
        "records:share", "records:request", "records:approve",
        "patient:view", "note:view",
    },
}


def get_group_permissions(groups: List[str]) -> Set[str]:
    """Get all permissions from a list of groups"""
    permissions = set()
    for group in groups:
        if group in GROUP_PERMISSIONS:
            permissions.update(GROUP_PERMISSIONS[group])
    return permissions


# ============================================================================
# MODELS
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None
    device_id: Optional[str] = None
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int                           # Seconds until expiration
    user: Dict[str, Any]
    mfa_required: bool = False
    session_id: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[str] = None
    permissions: List[str] = []
    expires_at: Optional[str] = None
    error: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    created_at: str
    last_activity: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_id: Optional[str]
    is_current: bool = False


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password against healthcare security requirements
    HIPAA/HITECH recommends strong password policies
    """
    errors = []
    
    if len(password) < AuthConfig.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {AuthConfig.PASSWORD_MIN_LENGTH} characters")
    
    if AuthConfig.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if AuthConfig.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    if AuthConfig.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")
    
    # Check for common patterns
    common_patterns = ["password", "123456", "qwerty", "admin", "letmein"]
    if any(pattern in password.lower() for pattern in common_patterns):
        errors.append("Password contains common patterns")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength": "strong" if len(errors) == 0 else "weak"
    }


def hash_password(password: str) -> str:
    """Hash password using bcrypt with high work factor"""
    # Work factor of 12 is recommended for healthcare
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def hash_ip(ip_address: str) -> str:
    """Hash IP address for token binding"""
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]


# ============================================================================
# TOKEN UTILITIES
# ============================================================================

def create_access_token(
    user: dict,
    session_id: str,
    mfa_verified: bool = False,
    ip_address: Optional[str] = None,
    device_id: Optional[str] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """
    Create JWT access token with all required claims
    
    Token structure includes:
    - Standard JWT claims (iss, sub, aud, exp, nbf, iat, jti)
    - User context (role, org_id, dept_id)
    - Permissions and groups
    - Security metadata
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Get user's groups and permissions
    user_groups = user.get("groups", [])
    user_permissions = user.get("permissions", [])
    
    # Combine direct permissions with group-based permissions
    all_permissions = set(user_permissions)
    all_permissions.update(get_group_permissions(user_groups))
    
    claims = {
        # Standard claims
        "iss": "yacco-emr",
        "sub": user["id"],
        "aud": "yacco-emr-api",
        "exp": expiration,
        "nbf": now,
        "iat": now,
        "jti": str(uuid.uuid4()),
        
        # Custom claims
        "role": user.get("role", ""),
        "org_id": user.get("organization_id"),
        "dept_id": user.get("department_id"),
        "permissions": list(all_permissions),
        "groups": user_groups,
        "token_type": TokenType.ACCESS.value,
        "session_id": session_id,
        "mfa_verified": mfa_verified,
        
        # User info for quick access
        "email": user.get("email"),
        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
    }
    
    # Add security metadata
    if ip_address:
        claims["ip_hash"] = hash_ip(ip_address)
    if device_id:
        claims["device_id"] = device_id
    
    # Add any additional claims
    if additional_claims:
        claims.update(additional_claims)
    
    return jwt.encode(claims, AuthConfig.JWT_SECRET, algorithm=AuthConfig.JWT_ALGORITHM)


def create_refresh_token(user_id: str, session_id: str) -> str:
    """Create refresh token for obtaining new access tokens"""
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    
    claims = {
        "iss": "yacco-emr",
        "sub": user_id,
        "exp": expiration,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "token_type": TokenType.REFRESH.value,
        "session_id": session_id,
    }
    
    return jwt.encode(claims, AuthConfig.JWT_SECRET, algorithm=AuthConfig.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token, 
            AuthConfig.JWT_SECRET, 
            algorithms=[AuthConfig.JWT_ALGORITHM],
            audience="yacco-emr-api",
            issuer="yacco-emr"
        )
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.InvalidAudienceError:
        return {"valid": False, "error": "Invalid audience"}
    except jwt.InvalidIssuerError:
        return {"valid": False, "error": "Invalid issuer"}
    except jwt.InvalidTokenError as e:
        return {"valid": False, "error": str(e)}


def validate_token_claims(payload: dict, required_claims: List[str] = None) -> bool:
    """Validate that token has required claims"""
    if required_claims is None:
        required_claims = ["sub", "role", "exp", "jti", "session_id"]
    
    return all(claim in payload for claim in required_claims)


# ============================================================================
# PERMISSION CHECKING UTILITIES
# ============================================================================

def check_permission(user_permissions: List[str], required_permission: str) -> bool:
    """Check if user has a specific permission"""
    return required_permission in user_permissions


def check_any_permission(user_permissions: List[str], required_permissions: List[str]) -> bool:
    """Check if user has at least one of the required permissions"""
    return any(perm in user_permissions for perm in required_permissions)


def check_all_permissions(user_permissions: List[str], required_permissions: List[str]) -> bool:
    """Check if user has all required permissions"""
    return all(perm in user_permissions for perm in required_permissions)


def check_organization_access(user_org_id: Optional[str], resource_org_id: str, user_role: str) -> bool:
    """
    Check if user can access resource from another organization
    Super admins can access all organizations
    """
    if user_role == "super_admin":
        return True
    return user_org_id == resource_org_id


# ============================================================================
# AUTHENTICATION FLOW IMPLEMENTATION
# ============================================================================

def create_auth_endpoints(db, get_current_user_func):
    """Create authentication endpoints with database access"""
    
    async def log_auth_event(
        user_id: str,
        action: str,
        success: bool,
        ip_address: str = None,
        user_agent: str = None,
        details: str = None
    ):
        """Log authentication events for audit"""
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "user_name": "Unknown",
            "user_role": "unknown",
            "action": action,
            "resource_type": "authentication",
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details,
            "severity": "info" if success else "warning"
        })
    
    async def create_session(
        user_id: str,
        ip_address: str = None,
        user_agent: str = None,
        device_id: str = None
    ) -> str:
        """Create a new session for user"""
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_id": device_id,
            "is_active": True
        }
        await db.sessions.insert_one(session)
        
        # Enforce session limits
        user_sessions = await db.sessions.find(
            {"user_id": user_id, "is_active": True}
        ).sort("created_at", 1).to_list(100)
        
        if len(user_sessions) > AuthConfig.MAX_SESSIONS_PER_USER:
            # Invalidate oldest sessions
            sessions_to_invalidate = user_sessions[:-AuthConfig.MAX_SESSIONS_PER_USER]
            for old_session in sessions_to_invalidate:
                await db.sessions.update_one(
                    {"id": old_session["id"]},
                    {"$set": {"is_active": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
                )
        
        return session_id
    
    @auth_router.post("/login/enhanced", response_model=LoginResponse)
    async def enhanced_login(request: Request, credentials: LoginRequest):
        """
        Enhanced login with full security features
        
        Flow:
        1. Validate credentials
        2. Check account status and lockout
        3. Verify organization is active
        4. Check MFA requirements
        5. Create session
        6. Generate tokens
        7. Log authentication event
        """
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Find user
        user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
        
        if not user:
            await log_auth_event(
                "unknown", "failed_login", False, ip_address, user_agent,
                f"Unknown email: {credentials.email}"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check account lockout
        if user.get("locked_until"):
            lock_time = datetime.fromisoformat(user["locked_until"].replace("Z", "+00:00"))
            if lock_time > datetime.now(timezone.utc):
                remaining = int((lock_time - datetime.now(timezone.utc)).total_seconds() / 60)
                raise HTTPException(
                    status_code=423,
                    detail=f"Account locked. Try again in {remaining} minutes."
                )
            else:
                # Unlock account
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {"locked_until": None, "failed_login_attempts": 0}}
                )
        
        # Verify password
        if not verify_password(credentials.password, user.get("password", "")):
            # Increment failed attempts
            attempts = user.get("failed_login_attempts", 0) + 1
            update_data = {"failed_login_attempts": attempts}
            
            if attempts >= AuthConfig.MAX_LOGIN_ATTEMPTS:
                lockout_until = datetime.now(timezone.utc) + timedelta(minutes=AuthConfig.LOCKOUT_DURATION_MINUTES)
                update_data["locked_until"] = lockout_until.isoformat()
                await log_auth_event(
                    user["id"], "account_locked", False, ip_address, user_agent,
                    f"Account locked after {attempts} failed attempts"
                )
            
            await db.users.update_one({"id": user["id"]}, {"$set": update_data})
            await log_auth_event(
                user["id"], "failed_login", False, ip_address, user_agent,
                "Invalid password"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Check organization status
        if user.get("organization_id") and user.get("role") != "super_admin":
            org = await db.organizations.find_one({"id": user["organization_id"]})
            if org and org.get("status") != "active":
                raise HTTPException(status_code=403, detail="Organization is not active")
        
        # Check MFA requirements
        mfa_verified = False
        user_2fa = await db.user_2fa.find_one({"user_id": user["id"]})
        mfa_enabled = user_2fa and user_2fa.get("enabled")
        
        # Check if MFA is required for this role
        mfa_required = user.get("role") in AuthConfig.MFA_REQUIRED_FOR_ROLES or mfa_enabled
        
        if mfa_required and mfa_enabled:
            if not credentials.totp_code:
                return LoginResponse(
                    access_token="",
                    token_type="Bearer",
                    expires_in=0,
                    user={"id": user["id"], "email": user["email"]},
                    mfa_required=True,
                    session_id=""
                )
            
            # Verify TOTP
            from twofa_module import verify_totp
            if not verify_totp(user_2fa["secret"], credentials.totp_code):
                # Try backup codes
                backup_valid = False
                backup_codes = user_2fa.get("backup_codes", [])
                code_normalized = credentials.totp_code.upper().replace("-", "").replace(" ", "")
                
                for bc in backup_codes:
                    if bc["code"].replace("-", "") == code_normalized and not bc.get("used"):
                        bc["used"] = True
                        bc["used_at"] = datetime.now(timezone.utc).isoformat()
                        await db.user_2fa.update_one(
                            {"user_id": user["id"]},
                            {"$set": {"backup_codes": backup_codes}}
                        )
                        backup_valid = True
                        break
                
                if not backup_valid:
                    await log_auth_event(
                        user["id"], "failed_mfa", False, ip_address, user_agent,
                        "Invalid MFA code"
                    )
                    raise HTTPException(status_code=401, detail="Invalid MFA code")
            
            mfa_verified = True
            await db.user_2fa.update_one(
                {"user_id": user["id"]},
                {"$set": {"last_used": datetime.now(timezone.utc).isoformat()}}
            )
        
        # Reset failed login attempts
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Create session
        session_id = await create_session(
            user["id"],
            ip_address,
            user_agent,
            credentials.device_id
        )
        
        # Generate tokens
        access_token = create_access_token(
            user,
            session_id,
            mfa_verified,
            ip_address,
            credentials.device_id
        )
        
        refresh_token = None
        if credentials.remember_me:
            refresh_token = create_refresh_token(user["id"], session_id)
        
        # Log successful login
        await log_auth_event(
            user["id"], "login", True, ip_address, user_agent,
            f"Successful login. MFA: {mfa_verified}"
        )
        
        # Prepare user response (exclude sensitive fields)
        user_response = {
            "id": user["id"],
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": user.get("role"),
            "organization_id": user.get("organization_id"),
            "department_id": user.get("department_id"),
            "groups": user.get("groups", []),
            "two_factor_enabled": mfa_enabled,
        }
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response,
            mfa_required=False,
            session_id=session_id
        )
    
    @auth_router.post("/refresh")
    async def refresh_access_token(request: RefreshTokenRequest):
        """Get new access token using refresh token"""
        result = decode_token(request.refresh_token)
        
        if not result["valid"]:
            raise HTTPException(status_code=401, detail=result["error"])
        
        payload = result["payload"]
        
        # Verify token type
        if payload.get("token_type") != TokenType.REFRESH.value:
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Verify session is still active
        session = await db.sessions.find_one({
            "id": payload.get("session_id"),
            "is_active": True
        })
        if not session:
            raise HTTPException(status_code=401, detail="Session expired")
        
        # Get user
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password": 0})
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Check MFA status from original session
        original_mfa = session.get("mfa_verified", False)
        
        # Update session activity
        await db.sessions.update_one(
            {"id": session["id"]},
            {"$set": {"last_activity": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Generate new access token
        new_access_token = create_access_token(
            user,
            session["id"],
            original_mfa
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @auth_router.post("/logout")
    async def logout(
        request: Request,
        current_user: dict = Depends(get_current_user_func)
    ):
        """Logout and invalidate session"""
        # Get session from token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            result = decode_token(token)
            if result["valid"]:
                session_id = result["payload"].get("session_id")
                if session_id:
                    await db.sessions.update_one(
                        {"id": session_id},
                        {"$set": {
                            "is_active": False,
                            "ended_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
        
        await log_auth_event(
            current_user["id"], "logout", True,
            request.client.host if request.client else None,
            request.headers.get("user-agent", ""),
            "User logged out"
        )
        
        return {"message": "Logged out successfully"}
    
    @auth_router.post("/logout/all")
    async def logout_all_sessions(
        request: Request,
        current_user: dict = Depends(get_current_user_func)
    ):
        """Logout from all sessions"""
        result = await db.sessions.update_many(
            {"user_id": current_user["id"], "is_active": True},
            {"$set": {
                "is_active": False,
                "ended_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        await log_auth_event(
            current_user["id"], "logout_all", True,
            request.client.host if request.client else None,
            request.headers.get("user-agent", ""),
            f"Logged out from {result.modified_count} sessions"
        )
        
        return {"message": f"Logged out from {result.modified_count} sessions"}
    
    @auth_router.get("/sessions", response_model=List[SessionInfo])
    async def get_user_sessions(
        request: Request,
        current_user: dict = Depends(get_current_user_func)
    ):
        """Get all active sessions for current user"""
        sessions = await db.sessions.find(
            {"user_id": current_user["id"], "is_active": True},
            {"_id": 0}
        ).to_list(50)
        
        # Get current session ID from token
        current_session_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            result = decode_token(token)
            if result["valid"]:
                current_session_id = result["payload"].get("session_id")
        
        return [
            SessionInfo(
                session_id=s["id"],
                user_id=s["user_id"],
                created_at=s["created_at"],
                last_activity=s["last_activity"],
                ip_address=s.get("ip_address"),
                user_agent=s.get("user_agent"),
                device_id=s.get("device_id"),
                is_current=s["id"] == current_session_id
            )
            for s in sessions
        ]
    
    @auth_router.delete("/sessions/{session_id}")
    async def revoke_session(
        session_id: str,
        current_user: dict = Depends(get_current_user_func)
    ):
        """Revoke a specific session"""
        session = await db.sessions.find_one({
            "id": session_id,
            "user_id": current_user["id"]
        })
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {
                "is_active": False,
                "ended_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Session revoked"}
    
    @auth_router.post("/validate")
    async def validate_token(request: Request):
        """Validate a token and return its claims"""
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return TokenValidationResponse(valid=False, error="No token provided")
        
        token = auth_header[7:]
        result = decode_token(token)
        
        if not result["valid"]:
            return TokenValidationResponse(valid=False, error=result["error"])
        
        payload = result["payload"]
        
        # Verify session is active
        session = await db.sessions.find_one({
            "id": payload.get("session_id"),
            "is_active": True
        })
        
        if not session:
            return TokenValidationResponse(valid=False, error="Session expired")
        
        return TokenValidationResponse(
            valid=True,
            user_id=payload.get("sub"),
            role=payload.get("role"),
            organization_id=payload.get("org_id"),
            permissions=payload.get("permissions", []),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc).isoformat()
        )
    
    @auth_router.post("/password/change")
    async def change_password(
        request: Request,
        password_data: PasswordChangeRequest,
        current_user: dict = Depends(get_current_user_func)
    ):
        """Change password for current user"""
        # Verify current password
        user = await db.users.find_one({"id": current_user["id"]})
        if not verify_password(password_data.current_password, user.get("password", "")):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Validate new password
        validation = validate_password_strength(password_data.new_password)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail={"errors": validation["errors"]})
        
        # Check password history
        password_history = user.get("password_history", [])
        for old_hash in password_history[-AuthConfig.PASSWORD_HISTORY_COUNT:]:
            if verify_password(password_data.new_password, old_hash):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reuse one of your last {AuthConfig.PASSWORD_HISTORY_COUNT} passwords"
                )
        
        # Update password
        new_hash = hash_password(password_data.new_password)
        password_history.append(user.get("password", ""))
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": {
                "password": new_hash,
                "password_history": password_history[-AuthConfig.PASSWORD_HISTORY_COUNT:],
                "password_changed_at": datetime.now(timezone.utc).isoformat(),
                "is_temp_password": False
            }}
        )
        
        # Invalidate all other sessions
        auth_header = request.headers.get("authorization", "")
        current_session_id = None
        if auth_header.startswith("Bearer "):
            result = decode_token(auth_header[7:])
            if result["valid"]:
                current_session_id = result["payload"].get("session_id")
        
        await db.sessions.update_many(
            {
                "user_id": current_user["id"],
                "is_active": True,
                "id": {"$ne": current_session_id}
            },
            {"$set": {"is_active": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        await log_auth_event(
            current_user["id"], "password_change", True,
            request.client.host if request.client else None,
            request.headers.get("user-agent", ""),
            "Password changed successfully"
        )
        
        return {"message": "Password changed successfully"}
    
    @auth_router.get("/permissions/check/{permission}")
    async def check_user_permission(
        permission: str,
        current_user: dict = Depends(get_current_user_func)
    ):
        """Check if current user has a specific permission"""
        # Get user's permissions from groups and direct assignments
        user_groups = current_user.get("groups", [])
        user_permissions = set(current_user.get("permissions", []))
        user_permissions.update(get_group_permissions(user_groups))
        
        # Super admin has all permissions
        if current_user.get("role") == "super_admin":
            return {"permission": permission, "granted": True, "reason": "super_admin"}
        
        granted = permission in user_permissions
        return {
            "permission": permission,
            "granted": granted,
            "reason": "permission_found" if granted else "permission_not_found"
        }
    
    @auth_router.get("/groups")
    async def get_permission_groups():
        """Get all available permission groups"""
        return [
            {
                "name": group.value,
                "display_name": group.value.replace("_", " ").title(),
                "permissions": list(GROUP_PERMISSIONS.get(group, set()))
            }
            for group in PermissionGroup
        ]
    
    return auth_router, create_access_token, decode_token, create_session


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'auth_router',
    'create_auth_endpoints',
    'AuthConfig',
    'JWTClaims',
    'TokenType',
    'PermissionGroup',
    'GROUP_PERMISSIONS',
    'create_access_token',
    'create_refresh_token',
    'decode_token',
    'validate_password_strength',
    'hash_password',
    'verify_password',
    'check_permission',
    'check_organization_access',
    'get_group_permissions',
]
