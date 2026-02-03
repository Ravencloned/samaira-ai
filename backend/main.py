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
    print("🚀 Starting SamairaAI...")
    
    # Validate settings
    errors = settings.validate()
    if errors:
        print(f"⚠️ Configuration warnings: {errors}")
    
    # Initialize Gemini client (lazy loading)
    from services.gemini_client import gemini_client
    try:
        gemini_client.initialize()
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"⚠️ Gemini client initialization failed: {e}")
    
    print("✅ SamairaAI ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down SamairaAI...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
