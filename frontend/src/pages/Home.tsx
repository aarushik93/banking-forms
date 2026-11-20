import { Link } from 'react-router-dom'

const COMING_SOON = [
  {
    name: 'Everyday Account',
    description: 'No monthly account fees, instant payments and a card that works everywhere.',
  },
  {
    name: 'Home Loans',
    description: 'Transparent rates with a fully digital approval process.',
  },
]

export default function Home() {
  return (
    <div className="home">
      <section className="hero-bank">
        <p className="hero-eyebrow">Opal Bank Investments</p>
        <h1>Invest with clarity.</h1>
        <p>
          Professionally managed portfolios with transparent fees and fully digital
          onboarding. Open your account online — identity verified electronically,
          no paperwork, no branch visits.
        </p>
        <div className="hero-ctas">
          <Link to="/investments" className="btn btn-primary btn-large">
            View managed funds
          </Link>
          <Link to="/apply" className="btn btn-secondary btn-large">
            Apply online
          </Link>
        </div>
      </section>

      <section className="hero-stats" aria-label="At a glance">
        <div>
          <strong>$500</strong>
          <span>minimum initial investment</span>
        </div>
        <div>
          <strong>0.22%–0.55%</strong>
          <span>annual fund charges, nothing hidden</span>
        </div>
        <div>
          <strong>~10 minutes</strong>
          <span>to apply, verified online</span>
        </div>
      </section>

      <section className="products" aria-label="Our products">
        <div className="products-inner">
          <h2>Our products</h2>
          <div className="product-grid">
            <article className="product-card product-card--live">
              <div className="product-status product-status--live">Available now</div>
              <h3>Managed Funds</h3>
              <p>
                Four professionally managed portfolios across the risk spectrum. Start from
                $500, add a monthly plan, and track everything online.
              </p>
              <div className="product-actions">
                <Link to="/apply" className="btn btn-primary">
                  Apply now
                </Link>
                <Link to="/investments" className="link-button">
                  Learn more
                </Link>
              </div>
            </article>
            {COMING_SOON.map((product) => (
              <article key={product.name} className="product-card product-card--soon">
                <div className="product-status">Coming soon</div>
                <h3>{product.name}</h3>
                <p>{product.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="trust-strip" aria-label="Why Opal Bank">
        <div>
          <h3>Verified in minutes</h3>
          <p>Electronic identity verification — no certified copies, no waiting rooms.</p>
        </div>
        <div>
          <h3>Security first</h3>
          <p>Encrypted end to end, with every decision recorded in a full audit trail.</p>
        </div>
        <div>
          <h3>Transparent fees</h3>
          <p>One simple annual charge per fund. No entry, exit or platform fees.</p>
        </div>
      </section>
    </div>
  )
}
