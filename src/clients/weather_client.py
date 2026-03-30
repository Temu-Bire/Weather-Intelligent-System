# src/clients/weather_client.py

import aiohttp
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import json

from ..config import Settings

from ..models.weather_model import (
    Location,
    CurrentWeather,
    Forecast,
    WeatherIntelligence,
     ForecastType, 
    WeatherDataPoint,
    WeatherCondition,
)

settings = Settings()  # Access global settings instance
class WeatherClient:
    """
    Async client for fetching weather data from OpenWeatherMap API
    and converting it into the intelligent weather models.
    """

    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.geo_url = settings.OPENWEATHER_GEO_URL
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get(self, url: str, params: Dict[str, Any] ) -> Dict:
        """Helper method for GET requests"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

    async def get_coordinates(self, city: str) -> Dict:
        """Get latitude and longitude for a city name"""
        url = f"{self.geo_url}/direct"
        params = {
            "q": city,
            "limit": 1,
            "appid": self.api_key
        }
        data = await self._get(url, params)
        if not data:
            raise ValueError(f"Could not find location for city: {city}")
        return data[0]

    async def get_current_weather(self, lat: float, lon: float) -> CurrentWeather:
        """Fetch current weather data"""
        url = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        data = await self._get(url, params)

        # Convert OpenWeatherMap response to our model
        weather_data = WeatherDataPoint(
            timestamp=datetime.utcnow(),
            temperature_c=data["main"]["temp"],
            feels_like_c=data["main"].get("feels_like"),
            humidity_percent=data["main"].get("humidity"),
            pressure_hpa=data["main"].get("pressure"),
            wind_speed_kmh=data["wind"].get("speed", 0) * 3.6,  # m/s to km/h
            wind_direction_deg=data["wind"].get("deg"),
            precipitation_mm=data.get("rain", {}).get("1h", 0) or data.get("snow", {}).get("1h", 0),
            condition=self._map_condition(data["weather"][0]["main"]),
            visibility_km=data.get("visibility", 0) / 1000,
            uv_index=None,  # Not available in current weather endpoint
            raw_data=data
        )

        location = Location(
            name=data["name"],
            latitude=lat,
            longitude=lon,
            country=data.get("sys", {}).get("country")
        )

        return CurrentWeather(
            location=location,
            data=weather_data
        )

    async def get_forecast(self, lat: float, lon: float, forecast_type: ForecastType = ForecastType.daily) -> Forecast:
        """Fetch hourly or daily forecast"""
        endpoint = "forecast"
        url = f"{self.base_url}/{endpoint}"
        
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        # Note: OpenWeatherMap free tier has limitations on daily forecast
        if forecast_type == ForecastType.daily:
            params["cnt"] = 7  # up to 7 days

        data = await self._get(url, params)

        data_points = []
        for item in data.get("list", [])[:24 if forecast_type == ForecastType.hourly else 7]:
            dp = WeatherDataPoint(
                timestamp=datetime.fromtimestamp(item["dt"]),
                temperature_c=item["main"]["temp"],
                feels_like_c=item["main"].get("feels_like"),
                humidity_percent=item["main"].get("humidity"),
                pressure_hpa=item["main"].get("pressure"),
                wind_speed_kmh=item["wind"].get("speed", 0) * 3.6,
                wind_direction_deg=item["wind"].get("deg"),
                precipitation_mm=item.get("rain", {}).get("1h") or item.get("snow", {}).get("1h") or 0,
                condition=self._map_condition(item["weather"][0]["main"]),
                visibility_km=item.get("visibility", 0) / 1000 if "visibility" in item else None,
                uv_index=item.get("uvi"),
                raw_data=item
            )
            data_points.append(dp)

        location = Location(
            name=data.get("city", {}).get("name", "Unknown"),
            latitude=lat,
            longitude=lon,
            country=data.get("city", {}).get("country")
        )

        return Forecast(
            location=location,
            forecast_type=forecast_type,
            data_points=data_points
        )

    def _map_condition(self, condition_str: str) -> WeatherCondition:
        """Map OpenWeatherMap condition to our enum"""
        condition_map = {
            "Clear": WeatherCondition.clear,
            "Clouds": WeatherCondition.cloudy,
            "Few clouds": WeatherCondition.partly_cloudy,
            "Scattered clouds": WeatherCondition.partly_cloudy,
            "Broken clouds": WeatherCondition.cloudy,
            "Rain": WeatherCondition.rain,
            "Shower rain": WeatherCondition.rain,
            "Thunderstorm": WeatherCondition.thunderstorm,
            "Snow": WeatherCondition.snow,
            "Mist": WeatherCondition.fog,
            "Smoke": WeatherCondition.fog,
            "Haze": WeatherCondition.fog,
            "Fog": WeatherCondition.fog,
            "Drizzle": WeatherCondition.rain,
        }
        return condition_map.get(condition_str, WeatherCondition.cloudy)

    async def get_weather_intelligence(self, city: str) -> WeatherIntelligence:
        """
        Main method: Fetch current weather + forecasts and return intelligent response
        """
        # Step 1: Get coordinates
        geo_data = await self.get_coordinates(city)
        lat = geo_data["lat"]
        lon = geo_data["lon"]

        # Step 2: Fetch current weather and forecasts in parallel
        current_task = self.get_current_weather(lat, lon)
        hourly_task = self.get_forecast(lat, lon, ForecastType.hourly)
        daily_task = self.get_forecast(lat, lon, ForecastType.daily)

        current, hourly, daily = await asyncio.gather(current_task, hourly_task, daily_task)

        # Step 3: Build final intelligence object
        # (Alerts and smart summary/recommendation will be added by intelligence/analyzer.py)
        return WeatherIntelligence(
            location=current.location,
            current=current,
            hourly_forecast=hourly,
            daily_forecast=daily,
            alerts=[],  # Populated later by analyzer
            summary=None,
            recommendation=None,
            fetched_at=datetime.utcnow()
        )


# Usage example (for testing)
async def main():
    city = input("Enter city name: ")  # User provides the city dynamically

    async with WeatherClient() as client:
        intelligence = await client.get_weather_intelligence(city)
        print(json.dumps(intelligence.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
