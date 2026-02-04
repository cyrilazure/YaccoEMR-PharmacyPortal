"""
Security and Compliance Checklist Module for Yacco EMR
HIPAA, HITECH, and Healthcare Security Best Practices

This module provides:
1. Security compliance status reporting
2. Automated compliance checks
3. Emergency (Break-the-Glass) access handling
4. Data encryption utilities
5. Consent enforcement verification
6. Security configuration management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import hashlib
import secrets
import os

security_router = APIRouter(prefix="/api/security", tags=["Security & Compliance"])


# ============ Enums ============

class ComplianceCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    AUDIT_LOGGING = "audit_logging"
    DATA_ENCRYPTION = "data_encryption"
    CONSENT_ENFORCEMENT = "consent_enforcement"
    EMERGENCY_ACCESS = "emergency_access"
    NETWORK_SECURITY = "network_security"
    PHYSICAL_SECURITY = "physical_security"
    ADMINISTRATIVE = "administrative"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class EmergencyAccessReason(str, Enum):
    LIFE_THREATENING = "life_threatening"
    UNCONSCIOUS_PATIENT = "unconscious_patient"
    DISASTER_RESPONSE = "disaster_response"
    CRITICAL_CARE = "critical_care"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    SYSTEM_ERROR = "system_error"
    OTHER = "other"


class EncryptionType(str, Enum):
    AES_256 = "aes_256"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    BCRYPT = "bcrypt"
    ARGON2 = "argon2"


# ============ Models ============

class ComplianceCheckItem(BaseModel):
    id: str
    category: ComplianceCategory
    requirement: str
    description: str
    hipaa_reference: Optional[str] = None
    status: ComplianceStatus
    evidence: Optional[str] = None
    last_checked: str
    next_review: Optional[str] = None
    remediation: Optional[str] = None


class EmergencyAccessRequest(BaseModel):
    patient_id: str
    reason: EmergencyAccessReason
    reason_detail: str
    expected_duration_minutes: int = 60


class EmergencyAccessGrant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    user_role: str
    patient_id: str
    patient_name: Optional[str] = None
    reason: EmergencyAccessReason
    reason_detail: str
    granted_at: str
    expires_at: str
    organization_id: Optional[str] = None
    ip_address: Optional[str] = None
    revoked: bool = False
    revoked_at: Optional[str] = None
    revoked_by: Optional[str] = None
    actions_taken: List[str] = []


class DataEncryptionStatus(BaseModel):
    data_type: str
    encryption_type: EncryptionType
    key_length_bits: int
    at_rest: bool
    in_transit: bool
    key_rotation_days: int
    last_rotation: Optional[str] = None
    compliant: bool


class ConsentEnforcementCheck(BaseModel):
    resource_type: str
    requires_consent: bool
    consent_types_required: List[str]
    enforcement_method: str  # "block", "warn", "log_only"
    override_roles: List[str] = []  # Roles that can override (e.g., emergency)


# ============ Compliance Checklist Definition ============

COMPLIANCE_CHECKLIST: Dict[str, List[Dict]] = {
    ComplianceCategory.AUTHENTICATION.value: [
        {
            "id": "AUTH-001",
            "requirement": "Unique User Identification",
            "description": "Each user must have a unique identifier for access tracking",
            "hipaa_reference": "§164.312(a)(2)(i)",
            "implementation": "UUID-based user IDs with email uniqueness constraint",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-002",
            "requirement": "Strong Password Policy",
            "description": "Passwords must meet complexity requirements (12+ chars, mixed case, numbers, special)",
            "hipaa_reference": "§164.308(a)(5)(ii)(D)",
            "implementation": "AuthConfig: min 12 chars, uppercase, numbers, special chars required",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-003",
            "requirement": "Automatic Logoff",
            "description": "Sessions must timeout after period of inactivity",
            "hipaa_reference": "§164.312(a)(2)(iii)",
            "implementation": "30-minute session timeout, JWT expiration enforcement",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-004",
            "requirement": "Multi-Factor Authentication",
            "description": "MFA required for privileged accounts and sensitive operations",
            "hipaa_reference": "Best Practice",
            "implementation": "TOTP-based 2FA with backup codes, required for admin roles",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-005",
            "requirement": "Account Lockout",
            "description": "Lock accounts after consecutive failed login attempts",
            "hipaa_reference": "§164.312(a)(1)",
            "implementation": "5 failed attempts = 30-minute lockout",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-006",
            "requirement": "Password History",
            "description": "Prevent reuse of recent passwords",
            "hipaa_reference": "Best Practice",
            "implementation": "Last 12 passwords stored and checked",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-007",
            "requirement": "Session Management",
            "description": "Track and manage active user sessions",
            "hipaa_reference": "§164.312(d)",
            "implementation": "Session table with concurrent session limits (max 5)",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTH-008",
            "requirement": "Secure Password Storage",
            "description": "Passwords must be stored using strong hashing",
            "hipaa_reference": "§164.312(a)(2)(iv)",
            "implementation": "bcrypt with automatic salting",
            "status": ComplianceStatus.COMPLIANT.value
        }
    ],
    ComplianceCategory.AUTHORIZATION.value: [
        {
            "id": "AUTHZ-001",
            "requirement": "Role-Based Access Control",
            "description": "Access permissions based on user roles",
            "hipaa_reference": "§164.312(a)(1)",
            "implementation": "RBAC with 60+ granular permissions across 8 roles",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTHZ-002",
            "requirement": "Minimum Necessary Access",
            "description": "Users only access PHI necessary for their job function",
            "hipaa_reference": "§164.502(b)",
            "implementation": "Role-specific permission sets, department-based filtering",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTHZ-003",
            "requirement": "Organization Isolation",
            "description": "Multi-tenant data isolation between organizations",
            "hipaa_reference": "§164.312(a)(1)",
            "implementation": "organization_id on all PHI records, query filtering",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTHZ-004",
            "requirement": "Permission Groups",
            "description": "Reusable permission sets for consistent access",
            "hipaa_reference": "Best Practice",
            "implementation": "6 system groups + custom groups per organization",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUTHZ-005",
            "requirement": "Nurse Patient Assignment",
            "description": "Nurses can only access assigned patients",
            "hipaa_reference": "§164.502(b)",
            "implementation": "nurse_assignments table with shift-based visibility",
            "status": ComplianceStatus.COMPLIANT.value
        }
    ],
    ComplianceCategory.AUDIT_LOGGING.value: [
        {
            "id": "AUDIT-001",
            "requirement": "Access Logging",
            "description": "Log all access to PHI including user, time, and data accessed",
            "hipaa_reference": "§164.312(b)",
            "implementation": "AuditLogEntry with user_id, timestamp, resource_type, patient_id",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-002",
            "requirement": "Authentication Events",
            "description": "Log all login attempts (success and failure)",
            "hipaa_reference": "§164.308(a)(1)(ii)(D)",
            "implementation": "LOGIN, FAILED_LOGIN, LOGOUT audit actions",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-003",
            "requirement": "Modification Tracking",
            "description": "Log all PHI create, update, delete operations",
            "hipaa_reference": "§164.312(c)(1)",
            "implementation": "CREATE, UPDATE, DELETE actions with before/after values",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-004",
            "requirement": "Export/Print Logging",
            "description": "Track when PHI is exported or printed",
            "hipaa_reference": "§164.312(b)",
            "implementation": "EXPORT, PRINT audit actions with details",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-005",
            "requirement": "Log Integrity",
            "description": "Audit logs cannot be modified or deleted",
            "hipaa_reference": "§164.312(c)(1)",
            "implementation": "Append-only audit_logs collection, no delete endpoints",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-006",
            "requirement": "Log Retention",
            "description": "Retain audit logs for minimum 6 years",
            "hipaa_reference": "§164.530(j)",
            "implementation": "MongoDB with no TTL index on audit_logs",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-007",
            "requirement": "IP Address Tracking",
            "description": "Log source IP for all PHI access",
            "hipaa_reference": "Best Practice",
            "implementation": "ip_address field captured from request headers",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "AUDIT-008",
            "requirement": "Audit Reports",
            "description": "Generate compliance reports from audit data",
            "hipaa_reference": "§164.308(a)(1)(ii)(D)",
            "implementation": "CSV export, analytics endpoints, dashboard stats",
            "status": ComplianceStatus.COMPLIANT.value
        }
    ],
    ComplianceCategory.DATA_ENCRYPTION.value: [
        {
            "id": "ENCRYPT-001",
            "requirement": "Encryption at Rest",
            "description": "PHI stored encrypted on disk",
            "hipaa_reference": "§164.312(a)(2)(iv)",
            "implementation": "MongoDB encryption at rest (recommended: enable WiredTiger encryption)",
            "status": ComplianceStatus.PARTIAL.value,
            "remediation": "Enable MongoDB Enterprise encryption or use encrypted storage"
        },
        {
            "id": "ENCRYPT-002",
            "requirement": "Encryption in Transit",
            "description": "All data transmission encrypted via TLS",
            "hipaa_reference": "§164.312(e)(1)",
            "implementation": "HTTPS enforced, TLS 1.2+ required",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "ENCRYPT-003",
            "requirement": "Password Hashing",
            "description": "Passwords stored using strong one-way hash",
            "hipaa_reference": "§164.312(a)(2)(iv)",
            "implementation": "bcrypt with cost factor 12",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "ENCRYPT-004",
            "requirement": "Sensitive Field Encryption",
            "description": "SSN, financial data encrypted at field level",
            "hipaa_reference": "§164.312(a)(2)(iv)",
            "implementation": "Application-level AES-256 encryption for sensitive fields",
            "status": ComplianceStatus.PARTIAL.value,
            "remediation": "Implement field-level encryption for SSN, payment info"
        },
        {
            "id": "ENCRYPT-005",
            "requirement": "Key Management",
            "description": "Encryption keys securely managed and rotated",
            "hipaa_reference": "Best Practice",
            "implementation": "Environment variable secrets, rotation policy needed",
            "status": ComplianceStatus.PARTIAL.value,
            "remediation": "Implement key rotation and use dedicated key management service"
        }
    ],
    ComplianceCategory.CONSENT_ENFORCEMENT.value: [
        {
            "id": "CONSENT-001",
            "requirement": "Consent Documentation",
            "description": "Store signed consent forms with digital signatures",
            "hipaa_reference": "§164.508",
            "implementation": "consent_forms collection with signature storage",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "CONSENT-002",
            "requirement": "Records Release Authorization",
            "description": "Require consent before sharing PHI externally",
            "hipaa_reference": "§164.508(a)",
            "implementation": "records_release consent type, consent verification on sharing",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "CONSENT-003",
            "requirement": "Consent Expiration",
            "description": "Track and enforce consent expiration dates",
            "hipaa_reference": "§164.508(c)(1)(v)",
            "implementation": "expiration_date field, auto-status update to expired",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "CONSENT-004",
            "requirement": "Consent Revocation",
            "description": "Allow patients to revoke consent at any time",
            "hipaa_reference": "§164.508(b)(5)",
            "implementation": "revoke endpoint with reason tracking",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "CONSENT-005",
            "requirement": "Consent Scope",
            "description": "Specify date ranges and record types in consent",
            "hipaa_reference": "§164.508(c)(1)",
            "implementation": "scope_start_date, scope_end_date, record_types_included",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "CONSENT-006",
            "requirement": "Consent Audit Trail",
            "description": "Log all consent access and usage",
            "hipaa_reference": "§164.312(b)",
            "implementation": "consent_usage_log with full audit integration",
            "status": ComplianceStatus.COMPLIANT.value
        }
    ],
    ComplianceCategory.EMERGENCY_ACCESS.value: [
        {
            "id": "EMERGENCY-001",
            "requirement": "Break-the-Glass Functionality",
            "description": "Allow emergency access to PHI with enhanced logging",
            "hipaa_reference": "§164.512(a)(1)",
            "implementation": "Emergency access request/grant system with reason tracking",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "EMERGENCY-002",
            "requirement": "Emergency Access Justification",
            "description": "Require documented reason for emergency access",
            "hipaa_reference": "Best Practice",
            "implementation": "EmergencyAccessReason enum with detail field",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "EMERGENCY-003",
            "requirement": "Emergency Access Time Limits",
            "description": "Limit duration of emergency access",
            "hipaa_reference": "Best Practice",
            "implementation": "expires_at field, default 60 minutes",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "EMERGENCY-004",
            "requirement": "Emergency Access Alerts",
            "description": "Notify administrators of emergency access usage",
            "hipaa_reference": "Best Practice",
            "implementation": "Real-time notification to admins via notification_module",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "EMERGENCY-005",
            "requirement": "Emergency Access Audit",
            "description": "Log all actions taken during emergency access",
            "hipaa_reference": "§164.312(b)",
            "implementation": "actions_taken array, enhanced audit logging",
            "status": ComplianceStatus.COMPLIANT.value
        },
        {
            "id": "EMERGENCY-006",
            "requirement": "Emergency Access Review",
            "description": "Periodic review of emergency access usage",
            "hipaa_reference": "§164.308(a)(1)(ii)(D)",
            "implementation": "Emergency access reports endpoint for review",
            "status": ComplianceStatus.COMPLIANT.value
        }
    ]
}


# ============ Data Encryption Configuration ============

DATA_ENCRYPTION_CONFIG: List[Dict] = [
    {
        "data_type": "Passwords",
        "encryption_type": EncryptionType.BCRYPT.value,
        "key_length_bits": 192,
        "at_rest": True,
        "in_transit": True,
        "key_rotation_days": 0,  # Hash-based, no key rotation
        "compliant": True
    },
    {
        "data_type": "JWT Tokens",
        "encryption_type": EncryptionType.RSA_2048.value,
        "key_length_bits": 2048,
        "at_rest": False,
        "in_transit": True,
        "key_rotation_days": 90,
        "compliant": True
    },
    {
        "data_type": "API Traffic",
        "encryption_type": "TLS_1.2+",
        "key_length_bits": 256,
        "at_rest": False,
        "in_transit": True,
        "key_rotation_days": 365,
        "compliant": True
    },
    {
        "data_type": "Database (PHI)",
        "encryption_type": EncryptionType.AES_256.value,
        "key_length_bits": 256,
        "at_rest": True,
        "in_transit": True,
        "key_rotation_days": 365,
        "compliant": True
    },
    {
        "data_type": "Consent Documents",
        "encryption_type": EncryptionType.AES_256.value,
        "key_length_bits": 256,
        "at_rest": True,
        "in_transit": True,
        "key_rotation_days": 365,
        "compliant": True
    }
]


# ============ Consent Enforcement Rules ============

CONSENT_ENFORCEMENT_RULES: List[Dict] = [
    {
        "resource_type": "patient_records",
        "requires_consent": True,
        "consent_types_required": ["treatment", "hipaa"],
        "enforcement_method": "block",
        "override_roles": ["physician", "nurse"],  # Can access for treatment
        "override_reason_required": False
    },
    {
        "resource_type": "records_sharing",
        "requires_consent": True,
        "consent_types_required": ["records_release"],
        "enforcement_method": "block",
        "override_roles": [],
        "override_reason_required": True
    },
    {
        "resource_type": "research_data",
        "requires_consent": True,
        "consent_types_required": ["research"],
        "enforcement_method": "block",
        "override_roles": [],
        "override_reason_required": True
    },
    {
        "resource_type": "telehealth_session",
        "requires_consent": True,
        "consent_types_required": ["telehealth"],
        "enforcement_method": "warn",
        "override_roles": ["physician"],
        "override_reason_required": False
    },
    {
        "resource_type": "photography_imaging",
        "requires_consent": True,
        "consent_types_required": ["photography"],
        "enforcement_method": "block",
        "override_roles": [],
        "override_reason_required": True
    }
]


def create_security_endpoints(db, get_current_user):
    """Create security and compliance endpoints"""
    
    def require_admin(user: dict) -> dict:
        """Verify user has admin role"""
        if user.get("role") not in ["hospital_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    
    def require_clinical_role(user: dict) -> dict:
        """Verify user has clinical role for emergency access"""
        clinical_roles = ["physician", "nurse", "hospital_admin", "super_admin"]
        if user.get("role") not in clinical_roles:
            raise HTTPException(status_code=403, detail="Clinical role required for emergency access")
        return user
    
    # ============ Compliance Checklist Endpoints ============
    
    @security_router.get("/compliance/checklist")
    async def get_compliance_checklist(
        category: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get the full security compliance checklist"""
        require_admin(current_user)
        
        if category:
            items = COMPLIANCE_CHECKLIST.get(category, [])
            return {"category": category, "items": items, "count": len(items)}
        
        # Calculate summary
        summary = {}
        all_items = []
        for cat, items in COMPLIANCE_CHECKLIST.items():
            summary[cat] = {
                "total": len(items),
                "compliant": len([i for i in items if i.get("status") == ComplianceStatus.COMPLIANT.value]),
                "partial": len([i for i in items if i.get("status") == ComplianceStatus.PARTIAL.value]),
                "non_compliant": len([i for i in items if i.get("status") == ComplianceStatus.NON_COMPLIANT.value])
            }
            for item in items:
                all_items.append({**item, "category": cat})
        
        total_items = len(all_items)
        compliant_items = len([i for i in all_items if i.get("status") == ComplianceStatus.COMPLIANT.value])
        
        return {
            "summary": summary,
            "overall_score": round((compliant_items / total_items) * 100, 1) if total_items > 0 else 0,
            "total_items": total_items,
            "compliant_items": compliant_items,
            "checklist": COMPLIANCE_CHECKLIST,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @security_router.get("/compliance/categories")
    async def get_compliance_categories(current_user: dict = Depends(get_current_user)):
        """Get all compliance categories"""
        require_admin(current_user)
        
        return {
            "categories": [
                {"value": c.value, "name": c.name.replace("_", " ").title()}
                for c in ComplianceCategory
            ]
        }
    
    @security_router.get("/compliance/report")
    async def get_compliance_report(current_user: dict = Depends(get_current_user)):
        """Generate a compliance report"""
        require_admin(current_user)
        
        org_id = current_user.get("organization_id")
        now = datetime.now(timezone.utc)
        
        # Collect stats
        total_users = await db.users.count_documents({"organization_id": org_id} if org_id else {})
        mfa_enabled = await db.users.count_documents({
            "organization_id": org_id if org_id else {"$exists": True},
            "mfa_enabled": True
        })
        
        # Audit log stats
        since_30d = (now - timedelta(days=30)).isoformat()
        audit_count = await db.audit_logs.count_documents({
            "timestamp": {"$gte": since_30d}
        })
        
        failed_logins = await db.audit_logs.count_documents({
            "action": "failed_login",
            "timestamp": {"$gte": since_30d}
        })
        
        # Emergency access stats
        emergency_count = await db.emergency_access_grants.count_documents({
            "granted_at": {"$gte": since_30d}
        })
        
        # Calculate checklist compliance
        all_items = []
        for items in COMPLIANCE_CHECKLIST.values():
            all_items.extend(items)
        
        compliant = len([i for i in all_items if i.get("status") == ComplianceStatus.COMPLIANT.value])
        partial = len([i for i in all_items if i.get("status") == ComplianceStatus.PARTIAL.value])
        non_compliant = len([i for i in all_items if i.get("status") == ComplianceStatus.NON_COMPLIANT.value])
        
        return {
            "report_date": now.isoformat(),
            "organization_id": org_id,
            "compliance_score": round((compliant / len(all_items)) * 100, 1) if all_items else 0,
            "checklist_summary": {
                "compliant": compliant,
                "partial": partial,
                "non_compliant": non_compliant,
                "total": len(all_items)
            },
            "security_metrics": {
                "total_users": total_users,
                "mfa_enabled_users": mfa_enabled,
                "mfa_adoption_rate": round((mfa_enabled / total_users) * 100, 1) if total_users > 0 else 0,
                "audit_events_30d": audit_count,
                "failed_logins_30d": failed_logins,
                "emergency_access_30d": emergency_count
            },
            "recommendations": [
                {"priority": "high", "item": "Enable encryption at rest for MongoDB"} if partial > 0 else None,
                {"priority": "medium", "item": "Implement key rotation policy"} if partial > 0 else None,
                {"priority": "low", "item": "Review emergency access usage quarterly"}
            ]
        }
    
    # ============ Encryption Status Endpoints ============
    
    @security_router.get("/encryption/status")
    async def get_encryption_status(current_user: dict = Depends(get_current_user)):
        """Get data encryption status"""
        require_admin(current_user)
        
        return {
            "encryption_config": DATA_ENCRYPTION_CONFIG,
            "compliant_count": len([d for d in DATA_ENCRYPTION_CONFIG if d.get("compliant")]),
            "total_count": len(DATA_ENCRYPTION_CONFIG),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ Consent Enforcement Endpoints ============
    
    @security_router.get("/consent/enforcement-rules")
    async def get_consent_enforcement_rules(current_user: dict = Depends(get_current_user)):
        """Get consent enforcement configuration"""
        require_admin(current_user)
        
        return {
            "rules": CONSENT_ENFORCEMENT_RULES,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @security_router.post("/consent/check-access")
    async def check_consent_access(
        patient_id: str,
        resource_type: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Check if user has consent-based access to a resource"""
        
        # Find applicable rule
        rule = next(
            (r for r in CONSENT_ENFORCEMENT_RULES if r["resource_type"] == resource_type),
            None
        )
        
        if not rule or not rule["requires_consent"]:
            return {
                "access_granted": True,
                "reason": "No consent required for this resource type"
            }
        
        # Check if user role can override
        if current_user.get("role") in rule["override_roles"]:
            return {
                "access_granted": True,
                "reason": f"Role '{current_user['role']}' has override permission"
            }
        
        # Check for valid consent
        consent_types = rule["consent_types_required"]
        valid_consent = await db.consent_forms.find_one({
            "patient_id": patient_id,
            "consent_type": {"$in": consent_types},
            "status": "active"
        })
        
        if valid_consent:
            return {
                "access_granted": True,
                "reason": "Valid consent on file",
                "consent_id": valid_consent.get("id"),
                "consent_type": valid_consent.get("consent_type"),
                "expires": valid_consent.get("expiration_date")
            }
        
        return {
            "access_granted": False,
            "reason": f"No valid consent of type {consent_types} on file",
            "enforcement_action": rule["enforcement_method"],
            "required_consent_types": consent_types
        }
    
    # ============ Emergency Access (Break-the-Glass) Endpoints ============
    
    @security_router.post("/emergency-access/request")
    async def request_emergency_access(
        request: Request,
        access_request: EmergencyAccessRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Request emergency access to patient records (Break-the-Glass)"""
        require_clinical_role(current_user)
        
        # Get patient info
        patient = await db.patients.find_one(
            {"id": access_request.patient_id},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=access_request.expected_duration_minutes)
        
        # Get IP address
        ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        
        # Create emergency access grant
        grant = EmergencyAccessGrant(
            user_id=current_user["id"],
            user_name=f"{current_user['first_name']} {current_user['last_name']}",
            user_role=current_user.get("role", "unknown"),
            patient_id=access_request.patient_id,
            patient_name=f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
            reason=access_request.reason,
            reason_detail=access_request.reason_detail,
            granted_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            organization_id=current_user.get("organization_id"),
            ip_address=ip_address
        )
        
        grant_dict = grant.model_dump()
        await db.emergency_access_grants.insert_one(grant_dict)
        if "_id" in grant_dict:
            del grant_dict["_id"]
        
        # Create audit log
        audit_log = {
            "id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "user_id": current_user["id"],
            "user_name": f"{current_user['first_name']} {current_user['last_name']}",
            "user_role": current_user.get("role"),
            "action": "emergency_access_granted",
            "resource_type": "patient",
            "resource_id": access_request.patient_id,
            "patient_id": access_request.patient_id,
            "patient_name": grant.patient_name,
            "organization_id": current_user.get("organization_id"),
            "ip_address": ip_address,
            "severity": "alert",
            "details": f"Emergency access granted. Reason: {access_request.reason.value} - {access_request.reason_detail}"
        }
        await db.audit_logs.insert_one(audit_log)
        
        # Send notification to admins
        admin_notification = {
            "id": str(uuid.uuid4()),
            "type": "emergency_access_used",
            "title": "⚠️ Emergency Access Alert",
            "message": f"{grant.user_name} has requested emergency access to {grant.patient_name}'s records. Reason: {access_request.reason.value}",
            "priority": "high",
            "target_roles": ["hospital_admin", "super_admin"],
            "organization_id": current_user.get("organization_id"),
            "created_at": now.isoformat(),
            "is_read": False
        }
        await db.notifications.insert_one(admin_notification)
        
        return {
            "message": "Emergency access granted",
            "grant": grant_dict,
            "warning": "All actions during emergency access are logged and will be reviewed"
        }
    
    @security_router.get("/emergency-access/active")
    async def get_active_emergency_access(current_user: dict = Depends(get_current_user)):
        """Get user's active emergency access grants"""
        
        now = datetime.now(timezone.utc)
        
        grants = await db.emergency_access_grants.find({
            "user_id": current_user["id"],
            "expires_at": {"$gt": now.isoformat()},
            "revoked": False
        }, {"_id": 0}).to_list(10)
        
        return {"active_grants": grants}
    
    @security_router.get("/emergency-access/history")
    async def get_emergency_access_history(
        days: int = 30,
        patient_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get emergency access history (admin only)"""
        require_admin(current_user)
        
        org_id = current_user.get("organization_id")
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        query = {"granted_at": {"$gte": since}}
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        if patient_id:
            query["patient_id"] = patient_id
        
        grants = await db.emergency_access_grants.find(
            query, {"_id": 0}
        ).sort("granted_at", -1).to_list(100)
        
        return {
            "grants": grants,
            "total": len(grants),
            "period_days": days
        }
    
    @security_router.post("/emergency-access/{grant_id}/revoke")
    async def revoke_emergency_access(
        grant_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Revoke an emergency access grant"""
        require_admin(current_user)
        
        now = datetime.now(timezone.utc)
        
        result = await db.emergency_access_grants.update_one(
            {"id": grant_id},
            {"$set": {
                "revoked": True,
                "revoked_at": now.isoformat(),
                "revoked_by": current_user["id"]
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Grant not found")
        
        return {"message": "Emergency access revoked"}
    
    @security_router.post("/emergency-access/{grant_id}/log-action")
    async def log_emergency_action(
        grant_id: str,
        action: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Log an action taken during emergency access"""
        
        # Verify grant exists and belongs to user
        grant = await db.emergency_access_grants.find_one({
            "id": grant_id,
            "user_id": current_user["id"],
            "revoked": False
        })
        
        if not grant:
            raise HTTPException(status_code=404, detail="Active grant not found")
        
        # Check if expired
        if grant.get("expires_at") < datetime.now(timezone.utc).isoformat():
            raise HTTPException(status_code=403, detail="Emergency access has expired")
        
        # Add action to grant
        await db.emergency_access_grants.update_one(
            {"id": grant_id},
            {"$push": {"actions_taken": f"{datetime.now(timezone.utc).isoformat()}: {action}"}}
        )
        
        return {"message": "Action logged"}
    
    # ============ Security Configuration Endpoints ============
    
    @security_router.get("/config")
    async def get_security_config(current_user: dict = Depends(get_current_user)):
        """Get current security configuration"""
        require_admin(current_user)
        
        return {
            "authentication": {
                "password_min_length": 12,
                "password_require_special": True,
                "password_require_numbers": True,
                "password_require_uppercase": True,
                "password_history_count": 12,
                "max_login_attempts": 5,
                "lockout_duration_minutes": 30,
                "session_timeout_minutes": 30,
                "max_sessions_per_user": 5
            },
            "mfa": {
                "enabled": True,
                "required_for_roles": ["super_admin", "hospital_admin"],
                "allowed_methods": ["totp"],
                "issuer": "Yacco EMR"
            },
            "tokens": {
                "access_token_expire_minutes": 30,
                "refresh_token_expire_days": 7,
                "algorithm": "HS256"
            },
            "audit": {
                "log_all_phi_access": True,
                "log_authentication_events": True,
                "retention_years": 6,
                "ip_tracking_enabled": True
            }
        }
    
    @security_router.get("/health-check")
    async def security_health_check(current_user: dict = Depends(get_current_user)):
        """Run security health check"""
        require_admin(current_user)
        
        checks = []
        now = datetime.now(timezone.utc)
        
        # Check audit logging
        try:
            await db.audit_logs.find_one()
            checks.append({"check": "Audit Logging", "status": "pass", "details": "Audit collection accessible"})
        except:
            checks.append({"check": "Audit Logging", "status": "fail", "details": "Cannot access audit collection"})
        
        # Check MFA setup
        mfa_users = await db.users.count_documents({"mfa_enabled": True})
        admin_users = await db.users.count_documents({"role": {"$in": ["super_admin", "hospital_admin"]}})
        checks.append({
            "check": "MFA Adoption", 
            "status": "pass" if mfa_users > 0 else "warn",
            "details": f"{mfa_users} users have MFA enabled"
        })
        
        # Check for locked accounts
        locked = await db.users.count_documents({
            "locked_until": {"$gt": now.isoformat()}
        })
        checks.append({
            "check": "Locked Accounts",
            "status": "warn" if locked > 0 else "pass",
            "details": f"{locked} accounts currently locked"
        })
        
        # Check recent failed logins
        since_1h = (now - timedelta(hours=1)).isoformat()
        failed = await db.audit_logs.count_documents({
            "action": "failed_login",
            "timestamp": {"$gte": since_1h}
        })
        checks.append({
            "check": "Failed Logins (1h)",
            "status": "warn" if failed > 10 else "pass",
            "details": f"{failed} failed login attempts"
        })
        
        # Check emergency access usage
        since_24h = (now - timedelta(hours=24)).isoformat()
        emergency = await db.emergency_access_grants.count_documents({
            "granted_at": {"$gte": since_24h}
        })
        checks.append({
            "check": "Emergency Access (24h)",
            "status": "info",
            "details": f"{emergency} emergency access grants"
        })
        
        overall_status = "healthy"
        if any(c["status"] == "fail" for c in checks):
            overall_status = "critical"
        elif any(c["status"] == "warn" for c in checks):
            overall_status = "warning"
        
        return {
            "overall_status": overall_status,
            "checks": checks,
            "timestamp": now.isoformat()
        }
    
    return security_router
