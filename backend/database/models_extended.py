"""
Extended SQLAlchemy Models for Yacco Health EMR - All remaining collections
"""

from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, Time,
    Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from .models import Base, utc_now, generate_uuid


# ============== APPOINTMENTS & SCHEDULING ==============

class Appointment(Base):
    """Patient appointments"""
    __tablename__ = 'appointments'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    provider_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    appointment_type: Mapped[Optional[str]] = mapped_column(String(100))
    date: Mapped[Optional[str]] = mapped_column(String(20))
    start_time: Mapped[Optional[str]] = mapped_column(String(10))
    end_time: Mapped[Optional[str]] = mapped_column(String(10))
    
    reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(50), default='scheduled')
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_appointments_patient', 'patient_id'),
        Index('ix_appointments_provider', 'provider_id'),
        Index('ix_appointments_date', 'date'),
    )


# ============== FINANCE & BILLING ==============

class BankAccount(Base):
    """Bank accounts for organizations"""
    __tablename__ = 'bank_accounts'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    bank_name: Mapped[Optional[str]] = mapped_column(String(255))
    account_name: Mapped[Optional[str]] = mapped_column(String(255))
    account_number: Mapped[Optional[str]] = mapped_column(String(50))
    branch: Mapped[Optional[str]] = mapped_column(String(255))
    swift_code: Mapped[Optional[str]] = mapped_column(String(50))
    account_type: Mapped[Optional[str]] = mapped_column(String(50))
    currency: Mapped[Optional[str]] = mapped_column(String(10), default='GHS')
    
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_bank_accounts_org', 'organization_id'),
    )


class MobileMoneyAccount(Base):
    """Mobile money accounts"""
    __tablename__ = 'mobile_money_accounts'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    account_name: Mapped[Optional[str]] = mapped_column(String(255))
    merchant_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_mobile_money_org', 'organization_id'),
    )


class Invoice(Base):
    """Patient invoices"""
    __tablename__ = 'invoices'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    encounter_id: Mapped[Optional[str]] = mapped_column(String(50))
    insurance_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    line_items: Mapped[Optional[list]] = mapped_column(JSONB)
    payments: Mapped[Optional[list]] = mapped_column(JSONB)
    
    subtotal: Mapped[Optional[float]] = mapped_column(Float, default=0)
    discount: Mapped[Optional[float]] = mapped_column(Float, default=0)
    tax: Mapped[Optional[float]] = mapped_column(Float, default=0)
    total: Mapped[Optional[float]] = mapped_column(Float, default=0)
    amount_paid: Mapped[Optional[float]] = mapped_column(Float, default=0)
    balance_due: Mapped[Optional[float]] = mapped_column(Float, default=0)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_invoices_patient', 'patient_id'),
        Index('ix_invoices_org', 'organization_id'),
        Index('ix_invoices_status', 'status'),
    )


class Payment(Base):
    """Payment records"""
    __tablename__ = 'payments'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    invoice_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    amount: Mapped[Optional[float]] = mapped_column(Float)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    recorded_by: Mapped[Optional[str]] = mapped_column(String(50))
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_payments_invoice', 'invoice_id'),
    )


class PaystackTransaction(Base):
    """Paystack payment transactions"""
    __tablename__ = 'paystack_transactions'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    authorization_url: Mapped[Optional[str]] = mapped_column(Text)
    access_code: Mapped[Optional[str]] = mapped_column(String(255))
    
    amount: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(10), default='GHS')
    email: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50))
    channel: Mapped[Optional[str]] = mapped_column(String(50))
    
    transaction_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_paystack_ref', 'reference'),
        Index('ix_paystack_org', 'organization_id'),
    )


class BillingPayment(Base):
    """Billing payments (cashier module)"""
    __tablename__ = 'billing_payments'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    shift_id: Mapped[Optional[str]] = mapped_column(String(50))
    invoice_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    amount: Mapped[Optional[float]] = mapped_column(Float)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    
    cashier_id: Mapped[Optional[str]] = mapped_column(String(50))
    cashier_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class BillingShift(Base):
    """Cashier billing shifts"""
    __tablename__ = 'billing_shifts'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    cashier_id: Mapped[Optional[str]] = mapped_column(String(50))
    cashier_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    opening_balance: Mapped[Optional[float]] = mapped_column(Float, default=0)
    closing_balance: Mapped[Optional[float]] = mapped_column(Float)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='open')
    
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)


