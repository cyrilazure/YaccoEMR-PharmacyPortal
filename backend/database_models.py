"""
Comprehensive Database Models for Yacco EMR
HIPAA-Compliant Electronic Medical Records System

This module defines all database entities with:
- Table/entity definitions
- Key relationships
- Fields for compliance and auditing
- Multi-tenant (organization) support

Collections:
- organizations: Hospitals/Healthcare facilities
- departments: Hospital departments and units
- users: Staff members with roles
- patients: Patient demographics
- medical_records: Clinical documentation
- consent_forms: Patient consent documents
- records_access_requests: Inter-hospital sharing requests
- audit_logs: HIPAA compliance audit trail
- notifications: System notifications
"""

from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid


# ============================================================================
# ENUMERATIONS
# ============================================================================

class OrganizationStatus(str, Enum):
    """Status of organization registration"""
    PENDING = "pending"        # Awaiting approval
    ACTIVE = "active"          # Approved and operational
    SUSPENDED = "suspended"    # Temporarily suspended
    REJECTED = "rejected"      # Registration rejected
    INACTIVE = "inactive"      # Voluntarily deactivated


class OrganizationType(str, Enum):
    """Type of healthcare organization"""
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    MEDICAL_CENTER = "medical_center"
    URGENT_CARE = "urgent_care"
    SPECIALTY_CENTER = "specialty_center"
    NURSING_HOME = "nursing_home"
    REHABILITATION_CENTER = "rehabilitation_center"
    DIAGNOSTIC_CENTER = "diagnostic_center"


class DepartmentType(str, Enum):
    """Type of hospital department"""
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    ICU = "icu"
    SURGERY = "surgery"
    PEDIATRICS = "pediatrics"
    OBSTETRICS = "obstetrics"
    CARDIOLOGY = "cardiology"
    ONCOLOGY = "oncology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    RADIOLOGY = "radiology"
    LABORATORY = "laboratory"
    PHARMACY = "pharmacy"
    ADMINISTRATION = "administration"
    OTHER = "other"


class UserRole(str, Enum):
    """User roles with hierarchical access levels"""
    SUPER_ADMIN = "super_admin"        # Platform administrator
    HOSPITAL_ADMIN = "hospital_admin"  # Hospital administrator
    ADMIN = "admin"                    # Department administrator
    PHYSICIAN = "physician"            # Doctor/Attending
    NURSE = "nurse"                    # Registered Nurse
    SCHEDULER = "scheduler"            # Front desk/Scheduling
    PHARMACIST = "pharmacist"          # Pharmacy staff
    LAB_TECH = "lab_tech"              # Laboratory technician
    RADIOLOGIST = "radiologist"        # Radiology specialist
    BILLING = "billing"                # Billing/Revenue staff


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"        # Invitation pending
    LOCKED = "locked"          # Account locked (security)


class PatientStatus(str, Enum):
    """Patient registration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"
    TRANSFERRED = "transferred"


class Gender(str, Enum):
    """Patient gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class RecordType(str, Enum):
    """Types of medical records"""
    CLINICAL_NOTE = "clinical_note"
    PROGRESS_NOTE = "progress_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    OPERATIVE_REPORT = "operative_report"
    CONSULTATION = "consultation"
    H_AND_P = "history_and_physical"
    LAB_RESULT = "lab_result"
    IMAGING_STUDY = "imaging_study"
    PRESCRIPTION = "prescription"
    VITAL_SIGNS = "vital_signs"
    IMMUNIZATION = "immunization"
    ALLERGY = "allergy"
    PROBLEM_LIST = "problem_list"
    PROCEDURE = "procedure"


class ConsentType(str, Enum):
    """Types of patient consent"""
    TREATMENT = "treatment"                    # General treatment consent
    HIPAA = "hipaa"                           # HIPAA privacy notice
    RECORDS_RELEASE = "records_release"       # Release of medical records
    PROCEDURE = "procedure"                   # Procedure-specific consent
    RESEARCH = "research"                     # Research participation
    TELEHEALTH = "telehealth"                 # Telehealth consent
    MEDICATION = "medication"                 # Medication consent
    PHOTOGRAPHY = "photography"               # Photography/recording consent
    FINANCIAL = "financial"                   # Financial responsibility


