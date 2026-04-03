"""
Nexora Backend - Database Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    referral_code = Column(String(20), unique=True, index=True, nullable=False)
    invited_by = Column(String(20), nullable=True)
    referral_used = Column(Boolean, default=False)
    wallet_address = Column(String(42), nullable=True, unique=True, index=True)  # EVM wallet 0x...
    tokens = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    claimed_tokens = Column(Float, default=0.0)
    last_claim_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    devices = relationship("Device", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True, nullable=False)
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
    node_token = Column(String(64), unique=True, index=True, nullable=False)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False)
    uptime = Column(Float, default=0.0)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    node_score = Column(Integer, default=100)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="nodes")


class ChainNode(Base):
    """Tracks a user's blockchain full node (Base, ETH, OP, BNB, etc.)"""
    __tablename__ = "chain_nodes"

    id = Column(Integer, primary_key=True, index=True)
    chain_node_id = Column(String(64), unique=True, index=True, nullable=False)
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)
    chain_id = Column(Integer, nullable=False, index=True)   # e.g. 8453 = Base mainnet
    chain_name = Column(String(50), nullable=False)          # e.g. "base_mainnet"
    rpc_url = Column(String(255), nullable=False)            # local RPC endpoint
    last_block = Column(Integer, default=0)                  # last verified block
    last_verified = Column(DateTime, nullable=True)
    sync_lag = Column(Integer, default=0)                    # blocks behind public RPC
    status = Column(String(20), default="active")            # active | stopped | unsynced
    created_at = Column(DateTime, default=datetime.utcnow)


class IPTracker(Base):
    __tablename__ = "ip_tracker"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, index=True, nullable=False)
    node_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    node_id = Column(String(64), nullable=True, index=True)
    device_id = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MiningConfig(Base):
    """Global mining configuration — single row, id=1."""
    __tablename__ = "mining_config"

    id = Column(Integer, primary_key=True, default=1)
    mining_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    halving_interval_days = Column(Integer, default=24)           # epoch = 24 days
    base_rate_per_min = Column(Float, default=0.28935185)         # 10000 / 34560
    total_distributed = Column(Float, default=0.0)
    mining_supply_cap = Column(Float, default=200_000.0)


class SystemReferral(Base):
    """System-generated referral codes not tied to any user."""
    __tablename__ = "system_referrals"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    used = Column(Boolean, default=False)
    used_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
