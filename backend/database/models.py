"""
SQLAlchemy Models for Yacco Health EMR
Enterprise-grade, normalized database schema
"""

from datetime import datetime, timezone
from typing import Optional, List
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Time,
    Text, JSON, ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint,
    DECIMAL, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


def utc_now():
    return datetime.now(timezone.utc)


def generate_uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# ============== CORE ENTITIES ==============

class Region(Base):
    """Ghana Regions"""
    __tablename__ = 'regions'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    capital: Mapped[Optional[str]] = mapped_column(String(100))
    code: Mapped[Optional[str]] = mapped_column(String(10))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    hospital_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class Organization(Base):
    """Multi-tenant Organizations (Hospitals, Clinics)"""
    __tablename__ = 'organizations'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[str] = mapped_column(String(50), default='hospital')
    region_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey('regions.id'))
    
    # Contact Information
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100), default='Ghana')
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Registration & Status
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    tax_id: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending', server_default='pending')
    registration_status: Mapped[Optional[str]] = mapped_column(String(50), default='pending', server_default='pending')
    
    # Subscription
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), default='basic', server_default='basic')
    max_users: Mapped[int] = mapped_column(Integer, default=50)
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    
    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    primary_color: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Metadata
    settings: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationships removed for flexible migration
    
    __table_args__ = (
        Index('ix_organizations_status', 'status'),
        Index('ix_organizations_region', 'region_id'),
    )


class Hospital(Base):
    """Hospitals registered in the system"""
    __tablename__ = 'hospitals'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_type: Mapped[str] = mapped_column(String(50), default='hospital')
    
    # Contact Info
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Registration
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    nhis_number: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending', server_default='pending')
    registration_status: Mapped[Optional[str]] = mapped_column(String(50), default='pending', server_default='pending')
    
    # Admin Info
    admin_name: Mapped[Optional[str]] = mapped_column(String(255))
    admin_email: Mapped[Optional[str]] = mapped_column(String(255))
    admin_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Settings
    settings: Mapped[Optional[dict]] = mapped_column(JSONB)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    
    __table_args__ = (
        Index('ix_hospitals_status', 'status'),
        Index('ix_hospitals_region', 'region_id'),
    )


# ============== USER MANAGEMENT ==============

class User(Base):
    """All system users (staff, physicians, nurses, admins)"""
    __tablename__ = 'users'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK for flexibility
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[Optional[str]] = mapped_column(String(255))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))  # Alternative field
    is_temp_password: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    two_factor_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    phone_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Role & Department
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    specialty: Mapped[Optional[str]] = mapped_column(String(100))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, server_default='true')
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active', server_default='active')
    
    # Security
    login_attempts: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_users_organization', 'organization_id'),
        Index('ix_users_role', 'role'),
        Index('ix_users_email', 'email'),
    )


class OTPSession(Base):
    """OTP Sessions for multi-factor authentication"""
    __tablename__ = 'otp_sessions'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    platform: Mapped[str] = mapped_column(String(50))  # emr, pharmacy, platform_owner
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Status
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_otp_user_platform', 'user_id', 'platform'),
    )


# ============== PATIENT MANAGEMENT ==============

class Patient(Base):
    """Patient records"""
    __tablename__ = 'patients'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK constraint for flexible migration
    
    # Identifiers
    mrn: Mapped[str] = mapped_column(String(50), nullable=False)  # Medical Record Number
    national_id: Mapped[Optional[str]] = mapped_column(String(50))
    nhis_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Demographics
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[Date]] = mapped_column(Date)  # Made nullable for migration
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))  # Increased length
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Insurance
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(255))
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(String(100))
    insurance_id: Mapped[Optional[str]] = mapped_column(String(100))  # Added
    insurance_plan: Mapped[Optional[str]] = mapped_column(String(255))  # Added
    payment_type: Mapped[Optional[str]] = mapped_column(String(50))  # Added
    
    # Notifications
    adt_notification: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)  # Added
    
    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, server_default='true')
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active', server_default='active')
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    
    __table_args__ = (
        Index('ix_patients_organization', 'organization_id'),
        Index('ix_patients_mrn', 'mrn'),
        Index('ix_patients_name', 'last_name', 'first_name'),
    )


