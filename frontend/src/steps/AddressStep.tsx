import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'

import { api } from '../api'
import { Field } from '../components/Field'
import { AU_STATES, COUNTRIES } from '../constants'
import type { AddressSuggestion } from '../types'
import { addressSchema, type AddressValues } from '../validation'

interface Props {
  defaultValues?: Partial<AddressValues>
  onNext: (values: AddressValues) => void
  onBack: () => void
  saving: boolean
}

export function AddressStep({ defaultValues, onNext, onBack, saving }: Props) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<AddressValues>({
    resolver: zodResolver(addressSchema),
    defaultValues: { country: 'AU', line2: '', ...defaultValues },
  })

  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([])
  const skipLookup = useRef(false)
  const line1 = watch('line1')

  useEffect(() => {
    if (skipLookup.current) {
      skipLookup.current = false
      return
    }
    if (!line1 || line1.trim().length < 4) {
      setSuggestions([])
      return
    }
    const timer = setTimeout(() => {
      api
        .suggestAddress(line1)
        .then(setSuggestions)
        .catch(() => setSuggestions([]))
    }, 350)
    return () => clearTimeout(timer)
  }, [line1])

  function pickSuggestion(suggestion: AddressSuggestion) {
    skipLookup.current = true
    setValue('line1', suggestion.line1, { shouldValidate: true })
    setValue('city', suggestion.suburb, { shouldValidate: true })
    setValue('state', suggestion.state as AddressValues['state'], { shouldValidate: true })
    setValue('postcode', suggestion.postcode, { shouldValidate: true })
    setSuggestions([])
  }

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>Your home address</h2>
      <p className="step-intro">
        We need your current residential address for identity checks. Start typing to search,
        or enter it manually.
      </p>
      <div className="autocomplete">
        <Field label="Address line 1" error={errors.line1?.message}>
          <input
            type="text"
            autoComplete="off"
            placeholder="Start typing your street address…"
            {...register('line1')}
          />
        </Field>
        {suggestions.length > 0 && (
          <ul className="suggestions" role="listbox" aria-label="Address suggestions">
            {suggestions.map((s) => (
              <li key={s.full_text}>
                <button type="button" onClick={() => pickSuggestion(s)}>
                  {s.full_text}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <Field label="Address line 2 (optional)" error={errors.line2?.message}>
        <input type="text" autoComplete="address-line2" {...register('line2')} />
      </Field>
      <div className="grid-2">
        <Field label="Suburb" error={errors.city?.message}>
          <input type="text" autoComplete="address-level2" {...register('city')} />
        </Field>
        <Field label="State / territory" error={errors.state?.message}>
          <select {...register('state')} defaultValue={defaultValues?.state ?? ''}>
            <option value="" disabled>
              Select…
            </option>
            {AU_STATES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Postcode" error={errors.postcode?.message}>
          <input
            type="text"
            inputMode="numeric"
            autoComplete="postal-code"
            placeholder="2000"
            maxLength={4}
            {...register('postcode')}
          />
        </Field>
        <Field label="Country" error={errors.country?.message}>
          <select {...register('country')}>
            {COUNTRIES.map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Years at this address" error={errors.years_at_address?.message}>
          <input
            type="number"
            min={0}
            max={100}
            {...register('years_at_address', { valueAsNumber: true })}
          />
        </Field>
      </div>
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
