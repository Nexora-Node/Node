"""
Nexora Backend - Explorer Routes
Public endpoints for network explorer (no auth required).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Node, Device, User

router = APIRouter(prefix="/explorer", tags=["explorer"])


def _mask_ip(ip: str | None) -> str:
    """Mask IP: 192.168.1.100 → 192.168.***.***"""
    if not ip:
        return "***.***.***"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
    # IPv6 or unusual format
    return ip[:6] + "***"


@router.get("/nodes")
def get_active_nodes(db: Session = Depends(get_db)):
    """Return all active nodes with masked IPs — public endpoint."""
    nodes = db.query(Node).filter(Node.status == "active").order_by(Node.last_seen.desc()).all()

    result = []
    for node in nodes:
        # Get username via device → user
        device = db.query(Device).filter(Device.device_id == node.device_id).first()
        username = None
        if device:
            user = db.query(User).filter(User.id == device.user_id).first()
            if user:
                username = user.username

        result.append({
            "node_id":    node.node_id[:16] + "...",
            "username":   username or "anonymous",
            "uptime":     node.uptime,
            "last_seen":  node.last_seen.isoformat() if node.last_seen else None,
            "node_score": node.node_score,
            "ip_address": _mask_ip(node.ip_address),
            "status":     node.status,
        })

    return result


@router.get("/stats")
def get_network_stats(db: Session = Depends(get_db)):
    """Return global network stats — public endpoint."""
    total_nodes   = db.query(Node).filter(Node.status == "active").count()
    total_users   = db.query(User).count()
    total_devices = db.query(Device).count()

    # Total uptime across all active nodes
    total_uptime = db.query(func.sum(Node.uptime)).filter(Node.status == "active").scalar() or 0.0

    return {
        "active_nodes":   total_nodes,
        "total_users":    total_users,
        "total_devices":  total_devices,
        "total_uptime_hours": round(total_uptime / 3600, 2),
    }
