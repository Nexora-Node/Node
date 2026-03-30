"""
Nexora Backend - Chain Node Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import ChainNodeRegister, ChainNodeHeartbeat, ChainNodeStatus, ChainNodeResponse, StatusResponse
from services.chain_service import (
    register_chain_node, process_chain_heartbeat,
    get_chain_nodes, get_supported_chains,
)

router = APIRouter(prefix="/chain", tags=["chain"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/supported")
def list_supported_chains():
    """List all supported blockchain networks and their reward multipliers."""
    return get_supported_chains()


@router.post("/register", response_model=ChainNodeResponse)
def register_chain(body: ChainNodeRegister, request: Request, db: Session = Depends(get_db)):
    """
    Register a local blockchain full node.
    Server will verify the RPC is reachable, chain ID matches, and node is synced.
    """
    ip = _client_ip(request)
    try:
        result = register_chain_node(db, body.node_id, body.node_token,
                                     body.chain_id, body.rpc_url, ip)
        return ChainNodeResponse(
            success=True,
            message=result["message"],
            chain_node_id=result["chain_node_id"],
            chain_name=result["chain_name"],
            reward_multiplier=result["reward_multiplier"],
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/heartbeat")
def chain_heartbeat(body: ChainNodeHeartbeat, request: Request, db: Session = Depends(get_db)):
    """Send heartbeat for a chain node — verifies block is advancing."""
    ip = _client_ip(request)
    try:
        return process_chain_heartbeat(
            db, body.chain_node_id, body.node_id,
            body.node_token, body.local_block, ip,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/nodes/{node_id}", response_model=list[ChainNodeStatus])
def get_node_chains(node_id: str, db: Session = Depends(get_db)):
    """Get all chain nodes registered under a Nexora node."""
    return get_chain_nodes(db, node_id)
