"""
Application configuration settings loaded from environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Settings:
    """Application settings container."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")  # Free LLM API
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")  # Natural TTS
    
    # Azure Speech (best quality for Hinglish)
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "centralindia")
    
    # LLM Provider: "groq" (recommended, free) or "gemini"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    
    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    
    # TTS Provider: "azure" (best Hinglish), "elevenlabs" (natural) or "browser" (fallback)
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "azure")
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # MCP Memory
    MCP_ENABLED: bool = os.getenv("MCP_ENABLED", "true").lower() == "true"
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    PROMPTS_DIR: Path = BASE_DIR / "prompts"
    DATA_DIR: Path = BASE_DIR / "data"  # For SQLite memory storage
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required settings. Returns list of errors."""
        errors = []
        
        # At least one LLM must be configured
        if not cls.GEMINI_API_KEY and not cls.GROQ_API_KEY:
            errors.append("No LLM API key configured (need GEMINI_API_KEY or GROQ_API_KEY)")
        
        # Warn if no TTS configured (but browser fallback works)
        if not cls.AZURE_SPEECH_KEY and not cls.ELEVENLABS_API_KEY:
            errors.append("No TTS API key configured (using browser fallback)")
        
        return errors


settings = Settings()
