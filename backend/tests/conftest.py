import os
import tempfile

_TMPDIR = tempfile.mkdtemp(prefix="bankforms-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMPDIR}/test.db"
os.environ["ENV"] = "test"
os.environ["KYC_PROVIDER"] = "mock"
os.environ["EMAIL_PROVIDER"] = "console"
os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"
# Point external lookups at unroutable endpoints: the BSB directory becomes
# unavailable (strict check skips) and nothing touches the network in tests.
os.environ["BSB_DIRECTORY_URL"] = "http://127.0.0.1:9/bsb.csv"
os.environ["ADDRESS_PROVIDER"] = "off"
os.environ["OTP_RESEND_SECONDS"] = "0"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app import models  # noqa: E402
from app.adapters.email import EmailMessage  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.providers import get_email_provider  # noqa: E402

ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}


class RecordingEmailProvider:
    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables(_schema):
    yield
    with SessionLocal() as db:
        db.execute(delete(models.AuditEvent))
        db.execute(delete(models.Application))
        db.commit()


@pytest.fixture()
def emails():
    recorder = RecordingEmailProvider()
    app.dependency_overrides[get_email_provider] = lambda: recorder
    yield recorder
    app.dependency_overrides.pop(get_email_provider, None)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def valid_sections(last_name: str = "Smith", email: str = "jane.smith@example.com") -> dict:
    return {
        "personal": {
            "title": "Ms",
            "first_name": "Jane",
            "last_name": last_name,
            "date_of_birth": "1990-04-12",
            "email": email,
            "phone": "+61 412 345 678",
        },
        "address": {
            "line1": "1 George Street",
            "line2": None,
            "city": "Sydney",
            "state": "NSW",
            "postcode": "2000",
            "country": "AU",
            "years_at_address": 5,
        },
        "financial": {
            "employment_status": "employed",
            "annual_income": 95000,
            "nationality": "AU",
            "tax_residency_country": "AU",
            "tfn": "876543210",
        },
        "investment": {
            "fund_code": "BAL",
            "initial_investment": 5000,
            "monthly_contribution": 250,
            "source_of_funds": "salary",
        },
        "bank": {
            "account_holder_name": "Jane Smith",
            "bsb": "062000",
            "account_number": "12345678",
        },
        "declarations": {
            "accepted_terms": True,
            "accepted_risk": True,
            "consent_kyc": True,
        },
    }


def verify_email(client: TestClient, app_id: str, headers: dict) -> None:
    sent = client.post(f"/api/v1/applications/{app_id}/verify-email", headers=headers)
    assert sent.status_code == 200, sent.text
    code = sent.json()["debug_code"]
    confirmed = client.post(
        f"/api/v1/applications/{app_id}/verify-email/confirm",
        json={"code": code},
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text


def create_filled_application(
    client: TestClient, *, verified: bool = True, **kwargs
) -> tuple[str, dict]:
    created = client.post("/api/v1/applications").json()
    headers = {"X-Resume-Token": created["resume_token"]}
    resp = client.put(
        f"/api/v1/applications/{created['id']}", json=valid_sections(**kwargs), headers=headers
    )
    assert resp.status_code == 200, resp.text
    if verified:
        verify_email(client, created["id"], headers)
    return created["id"], headers
