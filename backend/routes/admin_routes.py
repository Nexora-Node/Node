"""
Nexora Backend - Admin Routes
Protected endpoints for system management.
"""

import os
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from database import get_db
from models import SystemReferral

router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")


def verify_admin(x_admin_secret: str = Header(...)):
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def _gen_code(db: Session, length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        if not db.query(SystemReferral).filter(SystemReferral.code == code).first():
            return code


@router.post("/referrals/generate")
def generate_system_referrals(
    count: int = 50,
    db: Session = Depends(get_db),
    x_admin_secret: str = Header(...),
):
    """Generate N system referral codes not tied to any user."""
    verify_admin(x_admin_secret)
    codes = []
    for _ in range(count):
        code = _gen_code(db)
        ref = SystemReferral(code=code)
        db.add(ref)
        codes.append(code)
    db.commit()
    return {"generated": len(codes), "codes": codes}


@router.get("/referrals/unused")
def list_unused_referrals(
    db: Session = Depends(get_db),
    x_admin_secret: str = Header(...),
):
    """List all unused system referral codes."""
    verify_admin(x_admin_secret)
    refs = db.query(SystemReferral).filter(SystemReferral.used == False).all()
    return {"count": len(refs), "codes": [r.code for r in refs]}