class BillingAuditLog(Base):
    """Billing-specific audit logs"""
    __tablename__ = 'billing_audit_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    action: Mapped[Optional[str]] = mapped_column(String(100))
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


# ============== WARD & BED MANAGEMENT ==============

class Ward(Base):
    """Hospital wards"""
    __tablename__ = 'wards'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    name: Mapped[Optional[str]] = mapped_column(String(255))
    ward_type: Mapped[Optional[str]] = mapped_column(String(50))
    floor: Mapped[Optional[str]] = mapped_column(String(50))
    building: Mapped[Optional[str]] = mapped_column(String(100))
    department_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    gender_restriction: Mapped[Optional[str]] = mapped_column(String(20), default='any')
    total_beds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    available_beds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    occupied_beds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    nurse_station: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    hospital_prefix: Mapped[Optional[str]] = mapped_column(String(20))
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    is_auto_generated: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_wards_org', 'organization_id'),
    )


class Room(Base):
    """Hospital rooms"""
    __tablename__ = 'rooms'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    ward_id: Mapped[Optional[str]] = mapped_column(String(50))
    ward_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    room_number: Mapped[Optional[str]] = mapped_column(String(50))
    room_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    total_beds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    available_beds: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    has_bathroom: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_oxygen: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_suction: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_rooms_ward', 'ward_id'),
    )


class Bed(Base):
    """Hospital beds"""
    __tablename__ = 'beds'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    ward_id: Mapped[Optional[str]] = mapped_column(String(50))
    ward_name: Mapped[Optional[str]] = mapped_column(String(255))
    room_id: Mapped[Optional[str]] = mapped_column(String(50))
    room_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    bed_number: Mapped[Optional[str]] = mapped_column(String(50))
    bed_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    has_monitor: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_ventilator: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='available')
    current_patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    current_admission_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_beds_ward', 'ward_id'),
        Index('ix_beds_room', 'room_id'),
    )


class Admission(Base):
    """Patient admissions"""
    __tablename__ = 'admissions'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    
    ward_id: Mapped[Optional[str]] = mapped_column(String(50))
    ward_name: Mapped[Optional[str]] = mapped_column(String(255))
    room_id: Mapped[Optional[str]] = mapped_column(String(50))
    bed_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    admission_type: Mapped[Optional[str]] = mapped_column(String(50))
    admitting_diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text)
    
    attending_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    attending_physician_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='admitted')
    
    admitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    discharged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    discharge_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    
    __table_args__ = (
        Index('ix_admissions_patient', 'patient_id'),
        Index('ix_admissions_org', 'organization_id'),
    )


# ============== AMBULANCE SERVICES ==============

class AmbulanceVehicle(Base):
    """Ambulance vehicles"""
    __tablename__ = 'ambulance_vehicles'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(50))
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50))
    equipment_level: Mapped[Optional[str]] = mapped_column(String(50))
    make_model: Mapped[Optional[str]] = mapped_column(String(100))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, default=2)
    
    has_oxygen: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_defibrillator: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_ventilator: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_stretcher: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='available')
    current_trip_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    total_trips: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_mileage: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_ambulance_vehicles_org', 'organization_id'),
    )


class AmbulanceRequest(Base):
    """Ambulance service requests"""
    __tablename__ = 'ambulance_requests'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    request_number: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    
    pickup_location: Mapped[Optional[str]] = mapped_column(Text)
    destination_facility: Mapped[Optional[str]] = mapped_column(String(255))
    destination_address: Mapped[Optional[str]] = mapped_column(Text)
    
    referral_reason: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    trip_type: Mapped[Optional[str]] = mapped_column(String(50))
    priority_level: Mapped[Optional[str]] = mapped_column(String(50))
    special_requirements: Mapped[Optional[str]] = mapped_column(Text)
    physician_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    requesting_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    requesting_physician: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    
    vehicle_id: Mapped[Optional[str]] = mapped_column(String(50))
    driver_id: Mapped[Optional[str]] = mapped_column(String(50))
    paramedic_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    
    __table_args__ = (
        Index('ix_ambulance_requests_org', 'organization_id'),
        Index('ix_ambulance_requests_status', 'status'),
    )


