import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Field } from '../components/Field'
import { TITLES } from '../constants'
import { personalSchema, type PersonalValues } from '../validation'

interface Props {
  defaultValues?: Partial<PersonalValues>
  onNext: (values: PersonalValues) => void
  saving: boolean
}

export function PersonalStep({ defaultValues, onNext, saving }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PersonalValues>({ resolver: zodResolver(personalSchema), defaultValues })

  return (
    <form onSubmit={handleSubmit(onNext)} noValidate>
      <h2>About you</h2>
      <p className="step-intro">
        Tell us who you are. We use these details to verify your identity electronically.
      </p>
      <div className="grid-2">
        <Field label="Title" error={errors.title?.message}>
          <select {...register('title')} defaultValue={defaultValues?.title ?? ''}>
            <option value="" disabled>
              Select…
            </option>
            {TITLES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Date of birth" error={errors.date_of_birth?.message}>
          <input type="date" {...register('date_of_birth')} />
        </Field>
        <Field label="First name" error={errors.first_name?.message}>
          <input type="text" autoComplete="given-name" {...register('first_name')} />
        </Field>
        <Field label="Last name" error={errors.last_name?.message}>
          <input type="text" autoComplete="family-name" {...register('last_name')} />
        </Field>
        <Field label="Email address" error={errors.email?.message}>
          <input type="email" autoComplete="email" {...register('email')} />
        </Field>
        <Field label="Phone number" error={errors.phone?.message} hint="Include the country code">
          <input type="tel" autoComplete="tel" placeholder="+61 412 345 678" {...register('phone')} />
        </Field>
      </div>
      <div className="wizard-actions">
        <span />
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving…' : 'Continue'}
        </button>
      </div>
    </form>
  )
}
