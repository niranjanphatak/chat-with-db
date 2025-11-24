from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.services.database import db_service
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
    db_service.connect()
    cc_db_service.connect()
    yield
    # Shutdown
    logger.info("Shutting down...")
    db_service.close()
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
app.include_router(router, prefix="/api/v1", tags=["queries"])
app.include_router(cc_router, prefix="/credit-card/api", tags=["credit-card"])

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
        "version": "1.0.0",
        "docs": "/docs",
        "applications": {
            "notification_queries": {
                "ui": "/",
                "endpoints": {
                    "query": "/api/v1/query",
                    "aggregation": "/api/v1/aggregation",
                    "report": "/api/v1/report",
                    "schema": "/api/v1/schema",
                    "stats": "/api/v1/stats",
                    "health": "/api/v1/health"
                }
            },
            "credit_card_analyzer": {
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
