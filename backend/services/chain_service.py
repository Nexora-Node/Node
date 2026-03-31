"""
Nexora Backend - Chain Service
Verifies blockchain full nodes and applies reward multipliers
"""

import hashlib
import secrets
import json
import requests as http_requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models import ChainNode, Node, Device, User
from services.anti_cheat_service import validate_node_token, log_security_event

# ── SUPPORTED CHAINS ──────────────────────────────────────────────────────────
# chain_id → {name, public_rpc, multiplier, max_lag_blocks}
SUPPORTED_CHAINS: Dict[int, Dict[str, Any]] = {
    1:        {"name": "eth_mainnet",    "rpc": "https://eth.llamarpc.com",                    "multiplier": 5.0, "max_lag": 50},
    10:       {"name": "op_mainnet",     "rpc": "https://mainnet.optimism.io",                 "multiplier": 2.0, "max_lag": 50},
    56:       {"name": "bnb_mainnet",    "rpc": "https://bsc-dataseed.binance.org",             "multiplier": 2.0, "max_lag": 100},
    8453:     {"name": "base_mainnet",   "rpc": "https://mainnet.base.org",                    "multiplier": 3.0, "max_lag": 50},
    84532:    {"name": "base_sepolia",   "rpc": "https://sepolia.base.org",                    "multiplier": 1.5, "max_lag": 100},
    11155111: {"name": "eth_sepolia",    "rpc": "https://rpc.sepolia.org",                     "multiplier": 1.5, "max_lag": 100},
    11155420: {"name": "op_sepolia",     "rpc": "https://sepolia.optimism.io",                 "multiplier": 1.5, "max_lag": 100},
    97:       {"name": "bnb_testnet",    "rpc": "https://data-seed-prebsc-1-s1.binance.org:8545", "multiplier": 1.2, "max_lag": 200},
}


def get_chain_info(chain_id: int) -> Optional[Dict[str, Any]]:
    return SUPPORTED_CHAINS.get(chain_id)


def _rpc_block_number(rpc_url: str, timeout: int = 5) -> Optional[int]:
    """Call eth_blockNumber on any EVM RPC. Returns int or None on failure."""
    try:
        resp = http_requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        result = resp.json().get("result")
        if result:
            return int(result, 16)
    except Exception:
        pass
    return None


def _rpc_chain_id(rpc_url: str, timeout: int = 5) -> Optional[int]:
    """Call eth_chainId on local RPC to verify it matches expected chain."""
    try:
        resp = http_requests.post(
            rpc_url,
            json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1},
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        result = resp.json().get("result")
        if result:
            return int(result, 16)
    except Exception:
        pass
    return None


def verify_chain_node(chain_id: int, rpc_url: str) -> Dict[str, Any]:
    """
    Verify a local blockchain node:
    1. Confirm chain_id matches
    2. Get local block number
    3. Get public block number
    4. Calculate sync lag

    Returns dict with verified, local_block, public_block, lag
    """
    chain = get_chain_info(chain_id)
    if not chain:
        return {"verified": False, "error": f"Chain {chain_id} not supported"}

    # Verify chain ID matches
    local_chain_id = _rpc_chain_id(rpc_url)
    if local_chain_id is None:
        return {"verified": False, "error": "Cannot connect to local RPC"}
    if local_chain_id != chain_id:
        return {
            "verified": False,
            "error": f"Chain ID mismatch: expected {chain_id}, got {local_chain_id}",
        }

    # Get local block
    local_block = _rpc_block_number(rpc_url)
    if local_block is None:
        return {"verified": False, "error": "Cannot get block number from local RPC"}

    # Get public block
    public_block = _rpc_block_number(chain["rpc"])
    if public_block is None:
        # Public RPC down — accept local block, lag unknown
        return {
            "verified": True,
            "local_block": local_block,
            "public_block": local_block,
            "lag": 0,
            "warning": "Public RPC unavailable, lag unknown",
        }

    lag = max(0, public_block - local_block)
    synced = lag <= chain["max_lag"]

    return {
        "verified": synced,
        "local_block": local_block,
        "public_block": public_block,
        "lag": lag,
        "error": None if synced else f"Node out of sync: {lag} blocks behind (max {chain['max_lag']})",
    }


# ── REGISTER CHAIN NODE ───────────────────────────────────────────────────────

