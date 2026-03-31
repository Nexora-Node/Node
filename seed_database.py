#!/usr/bin/env python3
"""
Nexora Database Seed Script
Creates the initial admin user with a random referral code.
"""

import sys
import os

# Always use the backend folder so database.py resolves the correct DB path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from database import SessionLocal, engine
from models import Base, User
import secrets
import string


def random_referral_code(length: int = 8) -> str:
    """Generate a random uppercase alphanumeric code with no sequential pattern."""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def seed():
    print("=" * 50)
    print("NEXORA DATABASE SEED")
    print("=" * 50)

    print("\nInitializing database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print(f"\n✓ Seed user already exists")
            print(f"  Username    : {existing.username}")
            print(f"  Referral Code: {existing.referral_code}")
            return

        code = random_referral_code()
        # Ensure uniqueness (extremely unlikely collision, but be safe)
        while db.query(User).filter(User.referral_code == code).first():
            code = random_referral_code()

        admin = User(
            username="admin",
            referral_code=code,
            invited_by=None,
            tokens=0.0,
            claimed_tokens=0.0,
            total_earned=0.0,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\n✓ Seed user created!")
        print(f"  Username    : {admin.username}")
        print(f"  Referral Code: {admin.referral_code}")
        print(f"\nRegister your first user with:")
        print(f"  python cli/main.py register --ref {admin.referral_code}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
