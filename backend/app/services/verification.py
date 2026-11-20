"""Email ownership verification via one-time codes.

A 6-digit code is emailed to the applicant; only its SHA-256 hash is stored,
with an expiry, a resend cooldown, and an attempt limit. Changing the email
on a draft resets verification (handled in the application service).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models
from app.adapters.email import EmailMessage
from app.audit import record_event
from app.config import get_settings

log = structlog.get_logger("verification")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _as_aware(value: datetime | None) -> datetime | None:
    # SQLite returns naive datetimes; normalise for comparison.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def build_otp_email(to: str, first_name: str, code: str) -> EmailMessage:
    subject = "Your verification code"
    text = (
        f"Dear {first_name or 'Applicant'},\n\n"
        f"Your verification code is: {code}\n\n"
        "It expires in 10 minutes. If you didn't request this, you can ignore this email."
    )
    html = (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto\">"
        f"<p>Dear {first_name or 'Applicant'},</p>"
        f"<p>Your verification code is:</p>"
        f"<p style=\"font-size:28px;font-weight:700;letter-spacing:6px\">{code}</p>"
        "<p>It expires in 10 minutes. If you didn't request this, you can ignore this "
        "email.</p></div>"
    )
    return EmailMessage(to=to, subject=subject, text=text, html=html)


def start_email_verification(db: Session, application: models.Application) -> str:
    """Generate and store a new OTP; returns the plaintext code for sending."""
    settings = get_settings()
    if not application.email:
        raise HTTPException(status_code=400, detail="Provide your personal details first")
    if application.email_verified:
        raise HTTPException(status_code=409, detail="Email address is already verified")
    sent_at = _as_aware(application.email_otp_sent_at)
    if sent_at and (_utcnow() - sent_at) < timedelta(seconds=settings.otp_resend_seconds):
        raise HTTPException(
            status_code=429, detail="Please wait a moment before requesting another code"
        )
    code = f"{secrets.randbelow(1_000_000):06d}"
    application.email_otp_hash = _hash_code(code)
    application.email_otp_expires_at = _utcnow() + timedelta(seconds=settings.otp_expiry_seconds)
    application.email_otp_sent_at = _utcnow()
    application.email_otp_attempts = 0
    record_event(db, application.id, "email_otp_sent")
    db.commit()
    return code


def confirm_email_verification(
    db: Session, application: models.Application, code: str
) -> None:
    settings = get_settings()
    if application.email_verified:
        raise HTTPException(status_code=409, detail="Email address is already verified")
    if not application.email_otp_hash:
        raise HTTPException(status_code=400, detail="Request a verification code first")
    expires_at = _as_aware(application.email_otp_expires_at)
    if expires_at is None or _utcnow() > expires_at:
        raise HTTPException(
            status_code=400, detail="That code has expired — request a new one"
        )
    if application.email_otp_attempts >= settings.otp_max_attempts:
        raise HTTPException(
            status_code=429, detail="Too many attempts — request a new code"
        )
    if not hmac.compare_digest(_hash_code(code.strip()), application.email_otp_hash):
        application.email_otp_attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="That code is not correct")
    application.email_verified = True
    application.email_otp_hash = None
    application.email_otp_expires_at = None
    application.email_otp_attempts = 0
    record_event(db, application.id, "email_verified")
    db.commit()
    log.info("email_verified", reference=application.reference)


def reset_email_verification(application: models.Application) -> None:
    application.email_verified = False
    application.email_otp_hash = None
    application.email_otp_expires_at = None
    application.email_otp_sent_at = None
    application.email_otp_attempts = 0
