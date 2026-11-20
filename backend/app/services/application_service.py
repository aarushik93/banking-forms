from __future__ import annotations

import secrets
from datetime import UTC, datetime

import structlog
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.adapters.account_verification import AccountMatch, AccountVerificationProvider
from app.adapters.kyc import KycApplicant, KycDecision, KycError, KycProvider
from app.audit import record_event
from app.config import get_settings
from app.services.bsb import get_bsb_service
from app.services.verification import reset_email_verification

log = structlog.get_logger("applications")

_REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def generate_reference() -> str:
    return "MF-" + "".join(secrets.choice(_REFERENCE_ALPHABET) for _ in range(8))


def create_application(db: Session) -> models.Application:
    for _ in range(5):
        reference = generate_reference()
        exists = db.scalar(
            select(models.Application.id).where(models.Application.reference == reference)
        )
        if not exists:
            break
    else:  # pragma: no cover - 5 collisions in a 32^8 space
        raise HTTPException(status_code=500, detail="Could not allocate a reference")

    application = models.Application(
        reference=reference,
        resume_token=secrets.token_urlsafe(32)[:64],
        status=models.ApplicationStatus.DRAFT.value,
    )
    db.add(application)
    db.flush()
    record_event(db, application.id, "application_created")
    db.commit()
    log.info("application_created", reference=reference)
    return application


_SECTION_FIELD_MAP: dict[str, dict[str, str]] = {
    "personal": {
        "title": "title",
        "first_name": "first_name",
        "last_name": "last_name",
        "date_of_birth": "date_of_birth",
        "email": "email",
        "phone": "phone",
    },
    "address": {
        "line1": "address_line1",
        "line2": "address_line2",
        "city": "city",
        "state": "state",
        "postcode": "postcode",
        "country": "country",
        "years_at_address": "years_at_address",
    },
    "financial": {
        "employment_status": "employment_status",
        "annual_income": "annual_income",
        "nationality": "nationality",
        "tax_residency_country": "tax_residency_country",
        "tfn": "tfn",
    },
    "investment": {
        "fund_code": "fund_code",
        "initial_investment": "initial_investment",
        "monthly_contribution": "monthly_contribution",
        "source_of_funds": "source_of_funds",
    },
    "bank": {
        "account_holder_name": "account_holder_name",
        "bsb": "bsb",
        "account_number": "account_number",
    },
    "declarations": {
        "accepted_terms": "accepted_terms",
        "accepted_risk": "accepted_risk",
        "consent_kyc": "consent_kyc",
    },
}


def apply_draft_update(
    db: Session, application: models.Application, update: schemas.DraftUpdate
) -> models.Application:
    if application.status != models.ApplicationStatus.DRAFT.value:
        raise HTTPException(
            status_code=409, detail="Application has been submitted and can no longer be edited"
        )
    previous_email = application.email
    updated_sections: list[str] = []
    for section_name, field_map in _SECTION_FIELD_MAP.items():
        section = getattr(update, section_name)
        if section is None:
            continue
        for schema_field, model_field in field_map.items():
            setattr(application, model_field, getattr(section, schema_field))
        updated_sections.append(section_name)
    if "personal" in updated_sections and application.email != previous_email:
        # A new email address must be verified again.
        reset_email_verification(application)
        record_event(db, application.id, "email_changed", {"verification_reset": True})
    if updated_sections:
        record_event(db, application.id, "draft_updated", {"sections": updated_sections})
        db.commit()
    return application


def missing_sections(application: models.Application) -> list[str]:
    checks = {
        "personal": application.first_name is not None,
        "address": application.address_line1 is not None,
        "financial": application.employment_status is not None,
        "investment": application.fund_code is not None,
        "bank": application.bsb is not None,
    }
    return [name for name, present in checks.items() if not present]


def _to_kyc_applicant(application: models.Application) -> KycApplicant:
    assert application.first_name and application.last_name and application.date_of_birth
    return KycApplicant(
        first_name=application.first_name,
        last_name=application.last_name,
        date_of_birth=application.date_of_birth,
        email=application.email or "",
        phone=application.phone or "",
        address_line1=application.address_line1 or "",
        address_line2=application.address_line2,
        city=application.city or "",
        state=application.state or "",
        postcode=application.postcode or "",
        country=application.country or "AU",
    )


