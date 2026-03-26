# src/config.py

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings:
    # ==================== Application Settings ====================
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # ==================== Server Settings ====================
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # ==================== Weather API Settings ====================
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_GEO_URL: str = "https://api.openweathermap.org/geo/1.0"

    # ==================== Database Settings ====================
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str = os.getenv("DB_NAME", "weather_intelligent")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")

    # Async PostgreSQL Database URL
    DATABASE_URL: str = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

    # ==================== Cache Settings ====================
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 300))  # Default: 5 minutes

    # ==================== Intelligence Thresholds ====================
    TEMPERATURE_THRESHOLD_HIGH: float = float(os.getenv("TEMPERATURE_THRESHOLD_HIGH", 30.0))
    TEMPERATURE_THRESHOLD_LOW: float = float(os.getenv("TEMPERATURE_THRESHOLD_LOW", 5.0))
    RAIN_PROBABILITY_THRESHOLD: int = int(os.getenv("RAIN_PROBABILITY_THRESHOLD", 60))
    WIND_SPEED_THRESHOLD: float = float(os.getenv("WIND_SPEED_THRESHOLD", 25.0))  # km/h
    UV_INDEX_THRESHOLD: float = float(os.getenv("UV_INDEX_THRESHOLD", 8.0))

    # ==================== Application Metadata ====================
    APP_NAME: str = "Weather Intelligent"
    APP_VERSION: str = "1.0.0"
    DESCRIPTION: str = "Intelligent Weather Analysis & Recommendation System"

    @classmethod
    def validate(cls):
        """Validate required configuration values"""
        required_vars = [
            "OPENWEATHER_API_KEY",
            "DB_PASSWORD"
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file."
            )

        if cls.APP_ENV not in ["development", "production", "testing"]:
            raise ValueError(f"Invalid APP_ENV: {cls.APP_ENV}. Must be one of: development, production, testing")

        if cls.PORT < 1024 or cls.PORT > 65535:
            raise ValueError(f"Invalid PORT: {cls.PORT}. Must be between 1024 and 65535.")

    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    def is_production(self) -> bool:
        return self.APP_ENV == "production"


# Create a global settings instance
settings = Settings()
