from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.adapters.email import EmailProvider
from app.database import get_db
from app.dependencies import require_admin
from app.providers import get_email_provider
from app.routers.applications import queue_status_email
from app.services import application_service

router = APIRouter(
    prefix="/admin/applications", tags=["admin"], dependencies=[Depends(require_admin)]
)

_VALID_STATUSES = {s.value for s in models.ApplicationStatus}


def _get_application(db: Session, application_id: UUID) -> models.Application:
    application = db.get(models.Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("", response_model=list[schemas.AdminApplicationSummary])
def list_applications(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str | None, Query()] = None,
) -> list[schemas.AdminApplicationSummary]:
    query = select(models.Application).order_by(models.Application.created_at.desc()).limit(200)
    if status is not None:
        if status not in _VALID_STATUSES:
            raise HTTPException(status_code=422, detail="Unknown status filter")
        query = query.where(models.Application.status == status)
    return [application_service.to_admin_summary(a) for a in db.scalars(query)]


@router.get("/{application_id}", response_model=schemas.AdminApplicationDetail)
def get_application(
    application_id: UUID, db: Annotated[Session, Depends(get_db)]
) -> schemas.AdminApplicationDetail:
    application = _get_application(db, application_id)
    audit_events = list(
        db.scalars(
            select(models.AuditEvent)
            .where(models.AuditEvent.application_id == application.id)
            .order_by(models.AuditEvent.created_at, models.AuditEvent.id)
        )
    )
    return application_service.to_admin_detail(application, audit_events)


@router.post("/{application_id}/decision", response_model=schemas.AdminApplicationDetail)
def decide_application(
    application_id: UUID,
    decision: schemas.DecisionRequest,
    background: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
) -> schemas.AdminApplicationDetail:
    application = _get_application(db, application_id)
    application = application_service.admin_decide(db, application, decision)
    queue_status_email(background, email_provider, application)
    audit_events = list(
        db.scalars(
            select(models.AuditEvent)
            .where(models.AuditEvent.application_id == application.id)
            .order_by(models.AuditEvent.created_at, models.AuditEvent.id)
        )
    )
    return application_service.to_admin_detail(application, audit_events)
