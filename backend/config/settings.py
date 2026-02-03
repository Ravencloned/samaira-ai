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
    
    # LLM Provider: "groq" (recommended, free) or "gemini"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    
    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    
    # TTS Provider: "elevenlabs" (natural) or "browser" (fallback)
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "elevenlabs")
    
    # Session
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    PROMPTS_DIR: Path = BASE_DIR / "prompts"
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required settings. Returns list of errors."""
        errors = []
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set")
        return errors


settings = Settings()
