from tests.conftest import create_filled_application, valid_sections


def test_funds_seeded(client):
    funds = client.get("/api/v1/funds").json()
    codes = {f["code"] for f in funds}
    assert {"GEI", "BAL", "AFI", "ESG"} <= codes


def test_happy_path_approved(client, emails):
    app_id, headers = create_filled_application(client)
    emails.messages.clear()  # drop the OTP email; we assert on status emails

    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["kyc_status"] == "ACCEPT"
    assert body["reference"].startswith("MF-")

    assert len(emails.messages) == 1
    assert "approved" in emails.messages[0].subject.lower()
    assert emails.messages[0].to == "jane.smith@example.com"


def test_refer_goes_to_review(client, emails):
    app_id, headers = create_filled_application(client, last_name="Refer")
    emails.messages.clear()
    body = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers).json()
    assert body["status"] == "IN_REVIEW"
    assert body["kyc_status"] == "REFER"
    assert len(emails.messages) == 1
    assert "received" in emails.messages[0].subject.lower()


def test_reject_declines(client, emails):
    app_id, headers = create_filled_application(client, last_name="Reject")
    emails.messages.clear()
    body = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers).json()
    assert body["status"] == "DECLINED"
    assert body["kyc_status"] == "REJECT"
    assert len(emails.messages) == 1


def test_resubmit_after_decision_conflicts(client, emails):
    app_id, headers = create_filled_application(client)
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 409


def test_view_masks_account_number(client):
    app_id, headers = create_filled_application(client)
    view = client.get(f"/api/v1/applications/{app_id}", headers=headers).json()
    assert view["bank"]["account_number_masked"] == "****5678"
    assert "12345678" not in str(view)


def test_resume_token_enforced(client):
    app_id, _ = create_filled_application(client)
    assert client.get(f"/api/v1/applications/{app_id}").status_code == 403
    bad = {"X-Resume-Token": "wrong-token"}
    assert client.get(f"/api/v1/applications/{app_id}", headers=bad).status_code == 403
    assert (
        client.put(f"/api/v1/applications/{app_id}", json=valid_sections(), headers=bad)
    ).status_code == 403


def test_unknown_application_404(client):
    resp = client.get(
        "/api/v1/applications/00000000-0000-0000-0000-000000000000",
        headers={"X-Resume-Token": "x"},
    )
    assert resp.status_code == 404


def test_cannot_edit_after_submission(client, emails):
    app_id, headers = create_filled_application(client)
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    resp = client.put(
        f"/api/v1/applications/{app_id}", json=valid_sections(), headers=headers
    )
    assert resp.status_code == 409


def test_health_endpoints(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").status_code == 200
