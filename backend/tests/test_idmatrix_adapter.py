from datetime import date

import httpx
import pytest

from app.adapters.idmatrix import EquifaxIdMatrixProvider
from app.adapters.kyc import KycApplicant, KycDecision, KycError

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

URL = "https://idmatrix.test/sys2/idmatrix-v4"


def _provider(handler) -> EquifaxIdMatrixProvider:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return EquifaxIdMatrixProvider(
        url=URL,
        username="idm-user",
        password="idm-pass",
        client=client,
        backoff_seconds=0,
    )


def _response_xml(outcome: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <idm:response xmlns:idm="http://vedaxml.com/vxml2/idmatrix-v4-0.xsd" enquiry-id="IDM-12345">
      <idm:response-outcome>
        <idm:overall-outcome>{outcome}</idm:overall-outcome>
      </idm:response-outcome>
      <idm:component-responses>
        <idm:verification-outcome>
          <idm:total-points>340</idm:total-points>
          <idm:indicator>{outcome}</idm:indicator>
        </idm:verification-outcome>
        <idm:verification-response>
          <idm:data-source>CREDIT_HEADER</idm:data-source>
          <idm:source-outcome>VERIFIED</idm:source-outcome>
        </idm:verification-response>
        <idm:verification-response>
          <idm:data-source>ELECTORAL_ROLL</idm:data-source>
          <idm:source-outcome>VERIFIED</idm:source-outcome>
        </idm:verification-response>
        <idm:watchlist-response>
          <idm:watchlist-outcome>CLEAR</idm:watchlist-outcome>
        </idm:watchlist-response>
      </idm:component-responses>
    </idm:response>
  </env:Body>
</env:Envelope>"""


_FAULT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <env:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>Authentication failed</faultstring>
    </env:Fault>
  </env:Body>
</env:Envelope>"""


def test_idmatrix_accept_and_request_contents():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode()
        captured["content_type"] = request.headers["Content-Type"]
        captured["soap_action"] = request.headers["SOAPAction"]
        return httpx.Response(200, text=_response_xml("ACCEPT"))

    result = _provider(handler).verify(APPLICANT)
    assert result.decision is KycDecision.ACCEPT
    assert result.reference == "IDM-12345"
    assert result.detail == {
        "total_points": 340,
        "watchlist": "CLEAR",
        "sources": {"CREDIT_HEADER": "VERIFIED", "ELECTORAL_ROLL": "VERIFIED"},
    }

    body = captured["body"]
    assert "<wsse:Username>idm-user</wsse:Username>" in body
    assert "<idm:family-name>Smith</idm:family-name>" in body
    assert "<idm:first-given-name>Jane</idm:first-given-name>" in body
    assert "<idm:date-of-birth>1990-04-12</idm:date-of-birth>" in body
    assert "1 George Street, Sydney, NSW, 2000" in body
    assert "<idm:consent>yes</idm:consent>" in body
    assert captured["content_type"].startswith("text/xml")
    assert captured["soap_action"] == "http://vedaxml.com/idmatrix/VerifyIdentity"


@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        ("REJECT", KycDecision.REJECT),
        ("REFER", KycDecision.REFER),
        ("CAUTION", KycDecision.REFER),
    ],
)
def test_idmatrix_outcome_mapping(outcome, expected):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_response_xml(outcome))

    assert _provider(handler).verify(APPLICANT).decision is expected


def test_idmatrix_soap_fault_fails_without_retry():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, text=_FAULT_XML)

    with pytest.raises(KycError, match="Authentication failed"):
        _provider(handler).verify(APPLICANT)
    assert calls["n"] == 1  # faults are contract errors, not transient


def test_idmatrix_retries_transient_errors():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(200, text=_response_xml("ACCEPT"))

    assert _provider(handler).verify(APPLICANT).decision is KycDecision.ACCEPT
    assert calls["n"] == 3


def test_idmatrix_unknown_outcome_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_response_xml("WIBBLE"))

    with pytest.raises(KycError, match="Unrecognised"):
        _provider(handler).verify(APPLICANT)


def test_idmatrix_escapes_xml_in_applicant_data():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content.decode()
        return httpx.Response(200, text=_response_xml("ACCEPT"))

    hostile = KycApplicant(**{**APPLICANT.__dict__, "last_name": 'O\'Brien <&"injection">'})
    _provider(handler).verify(hostile)
    assert "<&" not in captured["body"].split("soapenv:Body")[1]
    assert "&lt;&amp;" in captured["body"]
