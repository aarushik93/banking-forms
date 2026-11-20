from tests.conftest import create_filled_application


def _track(client, reference, email="jane.smith@example.com", dob="1990-04-12"):
    return client.post(
        "/api/v1/applications/track",
        json={"reference": reference, "email": email, "date_of_birth": dob},
    )


def test_track_returns_status(client, emails):
    app_id, headers = create_filled_application(client)
    submitted = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers).json()

    resp = _track(client, submitted["reference"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "APPROVED"
    assert body["reference"] == submitted["reference"]
    assert body["submitted_at"] is not None
    # Status only — no personal or bank data in the response
    assert "email" not in body and "bank" not in str(body)


def test_track_is_case_and_whitespace_tolerant(client, emails):
    app_id, headers = create_filled_application(client)
    submitted = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers).json()
    resp = _track(client, f"  {submitted['reference'].lower()}  ")
    assert resp.status_code == 200


def test_track_rejects_mismatched_details(client, emails):
    app_id, headers = create_filled_application(client)
    submitted = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers).json()
    ref = submitted["reference"]

    assert _track(client, "MF-NOTREAL1").status_code == 404
    assert _track(client, ref, email="wrong@example.com").status_code == 404
    assert _track(client, ref, dob="1991-01-01").status_code == 404
