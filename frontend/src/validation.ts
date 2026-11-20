import { z } from 'zod'

export const MIN_INITIAL_INVESTMENT = 500
export const MAX_INITIAL_INVESTMENT = 1_000_000
export const MAX_MONTHLY_CONTRIBUTION = 50_000

const AU_POSTCODE = /^\d{4}$/
const TFN = /^\d{8,9}$/
export const BSB = /^\d{3}[- ]?\d{3}$/

function isAdult(dob: string): boolean {
  const birth = new Date(dob)
  if (Number.isNaN(birth.getTime())) return false
  const today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const beforeBirthday =
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate())
  if (beforeBirthday) age -= 1
  return age >= 18 && age <= 120
}

export const personalSchema = z.object({
  title: z.enum(['Mr', 'Mrs', 'Ms', 'Miss', 'Mx', 'Dr'], {
    errorMap: () => ({ message: 'Select a title' }),
  }),
  first_name: z.string().min(1, 'Enter your first name').max(100),
  last_name: z.string().min(1, 'Enter your last name').max(100),
  date_of_birth: z
    .string()
    .min(1, 'Enter your date of birth')
    .refine(isAdult, 'You must be at least 18 years old to apply'),
  email: z.string().min(1, 'Enter your email address').email('Enter a valid email address'),
  phone: z
    .string()
    .regex(/^\+?[0-9 ]{7,20}$/, 'Enter a valid phone number (digits and spaces only)'),
})

export const addressSchema = z.object({
  line1: z.string().min(1, 'Enter the first line of your address').max(255),
  line2: z.string().max(255),
  city: z.string().min(1, 'Enter your suburb').max(100),
  state: z.enum(['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'ACT', 'NT'], {
    errorMap: () => ({ message: 'Select your state or territory' }),
  }),
  postcode: z.string().regex(AU_POSTCODE, 'Enter a valid 4-digit postcode'),
  country: z.string().regex(/^[A-Z]{2}$/, 'Select a country'),
  years_at_address: z
    .number({ invalid_type_error: 'Enter the number of years at this address' })
    .int('Enter whole years')
    .min(0, 'Cannot be negative')
    .max(100, 'Enter a realistic number of years'),
})

export const financialSchema = z.object({
  employment_status: z.enum(
    ['employed', 'self_employed', 'retired', 'student', 'unemployed', 'other'],
    { errorMap: () => ({ message: 'Select your employment status' }) },
  ),
  annual_income: z
    .number({ invalid_type_error: 'Enter your annual income' })
    .int('Enter a whole number')
    .min(0, 'Cannot be negative')
    .max(100_000_000, 'Enter a realistic income'),
  nationality: z.string().regex(/^[A-Z]{2}$/, 'Select your nationality'),
  tax_residency_country: z.string().regex(/^[A-Z]{2}$/, 'Select your country of tax residency'),
  tfn: z
    .string()
    .refine((v) => v === '' || TFN.test(v), 'Enter a valid 8 or 9 digit Tax File Number'),
})

export const investmentSchema = z.object({
  fund_code: z.string().min(1, 'Select a fund'),
  initial_investment: z
    .number({ invalid_type_error: 'Enter an amount' })
    .min(MIN_INITIAL_INVESTMENT, `The minimum initial investment is $${MIN_INITIAL_INVESTMENT}`)
    .max(
      MAX_INITIAL_INVESTMENT,
      `Amounts above $${MAX_INITIAL_INVESTMENT.toLocaleString()} require an adviser`,
    ),
  monthly_contribution: z
    .number({ invalid_type_error: 'Enter an amount (0 for none)' })
    .min(0, 'Cannot be negative')
    .max(MAX_MONTHLY_CONTRIBUTION, 'Enter a smaller monthly amount'),
  source_of_funds: z.enum(
    ['salary', 'savings', 'inheritance', 'property_sale', 'investment_returns', 'other'],
    { errorMap: () => ({ message: 'Select the source of your investment' }) },
  ),
})

export const bankSchema = z.object({
  account_holder_name: z.string().min(1, 'Enter the account holder name').max(100),
  bsb: z.string().regex(BSB, 'Enter a valid 6-digit BSB'),
  account_number: z.string().regex(/^\d{6,9}$/, 'Enter a valid account number (6–9 digits)'),
})

export const declarationsSchema = z.object({
  accepted_terms: z.boolean().refine((v) => v, 'You must accept the terms and conditions'),
  accepted_risk: z.boolean().refine((v) => v, 'You must acknowledge the investment risks'),
  consent_kyc: z.boolean().refine((v) => v, 'We cannot proceed without consent for checks'),
})

export type PersonalValues = z.infer<typeof personalSchema>
export type AddressValues = z.infer<typeof addressSchema>
export type FinancialValues = z.infer<typeof financialSchema>
export type InvestmentValues = z.infer<typeof investmentSchema>
export type BankValues = z.infer<typeof bankSchema>
export type DeclarationsValues = z.infer<typeof declarationsSchema>
