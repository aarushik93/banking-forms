import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import {
  EMPLOYMENT_OPTIONS,
  SOURCE_OF_FUNDS_OPTIONS,
  formatMoney,
  labelFor,
} from '../constants'
import type { Fund } from '../types'
import { declarationsSchema, type DeclarationsValues } from '../validation'
import type { WizardData } from '../wizardTypes'

interface Props {
  data: WizardData
  funds: Fund[]
  onBack: () => void
  onEdit: (step: number) => void
  onSubmit: (values: DeclarationsValues) => void
  saving: boolean
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

export function ReviewStep({ data, funds, onBack, onEdit, onSubmit, saving }: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DeclarationsValues>({
    resolver: zodResolver(declarationsSchema),
    defaultValues: { accepted_terms: false, accepted_risk: false, consent_kyc: false },
  })

  const fund = funds.find((f) => f.code === data.investment?.fund_code)

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <h2>Check your answers</h2>

      <section className="summary-section">
        <header>
          <h3>About you</h3>
          <button type="button" className="link-button" onClick={() => onEdit(0)}>
            Edit
          </button>
        </header>
        <dl>
          <Row
            label="Name"
            value={`${data.personal?.title ?? ''} ${data.personal?.first_name ?? ''} ${data.personal?.last_name ?? ''}`}
          />
          <Row label="Date of birth" value={data.personal?.date_of_birth ?? '—'} />
          <Row label="Email" value={data.personal?.email ?? '—'} />
          <Row label="Phone" value={data.personal?.phone ?? '—'} />
        </dl>
      </section>

      <section className="summary-section">
        <header>
          <h3>Address</h3>
          <button type="button" className="link-button" onClick={() => onEdit(2)}>
            Edit
          </button>
        </header>
        <dl>
          <Row
            label="Address"
            value={[
              data.address?.line1,
              data.address?.line2,
              data.address?.city,
              data.address?.state,
              data.address?.postcode,
            ]
              .filter(Boolean)
              .join(', ')}
          />
          <Row label="Years at address" value={String(data.address?.years_at_address ?? '—')} />
        </dl>
      </section>

      <section className="summary-section">
        <header>
          <h3>Work, income and tax</h3>
          <button type="button" className="link-button" onClick={() => onEdit(3)}>
            Edit
          </button>
        </header>
        <dl>
          <Row
            label="Employment"
            value={labelFor(EMPLOYMENT_OPTIONS, data.financial?.employment_status)}
          />
          <Row label="Annual income" value={formatMoney(data.financial?.annual_income)} />
          <Row label="Tax residency" value={data.financial?.tax_residency_country ?? '—'} />
        </dl>
      </section>

      <section className="summary-section">
        <header>
          <h3>Investment</h3>
          <button type="button" className="link-button" onClick={() => onEdit(4)}>
            Edit
          </button>
        </header>
        <dl>
          <Row label="Fund" value={fund ? fund.name : (data.investment?.fund_code ?? '—')} />
          <Row label="Initial lump sum" value={formatMoney(data.investment?.initial_investment)} />
          <Row
            label="Monthly contribution"
            value={formatMoney(data.investment?.monthly_contribution)}
          />
          <Row
            label="Source of funds"
            value={labelFor(SOURCE_OF_FUNDS_OPTIONS, data.investment?.source_of_funds)}
          />
        </dl>
      </section>

      <section className="summary-section">
        <header>
          <h3>Funding account</h3>
          <button type="button" className="link-button" onClick={() => onEdit(5)}>
            Edit
          </button>
        </header>
        <dl>
          <Row label="Account holder" value={data.bank?.account_holder_name ?? '—'} />
          <Row label="BSB" value={data.bank?.bsb ?? '—'} />
          <Row
            label="Account number"
            value={data.bank ? `****${data.bank.account_number.slice(-4)}` : '—'}
          />
        </dl>
      </section>

      <section className="declarations">
        <h3>Declarations</h3>
        <div className={`check-field${errors.accepted_terms ? ' field--invalid' : ''}`}>
          <label>
            <input type="checkbox" {...register('accepted_terms')} />
            <span>
              I confirm the information I've given is accurate, and I accept the account terms
              and conditions and the fund's Key Investor Information Document.
            </span>
          </label>
          {errors.accepted_terms && (
            <p className="field-error" role="alert">
              {errors.accepted_terms.message}
            </p>
          )}
        </div>
        <div className={`check-field${errors.accepted_risk ? ' field--invalid' : ''}`}>
          <label>
            <input type="checkbox" {...register('accepted_risk')} />
            <span>
              I understand that investments can fall as well as rise in value and I may get back
              less than I invest.
            </span>
          </label>
          {errors.accepted_risk && (
            <p className="field-error" role="alert">
              {errors.accepted_risk.message}
            </p>
          )}
        </div>
        <div className={`check-field${errors.consent_kyc ? ' field--invalid' : ''}`}>
          <label>
            <input type="checkbox" {...register('consent_kyc')} />
            <span>
              I consent to my identity being verified electronically against records held by
              credit reporting bodies and other data sources, as required under the AML/CTF Act
              2006. This check is not a credit check and does not affect my credit score.
            </span>
          </label>
          {errors.consent_kyc && (
            <p className="field-error" role="alert">
              {errors.consent_kyc.message}
            </p>
          )}
        </div>
      </section>

      <div className="wizard-actions">
        <button type="button" className="btn btn-ghost" onClick={onBack} disabled={saving}>
          Back
        </button>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Submitting…' : 'Submit application'}
        </button>
      </div>
    </form>
  )
}
