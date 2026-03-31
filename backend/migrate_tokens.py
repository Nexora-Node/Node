"""
Migration: ensure tokens schema is up to date.
- If 'points' column exists → rename to tokens (PostgreSQL)
- If neither exists → add tokens column fresh
- Add claimed_tokens, last_claim_at if missing
- Create mining_config table
Run: python backend/migrate_tokens.py
"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from database import engine
from sqlalchemy import text, inspect

def col_exists(conn, table, column):
    try:
        conn.execute(text(f"SELECT {column} FROM {table} LIMIT 1"))
        return True
    except Exception:
        return False

def migrate():
    db_url = os.environ.get("DATABASE_URL", "")
    is_postgres = "postgresql" in db_url or "postgres" in db_url

    with engine.connect() as conn:
        has_tokens = col_exists(conn, "users", "tokens")
        has_points = col_exists(conn, "users", "points")

        if has_tokens:
            print("✓ 'tokens' column already exists.")
        elif has_points and is_postgres:
            print("Renaming 'points' → 'tokens' ...")
            conn.execute(text("ALTER TABLE users RENAME COLUMN points TO tokens"))
            conn.commit()
            print("✓ Renamed.")
        elif has_points:
            # SQLite
            print("Adding 'tokens' column (SQLite) ...")
            conn.execute(text("ALTER TABLE users ADD COLUMN tokens FLOAT DEFAULT 0.0"))
            conn.execute(text("UPDATE users SET tokens = points"))
            conn.commit()
            print("✓ Done.")
        else:
            print("Adding 'tokens' column fresh ...")
            if is_postgres:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS tokens FLOAT DEFAULT 0.0"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN tokens FLOAT DEFAULT 0.0"))
            conn.commit()
            print("✓ Done.")

        # claimed_tokens
        if not col_exists(conn, "users", "claimed_tokens"):
            print("Adding 'claimed_tokens' ...")
            if is_postgres:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS claimed_tokens FLOAT DEFAULT 0.0"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN claimed_tokens FLOAT DEFAULT 0.0"))
            conn.commit()
            print("✓ Done.")
        else:
            print("✓ 'claimed_tokens' already exists.")

        # last_claim_at
        if not col_exists(conn, "users", "last_claim_at"):
            print("Adding 'last_claim_at' ...")
            if is_postgres:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_claim_at TIMESTAMP"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_claim_at TIMESTAMP"))
            conn.commit()
            print("✓ Done.")
        else:
            print("✓ 'last_claim_at' already exists.")

    # Create all missing tables (mining_config, etc.)
    import models  # noqa
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("✓ All tables ensured.")
    print("\nMigration complete.")

if __name__ == "__main__":
    migrate()
