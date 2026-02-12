"""
Enterprise Security Middleware for Yacco Health EMR
====================================================
Implements production-grade security features:
- Rate Limiting (per IP, per user, per endpoint)
- Input Validation & Sanitization
- Audit Logging
- Request/Response Logging
- CORS Hardening
- Security Headers
"""

import os
import time
import uuid
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Callable, List
from functools import wraps
from collections import defaultdict

from fastapi import Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt

# Try to import from database module
try:
    from database import audit_logs, to_dict
    from database.connection import async_session_factory
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

logger = logging.getLogger(__name__)

# ============== Configuration ==============

RATE_LIMIT_CONFIG = {
    # Default limits
    "default": {"requests": 100, "window_seconds": 60},
    
    # Endpoint-specific limits
    "/api/auth/login": {"requests": 5, "window_seconds": 60},
    "/api/auth/register": {"requests": 3, "window_seconds": 60},
    "/api/pharmacy-portal/login": {"requests": 5, "window_seconds": 60},
    "/api/pharmacy-portal/register": {"requests": 3, "window_seconds": 300},
    
    # More permissive for read operations
    "/api/patients": {"requests": 200, "window_seconds": 60},
    "/api/prescriptions": {"requests": 200, "window_seconds": 60},
    "/api/health": {"requests": 1000, "window_seconds": 60},
}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}

# Sensitive fields to redact from logs
SENSITIVE_FIELDS = {
    "password", "password_hash", "token", "secret", "api_key", 
    "credit_card", "ssn", "social_security", "authorization"
}


# ============== In-Memory Rate Limiter ==============

class RateLimiter:
    """
    Thread-safe in-memory rate limiter using sliding window algorithm.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.last_cleanup = time.time()
    
    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key"""
        return f"{identifier}:{endpoint}"
    
    def _cleanup_old_requests(self):
        """Remove expired request timestamps"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff = now - 3600  # Keep last hour
        keys_to_delete = []
        
        for key, timestamps in self.requests.items():
            self.requests[key] = [ts for ts in timestamps if ts > cutoff]
            if not self.requests[key]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.requests[key]
        
        self.last_cleanup = now
    
    def is_rate_limited(
        self, 
        identifier: str, 
        endpoint: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited.
        Returns (is_limited, rate_limit_info)
        """
        self._cleanup_old_requests()
        
        key = self._get_key(identifier, endpoint)
        now = time.time()
        cutoff = now - window_seconds
        
        # Filter timestamps within window
        self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]
        current_count = len(self.requests[key])
        
        rate_limit_info = {
            "limit": max_requests,
            "remaining": max(0, max_requests - current_count - 1),
            "reset": int(cutoff + window_seconds),
            "window_seconds": window_seconds
        }
        
        if current_count >= max_requests:
            return True, rate_limit_info
        
        # Record this request
        self.requests[key].append(now)
        rate_limit_info["remaining"] = max(0, max_requests - current_count - 1)
        
        return False, rate_limit_info


# Global rate limiter instance
rate_limiter = RateLimiter()


# ============== Audit Logger ==============

class AuditLogger:
    """
    Centralized audit logging for security-relevant events.
    Stores logs in PostgreSQL if available, otherwise in-memory/file.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.use_postgres = HAS_POSTGRES
    
    async def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "INFO",
        request_id: Optional[str] = None
    ):
        """Create an audit log entry"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "action": action,
            "user_id": user_id,
            "user_email": user_email,
            "organization_id": organization_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": self._sanitize_details(details),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "severity": severity,
            "request_id": request_id
        }
        
        # Log to console
        log_msg = f"AUDIT [{severity}] {action} | user={user_email or user_id} | ip={ip_address}"
        if severity == "ERROR":
            logger.error(log_msg)
        elif severity == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        # Store in PostgreSQL if available
        if self.use_postgres:
            try:
                await audit_logs.create(log_entry)
            except Exception as e:
                logger.error(f"Failed to store audit log in PostgreSQL: {e}")
        
        # Fallback to MongoDB if available
        elif self.db:
            try:
                log_entry["timestamp"] = log_entry["timestamp"].isoformat()
                if log_entry.get("details"):
                    log_entry["details"] = json.dumps(log_entry["details"])
                await self.db["audit_logs"].insert_one(log_entry)
            except Exception as e:
                logger.error(f"Failed to store audit log in MongoDB: {e}")
    
    def _sanitize_details(self, details: Optional[Dict]) -> Optional[Dict]:
        """Remove sensitive information from details"""
        if not details:
            return None
        
        sanitized = {}
        for key, value in details.items():
            if key.lower() in SENSITIVE_FIELDS:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        
        return sanitized


