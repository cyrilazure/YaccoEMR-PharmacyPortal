"""
Enterprise Security Middleware for Yacco Health
- Authentication & Authorization
- Rate Limiting
- Input Validation
- Audit Logging
"""

import os
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Callable, Dict, Any
from functools import wraps
import jwt
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging
import re

logger = logging.getLogger(__name__)

# Security Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'yacco-health-super-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # per window

security = HTTPBearer(auto_error=False)


# ============== TOKEN MANAGEMENT ==============

class TokenPayload(BaseModel):
    """JWT Token payload structure"""
    user_id: str
    email: Optional[str] = None
    role: str
    organization_id: Optional[str] = None
    platform: str = "emr"  # emr, pharmacy, platform_owner
    exp: int
    iat: Optional[int] = None


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    organization_id: Optional[str] = None,
    platform: str = "emr",
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)
    
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "organization_id": organization_id,
        "platform": platform,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


# ============== AUTHENTICATION DEPENDENCIES ==============

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    return decode_access_token(token)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenPayload]:
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None
    
    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def require_roles(*allowed_roles: str):
    """Dependency factory to require specific roles"""
    async def role_checker(
        user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker


def require_platform(*allowed_platforms: str):
    """Dependency factory to require specific platforms"""
    async def platform_checker(
        user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        if user.platform not in allowed_platforms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. This endpoint is for: {', '.join(allowed_platforms)}"
            )
        return user
    return platform_checker


def require_organization(
    user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require user to belong to an organization"""
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization membership required"
        )
    return user


# Platform Owner and Super Admin checker
async def require_platform_owner(
    user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require platform owner or super admin role"""
    allowed_roles = ['super_admin', 'platform_owner', 'platform_admin']
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform owner access required"
        )
    return user


# Hospital Admin checker
async def require_hospital_admin(
    user: TokenPayload = Depends(get_current_user)
) -> TokenPayload:
    """Require hospital admin role"""
    allowed_roles = ['hospital_admin', 'hospital_it_admin', 'super_admin', 'platform_owner']
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hospital admin access required"
        )
    return user


# ============== RATE LIMITING ==============

class RateLimiter:
    """In-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
    
    def _get_key(self, identifier: str, endpoint: str) -> str:
        return f"{identifier}:{endpoint}"
    
    def _clean_old_requests(self, key: str, window: int):
        """Remove requests outside the time window"""
        now = time.time()
        cutoff = now - window
        if key in self._requests:
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]
    
    def is_rate_limited(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window: int = RATE_LIMIT_WINDOW
    ) -> bool:
        """Check if the identifier is rate limited"""
        key = self._get_key(identifier, endpoint)
        self._clean_old_requests(key, window)
        
        if key not in self._requests:
            self._requests[key] = []
        
        if len(self._requests[key]) >= max_requests:
            return True
        
        self._requests[key].append(time.time())
        return False
    
    def get_remaining(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window: int = RATE_LIMIT_WINDOW
    ) -> int:
        """Get remaining requests in the window"""
        key = self._get_key(identifier, endpoint)
        self._clean_old_requests(key, window)
        
        current = len(self._requests.get(key, []))
        return max(0, max_requests - current)


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 100, window: int = 60):
    """Rate limiting decorator for endpoints"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            user: Optional[TokenPayload] = kwargs.get('user') or kwargs.get('current_user')
            
            # Use user_id if authenticated, otherwise use IP
            if user:
                identifier = user.user_id
            elif request:
                identifier = request.client.host if request.client else "unknown"
            else:
                identifier = "unknown"
            
            endpoint = func.__name__
            
            if rate_limiter.is_rate_limited(identifier, endpoint, max_requests, window):
                remaining = rate_limiter.get_remaining(identifier, endpoint, max_requests, window)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {window} seconds.",
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(window)
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============== INPUT VALIDATION ==============

