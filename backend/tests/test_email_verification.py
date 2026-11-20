from tests.conftest import create_filled_application, valid_sections, verify_email


def _send(client, app_id, headers):
    return client.post(f"/api/v1/applications/{app_id}/verify-email", headers=headers)


def _confirm(client, app_id, headers, code):
    return client.post(
        f"/api/v1/applications/{app_id}/verify-email/confirm",
        json={"code": code},
        headers=headers,
    )


def test_submit_requires_verified_email(client, emails):
    app_id, headers = create_filled_application(client, verified=False)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 400
    assert "verify" in resp.json()["detail"]["message"].lower()


def test_full_otp_flow(client, emails):
    app_id, headers = create_filled_application(client, verified=False)

    sent = _send(client, app_id, headers)
    assert sent.status_code == 200
    body = sent.json()
    assert body["sent"] is True and body["debug_code"]

    # The code is emailed to the applicant
    assert any("verification code" in m.subject.lower() for m in emails.messages)
    assert body["debug_code"] in emails.messages[-1].text

    # Wrong code increments attempts but doesn't verify
    bad = "000000" if body["debug_code"] != "000000" else "111111"
    wrong = _confirm(client, app_id, headers, bad)
    assert wrong.status_code == 400

    confirmed = _confirm(client, app_id, headers, body["debug_code"])
    assert confirmed.status_code == 200
    assert confirmed.json()["email_verified"] is True

    # Re-sending or re-confirming after verification conflicts
    assert _send(client, app_id, headers).status_code == 409
    assert _confirm(client, app_id, headers, body["debug_code"]).status_code == 409


def test_attempt_limit(client, emails):
    app_id, headers = create_filled_application(client, verified=False)
    code = _send(client, app_id, headers).json()["debug_code"]
    bad = "999999" if code != "999999" else "888888"
    for _ in range(5):
        assert _confirm(client, app_id, headers, bad).status_code == 400
    assert _confirm(client, app_id, headers, bad).status_code == 429
    # Even the right code is locked out now
    assert _confirm(client, app_id, headers, code).status_code == 429


def test_changing_email_resets_verification(client, emails):
    app_id, headers = create_filled_application(client, verified=True)
    sections = {"personal": {**valid_sections()["personal"], "email": "new@example.com"}}
    view = client.put(
        f"/api/v1/applications/{app_id}", json=sections, headers=headers
    ).json()
    assert view["email_verified"] is False
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 400

    verify_email(client, app_id, headers)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 200


def test_send_requires_personal_details(client, emails):
    created = client.post("/api/v1/applications").json()
    headers = {"X-Resume-Token": created["resume_token"]}
    assert _send(client, created["id"], headers).status_code == 400
