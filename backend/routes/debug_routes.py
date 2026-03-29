from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/users")
def debug_users(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT username, referral_code, referral_used FROM users")).fetchall()
    return [{"username": r[0], "ref": r[1], "used": r[2]} for r in result]

@router.get("/columns")
def debug_columns(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'")).fetchall()
    return [r[0] for r in result]
