import os
import tempfile

_TMPDIR = tempfile.mkdtemp(prefix="bankforms-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMPDIR}/test.db"
os.environ["ENV"] = "test"
os.environ["KYC_PROVIDER"] = "mock"
os.environ["EMAIL_PROVIDER"] = "console"
os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
os.environ["RATE_LIMIT_PER_MINUTE"] = "0"

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
            "phone": "+44 7700 900123",
        },
        "address": {
            "line1": "1 High Street",
            "line2": None,
            "city": "London",
            "postcode": "SW1A 1AA",
            "country": "GB",
            "years_at_address": 5,
        },
        "financial": {
            "employment_status": "employed",
            "annual_income": 55000,
            "nationality": "GB",
            "tax_residency_country": "GB",
            "nino": "QQ123456C",
        },
        "investment": {
            "fund_code": "BAL",
            "initial_investment": 5000,
            "monthly_contribution": 250,
            "source_of_funds": "salary",
        },
        "bank": {
            "account_holder_name": "Jane Smith",
            "sort_code": "123456",
            "account_number": "12345678",
        },
        "declarations": {
            "accepted_terms": True,
            "accepted_risk": True,
            "consent_kyc": True,
        },
    }


def create_filled_application(client: TestClient, **kwargs) -> tuple[str, dict]:
    created = client.post("/api/v1/applications").json()
    headers = {"X-Resume-Token": created["resume_token"]}
    resp = client.put(
        f"/api/v1/applications/{created['id']}", json=valid_sections(**kwargs), headers=headers
    )
    assert resp.status_code == 200, resp.text
    return created["id"], headers
