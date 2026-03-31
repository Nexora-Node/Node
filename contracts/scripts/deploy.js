const hre = require("hardhat");
require("dotenv").config();

const TOKEN_ADDRESS   = "0xE0a4a9d3263ee93E167196954Ea4684418911E24";
const TREASURY        = process.env.TREASURY_ADDRESS;
const FEE_WALLET      = process.env.FEE_WALLET_ADDRESS;
const SIGNER          = process.env.SIGNER_ADDRESS;   // backend hot wallet
const OWNER           = process.env.OWNER_ADDRESS;

async function main() {
  if (!TREASURY || !FEE_WALLET || !SIGNER || !OWNER) {
    throw new Error("Set TREASURY_ADDRESS, FEE_WALLET_ADDRESS, SIGNER_ADDRESS, OWNER_ADDRESS in .env");
  }

  console.log("Deploying ClaimDistributor...");
  console.log("  Token:     ", TOKEN_ADDRESS);
  console.log("  Treasury:  ", TREASURY);
  console.log("  FeeWallet: ", FEE_WALLET);
  console.log("  Signer:    ", SIGNER);
  console.log("  Owner:     ", OWNER);

  const ClaimDistributor = await hre.ethers.getContractFactory("ClaimDistributor");
  const dist = await ClaimDistributor.deploy(
    TOKEN_ADDRESS,
    TREASURY,
    FEE_WALLET,
    SIGNER,
    OWNER
  );
  await dist.waitForDeployment();

  const address = await dist.getAddress();
  console.log("\n✓ ClaimDistributor deployed:", address);
  // 200,000 NEXOR (18 decimals) — mining allocation only
  const MINING_ALLOCATION = (200_000n * 10n ** 18n).toString();

  console.log("\nNext steps:");
  console.log("1. From TREASURY wallet, approve ClaimDistributor for 200,000 NEXOR only:");
  console.log("   Go to Basescan → token contract → Write Contract → approve");
  console.log("   spender: " + address);
  console.log("   value:   " + MINING_ALLOCATION + "  (200000 * 10^18)");
  console.log("\n   Remaining 40,000 NEXOR stays in treasury — NOT approved.");
  console.log("\n2. Set in Railway env:");
  console.log("   CLAIM_DISTRIBUTOR_ADDRESS=" + address);
  console.log("   SIGNER_PRIVATE_KEY=<your signer private key>");
  console.log("\nVerify on Basescan:");
  console.log(`npx hardhat verify --network base ${address} ${TOKEN_ADDRESS} ${TREASURY} ${FEE_WALLET} ${SIGNER} ${OWNER}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
