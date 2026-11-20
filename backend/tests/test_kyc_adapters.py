from datetime import date

import httpx
import pytest

from app.adapters.kyc import (
    ExperianCrossCoreProvider,
    KycApplicant,
    KycDecision,
    KycError,
    MockKycProvider,
)

APPLICANT = KycApplicant(
    first_name="Jane",
    last_name="Smith",
    date_of_birth=date(1990, 4, 12),
    email="jane@example.com",
    phone="+61 412 345 678",
    address_line1="1 George Street",
    address_line2=None,
    city="Sydney",
    state="NSW",
    postcode="2000",
    country="AU",
)


@pytest.mark.parametrize(
    ("last_name", "expected"),
    [("Smith", KycDecision.ACCEPT), ("Refer", KycDecision.REFER), ("Reject", KycDecision.REJECT)],
)
def test_mock_provider_decisions(last_name, expected):
    applicant = KycApplicant(**{**APPLICANT.__dict__, "last_name": last_name})
    result = MockKycProvider().verify(applicant)
    assert result.decision is expected
    assert result.reference.startswith("MOCK-")


def _provider(handler) -> ExperianCrossCoreProvider:
    client = httpx.Client(
        base_url="https://experian.test", transport=httpx.MockTransport(handler)
    )
    return ExperianCrossCoreProvider(
        base_url="https://experian.test",
        token_path="/oauth2/v1/token",
        kyc_path="/decisionanalytics/crosscore/v2/submit",
        client_id="cid",
        client_secret="secret",
        username="user",
        password="pass",
        client=client,
        backoff_seconds=0,
    )


def _cross_core_response(decision: str) -> dict:
    return {
        "responseHeader": {
            "expRequestId": "EXP-123",
            "overallResponse": {"decision": decision},
        }
    }


def test_experian_accept_flow():
    calls = {"token": 0, "submit": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/v1/token":
            calls["token"] += 1
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 1800})
        calls["submit"] += 1
        assert request.headers["Authorization"] == "Bearer tok"
        return httpx.Response(200, json=_cross_core_response("ACCEPT"))

    provider = _provider(handler)
    result = provider.verify(APPLICANT)
    assert result.decision is KycDecision.ACCEPT
    assert result.reference == "EXP-123"

    provider.verify(APPLICANT)
    assert calls["token"] == 1  # token is cached across calls
    assert calls["submit"] == 2


def test_experian_refer_mapping():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/v1/token":
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 1800})
        return httpx.Response(200, json=_cross_core_response("NODECISION"))

    assert _provider(handler).verify(APPLICANT).decision is KycDecision.REFER


def test_experian_retries_on_server_error():
    calls = {"submit": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/v1/token":
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 1800})
        calls["submit"] += 1
        if calls["submit"] < 3:
            return httpx.Response(502)
        return httpx.Response(200, json=_cross_core_response("ACCEPT"))

    result = _provider(handler).verify(APPLICANT)
    assert result.decision is KycDecision.ACCEPT
    assert calls["submit"] == 3


def test_experian_client_error_raises_kyc_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/v1/token":
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 1800})
        return httpx.Response(400, json={"error": "bad request"})

    with pytest.raises(KycError):
        _provider(handler).verify(APPLICANT)


def test_experian_unknown_decision_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/v1/token":
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 1800})
        return httpx.Response(200, json=_cross_core_response("WIBBLE"))

    with pytest.raises(KycError):
        _provider(handler).verify(APPLICANT)
