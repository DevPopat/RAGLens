"""FastAPI application entry point."""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db.database import engine, Base

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with timing information."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[{request_id}] {response.status_code} in {duration_ms:.0f}ms")
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Failed after {duration_ms:.0f}ms: {e}", exc_info=True)
            raise


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

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


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


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """Catch-all exception handler for unhandled errors."""
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Unhandled exception [{error_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "error_id": error_id}
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(_request: Request, exc: SQLAlchemyError):
    """Handle database errors with detailed logging."""
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Database error [{error_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Database error", "error_id": error_id}
    )


# Import and include routers
from app.api.routes import chat, evaluation, golden_set, diagnosis

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(golden_set.router, prefix="/api/golden-set", tags=["golden-set"])
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["diagnosis"])
