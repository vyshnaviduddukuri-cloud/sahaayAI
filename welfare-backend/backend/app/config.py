"""
Central configuration. Reads from environment variables (.env file),
falls back to hackathon-friendly defaults so the app runs with zero setup.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- General ---
    APP_NAME: str = "Welfare Scheme Eligibility Backend"
    ENV: str = "development"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./welfare.db"

    # --- Auth / JWT ---
    JWT_SECRET: str = "CHANGE_ME_BEFORE_DEMO_dev_only_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours, generous for a demo

    # --- Mock Aadhaar verification ---
    # Real UIDAI integration requires government empanelment. This is a
    # structurally-identical mock: same request/response shape, fixed OTP.
    MOCK_AADHAAR_OTP: str = "123456"

    # --- AI service (the teammate building extraction/rules/RAG/chat) ---
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT_SECONDS: float = 15.0

    class Config:
        env_file = ".env"


settings = Settings()