class InputSanitizer:
    """Input sanitization utilities"""
    
    # Patterns for common SQL/NoSQL injection attempts
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(UNION\s+SELECT)",
    ]
    
    NOSQL_INJECTION_PATTERNS = [
        r"(\$where|\$gt|\$lt|\$ne|\$regex|\$or|\$and)",
        r"(\{|\}|\[|\])",  # JSON special chars in unexpected places
    ]
    
    XSS_PATTERNS = [
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:)",
        r"(on\w+\s*=)",
        r"(<iframe|<object|<embed)",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return value
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Strip leading/trailing whitespace
        value = value.strip()
        
        return value
    
    @classmethod
    def check_injection(cls, value: str, check_type: str = "all") -> bool:
        """Check for injection attempts. Returns True if suspicious."""
        if not isinstance(value, str):
            return False
        
        patterns = []
        if check_type in ["sql", "all"]:
            patterns.extend(cls.SQL_INJECTION_PATTERNS)
        if check_type in ["nosql", "all"]:
            patterns.extend(cls.NOSQL_INJECTION_PATTERNS)
        if check_type in ["xss", "all"]:
            patterns.extend(cls.XSS_PATTERNS)
        
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential injection detected: {pattern}")
                return True
        
        return False
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """Validate and sanitize email"""
        email = cls.sanitize_string(email, 255).lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email
    
    @classmethod
    def sanitize_phone(cls, phone: str) -> str:
        """Sanitize phone number"""
        # Remove all non-digit characters except + at start
        phone = cls.sanitize_string(phone, 20)
        if phone.startswith('+'):
            phone = '+' + re.sub(r'[^\d]', '', phone[1:])
        else:
            phone = re.sub(r'[^\d]', '', phone)
        
        return phone
    
    @classmethod
    def sanitize_uuid(cls, value: str) -> str:
        """Validate UUID format"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, value.lower()):
            raise ValueError("Invalid UUID format")
        return value.lower()


def validate_input(
    max_length: int = 1000,
    check_injection: bool = True,
    allowed_fields: Optional[List[str]] = None
):
    """Decorator for input validation"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Validate all string arguments
            for key, value in kwargs.items():
                if allowed_fields and key not in allowed_fields:
                    continue
                
                if isinstance(value, str):
                    value = InputSanitizer.sanitize_string(value, max_length)
                    
                    if check_injection and InputSanitizer.check_injection(value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid input detected in field: {key}"
                        )
                    
                    kwargs[key] = value
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============== AUDIT LOGGING ==============

class AuditLogger:
    """Centralized audit logging"""
    
    def __init__(self, db_session_factory=None):
        self.db_session_factory = db_session_factory
    
    async def log(
        self,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """Log an audit event"""
        import uuid
        
        log_entry = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "action": action,
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "organization_id": organization_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_values": old_values,
            "new_values": new_values,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_method": request_method,
            "request_path": request_path,
            "status": status,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log to file/console
        logger.info(f"AUDIT: {event_type}/{action} by {user_email or 'anonymous'} - {status}")
        
        # Store in database if available
        if self.db_session_factory:
            try:
                from .database.models import AuditLog
                async with self.db_session_factory() as session:
                    audit_log = AuditLog(**log_entry)
                    session.add(audit_log)
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to store audit log: {e}")
        
        return log_entry


# Global audit logger instance
audit_logger = AuditLogger()


def audit_log(event_type: str, action: str, resource_type: Optional[str] = None):
    """Decorator for automatic audit logging"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            user: Optional[TokenPayload] = kwargs.get('user') or kwargs.get('current_user')
            
            ip_address = request.client.host if request and request.client else None
            user_agent = request.headers.get('user-agent') if request else None
            
            try:
                result = await func(*args, **kwargs)
                
                await audit_logger.log(
                    event_type=event_type,
                    action=action,
                    user_id=user.user_id if user else None,
                    user_email=user.email if user else None,
                    user_role=user.role if user else None,
                    organization_id=user.organization_id if user else None,
                    resource_type=resource_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_method=request.method if request else None,
                    request_path=str(request.url.path) if request else None,
                    status="success"
                )
                
                return result
                
            except Exception as e:
                await audit_logger.log(
                    event_type=event_type,
                    action=action,
                    user_id=user.user_id if user else None,
                    user_email=user.email if user else None,
                    user_role=user.role if user else None,
                    organization_id=user.organization_id if user else None,
                    resource_type=resource_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_method=request.method if request else None,
                    request_path=str(request.url.path) if request else None,
                    status="failure",
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator


# ============== PASSWORD UTILITIES ==============

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    import bcrypt
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def generate_temp_password(length: int = 8) -> str:
    """Generate a temporary password"""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============== ERROR HANDLERS ==============

class APIError(Exception):
    """Base API error"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.headers = headers


class ValidationError(APIError):
    """Validation error"""
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
        self.field = field


class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(APIError):
    """Authorization error"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class ConflictError(APIError):
    """Conflict error (duplicate resource)"""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT"
        )
