# src/intelligence/analyzer.py

from datetime import datetime
from typing import List, Optional

from ..config import settings
from ..models.weather_model import (
    WeatherIntelligence,
    WeatherDataPoint,
    WeatherAlert,
    AlertSeverity,
    WeatherCondition
)


class WeatherAnalyzer:
    """
    Intelligent analysis engine for weather data.
    Generates smart summaries, recommendations, and alerts.
    """

    def analyze(self, weather_intel: WeatherIntelligence) -> WeatherIntelligence:
        """
        Main method: Analyze weather data and enrich it with intelligence.
        """
        current = weather_intel.current.data
        location_name = weather_intel.location.name

        # Generate smart summary and recommendation
        summary = self._generate_summary(current, location_name)
        recommendation = self._generate_recommendation(current)

        # Generate alerts based on thresholds
        alerts = self._generate_alerts(current, location_name)

        # Enrich the original object
        weather_intel.summary = summary
        weather_intel.recommendation = recommendation
        weather_intel.alerts = alerts

        return weather_intel

    def _generate_summary(self, data: WeatherDataPoint, location: str) -> str:
        """Generate a human-friendly weather summary"""
        temp = round(data.temperature_c)
        condition = data.condition.value.replace("_", " ").title()

        if data.precipitation_mm and data.precipitation_mm > 5:
            return f"Heavy {condition.lower()} with {data.precipitation_mm:.1f}mm precipitation in {location}."
        elif temp > 30:
            return f"Very hot day in {location} with {temp}°C and {condition.lower()} conditions."
        elif temp < 5:
            return f"Cold conditions in {location} at {temp}°C with {condition.lower()}."
        else:
            return f"Currently {temp}°C with {condition.lower()} skies in {location}."

    def _generate_recommendation(self, data: WeatherDataPoint) -> str:
        """Generate practical recommendation based on weather"""
        temp = data.temperature_c
        precip = data.precipitation_mm or 0
        wind = data.wind_speed_kmh or 0
        condition = data.condition

        if precip > 10 or condition in [WeatherCondition.heavy_rain, WeatherCondition.thunderstorm]:
            return "Stay indoors and avoid unnecessary travel. Heavy rain or thunderstorms expected."

        elif temp > settings.TEMPERATURE_THRESHOLD_HIGH:
            return "Extreme heat. Stay hydrated, avoid direct sun, and limit outdoor activities."

        elif temp < settings.TEMPERATURE_THRESHOLD_LOW:
            return "Cold weather. Wear warm clothes and protect yourself from low temperatures."

        elif wind > settings.WIND_SPEED_THRESHOLD:
            return "Strong winds. Be careful with outdoor objects and driving."

        elif data.uv_index and data.uv_index > settings.UV_INDEX_THRESHOLD:
            return "High UV index. Use sunscreen and wear protective clothing if going outside."

        elif condition in [WeatherCondition.fog]:
            return "Poor visibility due to fog. Drive carefully and use fog lights."

        else:
            return "Good weather for most outdoor activities. Enjoy your day!"

    def _generate_alerts(self, data: WeatherDataPoint, location: str) -> List[WeatherAlert]:
        """Generate weather alerts based on configured thresholds"""
        alerts: List[WeatherAlert] = []
        now = datetime.utcnow()

        # Heat Alert
        if data.temperature_c >= settings.TEMPERATURE_THRESHOLD_HIGH:
            alerts.append(WeatherAlert(
                location=Location(name=location, latitude=0, longitude=0),  # Will be properly set by service
                severity=AlertSeverity.severe if data.temperature_c > 38 else AlertSeverity.moderate,
                title="Heat Warning",
                description=f"Temperature reaching {round(data.temperature_c)}°C. Take necessary precautions.",
                starts_at=now,
                ends_at=None,
                affected_parameters=["temperature"]
            ))

        # Cold Alert
        if data.temperature_c <= settings.TEMPERATURE_THRESHOLD_LOW:
            alerts.append(WeatherAlert(
                location=Location(name=location, latitude=0, longitude=0),
                severity=AlertSeverity.moderate,
                title="Cold Warning",
                description=f"Low temperature of {round(data.temperature_c)}°C. Dress warmly.",
                starts_at=now,
                ends_at=None,
                affected_parameters=["temperature"]
            ))

        # Heavy Rain / Thunderstorm Alert
        if (data.precipitation_mm and data.precipitation_mm > 15) or \
           data.condition in [WeatherCondition.heavy_rain, WeatherCondition.thunderstorm]:
            alerts.append(WeatherAlert(
                location=Location(name=location, latitude=0, longitude=0),
                severity=AlertSeverity.severe,
                title="Heavy Rain / Thunderstorm Alert",
                description="Significant precipitation and/or thunderstorm activity expected.",
                starts_at=now,
                ends_at=None,
                affected_parameters=["precipitation", "condition"]
            ))

        # Strong Wind Alert
        if data.wind_speed_kmh and data.wind_speed_kmh > settings.WIND_SPEED_THRESHOLD:
            alerts.append(WeatherAlert(
                location=Location(name=location, latitude=0, longitude=0),
                severity=AlertSeverity.moderate,
                title="Strong Wind Alert",
                description=f"Wind speeds up to {round(data.wind_speed_kmh)} km/h.",
                starts_at=now,
                ends_at=None,
                affected_parameters=["wind"]
            ))

        # High UV Alert
        if data.uv_index and data.uv_index >= settings.UV_INDEX_THRESHOLD:
            alerts.append(WeatherAlert(
                location=Location(name=location, latitude=0, longitude=0),
                severity=AlertSeverity.moderate,
                title="High UV Index",
                description=f"UV index is {data.uv_index:.1f}. Protect your skin.",
                starts_at=now,
                ends_at=None,
                affected_parameters=["uv_index"]
            ))

        return alerts


# Helper: Fix missing Location import
from ..models.weather_model import Location