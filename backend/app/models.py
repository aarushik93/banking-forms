from __future__ import annotations

import enum
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ApplicationStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"  # submitted but KYC not yet concluded (e.g. provider error)
    IN_REVIEW = "IN_REVIEW"  # KYC referred; awaiting manual decision
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


class KycStatus(enum.StrEnum):
    ACCEPT = "ACCEPT"
    REFER = "REFER"
    REJECT = "REJECT"
    ERROR = "ERROR"


def utcnow() -> datetime:
    return datetime.now(UTC)


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    risk_level: Mapped[int] = mapped_column(Integer)  # 1 (low) - 7 (high), SRRI style
    annual_charge_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    resume_token: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(20), default=ApplicationStatus.DRAFT.value, index=True
    )

    # Personal
    title: Mapped[str | None] = mapped_column(String(10))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(30))

    # Address
    address_line1: Mapped[str | None] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))  # suburb
    state: Mapped[str | None] = mapped_column(String(3))
    postcode: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str | None] = mapped_column(String(2))
    years_at_address: Mapped[int | None] = mapped_column(Integer)

    # Financial / tax
    employment_status: Mapped[str | None] = mapped_column(String(30))
    annual_income: Mapped[int | None] = mapped_column(Integer)
    nationality: Mapped[str | None] = mapped_column(String(2))
    tax_residency_country: Mapped[str | None] = mapped_column(String(2))
    tfn: Mapped[str | None] = mapped_column(String(9))  # Tax File Number (tax use only)

    # Investment
    fund_code: Mapped[str | None] = mapped_column(String(20))
    initial_investment: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    monthly_contribution: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    source_of_funds: Mapped[str | None] = mapped_column(String(30))

    # Bank (direct debit funding)
    account_holder_name: Mapped[str | None] = mapped_column(String(100))
    bsb: Mapped[str | None] = mapped_column(String(6))
    account_number: Mapped[str | None] = mapped_column(String(9))

    # Declarations
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_kyc: Mapped[bool] = mapped_column(Boolean, default=False)

    # KYC outcome
    kyc_status: Mapped[str | None] = mapped_column(String(20))
    kyc_reference: Mapped[str | None] = mapped_column(String(100))
    kyc_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Final decision
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[str | None] = mapped_column(String(20))  # auto | admin
    decision_note: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("applications.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
