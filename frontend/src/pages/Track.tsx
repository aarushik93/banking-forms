import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { api, ApiError } from '../api'
import { STATUS_LABELS } from '../constants'
import type { TrackResult } from '../types'

const STATUS_COPY: Record<string, string> = {
  APPROVED:
    'Your application has been approved. Your welcome email has the details, and your ' +
    'direct debit will be set up over the next few business days.',
  IN_REVIEW:
    'Your application is with our team for review. We aim to complete reviews within ' +
    '2 business days and will email you the outcome.',
  DECLINED:
    'We were unable to open an account for this application. We’ve emailed you more ' +
    'information about the decision.',
  SUBMITTED:
    'Your application is saved but our identity checks didn’t complete. Return to the ' +
    'device you applied on and try submitting again.',
  DRAFT:
    'This application hasn’t been submitted yet. Return to the device you started on ' +
    'to finish it.',
}

export default function Track() {
  const [reference, setReference] = useState('')
  const [email, setEmail] = useState('')
  const [dob, setDob] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TrackResult | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!reference.trim() || !email.trim() || !dob) {
      setError('Enter your application reference, email address and date of birth.')
      return
    }
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      setResult(await api.track(reference.trim(), email.trim(), dob))
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 404
          ? "We couldn't find an application matching those details. Check your reference, email and date of birth."
          : 'Something went wrong. Please try again shortly.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="wizard-shell">
      <div className="wizard-inner">
        <div className="wizard-header">
          <h1>Track your application</h1>
          <p className="wizard-reference">
            Enter the details from your confirmation email. We'll show the current status —
            your reference starts with <strong>MF-</strong>.
          </p>
        </div>
        {error && (
          <div className="banner banner-error" role="alert">
            {error}
          </div>
        )}
        <div className="page-card">
          {!result ? (
            <form onSubmit={submit} noValidate>
              <div className="field">
                <label>
                  <span className="field-label">Application reference</span>
                  <input
                    type="text"
                    placeholder="MF-XXXXXXXX"
                    value={reference}
                    onChange={(e) => setReference(e.target.value.toUpperCase())}
                    autoComplete="off"
                  />
                </label>
              </div>
              <div className="grid-2">
                <div className="field">
                  <label>
                    <span className="field-label">Email address</span>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      autoComplete="email"
                    />
                  </label>
                </div>
                <div className="field">
                  <label>
                    <span className="field-label">Date of birth</span>
                    <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
                  </label>
                </div>
              </div>
              <div className="wizard-actions">
                <span />
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  {busy ? 'Checking…' : 'Check status'}
                </button>
              </div>
            </form>
          ) : (
            <div className="track-result">
              <span className={`badge badge--${result.status.toLowerCase()}`}>
                {STATUS_LABELS[result.status]}
              </span>
              <h2>{result.reference}</h2>
              <p>{STATUS_COPY[result.status]}</p>
              {result.submitted_at && (
                <p className="muted">
                  Submitted {new Date(result.submitted_at).toLocaleDateString('en-AU')}
                  {result.decided_at &&
                    ` · decided ${new Date(result.decided_at).toLocaleDateString('en-AU')}`}
                </p>
              )}
              <div className="wizard-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setResult(null)}>
                  Check another
                </button>
                <Link to="/" className="btn btn-primary">
                  Back to Opal Bank
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