class ConsentStatus(str, Enum):
    """Status of consent form"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"


class AccessRequestStatus(str, Enum):
    """Status of record access request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class AccessRequestUrgency(str, Enum):
    """Urgency level of access request"""
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class NotificationType(str, Enum):
    """Types of system notifications"""
    ACCESS_REQUEST = "access_request"
    ACCESS_APPROVED = "access_approved"
    ACCESS_REJECTED = "access_rejected"
    CONSENT_REQUIRED = "consent_required"
    APPOINTMENT_REMINDER = "appointment_reminder"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    SECURITY_ALERT = "security_alert"
    SYSTEM = "system"


class AuditAction(str, Enum):
    """Audit log action types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    EXPORT = "export"
    PRINT = "print"
    ACCESS_GRANTED = "access_granted"
    ACCESS_REVOKED = "access_revoked"
    CONSENT_GIVEN = "consent_given"
    CONSENT_REVOKED = "consent_revoked"
    PERMISSION_DENIED = "permission_denied"


class AuditSeverity(str, Enum):
    """Severity level of audit events"""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


# ============================================================================
# ORGANIZATION MODEL
# Hospital/Healthcare Facility
# ============================================================================

class OrganizationModel(BaseModel):
    """
    Organization/Hospital entity
    
    Relationships:
    - Has many: Departments, Users, Patients
    - Referenced by: Medical Records, Consent Forms, Audit Logs
    
    Collection: organizations
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    name: str                                           # Hospital name
    organization_type: OrganizationType = OrganizationType.HOSPITAL
    status: OrganizationStatus = OrganizationStatus.PENDING
    
    # Identifiers
    license_number: str                                 # State license
    tax_id: Optional[str] = None                       # Tax identification
    npi_number: Optional[str] = None                   # National Provider Identifier
    
    # Contact Information
    email: EmailStr
    phone: str
    fax: Optional[str] = None
    website: Optional[str] = None
    
    # Address
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    
    # Primary Contact (Administrator)
    admin_first_name: str
    admin_last_name: str
    admin_email: EmailStr
    admin_phone: str
    admin_title: Optional[str] = "Administrator"
    
    # Branding
    logo_url: Optional[str] = None
    
    # Subscription/Limits
    subscription_plan: str = "standard"
    max_users: int = 50
    max_patients: int = 10000
    max_storage_gb: int = 100
    
    # Statistics (Denormalized for performance)
    total_users: int = 0
    total_patients: int = 0
    total_departments: int = 0
    
    # Compliance Settings
    hipaa_compliant: bool = True
    data_retention_days: int = 2555                    # 7 years default
    require_2fa: bool = False                          # Enforce 2FA for all users
    session_timeout_minutes: int = 30
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Approval Workflow
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    suspension_reason: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# DEPARTMENT MODEL
# Hospital Departments and Units
# ============================================================================

