"""
Migration: ensure all schema changes are applied.
Run: python backend/migrate_tokens.py
"""
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from sqlalchemy import text, inspect
from database import engine

def migrate():
    db_url = os.environ.get("DATABASE_URL", "")
    is_pg  = "postgresql" in db_url or "postgres" in db_url
    print(f"DB: {'PostgreSQL' if is_pg else 'SQLite'}")

    insp = inspect(engine)

    # Get existing columns in users table
    try:
        existing_cols = {c["name"] for c in insp.get_columns("users")}
        print(f"Existing users columns: {existing_cols}")
    except Exception as e:
        print(f"Cannot inspect users table: {e}")
        existing_cols = set()

    with engine.connect() as conn:
        # Rename points -> tokens (PostgreSQL only)
        if "points" in existing_cols and "tokens" not in existing_cols:
            print("Renaming points -> tokens...")
            if is_pg:
                conn.execute(text("ALTER TABLE users RENAME COLUMN points TO tokens"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN tokens FLOAT DEFAULT 0.0"))
                conn.execute(text("UPDATE users SET tokens = points"))
            conn.commit()
            existing_cols.add("tokens")
            existing_cols.discard("points")

        # Add tokens if missing
        if "tokens" not in existing_cols:
            print("Adding tokens column...")
            if is_pg:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS tokens FLOAT DEFAULT 0.0"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN tokens FLOAT DEFAULT 0.0"))
            conn.commit()

        # Add claimed_tokens if missing
        if "claimed_tokens" not in existing_cols:
            print("Adding claimed_tokens column...")
            if is_pg:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS claimed_tokens FLOAT DEFAULT 0.0"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN claimed_tokens FLOAT DEFAULT 0.0"))
            conn.commit()

        # Add last_claim_at if missing
        if "last_claim_at" not in existing_cols:
            print("Adding last_claim_at column...")
            if is_pg:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_claim_at TIMESTAMP"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_claim_at TIMESTAMP"))
            conn.commit()

    # Create any missing tables
    import models  # noqa
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
