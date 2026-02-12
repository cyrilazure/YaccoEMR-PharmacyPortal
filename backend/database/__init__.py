"""
PostgreSQL Database Configuration for Yacco Health EMR
Enterprise-grade, scalable database layer with SQLAlchemy
"""

from .connection import (
    get_db,
    get_async_session,
    engine,
    async_session_factory,
    init_db,
    close_db,
    check_db_connection
)
from .models import Base

# Import all models for easy access
from .models import (
    Organization, Hospital, User, Patient, Region,
    Prescription, Pharmacy, PharmacyStaff, Department,
    AuditLog, Vital, Allergy, OTPSession, PatientMedicalHistory,
    PatientReferral, ChatConversation, ChatMessage, RateLimitRecord
)
from .models_extended import (
    Appointment, Invoice, Payment, Ward, Room, Bed,
    RadiologyOrder, RadiologyReport, IRProcedure,
    Notification, SMSLog, LabOrder, LabResult,
    AmbulanceVehicle, AmbulanceRequest, PharmacyDrug,
    BankAccount, MobileMoneyAccount, PaystackTransaction,
    InventoryItem, Supplier, AccessGrant, User2FA
)

# Import repository pattern
from .repository import (
    BaseRepository,
    to_dict,
    to_dict_list,
    organizations,
    users,
    patients,
    prescriptions,
    pharmacies,
    pharmacy_drugs,
    audit_logs,
    regions,
    hospitals,
    departments,
    vitals,
    allergies,
    wards,
    rooms,
    beds,
    appointments,
    invoices,
    payments,
    radiology_orders,
    radiology_reports,
    notifications,
    pharmacy_staff
)

__all__ = [
    # Connection
    'get_db',
    'get_async_session', 
    'engine',
    'async_session_factory',
    'init_db',
    'close_db',
    'check_db_connection',
    'Base',
    
    # Models
    'Organization', 'Hospital', 'User', 'Patient', 'Region',
    'Prescription', 'Pharmacy', 'PharmacyStaff', 'Department',
    'AuditLog', 'Vital', 'Allergy', 'Appointment', 'Invoice',
    'Payment', 'Ward', 'Room', 'Bed', 'RadiologyOrder',
    'Notification', 'SMSLog', 'LabOrder', 'LabResult',
    'AmbulanceVehicle', 'AmbulanceRequest', 'PharmacyDrug',
    
    # Repository
    'BaseRepository', 'to_dict', 'to_dict_list',
    'organizations', 'users', 'patients', 'prescriptions',
    'pharmacies', 'pharmacy_drugs', 'audit_logs',
    'regions', 'hospitals', 'departments', 'vitals', 'allergies',
    'wards', 'rooms', 'beds', 'appointments', 'invoices', 'payments',
    'radiology_orders', 'radiology_reports', 'notifications', 'pharmacy_staff'
]
