import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function BridgePage({ token, userEmail, username, preferredCurrency }) {
  const navigate = useNavigate()

  // Form State
  const sourceChain = 'Bridgr L2'
  const targetChain = 'Bridgr L2'
  const [sourceToken, setSourceToken] = useState(preferredCurrency || 'USDT')
  const [targetToken, setTargetToken] = useState('USDC')
  const [amount, setAmount] = useState('100')
  const [recipient, setRecipient] = useState('')

  // Balance & Rate State
  const [balances, setBalances] = useState([])
  const [estimate, setEstimate] = useState(null)
  const [loadingEstimate, setLoadingEstimate] = useState(false)
  const [errorEstimate, setErrorEstimate] = useState('')

  // Transaction History State
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // Simulation State
  const [isSimulating, setIsSimulating] = useState(false)
  const [simStep, setSimStep] = useState(0) // 0 to 5
  const [simTxId, setSimTxId] = useState('')

  const chains = ['Ethereum', 'Solana', 'Arbitrum', 'Optimism', 'Base', 'Polygon']
  const tokens = ['USDT', 'USDC', 'ETH', 'SOL']

  // Update source token default
  useEffect(() => {
    if (preferredCurrency) {
      setSourceToken(preferredCurrency)
    }
  }, [preferredCurrency])

  // Resolve recipient's preferred currency from backend when username/email is typed
  useEffect(() => {
    const resolveRecipientCurrency = async () => {
      const key = recipient.trim();
      if (!key) {
        setTargetToken('USDC'); // Fallback default
        return;
      }
      try {
        const res = await fetch(`${API_URL}/api/bridge/recipient-currency?recipient=${encodeURIComponent(key)}`);
        if (res.ok) {
          const data = await res.json();
          setTargetToken(data.preferred_currency);
        }
      } catch (err) {
        // Keep current token if typing or not found yet
      }
    };

    const timer = setTimeout(resolveRecipientCurrency, 500);
    return () => clearTimeout(timer);
  }, [recipient]);

  // Fetch balances
  const fetchBalances = async () => {
    if (!token) return
    try {
      const res = await fetch(`${API_URL}/api/bridge/balances`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (res.ok) {
        const data = await res.json()
        setBalances(data)
      }
    } catch (err) {
      console.error('Failed to load wallet balances', err)
    }
  }

  // Fetch transaction history
  const fetchHistory = async () => {
    if (!token) return
    setLoadingHistory(true)
    try {
      const res = await fetch(`${API_URL}/api/bridge/transactions`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (res.ok) {
        const data = await res.json()
        setHistory(data)
      }
    } catch (err) {
      console.error('Failed to load transaction history', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  useEffect(() => {
    fetchBalances()
    fetchHistory()
  }, [token])

  // Update estimate whenever inputs change
  useEffect(() => {
    const fetchEstimate = async () => {
      const numAmount = parseFloat(amount)
      if (isNaN(numAmount) || numAmount <= 0) {
        setEstimate(null)
        setErrorEstimate('')
        return
      }

      setLoadingEstimate(true)
      setErrorEstimate('')
      try {
        const res = await fetch(`${API_URL}/api/bridge/estimate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            source_chain: sourceChain,
            target_chain: targetChain,
            source_token: sourceToken,
            target_token: targetToken,
            amount: numAmount,
          }),
        })

        if (res.ok) {
          const data = await res.json()
          setEstimate(data)
        } else {
          setErrorEstimate('Failed to retrieve exchange rates.')
        }
      } catch (err) {
        console.error(err)
        setErrorEstimate('Could not connect to Bridgr conversion server.')
      } finally {
        setLoadingEstimate(false)
      }
    }

    const timer = setTimeout(fetchEstimate, 400)
    return () => clearTimeout(timer)
  }, [sourceChain, targetChain, sourceToken, targetToken, amount])

  // Handle Send action execution
  const handleBridgeAction = async () => {
    if (!token) {
      navigate('/login')
      return
    }

    if (!estimate) return
    if (!recipient.trim()) {
      setErrorEstimate('Please specify a recipient email or username.')
      return
    }

    setLoadingEstimate(true)
    setErrorEstimate('')
    try {
      // 1. Submit transfer to backend
      const res = await fetch(`${API_URL}/api/bridge/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          source_chain: sourceChain,
          target_chain: targetChain,
          source_token: sourceToken,
          target_token: targetToken,
          amount: parseFloat(amount),
          recipient: recipient.trim()
        })
      })

      if (res.ok) {
        const txData = await res.json()
        
        // 2. Launch visual timeline simulation
        setIsSimulating(true)
        setSimStep(1)
        setSimTxId(txData.tx_hash.slice(0, 14) + '...')

        // Step-by-step state machine simulation
        setTimeout(() => {
          setSimStep(2)
          setTimeout(() => {
            setSimStep(3)
            setTimeout(() => {
              setSimStep(4)
              setTimeout(() => {
                setSimStep(5) // Complete
                fetchBalances() // Reload balances from DB
                fetchHistory() // Reload history list from DB
              }, 1500)
            }, 1500)
          }, 1500)
        }, 1500)

      } else {
        const errData = await res.json()
        setErrorEstimate(errData.detail || 'Transfer submission failed.')
      }
    } catch (err) {
      console.error(err)
      setErrorEstimate('Could not execute transfer on Bridgr engine.')
    } finally {
      setLoadingEstimate(false)
    }
  }

  const resetSimulation = () => {
    setIsSimulating(false)
    setSimStep(0)
    setSimTxId('')
  }

  const formatUsername = (uName) => {
    if (!uName) return ''
    if (uName.length > 20) {
      return `${uName.slice(0, 18)}...`
    }
    return `@${uName}`
  }

  const formatDate = (timestamp) => {
    const d = new Date(timestamp * 1000)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' ' + d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  // Get current user's balance for the selected source token
  const getSelectedSourceBalance = () => {
    const balObj = balances.find(b => b.currency === sourceToken)
    return balObj ? balObj.amount : 0.0
  }

  return (
    <div className="container bridge-page-container">
      {/* Wallet Balance Board Header */}
      {token && balances.length > 0 && (
        <div 
          className="glass-card reveal" 
          style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
            gap: '1.5rem', 
            marginBottom: '2rem', 
            padding: '1.5rem 2.25rem',
            animation: 'fadeIn 0.5s ease-out' 
          }}
        >
          {balances.map(b => (
            <div key={b.currency} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', borderRight: '1px solid var(--border-color)', paddingRight: '1rem', lastChild: { border: 'none' } }}>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {b.currency} Balance
              </span>
              <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: '700', fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
                {b.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="bridge-flex">
        {/* Left Side: Send Panel */}
        <div className="glass-card" style={{ padding: '2.5rem' }}>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontWeight: '600', marginBottom: '1.5rem', fontSize: 'var(--font-size-lg)' }}>
            Send & Swap Terminal
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Box 1: You Send */}
            <div style={{ background: 'rgba(0, 0, 0, 0.2)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="form-label" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>You Send</span>
                {token && (
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Available: {getSelectedSourceBalance().toFixed(4)} {sourceToken}
                  </span>
                )}
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <input
                  type="number"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  min="0.00001"
                  step="any"
                  style={{ fontSize: '1.75rem', fontFamily: 'var(--font-heading)', fontWeight: '600', color: 'var(--text-primary)', width: '60%', outline: 'none' }}
                />
                
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <select className="custom-select" value={sourceToken} onChange={(e) => setSourceToken(e.target.value)} style={{ padding: '0.5rem 2rem 0.5rem 0.75rem', fontSize: 'var(--font-size-sm)' }}>
                    {tokens.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* Spacer to replace flip button */}
            <div style={{ height: '0.5rem' }}></div>

            {/* Box 2: They Receive */}
            <div style={{ background: 'rgba(0, 0, 0, 0.2)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <span className="form-label" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>They Receive (Settles in Preferred Currency)</span>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '1.75rem', fontFamily: 'var(--font-heading)', fontWeight: '600', color: estimate ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                  {loadingEstimate ? '...' : estimate ? estimate.output_amount : '0.00'}
                </div>
                
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  {/* Read-Only Preferred Currency display */}
                  <span className="badge" style={{ padding: '0.5rem 1.05rem', fontSize: 'var(--font-size-sm)', background: 'rgba(255,255,255,0.05)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '8px', minWidth: '70px', textAlign: 'center' }}>
                    {targetToken}
                  </span>
                </div>
              </div>
            </div>

            {/* Recipient Email or Username */}
            <div className="form-group" style={{ marginTop: '0.25rem' }}>
              <label className="form-label">Recipient's Username or Email</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. friend_username or friend@example.com"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                required
              />
            </div>

            {errorEstimate && (
              <div style={{ color: 'white', border: '1px solid rgba(255,0,0,0.2)', background: 'rgba(255,0,0,0.02)', padding: '0.75rem', borderRadius: '8px', fontSize: 'var(--font-size-sm)' }}>
                {errorEstimate}
              </div>
            )}

            {/* Pricing details */}
            {estimate && !loadingEstimate && (
              <div className="estimate-summary" style={{ margin: '0.5rem 0', padding: '0.5rem 0 0 0', borderTop: 'none' }}>
                <div className="estimate-row">
                  <span className="estimate-label">Bridgr Swap Fee</span>
                  <span className="estimate-value">
                    {estimate.l2_fee} {estimate.source_token} (0.05%)
                  </span>
                </div>
                <div className="estimate-row">
                  <span className="estimate-label">Blockchain Fee Savings</span>
                  <span className="estimate-value" style={{ color: '#fff', fontWeight: 'bold' }}>
                    ~${estimate.l1_gas_saved_usd} USD Saved
                  </span>
                </div>
                <div className="estimate-row">
                  <span className="estimate-label">Settlement Speed</span>
                  <span className="estimate-value">Instant L2 Rollup</span>
                </div>
              </div>
            )}

            {/* Action button */}
            <button
              onClick={handleBridgeAction}
              className="btn btn-primary"
              style={{ width: '100%', display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }}
              disabled={!estimate || loadingEstimate || isSimulating}
            >
              {!token
                ? 'Log in to Send Money'
                : isSimulating
                ? 'Clearing Transfer...'
                : 'Send Money'}
            </button>
          </div>
        </div>

        {/* Right Side: Visual Timeline & Receipt or History Ledger */}
        <div className="glass-card" style={{ minHeight: '450px', padding: '2.5rem', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontWeight: '600', marginBottom: '1.25rem', fontSize: 'var(--font-size-md)' }}>
            {isSimulating ? 'Payment Progress Ledger' : 'Activity History'}
          </h3>

          {isSimulating ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                <span className="badge" style={{ fontFamily: 'monospace' }}>{simTxId}</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>Status: {simStep === 5 ? 'Completed' : 'Clearing'}</span>
              </div>

              {/* Steps timeline */}
              <div className="timeline-container" style={{ gap: '1.25rem' }}>
                {/* Step 1 */}
                <div className={`timeline-step ${simStep === 1 ? 'active' : simStep > 1 ? 'completed' : ''}`}>
                  <div className="timeline-icon-wrapper">
                    <div className={`timeline-dot ${simStep === 1 ? 'active' : simStep > 1 ? 'completed' : ''}`}></div>
                    <div className={`timeline-line ${simStep > 1 ? 'completed' : ''}`}></div>
                  </div>
                  <div className="timeline-content">
                    <span className="timeline-step-title">Verifying Account Balance</span>
                    <span className="timeline-step-desc" style={{ fontSize: '11px' }}>
                      Validating secure balance reserves for {amount} {sourceToken}...
                    </span>
                  </div>
                </div>

                {/* Step 2 */}
                <div className={`timeline-step ${simStep === 2 ? 'active' : simStep > 2 ? 'completed' : ''}`}>
                  <div className="timeline-icon-wrapper">
                    <div className={`timeline-dot ${simStep === 2 ? 'active' : simStep > 2 ? 'completed' : ''}`}></div>
                    <div className={`timeline-line ${simStep > 2 ? 'completed' : ''}`}></div>
                  </div>
                  <div className="timeline-content">
                    <span className="timeline-step-title">Routing to Rollup Network</span>
                    <span className="timeline-step-desc" style={{ fontSize: '11px' }}>
                      Routing payment variables through secure Bridgr instant settlement rollup...
                    </span>
                  </div>
                </div>

                {/* Step 3 */}
                <div className={`timeline-step ${simStep === 3 ? 'active' : simStep > 3 ? 'completed' : ''}`}>
                  <div className="timeline-icon-wrapper">
                    <div className={`timeline-dot ${simStep === 3 ? 'active' : simStep > 3 ? 'completed' : ''}`}></div>
                    <div className={`timeline-line ${simStep > 3 ? 'completed' : ''}`}></div>
                  </div>
                  <div className="timeline-content">
                    <span className="timeline-step-title">Exchanging Assets</span>
                    <span className="timeline-step-desc" style={{ fontSize: '11px' }}>
                      Converting {sourceToken} to {estimate?.output_amount} {targetToken}...
                    </span>
                  </div>
                </div>

                {/* Step 4 */}
                <div className={`timeline-step ${simStep === 4 ? 'active' : simStep > 4 ? 'completed' : ''}`}>
                  <div className="timeline-icon-wrapper">
                    <div className={`timeline-dot ${simStep === 4 ? 'active' : simStep > 4 ? 'completed' : ''}`}></div>
                  </div>
                  <div className="timeline-content">
                    <span className="timeline-step-title">Depositing in Recipient Account</span>
                    <span className="timeline-step-desc" style={{ fontSize: '11px' }}>
                      Crediting swapped {targetToken} to recipient {recipient}...
                    </span>
                  </div>
                </div>
              </div>

              {simStep === 5 && (
                <div className="glass-card" style={{ background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.2)', display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem', animation: 'fadeIn 0.5s ease-out' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '1.5rem' }}>✅</span>
                    <div>
                      <h4 style={{ fontFamily: 'var(--font-heading)', fontWeight: '600' }}>Payment Cleared!</h4>
                      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                        Funds deposited to recipient successfully.
                      </p>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', fontSize: 'var(--font-size-sm)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Amount Sent:</span>
                      <span style={{ fontWeight: '500' }}>-{amount} {sourceToken}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Recipient Receives:</span>
                      <span style={{ fontWeight: '500' }}>+{estimate?.output_amount} {targetToken}</span>
                    </div>
                  </div>

                  <button onClick={resetSimulation} className="btn btn-secondary" style={{ width: '100%', padding: '0.5rem 1rem', fontSize: 'var(--font-size-xs)' }}>
                    Make Another Payment
                  </button>
                </div>
              )}
            </div>
          ) : !token ? (
            /* Log in CTA state */
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexGrow: 1, color: 'var(--text-muted)', textAlign: 'center', gap: '1rem' }}>
              <div style={{ fontSize: '3rem' }}>💸</div>
              <p style={{ maxWidth: '300px', fontSize: 'var(--font-size-sm)' }}>
                Please log in to your account to view your transaction history ledger and send payments.
              </p>
            </div>
          ) : history.length === 0 ? (
            /* Empty history state */
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexGrow: 1, color: 'var(--text-muted)', textAlign: 'center', gap: '0.5rem' }}>
              <div style={{ fontSize: '2rem' }}>🗂️</div>
              <p style={{ fontSize: 'var(--font-size-sm)' }}>No transactions yet.</p>
              <p style={{ fontSize: '11px', maxWidth: '200px' }}>Your cross-chain payments will show up here after execution.</p>
            </div>
          ) : (
            /* Real Database History Ledger list */
            <div style={{ overflowY: 'auto', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '0.75rem', paddingRight: '0.25rem', maxHeight: '350px' }}>
              {history.map((tx) => {
                const isOutgoing = tx.sender_username === username
                return (
                  <div key={tx.id} style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: '600', fontFamily: 'var(--font-heading)' }}>
                          {isOutgoing ? `Sent to ${formatUsername(tx.recipient_username)}` : `Received from ${formatUsername(tx.sender_username)}`}
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {isOutgoing 
                          ? `${tx.source_currency} (debit) -> recipient gets ${tx.target_currency}`
                          : `Received swapped ${tx.target_currency} (credit)`
                        }
                      </span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                        {formatDate(tx.timestamp)}
                      </span>
                    </div>

                    <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                      <span 
                        style={{ 
                          fontSize: 'var(--font-size-md)', 
                          fontWeight: '700', 
                          fontFamily: 'var(--font-heading)',
                          color: isOutgoing ? 'var(--text-primary)' : '#4ade80' // Green for incoming credit!
                        }}
                      >
                        {isOutgoing ? `-${tx.source_amount} ${tx.source_currency}` : `+${tx.target_amount} ${tx.target_currency}`}
                      </span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: '500' }}>
                        Settled
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

    </div>
  )
}
