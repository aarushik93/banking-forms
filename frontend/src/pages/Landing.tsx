import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import type { Fund } from '../types'

export default function Landing() {
  const [funds, setFunds] = useState<Fund[]>([])

  useEffect(() => {
    api.getFunds().then(setFunds).catch(() => setFunds([]))
  }, [])

  return (
    <div className="landing">
      <section className="hero">
        <h1>Invest in your future, in minutes</h1>
        <p>
          Open a managed funds account online. Choose from our range of professionally managed
          portfolios, start from £500, and verify your identity electronically — no paperwork,
          no branch visit.
        </p>
        <Link to="/apply" className="btn btn-primary btn-large">
          Start your application
        </Link>
        <p className="hero-note">
          Takes about 10 minutes. You'll need your bank details and, ideally, your National
          Insurance number. Your progress is saved as you go.
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

      <section className="disclaimer">
        <p>
          Capital at risk. The value of investments can fall as well as rise and you may get back
          less than you invest. Tax treatment depends on individual circumstances and may change.
        </p>
      </section>
    </div>
  )
}
