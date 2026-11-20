import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Field } from '../components/Field'
import { bankSchema, type BankValues } from '../validation'

interface Props {
  defaultValues?: Partial<BankValues>
  onNext: (values: BankValues) => void
  onBack: () => void
  saving: boolean
}

export function BankStep({ defaultValues, onNext, onBack, saving }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<BankValues>({ resolver: zodResolver(bankSchema), defaultValues })

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>Funding account</h2>
      <p className="step-intro">
        Your initial investment and any monthly contributions will be collected by Direct Debit
        from this UK bank account. It must be in your name.
      </p>
      <Field label="Account holder name" error={errors.account_holder_name?.message}>
        <input type="text" autoComplete="name" {...register('account_holder_name')} />
      </Field>
      <div className="grid-2">
        <Field label="Sort code" error={errors.sort_code?.message}>
          <input type="text" inputMode="numeric" placeholder="12-34-56" {...register('sort_code')} />
        </Field>
        <Field label="Account number" error={errors.account_number?.message}>
          <input
            type="text"
            inputMode="numeric"
            placeholder="12345678"
            maxLength={8}
            {...register('account_number')}
          />
        </Field>
      </div>
      <p className="notice">
        Payments are protected by the Direct Debit Guarantee. We'll send confirmation of the
        mandate before the first collection.
      </p>
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
