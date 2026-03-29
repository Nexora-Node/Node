"""
Nexora Backend - Points Routes
API endpoints for points and rewards
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import PointsResponse, ClaimRequest, ClaimResponse
from services.points_service import get_user_points, claim_points

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/{username}", response_model=PointsResponse)
def get_points(username: str, db: Session = Depends(get_db)):
    """
    Get points information for a user
    
    - **username**: Username
    """
    try:
        points_info = get_user_points(db, username)
        return points_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/claim", response_model=ClaimResponse)
def claim_points_endpoint(claim_data: ClaimRequest, db: Session = Depends(get_db)):
    """
    Claim available points
    
    - **username**: Username
    """
    try:
        result = claim_points(db, claim_data.username)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
