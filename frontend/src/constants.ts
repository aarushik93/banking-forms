import type { ApplicationStatus } from './types'

export const TITLES = ['Mr', 'Mrs', 'Ms', 'Miss', 'Mx', 'Dr'] as const

export const COUNTRIES: Array<[string, string]> = [
  ['AU', 'Australia'],
  ['NZ', 'New Zealand'],
  ['GB', 'United Kingdom'],
  ['IE', 'Ireland'],
  ['US', 'United States'],
  ['CA', 'Canada'],
  ['SG', 'Singapore'],
  ['IN', 'India'],
  ['CN', 'China'],
  ['JP', 'Japan'],
  ['DE', 'Germany'],
  ['FR', 'France'],
  ['ZA', 'South Africa'],
]

export const AU_STATES = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'ACT', 'NT'] as const

export const EMPLOYMENT_OPTIONS = [
  { value: 'employed', label: 'Employed' },
  { value: 'self_employed', label: 'Self-employed' },
  { value: 'retired', label: 'Retired' },
  { value: 'student', label: 'Student' },
  { value: 'unemployed', label: 'Not currently working' },
  { value: 'other', label: 'Other' },
]

export const SOURCE_OF_FUNDS_OPTIONS = [
  { value: 'salary', label: 'Salary or bonus' },
  { value: 'savings', label: 'Existing savings' },
  { value: 'inheritance', label: 'Inheritance' },
  { value: 'property_sale', label: 'Sale of property' },
  { value: 'investment_returns', label: 'Returns from other investments' },
  { value: 'other', label: 'Other' },
]

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  IN_REVIEW: 'In review',
  APPROVED: 'Approved',
  DECLINED: 'Declined',
}

export function formatMoney(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '—'
  const n = typeof value === 'string' ? Number(value) : value
  if (Number.isNaN(n)) return String(value)
  return n.toLocaleString('en-AU', { style: 'currency', currency: 'AUD' })
}

export function labelFor(options: Array<{ value: string; label: string }>, value?: string | null) {
  return options.find((o) => o.value === value)?.label ?? value ?? '—'
}
