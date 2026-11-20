"""Builds and sends applicant notifications. Sending happens in FastAPI
background tasks so external email latency never blocks the response."""

from __future__ import annotations

from uuid import UUID

import structlog

from app.adapters.email import EmailError, EmailMessage, EmailProvider
from app.audit import record_event
from app.database import SessionLocal

log = structlog.get_logger("notifications")

_BRAND = "Example Bank Investments"


def _render(subject: str, greeting: str, lines: list[str]) -> tuple[str, str]:
    text = greeting + "\n\n" + "\n\n".join(lines) + f"\n\n{_BRAND}"
    paragraphs = "".join(f"<p>{line}</p>" for line in lines)
    html = (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;"
        "color:#1a2433\">"
        f"<h2 style=\"color:#0d3b66\">{_BRAND}</h2>"
        f"<p>{greeting}</p>{paragraphs}"
        f"<p style=\"color:#6b7686;font-size:12px\">This mailbox is not monitored. "
        "If you did not make this application, contact us immediately.</p></div>"
    )
    return text, html


def build_message(event: str, *, to: str, first_name: str, reference: str) -> EmailMessage:
    greeting = f"Dear {first_name},"
    if event == "received":
        subject = f"We've received your investment application ({reference})"
        lines = [
            f"Thank you for applying. Your application reference is {reference}.",
            "Your application is being reviewed by our team. We aim to complete reviews "
            "within 2 working days and will email you with the outcome.",
        ]
    elif event == "approved":
        subject = f"Your investment application {reference} has been approved"
        lines = [
            f"Great news — your application {reference} has been approved.",
            "Your account is being opened and your first contribution will be collected "
            "by Direct Debit from the account you provided.",
            "You will receive your welcome pack and login details separately.",
        ]
    elif event == "declined":
        subject = f"Update on your investment application {reference}"
        lines = [
            f"We're sorry — after reviewing your application {reference}, "
            "we are unable to open an account for you at this time.",
            "This decision was informed by identity and eligibility checks. You can "
            "contact us to discuss the decision or to request further information.",
        ]
    else:  # pragma: no cover
        raise ValueError(f"Unknown notification event: {event}")
    text, html = _render(subject, greeting, lines)
    return EmailMessage(to=to, subject=subject, text=text, html=html)


def send_notification(
    provider: EmailProvider, message: EmailMessage, application_id: UUID
) -> None:
    """Background-task entrypoint: sends the email and audits the outcome
    using its own database session."""
    try:
        provider.send(message)
        event_type, detail = "email_sent", {"subject": message.subject}
    except EmailError as exc:
        log.warning("notification_failed", subject=message.subject, error=str(exc))
        event_type, detail = "email_failed", {"subject": message.subject, "error": str(exc)[:200]}
    try:
        with SessionLocal() as db:
            record_event(db, application_id, event_type, detail)
            db.commit()
    except Exception:  # pragma: no cover - audit must never crash the worker
        log.exception("notification_audit_failed")
