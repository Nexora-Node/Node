"""
Nexora Backend - Token Service
Business logic for tokens and rewards
"""

from datetime import datetime
from sqlalchemy.orm import Session
from models import User


def get_user_tokens(db: Session, username: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("User not found")

    return {
        "username":      user.username,
        "tokens":        user.tokens,
        "total_earned":  user.total_earned,
        "claimed_tokens": user.claimed_tokens,
        "last_claim_at": user.last_claim_at,
    }


def prepare_claim(db: Session, username: str) -> dict:
    """
    Validate claim eligibility and generate an EIP-712 voucher.
    Does NOT deduct tokens yet — deduction happens after on-chain confirmation.
    """
    from services.voucher_service import generate_claim_voucher

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("User not found")
    if not user.wallet_address:
        raise ValueError("No wallet linked. Link your wallet first.")
    if user.tokens < 1.0:
        raise ValueError("Minimum claim is 1 token.")

    voucher = generate_claim_voucher(user.wallet_address, user.tokens)

    # Record pending claim amount on voucher (for confirmation step)
    voucher["pending_amount"] = user.tokens
    return voucher


def confirm_claim(db: Session, username: str, tx_hash: str, amount: float) -> dict:
    """
    Called after user submits the on-chain tx.
    Deducts tokens from DB and records claim history.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("User not found")

    # Deduct — cap at current balance to avoid going negative
    deducted = min(amount, user.tokens)
    user.claimed_tokens = (user.claimed_tokens or 0.0) + deducted
    user.tokens -= deducted
    user.last_claim_at = datetime.utcnow()

    db.commit()

    return {
        "success":       True,
        "message":       f"Claim recorded: {deducted:.4f} tokens",
        "tokens_claimed": deducted,
        "claimed_tokens": user.claimed_tokens,
        "tx_hash":       tx_hash,
    }
