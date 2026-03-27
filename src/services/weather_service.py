# src/services/weather_service.py
import asyncio
import logging
from datetime import datetime

from ..clients.weather_client import WeatherClient
from ..intelligence.analyzer import WeatherAnalyzer
from ..models.weather_model import WeatherIntelligence, Location
from ..config import settings
from ..db.database import Database
from ..db.queries import WeatherQueries

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Main business logic layer with database persistence.
    Fetches weather → Analyzes → Saves to DB → Returns intelligent response.
    """

    def __init__(self):
        self.weather_client = WeatherClient()
        self.analyzer = WeatherAnalyzer()

    async def get_intelligent_weather(self, city: str) -> WeatherIntelligence:
        """
        Main method: Get full intelligent weather with DB persistence.
        """
        try:
            # Step 1: Fetch raw weather data from API
            raw_weather: WeatherIntelligence = await self.weather_client.get_weather_intelligence(city)

            # Step 2: Apply intelligence (summary, recommendation, alerts)
            intelligent_weather = self.analyzer.analyze(raw_weather)

            # Step 3: Save to database (in background)
            asyncio.create_task(self._save_to_database(intelligent_weather))

            logger.info(f"Successfully processed intelligent weather for: {city}")
            return intelligent_weather

        except Exception as e:
            logger.error(f"Error processing weather for {city}: {e}")
            raise RuntimeError(f"Failed to get weather for {city}: {str(e)}")

    async def get_current_only(self, city: str) -> WeatherIntelligence:
        """
        Get only current weather with intelligence and save to DB.
        """
        try:
            geo_data = await self.weather_client.get_coordinates(city)
            lat = geo_data["lat"]
            lon = geo_data["lon"]

            current = await self.weather_client.get_current_weather(lat, lon)

            intel = WeatherIntelligence(
                location=current.location,
                current=current,
                hourly_forecast=None,
                daily_forecast=None,
                alerts=[],
                summary=None,
                recommendation=None,
                fetched_at=datetime.utcnow()
            )

            intelligent_weather = self.analyzer.analyze(intel)

            # Save to database
            asyncio.create_task(self._save_to_database(intelligent_weather))

            return intelligent_weather

        except Exception as e:
            logger.error(f"Error in get_current_only for {city}: {e}")
            raise

    async def _save_to_database(self, weather_intel: WeatherIntelligence):
        """
        Save weather data and alerts to PostgreSQL database.
        Runs in background to not block the API response.
        """
        try:
            # Save location and get location_id
            location_id = await WeatherQueries.save_location(weather_intel.location)

            # Save current weather data
            await WeatherQueries.save_weather_data(
                location_id=location_id,
                data=weather_intel.current.data
            )

            # Save alerts (if any)
            for alert in weather_intel.alerts:
                # Attach proper location_id to alert
                alert.location = weather_intel.location  # Ensure location is set
                await WeatherQueries.save_alert(alert, location_id)

            logger.info(f"✅ Saved weather data to DB for location_id: {location_id}")

        except Exception as e:
            logger.error(f"Failed to save weather data to database: {e}")
            # We don't raise here because we don't want to fail the user request

    async def get_weather_history(self, city: str, limit: int = 20):
        """
        Get historical weather data for a city.
        """
        try:
            # First get location
            geo_data = await self.weather_client.get_coordinates(city)
            # For simplicity, we can improve this later with proper location lookup
            # For now, we'll skip full history implementation
            return {"message": "History endpoint coming soon", "city": city}
        except Exception as e:
            raise RuntimeError(f"Failed to get history: {e}")

    def health_check(self) -> dict:
        """Service health check"""
        return {
            "service": "WeatherService",
            "status": "healthy",
            "environment": settings.APP_ENV,
            "database": "connected" if Database._pool else "disconnected",
            "high_temp_threshold": settings.TEMPERATURE_THRESHOLD_HIGH,
            "cache_ttl": settings.CACHE_TTL
        }


# Global singleton instance
weather_service = WeatherService()