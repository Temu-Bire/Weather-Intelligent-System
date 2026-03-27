# src/api/weather_routes.py

from aiohttp import web
from typing import Dict

from ..services.weather_service import weather_service
from ..models.weather_model import WeatherIntelligence


async def get_weather_handler(request: web.Request) -> web.Response:
    """GET /api/weather?city=Addis%20Ababa"""
    city = request.query.get("city", "Addis Ababa").strip()
    
    if not city:
        return web.json_response({"error": "City parameter is required"}, status=400)
    
    try:
        intelligence: WeatherIntelligence = await weather_service.get_intelligent_weather(city)
        
        return web.json_response(
            intelligence.model_dump(mode="json"),
            status=200
        )
        
    except Exception as e:
        return web.json_response(
            {"error": f"Failed to fetch weather for {city}", "detail": str(e)},
            status=500
        )


async def get_current_weather_handler(request: web.Request) -> web.Response:
    """GET /api/weather/current?city=Addis%20Ababa"""
    city = request.query.get("city", "Addis Ababa").strip()
    
    if not city:
        return web.json_response({"error": "City parameter is required"}, status=400)
    
    try:
        intelligence = await weather_service.get_current_only(city)
        
        return web.json_response(
            intelligence.model_dump(mode="json"),
            status=200
        )
        
    except Exception as e:
        return web.json_response(
            {"error": f"Failed to fetch current weather for {city}", "detail": str(e)},
            status=500
        )


async def health_check_handler(request: web.Request) -> web.Response:
    """GET /api/health"""
    return web.json_response(weather_service.health_check())


def setup_routes(app: web.Application):
    """Register all weather-related routes"""
    app.router.add_get('/api/weather', get_weather_handler)
    app.router.add_get('/api/weather/current', get_current_weather_handler)
    app.router.add_get('/api/health', health_check_handler)
    
    # Optional: Add more routes later
    # app.router.add_get('/api/weather/forecast', get_forecast_handler)