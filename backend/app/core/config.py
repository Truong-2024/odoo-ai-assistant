# backend/app/core/config.py
from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

class Settings(BaseSettings):
    """
    Cấu hình ứng dụng Odoo AI Assistant v2.0
    """
    # Odoo Configuration
    ODOO_HOST: str = os.getenv("ODOO_HOST", "localhost")
    ODOO_PORT: int = int(os.getenv("ODOO_PORT", 8069))
    ODOO_DB: str = os.getenv("ODOO_DB")
    ODOO_USER: str = os.getenv("ODOO_USER")
    ODOO_PASSWORD: str = os.getenv("ODOO_PASSWORD")

    # Database
    POSTGRES_CHECKPOINT_URI: str = os.getenv("POSTGRES_CHECKPOINT_URI")
    POSTGRES_VECTOR_URI: str = os.getenv("POSTGRES_VECTOR_URI")

    # AI / LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")

    # Tesseract OCR
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

    # Application
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Singleton instance
settings = Settings()

print(f"✅ Config loaded successfully | Environment: {settings.ENVIRONMENT}")