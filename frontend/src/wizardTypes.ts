import type {
  AddressValues,
  BankValues,
  FinancialValues,
  InvestmentValues,
  PersonalValues,
} from './validation'

export interface WizardData {
  personal?: PersonalValues
  address?: AddressValues
  financial?: FinancialValues
  investment?: InvestmentValues
  bank?: BankValues
}
