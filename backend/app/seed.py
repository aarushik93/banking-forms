from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models

DEFAULT_FUNDS: list[dict] = [
    {
        "code": "GEI",
        "name": "Global Equity Index",
        "description": "Passive tracker of developed-market global equities.",
        "risk_level": 6,
        "annual_charge_pct": Decimal("0.22"),
    },
    {
        "code": "BAL",
        "name": "Balanced Growth",
        "description": "Diversified multi-asset portfolio of equities and bonds.",
        "risk_level": 4,
        "annual_charge_pct": Decimal("0.45"),
    },
    {
        "code": "AFI",
        "name": "Australian Fixed Income",
        "description": "Investment-grade AUD corporate and government bonds.",
        "risk_level": 3,
        "annual_charge_pct": Decimal("0.35"),
    },
    {
        "code": "ESG",
        "name": "Sustainable Future Equity",
        "description": "Actively managed equities screened for ESG criteria.",
        "risk_level": 6,
        "annual_charge_pct": Decimal("0.55"),
    },
]


def seed_funds(db: Session) -> None:
    existing = set(db.scalars(select(models.Fund.code)).all())
    for fund in DEFAULT_FUNDS:
        if fund["code"] not in existing:
            db.add(models.Fund(**fund, active=True))
    db.commit()
