// SPDX-License-Identifier: MIT
pragma solidity ^0.8.25;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {EIP712} from "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title ClaimDistributor
/// @notice Users submit a backend-signed voucher to claim NEXOR tokens.
///         Treasury must approve this contract to spend its tokens.
///         0.05% fee on each claim goes to feeWallet (DEX listing fund).
contract ClaimDistributor is EIP712, Ownable {
    using ECDSA for bytes32;

    // ── State ──────────────────────────────────────────────────────────────

    IERC20  public immutable token;
    address public treasury;
    address public feeWallet;
    address public signer;          // backend hot wallet (signs vouchers)

    uint256 public constant FEE_BPS = 5;        // 0.05% = 5 basis points
    uint256 public constant BPS_BASE = 10_000;

    // Prevent replay: track used nonces per user
    mapping(address => mapping(uint256 => bool)) public usedNonces;

    // EIP-712 typehash
    bytes32 public constant CLAIM_TYPEHASH = keccak256(
        "Claim(address user,uint256 amount,uint256 nonce,uint256 deadline)"
    );

    // ── Events ─────────────────────────────────────────────────────────────

    event Claimed(address indexed user, uint256 amount, uint256 fee, uint256 nonce);
    event SignerUpdated(address indexed newSigner);
    event FeeWalletUpdated(address indexed newFeeWallet);
    event TreasuryUpdated(address indexed newTreasury);

    // ── Constructor ────────────────────────────────────────────────────────

    constructor(
        address token_,
        address treasury_,
        address feeWallet_,
        address signer_,
        address owner_
    ) EIP712("NexoraClaimDistributor", "1") Ownable(owner_) {
        require(token_     != address(0), "token=0");
        require(treasury_  != address(0), "treasury=0");
        require(feeWallet_ != address(0), "feeWallet=0");
        require(signer_    != address(0), "signer=0");

        token      = IERC20(token_);
        treasury   = treasury_;
        feeWallet  = feeWallet_;
        signer     = signer_;
    }

    // ── Claim ──────────────────────────────────────────────────────────────

    /// @notice Claim tokens using a backend-signed voucher.
    /// @param amount   Raw token amount to claim (18 decimals)
    /// @param nonce    Unique nonce from backend (prevents replay)
    /// @param deadline Unix timestamp after which voucher expires
    /// @param v,r,s    EIP-712 signature from backend signer
    function claim(
        uint256 amount,
        uint256 nonce,
        uint256 deadline,
        uint8 v, bytes32 r, bytes32 s
    ) external {
        require(block.timestamp <= deadline, "Voucher expired");
        require(!usedNonces[msg.sender][nonce], "Nonce already used");
        require(amount > 0, "Amount must be > 0");

        // Verify EIP-712 signature
        bytes32 structHash = keccak256(abi.encode(
            CLAIM_TYPEHASH,
            msg.sender,
            amount,
            nonce,
            deadline
        ));
        address recovered = _hashTypedDataV4(structHash).recover(v, r, s);
        require(recovered == signer, "Invalid signature");

        // Mark nonce used
        usedNonces[msg.sender][nonce] = true;

        // Calculate fee (0.05%)
        uint256 fee = (amount * FEE_BPS) / BPS_BASE;
        uint256 userAmount = amount - fee;

        // Transfer from treasury
        require(token.transferFrom(treasury, msg.sender, userAmount), "Transfer to user failed");
        if (fee > 0) {
            require(token.transferFrom(treasury, feeWallet, fee), "Transfer fee failed");
        }

        emit Claimed(msg.sender, userAmount, fee, nonce);
    }

    // ── Admin ──────────────────────────────────────────────────────────────

    function setSigner(address newSigner) external onlyOwner {
        require(newSigner != address(0), "signer=0");
        signer = newSigner;
        emit SignerUpdated(newSigner);
    }

    function setFeeWallet(address newFeeWallet) external onlyOwner {
        require(newFeeWallet != address(0), "feeWallet=0");
        feeWallet = newFeeWallet;
        emit FeeWalletUpdated(newFeeWallet);
    }

    function setTreasury(address newTreasury) external onlyOwner {
        require(newTreasury != address(0), "treasury=0");
        treasury = newTreasury;
        emit TreasuryUpdated(newTreasury);
    }
}
