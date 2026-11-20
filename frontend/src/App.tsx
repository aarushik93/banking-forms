import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import Admin from './pages/Admin'
import ApplyWizard from './pages/ApplyWizard'
import Home from './pages/Home'
import Investments from './pages/Investments'
import Result from './pages/Result'
import Track from './pages/Track'

export default function App() {
  return (
    <BrowserRouter>
      <div className="demo-banner" role="note">
        Demonstration only — Opal Bank is a fictional institution. Please don't enter real
        personal or banking information.
      </div>
      <header className="site-header">
        <div className="site-header-inner">
          <Link to="/" className="brand">
            <span className="brand-gem" aria-hidden="true">
              ◆
            </span>
            Opal Bank
          </Link>
          <nav>
            <Link to="/investments" className="nav-link">
              Investments
            </Link>
            <Link to="/apply" className="nav-cta">
              Apply now
            </Link>
          </nav>
        </div>
      </header>
      <main className="site-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/investments" element={<Investments />} />
          <Route path="/apply" element={<ApplyWizard />} />
          <Route path="/result" element={<Result />} />
          <Route path="/track" element={<Track />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <div className="footer-grid">
          <div className="footer-col footer-col--brand">
            <p className="footer-brand">
              <span className="brand-gem" aria-hidden="true">
                ◆
              </span>
              Opal Bank
            </p>
            <p className="footer-tag">Invest with clarity.</p>
          </div>
          <div className="footer-col">
            <h4>Products</h4>
            <Link to="/investments">Managed Funds</Link>
            <span>Everyday Account</span>
            <span>Home Loans</span>
          </div>
          <div className="footer-col">
            <h4>Support</h4>
            <Link to="/apply">Apply online</Link>
            <Link to="/track">Track an application</Link>
            <span>Help centre</span>
          </div>
          <div className="footer-col">
            <h4>Legal</h4>
            <span>Privacy policy</span>
            <span>Terms of use</span>
            <span>Target market determinations</span>
          </div>
        </div>
        <p className="footer-disclaimer">
          Opal Bank is a fictional demonstration platform and not a real financial institution.
          Nothing here is financial advice, and no real accounts are opened. Capital at risk.
        </p>
      </footer>
    </BrowserRouter>
  )
}
