import { Link } from 'react-router-dom'

function Icon({ path }: { path: string }) {
  return (
    <svg
      className="card-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  )
}

const ICON_CHART = 'M3 20h18 M6 16l4-5 3 3 5-7'
const ICON_CARD = 'M3 7h18v11H3z M3 10.5h18 M6 14.5h4'
const ICON_HOME = 'M4 11l8-7 8 7 M6 10v10h12V10 M10 20v-5h4v5'
const ICON_SHIELD = 'M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z'
const ICON_CLOCK = 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7v5l3.5 2'
const ICON_RECEIPT = 'M6 3h12v18l-2-1.4L14 21l-2-1.4L10 21l-2-1.4L6 21z M9 8h6 M9 12h6'

const COMING_SOON = [
  {
    name: 'Everyday Account',
    icon: ICON_CARD,
    description: 'No monthly account fees, instant payments and a card that works everywhere.',
  },
  {
    name: 'Home Loans',
    icon: ICON_HOME,
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
              <Icon path={ICON_CHART} />
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
                <Icon path={product.icon} />
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
          <Icon path={ICON_CLOCK} />
          <h3>Verified in minutes</h3>
          <p>Electronic identity verification — no certified copies, no waiting rooms.</p>
        </div>
        <div>
          <Icon path={ICON_SHIELD} />
          <h3>Security first</h3>
          <p>Encrypted end to end, with every decision recorded in a full audit trail.</p>
        </div>
        <div>
          <Icon path={ICON_RECEIPT} />
          <h3>Transparent fees</h3>
          <p>One simple annual charge per fund. No entry, exit or platform fees.</p>
        </div>
      </section>
    </div>
  )
}
