import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import Admin from './pages/Admin'
import ApplyWizard from './pages/ApplyWizard'
import Home from './pages/Home'
import Investments from './pages/Investments'
import Result from './pages/Result'

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
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <p className="footer-brand">
          <span className="brand-gem" aria-hidden="true">
            ◆
          </span>
          Opal Bank
        </p>
        <p>
          Opal Bank is a fictional demonstration platform and not a real financial institution.
          Nothing here is financial advice, and no real accounts are opened. Capital at risk.
        </p>
      </footer>
    </BrowserRouter>
  )
}
