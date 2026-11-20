import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { api } from '../api'
import { clearSession, loadSession } from '../storage'
import type { ApplicationStatus, SubmitResponse } from '../types'

interface Outcome {
  status: ApplicationStatus
  reference: string
  message?: string
}

const COPY: Record<string, { icon: string; title: string; body: string }> = {
  APPROVED: {
    icon: '✓',
    title: 'Your application has been approved',
    body: 'We’ve emailed you confirmation. Your account is being opened and your welcome pack, including your Direct Debit schedule, is on its way.',
  },
  IN_REVIEW: {
    icon: '⏳',
    title: 'Your application is being reviewed',
    body: 'We’ve received your application and our team is completing some additional checks. We aim to be in touch by email within 2 working days.',
  },
  DECLINED: {
    icon: '✕',
    title: 'We couldn’t open an account this time',
    body: 'We’ve emailed you more information about this decision and how to contact us if you’d like to discuss it.',
  },
  SUBMITTED: {
    icon: '!',
    title: 'We couldn’t finish our checks',
    body: 'Your application is saved, but our identity-checking service was temporarily unavailable. Please try submitting again.',
  },
}

export default function Result() {
  const location = useLocation()
  const navigate = useNavigate()
  const submitted = (location.state as SubmitResponse | null) ?? null
  const [outcome, setOutcome] = useState<Outcome | null>(
    submitted
      ? { status: submitted.status, reference: submitted.reference, message: submitted.message }
      : null,
  )
  const [retrying, setRetrying] = useState(false)

  useEffect(() => {
    if (outcome) return
    const session = loadSession()
    if (!session) {
      navigate('/')
      return
    }
    api
      .getApplication(session.id, session.resumeToken)
      .then((view) => {
        if (view.status === 'DRAFT') navigate('/apply')
        else setOutcome({ status: view.status, reference: view.reference })
      })
      .catch(() => navigate('/'))
  }, [outcome, navigate])

  async function retrySubmit() {
    const session = loadSession()
    if (!session) return
    setRetrying(true)
    try {
      const result = await api.submit(session.id, session.resumeToken)
      setOutcome({ status: result.status, reference: result.reference, message: result.message })
    } finally {
      setRetrying(false)
    }
  }

  if (!outcome) {
    return (
      <div className="page-card">
        <p className="loading">Checking your application…</p>
      </div>
    )
  }

  const copy = COPY[outcome.status] ?? COPY.IN_REVIEW

  return (
    <div className="page-card result">
      <div className={`result-icon result-icon--${outcome.status.toLowerCase()}`}>{copy.icon}</div>
      <h1>{copy.title}</h1>
      <p className="result-reference">
        Application reference <strong>{outcome.reference}</strong>
      </p>
      <p>{copy.body}</p>
      {outcome.status === 'SUBMITTED' && (
        <button className="btn btn-primary" onClick={() => void retrySubmit()} disabled={retrying}>
          {retrying ? 'Submitting…' : 'Try again'}
        </button>
      )}
      <button
        className="btn btn-ghost"
        onClick={() => {
          clearSession()
          navigate('/')
        }}
      >
        Start a new application
      </button>
    </div>
  )
}
