"""
PostgreSQL Repository Pattern for Yacco Health EMR
Provides async CRUD operations using SQLAlchemy
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
import uuid
import logging

from .connection import get_db, async_session_factory

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """Generic repository for CRUD operations"""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get a record by ID"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).limit(limit).offset(offset)
            )
            return list(result.scalars().all())
    
    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get a single record by field value"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(getattr(self.model, field) == value)
            )
            return result.scalar_one_or_none()
    
    async def get_many_by_field(self, field: str, value: Any, limit: int = 100) -> List[T]:
        """Get multiple records by field value"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model)
                .where(getattr(self.model, field) == value)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new record"""
        async with async_session_factory() as session:
            # Generate ID if not provided
            if 'id' not in data:
                data['id'] = str(uuid.uuid4())
            
            # Add timestamps if not provided
            now = datetime.now(timezone.utc)
            if hasattr(self.model, 'created_at') and 'created_at' not in data:
                data['created_at'] = now
            if hasattr(self.model, 'updated_at') and 'updated_at' not in data:
                data['updated_at'] = now
            
            record = self.model(**data)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update a record by ID"""
        async with async_session_factory() as session:
            # Add updated_at timestamp
            if hasattr(self.model, 'updated_at'):
                data['updated_at'] = datetime.now(timezone.utc)
            
            await session.execute(
                update(self.model)
                .where(self.model.id == id)
                .values(**data)
            )
            await session.commit()
            
            # Fetch and return updated record
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
    
    async def delete(self, id: str) -> bool:
        """Delete a record by ID"""
        async with async_session_factory() as session:
            result = await session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        async with async_session_factory() as session:
            query = select(func.count()).select_from(self.model)
            
            if filters:
                conditions = [
                    getattr(self.model, k) == v for k, v in filters.items()
                    if hasattr(self.model, k)
                ]
                if conditions:
                    query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar() or 0
    
    async def find(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """Find records with filters and ordering"""
        async with async_session_factory() as session:
            query = select(self.model)
            
            if filters:
                conditions = [
                    getattr(self.model, k) == v for k, v in filters.items()
                    if hasattr(self.model, k) and v is not None
                ]
                if conditions:
                    query = query.where(and_(*conditions))
            
            if order_by and hasattr(self.model, order_by):
                col = getattr(self.model, order_by)
                query = query.order_by(col.desc() if order_desc else col.asc())
            
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def exists(self, field: str, value: Any) -> bool:
        """Check if a record exists with given field value"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(func.count())
                .select_from(self.model)
                .where(getattr(self.model, field) == value)
            )
            return (result.scalar() or 0) > 0


def to_dict(obj: Any) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    if obj is None:
        return None
    
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        
        # Convert datetime to ISO string
        if isinstance(value, datetime):
            value = value.isoformat()
        
        result[column.name] = value
    
    return result


def to_dict_list(objects: List[Any]) -> List[Dict[str, Any]]:
    """Convert list of SQLAlchemy models to list of dictionaries"""
    return [to_dict(obj) for obj in objects if obj is not None]


# ============ Specialized Repositories ============

from .models import (
    Organization, Hospital, User, Patient, Region,
    Prescription, Pharmacy, PharmacyStaff, Department,
    AuditLog, Vital, Allergy
)
from .models_extended import (
    Appointment, Invoice, Payment, Ward, Room, Bed,
    RadiologyOrder, RadiologyReport, IRProcedure,
    Notification, SMSLog, LabOrder, LabResult,
    AmbulanceVehicle, AmbulanceRequest, PharmacyDrug
)


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self):
        super().__init__(Organization)
    
    async def get_by_email(self, email: str) -> Optional[Organization]:
        return await self.get_by_field('email', email)
    
    async def get_pending(self) -> List[Organization]:
        return await self.get_many_by_field('status', 'pending')
    
    async def get_approved(self) -> List[Organization]:
        return await self.get_many_by_field('status', 'approved')


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.get_by_field('email', email)
    
    async def get_by_organization(self, org_id: str) -> List[User]:
        return await self.get_many_by_field('organization_id', org_id)
    
    async def get_active_users(self, org_id: str) -> List[User]:
        return await self.find(
            filters={'organization_id': org_id, 'is_active': True}
        )


class PatientRepository(BaseRepository[Patient]):
    def __init__(self):
        super().__init__(Patient)
    
    async def get_by_mrn(self, mrn: str) -> Optional[Patient]:
        return await self.get_by_field('mrn', mrn)
    
    async def get_by_organization(self, org_id: str) -> List[Patient]:
        return await self.get_many_by_field('organization_id', org_id)
    
    async def search(self, org_id: str, query: str) -> List[Patient]:
        """Search patients by name or MRN"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Patient)
                .where(
                    and_(
                        Patient.organization_id == org_id,
                        or_(
                            Patient.mrn.ilike(f'%{query}%'),
                            Patient.first_name.ilike(f'%{query}%'),
                            Patient.last_name.ilike(f'%{query}%')
                        )
                    )
                )
                .limit(50)
            )
            return list(result.scalars().all())


