import React, { useState, useEffect } from 'react'
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ThreeBackground from './components/ThreeBackground'
import LandingPage from './pages/LandingPage'
import BridgePage from './pages/BridgePage'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  const [token, setToken] = useState(() => {
    return localStorage.getItem('bridgr_token') || null
  })
  const [userEmail, setUserEmail] = useState(() => {
    return localStorage.getItem('bridgr_email') || null
  })
  const [username, setUsername] = useState(() => {
    return localStorage.getItem('bridgr_username') || null
  })
  const [firstName, setFirstName] = useState(() => {
    return localStorage.getItem('bridgr_first_name') || null
  })
  const [preferredCurrency, setPreferredCurrency] = useState(() => {
    return localStorage.getItem('bridgr_pref_currency') || 'USDT'
  })

  const location = useLocation()
  const navigate = useNavigate()

  // Handle successful login or register
  const handleLoginSuccess = (loginData) => {
    const { access_token, user_email, username: uName, first_name, preferred_currency } = loginData
    setToken(access_token)
    setUserEmail(user_email)
    setUsername(uName)
    setFirstName(first_name)
    setPreferredCurrency(preferred_currency)

    localStorage.setItem('bridgr_token', access_token)
    localStorage.setItem('bridgr_email', user_email)
    localStorage.setItem('bridgr_username', uName)
    localStorage.setItem('bridgr_first_name', first_name)
    localStorage.setItem('bridgr_pref_currency', preferred_currency)
  }

  const handleLogout = () => {
    setToken(null)
    setUserEmail(null)
    setUsername(null)
    setFirstName(null)
    setPreferredCurrency('USDT')

    localStorage.removeItem('bridgr_token')
    localStorage.removeItem('bridgr_email')
    localStorage.removeItem('bridgr_username')
    localStorage.removeItem('bridgr_first_name')
    localStorage.removeItem('bridgr_pref_currency')

    navigate('/')
  }

  // Scroll reveal trigger on route change & scroll
  useEffect(() => {
    const handleReveal = () => {
      const reveals = document.querySelectorAll('.reveal')
      const windowHeight = window.innerHeight
      reveals.forEach((el) => {
        const elementTop = el.getBoundingClientRect().top
        const elementVisible = 100 // px offset before revealing
        if (elementTop < windowHeight - elementVisible) {
          el.classList.add('active')
        }
      })
    }

    setTimeout(handleReveal, 100)

    window.addEventListener('scroll', handleReveal)
    return () => window.removeEventListener('scroll', handleReveal)
  }, [location])

  return (
    <div className="app-container">
      {/* 3D Interactive WebGL Background */}
      <ThreeBackground />

      <Navbar userEmail={userEmail} firstName={firstName} username={username} onLogout={handleLogout} />

      <main>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
          <Route 
            path="/bridge" 
            element={
              <BridgePage 
                token={token} 
                userEmail={userEmail} 
                username={username}
                preferredCurrency={preferredCurrency} 
              />
            } 
          />
          <Route 
            path="/chat" 
            element={
              <ChatPage 
                token={token} 
                firstName={firstName} 
                username={username}
              />
            } 
          />
        </Routes>
      </main>

      <Footer />
    </div>
  )
}