# ============== RADIOLOGY ==============

class RadiologyOrder(Base):
    """Radiology orders"""
    __tablename__ = 'radiology_orders'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    accession_number: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    patient_dob: Mapped[Optional[str]] = mapped_column(String(20))
    
    modality: Mapped[Optional[str]] = mapped_column(String(50))
    study_type: Mapped[Optional[str]] = mapped_column(String(255))
    body_part: Mapped[Optional[str]] = mapped_column(String(100))
    laterality: Mapped[Optional[str]] = mapped_column(String(50))
    
    clinical_indication: Mapped[Optional[str]] = mapped_column(Text)
    relevant_history: Mapped[Optional[str]] = mapped_column(Text)
    
    priority: Mapped[Optional[str]] = mapped_column(String(50), default='routine')
    contrast_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    
    scheduled_date: Mapped[Optional[str]] = mapped_column(String(20))
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10))
    room: Mapped[Optional[str]] = mapped_column(String(50))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='ordered')
    
    ordering_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    ordering_physician: Mapped[Optional[str]] = mapped_column(String(255))
    
    technologist_notes: Mapped[Optional[str]] = mapped_column(Text)
    performed_by: Mapped[Optional[str]] = mapped_column(String(50))
    performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    result_id: Mapped[Optional[str]] = mapped_column(String(50))
    report_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_radiology_orders_patient', 'patient_id'),
        Index('ix_radiology_orders_org', 'organization_id'),
    )


class RadiologyReport(Base):
    """Radiology reports"""
    __tablename__ = 'radiology_reports'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    order_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    findings: Mapped[Optional[str]] = mapped_column(Text)
    impression: Mapped[Optional[str]] = mapped_column(Text)
    recommendations: Mapped[Optional[str]] = mapped_column(Text)
    
    critical_finding: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    critical_finding_communicated: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    radiologist_id: Mapped[Optional[str]] = mapped_column(String(50))
    radiologist_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='draft')
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_radiology_reports_order', 'order_id'),
    )


class RadiologyNote(Base):
    """Radiology notes"""
    __tablename__ = 'radiology_notes'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    order_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    note_type: Mapped[Optional[str]] = mapped_column(String(50))
    content: Mapped[Optional[str]] = mapped_column(Text)
    
    author_id: Mapped[Optional[str]] = mapped_column(String(50))
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


# ============== IR (INTERVENTIONAL RADIOLOGY) ==============

class IRProcedure(Base):
    """Interventional radiology procedures"""
    __tablename__ = 'ir_procedures'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    case_number: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    
    procedure_type: Mapped[Optional[str]] = mapped_column(String(100))
    procedure_description: Mapped[Optional[str]] = mapped_column(Text)
    indication: Mapped[Optional[str]] = mapped_column(Text)
    laterality: Mapped[Optional[str]] = mapped_column(String(50))
    
    scheduled_date: Mapped[Optional[str]] = mapped_column(String(20))
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10))
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    
    sedation_required: Mapped[Optional[str]] = mapped_column(String(50))
    contrast_required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    special_equipment: Mapped[Optional[list]] = mapped_column(JSONB)
    
    attending_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    attending_physician_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(50), default='scheduled')
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_by_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_ir_procedures_patient', 'patient_id'),
        Index('ix_ir_procedures_org', 'organization_id'),
    )


class IRPreAssessment(Base):
    """IR pre-procedure assessments"""
    __tablename__ = 'ir_pre_assessments'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    procedure_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    allergies: Mapped[Optional[list]] = mapped_column(JSONB)
    medications: Mapped[Optional[list]] = mapped_column(JSONB)
    vital_signs: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    consent_obtained: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    consent_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    assessed_by: Mapped[Optional[str]] = mapped_column(String(50))
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)


class IRSedationMonitoring(Base):
    """IR sedation monitoring records"""
    __tablename__ = 'ir_sedation_monitoring'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    procedure_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    vitals: Mapped[Optional[list]] = mapped_column(JSONB)
    medications_administered: Mapped[Optional[list]] = mapped_column(JSONB)
    
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    monitored_by: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


# ============== LABORATORY ==============

