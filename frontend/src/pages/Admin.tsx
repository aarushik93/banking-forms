import { useCallback, useEffect, useState, type FormEvent } from 'react'

import { api, ApiError } from '../api'
import { STATUS_LABELS, formatMoney } from '../constants'
import type { AdminDetail, AdminSummary, ApplicationStatus } from '../types'

const TOKEN_KEY = 'mf-admin-token'
const FILTERS: Array<ApplicationStatus | 'ALL'> = [
  'ALL',
  'IN_REVIEW',
  'SUBMITTED',
  'APPROVED',
  'DECLINED',
  'DRAFT',
]

function StatusBadge({ status }: { status: ApplicationStatus }) {
  return <span className={`badge badge--${status.toLowerCase()}`}>{STATUS_LABELS[status]}</span>
}

export default function Admin() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) ?? '')
  const [tokenInput, setTokenInput] = useState('')
  const [filter, setFilter] = useState<ApplicationStatus | 'ALL'>('ALL')
  const [rows, setRows] = useState<AdminSummary[]>([])
  const [detail, setDetail] = useState<AdminDetail | null>(null)
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const handleAuthError = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) {
      sessionStorage.removeItem(TOKEN_KEY)
      setToken('')
      setError('That admin token was rejected. Please sign in again.')
    } else {
      setError('Something went wrong talking to the server.')
    }
  }, [])

  const refresh = useCallback(async () => {
    if (!token) return
    try {
      setError(null)
      const list = await api.admin.list(token, filter === 'ALL' ? undefined : filter)
      setRows(list)
    } catch (e) {
      handleAuthError(e)
    }
  }, [token, filter, handleAuthError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  function signIn(event: FormEvent) {
    event.preventDefault()
    const trimmed = tokenInput.trim()
    if (!trimmed) return
    sessionStorage.setItem(TOKEN_KEY, trimmed)
    setToken(trimmed)
    setTokenInput('')
  }

  async function openDetail(id: string) {
    try {
      setDetail(await api.admin.detail(token, id))
      setNote('')
    } catch (e) {
      handleAuthError(e)
    }
  }

  async function decide(decision: 'approve' | 'decline') {
    if (!detail) return
    setBusy(true)
    try {
      const updated = await api.admin.decide(token, detail.id, decision, note)
      setDetail(updated)
      await refresh()
    } catch (e) {
      handleAuthError(e)
    } finally {
      setBusy(false)
    }
  }

  if (!token) {
    return (
      <div className="page-card admin-login">
        <h1>Back office</h1>
        <p className="step-intro">Enter the admin API token to review applications.</p>
        {error && (
          <div className="banner banner-error" role="alert">
            {error}
          </div>
        )}
        <form onSubmit={signIn}>
          <div className="field">
            <label>
              <span className="field-label">Admin token</span>
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                autoComplete="off"
              />
            </label>
          </div>
          <button type="submit" className="btn btn-primary">
            Sign in
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className="admin">
      <div className="admin-toolbar">
        <h1>Applications</h1>
        <div className="filter-chips" role="group" aria-label="Filter by status">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`chip${filter === f ? ' chip--active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'ALL' ? 'All' : STATUS_LABELS[f]}
            </button>
          ))}
        </div>
      </div>
      {error && (
        <div className="banner banner-error" role="alert">
          {error}
        </div>
      )}
      <div className="admin-layout">
        <div className="page-card table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Applicant</th>
                <th>Fund</th>
                <th>Amount</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty">
                    No applications found.
                  </td>
                </tr>
              )}
              {rows.map((row) => (
                <tr
                  key={row.id}
                  className={detail?.id === row.id ? 'row--selected' : ''}
                  onClick={() => void openDetail(row.id)}
                >
                  <td>{row.reference}</td>
                  <td>
                    {row.applicant_name ?? '—'}
                    <div className="muted">{row.email ?? ''}</div>
                  </td>
                  <td>{row.fund_code ?? '—'}</td>
                  <td>{formatMoney(row.initial_investment)}</td>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {detail && (
          <aside className="page-card admin-detail">
            <header className="admin-detail-header">
              <div>
                <h2>{detail.reference}</h2>
                <StatusBadge status={detail.status} />
              </div>
              <button className="link-button" onClick={() => setDetail(null)}>
                Close
              </button>
            </header>

            <h3>Applicant</h3>
            <dl className="detail-list">
              <div>
                <dt>Name</dt>
                <dd>
                  {detail.personal
                    ? `${detail.personal.title} ${detail.personal.first_name} ${detail.personal.last_name}`
                    : '—'}
                </dd>
              </div>
              <div>
                <dt>Date of birth</dt>
                <dd>{detail.personal?.date_of_birth ?? '—'}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{detail.personal?.email ?? '—'}</dd>
              </div>
              <div>
                <dt>Address</dt>
                <dd>
                  {detail.address
                    ? `${detail.address.line1}, ${detail.address.city}, ${detail.address.postcode}`
                    : '—'}
                </dd>
              </div>
            </dl>

            <h3>Investment</h3>
            <dl className="detail-list">
              <div>
                <dt>Fund</dt>
                <dd>{detail.investment?.fund_code ?? '—'}</dd>
              </div>
              <div>
                <dt>Initial</dt>
                <dd>{formatMoney(detail.investment?.initial_investment ?? null)}</dd>
              </div>
              <div>
                <dt>Monthly</dt>
                <dd>{formatMoney(detail.investment?.monthly_contribution ?? null)}</dd>
              </div>
              <div>
                <dt>Bank account</dt>
                <dd>
                  {detail.bank
                    ? `BSB ${detail.bank.bsb} / ${detail.bank.account_number_masked}`
                    : '—'}
                </dd>
              </div>
            </dl>

            <h3>KYC</h3>
            <dl className="detail-list">
              <div>
                <dt>Result</dt>
                <dd>{detail.kyc_status ?? 'Not run'}</dd>
              </div>
              <div>
                <dt>Provider ref</dt>
                <dd>{detail.kyc_reference ?? '—'}</dd>
              </div>
              {detail.decided_by && (
                <div>
                  <dt>Decided by</dt>
                  <dd>
                    {detail.decided_by}
                    {detail.decision_note ? ` — ${detail.decision_note}` : ''}
                  </dd>
                </div>
              )}
            </dl>

            {detail.status === 'IN_REVIEW' && (
              <div className="decision-box">
                <h3>Manual decision</h3>
                <div className="field">
                  <label>
                    <span className="field-label">Note (optional)</span>
                    <textarea
                      rows={2}
                      maxLength={500}
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                  </label>
                </div>
                <div className="decision-actions">
                  <button
                    className="btn btn-primary"
                    disabled={busy}
                    onClick={() => void decide('approve')}
                  >
                    Approve
                  </button>
                  <button
                    className="btn btn-danger"
                    disabled={busy}
                    onClick={() => void decide('decline')}
                  >
                    Decline
                  </button>
                </div>
              </div>
            )}

            <h3>Audit trail</h3>
            <ul className="audit-list">
              {detail.audit.map((event, i) => (
                <li key={i}>
                  <span className="audit-time">
                    {new Date(event.created_at).toLocaleString('en-GB')}
                  </span>
                  <span className="audit-type">{event.event_type}</span>
                  {event.detail && (
                    <span className="audit-detail">{JSON.stringify(event.detail)}</span>
                  )}
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </div>
  )
}
