"""
MongoDB to PostgreSQL Migration Script - V2
Migrates all data from MongoDB collections to PostgreSQL tables
with proper field filtering
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')
POSTGRES_URL = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://yacco:yacco_secure_2024@localhost:5432/yacco_health')


class MigrationManagerV2:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.pg_engine = None
        self.pg_session_factory = None
        self.table_columns: Dict[str, Set[str]] = {}
        self.stats = {"tables_created": 0, "records_migrated": 0, "errors": []}
    
    async def connect(self):
        self.mongo_client = AsyncIOMotorClient(MONGO_URL)
        self.mongo_db = self.mongo_client[DB_NAME]
        self.pg_engine = create_async_engine(POSTGRES_URL, echo=False)
        self.pg_session_factory = async_sessionmaker(
            self.pg_engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Connected to databases")
    
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
            # Get column names for each table
            def get_columns(connection):
                inspector = inspect(connection)
                for table_name in inspector.get_table_names():
                    columns = {col['name'] for col in inspector.get_columns(table_name)}
                    self.table_columns[table_name] = columns
            await conn.run_sync(get_columns)
        logger.info(f"Created tables: {list(self.table_columns.keys())}")
        self.stats["tables_created"] = len(self.table_columns)
    
    def filter_document(self, doc: Dict, table_name: str) -> Dict:
        """Filter document to only include columns that exist in the table"""
        if table_name not in self.table_columns:
            return {}
        
        valid_columns = self.table_columns[table_name]
        doc.pop('_id', None)
        
        filtered = {}
        for key, value in doc.items():
            if key in valid_columns:
                # Convert datetime strings
                if isinstance(value, str) and ('_at' in key or key in ['timestamp', 'date', 'onset_date', 'resolved_date']):
                    try:
                        filtered[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        filtered[key] = None
                else:
                    filtered[key] = value
        
        return filtered
    
    async def migrate_collection(self, collection_name: str, table_name: str):
        try:
            if table_name not in self.table_columns:
                logger.warning(f"Table {table_name} not found, skipping {collection_name}")
                return 0
            
            cursor = self.mongo_db[collection_name].find({})
            docs = await cursor.to_list(length=10000)
            
            if not docs:
                logger.info(f"No documents in {collection_name}")
                return 0
            
            count = 0
            async with self.pg_session_factory() as session:
                for doc in docs:
                    try:
                        filtered = self.filter_document(doc, table_name)
                        if not filtered or 'id' not in filtered:
                            continue
                        
                        columns = ', '.join(filtered.keys())
                        placeholders = ', '.join([f':{k}' for k in filtered.keys()])
                        sql = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING")
                        
                        await session.execute(sql, filtered)
                        count += 1
                    except Exception as e:
                        if 'duplicate key' not in str(e).lower():
                            logger.error(f"Error: {e}")
                
                await session.commit()
            
            logger.info(f"Migrated {count}/{len(docs)} from {collection_name} to {table_name}")
            self.stats["records_migrated"] += count
            return count
            
        except Exception as e:
            logger.error(f"Collection error {collection_name}: {e}")
            return 0
    
    async def run_migration(self):
        await self.connect()
        try:
            await self.create_tables()
            
            migrations = [
                ("regions", "regions"),
                ("organizations", "organizations"),
                ("hospitals", "hospitals"),
                ("users", "users"),
                ("otp_sessions", "otp_sessions"),
                ("patients", "patients"),
                ("vitals", "vitals"),
                ("allergies", "allergies"),
                ("prescriptions", "prescriptions"),
                ("pharmacies", "pharmacies"),
                ("pharmacy_staff", "pharmacy_staff"),
                ("departments", "departments"),
                ("audit_logs", "audit_logs"),
            ]
            
            for mongo_coll, pg_table in migrations:
                await self.migrate_collection(mongo_coll, pg_table)
            
            logger.info("=" * 50)
            logger.info(f"MIGRATION COMPLETE: {self.stats['records_migrated']} records migrated")
            logger.info("=" * 50)
            
        finally:
            await self.close()


async def main():
    migrator = MigrationManagerV2()
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
