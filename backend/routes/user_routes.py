"""
Nexora Backend - User Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserRegister, UserResponse, DeviceRegister, DeviceResponse
from services.user_service import register_user, register_device, get_user_by_username

router = APIRouter(prefix="/user", tags=["user"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        return register_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/device/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_device_endpoint(
    device_data: DeviceRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _client_ip(request)
    try:
        return register_device(db, device_data, ip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{username}", response_model=UserResponse)
def get_user(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
