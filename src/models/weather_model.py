from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

# 1. Basic enums for consistent values
class WeatherCondition(str, Enum):
    clear = "clear"
    cloudy = "cloudy"
    partly_cloudy = "partly_cloudy"
    rain = "rain"
    heavy_rain = "heavy_rain"
    thunderstorm = "thunderstorm"
    snow = "snow"
    fog = "fog"
    windy = "windy"

class AlertSeverity(str, Enum):
    minor = "minor"
    moderate = "moderate"
    severe = "severe"
    extreme = "extreme"

# 2. Core weather data point (for current, hourly, or daily)
class WeatherDataPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Useful when loading from DB

    timestamp: datetime = Field(default_factory=datetime.utcnow)    
    temperature_c: float = Field(..., ge=-100, le=100, description="Temperature in Celsius")
    feels_like_c: Optional[float] = Field(None, ge=-100, le=100, description="Feels like temperature in Celsius")
    humidity_percent: Optional[int] = Field(None, ge=0, le=100, description="Humidity percentage")
    pressure_hpa: Optional[float] = Field(None, ge=800, le=1200, description="Atmospheric pressure in hPa")
    
    wind_speed_kmh: Optional[float] = Field(None, ge=0, description="Wind speed in km/h")
    wind_direction_deg: Optional[int] = Field(None, ge=0, le=360, description="Wind direction in degrees")

    precipitation_mm: Optional[float] = Field(None, ge=0, description="Precipitation in mm")
    condition: WeatherCondition
    
    visibility_km: Optional[float] = Field(None, ge=0, description="Visibility in km")
    uv_index: Optional[float] = Field(None, ge=0, le=12, description="UV index")

    # Extra flexible field for any API-specific data
    raw_data: Optional[dict] = None


# 3. Location model
class Location(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: Optional[int] = None          # Will be set by PostgreSQL
    name: str=Field(..., min_length=2, max_length=100)                                 # e.g. "Nairobi Downtown" or "My Farm"
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country: Optional[str] = None
    timezone: Optional[str] = "UTC"


# 4. Current weather (simple wrapper)
class CurrentWeather(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location: Location
    data: WeatherDataPoint
#5. Forecast type enum
class ForecastType(str, Enum):
    hourly = "hourly"
    daily = "daily"

# 6. Forecast (hourly or daily)
class Forecast(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location: Location
    forecast_type: ForecastType
    data_points: List[WeatherDataPoint] = Field(..., min_length=1)


# 7. Weather Alert / Intelligence part
class WeatherAlert(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: Optional[int] = None
    location: Location
    severity: AlertSeverity
    title: str
    description: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    affected_parameters: List[str] = Field(default_factory=list)  # e.g. ["rain", "wind"]


# 8. Combined Smart Response (what your system returns to user)
class WeatherIntelligence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location: Location
    current: CurrentWeather
    hourly_forecast: Optional[Forecast] = None
    daily_forecast: Optional[Forecast] = None
    alerts: List[WeatherAlert] = Field(default_factory=list)
    
    summary: Optional[str] = None          # e.g. "Heavy rain expected tomorrow afternoon"
    recommendation: Optional[str] = None   # e.g. "Good day for farming" or "Stay indoors"
    
    fetched_at: datetime = Field(default_factory=datetime.utcnow)