class LabOrder(Base):
    """Laboratory orders"""
    __tablename__ = 'lab_orders'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    order_number: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_mrn: Mapped[Optional[str]] = mapped_column(String(50))
    
    tests: Mapped[Optional[list]] = mapped_column(JSONB)
    
    priority: Mapped[Optional[str]] = mapped_column(String(50), default='routine')
    clinical_indication: Mapped[Optional[str]] = mapped_column(Text)
    
    ordering_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    ordering_physician: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='ordered')
    
    specimen_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    specimen_type: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_lab_orders_patient', 'patient_id'),
        Index('ix_lab_orders_org', 'organization_id'),
    )


class LabResult(Base):
    """Laboratory results"""
    __tablename__ = 'lab_results'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    order_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    results: Mapped[Optional[list]] = mapped_column(JSONB)
    
    abnormal_flags: Mapped[Optional[list]] = mapped_column(JSONB)
    critical_values: Mapped[Optional[list]] = mapped_column(JSONB)
    
    technologist_id: Mapped[Optional[str]] = mapped_column(String(50))
    technologist_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    verified_by_id: Mapped[Optional[str]] = mapped_column(String(50))
    verified_by_name: Mapped[Optional[str]] = mapped_column(String(255))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


# ============== CLINICAL NOTES ==============

class ClinicalNote(Base):
    """Clinical notes"""
    __tablename__ = 'clinical_notes'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    encounter_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    note_type: Mapped[Optional[str]] = mapped_column(String(50))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    
    author_id: Mapped[Optional[str]] = mapped_column(String(50))
    author_name: Mapped[Optional[str]] = mapped_column(String(255))
    author_role: Mapped[Optional[str]] = mapped_column(String(50))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='draft')
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_clinical_notes_patient', 'patient_id'),
    )


class Problem(Base):
    """Patient problems/diagnoses"""
    __tablename__ = 'problems'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    problem_name: Mapped[Optional[str]] = mapped_column(String(255))
    icd_code: Mapped[Optional[str]] = mapped_column(String(20))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active')
    severity: Mapped[Optional[str]] = mapped_column(String(50))
    
    onset_date: Mapped[Optional[Date]] = mapped_column(Date)
    resolved_date: Mapped[Optional[Date]] = mapped_column(Date)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    recorded_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_problems_patient', 'patient_id'),
    )


class Medication(Base):
    """Current medications"""
    __tablename__ = 'medications'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    medication_name: Mapped[Optional[str]] = mapped_column(String(255))
    generic_name: Mapped[Optional[str]] = mapped_column(String(255))
    brand_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    dosage: Mapped[Optional[str]] = mapped_column(String(100))
    frequency: Mapped[Optional[str]] = mapped_column(String(100))
    route: Mapped[Optional[str]] = mapped_column(String(50))
    
    start_date: Mapped[Optional[Date]] = mapped_column(Date)
    end_date: Mapped[Optional[Date]] = mapped_column(Date)
    
    prescriber_id: Mapped[Optional[str]] = mapped_column(String(50))
    prescriber_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='active')
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_medications_patient', 'patient_id'),
    )


# ============== PHARMACY ==============

class PharmacyDrug(Base):
    """Pharmacy drug inventory"""
    __tablename__ = 'pharmacy_drugs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    pharmacy_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    generic_name: Mapped[Optional[str]] = mapped_column(String(255))
    brand_name: Mapped[Optional[str]] = mapped_column(String(255))
    brand_names: Mapped[Optional[list]] = mapped_column(JSONB)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255))
    
    strength: Mapped[Optional[str]] = mapped_column(String(100))
    all_strengths: Mapped[Optional[list]] = mapped_column(JSONB)
    dosage_form: Mapped[Optional[str]] = mapped_column(String(100))
    all_dosage_forms: Mapped[Optional[list]] = mapped_column(JSONB)
    
    category: Mapped[Optional[str]] = mapped_column(String(50))
    therapeutic_category: Mapped[Optional[str]] = mapped_column(String(100))
    
    unit_price: Mapped[Optional[float]] = mapped_column(Float, default=0)
    pack_size: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    reorder_level: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    current_stock: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_pharmacy_drugs_pharmacy', 'pharmacy_id'),
    )


