from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/users")
def debug_users(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT username, referral_code, referral_used FROM users")).fetchall()
        return [{"username": r[0], "ref": r[1], "used": r[2]} for r in result]
    except Exception as e:
        return {"error": str(e)}


@router.post("/seed")
def debug_seed(db: Session = Depends(get_db)):
    import secrets, string
    from models import User
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return {"status": "already exists", "referral_code": existing.referral_code}
    chars = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(chars) for _ in range(8))
    admin = User(username="admin", referral_code=code, invited_by=None,
                 referral_used=False, points=0.0, total_earned=0.0)
    db.add(admin)
    db.commit()
    return {"status": "seeded", "referral_code": code}


@router.post("/fix-device")
def fix_device(username: str = Query(...), db: Session = Depends(get_db)):
    from models import User, Device
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"error": f"User {username} not found"}
    device = db.query(Device).filter(
        Device.device_id == "f58ed4e839ff3dccbce111a01ec66eaf"
    ).first()
    if not device:
        return {"error": "Device not found"}
    device.user_id = user.id
    db.commit()
    return {"status": "moved", "username": username, "user_id": user.id}
