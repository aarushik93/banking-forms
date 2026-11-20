"""Provider factories used as FastAPI dependencies (overridable in tests)."""

from __future__ import annotations

from functools import lru_cache

from app.adapters.email import ConsoleEmailProvider, EmailProvider, SendGridEmailProvider
from app.adapters.kyc import ExperianCrossCoreProvider, KycProvider, MockKycProvider
from app.config import get_settings


@lru_cache
def _kyc_singleton() -> KycProvider:
    settings = get_settings()
    if settings.kyc_provider == "experian":
        return ExperianCrossCoreProvider(
            base_url=settings.experian_base_url,
            token_path=settings.experian_token_path,
            kyc_path=settings.experian_kyc_path,
            client_id=settings.experian_client_id,
            client_secret=settings.experian_client_secret,
            username=settings.experian_username,
            password=settings.experian_password,
        )
    return MockKycProvider()


@lru_cache
def _email_singleton() -> EmailProvider:
    settings = get_settings()
    if settings.email_provider == "sendgrid":
        return SendGridEmailProvider(
            api_key=settings.sendgrid_api_key,
            from_email=settings.email_from,
            from_name=settings.email_from_name,
        )
    return ConsoleEmailProvider()


def get_kyc_provider() -> KycProvider:
    return _kyc_singleton()


def get_email_provider() -> EmailProvider:
    return _email_singleton()
