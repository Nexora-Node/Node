"""
Nexora Backend - Database Configuration
Supports SQLite (local dev) and PostgreSQL (production via DATABASE_URL env var)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Railway injects DATABASE_URL for PostgreSQL automatically.
# Fall back to local SQLite for development.
_DATABASE_URL = os.environ.get("DATABASE_URL")

if _DATABASE_URL:
    # Railway gives postgres:// but SQLAlchemy needs postgresql://
    if _DATABASE_URL.startswith("postgres://"):
        _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(_DATABASE_URL)
else:
    _BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
    _SQLITE_PATH = os.path.join(_BACKEND_DIR, "nexora.db")
    engine = create_engine(
        f"sqlite:///{_SQLITE_PATH}",
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
