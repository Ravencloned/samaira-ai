"""
SamairaAI Backend - FastAPI Application
Voice-first financial literacy companion for Indian families.

Production-ready with:
- Structured logging and error handling
- Request/response middleware
- Health checks with dependency status
- Graceful startup/shutdown
"""

import sys
import logging
import time
import uuid
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

# Add backend to path for imports
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import chat, voice, session
try:
    from api.routes import memory as memory_routes
    has_memory_routes = True
except ImportError:
    has_memory_routes = False

# Import bank rates API
try:
    from api.routes import banks as banks_routes
    has_banks_routes = True
except ImportError as e:
    print(f"Warning: Could not import banks routes: {e}")
    has_banks_routes = False

from config.settings import settings

# ===== LOGGING SETUP =====
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("samaira")

# ===== APPLICATION STATE =====
app_state = {
    "start_time": None,
    "request_count": 0,
    "error_count": 0,
    "llm_ready": False,
    "tts_ready": False,
    "mcp_ready": False
}


# ===== REQUEST LOGGING MIDDLEWARE =====
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and correlation IDs."""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Add request ID to state for tracing
        request.state.request_id = request_id
        app_state["request_count"] += 1
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log request (skip static files and health checks for cleaner logs)
            if not request.url.path.startswith("/static") and request.url.path != "/health":
                logger.info(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"-> {response.status_code} ({process_time:.1f}ms)"
                )
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.1f}ms"
            return response
            
        except Exception as e:
            app_state["error_count"] += 1
            logger.error(f"[{request_id}] {request.method} {request.url.path} -> ERROR: {e}")
            raise


# ===== LIFESPAN MANAGER =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # STARTUP
    logger.info("🪷 Starting SamairaAI...")
    app_state["start_time"] = datetime.now()
    
    # Validate settings
    errors = settings.validate()
    if errors:
        for err in errors:
            logger.warning(f"Config: {err}")
    
    # Initialize LLM service
    try:
        from services.llm_service import llm_service
        llm_service.initialize()
        app_state["llm_ready"] = True
        logger.info(f"✅ LLM Provider: {llm_service.provider}")
    except Exception as e:
        logger.error(f"❌ LLM init failed: {e}")
    
    # Initialize TTS service
    try:
        from services.tts_service import tts_service
        tts_service.initialize()
        app_state["tts_ready"] = True
        logger.info("✅ TTS Service: Ready")
    except Exception as e:
        logger.warning(f"⚠️ TTS init failed: {e}")
    
    # Initialize MCP memory
    try:
        from memory.mcp import mcp_memory
        app_state["mcp_ready"] = True
        logger.info("✅ MCP Memory: Ready")
    except ImportError:
        logger.warning("⚠️ MCP Memory: Not available")
    
    logger.info("🪷 SamairaAI ready to serve!")
    
    yield  # Application runs here
    
    # SHUTDOWN
    logger.info("🪷 Shutting down SamairaAI...")
    uptime = datetime.now() - app_state["start_time"]
    logger.info(f"📊 Stats: {app_state['request_count']} requests, {app_state['error_count']} errors, uptime {uptime}")


# Create FastAPI app
app = FastAPI(
    title="SamairaAI",
    description="Voice-first financial literacy companion for Indian families",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:8000", "https://samaira-ai.azurewebsites.net"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(voice.router, prefix="/api", tags=["voice"])
app.include_router(session.router, prefix="/api", tags=["session"])

# Memory routes (MCP - Model Context Protocol)
if has_memory_routes:
    app.include_router(memory_routes.router, prefix="/api", tags=["memory"])

# Bank rates and financial data API
if has_banks_routes:
    app.include_router(banks_routes.router, prefix="/api", tags=["banks"])

# Serve frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# ===== GLOBAL EXCEPTION HANDLER =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for clean error responses."""
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.error(f"[{request_id}] Unhandled error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "Something went wrong. Please try again.",
            "request_id": request_id
        }
    )


@app.get("/")
async def root():
    """Serve the frontend index.html"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "SamairaAI API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check with dependency status."""
    uptime = None
    if app_state["start_time"]:
        uptime = str(datetime.now() - app_state["start_time"])
    
    # Determine overall health
    is_healthy = app_state["llm_ready"]  # LLM is critical
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "uptime": uptime,
        "version": "1.0.0",
        "services": {
            "llm": "ready" if app_state["llm_ready"] else "unavailable",
            "tts": "ready" if app_state["tts_ready"] else "unavailable", 
            "mcp_memory": "ready" if app_state["mcp_ready"] else "unavailable"
        },
        "stats": {
            "requests": app_state["request_count"],
            "errors": app_state["error_count"]
        },
        "debug": settings.DEBUG
    }


@app.get("/api/status")
async def api_status():
    """Quick API status for frontend connection check."""
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "llm_ready": app_state["llm_ready"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
