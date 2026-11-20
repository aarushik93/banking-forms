# Banking Forms — Managed Funds Application

A production-grade replacement for the bank's legacy iApply forms: customers apply online for a
managed funds investment account, identity is verified electronically for AML/CTF (primary
provider: **Equifax IDMatrix**; an **Experian CrossCore** adapter is also included), and
applicants are kept informed by **SendGrid** transactional email. Includes a token-protected
back office for manually deciding referred applications.

Localised for **Australia**: BSB + account number funding (Direct Debit Request), optional Tax
File Number for withholding, state/postcode address capture, AUD amounts, and AML/CTF Act
consent wording.

## Architecture

```
┌────────────┐     /api/v1      ┌─────────────────┐        ┌──────────────────┐
│  React SPA │ ───────────────▶ │  FastAPI backend │ ─────▶ │ Experian CrossCore│ (KYC)
│ (nginx)    │                  │                 │ ─────▶ │ SendGrid          │ (email)
└────────────┘                  └────────┬────────┘        └──────────────────┘
                                         │
                                   ┌─────▼─────┐
                                   │ PostgreSQL │ (applications, funds, audit trail)
                                   └───────────┘
```

- **`backend/`** — FastAPI + SQLAlchemy 2 + Alembic. Application lifecycle:
  `DRAFT → SUBMITTED → APPROVED / IN_REVIEW / DECLINED`. KYC `ACCEPT` auto-approves,
  `REFER` routes to the back office, `REJECT` auto-declines; a provider outage leaves the
  application safely in `SUBMITTED` for retry. Every transition is written to an audit table
  (no PII in audit detail).
- **`frontend/`** — React 19 + Vite + TypeScript. Six-step wizard (personal → address →
  finances/tax → investment → bank → review & declarations) with zod validation mirrored by
  Pydantic server-side, autosaved drafts with resume, and an `/admin` back office.
- **Integrations** sit behind interfaces (`KycProvider`, `EmailProvider`) with deterministic
  mock/console implementations, so the whole stack runs and tests without external credentials.

## Quick start

```bash
cp .env.example .env     # defaults are fine for a local run
docker compose up --build
```

- Customer journey: http://localhost:8080
- Back office: http://localhost:8080/admin (token = `ADMIN_API_TOKEN`, default `change-me`)
- API docs (non-prod): http://localhost:8000/docs

**Demo the KYC outcomes**: apply with surname `Refer` → goes to review (decide it in the
back office), `Reject` → declined, `Fault` → simulated provider failure (application stays
retryable), anything else → approved.

Out of the box, compose runs the **real IDMatrix SOAP adapter** against a bundled mock
IDMatrix service (`mock-services/idmatrix/`) that speaks the vedaxml wire format — WS-Security
auth, IDMatrix response XML, SOAP faults — so the whole integration path is exercised without
Equifax access. Going live is config-only: point `IDMATRIX_URL`/`IDMATRIX_USERNAME`/
`IDMATRIX_PASSWORD` at Equifax instead of the mock.

## Local development

