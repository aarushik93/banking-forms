from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app import models


def record_event(
    db: Session,
    application_id: UUID,
    event_type: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Append an audit event. Detail must never contain applicant PII —
    only event metadata (section names, decisions, references)."""
    db.add(
        models.AuditEvent(application_id=application_id, event_type=event_type, detail=detail)
    )
