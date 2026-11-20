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

export default function Investments() {
  const [funds, setFunds] = useState<Fund[]>([])

  useEffect(() => {
    api.getFunds().then(setFunds).catch(() => setFunds([]))
  }, [])

  return (
    <div className="landing">
      <section className="hero">
        <h1>Managed Funds</h1>
        <p>
          Four professionally managed portfolios, one simple application. Start from $500,
          add to it monthly, and verify your identity entirely online.
        </p>
        <Link to="/apply" className="btn btn-primary btn-large">
          Start your application
        </Link>
        <p className="hero-note">
          Takes about 10 minutes. You'll need your BSB and account number and, ideally, your
          Tax File Number. Your progress is saved as you go.
        </p>
      </section>

      <section className="fund-grid" aria-label="Available funds">
        {funds.map((fund) => (
          <article key={fund.code} className="fund-card">
            <div className="fund-risk">Risk {fund.risk_level}/7</div>
            <h3>{fund.name}</h3>
            <p>{fund.description}</p>
            <p className="fund-charge">
              Annual charge {Number(fund.annual_charge_pct).toFixed(2)}%
            </p>
          </article>
        ))}
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
