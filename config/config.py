import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    """Application configuration loaded from environment variables with safe defaults."""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "nutriscan_ai_default_secret_key_development_only")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))
    
    # Database Settings
    DB_HOST = os.getenv("DATABASE_HOST", "localhost")
    DB_PORT = int(os.getenv("DATABASE_PORT", 3306))
    DB_NAME = os.getenv("DATABASE_NAME", "nutriscan_ai_db")
    DB_USER = os.getenv("DATABASE_USER", "root")
    DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
    DB_SSL = os.getenv("DATABASE_SSL", "False").lower() in ("true", "1", "t", "yes")
    DB_SSL_CA = os.getenv("DATABASE_SSL_CA", "").strip()
    DB_CONNECT_TIMEOUT = int(os.getenv("DATABASE_CONNECT_TIMEOUT", 15))
    
    # Google Gemini AI Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
    
    # Upload Settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB limit
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    
    @classmethod
    def get_db_config(cls, include_db=True):
        """Returns database connection parameters dictionary for PyMySQL."""
        import ssl
        cfg = {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "charset": "utf8mb4",
            "autocommit": True,
            "connect_timeout": cls.DB_CONNECT_TIMEOUT,
        }
        if include_db:
            cfg["database"] = cls.DB_NAME

        if cls.DB_SSL:
            ctx = ssl.create_default_context()
            if cls.DB_SSL_CA and os.path.exists(cls.DB_SSL_CA):
                ctx.load_verify_locations(cafile=cls.DB_SSL_CA)
            elif os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
                ctx.load_verify_locations(cafile="/etc/ssl/certs/ca-certificates.crt")
            cfg["ssl"] = ctx

        return cfg