class DepartmentModel(BaseModel):
    """
    Department/Unit entity
    
    Relationships:
    - Belongs to: Organization
    - Has many: Users (staff assigned)
    - Parent/Child: Self-referential for sub-units
    
    Collection: departments
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    organization_id: str                               # Parent organization
    parent_department_id: Optional[str] = None         # Parent department (for units/sub-departments)
    
    # Basic Information
    name: str                                          # e.g., "Emergency Department"
    code: str                                          # e.g., "ED", "ICU"
    department_type: DepartmentType
    description: Optional[str] = None
    
    # Status
    is_active: bool = True
    
    # Contact Information
    phone: Optional[str] = None
    extension: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None                     # Building/Floor/Room
    
    # Capacity
    bed_count: Optional[int] = None
    max_patients: Optional[int] = None
    
    # Operating Hours
    operating_hours: Optional[Dict[str, Any]] = None   # JSON: {"mon": "08:00-17:00", ...}
    is_24_7: bool = False
    
    # Head of Department
    head_user_id: Optional[str] = None                 # Department head/chief
    
    # Cost Center (for billing)
    cost_center_code: Optional[str] = None
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# USER MODEL
# Staff Members with Roles
# ============================================================================

class UserModel(BaseModel):
    """
    User/Staff entity
    
    Relationships:
    - Belongs to: Organization, Department
    - Creates: Medical Records, Consent Forms
    - Has: Audit Logs, Notifications
    
    Collection: users
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    organization_id: Optional[str] = None              # Hospital (null for super_admin)
    department_id: Optional[str] = None                # Primary department
    
    # Authentication
    email: EmailStr
    password_hash: str                                 # Bcrypt hashed
    
    # Profile
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    title: Optional[str] = None                        # Dr., RN, etc.
    
    # Role & Permissions
    role: UserRole
    permissions: Optional[List[str]] = None            # Override permissions
    
    # Professional Information
    specialty: Optional[str] = None                    # Medical specialty
    license_number: Optional[str] = None               # Professional license
    npi_number: Optional[str] = None                   # National Provider Identifier
    dea_number: Optional[str] = None                   # DEA number for prescribing
    
    # Contact
    phone: Optional[str] = None
    mobile: Optional[str] = None
    pager: Optional[str] = None
    
    # Status
    status: UserStatus = UserStatus.ACTIVE
    is_active: bool = True
    
    # Security
    two_factor_enabled: bool = False
    is_temp_password: bool = False                     # Requires password change
    password_changed_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Session Management
    current_session_id: Optional[str] = None
    
    # Employment
    employee_id: Optional[str] = None
    hire_date: Optional[str] = None
    termination_date: Optional[str] = None
    
    # Preferences
    timezone: str = "America/New_York"
    language: str = "en"
    notification_preferences: Optional[Dict[str, bool]] = None
    
    # Digital Signature
    signature_image_url: Optional[str] = None
    signature_pin_hash: Optional[str] = None           # PIN for signing documents
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# PATIENT MODEL
# Patient Demographics and Registration
# ============================================================================

