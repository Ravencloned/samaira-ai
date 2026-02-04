"""
SamairaAI Backend - FastAPI Application
Voice-first financial literacy companion for Indian families.
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

# Create FastAPI app
app = FastAPI(
    title="SamairaAI",
    description="Voice-first financial literacy companion for Indian families",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for prototype
    allow_credentials=True,
    allow_methods=["*"],
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


@app.get("/")
async def root():
    """Serve the frontend index.html"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "SamairaAI API",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    errors = settings.validate()
    return {
        "status": "healthy" if not errors else "unhealthy",
        "errors": errors,
        "debug": settings.DEBUG
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("[STARTUP] Starting SamairaAI...")
    
    # Validate settings
    errors = settings.validate()
    if errors:
        print(f"[WARNING] Configuration warnings: {errors}")
    
    # Initialize LLM service (handles provider selection + MCP memory)
    from services.llm_service import llm_service
    try:
        llm_service.initialize()
    except Exception as e:
        print(f"[WARNING] LLM service initialization failed: {e}")
    
    # Initialize TTS service (handles Edge/Azure/ElevenLabs/Browser)
    from services.tts_service import tts_service
    try:
        tts_service.initialize()
    except Exception as e:
        print(f"[WARNING] TTS service initialization failed: {e}")
    
    # Initialize MCP memory
    try:
        from memory.mcp import mcp_memory
        print("[OK] MCP Memory: Ready")
    except ImportError:
        print("[WARNING] MCP Memory not available")
    
    print("[OK] SamairaAI ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("[SHUTDOWN] Shutting down SamairaAI...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