class PatientMedicalHistory(Base):
    """Patient medical history - chronic conditions, past diagnoses"""
    __tablename__ = 'patient_medical_history'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Condition Type
    condition_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Condition Details
    condition_name: Mapped[str] = mapped_column(String(255), nullable=False)
    icd_code: Mapped[Optional[str]] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Dates
    onset_date: Mapped[Optional[Date]] = mapped_column(Date)
    resolved_date: Mapped[Optional[Date]] = mapped_column(Date)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active')
    severity: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Treatment
    current_treatment: Mapped[Optional[str]] = mapped_column(Text)
    medications: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Family History specific
    family_member_relationship: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    recorded_by: Mapped[Optional[str]] = mapped_column(String(50))
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    __table_args__ = (
        Index('ix_medical_history_patient', 'patient_id'),
        Index('ix_medical_history_type', 'condition_type'),
    )


# ============== CLINICAL DATA ==============

class Vital(Base):
    """Patient vital signs"""
    __tablename__ = 'vitals'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Vital Signs
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(Integer)
    heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer)
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    oxygen_saturation: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    height: Mapped[Optional[float]] = mapped_column(Float)
    bmi: Mapped[Optional[float]] = mapped_column(Float)
    pain_level: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    recorded_by: Mapped[Optional[str]] = mapped_column(String(50))
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (
        Index('ix_vitals_patient', 'patient_id'),
        Index('ix_vitals_recorded', 'recorded_at'),
    )


class Allergy(Base):
    """Patient allergies"""
    __tablename__ = 'allergies'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    allergen: Mapped[Optional[str]] = mapped_column(String(255))
    allergen_type: Mapped[Optional[str]] = mapped_column(String(50))
    reaction: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[Optional[str]] = mapped_column(String(50), default='moderate')
    
    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    onset_date: Mapped[Optional[Date]] = mapped_column(Date)
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    recorded_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_allergies_patient', 'patient_id'),
    )


# ============== REFERRAL SYSTEM ==============

class PatientReferral(Base):
    """Patient referrals between hospitals"""
    __tablename__ = 'patient_referrals'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    referral_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Patient Info
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    patient_dob: Mapped[Optional[Date]] = mapped_column(Date)
    patient_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Source Hospital
    source_organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    source_hospital_name: Mapped[str] = mapped_column(String(255), nullable=False)
    referring_physician_id: Mapped[str] = mapped_column(String(50), nullable=False)
    referring_physician_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Destination Hospital
    destination_organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    destination_hospital_name: Mapped[Optional[str]] = mapped_column(String(255))
    destination_hospital_address: Mapped[Optional[str]] = mapped_column(Text)
    destination_department: Mapped[Optional[str]] = mapped_column(String(100))
    receiving_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    receiving_physician_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Referral Details
    referral_type: Mapped[Optional[str]] = mapped_column(String(50), default='standard')
    priority: Mapped[Optional[str]] = mapped_column(String(50), default='routine')
    reason: Mapped[Optional[str]] = mapped_column(Text)
    clinical_summary: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    icd_codes: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Records to send
    include_medical_history: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    include_lab_results: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    include_imaging: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    include_prescriptions: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    attached_records: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Notes
    referral_notes: Mapped[Optional[str]] = mapped_column(Text)
    receiving_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (
        Index('ix_referrals_patient', 'patient_id'),
        Index('ix_referrals_source', 'source_organization_id'),
        Index('ix_referrals_dest', 'destination_organization_id'),
        Index('ix_referrals_status', 'status'),
    )


# ============== INTERNAL CHAT SYSTEM ==============

class ChatConversation(Base):
    """Chat conversations between staff"""
    __tablename__ = 'chat_conversations'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Conversation Type
    conversation_type: Mapped[Optional[str]] = mapped_column(String(50), default='direct')
    name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Participants (for direct messages - 2 users)
    participant_1_id: Mapped[Optional[str]] = mapped_column(String(50))
    participant_2_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Group participants stored in JSONB for group chats
    participants: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation")
    
    __table_args__ = (
        Index('ix_chat_conv_org', 'organization_id'),
        Index('ix_chat_conv_participants', 'participant_1_id', 'participant_2_id'),
    )