class PatientModel(BaseModel):
    """
    Patient entity
    
    Relationships:
    - Belongs to: Organization
    - Has many: Medical Records, Consent Forms, Appointments
    - Referenced by: Access Requests
    
    Collection: patients
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Foreign Key
    organization_id: str                               # Primary organization
    
    # Identifiers
    mrn: str = Field(default_factory=lambda: f"MRN{str(uuid.uuid4())[:8].upper()}")  # Medical Record Number
    ssn_last_four: Optional[str] = None               # Last 4 digits only (encrypted)
    external_id: Optional[str] = None                 # External system ID
    
    # Demographics
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    date_of_birth: str                                # YYYY-MM-DD format
    gender: Gender
    
    # Contact Information
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Insurance (Primary)
    insurance_provider: Optional[str] = None
    insurance_plan: Optional[str] = None
    insurance_id: Optional[str] = None
    insurance_group: Optional[str] = None
    
    # Insurance (Secondary)
    secondary_insurance_provider: Optional[str] = None
    secondary_insurance_id: Optional[str] = None
    
    # Primary Care
    primary_care_physician_id: Optional[str] = None
    primary_care_physician_name: Optional[str] = None
    
    # Status
    status: PatientStatus = PatientStatus.ACTIVE
    
    # Preferences
    preferred_language: str = "en"
    preferred_pharmacy_id: Optional[str] = None
    communication_preferences: Optional[Dict[str, bool]] = None  # email, sms, phone
    
    # Privacy
    hipaa_consent_date: Optional[str] = None
    restrict_disclosure: bool = False                 # Restrict information disclosure
    vip_flag: bool = False                            # VIP patient (extra privacy)
    
    # Portal Access
    portal_enabled: bool = False
    portal_email: Optional[str] = None
    portal_registered_at: Optional[datetime] = None
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    registered_by: Optional[str] = None               # User who registered
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# MEDICAL RECORD MODEL
# Clinical Documentation
# ============================================================================

class MedicalRecordModel(BaseModel):
    """
    Medical Record entity - Base for all clinical documentation
    
    Relationships:
    - Belongs to: Patient, Organization
    - Created by: User
    - May have: Consent Form (for sharing)
    
    Collection: medical_records
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    patient_id: str
    organization_id: str
    author_id: str                                     # User who created
    department_id: Optional[str] = None
    encounter_id: Optional[str] = None                 # Associated encounter/visit
    
    # Record Type
    record_type: RecordType
    
    # Content
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None          # Structured content (JSON)
    content_text: Optional[str] = None                # Plain text version
    
    # SOAP Notes (for clinical notes)
    chief_complaint: Optional[str] = None
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    
    # Clinical Codes
    icd_codes: Optional[List[str]] = None             # ICD-10 diagnosis codes
    cpt_codes: Optional[List[str]] = None             # CPT procedure codes
    snomed_codes: Optional[List[str]] = None          # SNOMED CT codes
    
    # Status
    status: str = "draft"                             # draft, final, amended, deleted
    is_signed: bool = False
    signed_at: Optional[datetime] = None
    signed_by: Optional[str] = None
    
    # Amendment (if amended)
    is_amendment: bool = False
    amends_record_id: Optional[str] = None
    amendment_reason: Optional[str] = None
    
    # Confidentiality
    confidentiality_level: str = "normal"             # normal, restricted, very_restricted
    sensitive_categories: Optional[List[str]] = None  # HIV, mental_health, substance_abuse
    
    # Attachments
    attachments: Optional[List[Dict[str, str]]] = None  # [{id, filename, url, type}]
    
    # Versioning
    version: int = 1
    previous_version_id: Optional[str] = None
    
    # Sharing
    shared_with_organizations: Optional[List[str]] = None
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    updated_by: Optional[str] = None
    
    # Record date (when care was provided)
    record_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# CONSENT FORM MODEL
# Patient Consent Documents
# ============================================================================

class ConsentFormModel(BaseModel):
    """
    Patient Consent Form entity
    
    Relationships:
    - Belongs to: Patient, Organization
    - Witnessed by: User
    - Related to: Records Access Request (if records_release)
    
    Collection: consent_forms
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    patient_id: str
    organization_id: str
    related_request_id: Optional[str] = None          # Related access request
    
    # Consent Type
    consent_type: ConsentType
    
    # Content
    title: str
    description: str
    consent_text: str                                  # Full consent language
    
    # Scope (for records release)
    scope_start_date: Optional[str] = None            # Records from date
    scope_end_date: Optional[str] = None              # Records to date
    record_types_included: Optional[List[str]] = None # Types of records covered
    recipient_organization_id: Optional[str] = None   # Who can receive
    recipient_organization_name: Optional[str] = None
    purpose: Optional[str] = None                      # Purpose of release
    
    # Status
    status: ConsentStatus = ConsentStatus.ACTIVE
    
    # Signatures
    patient_signature: Optional[str] = None           # Base64 image or reference
    patient_signed_at: Optional[datetime] = None
    patient_signed_ip: Optional[str] = None
    
    guardian_name: Optional[str] = None               # If signed by guardian
    guardian_relationship: Optional[str] = None
    guardian_signature: Optional[str] = None
    
    # Witness (Staff)
    witness_id: Optional[str] = None
    witness_name: Optional[str] = None
    witness_signed_at: Optional[datetime] = None
    
    # Expiration
    effective_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiration_date: Optional[datetime] = None
    
    # Revocation
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revocation_reason: Optional[str] = None
    
    # Document
    document_url: Optional[str] = None                # PDF storage
    document_hash: Optional[str] = None               # SHA-256 for integrity
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    updated_by: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# RECORDS ACCESS REQUEST MODEL
# Inter-Hospital Record Sharing Requests
# ============================================================================

class RecordsAccessRequestModel(BaseModel):
    """
    Records Access Request entity - For inter-hospital sharing
    
    Relationships:
    - Belongs to: Patient
    - Requesting: User (requestor), Organization
    - Providing: User (responder), Organization
    - Requires: Consent Form
    
    Collection: records_access_requests
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Request Number (human-readable)
    request_number: str = Field(default_factory=lambda: f"RAR-{str(uuid.uuid4())[:8].upper()}")
    
    # Patient Information
    patient_id: str
    patient_name: str                                  # Denormalized for reference
    patient_dob: str
    patient_mrn: Optional[str] = None
    
    # Requesting Party
    requesting_user_id: str                            # Physician making request
    requesting_user_name: str
    requesting_organization_id: str
    requesting_organization_name: str
    
    # Providing Party (Source of records)
    providing_organization_id: str
    providing_organization_name: str
    responding_user_id: Optional[str] = None          # User who responds
    responding_user_name: Optional[str] = None
    
    # Request Details
    request_reason: str                                # Clinical reason
    urgency: AccessRequestUrgency = AccessRequestUrgency.ROUTINE
    
    # Scope
    record_types_requested: List[str]                  # Types of records needed
    date_range_start: Optional[str] = None            # Records from date
    date_range_end: Optional[str] = None              # Records to date
    specific_records: Optional[List[str]] = None      # Specific record IDs
    
    # Status
    status: AccessRequestStatus = AccessRequestStatus.PENDING
    
    # Consent
    consent_obtained: bool = False
    consent_form_id: Optional[str] = None
    consent_date: Optional[datetime] = None
    consent_method: Optional[str] = None              # verbal, written, electronic
    
    # Response
    response_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Access Grant
    access_granted_at: Optional[datetime] = None
    access_expires_at: Optional[datetime] = None
    access_duration_days: int = 30                     # Default 30 days
    
    # Records Shared
    shared_record_ids: Optional[List[str]] = None
    shared_records_count: int = 0
    
    # Tracking
    first_accessed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# AUDIT LOG MODEL
