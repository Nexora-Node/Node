"""
Nexora Backend - Pydantic Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ── USER ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    referral_code: str = Field(..., min_length=1, max_length=20)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    referral_code: str
    invited_by: Optional[str] = None
    points: float
    total_earned: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── DEVICE ────────────────────────────────────────────────────────────────────

class DeviceRegister(BaseModel):
    device_id: str = Field(..., min_length=32, max_length=64)
    device_fingerprint: str = Field(..., min_length=64, max_length=64)
    user_id: int
    ip_address: Optional[str] = Field(None, max_length=45)

    @field_validator("device_fingerprint")
    @classmethod
    def fingerprint_hex(cls, v: str) -> str:
        if not re.match(r"^[0-9a-f]{64}$", v):
            raise ValueError("device_fingerprint must be a 64-char lowercase hex SHA256 digest")
        return v


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_fingerprint: str
    user_id: int
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── NODE ──────────────────────────────────────────────────────────────────────

class NodeRegister(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    system: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    nonce: Optional[str] = Field(None, max_length=20)


class NodeHeartbeat(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=64)
    node_token: str = Field(..., min_length=64, max_length=64)
    device_id: str = Field(..., min_length=1, max_length=64)
    uptime: float = Field(..., ge=0)


class NodeStatus(BaseModel):
    node_id: str
    device_id: str
    uptime: float
    last_seen: datetime
    status: str
    node_score: int
    ip_address: Optional[str] = None

    model_config = {"from_attributes": True}


class NodeRegisterResponse(BaseModel):
    success: bool
    message: str
    node_id: str
    node_token: str


# ── POINTS ────────────────────────────────────────────────────────────────────

class PointsResponse(BaseModel):
    username: str
    points: float
    total_earned: float


class ClaimRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class ClaimResponse(BaseModel):
    success: bool
    message: str
    points_claimed: float


# ── SECURITY ──────────────────────────────────────────────────────────────────

class SecurityLogResponse(BaseModel):
    id: int
    event_type: str
    node_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── CHAIN NODE ────────────────────────────────────────────────────────────────

class ChainNodeRegister(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=64)
    node_token: str = Field(..., min_length=64, max_length=64)
    chain_id: int
    rpc_url: str = Field(..., max_length=255)


class ChainNodeHeartbeat(BaseModel):
    chain_node_id: str = Field(..., min_length=1, max_length=64)
    node_id: str = Field(..., min_length=1, max_length=64)
    node_token: str = Field(..., min_length=64, max_length=64)
    local_block: int = Field(..., ge=0)


class ChainNodeStatus(BaseModel):
    chain_node_id: str
    chain_id: int
    chain_name: str
    last_block: int
    sync_lag: int
    status: str
    last_verified: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChainNodeResponse(BaseModel):
    success: bool
    message: str
    chain_node_id: str
    chain_name: str
    reward_multiplier: float


# ── GENERAL ───────────────────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    success: bool
    message: str
