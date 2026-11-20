from app.adapters.account_verification import AccountMatch, MockAccountVerificationProvider
from tests.conftest import create_filled_application, valid_sections, verify_email


def test_mock_provider_rules():
    provider = MockAccountVerificationProvider()

    def status(account):
        return provider.verify(bsb="062000", account_number=account, account_name="Jane").status

    assert status("12345678") is AccountMatch.FULL_MATCH
    assert status("12345699") is AccountMatch.NO_MATCH
    assert status("12345688") is AccountMatch.PARTIAL_MATCH
    assert status("12345677") is AccountMatch.UNAVAILABLE


def test_no_match_blocks_submission_and_stays_draft(client, emails):
    app_id, headers = create_filled_application(client)
    sections = valid_sections()
    sections["bank"]["account_number"] = "12345699"
    client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)

    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 400
    assert "your name" in resp.json()["detail"]["message"]

    # Still a draft: the applicant can correct the bank details and resubmit
    view = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    assert view["status"] == "DRAFT"

    sections["bank"]["account_number"] = "12345678"
    client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"


def test_provider_outage_does_not_block(client, emails):
    app_id, headers = create_filled_application(client)
    sections = valid_sections()
    sections["bank"]["account_number"] = "12345677"  # mock: unavailable
    client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)

    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"


def test_verification_recorded_in_audit(client, emails):
    from tests.conftest import ADMIN_HEADERS

    app_id, headers = create_filled_application(client)
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    detail = client.get(f"/api/v1/admin/applications/{app_id}", headers=ADMIN_HEADERS).json()
    events = {e["event_type"]: e for e in detail["audit"]}
    assert events["account_verification"]["detail"]["status"] == "full_match"


def test_email_verified_included_in_flow(client, emails):
    # verify_email helper exercised explicitly for completeness
    app_id, headers = create_filled_application(client, verified=False)
    verify_email(client, app_id, headers)
    view = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    assert view["email_verified"] is True
