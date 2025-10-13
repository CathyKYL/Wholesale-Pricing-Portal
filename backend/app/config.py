"""
Configuration Management
------------------------
Purpose:
- Centralize all configuration settings
- Support both local and cloud environments
- Make switching between environments seamless
- Provide sensible defaults and validation

Usage:
    from config import settings
    
    # Access configuration
    print(settings.DATABASE_URL)
    print(settings.ENVIRONMENT)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows us to override settings locally
load_dotenv()


class Settings:
    """
    Application Settings
    --------------------
    This class holds all configuration for the application.
    
    Environment variables can be set in:
    - .env file (for local development)
    - Cloud platform environment variables (for production)
    
    The same code works in both environments!
    """
    
    # ========== ENVIRONMENT ==========
    # Determines which environment we're running in
    # Options: "development", "staging", "production"
    # Default: "development" for local work
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # ========== DATABASE CONFIGURATION ==========
    # PostgreSQL connection string
    # Local format: postgresql://user:password@localhost:5432/dbname
    # Cloud format: postgresql://user:password@cloud-host.com:5432/dbname
    # Most cloud services (Railway, Render, Supabase) provide this URL automatically
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Validate DATABASE_URL exists
    if not DATABASE_URL:
        raise ValueError(
            "❌ ERROR: DATABASE_URL not found in environment variables.\n"
            "→ For local: Set in .env file\n"
            "→ For cloud: Set in platform's environment variables"
        )
    
    # Fix for Heroku/some cloud providers that use 'postgres://' instead of 'postgresql://'
    # SQLAlchemy requires 'postgresql://' prefix
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # ========== API KEYS ==========
    # Keepa API key for Amazon price tracking
    # Get your key from: https://keepa.com/#!api
    KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")
    
    # ========== FILE PATHS ==========
    # Excel file path - flexible to work both locally and in cloud
    # Local: Can be absolute path or relative to project root
    # Cloud: Should be in a persistent storage or uploaded via API
    EXCEL_PATH = os.getenv("EXCEL_PATH")
    
    # If EXCEL_PATH is not absolute, make it relative to project root
    if EXCEL_PATH and not os.path.isabs(EXCEL_PATH):
        # Get the project root (2 levels up from this file)
        # config.py is in backend/app/, so go up to project root
        project_root = Path(__file__).parent.parent.parent
        EXCEL_PATH = str(project_root / EXCEL_PATH)
    
    # ========== CORS CONFIGURATION ==========
    # CORS (Cross-Origin Resource Sharing) allows frontend to call backend API
    # This is CRITICAL for Netlify frontend → Cloud backend communication
    
    # Allowed origins for CORS (websites that can call our API)
    # Local development: http://localhost:3000, http://localhost:5173, etc.
    # Production: your Netlify domain
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        # Default allows common local development ports
        "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000"
    ).split(",")
    
    # In production, add your Netlify domain
    # Example: "https://your-app.netlify.app"
    if ENVIRONMENT == "production":
        # Get production frontend URL from environment
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url not in CORS_ORIGINS:
            CORS_ORIGINS.append(frontend_url)
    
    # ========== API CONFIGURATION ==========
    # API settings
    API_VERSION = "v1"
    API_TITLE = "Wholesale Pricing Portal API"
    API_DESCRIPTION = "API for managing wholesale book pricing and Amazon data"
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 1000
    
    # ========== SECURITY ==========
    # Secret key for JWT tokens (if we add authentication later)
    # IMPORTANT: Generate a strong random key for production!
    # You can generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_STRING"
    )
    
    # ========== LOGGING ==========
    # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # ========== CLOUD PLATFORM DETECTION ==========
    # Automatically detect which cloud platform we're running on
    # This can be useful for platform-specific configurations
    
    @staticmethod
    def is_heroku():
        """Check if running on Heroku"""
        return os.getenv("DYNO") is not None
    
    @staticmethod
    def is_railway():
        """Check if running on Railway"""
        return os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    @staticmethod
    def is_render():
        """Check if running on Render"""
        return os.getenv("RENDER") is not None
    
    @staticmethod
    def is_cloud():
        """Check if running in any cloud environment"""
        return (
            Settings.is_heroku() or
            Settings.is_railway() or
            Settings.is_render() or
            os.getenv("ENVIRONMENT") == "production"
        )
    
    # ========== HELPER METHODS ==========
    
    @staticmethod
    def get_database_config():
        """
        Get database configuration dictionary
        Useful for debugging and logging
        """
        return {
            "environment": Settings.ENVIRONMENT,
            "database_url": Settings.DATABASE_URL.split("@")[1] if "@" in Settings.DATABASE_URL else "not set",
            "is_cloud": Settings.is_cloud(),
        }
    
    @staticmethod
    def validate():
        """
        Validate all required settings are present
        Call this at startup to catch configuration errors early
        """
        errors = []
        
        if not Settings.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        if Settings.ENVIRONMENT == "production" and Settings.SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION_USE_RANDOM_STRING":
            errors.append("SECRET_KEY must be changed in production")
        
        if errors:
            raise ValueError(
                "❌ Configuration errors:\n" +
                "\n".join(f"  - {error}" for error in errors)
            )
        
        return True


# Create a singleton instance
# This allows importing settings throughout the app
settings = Settings()

# Validate settings on import (fail fast if misconfigured)
# Comment this out if you want to delay validation
# settings.validate()

