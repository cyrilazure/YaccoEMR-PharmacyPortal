"""
Database Service Layer for Yacco Health EMR
Provides a unified interface for both MongoDB and PostgreSQL
Allows gradual migration from MongoDB to PostgreSQL
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid
import logging
import json

# PostgreSQL imports
from database import (
    organizations as pg_organizations,
    users as pg_users,
    patients as pg_patients,
    prescriptions as pg_prescriptions,
    pharmacies as pg_pharmacies,
    pharmacy_drugs as pg_pharmacy_drugs,
    audit_logs as pg_audit_logs,
    regions as pg_regions,
    hospitals as pg_hospitals,
    departments as pg_departments,
    to_dict, to_dict_list
)

logger = logging.getLogger(__name__)

# Configuration: Set to True to use PostgreSQL, False for MongoDB
# Can be controlled via environment variable
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'


class DatabaseService:
    """
    Unified database service that can use either MongoDB or PostgreSQL.
    During migration, this allows gradual transition from MongoDB to PostgreSQL.
    """
    
    def __init__(self, mongo_db=None):
        """
        Initialize with optional MongoDB connection.
        If USE_POSTGRES is True, will prefer PostgreSQL for supported collections.
        """
        self.mongo_db = mongo_db
        self.use_postgres = USE_POSTGRES
        
        # Collections that are fully migrated to PostgreSQL
        self.pg_collections = {
            'organizations', 'users', 'patients', 'prescriptions',
            'pharmacies', 'pharmacy_drugs', 'regions', 'hospitals',
            'departments', 'audit_logs'
        }
    
    def _should_use_postgres(self, collection: str) -> bool:
        """Determine if PostgreSQL should be used for this collection"""
        return self.use_postgres and collection in self.pg_collections
    
    # ============ Organization Operations ============
    
    async def get_organization(self, org_id: str) -> Optional[Dict]:
        """Get organization by ID"""
        if self._should_use_postgres('organizations'):
            result = await pg_organizations.get_by_id(org_id)
            return to_dict(result) if result else None
        else:
            doc = await self.mongo_db["organizations"].find_one({"id": org_id})
            if doc:
                doc.pop('_id', None)
            return doc
    
    async def get_organization_by_email(self, email: str) -> Optional[Dict]:
        """Get organization by email"""
        if self._should_use_postgres('organizations'):
            result = await pg_organizations.get_by_email(email)
            return to_dict(result) if result else None
        else:
            doc = await self.mongo_db["organizations"].find_one({"email": email})
            if doc:
                doc.pop('_id', None)
            return doc
    
    async def list_organizations(
        self, 
        status: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict]:
        """List organizations with optional status filter"""
        if self._should_use_postgres('organizations'):
            filters = {'status': status} if status else None
            results = await pg_organizations.find(
                filters=filters,
                order_by='created_at',
                limit=limit
            )
            return to_dict_list(results)
        else:
            query = {"status": status} if status else {}
            docs = await self.mongo_db["organizations"].find(
                query, {"_id": 0}
            ).sort("created_at", -1).to_list(limit)
            return docs
    
    async def create_organization(self, data: Dict) -> Dict:
        """Create a new organization"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        if 'updated_at' not in data:
            data['updated_at'] = datetime.now(timezone.utc)
        
        if self._should_use_postgres('organizations'):
            result = await pg_organizations.create(data)
            return to_dict(result)
        else:
            # Convert datetime to ISO string for MongoDB
            mongo_data = {**data}
            if isinstance(mongo_data.get('created_at'), datetime):
                mongo_data['created_at'] = mongo_data['created_at'].isoformat()
            if isinstance(mongo_data.get('updated_at'), datetime):
                mongo_data['updated_at'] = mongo_data['updated_at'].isoformat()
            await self.mongo_db["organizations"].insert_one(mongo_data)
            mongo_data.pop('_id', None)
            return mongo_data
    
    async def update_organization(self, org_id: str, data: Dict) -> bool:
        """Update an organization"""
        data['updated_at'] = datetime.now(timezone.utc)
        
        if self._should_use_postgres('organizations'):
            result = await pg_organizations.update(org_id, data)
            return result is not None
        else:
            if isinstance(data.get('updated_at'), datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result = await self.mongo_db["organizations"].update_one(
                {"id": org_id}, {"$set": data}
            )
            return result.modified_count > 0
    
    async def count_organizations(self, status: Optional[str] = None) -> int:
        """Count organizations with optional status filter"""
        if self._should_use_postgres('organizations'):
            filters = {'status': status} if status else None
            return await pg_organizations.count(filters)
        else:
            query = {"status": status} if status else {}
            return await self.mongo_db["organizations"].count_documents(query)
    
    # ============ User Operations ============
    
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        if self._should_use_postgres('users'):
            result = await pg_users.get_by_id(user_id)
            return to_dict(result) if result else None
        else:
            doc = await self.mongo_db["users"].find_one({"id": user_id})
            if doc:
                doc.pop('_id', None)
            return doc
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        if self._should_use_postgres('users'):
            result = await pg_users.get_by_email(email)
            return to_dict(result) if result else None
        else:
            doc = await self.mongo_db["users"].find_one({"email": email})
            if doc:
                doc.pop('_id', None)
            return doc
    
    async def get_users_by_organization(self, org_id: str, limit: int = 100) -> List[Dict]:
        """Get all users for an organization"""
        if self._should_use_postgres('users'):
            results = await pg_users.get_by_organization(org_id)
            return to_dict_list(results)
        else:
            docs = await self.mongo_db["users"].find(
                {"organization_id": org_id}, {"_id": 0}
            ).to_list(limit)
            return docs
    
    async def create_user(self, data: Dict) -> Dict:
        """Create a new user"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        
        if self._should_use_postgres('users'):
            result = await pg_users.create(data)
            return to_dict(result)
        else:
            mongo_data = {**data}
            if isinstance(mongo_data.get('created_at'), datetime):
                mongo_data['created_at'] = mongo_data['created_at'].isoformat()
            await self.mongo_db["users"].insert_one(mongo_data)
            mongo_data.pop('_id', None)
            return mongo_data
    
    async def update_user(self, user_id: str, data: Dict) -> bool:
        """Update a user"""
        if self._should_use_postgres('users'):
            result = await pg_users.update(user_id, data)
            return result is not None
        else:
            if isinstance(data.get('updated_at'), datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result = await self.mongo_db["users"].update_one(
                {"id": user_id}, {"$set": data}
            )
            return result.modified_count > 0
    
    async def user_exists(self, email: str) -> bool:
        """Check if user exists by email"""
        if self._should_use_postgres('users'):
            return await pg_users.exists('email', email)
        else:
            count = await self.mongo_db["users"].count_documents({"email": email})
            return count > 0
    
    # ============ Patient Operations ============
    
    async def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient by ID"""
        if self._should_use_postgres('patients'):
            result = await pg_patients.get_by_id(patient_id)
            return to_dict(result) if result else None
        else:
            doc = await self.mongo_db["patients"].find_one({"id": patient_id})
            if doc:
                doc.pop('_id', None)
            return doc
    
    async def get_patient_by_mrn(self, mrn: str) -> Optional[Dict]:
        """Get patient by MRN"""
        if self._should_use_postgres('patients'):
            result = await pg_patients.get_by_mrn(mrn)
            return to_dict(result) if result else None
        else:
            doc = await self.mongo_db["patients"].find_one({"mrn": mrn})
            if doc:
                doc.pop('_id', None)
            return doc
    
    async def get_patients_by_organization(self, org_id: str, limit: int = 100) -> List[Dict]:
        """Get all patients for an organization"""
        if self._should_use_postgres('patients'):
            results = await pg_patients.get_by_organization(org_id)
            return to_dict_list(results)
        else:
            docs = await self.mongo_db["patients"].find(
                {"organization_id": org_id}, {"_id": 0}
            ).to_list(limit)
            return docs
    
    async def create_patient(self, data: Dict) -> Dict:
        """Create a new patient"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.now(timezone.utc)
        
        if self._should_use_postgres('patients'):
            result = await pg_patients.create(data)
            return to_dict(result)
        else:
            mongo_data = {**data}
            if isinstance(mongo_data.get('created_at'), datetime):
                mongo_data['created_at'] = mongo_data['created_at'].isoformat()
            await self.mongo_db["patients"].insert_one(mongo_data)
            mongo_data.pop('_id', None)
            return mongo_data
    
    async def update_patient(self, patient_id: str, data: Dict) -> bool:
        """Update a patient"""
        data['updated_at'] = datetime.now(timezone.utc)
        
        if self._should_use_postgres('patients'):
            result = await pg_patients.update(patient_id, data)
            return result is not None
        else:
            if isinstance(data.get('updated_at'), datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            result = await self.mongo_db["patients"].update_one(
                {"id": patient_id}, {"$set": data}
            )
            return result.modified_count > 0
    
    async def search_patients(self, org_id: str, query: str) -> List[Dict]:
        """Search patients by name or MRN"""
        if self._should_use_postgres('patients'):
            results = await pg_patients.search(org_id, query)
            return to_dict_list(results)
        else:
            docs = await self.mongo_db["patients"].find({
                "organization_id": org_id,
                "$or": [
                    {"mrn": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}}
                ]
            }, {"_id": 0}).to_list(50)
            return docs
    
    # ============ Audit Log Operations ============
    
    async def log_audit(
        self,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ):
        """Create an audit log entry"""
        data = {
            'id': str(uuid.uuid4()),
            'action': action,
            'user_id': user_id,
            'user_email': user_email,
            'organization_id': organization_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'timestamp': datetime.now(timezone.utc)
        }
        
        if details:
            data['details'] = details if self._should_use_postgres('audit_logs') else json.dumps(details)
        
        if self._should_use_postgres('audit_logs'):
            await pg_audit_logs.create(data)
        else:
            data['timestamp'] = data['timestamp'].isoformat()
            await self.mongo_db["audit_logs"].insert_one(data)
    
    # ============ Generic Operations ============
    
    async def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        """Generic find one document"""
        doc = await self.mongo_db[collection].find_one(query)
        if doc:
            doc.pop('_id', None)
        return doc
    
    async def find_many(self, collection: str, query: Dict, limit: int = 100) -> List[Dict]:
        """Generic find multiple documents"""
        docs = await self.mongo_db[collection].find(query, {"_id": 0}).to_list(limit)
        return docs
    
    async def insert_one(self, collection: str, data: Dict) -> Dict:
        """Generic insert one document"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        await self.mongo_db[collection].insert_one(data)
        data.pop('_id', None)
        return data
    
    async def update_one(self, collection: str, query: Dict, update: Dict) -> bool:
        """Generic update one document"""
        result = await self.mongo_db[collection].update_one(query, {"$set": update})
        return result.modified_count > 0
    
    async def delete_one(self, collection: str, query: Dict) -> bool:
        """Generic delete one document"""
        result = await self.mongo_db[collection].delete_one(query)
        return result.deleted_count > 0
    
    async def count_documents(self, collection: str, query: Dict = None) -> int:
        """Generic count documents"""
        return await self.mongo_db[collection].count_documents(query or {})


# Global instance (will be initialized with MongoDB connection in server.py)
db_service: Optional[DatabaseService] = None


def init_db_service(mongo_db):
    """Initialize the database service with MongoDB connection"""
    global db_service
    db_service = DatabaseService(mongo_db)
    return db_service


def get_db_service() -> DatabaseService:
    """Get the database service instance"""
    if db_service is None:
        raise RuntimeError("Database service not initialized. Call init_db_service first.")
    return db_service
