#!/usr/bin/env python3
"""Mock Equifax IDMatrix SOAP endpoint for local development and demos.

Speaks the same wire format as the real service (vedaxml.com) so the
production adapter in backend/app/adapters/idmatrix.py is exercised
end-to-end: WS-Security UsernameToken auth, SOAP faults on bad
credentials, and IDMatrix-shaped response XML with per-source
verification results, a points score, and watchlist screening.

Behaviour (like a real bureau sandbox, see personas.py for the records):
1. Applicant matches a seeded persona -> that persona's scripted scenario,
   with a wrong DOB or postcode downgrading to a partial-match REFER.
2. Otherwise, surname triggers: REFER / REJECT / FAULT.
3. Otherwise MOCK_DEFAULT_OUTCOME (ACCEPT by default; set REFER for
   realistic "identity not found in any source" behaviour).

Stdlib only — no dependencies.
"""

import json
import os
import random
import re
import time
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from personas import ALL_PERSONAS, find_persona

USERNAME = os.environ.get("MOCK_IDMATRIX_USERNAME", "idm-demo")
PASSWORD = os.environ.get("MOCK_IDMATRIX_PASSWORD", "idm-demo-password")
PORT = int(os.environ.get("PORT", "8700"))
DEFAULT_OUTCOME = os.environ.get("MOCK_DEFAULT_OUTCOME", "ACCEPT").upper()
# Simulated bureau processing time — real IDMatrix calls take a few seconds.
MIN_LATENCY_MS = int(os.environ.get("MOCK_MIN_LATENCY_MS", "1200"))
MAX_LATENCY_MS = int(os.environ.get("MOCK_MAX_LATENCY_MS", "2800"))

RESPONSE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <idm:response xmlns:idm="http://vedaxml.com/vxml2/idmatrix-v4-0.xsd"
        enquiry-id="{enquiry_id}" client-reference="{client_reference}">
      <idm:response-outcome>
        <idm:overall-outcome>{outcome}</idm:overall-outcome>
      </idm:response-outcome>
      <idm:component-responses>
        <idm:verification-outcome>
          <idm:total-points>{points}</idm:total-points>
          <idm:indicator>{outcome}</idm:indicator>
        </idm:verification-outcome>
{source_results}
        <idm:watchlist-response>
          <idm:watchlist-outcome>{watchlist}</idm:watchlist-outcome>
        </idm:watchlist-response>
      </idm:component-responses>
    </idm:response>
  </env:Body>
</env:Envelope>"""

SOURCE_TEMPLATE = (
    "        <idm:verification-response>\n"
    "          <idm:data-source>{source}</idm:data-source>\n"
    "          <idm:source-outcome>{outcome}</idm:source-outcome>\n"
    "        </idm:verification-response>"
)

FAULT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <env:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>{message}</faultstring>
    </env:Fault>
  </env:Body>
</env:Envelope>"""

SURNAME_TRIGGERS = {"REFER": ("REFER", 150), "REJECT": ("REJECT", 40)}


def _find_text(root: ET.Element, local: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local and element.text:
            return element.text.strip()
    return None


def _decide(root: ET.Element) -> dict:
    """Return outcome, points, watchlist and per-source results for a request."""
    family_name = _find_text(root, "family-name") or ""
    first_name = _find_text(root, "first-given-name") or ""
    dob = _find_text(root, "date-of-birth") or ""
    address = _find_text(root, "unformatted-address") or ""
    postcode_match = re.search(r"\b(\d{4})\b(?!.*\b\d{4}\b)", address)
    postcode = postcode_match.group(1) if postcode_match else ""

    persona = find_persona(first_name, family_name)
    if persona:
        if dob != persona["date_of_birth"] or postcode != persona["postcode"]:
            # Right person, inconsistent data: a real bureau partial-matches.
            return {
                "outcome": "REFER",
                "points": 140,
                "watchlist": "CLEAR",
                "sources": {
                    "CREDIT_HEADER": "MISMATCH",
                    "ELECTORAL_ROLL": "MISMATCH",
                    "DVS_DRIVERS_LICENCE": "NOT_CHECKED",
                },
            }
        return {
            "outcome": persona["outcome"],
            "points": persona["points"],
            "watchlist": persona["watchlist"],
            "sources": persona["sources"],
        }

    surname = family_name.strip().upper()
    if surname in SURNAME_TRIGGERS:
        outcome, points = SURNAME_TRIGGERS[surname]
        return {
            "outcome": outcome,
            "points": points,
            "watchlist": "CLEAR",
            "sources": {"CREDIT_HEADER": "NOT_FOUND", "ELECTORAL_ROLL": "NOT_FOUND"},
        }

    if DEFAULT_OUTCOME == "ACCEPT":
        return {
            "outcome": "ACCEPT",
            "points": 300,
            "watchlist": "CLEAR",
            "sources": {"CREDIT_HEADER": "VERIFIED", "ELECTORAL_ROLL": "VERIFIED"},
        }
    return {
        "outcome": "REFER",
        "points": 0,
        "watchlist": "CLEAR",
        "sources": {"CREDIT_HEADER": "NOT_FOUND", "ELECTORAL_ROLL": "NOT_FOUND"},
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "MockIDMatrix/2.0"

    def _send(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _fault(self, message: str) -> None:
        self._send(500, FAULT_TEMPLATE.format(message=message))

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send_json({"status": "ok"})
        elif self.path.rstrip("/") == "/personas":
            # Sandbox data dictionary: every identity this mock bureau holds.
            self._send_json(
                [
                    {
                        "first_name": p["first_name"],
                        "last_name": p["last_name"],
                        "date_of_birth": p["date_of_birth"],
                        "suburb": p.get("suburb", ""),
                        "state": p.get("state", ""),
                        "postcode": p["postcode"],
                        "expected_outcome": p["outcome"],
                        "watchlist": p["watchlist"],
                        "points": p["points"],
                        "scenario": p["scenario"],
                    }
                    for p in ALL_PERSONAS
                ]
            )
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            self._fault("Malformed SOAP request")
            return

        if _find_text(root, "Username") != USERNAME or _find_text(root, "Password") != PASSWORD:
            self._fault("Authentication failed")
            return

        if MAX_LATENCY_MS > 0:
            time.sleep(random.uniform(MIN_LATENCY_MS, MAX_LATENCY_MS) / 1000)

        if (_find_text(root, "family-name") or "").upper() == "FAULT":
            self._fault("Simulated downstream failure")
            return

        decision = _decide(root)
        source_results = "\n".join(
            SOURCE_TEMPLATE.format(source=source, outcome=outcome)
            for source, outcome in decision["sources"].items()
        )
        self._send(
            200,
            RESPONSE_TEMPLATE.format(
                enquiry_id=f"MOCKIDM-{uuid.uuid4().hex[:12].upper()}",
                client_reference=_find_text(root, "client-reference") or "",
                outcome=decision["outcome"],
                points=decision["points"],
                watchlist=decision["watchlist"],
                source_results=source_results,
            ),
        )

    def log_message(self, format: str, *args) -> None:
        print(f"idmatrix-mock: {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")


if __name__ == "__main__":
    print(
        f"Mock IDMatrix listening on :{PORT} "
        f"(user: {USERNAME}, default outcome: {DEFAULT_OUTCOME})"
    )
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
