"""
Nexora Backend - Database Configuration
Supports SQLite (local dev) and PostgreSQL (production via DATABASE_URL env var)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DATABASE_URL = os.environ.get("DATABASE_URL")

if _DATABASE_URL:
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


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
