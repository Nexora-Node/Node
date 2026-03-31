"""
Migration: ensure all schema changes are applied.
Run: python backend/migrate_tokens.py
"""
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from sqlalchemy import text
from database import engine

def col_exists(conn, table, col):
    try:
        conn.execute(text(f"SELECT {col} FROM {col} LIMIT 0"))
        return True
    except Exception:
        pass
    try:
        conn.execute(text(f"SELECT {col} FROM {table} LIMIT 0"))
        return True
    except Exception:
        return False

def add_col(conn, table, col, coltype, is_postgres):
    if col_exists(conn, table, col):
        print(f"  [skip] {table}.{col} already exists")
        return
    print(f"  [add]  {table}.{col} {coltype}")
    if is_postgres:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {coltype}"))
    else:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}"))
    conn.commit()

def migrate():
    db_url = os.environ.get("DATABASE_URL", "")
    is_pg  = "postgresql" in db_url or "postgres" in db_url
    print(f"DB: {'PostgreSQL' if is_pg else 'SQLite'}")

    with engine.connect() as conn:
        # users table
        if col_exists(conn, "users", "points") and not col_exists(conn, "users", "tokens"):
            print("  [rename] users.points -> tokens")
            if is_pg:
                conn.execute(text("ALTER TABLE users RENAME COLUMN points TO tokens"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN tokens FLOAT DEFAULT 0.0"))
                conn.execute(text("UPDATE users SET tokens = points"))
            conn.commit()

        add_col(conn, "users", "tokens",        "FLOAT DEFAULT 0.0",  is_pg)
        add_col(conn, "users", "claimed_tokens", "FLOAT DEFAULT 0.0", is_pg)
        add_col(conn, "users", "last_claim_at",  "TIMESTAMP",         is_pg)

    # Create any missing tables (mining_config etc.)
    import models  # noqa
    from database import Base
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
