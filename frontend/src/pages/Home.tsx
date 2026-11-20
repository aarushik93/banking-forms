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

function PortfolioCard() {
  return (
    <div className="hero-card" aria-hidden="true">
      <div className="hero-card-head">
        <span className="hero-card-label">Portfolio value</span>
        <span className="hero-card-badge">▲ 6.4% this year</span>
      </div>
      <div className="hero-card-balance">$24,836.22</div>
      <svg viewBox="0 0 320 84" role="presentation">
        <path
          d="M0 66 C 24 60, 40 68, 62 56 S 104 34, 128 40 S 172 46, 196 32 S 244 16, 268 22 S 304 10, 320 14 L 320 84 L 0 84 Z"
          fill="#0f766e"
          opacity="0.09"
        />
        <path
          d="M0 66 C 24 60, 40 68, 62 56 S 104 34, 128 40 S 172 46, 196 32 S 244 16, 268 22 S 304 10, 320 14"
          fill="none"
          stroke="#0f766e"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>
      <div className="hero-card-funds">
        <span>Balanced Growth</span>
        <span>Global Equity Index</span>
        <span>+ $250 monthly</span>
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <div className="home">
      <section className="hero-bank">
        <div className="hero-inner">
          <div>
            <p className="hero-eyebrow">Opal Bank Investments</p>
            <h1>Invest with clarity.</h1>
            <p className="hero-sub">
              Professionally managed portfolios with transparent fees and fully digital
              onboarding. Verified online, invested in minutes — no paperwork, no branches.
            </p>
            <div className="hero-ctas">
              <Link to="/apply" className="btn btn-cream btn-large">
                Apply online
              </Link>
              <Link to="/investments" className="btn btn-outline-cream btn-large">
                View managed funds
              </Link>
            </div>
          </div>
          <PortfolioCard />
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
                  Learn more →
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
