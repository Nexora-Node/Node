"""
Nexora Backend - Voucher Service
Signs EIP-712 claim vouchers for ClaimDistributor contract.
"""

import os
import time
import secrets
from eth_account import Account
from eth_account.messages import encode_typed_data


SIGNER_PRIVATE_KEY        = os.environ.get("SIGNER_PRIVATE_KEY", "")
CLAIM_DISTRIBUTOR_ADDRESS = os.environ.get("CLAIM_DISTRIBUTOR_ADDRESS", "")
CHAIN_ID                  = int(os.environ.get("CHAIN_ID", "8453"))  # Base mainnet
TOKEN_DECIMALS            = 18
VOUCHER_TTL_SECONDS       = 300   # voucher valid for 5 minutes
MINING_SUPPLY_CAP         = 200_000.0  # only 200k approved to distributor


def _to_wei(amount: float) -> int:
    """Convert float token amount to wei (18 decimals)."""
    return int(amount * (10 ** TOKEN_DECIMALS))


def generate_claim_voucher(user_wallet: str, token_amount: float) -> dict:
    """
    Generate a signed EIP-712 voucher for the ClaimDistributor contract.

    Args:
        user_wallet: User's EVM wallet address (0x...)
        token_amount: Amount of tokens to claim (float, e.g. 10.5)

    Returns:
        dict with amount_wei, nonce, deadline, v, r, s
    """
    if not SIGNER_PRIVATE_KEY:
        raise RuntimeError("SIGNER_PRIVATE_KEY not set in environment")
    if not CLAIM_DISTRIBUTOR_ADDRESS:
        raise RuntimeError("CLAIM_DISTRIBUTOR_ADDRESS not set in environment")
    if token_amount > MINING_SUPPLY_CAP:
        raise ValueError(f"Claim exceeds mining allocation cap ({MINING_SUPPLY_CAP:,.0f} tokens)")

    amount_wei = _to_wei(token_amount)
    nonce      = int(secrets.token_hex(16), 16) % (2**64)  # random 64-bit nonce
    deadline   = int(time.time()) + VOUCHER_TTL_SECONDS

    domain = {
        "name": "NexoraClaimDistributor",
        "version": "1",
        "chainId": CHAIN_ID,
        "verifyingContract": CLAIM_DISTRIBUTOR_ADDRESS,
    }

    types = {
        "EIP712Domain": [
            {"name": "name",              "type": "string"},
            {"name": "version",           "type": "string"},
            {"name": "chainId",           "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "Claim": [
            {"name": "user",     "type": "address"},
            {"name": "amount",   "type": "uint256"},
            {"name": "nonce",    "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
    }

    message = {
        "user":     user_wallet,
        "amount":   amount_wei,
        "nonce":    nonce,
        "deadline": deadline,
    }

    structured_data = {
        "types":       types,
        "domain":      domain,
        "primaryType": "Claim",
        "message":     message,
    }

    signed = Account.sign_typed_data(SIGNER_PRIVATE_KEY, full_message=structured_data)

    return {
        "amount":   str(amount_wei),   # string to avoid JS BigInt issues
        "nonce":    str(nonce),
        "deadline": deadline,
        "v":        signed.v,
        "r":        "0x" + signed.r.hex(),
        "s":        "0x" + signed.s.hex(),
        "contract": CLAIM_DISTRIBUTOR_ADDRESS,
        "chain_id": CHAIN_ID,
    }
