"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import engine, Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting RAGLens application...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down RAGLens application...")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="RAGLens API",
    description="Customer service chatbot RAG evaluation platform",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "raglens-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RAGLens API",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers
from app.api.routes import chat

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# To be added in later phases:
# from app.api.routes import evaluation, golden_set, metrics
# app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
# app.include_router(golden_set.router, prefix="/api/golden-set", tags=["golden-set"])
# app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
