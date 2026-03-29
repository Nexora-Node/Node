"""
Nexora Backend - Anti-Cheat Service
Advanced anti-abuse and security detection
"""

import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from models import Node, Device, IPTracker, SecurityLog


# ── TOKEN & FINGERPRINT ───────────────────────────────────────────────────────

def generate_node_token() -> str:
    """Generate a cryptographically secure 64-char hex node token."""
    return secrets.token_hex(32)


def generate_device_fingerprint(
    os_info: str,
    hostname: str,
    mac_address: str,
    cpu_count: int,
    ram_size: int,
    disk_size: int,
) -> str:
    """
    SHA256 of 'os:hostname:mac:cpu:ram:disk'.
    Returns a 64-char lowercase hex digest.
    """
    combined = f"{os_info}:{hostname}:{mac_address}:{cpu_count}:{ram_size}:{disk_size}"
    return hashlib.sha256(combined.encode()).hexdigest()


# ── NODE TOKEN VALIDATION ─────────────────────────────────────────────────────

def validate_node_token(db: Session, node_id: str, node_token: str) -> bool:
    """Return True only if node_id + node_token match an active node."""
    node = db.query(Node).filter(
        Node.node_id == node_id,
        Node.node_token == node_token,
        Node.status == "active",
    ).first()
    return node is not None


# ── IP TRACKING ───────────────────────────────────────────────────────────────

def get_ip_node_count(db: Session, ip_address: str) -> int:
    """Return the number of active nodes registered from this IP."""
    return db.query(Node).filter(
        Node.ip_address == ip_address,
        Node.status == "active",
    ).count()


def check_ip_limit(db: Session, ip_address: str, max_nodes: int = 3) -> bool:
    """Return True if the IP is still within the allowed node limit."""
    return get_ip_node_count(db, ip_address) < max_nodes


def increment_ip_tracker(db: Session, ip_address: str) -> None:
    """Upsert the IPTracker row for this IP, incrementing node_count."""
    tracker = db.query(IPTracker).filter(IPTracker.ip_address == ip_address).first()
    if tracker:
        tracker.node_count += 1
        tracker.last_updated = datetime.utcnow()
    else:
        tracker = IPTracker(ip_address=ip_address, node_count=1)
        db.add(tracker)
    db.commit()


def decrement_ip_tracker(db: Session, ip_address: str) -> None:
    """Decrement node_count for this IP (called when a node is stopped/suspended)."""
    tracker = db.query(IPTracker).filter(IPTracker.ip_address == ip_address).first()
    if tracker and tracker.node_count > 0:
        tracker.node_count -= 1
        tracker.last_updated = datetime.utcnow()
        db.commit()


# ── RATE LIMITING ─────────────────────────────────────────────────────────────

def check_rate_limit(db: Session, node_id: str, min_interval: int = 20) -> bool:
    """
    Return True if enough time has passed since the last heartbeat.
    A node with no prior heartbeat always passes.
    """
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node or node.last_heartbeat is None:
        return True
    elapsed = (datetime.utcnow() - node.last_heartbeat).total_seconds()
    return elapsed >= min_interval


# ── BEHAVIOR ANALYSIS ─────────────────────────────────────────────────────────

# How many seconds of tolerance we allow for "perfect timing" detection.
# A bot sending heartbeats at exactly N seconds is suspicious; real clients
# have jitter.  We flag if the interval is within ±0.5 s of an exact multiple
# of 30 s AND the node has sent at least 5 heartbeats (tracked via uptime proxy).
_PERFECT_TIMING_TOLERANCE = 0.5
_PERFECT_TIMING_INTERVAL = 30.0


