"""
MongoDB to PostgreSQL Migration Script - V3
Robust migration with proper error handling and default values
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import logging

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, inspect

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
POSTGRES_URL = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://yacco:yacco_secure_2024@localhost:5432/yacco_health')

# Default values for required fields that might be missing in MongoDB
DEFAULT_VALUES = {
    'organizations': {
        'registration_status': 'pending',
        'status': 'pending',
        'subscription_tier': 'basic',
        'max_users': 50,
        'total_users': 0,
        'country': 'Ghana'
    },
    'hospitals': {
        'registration_status': 'pending',
        'status': 'pending',
        'organization_type': 'hospital'
    },
    'users': {
        'status': 'active',
        'is_active': True,
        'is_temp_password': False,
        'login_attempts': 0
    },
    'patients': {
        'status': 'active',
        'is_active': True
    },
    'pharmacies': {
        'status': 'pending',
        'registration_status': 'pending'
    },
    'pharmacy_staff': {
        'status': 'active',
        'is_active': True
    }
}


class MigrationManagerV3:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.pg_engine = None
        self.pg_session_factory = None
        self.table_columns: Dict[str, Set[str]] = {}
        self.stats = {
            "tables_created": 0,
            "records_migrated": 0,
            "records_failed": 0,
            "collections_processed": 0
        }
    
    async def connect(self):
        self.mongo_client = AsyncIOMotorClient(MONGO_URL)
        self.mongo_db = self.mongo_client[DB_NAME]
        self.pg_engine = create_async_engine(POSTGRES_URL, echo=False)
        self.pg_session_factory = async_sessionmaker(
            self.pg_engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("✅ Connected to MongoDB and PostgreSQL")
    
    async def close(self):
        if self.mongo_client:
            self.mongo_client.close()
        if self.pg_engine:
            await self.pg_engine.dispose()
    
    async def create_tables(self):
        from database.models import Base
        async with self.pg_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
            def get_columns(connection):
                inspector = inspect(connection)
                for table_name in inspector.get_table_names():
                    columns = {col['name'] for col in inspector.get_columns(table_name)}
                    self.table_columns[table_name] = columns
            await conn.run_sync(get_columns)
        
        self.stats["tables_created"] = len(self.table_columns)
        logger.info(f"✅ Created {len(self.table_columns)} tables")
    
    def apply_defaults(self, doc: Dict, table_name: str) -> Dict:
        """Apply default values for missing required fields"""
        defaults = DEFAULT_VALUES.get(table_name, {})
        for field, default_value in defaults.items():
            if field not in doc or doc[field] is None:
                doc[field] = default_value
        return doc
    
    def convert_value(self, key: str, value: Any) -> Any:
        """Convert value to PostgreSQL compatible format"""
        if value is None:
            return None
        
        # Convert datetime strings
        datetime_fields = ['created_at', 'updated_at', 'approved_at', 'sent_at', 
                       'received_at', 'completed_at', 'expires_at', 'timestamp',
                       'last_login', 'locked_at', 'suspended_at', 'password_reset_at',
                       'verified_at', 'last_message_at', 'prescribed_at', 'recorded_at',
                       'accepted_at', 'edited_at', 'deactivated_at', 'activated_at', 
                       'unlocked_at', 'phone_updated_at']
        
        # Date only fields (not datetime)
        date_fields = ['date_of_birth', 'onset_date', 'resolved_date', 'patient_dob']
        
        if key in datetime_fields and isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return None
        
        if key in date_fields and isinstance(value, str):
            try:
                # Parse date string to date object
                from datetime import date as dt_date
                if 'T' in value:
                    return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
                else:
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            return datetime.strptime(value, fmt).date()
                        except:
                            continue
                    return None
            except:
                return None
        
        # Convert lists and dicts to JSON strings for JSONB columns
        if isinstance(value, (list, dict)):
            import json
            return json.dumps(value)
        
        return value
    
    def filter_document(self, doc: Dict, table_name: str) -> Dict:
        """Filter and transform document for PostgreSQL"""
        if table_name not in self.table_columns:
            return {}
        
        # Remove MongoDB _id
        doc.pop('_id', None)
        
        # Apply defaults
        doc = self.apply_defaults(doc, table_name)
        
        # Filter to valid columns and convert values
        valid_columns = self.table_columns[table_name]
        filtered = {}
        
        for key, value in doc.items():
            if key in valid_columns:
                converted = self.convert_value(key, value)
                filtered[key] = converted
        
        return filtered
    
    async def migrate_collection(self, collection_name: str, table_name: str):
        """Migrate a single collection with individual transaction per record"""
        if table_name not in self.table_columns:
            logger.warning(f"⚠️  Table '{table_name}' not found, skipping '{collection_name}'")
            return 0
        
        try:
            cursor = self.mongo_db[collection_name].find({})
            docs = await cursor.to_list(length=10000)
            
            if not docs:
                logger.info(f"⏭️  No documents in '{collection_name}'")
                return 0
            
            success_count = 0
            fail_count = 0
            
            for doc in docs:
                try:
                    filtered = self.filter_document(doc, table_name)
                    if not filtered or 'id' not in filtered:
                        continue
                    
                    # Use individual session per record to avoid transaction failures
                    async with self.pg_session_factory() as session:
                        columns = ', '.join(filtered.keys())
                        placeholders = ', '.join([f':{k}' for k in filtered.keys()])
                        sql = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING")
                        
                        await session.execute(sql, filtered)
                        await session.commit()
                        success_count += 1
                        
                except Exception as e:
                    fail_count += 1
                    if 'duplicate key' not in str(e).lower() and 'unique constraint' not in str(e).lower():
                        # Only log non-duplicate errors
                        if fail_count <= 3:  # Limit error logging
                            logger.debug(f"  Record error: {str(e)[:100]}")
            
            self.stats["records_migrated"] += success_count
            self.stats["records_failed"] += fail_count
            self.stats["collections_processed"] += 1
            
            status = "✅" if fail_count == 0 else "⚠️ "
            logger.info(f"{status} {collection_name} → {table_name}: {success_count}/{len(docs)} migrated")
            
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Collection error '{collection_name}': {e}")
            return 0
    
    async def run_migration(self):
        """Run the full migration"""
        logger.info("=" * 60)
        logger.info("MONGODB TO POSTGRESQL MIGRATION")
        logger.info("=" * 60)
        
        await self.connect()
        
        try:
            await self.create_tables()
            
            # Migration mapping
            migrations = [
                # Core entities
                ("regions", "regions"),
                ("organizations", "organizations"),
                ("hospitals", "hospitals"),
                
                # Users & Auth
                ("users", "users"),
                ("otp_sessions", "otp_sessions"),
                
                # Patients
                ("patients", "patients"),
                ("patient_medical_history", "patient_medical_history"),
                
                # Clinical data
                ("vitals", "vitals"),
                ("allergies", "allergies"),
                ("prescriptions", "prescriptions"),
                
                # Pharmacy
                ("pharmacies", "pharmacies"),
                ("pharmacy_staff", "pharmacy_staff"),
                
                # Infrastructure
                ("departments", "departments"),
                
                # Audit
                ("audit_logs", "audit_logs"),
            ]
            
            logger.info("\n📦 Migrating collections...")
            for mongo_coll, pg_table in migrations:
                await self.migrate_collection(mongo_coll, pg_table)
            
            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("MIGRATION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"📊 Tables created: {self.stats['tables_created']}")
            logger.info(f"📦 Collections processed: {self.stats['collections_processed']}")
            logger.info(f"✅ Records migrated: {self.stats['records_migrated']}")
            logger.info(f"⚠️  Records failed: {self.stats['records_failed']}")
            logger.info("=" * 60)
            
            return self.stats
            
        finally:
            await self.close()


async def verify_migration():
    """Verify the migration was successful"""
    engine = create_async_engine(POSTGRES_URL, echo=False)
    
    async with engine.begin() as conn:
        tables_to_check = ['regions', 'organizations', 'hospitals', 'users', 'patients', 'pharmacies']
        
        logger.info("\n📋 VERIFICATION")
        logger.info("-" * 40)
        
        for table in tables_to_check:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            logger.info(f"  {table}: {count} records")
    
    await engine.dispose()


async def main():
    migrator = MigrationManagerV3()
    stats = await migrator.run_migration()
    
    if stats["records_migrated"] > 0:
        await verify_migration()


if __name__ == "__main__":
    asyncio.run(main())