def _check_bank_account(
    db: Session,
    application: models.Application,
    account_verifier: AccountVerificationProvider,
) -> None:
    assert application.bsb and application.account_number

    settings = get_settings()
    bsb_service = get_bsb_service()
    if (
        settings.bsb_strict
        and bsb_service.available
        and bsb_service.lookup(application.bsb) is None
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "That BSB isn't in the national BSB directory — "
                "please check your bank details"
            },
        )

    result = account_verifier.verify(
        bsb=application.bsb,
        account_number=application.account_number,
        account_name=application.account_holder_name or "",
    )
    record_event(
        db,
        application.id,
        "account_verification",
        {"status": result.status.value, "reference": result.reference},
    )
    if result.status is AccountMatch.NO_MATCH:
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={
                "message": "We couldn't confirm that bank account is held in your name. "
                "Please check the account details — the funding account must be yours."
            },
        )
    application.account_verification_status = result.status.value


def submit_application(
    db: Session,
    application: models.Application,
    kyc: KycProvider,
    account_verifier: AccountVerificationProvider,
) -> models.Application:
    retry_after_error = (
        application.status == models.ApplicationStatus.SUBMITTED.value
        and application.kyc_status == models.KycStatus.ERROR.value
    )
    if application.status != models.ApplicationStatus.DRAFT.value and not retry_after_error:
        raise HTTPException(status_code=409, detail="Application has already been submitted")

    missing = missing_sections(application)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "Application is incomplete", "missing_sections": missing},
        )
    if not application.email_verified:
        raise HTTPException(
            status_code=400,
            detail={"message": "Please verify your email address before submitting"},
        )
    if not (
        application.accepted_terms and application.accepted_risk and application.consent_kyc
    ):
        raise HTTPException(
            status_code=400,
            detail={"message": "All declarations must be accepted before submission"},
        )
    fund = db.scalar(
        select(models.Fund).where(
            models.Fund.code == application.fund_code, models.Fund.active.is_(True)
        )
    )
    if fund is None:
        raise HTTPException(status_code=400, detail={"message": "Unknown or inactive fund"})

    if not retry_after_error:
        _check_bank_account(db, application, account_verifier)
        application.status = models.ApplicationStatus.SUBMITTED.value
        application.submitted_at = _utcnow()
        record_event(db, application.id, "application_submitted")
        db.commit()  # persist the submission before calling out to the KYC provider

    try:
        result = kyc.verify(_to_kyc_applicant(application))
    except KycError as exc:
        application.kyc_status = models.KycStatus.ERROR.value
        application.kyc_checked_at = _utcnow()
        record_event(db, application.id, "kyc_error", {"error": str(exc)[:200]})
        db.commit()
        log.warning("kyc_error", reference=application.reference, error=str(exc))
        return application

    application.kyc_status = result.decision.value
    application.kyc_reference = result.reference
    application.kyc_checked_at = _utcnow()

    previous_status = application.status
    if result.decision is KycDecision.ACCEPT:
        application.status = models.ApplicationStatus.APPROVED.value
        application.decided_at = _utcnow()
        application.decided_by = "auto"
    elif result.decision is KycDecision.REFER:
        application.status = models.ApplicationStatus.IN_REVIEW.value
    else:
        application.status = models.ApplicationStatus.DECLINED.value
        application.decided_at = _utcnow()
        application.decided_by = "auto"

    record_event(
        db,
        application.id,
        "kyc_completed",
        {"decision": result.decision.value, "provider_reference": result.reference},
    )
    record_event(
        db,
        application.id,
        "status_changed",
        {"from": previous_status, "to": application.status},
    )
    db.commit()
    log.info(
        "application_decisioned",
        reference=application.reference,
        status=application.status,
        kyc_decision=result.decision.value,
    )
    return application


