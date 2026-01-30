"""
FastAPI application for DS-Playbook GraphRAG system

FSD 2.1 App Layer - 앱 초기화 및 설정
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app import dependencies
from src.features.chat.api import routes as chat_routes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DS-Playbook GraphRAG API",
    description="Knowledge graph exploration and analysis API",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        dependencies.init_dependencies()
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# Register routers
# Override chat router's DI function
app.dependency_overrides[chat_routes.get_chat_service] = dependencies.get_chat_service
app.include_router(chat_routes.router)


# Root endpoints
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "DS-Playbook GraphRAG API",
        "version": "2.0.0",
        "architecture": "FSD 2.1",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "chat": "/api/chat"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        supabase_loader = dependencies.get_supabase_loader()
        result = supabase_loader.client.table('playbook_semantic_terms')\
            .select("id")\
            .limit(1)\
            .execute()

        return {
            "status": "healthy",
            "database": "connected",
            "architecture": "FSD 2.1"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