def is_suspicious(node: Node, uptime: float, heartbeat_interval: float) -> Dict[str, Any]:
    """
    Analyse a heartbeat for suspicious patterns.

    Checks:
      A. Uptime jump  — reported uptime grew more than 2× the elapsed wall time
      B. Perfect timing — heartbeat arrives within ±0.5 s of exactly 30 s
                          (only flagged after the node has been running > 5 min
                           to avoid false positives on first few beats)
      C. Time regression — uptime went backwards by more than 5 s
      D. Abnormal growth rate — uptime growing faster than 1.5× real time

    Returns:
        {"suspicious": bool, "reasons": List[str]}
    """
    suspicious = False
    reasons: List[str] = []

    # A. Uptime jump
    expected_max = node.uptime + heartbeat_interval * 2
    if uptime > expected_max and heartbeat_interval > 0:
        suspicious = True
        reasons.append("uptime_jump")

    # B. Perfect timing — only meaningful after node has been running a while
    if node.uptime > 300:  # 5 minutes of history
        deviation = abs(heartbeat_interval - _PERFECT_TIMING_INTERVAL)
        if deviation < _PERFECT_TIMING_TOLERANCE:
            suspicious = True
            reasons.append("perfect_timing")

    # C. Time regression
    if uptime < node.uptime - 5:
        suspicious = True
        reasons.append("time_regression")

    # D. Abnormal growth rate
    if heartbeat_interval > 0 and node.uptime > 0:
        growth_rate = (uptime - node.uptime) / heartbeat_interval
        if growth_rate > 1.5:
            suspicious = True
            reasons.append("abnormal_growth")

    return {"suspicious": suspicious, "reasons": reasons}


# ── NODE SCORE ────────────────────────────────────────────────────────────────

_VIOLATION_PENALTIES: Dict[str, int] = {
    "spam": -10,
    "invalid_uptime": -15,
    "suspicious": -20,
    "ip_abuse": -25,
    "uptime_jump": -15,
    "perfect_timing": -10,
    "time_regression": -20,
    "abnormal_growth": -15,
    "invalid_pow": -30,
}

_SCORE_MIN = 0
_SCORE_MAX = 100
_SUSPENSION_THRESHOLD = 20
_REDUCED_REWARD_THRESHOLD = 50


def calculate_node_score(
    current_score: int,
    violations: List[str],
    stable_uptime: float = 0,
) -> int:
    """
    Adjust node score based on violations and stable uptime.

    - Each violation applies a penalty from _VIOLATION_PENALTIES.
    - Stable uptime > 1 h grants +1 per hour (capped at 100).
    """
    score = current_score

    for v in violations:
        score += _VIOLATION_PENALTIES.get(v, -5)

    if stable_uptime > 3600:
        bonus = min(int(stable_uptime / 3600), 5)  # max +5 per heartbeat
        score = min(_SCORE_MAX, score + bonus)

    return max(_SCORE_MIN, min(_SCORE_MAX, score))


def is_node_suspended(score: int) -> bool:
    return score < _SUSPENSION_THRESHOLD


def reward_multiplier(score: int) -> float:
    """
    Returns a multiplier in [0.0, 1.0] applied to points earned.
    Nodes below the reduced-reward threshold earn proportionally less.
    """
    if score >= _REDUCED_REWARD_THRESHOLD:
        return score / _SCORE_MAX
    # Linear scale from 0 → 0.5 for scores 0–50
    return (score / _REDUCED_REWARD_THRESHOLD) * 0.5


# ── PROOF OF WORK ─────────────────────────────────────────────────────────────

def validate_proof_of_work(device_id: str, nonce: str, difficulty: int = 3) -> bool:
    """
    Validate lightweight PoW: sha256(device_id + nonce) must start with
    `difficulty` leading zeros.
    """
    if not nonce or not nonce.isdigit():
        return False
    data = f"{device_id}{nonce}"
    hash_result = hashlib.sha256(data.encode()).hexdigest()
    return hash_result.startswith("0" * difficulty)


# ── SECURITY LOGGING ──────────────────────────────────────────────────────────

def log_security_event(
    db: Session,
    event_type: str,
    node_id: Optional[str] = None,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist a security event to the security_logs table."""
    entry = SecurityLog(
        event_type=event_type,
        node_id=node_id,
        device_id=device_id,
        ip_address=ip_address,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    db.commit()