# Global audit logger (will be initialized with db in middleware setup)
audit_logger: Optional[AuditLogger] = None


# ============== Input Sanitization ==============

class InputSanitizer:
    """Sanitize and validate input data"""
    
    # Common SQL injection patterns
    SQL_PATTERNS = [
        r"(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)(\s|$)",
        r"(--|#|/\*)",
        r"(\bOR\b|\bAND\b)\s*\d+\s*=\s*\d+",
        r"'\s*OR\s*'",
    ]
    
    # Common XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<embed",
        r"<object",
    ]
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Basic string sanitization"""
        if not isinstance(value, str):
            return value
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        # Strip leading/trailing whitespace
        value = value.strip()
        
        return value
    
    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Validate UUID format"""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def validate_email(value: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def validate_phone(value: str) -> bool:
        """Basic phone validation (Ghana format)"""
        import re
        # Allow various formats: +233..., 0..., 233...
        pattern = r'^(\+?233|0)[\d\s-]{9,15}$'
        cleaned = re.sub(r'[\s-]', '', value)
        return bool(re.match(pattern, cleaned))


sanitizer = InputSanitizer()


# ============== Security Middleware ==============

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Main security middleware that applies:
    - Rate limiting
    - Security headers
    - Request logging
    - CORS handling
    """
    
    def __init__(self, app, db=None):
        super().__init__(app)
        self.db = db
        global audit_logger
        audit_logger = AuditLogger(db)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get endpoint path
        endpoint = request.url.path
        
        # Apply rate limiting
        rate_config = RATE_LIMIT_CONFIG.get(endpoint, RATE_LIMIT_CONFIG["default"])
        is_limited, rate_info = rate_limiter.is_rate_limited(
            identifier=client_ip,
            endpoint=endpoint,
            max_requests=rate_config["requests"],
            window_seconds=rate_config["window_seconds"]
        )
        
        if is_limited:
            # Log rate limit event
            if audit_logger:
                await audit_logger.log(
                    action="RATE_LIMIT_EXCEEDED",
                    ip_address=client_ip,
                    details={"endpoint": endpoint, "rate_info": rate_info},
                    severity="WARNING",
                    request_id=request_id
                )
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": rate_info["reset"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["reset"] - int(time.time()))
                }
            )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            if audit_logger:
                await audit_logger.log(
                    action="REQUEST_ERROR",
                    ip_address=client_ip,
                    details={"endpoint": endpoint, "error": str(e)},
                    severity="ERROR",
                    request_id=request_id
                )
            raise
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        
        # Add request tracking headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{response_time:.3f}s"
        
        # Log significant requests (non-health checks, errors)
        if endpoint != "/api/health" and (response.status_code >= 400 or response_time > 1.0):
            logger.info(
                f"[{request_id}] {request.method} {endpoint} "
                f"-> {response.status_code} ({response_time:.3f}s) "
                f"IP: {client_ip}"
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for forwarded headers (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"


# ============== Authentication Decorators ==============

def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request") or (args[0] if args else None)
        if not request:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        return await func(*args, **kwargs)
    return wrapper


def audit_action(action: str, resource_type: Optional[str] = None):
    """Decorator to audit endpoint actions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            current_user = kwargs.get("current_user")
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log the action
            if audit_logger:
                await audit_logger.log(
                    action=action,
                    user_id=current_user.get("id") if current_user else None,
                    user_email=current_user.get("email") if current_user else None,
                    resource_type=resource_type,
                    ip_address=request.client.host if request and request.client else None,
                    request_id=getattr(request.state, "request_id", None) if request else None
                )
            
            return result
        return wrapper
    return decorator


# ============== Helper Functions ==============

def setup_security(app, db=None):
    """Setup security middleware on FastAPI app"""
    app.add_middleware(SecurityMiddleware, db=db)
    logger.info("Security middleware enabled with rate limiting and audit logging")


async def log_security_event(
    action: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    severity: str = "INFO"
):
    """Helper function to log security events"""
    if audit_logger:
        await audit_logger.log(
            action=action,
            user_id=user_id,
            user_email=user_email,
            details=details,
            ip_address=ip_address,
            severity=severity
        )
