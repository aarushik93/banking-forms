from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

AU_POSTCODE = r"^\d{4}$"
COUNTRY = r"^[A-Z]{2}$"
MIN_INITIAL_INVESTMENT = Decimal("500")
MAX_INITIAL_INVESTMENT = Decimal("1000000")
MAX_MONTHLY_CONTRIBUTION = Decimal("50000")


class PersonalDetails(BaseModel):
    title: Literal["Mr", "Mrs", "Ms", "Miss", "Mx", "Dr"]
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr = Field(max_length=255)
    phone: str = Field(pattern=r"^\+?[0-9 ]{7,20}$")

    @field_validator("date_of_birth")
    @classmethod
    def must_be_adult(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("date of birth cannot be in the future")
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("applicants must be at least 18 years old")
        if age > 120:
            raise ValueError("date of birth is not plausible")
        return v


AuState = Literal["NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT"]


class AddressDetails(BaseModel):
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)  # suburb
    state: AuState
    postcode: str = Field(pattern=AU_POSTCODE)
    country: str = Field(default="AU", pattern=COUNTRY)
    years_at_address: int = Field(ge=0, le=100)


EmploymentStatus = Literal["employed", "self_employed", "retired", "student", "unemployed", "other"]
SourceOfFunds = Literal[
    "salary", "savings", "inheritance", "property_sale", "investment_returns", "other"
]


class FinancialDetails(BaseModel):
    employment_status: EmploymentStatus
    annual_income: int = Field(ge=0, le=100_000_000)
    nationality: str = Field(pattern=COUNTRY)
    tax_residency_country: str = Field(pattern=COUNTRY)
    # Tax File Number: collected for withholding-tax purposes only; optional —
    # quoting a TFN is never compulsory, but withholding applies without it.
    tfn: str | None = Field(default=None, pattern=r"^\d{8,9}$")


class InvestmentDetails(BaseModel):
    fund_code: str = Field(min_length=1, max_length=20)
    initial_investment: Decimal = Field(
        ge=MIN_INITIAL_INVESTMENT, le=MAX_INITIAL_INVESTMENT, decimal_places=2
    )
    monthly_contribution: Decimal = Field(
        default=Decimal("0"), ge=0, le=MAX_MONTHLY_CONTRIBUTION, decimal_places=2
    )
    source_of_funds: SourceOfFunds


class BankDetails(BaseModel):
    account_holder_name: str = Field(min_length=1, max_length=100)
    bsb: str = Field(pattern=r"^\d{6}$")
    account_number: str = Field(pattern=r"^\d{6,9}$")


class Declarations(BaseModel):
    accepted_terms: bool
    accepted_risk: bool
    consent_kyc: bool


class DraftUpdate(BaseModel):
    """Partial update: any section that is provided is validated in full."""

    personal: PersonalDetails | None = None
    address: AddressDetails | None = None
    financial: FinancialDetails | None = None
    investment: InvestmentDetails | None = None
    bank: BankDetails | None = None
    declarations: Declarations | None = None


# --- Responses ---


class FundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str
    risk_level: int
    annual_charge_pct: Decimal


class ApplicationCreated(BaseModel):
    id: UUID
    reference: str
    resume_token: str


class MaskedBankDetails(BaseModel):
    account_holder_name: str
    bsb: str
    account_number_masked: str


class BsbLookupOut(BaseModel):
    bsb: str
    found: bool
    directory_available: bool
    bank_name: str | None = None
    branch: str | None = None
    suburb: str | None = None
    state: str | None = None


class AddressSuggestionOut(BaseModel):
    full_text: str
    line1: str
    suburb: str
    state: str
    postcode: str


class EmailOtpSendOut(BaseModel):
    sent: bool
    expires_in: int
    resend_in: int
    debug_code: str | None = None  # populated outside prod only


class EmailOtpConfirmIn(BaseModel):
    code: str = Field(min_length=4, max_length=8)


class ApplicationView(BaseModel):
    id: UUID
    reference: str
    status: str
    kyc_status: str | None
    email_verified: bool
    personal: PersonalDetails | None
    address: AddressDetails | None
    financial: FinancialDetails | None
    investment: InvestmentDetails | None
    bank: MaskedBankDetails | None
    declarations: Declarations | None
    submitted_at: datetime | None


class TrackRequest(BaseModel):
    reference: str = Field(min_length=5, max_length=20)
    email: EmailStr
    date_of_birth: date


class TrackResponse(BaseModel):
    reference: str
    status: str
    submitted_at: datetime | None
    decided_at: datetime | None


class SubmitResponse(BaseModel):
    id: UUID
    reference: str
    status: str
    kyc_status: str | None
    message: str


class AuditEventOut(BaseModel):
    event_type: str
    detail: dict[str, Any] | None
    created_at: datetime


class AdminApplicationSummary(BaseModel):
    id: UUID
    reference: str
    status: str
    kyc_status: str | None
    applicant_name: str | None
    email: str | None
    fund_code: str | None
    initial_investment: Decimal | None
    created_at: datetime
    submitted_at: datetime | None


class AdminApplicationDetail(ApplicationView):
    kyc_reference: str | None
    kyc_checked_at: datetime | None
    decided_at: datetime | None
    decided_by: str | None
    decision_note: str | None
    audit: list[AuditEventOut]


class DecisionRequest(BaseModel):
    decision: Literal["approve", "decline"]
    note: str | None = Field(default=None, max_length=500)
