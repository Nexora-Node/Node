"""
Nexora Backend - User Service
"""

import secrets
import string
from sqlalchemy.orm import Session
from models import User, Device
from schemas import UserRegister, DeviceRegister
from services.anti_cheat_service import log_security_event


def _unique_referral_code(db: Session, length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(chars) for _ in range(length))
        if not db.query(User).filter(User.referral_code == code).first():
            return code


def register_user(db: Session, user_data: UserRegister) -> User:
    # v2 — referral single-use
    if db.query(User).filter(User.username == user_data.username).first():
        raise ValueError("Username already exists.")

    inviter = db.query(User).filter(User.referral_code == user_data.referral_code).first()
    if not inviter:
        raise ValueError("Invalid referral code.")

    # Referral code hanya boleh dipakai sekali
    if inviter.referral_used:
        raise ValueError("Referral code has already been used.")

    new_user = User(
        username=user_data.username,
        referral_code=_unique_referral_code(db),
        invited_by=user_data.referral_code,
        points=0.0,
        total_earned=0.0,
    )
    db.add(new_user)

    # Tandai referral code inviter sebagai sudah dipakai
    inviter.referral_used = True

    db.commit()
    db.refresh(new_user)
    return new_user


def register_device(db: Session, device_data: DeviceRegister, ip_address: str) -> Device:
    # Reject duplicate device_id
    if db.query(Device).filter(Device.device_id == device_data.device_id).first():
        raise ValueError("Device already registered.")

    # Reject duplicate fingerprint — prevents cloned/spoofed devices
    if db.query(Device).filter(Device.device_fingerprint == device_data.device_fingerprint).first():
        log_security_event(
            db, "duplicate_fingerprint",
            device_id=device_data.device_id,
            ip_address=ip_address,
            details={"fingerprint": device_data.device_fingerprint},
        )
        raise ValueError("Device fingerprint already registered.")

    # Validate user exists
    if not db.query(User).filter(User.id == device_data.user_id).first():
        raise ValueError("User not found.")

    new_device = Device(
        device_id=device_data.device_id,
        device_fingerprint=device_data.device_fingerprint,
        user_id=device_data.user_id,
        ip_address=ip_address,
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()
