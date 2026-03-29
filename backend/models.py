"""
Nexora Backend - Database Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    referral_code = Column(String(20), unique=True, index=True, nullable=False)
    invited_by = Column(String(20), nullable=True)
    referral_used = Column(Boolean, default=False)  # True once someone uses this code
    points = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    devices = relationship("Device", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True, nullable=False)
    # SHA256 of OS:hostname:MAC:cpu_count:ram_gb:disk_gb
    device_fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="devices")
    nodes = relationship("Node", back_populates="device")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(64), unique=True, index=True, nullable=False)
    # secrets.token_hex(32) — 64 hex chars
    node_token = Column(String(64), unique=True, index=True, nullable=False)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False)
    uptime = Column(Float, default=0.0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")   # active | stopped | suspended
    node_score = Column(Integer, default=100)        # 0–100
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="nodes")


class IPTracker(Base):
    """Tracks how many active nodes are registered per IP address."""
    __tablename__ = "ip_tracker"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    node_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    # spam | invalid_uptime | suspicious | ip_abuse | invalid_token
    # invalid_pow | device_limit | node_not_found | time_regression
    event_type = Column(String(50), nullable=False)
    node_id = Column(String(64), nullable=True, index=True)
    device_id = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    details = Column(Text, nullable=True)   # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
