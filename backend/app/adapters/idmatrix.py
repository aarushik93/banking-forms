"""Equifax IDMatrix (Australia) identity-verification provider.

IDMatrix v4 is a SOAP/XML service (vedaxml.com) authenticated with a
WS-Security UsernameToken. Element names below follow the public
idmatrix-v4-0 schema; align any tenant-specific details (consent wording,
reason-for-enquiry codes, verification rule set) against the schema and
sample XML on https://developer.equifax.com.au for your account.

Test endpoint:       https://ctaau.vedaxml.com/cta/sys2/idmatrix-v4
Production endpoint: https://vedaxml.com/sys2/idmatrix-v4
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import httpx
import structlog
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.adapters.kyc import KycApplicant, KycDecision, KycError, KycResult

log = structlog.get_logger("kyc.idmatrix")

_SOAP_ACTION = "http://vedaxml.com/idmatrix/VerifyIdentity"

_ENVELOPE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
    xmlns:wsa="http://www.w3.org/2005/08/addressing"
    xmlns:idm="http://vedaxml.com/vxml2/idmatrix-v4-0.xsd">
  <soapenv:Header>
    <wsse:Security soapenv:mustUnderstand="1">
      <wsse:UsernameToken>
        <wsse:Username>{username}</wsse:Username>
        <wsse:Password>{password}</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
    <wsa:To>{url}</wsa:To>
    <wsa:Action>{action}</wsa:Action>
  </soapenv:Header>
  <soapenv:Body>
    <idm:request client-reference="{client_reference}" reason-for-enquiry="{reason}">
      <idm:individual-name>
        <idm:family-name>{family_name}</idm:family-name>
        <idm:first-given-name>{first_given_name}</idm:first-given-name>
      </idm:individual-name>
      <idm:date-of-birth>{date_of_birth}</idm:date-of-birth>
      <idm:current-address>
        <idm:unformatted-address>{unformatted_address}</idm:unformatted-address>
      </idm:current-address>
      <idm:mobile-phone-number verify="false">{phone}</idm:mobile-phone-number>
      <idm:email-address verify="false">{email}</idm:email-address>
      <idm:consents>
        <idm:consent>{consent}</idm:consent>
      </idm:consents>
    </idm:request>
  </soapenv:Body>
</soapenv:Envelope>"""


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_text(root: ET.Element, local: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == local and element.text:
            return element.text.strip()
    return None


def _find_attribute(root: ET.Element, name: str) -> str | None:
    for element in root.iter():
        for key, value in element.attrib.items():
            if _local_name(key) == name and value:
                return value
    return None


class EquifaxIdMatrixProvider:
    def __init__(
        self,
        *,
        url: str,
        username: str,
        password: str,
        reason_for_enquiry: str = "Account opening",
        client: httpx.Client | None = None,
        # Generous retry budget (~45s worst case): hosted dependencies can be
        # cold-starting or briefly 502ing behind a proxy, and an applicant
        # mid-submission is worth waiting for.
        max_attempts: int = 8,
        backoff_seconds: float = 0.5,
    ) -> None:
        self._url = url
        self._username = username
        self._password = password
        self._reason = reason_for_enquiry
        self._client = client or httpx.Client(timeout=15.0)
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    def _build_envelope(self, applicant: KycApplicant, client_reference: str) -> str:
        address_parts = [
            applicant.address_line1,
            applicant.address_line2 or "",
            applicant.city,
            applicant.state,
            applicant.postcode,
        ]
        unformatted_address = ", ".join(p for p in address_parts if p)
        return _ENVELOPE_TEMPLATE.format(
            username=escape(self._username),
            password=escape(self._password),
            url=escape(self._url),
            action=_SOAP_ACTION,
            client_reference=escape(client_reference),
            reason=escape(self._reason),
            family_name=escape(applicant.last_name),
            first_given_name=escape(applicant.first_name),
            date_of_birth=applicant.date_of_birth.isoformat(),
            unformatted_address=escape(unformatted_address),
            phone=escape(applicant.phone),
            email=escape(applicant.email),
            # Submission is gated on the applicant's electronic-verification
            # consent declaration, so this is always "yes" by the time we run.
            consent="yes",
        )

    def _post(self, envelope: str) -> str:
        response = self._client.post(
            self._url,
            content=envelope.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": _SOAP_ACTION,
            },
        )
        # SOAP faults typically arrive as HTTP 500 with a Fault body. Those are
        # contract/auth errors, not transient outages — fail without retrying.
        if response.status_code >= 500 and b"Fault" in response.content:
            fault = self._fault_message(response.text)
            raise KycError(f"IDMatrix fault: {fault}")
        response.raise_for_status()
        return response.text

    @staticmethod
    def _fault_message(text: str) -> str:
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return "unparseable fault response"
        return _find_text(root, "faultstring") or "unknown fault"

    @staticmethod
    def _extract_detail(root: ET.Element) -> dict | None:
        """Pull decision evidence (points, per-source results, watchlist) when present."""
        detail: dict = {}
        points = _find_text(root, "total-points")
        if points and points.lstrip("-").isdigit():
            detail["total_points"] = int(points)
        watchlist = _find_text(root, "watchlist-outcome")
        if watchlist:
            detail["watchlist"] = watchlist
        sources: dict[str, str] = {}
        for element in root.iter():
            if _local_name(element.tag) != "verification-response":
                continue
            source = outcome = None
            for child in element:
                if _local_name(child.tag) == "data-source":
                    source = (child.text or "").strip()
                elif _local_name(child.tag) == "source-outcome":
                    outcome = (child.text or "").strip()
            if source and outcome:
                sources[source] = outcome
        if sources:
            detail["sources"] = sources
        return detail or None

    def _parse(self, text: str, client_reference: str) -> KycResult:
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise KycError(f"IDMatrix returned unparseable XML: {exc}") from exc
        fault = _find_text(root, "faultstring")
        if fault:
            raise KycError(f"IDMatrix fault: {fault}")
        raw = (_find_text(root, "overall-outcome") or "").upper()
        mapping = {
            "ACCEPT": KycDecision.ACCEPT,
            "REJECT": KycDecision.REJECT,
            "DECLINE": KycDecision.REJECT,
            "REFER": KycDecision.REFER,
            "CAUTION": KycDecision.REFER,
            "FLAG": KycDecision.REFER,
        }
        decision = mapping.get(raw)
        if decision is None:
            raise KycError(f"Unrecognised IDMatrix outcome: {raw!r}")
        reference = (
            _find_text(root, "enquiry-id")
            or _find_attribute(root, "enquiry-id")
            or client_reference
        )
        return KycResult(
            decision=decision,
            reference=reference,
            raw_decision=raw,
            detail=self._extract_detail(root),
        )

    def verify(self, applicant: KycApplicant) -> KycResult:
        client_reference = f"MFAPP-{uuid.uuid4().hex[:16].upper()}"
        envelope = self._build_envelope(applicant, client_reference)
        retryer = Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=self._backoff_seconds, max=15),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        )
        try:
            text = retryer(self._post, envelope)
        except KycError:
            raise
        except Exception as exc:
            log.warning("idmatrix_request_failed", error=str(exc))
            raise KycError(f"IDMatrix request failed: {exc}") from exc
        return self._parse(text, client_reference)
