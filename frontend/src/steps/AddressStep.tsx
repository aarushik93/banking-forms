import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Field } from '../components/Field'
import { AU_STATES, COUNTRIES } from '../constants'
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
    formState: { errors },
  } = useForm<AddressValues>({
    resolver: zodResolver(addressSchema),
    defaultValues: { country: 'AU', line2: '', ...defaultValues },
  })

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>Your home address</h2>
      <p className="step-intro">We need your current residential address for identity checks.</p>
      <Field label="Address line 1" error={errors.line1?.message}>
        <input type="text" autoComplete="address-line1" {...register('line1')} />
      </Field>
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
