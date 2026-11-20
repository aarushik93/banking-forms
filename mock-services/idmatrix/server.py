#!/usr/bin/env python3
"""Mock Equifax IDMatrix SOAP endpoint for local development and demos.

Speaks the same wire format as the real service (vedaxml.com) so the
production adapter in backend/app/adapters/idmatrix.py is exercised
end-to-end: WS-Security UsernameToken auth, SOAP faults on bad
credentials, and IDMatrix-shaped response XML.

Deterministic outcomes by surname (case-insensitive):
  REFER  -> overall-outcome REFER   (application goes to manual review)
  REJECT -> overall-outcome REJECT  (application declined)
  FAULT  -> SOAP fault              (exercises the adapter's fail-fast path)
  else   -> overall-outcome ACCEPT

Stdlib only — no dependencies.
"""

import os
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

USERNAME = os.environ.get("MOCK_IDMATRIX_USERNAME", "idm-demo")
PASSWORD = os.environ.get("MOCK_IDMATRIX_PASSWORD", "idm-demo-password")
PORT = int(os.environ.get("PORT", "8700"))

RESPONSE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <idm:response xmlns:idm="http://vedaxml.com/vxml2/idmatrix-v4-0.xsd"
        enquiry-id="{enquiry_id}" client-reference="{client_reference}">
      <idm:response-outcome>
        <idm:overall-outcome>{outcome}</idm:overall-outcome>
      </idm:response-outcome>
      <idm:component-responses>
        <idm:verification-response>
          <idm:verification-outcome>
            <idm:total-points>{points}</idm:total-points>
            <idm:indicator>{outcome}</idm:indicator>
          </idm:verification-outcome>
        </idm:verification-response>
      </idm:component-responses>
    </idm:response>
  </env:Body>
</env:Envelope>"""

FAULT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <env:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>{message}</faultstring>
    </env:Fault>
  </env:Body>
</env:Envelope>"""

OUTCOMES = {"REFER": ("REFER", 40), "REJECT": ("REJECT", 0)}


def _find_text(root: ET.Element, local: str) -> str | None:
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == local and element.text:
            return element.text.strip()
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "MockIDMatrix/1.0"

    def _send(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _fault(self, message: str) -> None:
        self._send(500, FAULT_TEMPLATE.format(message=message))

    def do_GET(self) -> None:
        if self.path == "/healthz":
            body = b'{"status": "ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
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

        family_name = (_find_text(root, "family-name") or "").upper()
        if family_name == "FAULT":
            self._fault("Simulated downstream failure")
            return

        outcome, points = OUTCOMES.get(family_name, ("ACCEPT", 300))
        self._send(
            200,
            RESPONSE_TEMPLATE.format(
                enquiry_id=f"MOCKIDM-{uuid.uuid4().hex[:12].upper()}",
                client_reference=_find_text(root, "client-reference") or "",
                outcome=outcome,
                points=points,
            ),
        )

    def log_message(self, format: str, *args) -> None:
        print(f"idmatrix-mock: {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")


if __name__ == "__main__":
    print(f"Mock IDMatrix listening on :{PORT} (user: {USERNAME})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
