from __future__ import annotations

import hmac
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.database import get_db


def require_admin(x_admin_token: Annotated[str | None, Header()] = None) -> None:
    settings = get_settings()
    if not x_admin_token or not hmac.compare_digest(x_admin_token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token",
        )


def get_owned_application(
    application_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    x_resume_token: Annotated[str | None, Header()] = None,
) -> models.Application:
    application = db.get(models.Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if not x_resume_token or not hmac.compare_digest(x_resume_token, application.resume_token):
        raise HTTPException(status_code=403, detail="Invalid resume token")
    return application
