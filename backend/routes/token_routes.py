"""
Nexora Backend - Token Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
from schemas import TokensResponse
from services.token_service import get_user_tokens, prepare_claim, confirm_claim

router = APIRouter(prefix="/tokens", tags=["tokens"])


class PrepareClaimRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class ConfirmClaimRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    tx_hash:  str = Field(..., min_length=66, max_length=66)
    amount:   float = Field(..., gt=0)


@router.get("/{username}", response_model=TokensResponse)
def get_tokens(username: str, db: Session = Depends(get_db)):
    try:
        return get_user_tokens(db, username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/prepare-claim")
def prepare_claim_endpoint(body: PrepareClaimRequest, db: Session = Depends(get_db)):
    """
    Generate a signed EIP-712 voucher.
    Frontend submits this voucher to ClaimDistributor contract.
    """
    try:
        return prepare_claim(db, body.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/confirm-claim")
def confirm_claim_endpoint(body: ConfirmClaimRequest, db: Session = Depends(get_db)):
    """
    Called after user successfully submits on-chain tx.
    Deducts tokens from DB balance.
    """
    try:
        return confirm_claim(db, body.username, body.tx_hash, body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
