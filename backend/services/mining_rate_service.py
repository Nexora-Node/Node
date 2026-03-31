"""
Nexora Backend - Mining Rate Service
Smooth 5% decay every 24 days from mining_start.

Formula: rate = BASE_RATE * (0.95 ^ epoch)
Where epoch = floor(days_elapsed / 24)

Epoch 0  (day   0-23):  0.289350 NXR/min  → 10,000 NXR emitted
Epoch 1  (day  24-47):  0.274883 NXR/min  →  9,500 NXR emitted
Epoch 2  (day  48-71):  0.261138 NXR/min  →  9,025 NXR emitted
...
Total converges to 200,000 NXR over ~100 years.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from models import MiningConfig

# Base rate derived from geometric series:
# Total = BASE_RATE_PER_PERIOD / (1 - 0.95)
# 200,000 = R / 0.05  →  R = 10,000 NXR per first period (34,560 min)
# BASE_RATE = 10,000 / 34,560 = 0.289351851...
BASE_RATE_PER_MIN  = 10_000 / (24 * 24 * 60)   # 0.28935 NXR/min
DECAY_FACTOR       = 0.95                        # 5% reduction per epoch
EPOCH_DAYS         = 24                          # new epoch every 24 days
MINING_SUPPLY_CAP  = 200_000.0


def _get_config(db: Session) -> MiningConfig:
    cfg = db.query(MiningConfig).filter(MiningConfig.id == 1).first()
    if not cfg:
        cfg = MiningConfig(
            id=1,
            mining_start=datetime.utcnow(),
            halving_interval_days=EPOCH_DAYS,
            base_rate_per_min=BASE_RATE_PER_MIN,
            total_distributed=0.0,
            mining_supply_cap=MINING_SUPPLY_CAP,
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def current_epoch(db: Session) -> int:
    """Return current decay epoch (0-indexed)."""
    cfg = _get_config(db)
    elapsed_days = (datetime.utcnow() - cfg.mining_start).total_seconds() / 86400
    return int(elapsed_days // cfg.halving_interval_days)


def current_rate(db: Session) -> float:
    """
    Return current NXR/min rate after smooth decay.
    rate = BASE_RATE * 0.95^epoch
    """
    epoch = current_epoch(db)
    rate = BASE_RATE_PER_MIN * (DECAY_FACTOR ** epoch)
    return max(rate, 1e-9)  # never zero


def is_supply_exhausted(db: Session) -> bool:
    cfg = _get_config(db)
    return cfg.total_distributed >= cfg.mining_supply_cap


def add_distributed(db: Session, amount: float) -> float:
    """
    Add to total_distributed. Returns actual credited amount (capped at remaining).
    """
    cfg = _get_config(db)
    remaining = cfg.mining_supply_cap - cfg.total_distributed
    credited = min(amount, max(remaining, 0.0))
    if credited > 0:
        cfg.total_distributed += credited
        db.commit()
    return credited


def get_mining_info(db: Session) -> dict:
    cfg = _get_config(db)
    epoch = current_epoch(db)
    rate = current_rate(db)
    elapsed_days = (datetime.utcnow() - cfg.mining_start).total_seconds() / 86400
    days_until_next = cfg.halving_interval_days - (elapsed_days % cfg.halving_interval_days)

    return {
        "mining_start":          cfg.mining_start.isoformat(),
        "current_epoch":         epoch,
        "current_rate_per_min":  round(rate, 8),
        "decay_factor":          DECAY_FACTOR,
        "epoch_duration_days":   cfg.halving_interval_days,
        "days_until_next_decay": round(days_until_next, 2),
        "total_distributed":     round(cfg.total_distributed, 6),
        "mining_supply_cap":     cfg.mining_supply_cap,
        "remaining_supply":      round(cfg.mining_supply_cap - cfg.total_distributed, 6),
        "supply_exhausted":      is_supply_exhausted(db),
    }