def admin_decide(
    db: Session,
    application: models.Application,
    decision: schemas.DecisionRequest,
) -> models.Application:
    if application.status != models.ApplicationStatus.IN_REVIEW.value:
        raise HTTPException(
            status_code=409, detail="Only applications in review can be decided manually"
        )
    previous_status = application.status
    application.status = (
        models.ApplicationStatus.APPROVED.value
        if decision.decision == "approve"
        else models.ApplicationStatus.DECLINED.value
    )
    application.decided_at = _utcnow()
    application.decided_by = "admin"
    application.decision_note = decision.note
    record_event(db, application.id, "admin_decision", {"decision": decision.decision})
    record_event(
        db,
        application.id,
        "status_changed",
        {"from": previous_status, "to": application.status},
    )
    db.commit()
    log.info(
        "admin_decision", reference=application.reference, status=application.status
    )
    return application


# --- view builders ---


def _mask_account_number(account_number: str) -> str:
    return "****" + account_number[-4:]


def to_view(application: models.Application) -> schemas.ApplicationView:
    personal = None
    if application.first_name is not None:
        personal = schemas.PersonalDetails.model_construct(
            title=application.title,
            first_name=application.first_name,
            last_name=application.last_name,
            date_of_birth=application.date_of_birth,
            email=application.email,
            phone=application.phone,
        )
    address = None
    if application.address_line1 is not None:
        address = schemas.AddressDetails.model_construct(
            line1=application.address_line1,
            line2=application.address_line2,
            city=application.city,
            state=application.state,
            postcode=application.postcode,
            country=application.country,
            years_at_address=application.years_at_address,
        )
    financial = None
    if application.employment_status is not None:
        financial = schemas.FinancialDetails.model_construct(
            employment_status=application.employment_status,
            annual_income=application.annual_income,
            nationality=application.nationality,
            tax_residency_country=application.tax_residency_country,
            tfn=application.tfn,
        )
    investment = None
    if application.fund_code is not None:
        investment = schemas.InvestmentDetails.model_construct(
            fund_code=application.fund_code,
            initial_investment=application.initial_investment,
            monthly_contribution=application.monthly_contribution,
            source_of_funds=application.source_of_funds,
        )
    bank = None
    if application.bsb is not None and application.account_number is not None:
        bank = schemas.MaskedBankDetails(
            account_holder_name=application.account_holder_name or "",
            bsb=application.bsb,
            account_number_masked=_mask_account_number(application.account_number),
        )
    declarations = schemas.Declarations(
        accepted_terms=application.accepted_terms,
        accepted_risk=application.accepted_risk,
        consent_kyc=application.consent_kyc,
    )
    return schemas.ApplicationView(
        id=application.id,
        reference=application.reference,
        status=application.status,
        kyc_status=application.kyc_status,
        email_verified=application.email_verified,
        personal=personal,
        address=address,
        financial=financial,
        investment=investment,
        bank=bank,
        declarations=declarations,
        submitted_at=application.submitted_at,
    )


def to_admin_detail(
    application: models.Application, audit_events: list[models.AuditEvent]
) -> schemas.AdminApplicationDetail:
    base = to_view(application)
    return schemas.AdminApplicationDetail(
        **base.model_dump(),
        kyc_reference=application.kyc_reference,
        kyc_checked_at=application.kyc_checked_at,
        decided_at=application.decided_at,
        decided_by=application.decided_by,
        decision_note=application.decision_note,
        audit=[
            schemas.AuditEventOut(
                event_type=e.event_type, detail=e.detail, created_at=e.created_at
            )
            for e in audit_events
        ],
    )


def to_admin_summary(application: models.Application) -> schemas.AdminApplicationSummary:
    name = None
    if application.first_name:
        name = f"{application.first_name} {application.last_name or ''}".strip()
    return schemas.AdminApplicationSummary(
        id=application.id,
        reference=application.reference,
        status=application.status,
        kyc_status=application.kyc_status,
        applicant_name=name,
        email=application.email,
        fund_code=application.fund_code,
        initial_investment=application.initial_investment,
        created_at=application.created_at,
        submitted_at=application.submitted_at,
    )
