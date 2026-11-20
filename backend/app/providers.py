"""Provider factories used as FastAPI dependencies (overridable in tests)."""

from __future__ import annotations

from functools import lru_cache

from app.adapters.account_verification import (
    AccountVerificationProvider,
    DisabledAccountVerificationProvider,
    MockAccountVerificationProvider,
)
from app.adapters.address import (
    AddressLookupProvider,
    DisabledAddressProvider,
    GeoscapeAddressProvider,
    NominatimAddressProvider,
)
from app.adapters.email import (
    ConsoleEmailProvider,
    EmailProvider,
    ResendEmailProvider,
    SendGridEmailProvider,
)
from app.adapters.idmatrix import EquifaxIdMatrixProvider
from app.adapters.kyc import ExperianCrossCoreProvider, KycProvider, MockKycProvider
from app.config import get_settings


@lru_cache
def _kyc_singleton() -> KycProvider:
    settings = get_settings()
    if settings.kyc_provider == "idmatrix":
        return EquifaxIdMatrixProvider(
            url=settings.idmatrix_url,
            username=settings.idmatrix_username,
            password=settings.idmatrix_password,
            reason_for_enquiry=settings.idmatrix_reason_for_enquiry,
        )
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
    if settings.email_provider == "resend":
        return ResendEmailProvider(
            api_key=settings.resend_api_key,
            from_email=settings.email_from,
            from_name=settings.email_from_name,
        )
    if settings.email_provider == "sendgrid":
        return SendGridEmailProvider(
            api_key=settings.sendgrid_api_key,
            from_email=settings.email_from,
            from_name=settings.email_from_name,
        )
    return ConsoleEmailProvider()


@lru_cache
def _address_singleton() -> AddressLookupProvider:
    settings = get_settings()
    if settings.address_provider == "geoscape":
        return GeoscapeAddressProvider(
            api_key=settings.geoscape_api_key, base_url=settings.geoscape_base_url
        )
    if settings.address_provider == "nominatim":
        return NominatimAddressProvider(base_url=settings.nominatim_base_url)
    return DisabledAddressProvider()


@lru_cache
def _account_verification_singleton() -> AccountVerificationProvider:
    settings = get_settings()
    if settings.account_verification_provider == "off":
        return DisabledAccountVerificationProvider()
    return MockAccountVerificationProvider()


def get_kyc_provider() -> KycProvider:
    return _kyc_singleton()


def get_email_provider() -> EmailProvider:
    return _email_singleton()


def get_address_provider() -> AddressLookupProvider:
    return _address_singleton()


def get_account_verification_provider() -> AccountVerificationProvider:
    return _account_verification_singleton()
