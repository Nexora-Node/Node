"""
Migration: rename points -> tokens, add claimed_tokens, last_claim_at
Run once: python backend/migrate_tokens.py
"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        # Check if 'tokens' column already exists (migration already ran)
        try:
            conn.execute(text("SELECT tokens FROM users LIMIT 1"))
            print("Migration already applied. Skipping.")
            return
        except Exception:
            pass

        print("Applying migration: points -> tokens ...")

        db_url = os.environ.get("DATABASE_URL", "")
        is_postgres = "postgresql" in db_url or "postgres" in db_url

        if is_postgres:
            conn.execute(text("ALTER TABLE users RENAME COLUMN points TO tokens"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS claimed_tokens FLOAT DEFAULT 0.0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_claim_at TIMESTAMP"))
        else:
            # SQLite fallback
            conn.execute(text("ALTER TABLE users ADD COLUMN tokens FLOAT DEFAULT 0.0"))
            conn.execute(text("UPDATE users SET tokens = points"))
            conn.execute(text("ALTER TABLE users ADD COLUMN claimed_tokens FLOAT DEFAULT 0.0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN last_claim_at TIMESTAMP"))

        conn.commit()
        print("Migration complete.")

    # Create mining_config table if not exists (handled by SQLAlchemy create_all in main.py)
    # But run it here too for safety
    import models  # noqa
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("Tables ensured (including mining_config).")

if __name__ == "__main__":
    migrate()
