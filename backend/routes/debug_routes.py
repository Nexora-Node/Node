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

@router.post("/move-device")
def move_device(db: Session = Depends(get_db)):
    """Move device f58ed4e8 to Danixyz"""
    from models import User, Device
    from sqlalchemy import text
    danixyz = db.query(User).filter(User.username == 'Danixyz').first()
    device = db.query(Device).filter(Device.device_id == 'f58ed4e839ff3dccbce111a01ec66eaf').first()
    if not danixyz:
        return {"error": "Danixyz not found"}
    if not device:
        return {"error": "Device not found"}
    device.user_id = danixyz.id
    db.commit()
    return {"status": "moved", "device_user_id": device.user_id, "danixyz_id": danixyz.id}
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
