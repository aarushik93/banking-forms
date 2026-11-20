import { useEffect, useState } from 'react'

import type { EmailOtpSend } from '../types'

interface Props {
  email: string
  verified: boolean
  onSend: () => Promise<EmailOtpSend>
  onConfirm: (code: string) => Promise<void>
  onContinue: () => void
  onBack: () => void
}

export function EmailVerifyStep({ email, verified, onSend, onConfirm, onContinue, onBack }: Props) {
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState(false)
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => setCooldown((s) => Math.max(0, s - 1)), 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  async function sendCode() {
    setBusy(true)
    setError(null)
    try {
      const result = await onSend()
      setSent(true)
      setCooldown(result.resend_in)
    } catch {
      setError('We could not send the code. Please try again shortly.')
    } finally {
      setBusy(false)
    }
  }

  async function confirm() {
    if (!code.trim()) {
      setError('Enter the 6-digit code from the email')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await onConfirm(code.trim())
      onContinue()
    } catch (e) {
      setError(
        e instanceof Error && e.message && !e.message.startsWith('Request failed')
          ? e.message
          : 'That code is not correct. Please try again.',
      )
    } finally {
      setBusy(false)
    }
  }

  if (verified) {
    return (
      <div>
        <h2>Email verified</h2>
        <p className="step-intro">
          <strong>{email}</strong> has been verified. You're good to continue.
        </p>
        <div className="wizard-actions">
          <button type="button" className="btn btn-ghost" onClick={onBack}>
            Back
          </button>
          <button type="button" className="btn btn-primary" onClick={onContinue}>
            Continue
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h2>Verify your email</h2>
      <p className="step-intro">
        We'll email a 6-digit code to <strong>{email}</strong> to confirm it's yours. All
        updates about your application go to this address.
      </p>
      {error && (
        <div className="banner banner-error" role="alert">
          {error}
        </div>
      )}
      {!sent ? (
        <button type="button" className="btn btn-primary" onClick={() => void sendCode()} disabled={busy}>
          {busy ? 'Sending…' : 'Email me a code'}
        </button>
      ) : (
        <>
          <div className="field otp-field">
            <label>
              <span className="field-label">Verification code</span>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                className="otp-input"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                autoComplete="one-time-code"
              />
            </label>
          </div>
          <div className="otp-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void confirm()}
              disabled={busy}
            >
              {busy ? 'Checking…' : 'Verify'}
            </button>
            <button
              type="button"
              className="link-button"
              onClick={() => void sendCode()}
              disabled={busy || cooldown > 0}
            >
              {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
            </button>
          </div>
        </>
      )}
      <div className="wizard-actions">
        <button type="button" className="btn btn-ghost" onClick={onBack} disabled={busy}>
          Back
        </button>
        <span />
      </div>
    </div>
  )
}
