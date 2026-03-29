"""
Nexora Backend - Points Service
Business logic for points and rewards
"""

from sqlalchemy.orm import Session
from models import User


def get_user_points(db: Session, username: str) -> dict:
    """
    Get points information for a user
    
    Args:
        db: Database session
        username: Username
    
    Returns:
        Dict with points information
    
    Raises:
        ValueError: If user not found
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("User not found")
    
    return {
        "username": user.username,
        "points": user.points,
        "total_earned": user.total_earned
    }


def claim_points(db: Session, username: str) -> dict:
    """
    Claim available points
    
    Args:
        db: Database session
        username: Username
    
    Returns:
        Dict with claim result
    
    Raises:
        ValueError: If user not found or no points to claim
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("User not found")
    
    if user.points <= 0:
        raise ValueError("No points available to claim")
    
    # Transfer points to claimed (in this simple system, we just reset points)
    # In a more complex system, you might move to a separate "claimed" field
    points_claimed = user.points
    user.points = 0.0
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully claimed {points_claimed:.2f} points",
        "points_claimed": points_claimed
    }
