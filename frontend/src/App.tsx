import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import Admin from './pages/Admin'
import ApplyWizard from './pages/ApplyWizard'
import Landing from './pages/Landing'
import Result from './pages/Result'

export default function App() {
  return (
    <BrowserRouter>
      <header className="site-header">
        <div className="site-header-inner">
          <Link to="/" className="brand">
            Example Bank <span>Investments</span>
          </Link>
          <nav>
            <Link to="/apply">Apply</Link>
          </nav>
        </div>
      </header>
      <main className="site-main">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/apply" element={<ApplyWizard />} />
          <Route path="/result" element={<Result />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <p>
          Example Bank Investments is a demonstration service. Capital at risk. © 2026 Example
          Bank plc.
        </p>
      </footer>
    </BrowserRouter>
  )
}