# HIPAA Compliance Audit Trail
# ============================================================================

class AuditLogModel(BaseModel):
    """
    Audit Log entity - HIPAA compliance tracking
    
    Relationships:
    - References: User, Patient, Organization
    - Tracks: All PHI access and system events
    
    Collection: audit_logs
    
    HIPAA Requirements:
    - Track all access to PHI
    - 6-year retention minimum
    - Immutable records
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Timestamp (ISO 8601)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Actor (Who)
    user_id: str
    user_name: str
    user_role: str
    user_email: Optional[str] = None
    
    # Organization Context
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    
    # Action (What)
    action: AuditAction
    severity: AuditSeverity = AuditSeverity.INFO
    
    # Resource (On What)
    resource_type: str                                 # patient, medical_record, etc.
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Patient Context (if PHI access)
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    
    # Details
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None          # Additional structured data
    
    # Before/After (for updates)
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    fields_changed: Optional[List[str]] = None
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    # Request Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None                   # Correlation ID
    
    # Geolocation (optional)
    geo_country: Optional[str] = None
    geo_region: Optional[str] = None
    geo_city: Optional[str] = None
    
    # Compliance Flags
    phi_accessed: bool = False                         # Protected Health Information
    is_breach: bool = False                            # Potential security breach
    requires_review: bool = False                      # Flagged for review


# ============================================================================
# NOTIFICATION MODEL
# System Notifications
# ============================================================================

class NotificationModel(BaseModel):
    """
    Notification entity
    
    Relationships:
    - Belongs to: User (recipient)
    - References: Various entities based on type
    
    Collection: notifications
    """
    model_config = ConfigDict(extra="ignore")
    
    # Primary Key
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Recipient
    user_id: str
    organization_id: Optional[str] = None
    
    # Notification Type
    notification_type: NotificationType
    
    # Content
    title: str
    message: str
    
    # Priority
    priority: str = "normal"                           # low, normal, high, urgent
    
    # Status
    is_read: bool = False
    read_at: Optional[datetime] = None
    
    # Dismissal
    is_dismissed: bool = False
    dismissed_at: Optional[datetime] = None
    
    # Related Entity
    related_type: Optional[str] = None                 # Type of related entity
    related_id: Optional[str] = None                   # ID of related entity
    
    # Action
    action_url: Optional[str] = None                   # URL to navigate to
    action_label: Optional[str] = None                 # Button text
    
    # Delivery
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    sms_sent: bool = False
    sms_sent_at: Optional[datetime] = None
    push_sent: bool = False
    push_sent_at: Optional[datetime] = None
    
    # Expiration
    expires_at: Optional[datetime] = None
    
    # Audit Fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# DATABASE INDEXES AND RELATIONSHIPS
# ============================================================================

"""
MongoDB Indexes for Performance:

