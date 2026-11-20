import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import type { Fund } from '../types'

const STEPS = [
  ['Tell us about you', 'Your details, address and finances — about 10 minutes.'],
  ['Verify as you go', 'We confirm your email and verify your identity electronically.'],
  ['Choose your investment', 'Pick a fund, your starting amount, and an optional monthly plan.'],
  ['Start investing', 'Approved applications are funded by direct debit and invested.'],
]

function RiskDots({ level }: { level: number }) {
  return (
    <span className="risk-dots" aria-hidden="true">
      {Array.from({ length: 7 }, (_, i) => (
        <span key={i} className={`risk-dot${i < level ? ' risk-dot--on' : ''}`} />
      ))}
    </span>
  )
}

export default function Investments() {
  const [funds, setFunds] = useState<Fund[]>([])

  useEffect(() => {
    api.getFunds().then(setFunds).catch(() => setFunds([]))
  }, [])

  return (
    <div className="landing">
      <section className="invest-hero">
        <p className="eyebrow">Our funds</p>
        <h1>Managed funds, without the management fuss.</h1>
        <p>
          Four professionally managed portfolios across the risk spectrum, one simple annual
          charge, and a fully online application. Start from $500, add to it monthly.
        </p>
        <Link to="/apply" className="btn btn-primary btn-large">
          Start your application
        </Link>
        <p className="hero-note">
          Takes about 10 minutes. You'll need your BSB and account number and, ideally, your
          Tax File Number. Your progress is saved as you go.
        </p>
      </section>

      <section aria-label="Fund comparison">
        <div className="funds-table-wrap">
          <table className="funds-table">
            <thead>
              <tr>
                <th>Fund</th>
                <th>Risk level</th>
                <th>Annual charge</th>
              </tr>
            </thead>
            <tbody>
              {funds.map((fund) => (
                <tr key={fund.code}>
                  <td>
                    <p className="fund-name">{fund.name}</p>
                    <p className="fund-desc">{fund.description}</p>
                  </td>
                  <td className="risk-cell">
                    <RiskDots level={fund.risk_level} />
                    {fund.risk_level}/7
                  </td>
                  <td className="fund-charge-cell">
                    {Number(fund.annual_charge_pct).toFixed(2)}% p.a.
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="how-steps" aria-label="How applying works">
        <h2>How it works</h2>
        <ol>
          {STEPS.map(([title, body], index) => (
            <li key={title}>
              <span className="step-number">{index + 1}</span>
              <div>
                <h3>{title}</h3>
                <p>{body}</p>
              </div>
            </li>
          ))}
        </ol>
        <Link to="/apply" className="btn btn-primary btn-large">
          Apply online
        </Link>
      </section>

      <section className="disclaimer">
        <p>
          Capital at risk. The value of investments can fall as well as rise and you may get back
          less than you invest. Tax treatment depends on individual circumstances and may change.
        </p>
      </section>
    </div>
  )
}
