import React from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'

export default function Navbar({ userEmail, firstName, username, onLogout }) {
  const navigate = useNavigate()

  return (
    <nav className="navbar">
      <div className="container nav-flex">
        <Link to="/" className="logo">
          <span className="logo-square"></span>
          Bridgr
        </Link>

        <ul className="nav-links">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              Home
            </NavLink>
          </li>
          <li>
            <NavLink to="/bridge" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              Send Money
            </NavLink>
          </li>
          <li>
            <NavLink to="/chat" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              AI Chatbot
            </NavLink>
          </li>
        </ul>

        <div>
          {userEmail ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-primary)', fontFamily: 'var(--font-heading)', fontWeight: '500' }}>
                Hi, {firstName || 'User'} <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-size-xs)' }}>@{username}</span>
              </span>
              <button onClick={onLogout} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: 'var(--font-size-xs)' }}>
                Log Out
              </button>
            </div>
          ) : (
            <button onClick={() => navigate('/login')} className="btn btn-primary" style={{ padding: '0.5rem 1rem', fontSize: 'var(--font-size-sm)' }}>
              Log In / Sign Up
            </button>
          )}
        </div>
      </div>
    </nav>
  )
}