class PharmacyPrescription(Base):
    """Pharmacy prescriptions (received from EMR)"""
    __tablename__ = 'pharmacy_prescriptions'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    pharmacy_id: Mapped[Optional[str]] = mapped_column(String(50))
    rx_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    medications: Mapped[Optional[list]] = mapped_column(JSONB)
    
    prescriber_name: Mapped[Optional[str]] = mapped_column(String(255))
    prescriber_license: Mapped[Optional[str]] = mapped_column(String(100))
    source_hospital: Mapped[Optional[str]] = mapped_column(String(255))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='received')
    
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    dispensed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    dispensed_by: Mapped[Optional[str]] = mapped_column(String(50))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (
        Index('ix_pharmacy_prescriptions_pharmacy', 'pharmacy_id'),
    )


class PharmacyActivityLog(Base):
    """Pharmacy activity logs"""
    __tablename__ = 'pharmacy_activity_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    pharmacy_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    activity_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class PharmacyAuditLog(Base):
    """Pharmacy audit logs"""
    __tablename__ = 'pharmacy_audit_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    pharmacy_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    action: Mapped[Optional[str]] = mapped_column(String(100))
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(100))
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class PrescriptionRouting(Base):
    """Prescription routing records"""
    __tablename__ = 'prescription_routings'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    prescription_id: Mapped[Optional[str]] = mapped_column(String(50))
    pharmacy_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='sent')
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_prescription_routings_rx', 'prescription_id'),
    )


# ============== INVENTORY ==============

class InventoryItem(Base):
    """Inventory items (general supplies)"""
    __tablename__ = 'inventory_items'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    name: Mapped[Optional[str]] = mapped_column(String(255))
    sku: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    
    unit_price: Mapped[Optional[float]] = mapped_column(Float, default=0)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    reorder_level: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    
    supplier_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_inventory_items_org', 'organization_id'),
    )


class InventoryBatch(Base):
    """Inventory batches"""
    __tablename__ = 'inventory_batches'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    item_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    batch_number: Mapped[Optional[str]] = mapped_column(String(100))
    quantity: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    expiry_date: Mapped[Optional[Date]] = mapped_column(Date)
    
    received_date: Mapped[Optional[Date]] = mapped_column(Date)
    supplier_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class StockMovement(Base):
    """Stock movements"""
    __tablename__ = 'stock_movements'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    item_id: Mapped[Optional[str]] = mapped_column(String(50))
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    movement_type: Mapped[Optional[str]] = mapped_column(String(50))
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    
    reference_type: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    performed_by: Mapped[Optional[str]] = mapped_column(String(50))
    performed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class Supplier(Base):
    """Suppliers"""
    __tablename__ = 'suppliers'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    name: Mapped[Optional[str]] = mapped_column(String(255))
    contact_person: Mapped[Optional[str]] = mapped_column(String(255))
    
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    __table_args__ = (
        Index('ix_suppliers_org', 'organization_id'),
    )


# ============== NURSING ==============

class NurseShift(Base):
    """Nurse shifts"""
    __tablename__ = 'nurse_shifts'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    nurse_id: Mapped[Optional[str]] = mapped_column(String(50))
    nurse_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    ward_id: Mapped[Optional[str]] = mapped_column(String(50))
    ward_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    shift_type: Mapped[Optional[str]] = mapped_column(String(50))
    date: Mapped[Optional[Date]] = mapped_column(Date)
    
    start_time: Mapped[Optional[str]] = mapped_column(String(10))
    end_time: Mapped[Optional[str]] = mapped_column(String(10))
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='scheduled')
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class NurseAssignment(Base):
    """Nurse patient assignments"""
    __tablename__ = 'nurse_assignments'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    nurse_id: Mapped[Optional[str]] = mapped_column(String(50))
    nurse_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    shift_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    assigned_by: Mapped[Optional[str]] = mapped_column(String(50))


# ============== NOTIFICATIONS & COMMUNICATIONS ==============

class Notification(Base):
    """System notifications"""
    __tablename__ = 'notifications'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    type: Mapped[Optional[str]] = mapped_column(String(50))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    priority: Mapped[Optional[str]] = mapped_column(String(20), default='normal')
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_notifications_user', 'user_id'),
    )


