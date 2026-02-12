"""
MongoDB to PostgreSQL Migration Script
Migrates all data from MongoDB collections to PostgreSQL tables
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

# Add backend to path
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connections
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
POSTGRES_URL = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://yacco:yacco_secure_2024@localhost:5432/yacco_health')


class MigrationManager:
    """Manages the migration from MongoDB to PostgreSQL"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.pg_engine = None
        self.pg_session_factory = None
        self.stats = {
            "tables_created": 0,
            "records_migrated": 0,
            "errors": []
        }
    
    async def connect(self):
        """Establish database connections"""
        # MongoDB
        self.mongo_client = AsyncIOMotorClient(MONGO_URL)
        self.mongo_db = self.mongo_client[DB_NAME]
        
        # PostgreSQL
        self.pg_engine = create_async_engine(POSTGRES_URL, echo=False)
        self.pg_session_factory = async_sessionmaker(
            self.pg_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        logger.info("Connected to MongoDB and PostgreSQL")
    
    async def close(self):
        """Close database connections"""
        if self.mongo_client:
            self.mongo_client.close()
        if self.pg_engine:
            await self.pg_engine.dispose()
    
    async def create_tables(self):
        """Create PostgreSQL tables from SQLAlchemy models"""
        from database.models import Base
        
        async with self.pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)  # Clean slate
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("PostgreSQL tables created")
        self.stats["tables_created"] += 1
    
    def convert_mongo_doc(self, doc: Dict, table_name: str) -> Dict:
        """Convert MongoDB document to PostgreSQL compatible format"""
        if not doc:
            return None
        
        # Remove MongoDB _id
        doc.pop('_id', None)
        
        # Convert datetime strings to datetime objects
        date_fields = ['created_at', 'updated_at', 'approved_at', 'sent_at', 
                       'received_at', 'completed_at', 'expires_at', 'timestamp',
                       'last_login', 'locked_at', 'suspended_at', 'password_reset_at',
                       'verified_at', 'last_message_at', 'prescribed_at', 'recorded_at',
                       'onset_date', 'resolved_date', 'accepted_at', 'edited_at',
                       'start_time', 'end_time', 'clock_in_time', 'clock_out_time']
        
        for field in date_fields:
            if field in doc and doc[field]:
                value = doc[field]
                if isinstance(value, str):
                    try:
                        doc[field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        doc[field] = None
        
        # Handle special fields
        if 'is_active' in doc and doc['is_active'] is None:
            doc['is_active'] = True
        
        return doc
    
    async def migrate_collection(
        self,
        collection_name: str,
        table_name: str,
        field_mapping: Optional[Dict[str, str]] = None,
        transform_func: Optional[callable] = None
    ):
        """Migrate a single collection to a table"""
        try:
            cursor = self.mongo_db[collection_name].find({})
            docs = await cursor.to_list(length=10000)
            
            if not docs:
                logger.info(f"Skipping {collection_name} - no documents")
                return 0
            
            async with self.pg_session_factory() as session:
                count = 0
                for doc in docs:
                    try:
                        # Convert document
                        converted = self.convert_mongo_doc(doc, table_name)
                        if not converted:
                            continue
                        
                        # Apply field mapping
                        if field_mapping:
                            for old_key, new_key in field_mapping.items():
                                if old_key in converted:
                                    converted[new_key] = converted.pop(old_key)
                        
                        # Apply custom transform
                        if transform_func:
                            converted = transform_func(converted)
                            if not converted:
                                continue
                        
                        # Build INSERT statement
                        columns = ', '.join(converted.keys())
                        placeholders = ', '.join([f':{k}' for k in converted.keys()])
                        
                        sql = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING")
                        await session.execute(sql, converted)
                        count += 1
                        
                    except Exception as e:
                        logger.error(f"Error migrating doc in {collection_name}: {e}")
                        self.stats["errors"].append(f"{collection_name}: {str(e)[:100]}")
                
                await session.commit()
                logger.info(f"Migrated {count} records from {collection_name} to {table_name}")
                self.stats["records_migrated"] += count
                return count
                
        except Exception as e:
            logger.error(f"Error migrating collection {collection_name}: {e}")
            self.stats["errors"].append(f"{collection_name}: {str(e)}")
            return 0
    
    async def run_migration(self):
        """Run the full migration"""
        await self.connect()
        
        try:
            # Create tables
            await self.create_tables()
            
            # Migration mapping: (mongo_collection, pg_table, field_mapping, transform)
            migrations = [
                # Core entities
                ("regions", "regions", None, None),
                ("organizations", "organizations", None, None),
                ("hospitals", "hospitals", None, None),
                
                # Users
                ("users", "users", None, None),
                ("otp_sessions", "otp_sessions", None, None),
                
                # Patients
                ("patients", "patients", None, None),
                
                # Clinical data
                ("vitals", "vitals", None, None),
                ("allergies", "allergies", None, None),
                ("prescriptions", "prescriptions", None, None),
                
                # Pharmacy
                ("pharmacies", "pharmacies", None, None),
                ("pharmacy_staff", "pharmacy_staff", None, None),
                
                # Departments
                ("departments", "departments", None, None),
                
                # Audit logs
                ("audit_logs", "audit_logs", None, None),
            ]
            
            for mongo_coll, pg_table, mapping, transform in migrations:
                await self.migrate_collection(mongo_coll, pg_table, mapping, transform)
            
            # Print summary
            logger.info("=" * 50)
            logger.info("MIGRATION COMPLETE")
            logger.info(f"Tables created: {self.stats['tables_created']}")
            logger.info(f"Records migrated: {self.stats['records_migrated']}")
            logger.info(f"Errors: {len(self.stats['errors'])}")
            if self.stats['errors']:
                for err in self.stats['errors'][:10]:
                    logger.error(f"  - {err}")
            logger.info("=" * 50)
            
        finally:
            await self.close()


async def main():
    """Main entry point"""
    migrator = MigrationManager()
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
