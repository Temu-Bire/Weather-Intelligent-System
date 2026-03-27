# src/db/database.py
import logging
from typing import Optional

import asyncpg
from asyncpg import Pool

from ..config import settings

logger = logging.getLogger(__name__)

class Database:
    """
    Database connection pool manager using asyncpg (PostgreSQL)
    """
    
    _pool: Optional[Pool] = None

    @classmethod
    async def connect(cls) -> None:
        """Create connection pool"""
        if cls._pool is not None:
            return

        try:
            cls._pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                min_size=5,
                max_size=20,
                command_timeout=60,
                timeout=30,
            )
            logger.info(f"✅ Connected to PostgreSQL database: {settings.DB_NAME}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise

    @classmethod
    async def close(cls) -> None:
        """Close the connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database connection pool closed.")

    @classmethod
    async def get_pool(cls) -> Pool:
        """Get the connection pool"""
        if cls._pool is None:
            await cls.connect()
        assert cls._pool # type: ignore is not None, "Database connection pool is not initialized"
        return cls._pool

    @classmethod
    async def execute(cls, query: str, *args):
        """Execute a query without returning rows"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args):
        """Fetch multiple rows"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args):
        """Fetch a single row"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    @classmethod
    async def fetchval(cls, query: str, *args):
        """Fetch a single value"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# Initialize database on startup
async def init_db():
    """Initialize database connection and create tables"""
    await Database.connect()
    await create_tables()
    logger.info("Database initialized successfully")


async def close_db():
    """Close database connection on shutdown"""
    await Database.close()


# Table creation
async def create_tables():
    """Create necessary tables if they don't exist"""
    create_location_table = """
    CREATE TABLE IF NOT EXISTS locations (
        location_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        latitude DOUBLE PRECISION NOT NULL,
        longitude DOUBLE PRECISION NOT NULL,
        country VARCHAR(50),
        timezone VARCHAR(50) DEFAULT 'UTC',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(latitude, longitude)
    );
    """

    create_weather_data_table = """
    CREATE TABLE IF NOT EXISTS weather_data (
        id SERIAL PRIMARY KEY,
        location_id INTEGER REFERENCES locations(location_id) ON DELETE CASCADE,
        timestamp TIMESTAMP NOT NULL,
        temperature_c DOUBLE PRECISION NOT NULL,
        feels_like_c DOUBLE PRECISION,
        humidity_percent INTEGER,
        pressure_hpa DOUBLE PRECISION,
        wind_speed_kmh DOUBLE PRECISION,
        wind_direction_deg INTEGER,
        precipitation_mm DOUBLE PRECISION,
        condition VARCHAR(50),
        visibility_km DOUBLE PRECISION,
        uv_index DOUBLE PRECISION,
        raw_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_alerts_table = """
    CREATE TABLE IF NOT EXISTS weather_alerts (
        alert_id SERIAL PRIMARY KEY,
        location_id INTEGER REFERENCES locations(location_id) ON DELETE CASCADE,
        severity VARCHAR(20) NOT NULL,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        starts_at TIMESTAMP NOT NULL,
        ends_at TIMESTAMP,
        affected_parameters JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    queries = [create_location_table, create_weather_data_table, create_alerts_table]

    for query in queries:
        await Database.execute(query)

    logger.info("✅ Database tables are ready")