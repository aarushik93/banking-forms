import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Field } from '../components/Field'
import { MIN_INITIAL_INVESTMENT, investmentSchema, type InvestmentValues } from '../validation'
import { SOURCE_OF_FUNDS_OPTIONS } from '../constants'
import type { Fund } from '../types'

interface Props {
  funds: Fund[]
  defaultValues?: Partial<InvestmentValues>
  onNext: (values: InvestmentValues) => void
  onBack: () => void
  saving: boolean
}

export function InvestmentStep({ funds, defaultValues, onNext, onBack, saving }: Props) {
  const {
    register,
    watch,
    handleSubmit,
    formState: { errors },
  } = useForm<InvestmentValues>({
    resolver: zodResolver(investmentSchema),
    defaultValues: { monthly_contribution: 0, ...defaultValues },
  })

  const selectedCode = watch('fund_code')
  const selected = funds.find((f) => f.code === selectedCode)

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>Your investment</h2>
      <p className="step-intro">
        Choose a fund and how much you'd like to invest. The minimum initial investment is £
        {MIN_INITIAL_INVESTMENT}.
      </p>
      <Field label="Fund" error={errors.fund_code?.message}>
        <select {...register('fund_code')} defaultValue={defaultValues?.fund_code ?? ''}>
          <option value="" disabled>
            Select a fund…
          </option>
          {funds.map((f) => (
            <option key={f.code} value={f.code}>
              {f.name} — risk {f.risk_level}/7, {Number(f.annual_charge_pct).toFixed(2)}% p.a.
            </option>
          ))}
        </select>
      </Field>
      {selected && <p className="fund-description">{selected.description}</p>}
      <div className="grid-2">
        <Field label="Initial lump sum (£)" error={errors.initial_investment?.message}>
          <input
            type="number"
            min={MIN_INITIAL_INVESTMENT}
            step="0.01"
            {...register('initial_investment', { valueAsNumber: true })}
          />
        </Field>
        <Field
          label="Monthly contribution (£)"
          hint="Enter 0 if you don't want to contribute monthly"
          error={errors.monthly_contribution?.message}
        >
          <input
            type="number"
            min={0}
            step="0.01"
            {...register('monthly_contribution', { valueAsNumber: true })}
          />
        </Field>
      </div>
      <Field label="Source of this money" error={errors.source_of_funds?.message}>
        <select {...register('source_of_funds')} defaultValue={defaultValues?.source_of_funds ?? ''}>
          <option value="" disabled>
            Select…
          </option>
          {SOURCE_OF_FUNDS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </Field>
      <div className="wizard-actions">
        <button type="button" className="btn btn-ghost" onClick={onBack} disabled={saving}>
          Back
        </button>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving…' : 'Continue'}
        </button>
      </div>
    </form>
  )
}