class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self):
        super().__init__(Prescription)
    
    async def get_by_patient(self, patient_id: str) -> List[Prescription]:
        return await self.find(
            filters={'patient_id': patient_id},
            order_by='created_at'
        )
    
    async def get_pending_by_org(self, org_id: str) -> List[Prescription]:
        return await self.find(
            filters={'organization_id': org_id, 'status': 'active'}
        )


class PharmacyRepository(BaseRepository[Pharmacy]):
    def __init__(self):
        super().__init__(Pharmacy)
    
    async def get_by_region(self, region: str) -> List[Pharmacy]:
        return await self.get_many_by_field('region', region)
    
    async def get_approved(self) -> List[Pharmacy]:
        return await self.get_many_by_field('status', 'approved')


class PharmacyDrugRepository(BaseRepository[PharmacyDrug]):
    def __init__(self):
        super().__init__(PharmacyDrug)
    
    async def get_by_pharmacy(self, pharmacy_id: str) -> List[PharmacyDrug]:
        return await self.get_many_by_field('pharmacy_id', pharmacy_id, limit=1000)
    
    async def search(self, pharmacy_id: str, query: str) -> List[PharmacyDrug]:
        """Search drugs by name"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(PharmacyDrug)
                .where(
                    and_(
                        PharmacyDrug.pharmacy_id == pharmacy_id,
                        or_(
                            PharmacyDrug.generic_name.ilike(f'%{query}%'),
                            PharmacyDrug.brand_name.ilike(f'%{query}%')
                        )
                    )
                )
                .limit(100)
            )
            return list(result.scalars().all())


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self):
        super().__init__(AuditLog)
    
    async def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        return await self.create({
            'action': action,
            'user_id': user_id,
            'user_email': user_email,
            'organization_id': organization_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details,
            'ip_address': ip_address,
            'timestamp': datetime.now(timezone.utc)
        })


# ============ Repository Instances ============

# Create singleton instances for easy import
organizations = OrganizationRepository()
users = UserRepository()
patients = PatientRepository()
prescriptions = PrescriptionRepository()
pharmacies = PharmacyRepository()
pharmacy_drugs = PharmacyDrugRepository()
audit_logs = AuditLogRepository()

# Generic repositories for other models
regions = BaseRepository(Region)
hospitals = BaseRepository(Hospital)
departments = BaseRepository(Department)
vitals = BaseRepository(Vital)
allergies = BaseRepository(Allergy)
wards = BaseRepository(Ward)
rooms = BaseRepository(Room)
beds = BaseRepository(Bed)
appointments = BaseRepository(Appointment)
invoices = BaseRepository(Invoice)
payments = BaseRepository(Payment)
radiology_orders = BaseRepository(RadiologyOrder)
radiology_reports = BaseRepository(RadiologyReport)
ir_procedures = BaseRepository(IRProcedure)
notifications = BaseRepository(Notification)
sms_logs = BaseRepository(SMSLog)
lab_orders = BaseRepository(LabOrder)
lab_results = BaseRepository(LabResult)
ambulance_vehicles = BaseRepository(AmbulanceVehicle)
ambulance_requests = BaseRepository(AmbulanceRequest)
pharmacy_staff = BaseRepository(PharmacyStaff)
