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

@router.post("/seed")
def debug_seed(db: Session = Depends(get_db)):
    import secrets, string
    from models import User
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return {"status": "already exists", "referral_code": existing.referral_code}
    chars = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(chars) for _ in range(8))
    admin = User(username="admin", referral_code=code, invited_by=None, referral_used=False, points=0.0, total_earned=0.0)
    db.add(admin)
    db.commit()
    return {"status": "seeded", "referral_code": code}
