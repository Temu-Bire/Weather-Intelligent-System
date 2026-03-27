# src/db/queries.py

import json
from typing import List, Optional

from .database import Database
from ..models.weather_model import Location, WeatherDataPoint, WeatherAlert


class WeatherQueries:
    """All SQL queries related to weather data"""

    @staticmethod
    async def save_location(location: Location) -> int:
        """Save location and return location_id"""
        query = """
        INSERT INTO locations (name, latitude, longitude, country, timezone)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (latitude, longitude) 
        DO UPDATE SET name = EXCLUDED.name, country = EXCLUDED.country
        RETURNING location_id
        """
        result = await Database.fetchrow(
            query,
            location.name,
            location.latitude,
            location.longitude,
            location.country,
            location.timezone
        )
        return result['location_id']

    @staticmethod
    async def save_weather_data(location_id: int, data: WeatherDataPoint):
        """Save weather data point - FIXED for raw_data JSONB"""
        query = """
        INSERT INTO weather_data (
            location_id, timestamp, temperature_c, feels_like_c, humidity_percent,
            pressure_hpa, wind_speed_kmh, wind_direction_deg, precipitation_mm,
            condition, visibility_km, uv_index, raw_data
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        
        # Convert raw_data dict to JSON string (this was the bug)
        raw_data_json = json.dumps(data.raw_data) if data.raw_data else None

        await Database.execute(
            query,
            location_id,
            data.timestamp,
            data.temperature_c,
            data.feels_like_c,
            data.humidity_percent,
            data.pressure_hpa,
            data.wind_speed_kmh,
            data.wind_direction_deg,
            data.precipitation_mm,
            data.condition.value,
            data.visibility_km,
            data.uv_index,
            raw_data_json                    # ← Fixed: now passing string
        )

    @staticmethod
    async def save_alert(alert: WeatherAlert, location_id: int):
        """Save weather alert"""
        query = """
        INSERT INTO weather_alerts (
            location_id, severity, title, description, 
            starts_at, ends_at, affected_parameters
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await Database.execute(
            query,
            location_id,
            alert.severity.value,
            alert.title,
            alert.description,
            alert.starts_at,
            alert.ends_at,
            json.dumps(alert.affected_parameters)   # Also safe for list
        )

    @staticmethod
    async def get_latest_weather(location_id: int) -> Optional[dict]:
        query = """
        SELECT * FROM weather_data 
        WHERE location_id = $1 
        ORDER BY timestamp DESC 
        LIMIT 1
        """
        return await Database.fetchrow(query, location_id)

    @staticmethod
    async def get_weather_history(location_id: int, limit: int = 50) -> List[dict]:
        query = """
        SELECT * FROM weather_data 
        WHERE location_id = $1 
        ORDER BY timestamp DESC 
        LIMIT $2
        """
        return await Database.fetch(query, location_id, limit)