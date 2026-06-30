import React from 'react'
import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div>
      {/* Centered Hero Section */}
      <section className="hero-section" style={{ textAlign: 'center', padding: '7rem 0 5rem 0' }}>
        <div className="container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.75rem' }}>
          <span className="badge" style={{ width: 'fit-content' }}>⚡ Instant Multi-Chain Payments</span>
          <h1 className="hero-title" style={{ maxWidth: '800px', margin: '0 auto', fontSize: 'var(--font-size-giant)' }}>
            Send crypto.
            <span>Any chain, instantly.</span>
          </h1>
          <p className="hero-desc" style={{ maxWidth: '580px', margin: '0 auto', fontSize: 'var(--font-size-lg)' }}>
            Bridgr is the easiest way to send and receive crypto across different blockchains with zero hassle and virtually zero network fees. Just like PayPal, but powered by secure blockchain routers.
          </p>
          <div className="hero-buttons" style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
            <Link to="/bridge" className="btn btn-primary">
              Send Money Now
            </Link>
            <Link to="/login" className="btn btn-secondary">
              Create Free Account
            </Link>
          </div>
        </div>
      </section>

      {/* How it Works / 3-Step Guide */}
      <section style={{ padding: '5rem 0', background: 'rgba(255, 255, 255, 0.01)', borderTop: '1px solid var(--border-color)', borderBottom: '1px solid var(--border-color)' }}>
        <div className="container">
          <div className="section-header reveal" style={{ textAlign: 'center', margin: '0 auto 4rem auto' }}>
            <span className="section-tag">Simple Setup</span>
            <h2 className="section-title">Send money in 3 simple steps</h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '500px', margin: '0 auto' }}>
              Bridgr hides the complexity of blockchain technology, letting you transfer assets with a few simple clicks.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>
            <div className="glass-card reveal" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto', fontSize: '1.25rem', fontWeight: 'bold', fontFamily: 'var(--font-heading)' }}>
                1
              </div>
              <h3 className="feature-title">Create Free Account</h3>
              <p className="feature-desc" style={{ fontSize: 'var(--font-size-sm)' }}>
                Sign up securely using your email and password in seconds. No complex Web3 wallet linking required.
              </p>
            </div>

            <div className="glass-card reveal" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto', fontSize: '1.25rem', fontWeight: 'bold', fontFamily: 'var(--font-heading)' }}>
                2
              </div>
              <h3 className="feature-title">Enter Recipient & Amount</h3>
              <p className="feature-desc" style={{ fontSize: 'var(--font-size-sm)' }}>
                Choose the asset (USDT, USDC, ETH, SOL), type the amount, and input your friend's email address or username.
              </p>
            </div>

            <div className="glass-card reveal" style={{ textAlign: 'center', padding: '2rem' }}>
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem auto', fontSize: '1.25rem', fontWeight: 'bold', fontFamily: 'var(--font-heading)' }}>
                3
              </div>
              <h3 className="feature-title">Deliver Instantly</h3>
              <p className="feature-desc" style={{ fontSize: 'var(--font-size-sm)' }}>
                Confirm the transfer. Our network swaps and settles the funds to their account in under 3 seconds.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Value Proposition Features Grid */}
      <section className="features-section" id="features" style={{ padding: '6rem 0' }}>
        <div className="container">
          <div className="section-header reveal" style={{ margin: '0 auto 4rem auto', textAlign: 'center' }}>
            <span className="section-tag">Why Bridgr</span>
            <h2 className="section-title">Zero friction. Natively secure.</h2>
            <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
              Traditional crypto transfers require understanding gas limits, slippage, and complex wallet switching. Bridgr solves all three natively.
            </p>
          </div>

          <div className="features-grid">
            <div className="glass-card reveal">
              <div className="feature-icon">💸</div>
              <h3 className="feature-title">Micro-cent fees</h3>
              <p className="feature-desc">
                By bundling transfers, we bypass high network fees. Pay practically zero gas costs compared to typical L1 network swappers.
              </p>
            </div>

            <div className="glass-card reveal">
              <div className="feature-icon">⚡</div>
              <h3 className="feature-title">Instant clearing</h3>
              <p className="feature-desc">
                No waiting for block confirmations. Your transfers are approved off-chain instantly and settled within seconds.
              </p>
            </div>

            <div className="glass-card reveal">
              <div className="feature-icon">🛡️</div>
              <h3 className="feature-title">Bank-grade safety</h3>
              <p className="feature-desc">
                Funds are fully protected. All transfers undergo secure ledger validations, meaning your crypto is always safe and completely in your control.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
