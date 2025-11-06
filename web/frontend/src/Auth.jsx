import React, { useState } from 'react'
import { LogIn, UserPlus, Mail, Lock, AlertCircle, X, User, Trash2 } from 'lucide-react'
import './Auth.css'

// API URL must be set at build time - no default to prevent production errors
const API_BASE_URL = import.meta.env.VITE_API_URL
if (!API_BASE_URL) {
  console.error('VITE_API_URL is not set! The application will not work correctly.')
  throw new Error('VITE_API_URL environment variable is required')
}
const REQUIRED_DOMAIN = 'asl.apps-eval.com' // Internal use only - don't expose to users

function Auth({ user, onAuthChange }) {
  const [mode, setMode] = useState('login') // 'login', 'signup', 'forgot'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showAccountMenu, setShowAccountMenu] = useState(false)

  const validateEmail = (email) => {
    if (!email) return 'Email is required'
    if (!email.includes('@')) return 'Invalid email format'
    const domain = email.split('@')[1]
    if (domain !== REQUIRED_DOMAIN) {
      return 'Please use your ASL class account email address'
    }
    return null
  }

  const validatePassword = (password) => {
    if (!password) return 'Password is required'
    if (password.length < 6) return 'Password must be at least 6 characters'
    return null
  }

  const handleSignup = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Validate email domain
    const emailError = validateEmail(email)
    if (emailError) {
      setError(emailError)
      setLoading(false)
      return
    }

    // Validate password
    const passwordError = validatePassword(password)
    if (passwordError) {
      setError(passwordError)
      setLoading(false)
      return
    }

    // Check password confirmation
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to create account' }))
        setError(errorData.detail || 'Failed to create account')
        setLoading(false)
        return
      }

      const userData = await response.json()
      console.log('User created:', userData)
      
      // Auto-login after signup
      await handleLogin(e, email, password)
    } catch (err) {
      console.error('Signup error:', err)
      setError(err.message || 'Failed to create account')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (e, emailOverride = null, passwordOverride = null) => {
    if (e) e.preventDefault()
    setError('')
    setLoading(true)

    const loginEmail = emailOverride || email
    const loginPassword = passwordOverride || password

    const emailError = validateEmail(loginEmail)
    if (emailError) {
      setError(emailError)
      setLoading(false)
      return
    }

    if (!loginPassword) {
      setError('Password is required')
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginEmail,
          password: loginPassword
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to sign in' }))
        setError(errorData.detail || 'Invalid email or password')
        setLoading(false)
        return
      }

      const tokenData = await response.json()
      console.log('User signed in:', tokenData)
      
      // Store token and user info
      localStorage.setItem('auth_token', tokenData.access_token)
      localStorage.setItem('user_id', tokenData.user_id)
      localStorage.setItem('user_email', tokenData.email)
      
      console.log('Login successful, stored token:', tokenData.access_token.substring(0, 20) + '...')
      
      // Call onAuthChange with user object (App.jsx will handle setting userToken)
      onAuthChange({
        user_id: tokenData.user_id,
        email: tokenData.email
      })
      
      setEmail('')
      setPassword('')
    } catch (err) {
      console.error('Login error:', err)
      setError(err.message || 'Failed to sign in')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      // Clear local storage
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_email')
      
      onAuthChange(null)
      setShowAccountMenu(false)
    } catch (err) {
      console.error('Logout error:', err)
      setError('Failed to sign out')
    }
  }

  const handleDeleteAccount = async () => {
    if (!user) return
    
    if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      return
    }

    if (!confirm('This will permanently delete your account and all your data. Are you absolutely sure?')) {
      return
    }

    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete account' }))
        setError(errorData.detail || 'Failed to delete account')
        setLoading(false)
        return
      }

      // Clear local storage
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_email')
      
      onAuthChange(null)
      setShowAccountMenu(false)
      alert('Account deleted successfully')
    } catch (err) {
      console.error('Delete account error:', err)
      setError('Failed to delete account: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleForgotPassword = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const emailError = validateEmail(email)
    if (emailError) {
      setError(emailError)
      setLoading(false)
      return
    }

    // Password reset not implemented yet - would need email service
    setError('Password reset is not yet implemented. Please contact an administrator.')
    setLoading(false)
    
    // TODO: Implement password reset with email service
    // For now, just show a message
  }

  // If user is logged in, show account menu (without full-screen container)
  if (user) {
    return (
      <div className="account-menu">
        <button 
          className="account-button"
          onClick={() => setShowAccountMenu(!showAccountMenu)}
        >
          <User size={20} />
          <span>{user.email}</span>
        </button>
        {showAccountMenu && (
          <div className="account-dropdown">
            <div className="account-info">
              <div className="account-email">{user.email || user.user_email}</div>
              <div className="account-uid">User ID: {user.user_id ? user.user_id.substring(0, 8) + '...' : 'N/A'}</div>
            </div>
            <div className="account-actions">
              <button 
                className="account-action-button"
                onClick={handleLogout}
                disabled={loading}
              >
                Sign Out
              </button>
              <button 
                className="account-action-button delete-account"
                onClick={handleDeleteAccount}
                disabled={loading}
              >
                <Trash2 size={16} />
                Delete Account
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Show login/signup form
  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>{mode === 'login' ? 'Sign In' : mode === 'signup' ? 'Create Account' : 'Reset Password'}</h2>
          <p className="auth-subtitle">
            {mode === 'login' && 'Sign in to access GCP Billing Agent'}
            {mode === 'signup' && 'Create an account (ASL class account required)'}
            {mode === 'forgot' && 'Enter your email to reset your password'}
          </p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            <span>{error}</span>
            <button onClick={() => setError('')} className="error-close">
              <X size={14} />
            </button>
          </div>
        )}

        <form onSubmit={mode === 'login' ? handleLogin : mode === 'signup' ? handleSignup : handleForgotPassword}>
          <div className="auth-field">
            <Mail size={20} className="field-icon" />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          {mode !== 'forgot' && (
            <div className="auth-field">
              <Lock size={20} className="field-icon" />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>
          )}

          {mode === 'signup' && (
            <div className="auth-field">
              <Lock size={20} className="field-icon" />
              <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>
          )}

          <button 
            type="submit" 
            className="auth-submit-button"
            disabled={loading}
          >
            {loading ? (
              <span className="spinner">Loading...</span>
            ) : (
              <>
                {mode === 'login' && <><LogIn size={18} /> Sign In</>}
                {mode === 'signup' && <><UserPlus size={18} /> Create Account</>}
                {mode === 'forgot' && <><Mail size={18} /> Send Reset Email</>}
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          {mode === 'login' && (
            <>
              <button 
                className="auth-link"
                onClick={() => {
                  setMode('signup')
                  setError('')
                }}
              >
                Don't have an account? Sign up
              </button>
              <button 
                className="auth-link"
                onClick={() => {
                  setMode('forgot')
                  setError('')
                }}
              >
                Forgot password?
              </button>
            </>
          )}
          {mode === 'signup' && (
            <button 
              className="auth-link"
              onClick={() => {
                setMode('login')
                setError('')
              }}
            >
              Already have an account? Sign in
            </button>
          )}
          {mode === 'forgot' && (
            <button 
              className="auth-link"
              onClick={() => {
                setMode('login')
                setError('')
              }}
            >
              Back to sign in
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default Auth