```bash
# Backend (Python 3.12+)
cd backend
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
docker compose up -d db            # or point DATABASE_URL at any Postgres
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload

# Frontend (Node 20+) — dev server proxies /api to localhost:8000
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

### Tests & checks

```bash
cd backend  && .venv/bin/ruff check . && .venv/bin/mypy app && .venv/bin/pytest
cd frontend && npm run lint && npm test && npm run build
```

## Configuration

All configuration is via environment variables (see `.env.example`). Key switches:

| Variable | Values | Notes |
| --- | --- | --- |
| `KYC_PROVIDER` | `mock` / `idmatrix` / `experian` | `idmatrix` needs `IDMATRIX_USERNAME`/`IDMATRIX_PASSWORD` from Equifax; `experian` needs the `EXPERIAN_*` credentials |
| `EMAIL_PROVIDER` | `console` / `sendgrid` | `sendgrid` needs `SENDGRID_API_KEY`; sender must be a [verified sender/domain](https://docs.sendgrid.com/ui/sending-email/sender-verification) |
| `ADMIN_API_TOKEN` | string | Protects `/api/v1/admin/*`; must be strong (16+ chars) in prod |
| `ENV` | `dev` / `test` / `prod` | `prod` refuses to boot with mock KYC, console email, or a weak admin token, and disables `/docs` |

### Verification & lookup services

- **Email ownership (OTP)** — a 6-digit code is emailed (SendGrid/console) and must be
  confirmed before submission. Hash-only storage, 10-minute expiry, resend cooldown,
  5-attempt limit; changing the email resets verification. Outside prod the send response
  includes a `debug_code` so local demos work with the console email provider.
- **BSB directory (live)** — AusPayNet's official full directory is fetched at runtime from
  its permanent public URL, cached in memory and refreshed daily. The UI shows the matched
  bank/branch as you type; `BSB_STRICT=true` rejects unknown BSBs at submit (skipped if the
  directory is unreachable).
- **Address autocomplete (live)** — suggestions as you type, filling suburb/state/postcode.
  Dev default is Nominatim (keyless; not licensed for production traffic); production uses
  the Geoscape Predictive Address API (`ADDRESS_PROVIDER=geoscape` + API key). Manual entry
  always works; the KYC check independently verifies the address.
- **Account ownership** — the funding account must be held in the applicant's name, checked
  at submit through an `AccountVerificationProvider`. A no-match blocks submission (the
  draft stays editable); a provider outage never blocks. Real AU implementations (CDR /
  PayID name-matching) require accreditation, so a deterministic mock ships for now
  (account numbers ending 99 → no match, 88 → partial, 77 → outage) and prod refuses the
  mock unless verification is explicitly set to `off`.

### Equifax IDMatrix integration (primary)

`app/adapters/idmatrix.py` implements the IDMatrix v4 SOAP/XML contract: WS-Security
UsernameToken auth, applicant submission (name, DOB, address, phone, email, consent), and
mapping of the `overall-outcome` decision (`ACCEPT` / `REJECT`; `REFER`-family outcomes route
to manual review). Transient 5xx/network errors retry with backoff; SOAP faults fail fast.
Endpoints: test `https://ctaau.vedaxml.com/cta/sys2/idmatrix-v4`, production
`https://vedaxml.com/sys2/idmatrix-v4`. Credentials and the account's verification rule set
come from your Equifax account manager / [developer.equifax.com.au](https://developer.equifax.com.au);
align any tenant-specific schema details (consent elements, reason-for-enquiry codes) against
the sample XML there.

Until Equifax access is provisioned, `mock-services/idmatrix/` provides a wire-compatible
stand-in (used by default in Docker Compose): same SOAP envelope in, same response XML out,
including auth faults on wrong credentials. Production refuses to boot if the mock's URL or
demo credentials are still configured.

### Experian integration (alternative)

`app/adapters/kyc.py` implements OAuth2 token acquisition (cached, auto-refreshed on 401) and
CrossCore transaction submit with retries/backoff on 5xx and network errors. CrossCore request
payloads and decision elements are tenant-specific — when onboarding completes, align
`_build_payload` / `_map_response` with your workflow pack and set `EXPERIAN_KYC_PATH`.
The decision mapping is: `ACCEPT/CONTINUE → approve`, `REFER/NODECISION → manual review`,
`REJECT/DECLINE/STOP → decline`; anything unrecognised fails safe (application stays
submitted, applicant is asked to retry).

### SendGrid integration

`app/adapters/email.py` posts to the v3 Mail Send API with the same retry policy. Emails
(received / approved / declined) are sent from FastAPI background tasks so SendGrid latency
never blocks a response; failures are logged and recorded in the audit trail.

## API overview

| Method & path | Auth | Purpose |
| --- | --- | --- |
| `GET /api/v1/funds` | — | Active funds for the picker |
| `POST /api/v1/applications` | rate-limited | Create a draft; returns `id` + `resume_token` |
| `PUT /api/v1/applications/{id}` | `X-Resume-Token` | Save validated sections (autosave/resume) |
| `GET /api/v1/applications/{id}` | `X-Resume-Token` | Read own application (bank account masked) |
| `POST /api/v1/applications/{id}/submit` | `X-Resume-Token`, rate-limited | Validate completeness, run KYC, decision + email |
| `GET /api/v1/admin/applications[?status=]` | `X-Admin-Token` | Back-office list |
| `GET /api/v1/admin/applications/{id}` | `X-Admin-Token` | Detail incl. audit trail |
| `POST /api/v1/admin/applications/{id}/decision` | `X-Admin-Token` | Approve/decline a referred case |
| `GET /healthz`, `GET /readyz` | — | Liveness / readiness (DB check) |

## CI/CD

`.github/workflows/ci.yml`:

1. **backend** — ruff, mypy, pytest (34 tests, including Experian/SendGrid contract tests
   against mocked HTTP transports).
2. **frontend** — eslint, vitest, type-checked production build.
3. **publish-images** — on push to `main`, builds and pushes
   `ghcr.io/<repo>-backend` and `ghcr.io/<repo>-frontend` (tagged `latest` + commit SHA).

Deployment is intentionally simple: any Docker host can run `docker compose up -d`. A
commented SSH deploy job in the workflow shows how to automate it against a VM.

## Production hardening already in place

- Config validation at boot (prod refuses unsafe settings), secrets only via env vars
- Structured JSON logs with per-request IDs (`X-Request-ID` honoured and returned)
- Retries with exponential backoff + timeouts on all outbound calls; KYC failure degrades
  gracefully instead of losing the application
- Per-IP rate limiting on anonymous endpoints; resume tokens and admin token compared in
  constant time; bank account numbers masked in every read API
- Audit trail for every state change, KYC result, decision, and email outcome
- Non-root Docker containers, healthchecks, migrations applied on boot

## Before go-live (checklist)

- [ ] Equifax IDMatrix credentials + rule-set certification run (or Experian CrossCore)
- [ ] Geoscape API key for address autocomplete (`ADDRESS_PROVIDER=geoscape`)
- [ ] Account-ownership vendor (CDR or PayID name-matching) wired into
      `adapters/account_verification.py`
- [ ] SendGrid domain authentication (SPF/DKIM) and branded templates
- [ ] TLS in front of nginx (load balancer or reverse proxy) and HSTS
- [ ] Replace the shared admin token with SSO/OIDC for back-office users
- [ ] Encryption at rest for PII columns (pgcrypto or KMS-level), plus data-retention policy
- [ ] Redis-backed rate limiting if running more than one backend replica
- [ ] Monitoring/alerting on `readyz`, KYC error rate, and email failure audit events
- [ ] Penetration test & Privacy Impact Assessment (Privacy Act 1988 / APPs) sign-off
- [ ] AML/CTF program alignment (AUSTRAC) — safe-harbour verification settings in the
      CrossCore workflow
