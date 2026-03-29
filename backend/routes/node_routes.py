"""
Nexora Backend - Node Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    NodeRegister, NodeHeartbeat, NodeStatus,
    NodeRegisterResponse, StatusResponse,
)
from services.node_service import (
    register_node, process_heartbeat,
    get_node_status, get_user_nodes,
)

router = APIRouter(prefix="/node", tags=["node"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=NodeRegisterResponse)
def register_node_endpoint(
    node_data: NodeRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _client_ip(request)
    try:
        result = register_node(db, node_data, ip, node_data.nonce)
        return NodeRegisterResponse(
            success=True,
            message=result["message"],
            node_id=result["node_id"],
            node_token=result["node_token"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/heartbeat", response_model=StatusResponse)
def node_heartbeat(
    heartbeat: NodeHeartbeat,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = _client_ip(request)
    try:
        result = process_heartbeat(
            db,
            heartbeat.node_id,
            heartbeat.node_token,
            heartbeat.device_id,
            heartbeat.uptime,
            ip,
        )
        return StatusResponse(success=True, message=result["message"])
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status/{device_id}", response_model=list[NodeStatus])
def get_node_status_endpoint(device_id: str, db: Session = Depends(get_db)):
    return get_node_status(db, device_id)


@router.get("/user/{username}", response_model=list[NodeStatus])
def get_user_nodes_endpoint(username: str, db: Session = Depends(get_db)):
    return get_user_nodes(db, username)
