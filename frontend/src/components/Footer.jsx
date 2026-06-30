import React from 'react'
import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-column">
            <Link to="/" className="logo" style={{ marginBottom: '0.5rem' }}>
              <span className="logo-square"></span>
              Bridgr
            </Link>
            <p className="footer-desc">
              Bridgr is a high-performance Layer-2 protocol facilitating instant, zero-fee cross-currency and cross-chain transactions.
            </p>
          </div>

          <div className="footer-column">
            <h4 className="footer-title">Protocol</h4>
            <ul className="footer-links">
              <li><Link to="/bridge" className="footer-link">Bridge Assets</Link></li>
              <li><a href="#features" className="footer-link">Features</a></li>
              <li><a href="#developers" className="footer-link">Developer Hub</a></li>
            </ul>
          </div>

          <div className="footer-column">
            <h4 className="footer-title">Security</h4>
            <ul className="footer-links">
              <li><a href="#validators" className="footer-link">Validator Status</a></li>
              <li><a href="#audits" className="footer-link">Smart Audits</a></li>
              <li><a href="#provability" className="footer-link">ZK-Proofs</a></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} Bridgr Labs. All rights reserved.</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#fff', display: 'inline-block' }}></span>
            <span style={{ fontFamily: 'var(--font-heading)' }}>L2 Validators Online (99.99% uptime)</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
