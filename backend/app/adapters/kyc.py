"""Identity verification (KYC) providers.

`KycProvider` is the seam between the application service and any IDV vendor.
`ExperianCrossCoreProvider` talks to Experian's CrossCore API (OAuth2 token +
transaction submit); `MockKycProvider` is a deterministic stand-in for local
development, CI, and demos.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Protocol

import httpx
import structlog
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

log = structlog.get_logger("kyc")


class KycDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REFER = "REFER"
    REJECT = "REJECT"


@dataclass(frozen=True)
class KycApplicant:
    first_name: str
    last_name: str
    date_of_birth: date
    email: str
    phone: str
    address_line1: str
    address_line2: str | None
    city: str
    postcode: str
    country: str
    nino: str | None


@dataclass(frozen=True)
class KycResult:
    decision: KycDecision
    reference: str
    raw_decision: str


class KycError(Exception):
    """The provider could not produce a decision (network, auth, contract errors)."""


class KycProvider(Protocol):
    def verify(self, applicant: KycApplicant) -> KycResult: ...


class MockKycProvider:
    """Deterministic provider for dev/test.

    Surname "Refer" -> REFER, "Reject" -> REJECT, anything else -> ACCEPT.
    """

    def verify(self, applicant: KycApplicant) -> KycResult:
        surname = applicant.last_name.strip().upper()
        if surname == "REFER":
            decision = KycDecision.REFER
        elif surname == "REJECT":
            decision = KycDecision.REJECT
        else:
            decision = KycDecision.ACCEPT
        return KycResult(
            decision=decision,
            reference=f"MOCK-{uuid.uuid4().hex[:12].upper()}",
            raw_decision=decision.value,
        )


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


class ExperianCrossCoreProvider:
    """CrossCore client. The exact payload fields and decision elements depend on the
    workflow Experian configures for the tenant — adjust `_build_payload` and
    `_map_response` against the onboarding pack; everything else stays the same."""

    def __init__(
        self,
        *,
        base_url: str,
        token_path: str,
        kyc_path: str,
        client_id: str,
        client_secret: str,
        username: str = "",
        password: str = "",
        client: httpx.Client | None = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=10.0)
        self._token_path = token_path
        self._kyc_path = kyc_path
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds
        self._token: str | None = None
        self._token_expiry = 0.0

    # --- auth ---

    def _get_token(self) -> str:
        if self._token and time.monotonic() < self._token_expiry - 60:
            return self._token
        body: dict[str, str] = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        grant = "client_credentials"
        if self._username:
            body.update({"username": self._username, "password": self._password})
            grant = "password"
        resp = self._client.post(
            self._token_path,
            json=body,
            headers={"Content-Type": "application/json", "Grant_type": grant},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.monotonic() + int(data.get("expires_in", 1800))
        return self._token

    # --- request ---

    def _build_payload(self, applicant: KycApplicant) -> dict[str, Any]:
        contact: dict[str, Any] = {
            "id": "APPLICANT_1",
            "person": {
                "typeOfPerson": "APPLICANT",
                "names": [{"firstName": applicant.first_name, "surName": applicant.last_name}],
                "personDetails": {"dateOfBirth": applicant.date_of_birth.isoformat()},
            },
            "addresses": [
                {
                    "id": "ADDRESS_1",
                    "addressType": "CURRENT",
                    "street": applicant.address_line1,
                    "street2": applicant.address_line2 or "",
                    "postTown": applicant.city,
                    "postal": applicant.postcode,
                    "countryCode": applicant.country,
                }
            ],
            "emails": [{"id": "EMAIL_1", "email": applicant.email}],
            "telephones": [{"id": "PHONE_1", "number": applicant.phone}],
        }
        if applicant.nino:
            contact["identityDocuments"] = [
                {"documentType": "NATIONAL_INSURANCE_NUMBER", "documentNumber": applicant.nino}
            ]
        return {
            "header": {
                "requestType": "IdAndFraud",
                "clientReferenceId": uuid.uuid4().hex,
            },
            "payload": {
                "contacts": [contact],
                "application": {"productDetails": {"productType": "INVESTMENT"}},
            },
        }

    def _submit(self, applicant: KycApplicant) -> dict[str, Any]:
        token = self._get_token()
        payload = self._build_payload(applicant)
        resp = self._client.post(
            self._kyc_path, json=payload, headers={"Authorization": f"Bearer {token}"}
        )
        if resp.status_code == 401:
            # Token invalidated server-side; refresh once and retry.
            self._token = None
            token = self._get_token()
            resp = self._client.post(
                self._kyc_path, json=payload, headers={"Authorization": f"Bearer {token}"}
            )
        resp.raise_for_status()
        return resp.json()

    def _map_response(self, data: dict[str, Any]) -> KycResult:
        header = data.get("responseHeader", {})
        raw = str(header.get("overallResponse", {}).get("decision", "")).upper()
        mapping = {
            "ACCEPT": KycDecision.ACCEPT,
            "CONTINUE": KycDecision.ACCEPT,
            "REFER": KycDecision.REFER,
            "NODECISION": KycDecision.REFER,
            "REJECT": KycDecision.REJECT,
            "DECLINE": KycDecision.REJECT,
            "STOP": KycDecision.REJECT,
        }
        decision = mapping.get(raw)
        if decision is None:
            raise KycError(f"Unrecognised CrossCore decision: {raw!r}")
        reference = str(
            header.get("expRequestId") or header.get("clientReferenceId") or "UNKNOWN"
        )
        return KycResult(decision=decision, reference=reference, raw_decision=raw)

    def verify(self, applicant: KycApplicant) -> KycResult:
        retryer = Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=self._backoff_seconds, max=5),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        )
        try:
            data = retryer(self._submit, applicant)
        except KycError:
            raise
        except Exception as exc:
            log.warning("kyc_request_failed", error=str(exc))
            raise KycError(f"Experian request failed: {exc}") from exc
        return self._map_response(data)
