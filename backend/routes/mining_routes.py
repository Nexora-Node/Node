"""
Nexora Backend - Mining Info Routes
Public endpoint for halving/rate info.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.mining_rate_service import get_mining_info

router = APIRouter(prefix="/mining", tags=["mining"])


@router.get("/info")
def mining_info(db: Session = Depends(get_db)):
    """
    Returns current mining rate, epoch, halving schedule, and supply stats.
    """
    return get_mining_info(db)
