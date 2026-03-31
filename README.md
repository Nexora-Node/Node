# Nexora Node

**Earn NEXORA tokens by running a lightweight node that helps secure the Base network.**

No GPU. No heavy computation. Just run the CLI and earn passively.

[![Backend](https://img.shields.io/badge/Backend-Railway-blueviolet)](https://node-production-712b.up.railway.app)
[![Dashboard](https://img.shields.io/badge/Dashboard-Vercel-black)](https://node-delta-ten.vercel.app)
[![Token](https://img.shields.io/badge/Token-Base%20Mainnet-blue)](https://basescan.org/token/0xE0a4a9d3263ee93E167196954Ea4684418911E24)
[![Contract](https://img.shields.io/badge/ClaimDistributor-Verified-green)](https://basescan.org/address/0xaeD12935DA40EFf65d919CCc4b77Df185f4A2cf0#code)

---

## What is Nexora?

Nexora is a distributed node network where users run lightweight CLI nodes and earn **NEXORA (NEXOR)** tokens based on uptime. Optionally, running a local Base/ETH/OP/BNB full node earns up to **5× bonus rewards**.

- **Token:** NEXORA (NEXOR) on Base Mainnet
- **Supply:** 240,000 NEXOR total (200,000 for mining, 40,000 reserved)
- **Model:** Smooth 5% decay every 24 days — rewards last ~100 years
- **Claim:** On-chain via ClaimDistributor contract (user pays gas)

---

## Quick Start

### Requirements
- Python 3.8+
- A referral code (get one from the community)

### Install

```bash
git clone https://github.com/Nexora-Node/Node
cd Node
pip install -r requirements.txt
```

### Register

```bash
cd cli
python main.py register --ref YOUR_REFERRAL_CODE
```

### Start Mining

```bash
python main.py start
```

The live dashboard opens automatically. Press **Ctrl+C** to stop.

---

## CLI Commands

| Command | Description |
|---|---|
| `python main.py register --ref CODE` | Register with a referral code |
| `python main.py start` | Start node + open live dashboard |
| `python main.py stop` | Stop running node |
| `python main.py status` | Show NEXORA balance and node status |
| `python main.py dashboard` | Open dashboard without starting node |
| `python main.py wallet 0x...` | Link EVM wallet for claiming |
| `python main.py claim` | Instructions to claim on web |

---

## Live Dashboard

When you run `python main.py start`, a live terminal dashboard opens:

```
====================================================================================================
                         NEXORA NODE DASHBOARD
====================================================================================================
  User: YourUsername   Node: [RUNNING]   2026-04-01 00:00:00
  Referral: ABCD1234  (share to invite others)

  NEXORA BALANCE
  Available   : 12.345678 NEXORA
  Total Earned: 12.345678 NEXORA   Claimed: 0.000000 NEXORA

  MINING INFO
  Rate: 0.289352 NEXORA/min  Epoch #0  Decay in 23.8d
  Supply: [##..................] 16/200000

  NODES (1 active)
  [ON] a1b2c3d4e5f6...  uptime 2h 15m  score 100/100

  LIVE LOG  (last 8 lines)
  [00:00:30] Node active — verifying Base network | uptime 0m | score 100/100
  [00:01:00] Node active — verifying Base network | uptime 1m | score 100/100
```

---

## Claiming NEXORA

1. Open [node-delta-ten.vercel.app](https://node-delta-ten.vercel.app)
2. Enter your username
3. Connect MetaMask and link your wallet
4. Click **Claim NEXORA**
5. Confirm the transaction (gas on Base, ~$0.01)

NEXORA transfers directly to your wallet. 0.05% fee goes to the DEX listing fund.

---

## Reward Formula

```
rate    = 0.289352 × 0.95^epoch   (NEXORA/min, decays 5% every 24 days)
earned  = (uptime_delta / 60) × rate × (node_score / 100)
```

| Epoch | Days | Rate | Period Emission |
|---|---|---|---|
| 0 | 0–23 | 0.2894 NEXORA/min | 10,000 NEXORA |
| 1 | 24–47 | 0.2749 NEXORA/min | 9,500 NEXORA |
| 2 | 48–71 | 0.2611 NEXORA/min | 9,025 NEXORA |
| ... | ... | ... | ... |

Total converges to exactly **200,000 NEXORA** over ~100 years.

---

## Token

| Property | Value |
|---|---|
| Name | NEXORA NODE |
| Symbol | NEXOR |
| Network | Base Mainnet |
| Contract | [`0xE0a4a9d3...`](https://basescan.org/token/0xE0a4a9d3263ee93E167196954Ea4684418911E24) |
| Distributor | [`0xaeD12935...`](https://basescan.org/address/0xaeD12935DA40EFf65d919CCc4b77Df185f4A2cf0#code) |
| Total Supply | 240,000 NEXOR |
| Decimals | 18 |

---

## Platform Support

| Platform | Supported |
|---|---|
| Windows | ✅ |
| Linux / VPS | ✅ |
| macOS | ✅ |
| Android (Termux) | ✅ |
| Raspberry Pi | ✅ |

---

## Documentation

Full docs at [github.com/Nexora-Node/Docs](https://github.com/Nexora-Node/Docs)

- [Introduction](https://github.com/Nexora-Node/Docs/blob/master/introduction.md)
- [How It Works](https://github.com/Nexora-Node/Docs/blob/master/how-it-works.md)
- [Reward System](https://github.com/Nexora-Node/Docs/blob/master/rewards.md)
- [Roadmap](https://github.com/Nexora-Node/Docs/blob/master/roadmap.md)

---

## License

MIT
