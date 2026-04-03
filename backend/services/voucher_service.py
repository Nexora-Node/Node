"""
Nexora Backend - Voucher Service
Signs EIP-712 claim vouchers for ClaimDistributor contract.
"""

import os
import time
import secrets
from eth_account import Account
from eth_account._utils.structured_data.hashing import hash_domain, hash_message
from eth_account._utils.structured_data.validation import validate_structured_data


SIGNER_PRIVATE_KEY        = os.environ.get("SIGNER_PRIVATE_KEY", "")
CLAIM_DISTRIBUTOR_ADDRESS = os.environ.get("CLAIM_DISTRIBUTOR_ADDRESS", "")
CHAIN_ID                  = int(os.environ.get("CHAIN_ID", "8453"))
TOKEN_DECIMALS            = 18
VOUCHER_TTL_SECONDS       = 300
MINING_SUPPLY_CAP         = 200_000.0


def _to_wei(amount: float) -> int:
    return int(amount * (10 ** TOKEN_DECIMALS))


def generate_claim_voucher(user_wallet: str, token_amount: float) -> dict:
    if not SIGNER_PRIVATE_KEY:
        raise RuntimeError("SIGNER_PRIVATE_KEY not set in environment")
    if not CLAIM_DISTRIBUTOR_ADDRESS:
        raise RuntimeError("CLAIM_DISTRIBUTOR_ADDRESS not set in environment")
    if token_amount > MINING_SUPPLY_CAP:
        raise ValueError(f"Claim exceeds mining allocation cap ({MINING_SUPPLY_CAP:,.0f} tokens)")

    amount_wei = _to_wei(token_amount)
    nonce      = int(secrets.token_hex(16), 16) % (2**64)
    deadline   = int(time.time()) + VOUCHER_TTL_SECONDS

    structured_data = {
        "types": {
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
        },
        "domain": {
            "name":              "NexoraClaimDistributor",
            "version":           "1",
            "chainId":           CHAIN_ID,
            "verifyingContract": CLAIM_DISTRIBUTOR_ADDRESS,
        },
        "primaryType": "Claim",
        "message": {
            "user":     user_wallet,
            "amount":   amount_wei,
            "nonce":    nonce,
            "deadline": deadline,
        },
    }

    signed = Account.sign_typed_data(
        SIGNER_PRIVATE_KEY,
        domain_data=structured_data["domain"],
        message_types={"Claim": structured_data["types"]["Claim"]},
        message_data=structured_data["message"],
    )

    return {
        "amount":          str(amount_wei),
        "nonce":           str(nonce),
        "deadline":        deadline,
        "v":               signed.v,
        "r":               "0x" + signed.r.hex(),
        "s":               "0x" + signed.s.hex(),
        "contract":        CLAIM_DISTRIBUTOR_ADDRESS,
        "chain_id":        CHAIN_ID,
        "pending_amount":  token_amount,
    }
