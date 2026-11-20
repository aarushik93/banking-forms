"""Bank account ownership verification.

Confirms the funding account (BSB + account number) is actually held in the
applicant's name before money moves. In Australia the real implementations
are CDR (open banking) account-detail verification or PayID/NPP name-matching
services — both require accreditation or a commercial agreement, so this
module ships the provider seam plus a deterministic mock. Wire a vendor
adapter here when one is contracted; until then prod must explicitly opt out
with ACCOUNT_VERIFICATION_PROVIDER=off (the Direct Debit dispute process
remains the regulatory backstop).

Mock rules (by account number suffix): ...99 -> no_match, ...88 ->
partial_match, ...77 -> unavailable, anything else -> full_match.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class AccountMatch(StrEnum):
    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    UNAVAILABLE = "unavailable"  # provider outage — do not block the applicant
    SKIPPED = "skipped"  # verification disabled by configuration


@dataclass(frozen=True)
class AccountVerificationResult:
    status: AccountMatch
    reference: str


class AccountVerificationProvider(Protocol):
    def verify(
        self, *, bsb: str, account_number: str, account_name: str
    ) -> AccountVerificationResult: ...


class MockAccountVerificationProvider:
    def verify(
        self, *, bsb: str, account_number: str, account_name: str
    ) -> AccountVerificationResult:
        suffix_rules = {
            "99": AccountMatch.NO_MATCH,
            "88": AccountMatch.PARTIAL_MATCH,
            "77": AccountMatch.UNAVAILABLE,
        }
        status = suffix_rules.get(account_number[-2:], AccountMatch.FULL_MATCH)
        return AccountVerificationResult(
            status=status, reference=f"MOCKAV-{uuid.uuid4().hex[:12].upper()}"
        )


class DisabledAccountVerificationProvider:
    def verify(
        self, *, bsb: str, account_number: str, account_name: str
    ) -> AccountVerificationResult:
        return AccountVerificationResult(status=AccountMatch.SKIPPED, reference="")
