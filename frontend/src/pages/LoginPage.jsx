import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function LoginPage({ onLoginSuccess }) {
  const [mode, setMode] = useState('login') // 'login' or 'signup'
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [username, setUsername] = useState('')
  const [preferredCurrency, setPreferredCurrency] = useState('USDT')
  const [loginInput, setLoginInput] = useState('') // Username or Email Address for log in
  const [emailInput, setEmailInput] = useState('') // Email for sign up
  const [passwordInput, setPasswordInput] = useState('')
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const payloadLoginInput = mode === 'login' ? loginInput.trim() : emailInput.trim()
    if (!payloadLoginInput || !passwordInput.trim()) {
      setError('Please fill in all credentials.')
      return
    }

    if (mode === 'signup') {
      if (!firstName.trim() || !lastName.trim() || !username.trim()) {
        setError('Please fill in your first name, last name, and username.')
        return
      }
      if (username.trim().includes(' ')) {
        setError('Username cannot contain spaces.')
        return
      }
    }

    setLoading(true)

    try {
      if (mode === 'signup') {
        // 1. Trigger signup POST request
        const signupRes = await fetch(`${API_URL}/api/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: emailInput.trim(),
            username: username.trim(),
            password: passwordInput,
            first_name: firstName.trim(),
            last_name: lastName.trim(),
            preferred_currency: preferredCurrency
          }),
        })

        if (!signupRes.ok) {
          const errData = await signupRes.json()
          setError(errData.detail || 'Sign up failed. Please try again.')
          setLoading(false)
          return
        }
      }

      // 2. Trigger login POST request
      const loginPayload = {
        username_or_email: mode === 'login' ? loginInput.trim() : emailInput.trim(),
        password: passwordInput
      }

      const loginRes = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginPayload),
      })

      if (loginRes.ok) {
        const data = await loginRes.json()
        onLoginSuccess(data) // Pass the full token payload
        navigate('/bridge')
      } else {
        const errData = await loginRes.json()
        setError(errData.detail || 'Authentication failed. Please verify credentials.')
      }
    } catch (err) {
      console.error(err)
      setError('Could not connect to Bridgr Authentication server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container login-container">
      <div className="glass-card login-card" style={{ padding: '2.5rem' }}>
        <div className="login-logo">
          <span className="logo-square"></span>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: '700', fontSize: 'var(--font-size-md)' }}>BRIDGR</span>
        </div>

        <div>
          <h2 className="login-title">
            {mode === 'login' ? 'Log in to your account' : 'Create your account'}
          </h2>
          <p className="login-desc" style={{ marginTop: '0.4rem' }}>
            {mode === 'login' 
              ? 'Enter your credentials to access your Bridgr balance.' 
              : 'Sign up in seconds to start sending cross-chain crypto.'}
          </p>
        </div>

        {/* Tab Toggle */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', margin: '0 -0.5rem' }}>
          <button
            onClick={() => { setMode('login'); setError('') }}
            style={{
              flex: 1,
              padding: '0.75rem 0',
              fontFamily: 'var(--font-heading)',
              fontSize: 'var(--font-size-sm)',
              borderBottom: mode === 'login' ? '2px solid var(--accent-white)' : '2px solid transparent',
              color: mode === 'login' ? 'var(--text-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: mode === 'login' ? '600' : '400',
              transition: 'all 0.2s'
            }}
          >
            Log In
          </button>
          <button
            onClick={() => { setMode('signup'); setError('') }}
            style={{
              flex: 1,
              padding: '0.75rem 0',
              fontFamily: 'var(--font-heading)',
              fontSize: 'var(--font-size-sm)',
              borderBottom: mode === 'signup' ? '2px solid var(--accent-white)' : '2px solid transparent',
              color: mode === 'signup' ? 'var(--text-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: mode === 'signup' ? '600' : '400',
              transition: 'all 0.2s'
            }}
          >
            Sign Up
          </button>
        </div>

        {error && (
          <div style={{ padding: '0.75rem 1rem', border: '1px solid rgba(255, 0, 0, 0.2)', background: 'rgba(255,0,0,0.02)', color: 'white', borderRadius: '8px', fontSize: 'var(--font-size-sm)', textAlign: 'left' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
          {mode === 'signup' && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group" style={{ textAlign: 'left' }}>
                  <label className="form-label">First Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="John"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    disabled={loading}
                    required
                  />
                </div>
                <div className="form-group" style={{ textAlign: 'left' }}>
                  <label className="form-label">Last Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Doe"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    disabled={loading}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1rem' }}>
                <div className="form-group" style={{ textAlign: 'left' }}>
                  <label className="form-label">Username</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="johndoe12"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                    required
                  />
                </div>
                <div className="form-group" style={{ textAlign: 'left' }}>
                  <label className="form-label">Pref. Currency</label>
                  <select 
                    className="custom-select" 
                    value={preferredCurrency} 
                    onChange={(e) => setPreferredCurrency(e.target.value)}
                    disabled={loading}
                    style={{ background: 'rgba(0, 0, 0, 0.4)' }}
                  >
                    <option value="USDT">USDT</option>
                    <option value="USDC">USDC</option>
                    <option value="ETH">ETH</option>
                    <option value="SOL">SOL</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {mode === 'login' ? (
            <div className="form-group" style={{ textAlign: 'left' }}>
              <label className="form-label">Username or Email Address</label>
              <input
                type="text"
                className="form-input"
                placeholder="Username or email"
                value={loginInput}
                onChange={(e) => setLoginInput(e.target.value)}
                disabled={loading}
                required
              />
            </div>
          ) : (
            <div className="form-group" style={{ textAlign: 'left' }}>
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                placeholder="name@example.com"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                disabled={loading}
                required
              />
            </div>
          )}

          <div className="form-group" style={{ textAlign: 'left' }}>
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }} disabled={loading}>
            {loading ? 'Processing...' : mode === 'login' ? 'Log In' : 'Create Free Account'}
          </button>
        </form>
      </div>
    </div>
  )
}
