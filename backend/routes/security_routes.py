"""
Nexora Backend - Security Routes
Read-only endpoints for security log inspection
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import SecurityLog
from schemas import SecurityLogResponse

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/logs", response_model=List[SecurityLogResponse])
def get_security_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent security log entries, newest first."""
    q = db.query(SecurityLog)
    if event_type:
        q = q.filter(SecurityLog.event_type == event_type)
    if ip_address:
        q = q.filter(SecurityLog.ip_address == ip_address)
    if node_id:
        q = q.filter(SecurityLog.node_id == node_id)
    return q.order_by(SecurityLog.created_at.desc()).limit(limit).all()
