import { describe, expect, it } from 'vitest'

import { bankSchema, investmentSchema, personalSchema } from '../validation'

const validPersonal = {
  title: 'Ms',
  first_name: 'Jane',
  last_name: 'Smith',
  date_of_birth: '1990-04-12',
  email: 'jane@example.com',
  phone: '+61 412 345 678',
}

function dobForAge(age: number): string {
  const d = new Date()
  d.setFullYear(d.getFullYear() - age)
  return d.toISOString().slice(0, 10)
}

describe('personalSchema', () => {
  it('accepts a valid adult applicant', () => {
    expect(personalSchema.safeParse(validPersonal).success).toBe(true)
  })

  it('rejects applicants under 18', () => {
    const result = personalSchema.safeParse({
      ...validPersonal,
      date_of_birth: dobForAge(17),
    })
    expect(result.success).toBe(false)
  })

  it('rejects an invalid email', () => {
    expect(personalSchema.safeParse({ ...validPersonal, email: 'not-an-email' }).success).toBe(
      false,
    )
  })
})

describe('bankSchema', () => {
  const base = {
    account_holder_name: 'Jane Smith',
    bsb: '062000',
    account_number: '12345678',
  }

  it('accepts plain and formatted BSBs', () => {
    expect(bankSchema.safeParse(base).success).toBe(true)
    expect(bankSchema.safeParse({ ...base, bsb: '062-000' }).success).toBe(true)
  })

  it('rejects malformed BSBs and account numbers', () => {
    expect(bankSchema.safeParse({ ...base, bsb: '06200' }).success).toBe(false)
    expect(bankSchema.safeParse({ ...base, account_number: '1234' }).success).toBe(false)
  })
})

describe('investmentSchema', () => {
  const base = {
    fund_code: 'BAL',
    initial_investment: 5000,
    monthly_contribution: 100,
    source_of_funds: 'salary',
  }

  it('accepts a valid investment', () => {
    expect(investmentSchema.safeParse(base).success).toBe(true)
  })

  it('enforces the minimum initial investment', () => {
    expect(investmentSchema.safeParse({ ...base, initial_investment: 100 }).success).toBe(false)
  })
})
