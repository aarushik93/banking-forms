from datetime import date

from tests.conftest import valid_sections


def _create(client) -> tuple[str, dict]:
    created = client.post("/api/v1/applications").json()
    return created["id"], {"X-Resume-Token": created["resume_token"]}


def test_underage_applicant_rejected(client):
    app_id, headers = _create(client)
    sections = valid_sections()
    today = date.today()
    sections["personal"]["date_of_birth"] = f"{today.year - 17}-01-01"
    resp = client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    assert resp.status_code == 422
    assert "18" in resp.text


def test_bad_sort_code_rejected(client):
    app_id, headers = _create(client)
    sections = valid_sections()
    sections["bank"]["sort_code"] = "12-34-56"
    resp = client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    assert resp.status_code == 422


def test_investment_below_minimum_rejected(client):
    app_id, headers = _create(client)
    sections = valid_sections()
    sections["investment"]["initial_investment"] = 100
    resp = client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    assert resp.status_code == 422


def test_submit_incomplete_application(client):
    app_id, headers = _create(client)
    sections = {"personal": valid_sections()["personal"]}
    client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 400
    missing = resp.json()["detail"]["missing_sections"]
    assert "investment" in missing and "bank" in missing


def test_submit_without_consent(client):
    app_id, headers = _create(client)
    sections = valid_sections()
    sections["declarations"]["consent_kyc"] = False
    client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 400
    assert "declarations" in resp.json()["detail"]["message"].lower()


def test_submit_unknown_fund(client):
    app_id, headers = _create(client)
    sections = valid_sections()
    sections["investment"]["fund_code"] = "NOPE"
    client.put(f"/api/v1/applications/{app_id}", json=sections, headers=headers)
    resp = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert resp.status_code == 400
    assert "fund" in resp.json()["detail"]["message"].lower()
