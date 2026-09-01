"""
Application Configuration and Settings.
"""
from typing import List, Optional
from pydantic import BaseModel
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Detect serverless environment (Vercel, AWS Lambda, etc.)
IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("SERVERLESS"))

if IS_SERVERLESS:
    DATA_DIR = Path("/tmp") / "data"
else:
    DATA_DIR = BASE_DIR / "data"

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DATA_DIR = Path("/tmp") / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = DATA_DIR / "uploads"
ENCRYPTED_STORAGE_DIR = DATA_DIR / "encrypted_storage"

try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ENCRYPTED_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


class Settings(BaseModel):
    PROJECT_NAME: str = "Personalized Healthcare AI Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "healthcare-ai-super-secret-key-2026-audit-protected-32bytes-min")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    FILE_ENCRYPTION_KEY: bytes = os.getenv("FILE_ENCRYPTION_KEY", "32bytesencryptionkeyforhealthdoc").encode("utf-8").ljust(32, b"#")[:32]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR.as_posix()}/healthcare_assistant.db")
    
    # Medical Safety & Guardrails
    CONFIDENCE_THRESHOLD_MIN: float = 0.70
    REQUIRE_USER_VERIFICATION: bool = True
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "txt"]
    
    # Emergency Triage Red Flags
    EMERGENCY_KEYWORDS: List[str] = [
        "chest pain", "crushing chest", "heart attack", "left arm pain", "radiating jaw pain",
        "difficulty breathing", "severe shortness of breath", "gasping for air", "choking",
        "stroke", "facial drooping", "slurred speech", "sudden paralysis", "arm weakness",
        "sudden loss of vision", "worst headache of my life", "thunderclap headache",
        "coughing up blood", "vomiting blood", "severe hemorrhage", "uncontrolled bleeding",
        "suicidal", "kill myself", "end my life", "anaphylaxis", "throat swelling", "blue lips",
        "unconscious", "passed out", "seizure", "unresponsive"
    ]
    
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)


settings = Settings()
