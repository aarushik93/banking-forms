import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Field } from '../components/Field'
import { COUNTRIES, EMPLOYMENT_OPTIONS } from '../constants'
import { financialSchema, type FinancialValues } from '../validation'

interface Props {
  defaultValues?: Partial<FinancialValues>
  onNext: (values: FinancialValues) => void
  onBack: () => void
  saving: boolean
}

export function FinancialStep({ defaultValues, onNext, onBack, saving }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FinancialValues>({
    resolver: zodResolver(financialSchema),
    defaultValues: { nationality: 'AU', tax_residency_country: 'AU', tfn: '', ...defaultValues },
  })

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>Work, income and tax</h2>
      <p className="step-intro">
        We're required to collect this for suitability and international tax reporting (CRS/FATCA).
      </p>
      <div className="grid-2">
        <Field label="Employment status" error={errors.employment_status?.message}>
          <select
            {...register('employment_status')}
            defaultValue={defaultValues?.employment_status ?? ''}
          >
            <option value="" disabled>
              Select…
            </option>
            {EMPLOYMENT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Annual income ($)" error={errors.annual_income?.message}>
          <input type="number" min={0} {...register('annual_income', { valueAsNumber: true })} />
        </Field>
        <Field label="Nationality" error={errors.nationality?.message}>
          <select {...register('nationality')}>
            {COUNTRIES.map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Country of tax residency" error={errors.tax_residency_country?.message}>
          <select {...register('tax_residency_country')}>
            {COUNTRIES.map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field
        label="Tax File Number (optional)"
        hint="Quoting your TFN is not compulsory, but without it we must withhold tax from earnings at the highest marginal rate"
        error={errors.tfn?.message}
      >
        <input type="text" inputMode="numeric" placeholder="123 456 789" maxLength={9} {...register('tfn')} />
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
