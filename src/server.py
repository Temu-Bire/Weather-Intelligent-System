# src/server.py - Updated with CORS

import asyncio
import logging
import os
from aiohttp import web
import aiohttp_cors

from .config import settings
from .api.weather_routes import setup_routes
from .db.database import init_db, close_db

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    app = web.Application()
# Serve frontend static files
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    app.router.add_static('/static/', path=frontend_path, name='static')
    # Main page
    async def index_handler(request):
        return web.FileResponse(os.path.join(frontend_path, 'index.html'))
    
    app.router.add_get('/', index_handler)
    # Setup routes
    setup_routes(app)
    
    # Add health check
    async def health_handler(request):
        return web.json_response({
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        })
    
    app.router.add_get('/health', health_handler)
    
    # =============== ADD CORS ===============
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    # Apply CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)
    # =======================================

    return app


async def main():
    logger.info("Starting Weather Intelligent Application...")
    
    await init_db()
    
    app = create_app()
    
    async def on_cleanup(app):
        await close_db()
        logger.info("Database connection closed.")

    app.on_cleanup.append(on_cleanup)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, settings.HOST, settings.PORT)
    await site.start()
    
    logger.info(f"✅ Server is running at http://127.0.0.1:{settings.PORT}")
    logger.info("Press Ctrl + C to stop the server")
    
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")