class ChatMessage(Base):
    """Chat messages"""
    __tablename__ = 'chat_messages'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(String(50), ForeignKey('chat_conversations.id'), nullable=False)
    
    # Sender
    sender_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Message Content
    message_type: Mapped[str] = mapped_column(String(50), default='text')  # text, image, file, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Attachments
    attachments: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Reply
    reply_to_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Status
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Read receipts stored as JSONB {user_id: timestamp}
    read_by: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    
    __table_args__ = (
        Index('ix_chat_msg_conv', 'conversation_id'),
        Index('ix_chat_msg_sender', 'sender_id'),
        Index('ix_chat_msg_created', 'created_at'),
    )


# ============== PRESCRIPTIONS ==============

class Prescription(Base):
    """Prescriptions"""
    __tablename__ = 'prescriptions'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    rx_number: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Patient
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Prescriber
    prescriber_id: Mapped[Optional[str]] = mapped_column(String(50))
    prescriber_name: Mapped[Optional[str]] = mapped_column(String(255))
    prescriber_license: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Medications (stored as JSONB array)
    medications: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Diagnosis
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    icd_codes: Mapped[Optional[list]] = mapped_column(JSONB)
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active')
    
    # Timestamps
    prescribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions", foreign_keys=[patient_id])
    
    __table_args__ = (
        Index('ix_prescriptions_patient', 'patient_id'),
        Index('ix_prescriptions_org', 'organization_id'),
    )


# ============== AUDIT & SECURITY ==============

class AuditLog(Base):
    """System-wide audit logs"""
    __tablename__ = 'audit_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    
    # Event Details
    event_type: Mapped[Optional[str]] = mapped_column(String(100))
    action: Mapped[Optional[str]] = mapped_column(String(100))
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(50))
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))  # MongoDB compat
    entity_id: Mapped[Optional[str]] = mapped_column(String(50))  # MongoDB compat
    
    # Actor
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    user_role: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    performed_by: Mapped[Optional[str]] = mapped_column(String(255))  # MongoDB compat
    
    # Request Details
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_method: Mapped[Optional[str]] = mapped_column(String(10))
    request_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Changes
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Result
    status: Mapped[Optional[str]] = mapped_column(String(50), default='success')
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamp
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)  # MongoDB compat
    
    __table_args__ = (
        Index('ix_audit_event', 'event_type'),
        Index('ix_audit_user', 'user_id'),
        Index('ix_audit_org', 'organization_id'),
        Index('ix_audit_timestamp', 'timestamp'),
    )


class RateLimitRecord(Base):
    """Rate limiting records"""
    __tablename__ = 'rate_limit_records'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    
    # Identifier
    key: Mapped[str] = mapped_column(String(255), nullable=False)  # user_id or IP
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Counts
    request_count: Mapped[int] = mapped_column(Integer, default=1)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        UniqueConstraint('key', 'endpoint', 'window_start', name='uq_rate_limit_key'),
        Index('ix_rate_limit_key', 'key'),
    )


# ============== PHARMACY ==============

class Pharmacy(Base):
    """Pharmacies"""
    __tablename__ = 'pharmacies'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Location
    region: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    town: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    gps_coordinates: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Admin
    admin_email: Mapped[Optional[str]] = mapped_column(String(255))
    admin_phone: Mapped[Optional[str]] = mapped_column(String(20))
    owner_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Status
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    registration_status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    
    # Settings
    settings: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[str]] = mapped_column(String(255))
    
    __table_args__ = (
        Index('ix_pharmacies_region', 'region'),
        Index('ix_pharmacies_status', 'status'),
    )


class PharmacyStaff(Base):
    """Pharmacy staff members"""
    __tablename__ = 'pharmacy_staff'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    pharmacy_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK
    pharmacy_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Profile
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Role
    role: Mapped[Optional[str]] = mapped_column(String(50))
    department: Mapped[Optional[str]] = mapped_column(String(100))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Status
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active')
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    __table_args__ = (
        Index('ix_pharmacy_staff_pharmacy', 'pharmacy_id'),
        Index('ix_pharmacy_staff_email', 'email'),
    )


# ============== DEPARTMENTS & FACILITIES ==============

class Department(Base):
    """Hospital departments"""
    __tablename__ = 'departments'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))  # No FK
    
    name: Mapped[Optional[str]] = mapped_column(String(255))
    code: Mapped[Optional[str]] = mapped_column(String(50))
    department_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    staff_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_departments_org', 'organization_id'),
    )


# Additional models will be added in subsequent files...
