"""
FastAPI main application for Local AI Helper
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yaml
from pathlib import Path

from src.api.routers import chat, memory, models
from src.memory.vector_store import VectorStore
from src.memory.conversation_db import ConversationDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "agent_configs.yaml"
with open(CONFIG_PATH, 'r') as f:
    CONFIG = yaml.safe_load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Initializing Local AI Helper API...")
    
    # Initialize database connections
    app.state.conversation_db = ConversationDB()
    await app.state.conversation_db.initialize()
    
    # Initialize vector store
    app.state.vector_store = VectorStore()
    await app.state.vector_store.initialize()
    
    logger.info("API initialization complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")
    await app.state.conversation_db.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Local AI Helper API",
    description="API for multi-mode AI assistant with persistent memory",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Local AI Helper API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_healthy = await app.state.conversation_db.health_check()
        
        # Check vector store
        vector_healthy = await app.state.vector_store.health_check()
        
        return {
            "status": "healthy" if (db_healthy and vector_healthy) else "degraded",
            "database": "healthy" if db_healthy else "unhealthy",
            "vector_store": "healthy" if vector_healthy else "unhealthy"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "agents": list(CONFIG["agents"].keys()),
        "models": CONFIG["models"]["available"],
        "default_model": CONFIG["models"]["default"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)