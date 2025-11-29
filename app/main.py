from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.api.multi_collection_routes import router as multi_collection_router
from app.services.multi_collection_db_service import multi_collection_db_service
from credit_card_app.api.credit_card_routes import router as cc_router
from credit_card_app.services.database_service import cc_db_service
from app.config import settings
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting up MongoDB Query AI application...")
    cc_db_service.connect()
    yield
    # Shutdown
    logger.info("Shutting down...")
    cc_db_service.close()


app = FastAPI(
    title="MongoDB Query AI",
    description="Convert natural language to MongoDB queries using AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(multi_collection_router, prefix="/api", tags=["Notifications - Multi-Collection"])
app.include_router(cc_router, prefix="/credit-card/api", tags=["Credit Card"])

# Mount static files
static_path = Path(__file__).parent.parent / "static"
cc_static_path = Path(__file__).parent.parent / "credit_card_app" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
app.mount("/credit-card/static", StaticFiles(directory=str(cc_static_path)), name="cc_static")


@app.get("/")
async def root():
    """Serve the web UI"""
    return FileResponse(str(static_path / "index.html"))


@app.get("/credit-card")
async def credit_card_ui():
    """Serve the Credit Card Analyzer UI"""
    return FileResponse(str(cc_static_path / "index.html"))


@app.get("/api")
async def api_root():
    """API information endpoint"""
    return {
        "message": "MongoDB Query AI Platform",
        "version": "2.0.0",
        "docs": "/docs",
        "applications": {
            "notification_queries": {
                "description": "Multi-collection notification system",
                "documentation": "/MULTI_COLLECTION_ARCHITECTURE.md",
                "endpoints": {
                    "query": "/api/v2/query",
                    "dashboard": "/api/v2/dashboard",
                    "event_details": "/api/v2/event/{event_tracking_id}",
                    "events_with_channels": "/api/v2/events/with-channels",
                    "channel_stats": "/api/v2/stats/channel/{channel_name}",
                    "event_name_stats": "/api/v2/stats/event-name",
                    "event_name_breakdown": "/api/v2/stats/event-name/{event_name}",
                    "schema": "/api/v2/schema",
                    "health": "/api/v2/health"
                },
                "features": [
                    "Primary collection (notification_events)",
                    "Channel collections (email, sms, push, in-app)",
                    "Cross-collection queries with $lookup",
                    "Event-level and channel-level tracking",
                    "Comprehensive dashboard with analytics",
                    "Event name-based analytics and filtering"
                ]
            },
            "credit_card_analyzer": {
                "description": "Credit card transaction analyzer",
                "ui": "/credit-card",
                "endpoints": {
                    "query": "/credit-card/api/query",
                    "analyze": "/credit-card/api/analyze",
                    "stats": "/credit-card/api/stats",
                    "schema": "/credit-card/api/schema",
                    "health": "/credit-card/api/health"
                }
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
