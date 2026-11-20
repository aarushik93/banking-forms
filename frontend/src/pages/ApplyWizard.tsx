import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError } from '../api'
import { ProcessingScreen } from '../components/ProcessingScreen'
import { Stepper } from '../components/Stepper'
import { clearSession, loadSession, saveSession, type Session } from '../storage'
import { AddressStep } from '../steps/AddressStep'
import { BankStep } from '../steps/BankStep'
import { EmailVerifyStep } from '../steps/EmailVerifyStep'
import { FinancialStep } from '../steps/FinancialStep'
import { InvestmentStep } from '../steps/InvestmentStep'
import { PersonalStep } from '../steps/PersonalStep'
import { ReviewStep } from '../steps/ReviewStep'
import type { ApplicationView, Fund } from '../types'
import type { DeclarationsValues } from '../validation'
import type { WizardData } from '../wizardTypes'

const STEPS = [
  'About you',
  'Verify email',
  'Address',
  'Finances',
  'Investment',
  'Bank',
  'Review',
] as const

function describeError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (typeof e.detail === 'string') return e.detail
    if (e.detail && typeof e.detail === 'object' && 'message' in e.detail) {
      return String((e.detail as { message: unknown }).message)
    }
  }
  return fallback
}

export default function ApplyWizard() {
  const navigate = useNavigate()
  const [funds, setFunds] = useState<Fund[]>([])
  const [session, setSession] = useState<Session | null>(null)
  const [reference, setReference] = useState('')
  const [data, setData] = useState<WizardData>({})
  const [step, setStep] = useState(0)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [emailVerified, setEmailVerified] = useState(false)
  const [processing, setProcessing] = useState(false)

  const hydrate = useCallback((view: ApplicationView) => {
    // The API returns values that already passed backend validation, so the
    // narrowing casts to the form value types are safe.
    const next: WizardData = {}
    if (view.personal) next.personal = view.personal as WizardData['personal']
    if (view.address) {
      next.address = {
        ...view.address,
        line2: view.address.line2 ?? '',
      } as WizardData['address']
    }
    if (view.financial) {
      next.financial = {
        ...view.financial,
        tfn: view.financial.tfn ?? '',
      } as WizardData['financial']
    }
    if (view.investment) {
      next.investment = {
        ...view.investment,
        initial_investment: Number(view.investment.initial_investment),
        monthly_contribution: Number(view.investment.monthly_contribution ?? 0),
      } as WizardData['investment']
    }
    // Bank details come back masked, so they are re-entered when resuming.
    setData(next)
    setEmailVerified(view.email_verified)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const fundsList = await api.getFunds()
        if (cancelled) return
        setFunds(fundsList)

        const existing = loadSession()
        if (existing) {
          try {
            const view = await api.getApplication(existing.id, existing.resumeToken)
            if (cancelled) return
            if (view.status !== 'DRAFT') {
              navigate('/result')
              return
            }
            setSession(existing)
            setReference(view.reference)
            hydrate(view)
            setLoading(false)
            return
          } catch {
            clearSession()
          }
        }
        const created = await api.createApplication()
        if (cancelled) return
        const newSession = { id: created.id, resumeToken: created.resume_token }
        saveSession(newSession)
        setSession(newSession)
        setReference(created.reference)
        setLoading(false)
      } catch {
        if (!cancelled) {
          setError('We could not start your application. Please refresh to try again.')
          setLoading(false)
        }
      }
    }
    void init()
    return () => {
      cancelled = true
    }
  }, [navigate, hydrate])

  async function saveSection<K extends keyof WizardData>(
    name: K,
    values: NonNullable<WizardData[K]>,
    payload: Record<string, unknown>,
  ) {
    if (!session) return
    setSaving(true)
    setError(null)
    try {
      const view = await api.updateDraft(session.id, session.resumeToken, { [name]: payload })
      setEmailVerified(view.email_verified)
      setData((d) => ({ ...d, [name]: values }))
      setStep((s) => s + 1)
      window.scrollTo(0, 0)
    } catch (e) {
      setError(describeError(e, 'We could not save your answers. Please try again.'))
    } finally {
      setSaving(false)
    }
  }

  async function submitAll(declarations: DeclarationsValues) {
    if (!session) return
    setSaving(true)
    setError(null)
    setProcessing(true)
    window.scrollTo(0, 0)
    // Keep the processing screen up for a minimum beat so the decisioning
    // stages are legible even when the checks come back quickly.
    const startedAt = Date.now()
    const MIN_PROCESSING_MS = 4500
    try {
      await api.updateDraft(session.id, session.resumeToken, { declarations })
      const result = await api.submit(session.id, session.resumeToken)
      const remaining = MIN_PROCESSING_MS - (Date.now() - startedAt)
      if (remaining > 0) await new Promise((resolve) => setTimeout(resolve, remaining))
      navigate('/result', { state: result })
    } catch (e) {
      setProcessing(false)
      setError(describeError(e, 'We could not submit your application. Please try again.'))
    } finally {
      setSaving(false)
    }
  }

  const goBack = () => {
    setStep((s) => Math.max(0, s - 1))
    window.scrollTo(0, 0)
  }

  if (loading) {
    return (
      <div className="page-card">
        <p className="loading">Preparing your application…</p>
      </div>
    )
  }

  if (processing) {
    return (
      <div className="page-card">
        <ProcessingScreen />
      </div>
    )
  }

  return (
    <div className="wizard">
      <div className="wizard-header">
        <h1>Managed funds application</h1>
        {reference && (
          <p className="wizard-reference">
            Reference <strong>{reference}</strong> — your progress is saved automatically.
          </p>
        )}
      </div>
      <Stepper steps={STEPS} current={step} />
      {error && (
        <div className="banner banner-error" role="alert">
          {error}
        </div>
      )}
      <div className="page-card">
        {step === 0 && (
          <PersonalStep
            defaultValues={data.personal}
            saving={saving}
            onNext={(v) => void saveSection('personal', v, v)}
          />
        )}
        {step === 1 && session && (
          <EmailVerifyStep
            email={data.personal?.email ?? ''}
            verified={emailVerified}
            onSend={() => api.sendEmailOtp(session.id, session.resumeToken)}
            onConfirm={async (code) => {
              await api.confirmEmailOtp(session.id, session.resumeToken, code)
              setEmailVerified(true)
            }}
            onContinue={() => {
              setStep(2)
              window.scrollTo(0, 0)
            }}
            onBack={goBack}
          />
        )}
        {step === 2 && (
          <AddressStep
            defaultValues={data.address}
            saving={saving}
            onBack={goBack}
            onNext={(v) => void saveSection('address', v, { ...v, line2: v.line2 || null })}
          />
        )}
        {step === 3 && (
          <FinancialStep
            defaultValues={data.financial}
            saving={saving}
            onBack={goBack}
            onNext={(v) => void saveSection('financial', v, { ...v, tfn: v.tfn || null })}
          />
        )}
        {step === 4 && (
          <InvestmentStep
            funds={funds}
            defaultValues={data.investment}
            saving={saving}
            onBack={goBack}
            onNext={(v) => void saveSection('investment', v, v)}
          />
        )}
        {step === 5 && (
          <BankStep
            defaultValues={data.bank}
            saving={saving}
            onBack={goBack}
            onNext={(v) =>
              void saveSection('bank', v, { ...v, bsb: v.bsb.replace(/\D/g, '') })
            }
          />
        )}
        {step === 6 && (
          <ReviewStep
            data={data}
            funds={funds}
            saving={saving}
            onBack={goBack}
            onEdit={(s) => {
              setStep(s)
              window.scrollTo(0, 0)
            }}
            onSubmit={(v) => void submitAll(v)}
          />
        )}
      </div>
    </div>
  )
}
