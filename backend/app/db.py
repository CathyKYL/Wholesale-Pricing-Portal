"""
Database Bootstrap and Connection Management
--------------------------------------------
Purpose:
- Initialize database connection using SQLAlchemy
- Read credentials from .env file (never hardcoded)
- Provide session factory for database operations
- Create tables if they don't exist (idempotent operation)

Usage:
    from db import init_db, SessionLocal
    
    # Initialize tables (safe to call multiple times)
    init_db()
    
    # Get a database session for queries/inserts
    with SessionLocal() as session:
        # Your database operations here
        pass
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the Base class from models
# This contains metadata about all our tables
from models import Base

# Import centralized configuration
# This works seamlessly in both local and cloud environments
from config import settings

# Get database connection string from centralized config
# The config module handles environment variables and cloud platform differences
# This same code works locally and in production!
DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy engine
# This manages the connection pool to PostgreSQL
# echo=False means don't print all SQL queries (set to True for debugging)
# future=True enables SQLAlchemy 2.0 style (recommended)
engine = create_engine(DATABASE_URL, echo=False, future=True)

# Create a session factory
# SessionLocal() will create new database sessions
# autocommit=False means we control when to commit transactions
# autoflush=False means we control when to flush changes to DB
# bind=engine connects sessions to our PostgreSQL database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize Database Tables
    --------------------------
    This function creates all tables defined in models.py if they don't exist.
    
    How it works:
    1. Reads all model definitions from Base.metadata
    2. Generates CREATE TABLE statements for each model
    3. Executes them on PostgreSQL (skips if table already exists)
    
    Safe to call multiple times - it's idempotent.
    Won't drop or modify existing tables.
    """
    
    # Create all tables defined in our models
    # This looks at all classes that inherit from Base (e.g., CatalogRow)
    # and creates corresponding tables in PostgreSQL
    Base.metadata.create_all(bind=engine)
    
    # Print success message
    print("✅ Tables created (or already exist).")


def get_db():
    """
    Get Database Session (for dependency injection)
    -----------------------------------------------
    This function provides a database session and ensures it's closed properly.
    Typically used with FastAPI's dependency injection system.
    
    Usage with FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(CatalogRow).all()
    
    Yields:
        Session: A SQLAlchemy database session
    """
    
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Yield the session to the caller
        # This allows the caller to use it in their function
        yield db
    finally:
        # Always close the session when done
        # This happens even if there's an error
        # Ensures connections are returned to the pool
        db.close()

