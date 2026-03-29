"""
Nexora Backend - Node Service
Business logic for node operations with full anti-cheat integration
"""

import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from models import Node, Device, User
from schemas import NodeRegister
from services.anti_cheat_service import (
    generate_node_token,
    validate_node_token,
    check_ip_limit,
    increment_ip_tracker,
    decrement_ip_tracker,
    check_rate_limit,
    is_suspicious,
    calculate_node_score,
    is_node_suspended,
    reward_multiplier,
    validate_proof_of_work,
    log_security_event,
)


def _generate_node_id(device_id: str) -> str:
    """Generate a unique 32-char hex node ID."""
    salt = secrets.token_hex(8)
    ts = str(int(datetime.utcnow().timestamp()))
    return hashlib.sha256(f"{device_id}:{ts}:{salt}".encode()).hexdigest()[:32]


# ── REGISTER ──────────────────────────────────────────────────────────────────

def register_node(
    db: Session,
    node_data: NodeRegister,
    ip_address: str,
    nonce: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Register a new node.

    Checks (in order):
      1. Device exists
      2. Max 2 active nodes per device
      3. Max 3 active nodes per IP
      4. Proof-of-work (required)
    """
    # 1. Device must exist
    device = db.query(Device).filter(Device.device_id == node_data.device_id).first()
    if not device:
        raise ValueError("Device not found. Register your device first.")

    # 2. Per-device node cap
    active_on_device = db.query(Node).filter(
        Node.device_id == node_data.device_id,
        Node.status == "active",
    ).count()
    if active_on_device >= 2:
        log_security_event(
            db, "device_limit",
            device_id=node_data.device_id,
            ip_address=ip_address,
            details={"active_nodes": active_on_device},
        )
        raise ValueError("Maximum 2 active nodes per device allowed.")

    # 3. Per-IP node cap
    if not check_ip_limit(db, ip_address, max_nodes=3):
        log_security_event(
            db, "ip_abuse",
            device_id=node_data.device_id,
            ip_address=ip_address,
            details={"reason": "max_nodes_per_ip"},
        )
        raise ValueError("Maximum 3 active nodes per IP address allowed.")

    # 4. Proof-of-work is mandatory
    if not nonce:
        raise ValueError("Proof-of-work nonce is required.")
    if not validate_proof_of_work(node_data.device_id, nonce):
        log_security_event(
            db, "invalid_pow",
            device_id=node_data.device_id,
            ip_address=ip_address,
            details={"nonce": nonce},
        )
        raise ValueError("Invalid proof-of-work. Solve the PoW challenge and retry.")

    # All checks passed — create node
    node_id = _generate_node_id(node_data.device_id)
    node_token = generate_node_token()

    new_node = Node(
        node_id=node_id,
        node_token=node_token,
        device_id=node_data.device_id,
        uptime=0.0,
        last_seen=datetime.utcnow(),
        last_heartbeat=None,
        status="active",
        node_score=100,
        ip_address=ip_address,
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)

    # Update IP tracker
    increment_ip_tracker(db, ip_address)

    return {
        "node_id": new_node.node_id,
        "node_token": new_node.node_token,
        "message": "Node registered successfully.",
    }


# ── HEARTBEAT ─────────────────────────────────────────────────────────────────

def process_heartbeat(
    db: Session,
    node_id: str,
    node_token: str,
    device_id: str,
    uptime: float,
    ip_address: str,
) -> Dict[str, Any]:
    """
    Process a heartbeat from a node.

    Checks (in order):
      1. Token authentication
      2. Node exists and is active
      3. Rate limit (≥ 20 s between beats)
      4. Suspicious behaviour analysis
      5. Uptime regression guard
    """
    # 1. Authenticate
    if not validate_node_token(db, node_id, node_token):
        log_security_event(
            db, "invalid_token",
            node_id=node_id,
            ip_address=ip_address,
            details={"device_id": device_id},
        )
        raise PermissionError("Invalid node_id or node_token.")

    # 2. Fetch node (active or stopped — stopped nodes can be resumed)
    node = db.query(Node).filter(
        Node.node_id == node_id,
        Node.device_id == device_id,
        Node.status.in_(["active", "stopped"]),
    ).first()
    if not node:
        log_security_event(
            db, "node_not_found",
            node_id=node_id,
            ip_address=ip_address,
            details={"device_id": device_id},
        )
        raise ValueError("Node not found or suspended.")

    # Reactivate if stopped
    if node.status == "stopped":
        node.status = "active"
        increment_ip_tracker(db, ip_address)
        db.commit()

    # 3. Rate limit
    if not check_rate_limit(db, node_id, min_interval=20):
        log_security_event(
            db, "spam",
            node_id=node_id,
            ip_address=ip_address,
            details={"reason": "rate_limit_violation"},
        )
        node.node_score = calculate_node_score(node.node_score, ["spam"])
        db.commit()
        raise ValueError("Heartbeat too frequent. Minimum interval is 20 seconds.")

    # Compute interval for behaviour checks
    heartbeat_interval = (
        (datetime.utcnow() - node.last_heartbeat).total_seconds()
        if node.last_heartbeat
        else 30.0
    )

    # 4. Behaviour analysis
    suspicion = is_suspicious(node, uptime, heartbeat_interval)
    if suspicion["suspicious"]:
        log_security_event(
            db, "suspicious",
            node_id=node_id,
            ip_address=ip_address,
            details=suspicion,
        )
        node.node_score = calculate_node_score(node.node_score, suspicion["reasons"])
        db.commit()

        if is_node_suspended(node.node_score):
            node.status = "suspended"
            decrement_ip_tracker(db, node.ip_address or ip_address)
            db.commit()
            raise ValueError("Node suspended due to repeated suspicious activity.")

    # 5. Uptime regression guard
    if uptime < node.uptime - 5:
        log_security_event(
            db, "invalid_uptime",
            node_id=node_id,
            ip_address=ip_address,
            details={"stored": node.uptime, "reported": uptime},
        )
        node.node_score = calculate_node_score(node.node_score, ["time_regression"])
        db.commit()
        raise ValueError("Invalid uptime: reported value went backwards.")

    # ── All checks passed — compute rewards ──────────────────────────────────
    uptime_delta = max(0.0, uptime - node.uptime)
    raw_points = uptime_delta / 60.0                        # 1 pt / min
    multiplier = reward_multiplier(node.node_score)
    adjusted_points = raw_points * multiplier

    # Update node
    node.uptime = uptime
    node.last_seen = datetime.utcnow()
    node.last_heartbeat = datetime.utcnow()
    node.ip_address = ip_address

    # Reward stable uptime bonus on score
    if uptime > 3600:
        node.node_score = calculate_node_score(node.node_score, [], stable_uptime=uptime)

    # Credit user
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        user = db.query(User).filter(User.id == device.user_id).first()
        if user and adjusted_points > 0:
            user.points += adjusted_points
            user.total_earned += adjusted_points

    db.commit()

    return {
        "success": True,
        "message": "Heartbeat received.",
        "points_earned": round(adjusted_points, 6),
        "node_score": node.node_score,
    }


# ── QUERIES ───────────────────────────────────────────────────────────────────

def stop_node(db: Session, node_id: str, node_token: str, device_id: str, ip_address: str) -> None:
    """Set node status to stopped and update IP tracker."""
    if not validate_node_token(db, node_id, node_token):
        raise PermissionError("Invalid node_id or node_token.")

    node = db.query(Node).filter(
        Node.node_id == node_id,
        Node.device_id == device_id,
    ).first()
    if not node:
        raise ValueError("Node not found.")

    if node.status == "active":
        node.status = "stopped"
        node.last_seen = datetime.utcnow()
        decrement_ip_tracker(db, node.ip_address or ip_address)
        db.commit()


def get_node_status(db: Session, device_id: str) -> List[Node]:
    return db.query(Node).filter(Node.device_id == device_id).all()


def get_user_nodes(db: Session, username: str) -> List[Node]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return []
    device_ids = [d.device_id for d in db.query(Device).filter(Device.user_id == user.id).all()]
    return db.query(Node).filter(Node.device_id.in_(device_ids)).all()
