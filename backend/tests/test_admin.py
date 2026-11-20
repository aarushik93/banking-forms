from tests.conftest import ADMIN_HEADERS, create_filled_application


def test_admin_requires_token(client):
    assert client.get("/api/v1/admin/applications").status_code == 401
    bad = {"X-Admin-Token": "nope"}
    assert client.get("/api/v1/admin/applications", headers=bad).status_code == 401


def test_admin_list_and_filter(client, emails):
    app_id, headers = create_filled_application(client, last_name="Refer")
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)

    rows = client.get("/api/v1/admin/applications", headers=ADMIN_HEADERS).json()
    assert any(r["id"] == app_id for r in rows)

    in_review = client.get(
        "/api/v1/admin/applications", params={"status": "IN_REVIEW"}, headers=ADMIN_HEADERS
    ).json()
    assert [r["id"] for r in in_review] == [app_id]
    assert in_review[0]["applicant_name"] == "Jane Refer"

    assert (
        client.get(
            "/api/v1/admin/applications", params={"status": "BOGUS"}, headers=ADMIN_HEADERS
        ).status_code
        == 422
    )


def test_admin_detail_includes_audit_and_masked_bank(client, emails):
    app_id, headers = create_filled_application(client, last_name="Refer")
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)

    detail = client.get(f"/api/v1/admin/applications/{app_id}", headers=ADMIN_HEADERS).json()
    events = [e["event_type"] for e in detail["audit"]]
    assert "application_created" in events
    assert "application_submitted" in events
    assert "kyc_completed" in events
    assert detail["bank"]["account_number_masked"] == "****5678"
    assert detail["kyc_reference"].startswith("MOCK-")


def test_admin_decision_approves_and_emails(client, emails):
    app_id, headers = create_filled_application(client, last_name="Refer")
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    emails.messages.clear()

    resp = client.post(
        f"/api/v1/admin/applications/{app_id}/decision",
        json={"decision": "approve", "note": "Verified manually"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["decided_by"] == "admin"
    assert len(emails.messages) == 1
    assert "approved" in emails.messages[0].subject.lower()


def test_admin_decision_requires_in_review(client, emails):
    app_id, headers = create_filled_application(client)
    client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    resp = client.post(
        f"/api/v1/admin/applications/{app_id}/decision",
        json={"decision": "decline"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 409
