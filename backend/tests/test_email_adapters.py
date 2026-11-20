import httpx
import pytest

from app.adapters.email import (
    EmailError,
    EmailMessage,
    ResendEmailProvider,
    SendGridEmailProvider,
)

MESSAGE = EmailMessage(
    to="jane@example.com", subject="Test", text="Hello", html="<p>Hello</p>"
)


def _provider(handler) -> SendGridEmailProvider:
    client = httpx.Client(
        base_url="https://api.sendgrid.test", transport=httpx.MockTransport(handler)
    )
    return SendGridEmailProvider(
        api_key="sg-key",
        from_email="noreply@bank.test",
        from_name="Bank",
        client=client,
        backoff_seconds=0,
    )


def test_sendgrid_sends_expected_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers["Authorization"]
        import json

        captured["body"] = json.loads(request.content)
        return httpx.Response(202)

    _provider(handler).send(MESSAGE)
    assert captured["path"] == "/v3/mail/send"
    assert captured["auth"] == "Bearer sg-key"
    body = captured["body"]
    assert body["personalizations"][0]["to"][0]["email"] == "jane@example.com"
    assert body["from"] == {"email": "noreply@bank.test", "name": "Bank"}
    assert body["subject"] == "Test"
    assert {c["type"] for c in body["content"]} == {"text/plain", "text/html"}


def test_sendgrid_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500) if calls["n"] < 3 else httpx.Response(202)

    _provider(handler).send(MESSAGE)
    assert calls["n"] == 3


def test_sendgrid_client_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"errors": [{"message": "bad key"}]})

    with pytest.raises(EmailError):
        _provider(handler).send(MESSAGE)


def _resend_provider(handler) -> ResendEmailProvider:
    client = httpx.Client(
        base_url="https://api.resend.test", transport=httpx.MockTransport(handler)
    )
    return ResendEmailProvider(
        api_key="re-key",
        from_email="noreply@bank.test",
        from_name="Bank",
        client=client,
        backoff_seconds=0,
    )


def test_resend_sends_expected_payload():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured["path"] = request.url.path
        captured["auth"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "email_123"})

    _resend_provider(handler).send(MESSAGE)
    assert captured["path"] == "/emails"
    assert captured["auth"] == "Bearer re-key"
    body = captured["body"]
    assert body["from"] == "Bank <noreply@bank.test>"
    assert body["to"] == ["jane@example.com"]
    assert body["subject"] == "Test"
    assert body["text"] == "Hello" and body["html"] == "<p>Hello</p>"


def test_resend_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500) if calls["n"] < 3 else httpx.Response(200, json={"id": "x"})

    _resend_provider(handler).send(MESSAGE)
    assert calls["n"] == 3


def test_resend_client_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "domain not verified"})

    with pytest.raises(EmailError):
        _resend_provider(handler).send(MESSAGE)
