import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import { api } from '../api'
import { Field } from '../components/Field'
import type { BsbLookup } from '../types'
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
    watch,
    formState: { errors },
  } = useForm<BankValues>({ resolver: zodResolver(bankSchema), defaultValues })

  const [bsbInfo, setBsbInfo] = useState<BsbLookup | null>(null)
  const bsbValue = watch('bsb')

  useEffect(() => {
    const digits = (bsbValue ?? '').replace(/\D/g, '')
    if (digits.length !== 6) {
      setBsbInfo(null)
      return
    }
    const timer = setTimeout(() => {
      api
        .lookupBsb(digits)
        .then(setBsbInfo)
        .catch(() => setBsbInfo(null))
    }, 250)
    return () => clearTimeout(timer)
  }, [bsbValue])

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>Funding account</h2>
      <p className="step-intro">
        Your initial investment and any monthly contributions will be collected by direct debit
        from this Australian bank account. It must be in your name.
      </p>
      <Field label="Account holder name" error={errors.account_holder_name?.message}>
        <input type="text" autoComplete="name" {...register('account_holder_name')} />
      </Field>
      <div className="grid-2">
        <Field label="BSB" error={errors.bsb?.message}>
          <input type="text" inputMode="numeric" placeholder="062-000" {...register('bsb')} />
          {bsbInfo?.found && (
            <p className="bsb-match">
              ✓ {bsbInfo.bank_name}
              {bsbInfo.suburb ? ` — ${bsbInfo.suburb} ${bsbInfo.state ?? ''}` : ''}
            </p>
          )}
          {bsbInfo && !bsbInfo.found && bsbInfo.directory_available && (
            <p className="bsb-warn">
              We don't recognise this BSB — please double-check it
            </p>
          )}
        </Field>
        <Field label="Account number" error={errors.account_number?.message}>
          <input
            type="text"
            inputMode="numeric"
            placeholder="12345678"
            maxLength={9}
            {...register('account_number')}
          />
        </Field>
      </div>
      <p className="notice">
        By continuing you authorise us to debit this account under a Direct Debit Request. We'll
        send you the DDR Service Agreement before the first collection.
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
