"""Transactional email providers.

`ResendEmailProvider` posts to the Resend API, `SendGridEmailProvider` to the
SendGrid v3 Mail Send API; the console provider logs messages for local
development and CI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
import structlog
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

log = structlog.get_logger("email")


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str


class EmailError(Exception):
    pass


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class ConsoleEmailProvider:
    def send(self, message: EmailMessage) -> None:
        log.info("email_console", to=message.to, subject=message.subject, body=message.text)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


class ResendEmailProvider:
    """Resend (resend.com) client.

    Until a sending domain is verified in Resend, their API only accepts
    `onboarding@resend.dev` as the from address and only delivers to the
    account owner's email — set EMAIL_FROM accordingly while testing.
    """

    def __init__(
        self,
        *,
        api_key: str,
        from_email: str,
        from_name: str,
        client: httpx.Client | None = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
    ) -> None:
        self._client = client or httpx.Client(base_url="https://api.resend.com", timeout=10.0)
        self._api_key = api_key
        self._from = f"{from_name} <{from_email}>" if from_name else from_email
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    def _post(self, message: EmailMessage) -> None:
        payload = {
            "from": self._from,
            "to": [message.to],
            "subject": message.subject,
            "text": message.text,
            "html": message.html,
        }
        resp = self._client.post(
            "/emails",
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        resp.raise_for_status()

    def send(self, message: EmailMessage) -> None:
        retryer = Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=self._backoff_seconds, max=5),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        )
        try:
            retryer(self._post, message)
        except Exception as exc:
            log.warning("email_send_failed", to=message.to, error=str(exc))
            raise EmailError(f"Resend request failed: {exc}") from exc


class SendGridEmailProvider:
    def __init__(
        self,
        *,
        api_key: str,
        from_email: str,
        from_name: str,
        client: httpx.Client | None = None,
        max_attempts: int = 3,
        backoff_seconds: float = 0.5,
    ) -> None:
        self._client = client or httpx.Client(
            base_url="https://api.sendgrid.com", timeout=10.0
        )
        self._api_key = api_key
        self._from_email = from_email
        self._from_name = from_name
        self._max_attempts = max_attempts
        self._backoff_seconds = backoff_seconds

    def _post(self, message: EmailMessage) -> None:
        payload = {
            "personalizations": [{"to": [{"email": message.to}]}],
            "from": {"email": self._from_email, "name": self._from_name},
            "subject": message.subject,
            "content": [
                {"type": "text/plain", "value": message.text},
                {"type": "text/html", "value": message.html},
            ],
        }
        resp = self._client.post(
            "/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        resp.raise_for_status()

    def send(self, message: EmailMessage) -> None:
        retryer = Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential(multiplier=self._backoff_seconds, max=5),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        )
        try:
            retryer(self._post, message)
        except Exception as exc:
            log.warning("email_send_failed", to=message.to, error=str(exc))
            raise EmailError(f"SendGrid request failed: {exc}") from exc