def register_chain_node(
    db: Session,
    node_id: str,
    node_token: str,
    chain_id: int,
    rpc_url: str,
    ip_address: str,
) -> Dict[str, Any]:
    """Register a blockchain full node linked to a Nexora node."""

    # Auth
    if not validate_node_token(db, node_id, node_token):
        raise PermissionError("Invalid node_id or node_token.")

    chain = get_chain_info(chain_id)
    if not chain:
        raise ValueError(f"Chain ID {chain_id} is not supported.")

    # Verify the node is actually running and synced
    verification = verify_chain_node(chain_id, rpc_url)
    if not verification["verified"]:
        log_security_event(db, "chain_verify_failed", node_id=node_id,
                           ip_address=ip_address,
                           details={"chain_id": chain_id, "error": verification.get("error")})
        raise ValueError(f"Chain node verification failed: {verification.get('error')}")

    # Check if already registered for this chain
    existing = db.query(ChainNode).filter(
        ChainNode.node_id == node_id,
        ChainNode.chain_id == chain_id,
        ChainNode.status == "active",
    ).first()
    if existing:
        return {
            "chain_node_id": existing.chain_node_id,
            "chain_name": chain["name"],
            "reward_multiplier": chain["multiplier"],
            "message": "Chain node already registered.",
        }

    chain_node_id = hashlib.sha256(
        f"{node_id}:{chain_id}:{secrets.token_hex(8)}".encode()
    ).hexdigest()[:32]

    cn = ChainNode(
        chain_node_id=chain_node_id,
        node_id=node_id,
        chain_id=chain_id,
        chain_name=chain["name"],
        rpc_url=rpc_url,
        last_block=verification["local_block"],
        last_verified=datetime.utcnow(),
        sync_lag=verification["lag"],
        status="active",
    )
    db.add(cn)
    db.commit()

    return {
        "chain_node_id": chain_node_id,
        "chain_name": chain["name"],
        "reward_multiplier": chain["multiplier"],
        "message": f"Chain node registered: {chain['name']}",
    }


# ── CHAIN HEARTBEAT ───────────────────────────────────────────────────────────

def process_chain_heartbeat(
    db: Session,
    chain_node_id: str,
    node_id: str,
    node_token: str,
    local_block: int,
    ip_address: str,
) -> Dict[str, Any]:
    """
    Process heartbeat for a chain node.
    Verifies block is advancing, calculates sync lag, awards bonus points.
    """
    if not validate_node_token(db, node_id, node_token):
        raise PermissionError("Invalid node_id or node_token.")

    cn = db.query(ChainNode).filter(
        ChainNode.chain_node_id == chain_node_id,
        ChainNode.node_id == node_id,
        ChainNode.status == "active",
    ).first()
    if not cn:
        raise ValueError("Chain node not found or inactive.")

    chain = get_chain_info(cn.chain_id)
    if not chain:
        raise ValueError("Chain no longer supported.")

    # Block must be advancing (anti-cheat: fake nodes report same block)
    if local_block < cn.last_block:
        log_security_event(db, "chain_block_regression", node_id=node_id,
                           ip_address=ip_address,
                           details={"chain_id": cn.chain_id,
                                    "stored": cn.last_block, "reported": local_block})
        raise ValueError("Block number went backwards — possible fake node.")

    # Get public block for lag check
    public_block = _rpc_block_number(chain["rpc"])
    lag = max(0, (public_block or local_block) - local_block)
    synced = lag <= chain["max_lag"]

    if not synced:
        cn.status = "unsynced"
        cn.sync_lag = lag
        db.commit()
        raise ValueError(f"Node out of sync: {lag} blocks behind. Rewards paused.")

    # Calculate bonus tokens (halving-adjusted)
    from services.mining_rate_service import current_rate, add_distributed, is_supply_exhausted
    if is_supply_exhausted(db):
        bonus_tokens = 0.0
    else:
        rate = current_rate(db)
        bonus_tokens = chain["multiplier"] * 0.5 * rate  # scaled by current rate

    # Credit user
    nexora_node = db.query(Node).filter(Node.node_id == node_id).first()
    if nexora_node and bonus_tokens > 0:
        from models import Device, User
        device = db.query(Device).filter(Device.device_id == nexora_node.device_id).first()
        if device:
            user = db.query(User).filter(User.id == device.user_id).first()
            if user:
                credited = add_distributed(db, bonus_tokens)
                user.tokens += credited
                user.total_earned += credited

    cn.last_block = local_block
    cn.last_verified = datetime.utcnow()
    cn.sync_lag = lag
    cn.status = "active"
    db.commit()

    return {
        "success": True,
        "message": f"Chain heartbeat received: {chain['name']}",
        "chain_name": chain["name"],
        "local_block": local_block,
        "sync_lag": lag,
        "bonus_tokens": round(bonus_tokens, 4),
        "reward_multiplier": chain["multiplier"],
    }


def get_chain_nodes(db: Session, node_id: str) -> List[ChainNode]:
    return db.query(ChainNode).filter(ChainNode.node_id == node_id).all()


def get_supported_chains() -> List[Dict[str, Any]]:
    return [
        {"chain_id": cid, "name": info["name"], "multiplier": info["multiplier"]}
        for cid, info in SUPPORTED_CHAINS.items()
    ]
