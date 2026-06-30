import React, { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function ChatPage({ token, firstName, username }) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I am your Bridgr AI Assistant. How can I help you today? You can ask me to check your balances, explain transactions, or talk about Bridgr L2.`,
    },
  ])
  const [inputVal, setInputVal] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const messagesEndRef = useRef(null)

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  // If not logged in, render CTA
  if (!token) {
    return (
      <div className="container login-container" style={{ animation: 'fadeIn 0.5s ease-out' }}>
        <div className="glass-card login-card" style={{ padding: '2.5rem', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '1.5rem', alignItems: 'center' }}>
          <div style={{ fontSize: '3rem' }}>💬</div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontWeight: '600' }}>Talk to Bridgr AI</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            Please log in or register to chat with our AI assistant and view your wallet balances.
          </p>
          <button onClick={() => navigate('/login')} className="btn btn-primary" style={{ width: '100%' }}>
            Log In / Sign Up
          </button>
        </div>
      </div>
    )
  }

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading) return

    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setInputVal('')
    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/api/bridge/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          messages: [...messages, userMessage].map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setMessages((prev) => [...prev, { role: 'assistant', content: data.content }])
      } else {
        const errData = await res.json()
        setError(errData.detail || 'The AI service returned an error. Please try again.')
      }
    } catch (err) {
      console.error(err)
      setError('Could not connect to the local Ollama backend service. Verify Ollama is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickAction = (actionText) => {
    handleSendMessage(actionText)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(inputVal)
    }
  }

  return (
    <div className="container" style={{ padding: '5rem 0', animation: 'fadeIn 0.5s ease-out' }}>
      <div className="glass-card" style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', height: '600px', padding: '0', overflow: 'hidden' }}>
        
        {/* Chat Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem 2rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.01)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#4ade80', boxShadow: '0 0 8px #4ade80' }}></div>
            <div>
              <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: 'var(--font-size-md)', fontWeight: '600' }}>Bridgr AI Copilot</h2>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Connected to Ollama Instance</span>
            </div>
          </div>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>@{username}</span>
        </div>

        {/* Message Log */}
        <div style={{ flexGrow: 1, overflowY: 'auto', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {messages.map((msg, index) => {
            const isBot = msg.role === 'assistant'
            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  justifyContent: isBot ? 'flex-start' : 'flex-end',
                  animation: 'fadeIn 0.3s ease-out',
                }}
              >
                <div
                  style={{
                    maxWidth: '75%',
                    padding: '0.85rem 1.25rem',
                    borderRadius: isBot ? '16px 16px 16px 4px' : '16px 16px 4px 16px',
                    background: isBot ? 'rgba(255, 255, 255, 0.03)' : 'var(--accent-white)',
                    color: isBot ? 'var(--text-primary)' : 'var(--bg-primary)',
                    border: isBot ? '1px solid var(--border-color)' : 'none',
                    fontSize: 'var(--font-size-sm)',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap',
                    fontFamily: isBot ? 'var(--font-body)' : 'var(--font-body)',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            )
          })}

          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div
                style={{
                  padding: '0.85rem 1.25rem',
                  borderRadius: '16px 16px 16px 4px',
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontSize: 'var(--font-size-sm)',
                }}
              >
                <span className="typing-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-secondary)', animation: 'pulse 1.4s infinite both 0s' }}></span>
                <span className="typing-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-secondary)', animation: 'pulse 1.4s infinite both 0.2s' }}></span>
                <span className="typing-dot" style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--text-secondary)', animation: 'pulse 1.4s infinite both 0.4s' }}></span>
              </div>
            </div>
          )}

          {error && (
            <div style={{ color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.2)', background: 'rgba(239, 68, 68, 0.02)', padding: '0.75rem 1rem', borderRadius: '8px', fontSize: 'var(--font-size-sm)', textAlign: 'center' }}>
              ⚠️ {error}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick-Prompt suggestions */}
        <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', padding: '0.5rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.03)', background: 'rgba(0,0,0,0.1)' }}>
          <button onClick={() => handleQuickAction('What is my current balance?')} className="badge" style={{ cursor: 'pointer', border: '1px solid var(--border-color)', whiteSpace: 'nowrap', transition: 'all 0.2s' }}>
            💰 Check balances
          </button>
          <button onClick={() => handleQuickAction('Show my recent transactions')} className="badge" style={{ cursor: 'pointer', border: '1px solid var(--border-color)', whiteSpace: 'nowrap', transition: 'all 0.2s' }}>
            🗂️ View transactions
          </button>
          <button onClick={() => handleQuickAction('Explain Bridgr Layer 2 network')} className="badge" style={{ cursor: 'pointer', border: '1px solid var(--border-color)', whiteSpace: 'nowrap', transition: 'all 0.2s' }}>
            ⚡ What is Bridgr L2?
          </button>
        </div>

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: '1rem', padding: '1.25rem 2rem', borderTop: '1px solid var(--border-color)', background: 'rgba(255,255,255,0.01)' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Type your message here..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            style={{ flexGrow: 1, borderRadius: '8px' }}
          />
          <button
            onClick={() => handleSendMessage(inputVal)}
            className="btn btn-primary"
            disabled={loading || !inputVal.trim()}
            style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', minWidth: '100px' }}
          >
            Send
          </button>
        </div>

      </div>

      {/* Typing dots keyframe stylesheet injected inline */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.2; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }
        .badge:hover {
          background: rgba(255,255,255,0.1) !important;
          border-color: var(--border-color-hover) !important;
          transform: translateY(-1px);
        }
      `}</style>
    </div>
  )
}
