export interface Fund {
  code: string
  name: string
  description: string
  risk_level: number
  annual_charge_pct: string | number
}

export type ApplicationStatus = 'DRAFT' | 'SUBMITTED' | 'IN_REVIEW' | 'APPROVED' | 'DECLINED'

export interface PersonalSection {
  title: string
  first_name: string
  last_name: string
  date_of_birth: string
  email: string
  phone: string
}

export interface AddressSection {
  line1: string
  line2: string | null
  city: string
  postcode: string
  country: string
  years_at_address: number
}

export interface FinancialSection {
  employment_status: string
  annual_income: number
  nationality: string
  tax_residency_country: string
  nino: string | null
}

export interface InvestmentSection {
  fund_code: string
  initial_investment: number | string
  monthly_contribution: number | string
  source_of_funds: string
}

export interface MaskedBankSection {
  account_holder_name: string
  sort_code: string
  account_number_masked: string
}

export interface DeclarationsSection {
  accepted_terms: boolean
  accepted_risk: boolean
  consent_kyc: boolean
}

export interface ApplicationView {
  id: string
  reference: string
  status: ApplicationStatus
  kyc_status: string | null
  personal: PersonalSection | null
  address: AddressSection | null
  financial: FinancialSection | null
  investment: InvestmentSection | null
  bank: MaskedBankSection | null
  declarations: DeclarationsSection | null
  submitted_at: string | null
}

export interface ApplicationCreated {
  id: string
  reference: string
  resume_token: string
}

export interface SubmitResponse {
  id: string
  reference: string
  status: ApplicationStatus
  kyc_status: string | null
  message: string
}

export interface AdminSummary {
  id: string
  reference: string
  status: ApplicationStatus
  kyc_status: string | null
  applicant_name: string | null
  email: string | null
  fund_code: string | null
  initial_investment: string | number | null
  created_at: string
  submitted_at: string | null
}

export interface AuditEventOut {
  event_type: string
  detail: Record<string, unknown> | null
  created_at: string
}

export interface AdminDetail extends ApplicationView {
  kyc_reference: string | null
  kyc_checked_at: string | null
  decided_at: string | null
  decided_by: string | null
  decision_note: string | null
  audit: AuditEventOut[]
}
