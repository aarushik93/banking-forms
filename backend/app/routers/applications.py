from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.adapters.email import EmailProvider
from app.adapters.kyc import KycProvider
from app.database import get_db
from app.dependencies import get_owned_application
from app.providers import get_email_provider, get_kyc_provider
from app.ratelimit import rate_limit
from app.services import application_service, notifications

router = APIRouter(prefix="/applications", tags=["applications"])

_STATUS_MESSAGES = {
    models.ApplicationStatus.APPROVED.value: (
        "Congratulations — your application has been approved. "
        "A confirmation email is on its way."
    ),
    models.ApplicationStatus.IN_REVIEW.value: (
        "Your application has been received and is being reviewed by our team. "
        "We'll email you with the outcome."
    ),
    models.ApplicationStatus.DECLINED.value: (
        "We're unable to open an account for you at this time. "
        "We've emailed you more information."
    ),
    models.ApplicationStatus.SUBMITTED.value: (
        "We couldn't complete our identity checks just now. "
        "Your application is saved — please try submitting again shortly."
    ),
}

_STATUS_EMAIL_EVENT = {
    models.ApplicationStatus.APPROVED.value: "approved",
    models.ApplicationStatus.IN_REVIEW.value: "received",
    models.ApplicationStatus.DECLINED.value: "declined",
}


def queue_status_email(
    background: BackgroundTasks,
    email_provider: EmailProvider,
    application: models.Application,
) -> None:
    event = _STATUS_EMAIL_EVENT.get(application.status)
    if event is None or not application.email:
        return
    message = notifications.build_message(
        event,
        to=application.email,
        first_name=application.first_name or "Applicant",
        reference=application.reference,
    )
    background.add_task(
        notifications.send_notification, email_provider, message, application.id
    )


@router.post(
    "",
    response_model=schemas.ApplicationCreated,
    status_code=201,
    dependencies=[Depends(rate_limit)],
)
def create_application(db: Annotated[Session, Depends(get_db)]) -> schemas.ApplicationCreated:
    application = application_service.create_application(db)
    return schemas.ApplicationCreated(
        id=application.id,
        reference=application.reference,
        resume_token=application.resume_token,
    )


@router.get("/{application_id}", response_model=schemas.ApplicationView)
def get_application(
    application: Annotated[models.Application, Depends(get_owned_application)],
) -> schemas.ApplicationView:
    return application_service.to_view(application)


@router.put("/{application_id}", response_model=schemas.ApplicationView)
def update_application(
    update: schemas.DraftUpdate,
    application: Annotated[models.Application, Depends(get_owned_application)],
    db: Annotated[Session, Depends(get_db)],
) -> schemas.ApplicationView:
    application = application_service.apply_draft_update(db, application, update)
    return application_service.to_view(application)


@router.post(
    "/{application_id}/submit",
    response_model=schemas.SubmitResponse,
    dependencies=[Depends(rate_limit)],
)
def submit_application(
    background: BackgroundTasks,
    application: Annotated[models.Application, Depends(get_owned_application)],
    db: Annotated[Session, Depends(get_db)],
    kyc: Annotated[KycProvider, Depends(get_kyc_provider)],
    email_provider: Annotated[EmailProvider, Depends(get_email_provider)],
) -> schemas.SubmitResponse:
    application = application_service.submit_application(db, application, kyc)
    queue_status_email(background, email_provider, application)
    return schemas.SubmitResponse(
        id=application.id,
        reference=application.reference,
        status=application.status,
        kyc_status=application.kyc_status,
        message=_STATUS_MESSAGES.get(application.status, ""),
    )