organizations:
  - { "id": 1 } (unique)
  - { "status": 1 }
  - { "email": 1 } (unique)
  - { "npi_number": 1 }

departments:
  - { "id": 1 } (unique)
  - { "organization_id": 1 }
  - { "organization_id": 1, "code": 1 } (unique)
  - { "parent_department_id": 1 }

users:
  - { "id": 1 } (unique)
  - { "email": 1 } (unique)
  - { "organization_id": 1 }
  - { "organization_id": 1, "role": 1 }
  - { "department_id": 1 }

patients:
  - { "id": 1 } (unique)
  - { "organization_id": 1 }
  - { "organization_id": 1, "mrn": 1 } (unique)
  - { "last_name": 1, "first_name": 1 }
  - { "date_of_birth": 1 }
  - { "email": 1 }

medical_records:
  - { "id": 1 } (unique)
  - { "patient_id": 1 }
  - { "organization_id": 1 }
  - { "patient_id": 1, "record_type": 1 }
  - { "author_id": 1 }
  - { "created_at": -1 }

consent_forms:
  - { "id": 1 } (unique)
  - { "patient_id": 1 }
  - { "organization_id": 1 }
  - { "consent_type": 1 }
  - { "status": 1 }

records_access_requests:
  - { "id": 1 } (unique)
  - { "request_number": 1 } (unique)
  - { "patient_id": 1 }
  - { "requesting_organization_id": 1 }
  - { "providing_organization_id": 1 }
  - { "status": 1 }

audit_logs:
  - { "id": 1 } (unique)
  - { "timestamp": -1 }
  - { "user_id": 1, "timestamp": -1 }
  - { "patient_id": 1, "timestamp": -1 }
  - { "organization_id": 1, "timestamp": -1 }
  - { "action": 1, "timestamp": -1 }
  - { "severity": 1 }
  - { "phi_accessed": 1, "timestamp": -1 }

notifications:
  - { "id": 1 } (unique)
  - { "user_id": 1, "is_read": 1 }
  - { "user_id": 1, "created_at": -1 }
  - { "organization_id": 1 }
  - { "notification_type": 1 }

Entity Relationship Diagram (ERD):

┌──────────────────┐
│  Organization    │
│  (Hospital)      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Depart- │ │ Users  │
│ments   │ │(Staff) │
└────────┘ └───┬────┘
               │
               ▼
         ┌──────────┐
         │ Patients │
         └────┬─────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│Medical │ │Consent │ │Access  │
│Records │ │ Forms  │ │Requests│
└────────┘ └────────┘ └────────┘
              │
              ▼
         ┌──────────┐
         │ Audit    │
         │ Logs     │
         └──────────┘
"""

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    'OrganizationStatus', 'OrganizationType', 'DepartmentType',
    'UserRole', 'UserStatus', 'PatientStatus', 'Gender',
    'RecordType', 'ConsentType', 'ConsentStatus',
    'AccessRequestStatus', 'AccessRequestUrgency',
    'NotificationType', 'AuditAction', 'AuditSeverity',
    # Models
    'OrganizationModel', 'DepartmentModel', 'UserModel',
    'PatientModel', 'MedicalRecordModel', 'ConsentFormModel',
    'RecordsAccessRequestModel', 'AuditLogModel', 'NotificationModel',
]
