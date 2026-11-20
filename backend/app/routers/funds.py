from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("", response_model=list[schemas.FundOut])
def list_funds(db: Annotated[Session, Depends(get_db)]) -> list[models.Fund]:
    return list(
        db.scalars(
            select(models.Fund)
            .where(models.Fund.active.is_(True))
            .order_by(models.Fund.risk_level, models.Fund.code)
        )
    )
