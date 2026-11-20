import { Link } from 'react-router-dom'

const PRODUCTS = [
  {
    name: 'Everyday Account',
    description: 'Zero monthly fees, instant payments, and a card that works everywhere.',
    status: 'Coming soon',
  },
  {
    name: 'Home Loans',
    description: 'Transparent rates and a fully digital approval journey.',
    status: 'Coming soon',
  },
]

export default function Home() {
  return (
    <div className="home">
      <section className="hero-bank">
        <h1>
          Wealth, <span className="opal-text">brilliantly</span> simple.
        </h1>
        <p>
          Opal Bank brings private-bank quality investing to everyone. Open a managed funds
          account entirely online — verified, approved, and invested in minutes.
        </p>
        <div className="hero-ctas">
          <Link to="/investments" className="btn btn-opal btn-large">
            Explore investments
          </Link>
          <Link to="/apply" className="btn btn-outline-light btn-large">
            Apply online
          </Link>
        </div>
      </section>

      <section className="products" aria-label="Our products">
        <h2>Our products</h2>
        <div className="product-grid">
          <article className="product-card product-card--live">
            <div className="product-status product-status--live">Available now</div>
            <h3>Managed Funds</h3>
            <p>
              Professionally managed portfolios from $500. Choose your fund, set a monthly
              contribution, and track it all online.
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
          {PRODUCTS.map((product) => (
            <article key={product.name} className="product-card product-card--soon">
              <div className="product-status">{product.status}</div>
              <h3>{product.name}</h3>
              <p>{product.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="trust-strip" aria-label="Why Opal Bank">
        <div>
          <h3>Verified in minutes</h3>
          <p>Electronic identity verification — no branch visits, no certified copies.</p>
        </div>
        <div>
          <h3>Security first</h3>
          <p>Encrypted end to end, with every decision recorded in a full audit trail.</p>
        </div>
        <div>
          <h3>Transparent fees</h3>
          <p>One simple annual charge per fund. No entry, exit, or hidden platform fees.</p>
        </div>
      </section>
    </div>
  )
}
