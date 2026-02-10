"""
Database Service Layer V2 for Yacco Health EMR
===============================================
Provides a unified, simple interface for database operations.
Works with MongoDB now, designed for easy PostgreSQL migration later.

Usage:
    from db_service_v2 import get_db_service
    db = get_db_service()
    
    # Find documents
    docs = await db.find("users", {"role": "physician"}, limit=50)
    doc = await db.find_one("patients", {"id": patient_id})
    
    # Insert/Update
    await db.insert("audit_logs", {"action": "login", ...})
    await db.update("users", {"id": user_id}, {"last_login": datetime.now()})
    
    # Count
    count = await db.count("notifications", {"read": False})
"""

import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

# Configuration
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'false').lower() == 'true'


class DatabaseServiceV2:
    """
    Simplified database service with consistent interface.
    All operations return plain Python dicts (no ObjectId, no _id).
    """
    
    def __init__(self, mongo_db=None):
        self.mongo_db = mongo_db
        self.use_postgres = USE_POSTGRES
        logger.info(f"DatabaseServiceV2 initialized. PostgreSQL mode: {self.use_postgres}")
    
    # ==================== Core Operations ====================
    
    async def find_one(
        self, 
        collection: str, 
        query: Dict,
        projection: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Find a single document by query.
        Always excludes _id from results.
        """
        if projection is None:
            projection = {"_id": 0}
        elif "_id" not in projection:
            projection["_id"] = 0
            
        doc = await self.mongo_db[collection].find_one(query, projection)
        if doc:
            doc.pop('_id', None)
        return doc
    
    async def find(
        self,
        collection: str,
        query: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        sort: Optional[List[tuple]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """
        Find multiple documents with optional sorting and pagination.
        """
        if query is None:
            query = {}
        if projection is None:
            projection = {"_id": 0}
        elif "_id" not in projection:
            projection["_id"] = 0
        
        cursor = self.mongo_db[collection].find(query, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip > 0:
            cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        
        docs = await cursor.to_list(limit)
        for doc in docs:
            doc.pop('_id', None)
        return docs
    
    async def insert(
        self,
        collection: str,
        document: Dict,
        generate_id: bool = True
    ) -> Dict:
        """
        Insert a single document.
        Automatically generates 'id' field if not present.
        Returns the inserted document (without _id).
        """
        if generate_id and 'id' not in document:
            document['id'] = str(uuid.uuid4())
        
        await self.mongo_db[collection].insert_one(document)
        document.pop('_id', None)
        return document
    
    async def insert_many(
        self,
        collection: str,
        documents: List[Dict],
        generate_ids: bool = True
    ) -> List[Dict]:
        """Insert multiple documents."""
        if generate_ids:
            for doc in documents:
                if 'id' not in doc:
                    doc['id'] = str(uuid.uuid4())
        
        await self.mongo_db[collection].insert_many(documents)
        for doc in documents:
            doc.pop('_id', None)
        return documents
    
    async def update(
        self,
        collection: str,
        query: Dict,
        update_data: Dict,
        upsert: bool = False
    ) -> bool:
        """
        Update a single document.
        Returns True if document was modified.
        """
        result = await self.mongo_db[collection].update_one(
            query, 
            {"$set": update_data},
            upsert=upsert
        )
        return result.modified_count > 0 or (upsert and result.upserted_id is not None)
    
    async def update_many(
        self,
        collection: str,
        query: Dict,
        update_data: Dict
    ) -> int:
        """
        Update multiple documents.
        Returns count of modified documents.
        """
        result = await self.mongo_db[collection].update_many(
            query,
            {"$set": update_data}
        )
        return result.modified_count
    
    async def delete(
        self,
        collection: str,
        query: Dict
    ) -> bool:
        """
        Delete a single document.
        Returns True if document was deleted.
        """
        result = await self.mongo_db[collection].delete_one(query)
        return result.deleted_count > 0
    
    async def delete_many(
        self,
        collection: str,
        query: Dict
    ) -> int:
        """
        Delete multiple documents.
        Returns count of deleted documents.
        """
        result = await self.mongo_db[collection].delete_many(query)
        return result.deleted_count
    
    async def count(
        self,
        collection: str,
        query: Optional[Dict] = None
    ) -> int:
        """Count documents matching query."""
        return await self.mongo_db[collection].count_documents(query or {})
    
    async def exists(
        self,
        collection: str,
        query: Dict
    ) -> bool:
        """Check if any document matches the query."""
        count = await self.mongo_db[collection].count_documents(query, limit=1)
        return count > 0
    
    # ==================== Convenience Methods ====================
    
    async def get_by_id(self, collection: str, doc_id: str) -> Optional[Dict]:
        """Get document by id field."""
        return await self.find_one(collection, {"id": doc_id})
    
    async def update_by_id(
        self,
        collection: str,
        doc_id: str,
        update_data: Dict
    ) -> bool:
        """Update document by id field."""
        return await self.update(collection, {"id": doc_id}, update_data)
    
    async def delete_by_id(self, collection: str, doc_id: str) -> bool:
        """Delete document by id field."""
        return await self.delete(collection, {"id": doc_id})
    
    # ==================== Aggregation ====================
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict],
        limit: int = 1000
    ) -> List[Dict]:
        """
        Run aggregation pipeline.
        """
        cursor = self.mongo_db[collection].aggregate(pipeline)
        docs = await cursor.to_list(limit)
        for doc in docs:
            doc.pop('_id', None)
        return docs
    
    # ==================== Specialized Queries ====================
    
    async def find_with_or(
        self,
        collection: str,
        or_conditions: List[Dict],
        additional_query: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Find documents matching any of the OR conditions.
        """
        query = {"$or": or_conditions}
        if additional_query:
            query = {"$and": [query, additional_query]}
        return await self.find(collection, query, limit=limit)
    
    async def find_in(
        self,
        collection: str,
        field: str,
        values: List[Any],
        additional_query: Optional[Dict] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Find documents where field value is in the list.
        """
        query = {field: {"$in": values}}
        if additional_query:
            query.update(additional_query)
        return await self.find(collection, query, limit=limit)
    
    async def search_text(
        self,
        collection: str,
        fields: List[str],
        search_term: str,
        additional_query: Optional[Dict] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search documents with regex on multiple fields.
        """
        or_conditions = [
            {field: {"$regex": search_term, "$options": "i"}}
            for field in fields
        ]
        return await self.find_with_or(
            collection, or_conditions, additional_query, limit
        )
    
    # ==================== Audit Logging Helper ====================
    
    async def log_audit(
        self,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        organization_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        severity: str = "INFO"
    ):
        """Create an audit log entry."""
        log_entry = {
            'id': str(uuid.uuid4()),
            'action': action,
            'user_id': user_id,
            'user_email': user_email,
            'organization_id': organization_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'severity': severity,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if details:
            log_entry['details'] = details
        
        await self.insert("audit_logs", log_entry, generate_id=False)
    
    # ==================== Direct MongoDB Access ====================
    
    def collection(self, name: str):
        """
        Get direct access to MongoDB collection.
        Use sparingly - prefer the abstracted methods above.
        """
        return self.mongo_db[name]


# Global instance
_db_service: Optional[DatabaseServiceV2] = None


def init_db_service_v2(mongo_db) -> DatabaseServiceV2:
    """Initialize the database service with MongoDB connection."""
    global _db_service
    _db_service = DatabaseServiceV2(mongo_db)
    return _db_service


def get_db_service() -> DatabaseServiceV2:
    """Get the database service instance."""
    if _db_service is None:
        raise RuntimeError("Database service not initialized. Call init_db_service_v2 first.")
    return _db_service