class SMSLog(Base):
    """SMS log records"""
    __tablename__ = 'sms_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    phone_number: Mapped[Optional[str]] = mapped_column(String(50))
    message: Mapped[Optional[str]] = mapped_column(Text)
    notification_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    success: Mapped[Optional[bool]] = mapped_column(Boolean)
    error: Mapped[Optional[str]] = mapped_column(Text)
    
    provider_response: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class VoiceDictationLog(Base):
    """Voice dictation logs"""
    __tablename__ = 'voice_dictation_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    audio_duration: Mapped[Optional[float]] = mapped_column(Float)
    transcription: Mapped[Optional[str]] = mapped_column(Text)
    
    context_type: Mapped[Optional[str]] = mapped_column(String(50))
    context_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    success: Mapped[Optional[bool]] = mapped_column(Boolean)
    error: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


# ============== SECURITY & ACCESS ==============

class AccessGrant(Base):
    """Record access grants"""
    __tablename__ = 'access_grants'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    request_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    granting_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    granting_organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    granted_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    granted_organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    records_types: Mapped[Optional[list]] = mapped_column(JSONB)
    
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    __table_args__ = (
        Index('ix_access_grants_patient', 'patient_id'),
    )


class RecordsRequest(Base):
    """Medical records requests"""
    __tablename__ = 'records_requests'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    requesting_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    requesting_physician_name: Mapped[Optional[str]] = mapped_column(String(255))
    requesting_organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    target_organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    target_physician_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    records_types: Mapped[Optional[list]] = mapped_column(JSONB)
    purpose: Mapped[Optional[str]] = mapped_column(Text)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    
    requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_records_requests_patient', 'patient_id'),
    )


class User2FA(Base):
    """User 2FA settings"""
    __tablename__ = 'user_2fa'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    method: Mapped[Optional[str]] = mapped_column(String(50))
    secret: Mapped[Optional[str]] = mapped_column(String(255))
    
    is_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    
    backup_codes: Mapped[Optional[list]] = mapped_column(JSONB)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_user_2fa_user', 'user_id'),
    )


class ITAuditLog(Base):
    """IT-specific audit logs"""
    __tablename__ = 'it_audit_logs'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    action: Mapped[Optional[str]] = mapped_column(String(100))
    category: Mapped[Optional[str]] = mapped_column(String(50))
    
    user_id: Mapped[Optional[str]] = mapped_column(String(50))
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    
    target_type: Mapped[Optional[str]] = mapped_column(String(100))
    target_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(100))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


# ============== HL7 & INTEGRATION ==============

class HL7Message(Base):
    """HL7 messages"""
    __tablename__ = 'hl7_messages'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    message_type: Mapped[Optional[str]] = mapped_column(String(50))
    trigger_event: Mapped[Optional[str]] = mapped_column(String(50))
    
    message_control_id: Mapped[Optional[str]] = mapped_column(String(100))
    raw_message: Mapped[Optional[str]] = mapped_column(Text)
    
    direction: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[Optional[str]] = mapped_column(String(50))
    
    source_system: Mapped[Optional[str]] = mapped_column(String(100))
    destination_system: Mapped[Optional[str]] = mapped_column(String(100))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class HospitalLocation(Base):
    """Hospital locations"""
    __tablename__ = 'hospital_locations'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    name: Mapped[Optional[str]] = mapped_column(String(255))
    location_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    building: Mapped[Optional[str]] = mapped_column(String(100))
    floor: Mapped[Optional[str]] = mapped_column(String(50))
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)


class Order(Base):
    """General orders"""
    __tablename__ = 'orders'
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=generate_uuid)
    organization_id: Mapped[Optional[str]] = mapped_column(String(50))
    
    order_number: Mapped[Optional[str]] = mapped_column(String(50))
    order_type: Mapped[Optional[str]] = mapped_column(String(50))
    
    patient_id: Mapped[Optional[str]] = mapped_column(String(50))
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    items: Mapped[Optional[list]] = mapped_column(JSONB)
    
    status: Mapped[Optional[str]] = mapped_column(String(50), default='pending')
    priority: Mapped[Optional[str]] = mapped_column(String(50), default='routine')
    
    ordering_provider_id: Mapped[Optional[str]] = mapped_column(String(50))
    ordering_provider_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('ix_orders_patient', 'patient_id'),
    )
