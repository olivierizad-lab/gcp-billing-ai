import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2, AlertCircle, History, Trash2, X, HelpCircle, BookOpen, ExternalLink } from 'lucide-react'
import Auth from './Auth'
import './App.css'

// API URL must be set at build time - no default to prevent production errors
const API_BASE_URL = import.meta.env.VITE_API_URL
if (!API_BASE_URL) {
  console.error('VITE_API_URL is not set! The application will not work correctly.')
  throw new Error('VITE_API_URL environment variable is required')
}

// Format message content - detect and format tables with fixed-width columns
function formatMessageContent(content) {
  if (!content) return content
  
  // Split content into lines
  const lines = content.split('\n')
  const formattedLines = []
  let inTable = false
  let tableRows = []
  let columnWidths = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    // Detect table rows (lines with pipes)
    const isTableRow = line.includes('|') && line.trim().startsWith('|') && line.trim().endsWith('|')
    const isSeparator = /^\|[\s\-:]+\|/.test(line.trim())
    
    if (isTableRow || isSeparator) {
      if (!inTable) {
        inTable = true
        tableRows = []
        columnWidths = []
      }
      
      if (!isSeparator) {
        // Extract cells
        const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell.length > 0)
        tableRows.push(cells)
        
        // Update column widths
        cells.forEach((cell, colIndex) => {
          if (!columnWidths[colIndex] || cell.length > columnWidths[colIndex]) {
            columnWidths[colIndex] = cell.length
          }
        })
      }
    } else {
      // Not a table row - process any accumulated table
      if (inTable && tableRows.length > 0) {
        formattedLines.push(formatTable(tableRows, columnWidths))
        tableRows = []
        columnWidths = []
        inTable = false
      }
      formattedLines.push(line)
    }
  }
  
  // Process any remaining table
  if (inTable && tableRows.length > 0) {
    formattedLines.push(formatTable(tableRows, columnWidths))
  }
  
  return formattedLines.join('\n')
}

// Format table with fixed-width columns
function formatTable(rows, columnWidths) {
  if (rows.length === 0) return ''
  
  // Ensure we have column widths for all columns
  const maxCols = Math.max(...rows.map(row => row.length), columnWidths.length)
  
  // Recalculate column widths to ensure all columns are covered
  const finalColumnWidths = []
  for (let i = 0; i < maxCols; i++) {
    const width = rows.reduce((max, row) => {
      const cellLength = (row[i] || '').toString().length
      return Math.max(max, cellLength)
    }, columnWidths[i] || 0)
    finalColumnWidths[i] = Math.max(width, 1) // Minimum width of 1
  }
  
  // Pad each column to its width with proper spacing
  const formattedRows = rows.map(row => {
    const paddedCells = finalColumnWidths.map((width, colIndex) => {
      const cell = (row[colIndex] || '').toString()
      return cell.padEnd(width, ' ')
    })
    return `| ${paddedCells.join(' | ')} |`
  })
  
  // Create separator row with proper dashes
  const separatorParts = finalColumnWidths.map(width => {
    return '-'.repeat(width + 2)
  })
  const separator = `|${separatorParts.join('|')}|`
  
  // Insert separator after header (first row) if we have multiple rows
  if (formattedRows.length > 1) {
    formattedRows.splice(1, 0, separator)
  }
  
  return formattedRows.join('\n')
}

function App() {
  const [user, setUser] = useState(null)
  const [userToken, setUserToken] = useState(null)
  
  // Handle auth changes from Auth component
  const handleAuthChange = (newUser) => {
    if (newUser) {
      // Get token from localStorage (Auth component just stored it)
      const token = localStorage.getItem('auth_token')
      if (token) {
        setUser(newUser)
        setUserToken(token)
        console.log('handleAuthChange: User and token set', { user: newUser, token: token.substring(0, 20) + '...' })
      } else {
        console.error('handleAuthChange: No token found in localStorage')
        setUser(null)
        setUserToken(null)
      }
    } else {
      // User logged out
      setUser(null)
      setUserToken(null)
    }
  }
  
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [sessionId, setSessionId] = useState(null) // Session ID for conversation context
  const [showHelpMenu, setShowHelpMenu] = useState(false)
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  // Documentation URL - defaults to GitHub Pages, can be overridden via environment variable
  const GITBOOK_BASE_URL = import.meta.env.VITE_GITBOOK_URL || 'https://olivierizad-lab.github.io/gcp-billing-ai'
  
  // Documentation links - URLs match GitBook structure from SUMMARY.md
  // GitBook generates URLs from file names (without .md, lowercase, hyphens for spaces/underscores)
  const helpLinks = [
    { title: 'Getting Started', url: `${GITBOOK_BASE_URL}/getting-started/start-here`, icon: BookOpen },
    { title: 'Architecture', url: `${GITBOOK_BASE_URL}/getting-started/architecture`, icon: BookOpen },
    { title: 'Deployment Guide', url: `${GITBOOK_BASE_URL}/deployment/automated-deployment`, icon: BookOpen },
    { title: 'Authentication', url: `${GITBOOK_BASE_URL}/authentication-and-security/authentication-setup`, icon: BookOpen },
    { title: 'API Documentation', url: `${GITBOOK_BASE_URL}/solution-documentation/gen-ai-solution`, icon: BookOpen },
    { title: 'Troubleshooting', url: `${GITBOOK_BASE_URL}/deployment/deployment-faq`, icon: BookOpen },
  ]
  
  // Documentation is always configured (has a default URL), but check if it's explicitly empty
  const isGitBookConfigured = GITBOOK_BASE_URL && GITBOOK_BASE_URL.trim() !== ''

  // Check for existing auth token on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const userId = localStorage.getItem('user_id')
    const userEmail = localStorage.getItem('user_email')
    
    if (token && userId && userEmail) {
      // Verify token is still valid by checking user info
      fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'  // Include credentials for CORS
      })
      .then(response => {
        if (response.ok) {
          return response.json()
        } else {
          // Token invalid or expired, clear storage
          console.log('Token verification failed, clearing storage')
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_id')
          localStorage.removeItem('user_email')
          setUser(null)
          setUserToken(null)
          return null
        }
      })
      .then(userData => {
        if (userData) {
          console.log('Token verified, user authenticated:', userData)
          setUser({
            user_id: userData.user_id,
            email: userData.email
          })
          setUserToken(token)  // Make sure token is set
          console.log('userToken set to:', token.substring(0, 20) + '...')
        }
      })
      .catch(err => {
        console.error('Error verifying token:', err)
        // Don't clear storage on network errors - might be temporary
        // Only clear if it's a 401 (handled above) or if we're sure it's an auth error
        if (err.message && err.message.includes('401')) {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user_id')
          localStorage.removeItem('user_email')
          setUser(null)
          setUserToken(null)
        }
      })
    }
  }, [])

  // Load agents on mount (public endpoint, no auth required)
  useEffect(() => {
    loadAgents()
  }, [])

  // Load history when user is authenticated
  useEffect(() => {
    if (user && userToken) {
      loadHistory()
    }
  }, [user, userToken])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Close help menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showHelpMenu && !event.target.closest('.help-menu-container')) {
        setShowHelpMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showHelpMenu])

  const loadAgents = async () => {
    if (!API_BASE_URL) {
      console.error('loadAgents: API_BASE_URL is not set!')
      setError('API URL is not configured. Please refresh the page.')
      return
    }
    try {
      console.log('loadAgents: Fetching from', `${API_BASE_URL}/agents`)
      // Agents endpoint is public (no auth required)
      const headers = {}
      if (userToken) {
        headers['Authorization'] = `Bearer ${userToken}`
      }
      const response = await fetch(`${API_BASE_URL}/agents`, { headers })
      console.log('loadAgents: Response status', response.status)
      if (!response.ok) {
        const errorText = await response.text()
        console.error('loadAgents: Error response', errorText)
        throw new Error(`Failed to load agents: ${response.status} ${errorText}`)
      }
      const data = await response.json()
      console.log('loadAgents: Received agents', data)
      setAgents(data)
      
      // Auto-select first available agent
      const available = data.find(a => a.is_available)
      if (available) {
        setSelectedAgent(available.name)
      } else if (data.length > 0) {
        console.warn('loadAgents: No available agents found, but agents exist:', data)
      } else {
        console.warn('loadAgents: No agents returned from API')
      }
    } catch (err) {
      console.error('loadAgents: Exception', err)
      setError(`Failed to load agents: ${err.message}`)
    }
  }

  const loadHistory = async () => {
    if (!user || !userToken) return
    setIsLoadingHistory(true)
    try {
      const response = await fetch(`${API_BASE_URL}/history?user_id=${user.user_id}&limit=50`, {
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      })
      if (!response.ok) {
        if (response.status === 401) {
          console.error('Authentication failed')
          return
        }
        throw new Error('Failed to load history')
      }
      const data = await response.json()
      setHistory(data)
    } catch (err) {
      console.error('Failed to load history:', err)
      // Don't show error for history loading failures
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const loadHistoryAsMessages = (historyItem) => {
    // Convert history item to messages format
    const historyMessages = [
      {
        role: 'user',
        content: historyItem.message,
        timestamp: new Date(historyItem.timestamp)
      },
      {
        role: 'assistant',
        content: historyItem.response,
        timestamp: new Date(historyItem.timestamp)
      }
    ]
    setMessages(historyMessages)
    // Keep sessionId - this allows the agent to continue the conversation
    // The agent will have context from the loaded messages
    setShowHistory(false)
    // Scroll to bottom
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 100)
  }

  const deleteHistoryItem = async (queryId, e) => {
    e.stopPropagation() // Prevent loading the history item when clicking delete
    
    if (!user || !userToken) return
    
    if (!confirm('Delete this query from history?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/history/${queryId}?user_id=${user.user_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      })
      if (!response.ok) {
        if (response.status === 401) {
          setError('Authentication failed. Please sign in again.')
          return
        }
        throw new Error('Failed to delete query')
      }
      
      // Remove from local state
      setHistory(prev => prev.filter(item => item.id !== queryId))
      
      // If this was the current conversation, clear it
      // (This is a simple check - in production you might want to track query_id)
    } catch (err) {
      setError(`Failed to delete query: ${err.message}`)
    }
  }

  const deleteAllHistory = async () => {
    if (!user || !userToken) return
    
    if (!confirm('Delete all query history? This cannot be undone.')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/history?user_id=${user.user_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      })
      if (!response.ok) {
        if (response.status === 401) {
          setError('Authentication failed. Please sign in again.')
          return
        }
        throw new Error('Failed to delete history')
      }
      
      setHistory([])
      setMessages([])
    } catch (err) {
      setError(`Failed to delete history: ${err.message}`)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || !selectedAgent || isLoading) return
    
    // Check if we have a valid token
    if (!userToken) {
      console.error('sendMessage: No userToken available')
      setError('Authentication required. Please log in again.')
      return
    }
    
    if (!user || !user.user_id) {
      console.error('sendMessage: No user or user_id available')
      setError('User information missing. Please log in again.')
      return
    }

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setError(null)

    // Create abort controller for this request
    abortControllerRef.current = new AbortController()

    try {
      // Build conversation context from previous messages
      // Include the last few messages to give the agent context
      const conversationContext = messages.slice(-6) // Last 6 messages (3 exchanges)
      const contextMessages = conversationContext.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      
      // Combine context with the new message
      const messageWithContext = contextMessages.length > 0
        ? `${contextMessages.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`).join('\n\n')}\n\nUser: ${userMessage.content}`
        : userMessage.content

      console.log('sendMessage: Sending query with token:', userToken.substring(0, 20) + '...')
      const response = await fetch(`${API_BASE_URL}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({
          agent_name: selectedAgent,
          message: messageWithContext,
          // Note: user_id is not sent - backend uses authenticated user's ID from token
          session_id: getSessionId() // Include session ID for conversation context
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = `HTTP ${response.status}`
        try {
          const errorText = await response.text()
          if (errorText) {
            try {
              const errorData = JSON.parse(errorText)
              errorMessage = errorData.detail || errorData.error || errorText.substring(0, 200)
            } catch {
              errorMessage = errorText.substring(0, 200)
            }
          }
        } catch {
          // If we can't read the error, use the status code
          errorMessage = `HTTP ${response.status}`
        }
        throw new Error(errorMessage)
      }

      // Add assistant message placeholder
      const assistantMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMessage])

      // Read stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              // Handle error messages from backend
              if (data.error) {
                setError(`Query failed: ${data.error}`)
                setMessages(prev => {
                  const newMessages = [...prev]
                  const lastMessage = newMessages[newMessages.length - 1]
                  if (lastMessage.role === 'assistant') {
                    lastMessage.content = `Error: ${data.error}`
                  }
                  return newMessages
                })
                break
              }
              
              // Handle warning messages (non-fatal)
              if (data.warning) {
                console.warn('Warning from backend:', data.warning)
              }
              
              // Handle save errors (non-fatal)
              if (data.save_error) {
                console.warn('Failed to save query to history:', data.save_error)
              }
              
              if (data.text) {
                setMessages(prev => {
                  const newMessages = [...prev]
                  const lastMessage = newMessages[newMessages.length - 1]
                  if (lastMessage.role === 'assistant') {
                    lastMessage.content += data.text
                  }
                  return newMessages
                })
              }

              if (data.done) {
                // Only reload history if there was no error
                if (!data.error) {
                  setTimeout(() => {
                    loadHistory()
                  }, 500) // Small delay to ensure Firestore write completes
                }
                break
              }
            
              // Track query_id if received
              if (data.query_id) {
                console.log('Query saved with ID:', data.query_id)
              }
            } catch (err) {
              console.error('Error parsing SSE data:', err, 'Line:', line)
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        // Request was cancelled, remove the assistant message
        setMessages(prev => prev.slice(0, -1))
        return
      }
      
      setError(`Error: ${err.message}`)
      // Remove assistant message on error
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
    setSessionId(null) // Reset session when clearing chat
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsLoading(false)
  }
  
  // Generate session ID if not exists
  const getSessionId = () => {
    if (!sessionId) {
      // Generate a new session ID for this conversation
      const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      setSessionId(newSessionId)
      return newSessionId
    }
    return sessionId
  }

  const selectedAgentInfo = agents.find(a => a.name === selectedAgent)

  // Show auth screen if not logged in
  if (!user) {
    return <Auth user={user} onAuthChange={handleAuthChange} />
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <Bot className="header-icon" />
            <h1>GCP Billing Agent</h1>
            <span className="header-subtitle">Agent Engine Chat</span>
          </div>
          <div className="header-right">
            {/* Help Menu */}
            <div className="help-menu-container">
              <button 
                className="help-button"
                onClick={() => setShowHelpMenu(!showHelpMenu)}
                title="Help & Documentation"
              >
                <HelpCircle size={20} />
                <span>Help</span>
              </button>
              {showHelpMenu && (
                <div className="help-dropdown">
                  <div className="help-dropdown-header">
                    <BookOpen size={16} />
                    <span>Documentation</span>
                  </div>
                  <div className="help-dropdown-links">
                    {helpLinks.map((link, index) => (
                      <a
                        key={index}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="help-link"
                        onClick={() => setShowHelpMenu(false)}
                      >
                        <link.icon size={16} />
                        <span>{link.title}</span>
                        <ExternalLink size={14} className="external-link-icon" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <Auth user={user} onAuthChange={handleAuthChange} />
            <select
              className="agent-selector"
              value={selectedAgent || ''}
              onChange={(e) => {
                setSelectedAgent(e.target.value)
                clearChat()
              }}
              disabled={isLoading}
            >
              <option value="">Select an agent...</option>
              {agents.map(agent => (
                <option key={agent.name} value={agent.name} disabled={!agent.is_available}>
                  {agent.display_name} {!agent.is_available && '(Not configured)'}
                </option>
              ))}
            </select>
            <button 
              className="history-button" 
              onClick={() => setShowHistory(!showHistory)}
              title="View query history"
            >
              <History size={20} />
            </button>
            {messages.length > 0 && (
              <button className="clear-button" onClick={clearChat} disabled={isLoading}>
                Clear
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={16} />
          <span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* History Sidebar */}
      {showHistory && (
        <div className="history-sidebar">
          <div className="history-header">
            <h3>Query History</h3>
            <div className="history-actions">
              {history.length > 0 && (
                <button 
                  className="delete-all-button" 
                  onClick={deleteAllHistory}
                  title="Delete all history"
                >
                  <Trash2 size={16} />
                </button>
              )}
              <button 
                className="close-history-button" 
                onClick={() => setShowHistory(false)}
                title="Close history"
              >
                <X size={16} />
              </button>
            </div>
          </div>
          <div className="history-content">
            {isLoadingHistory ? (
              <div className="history-loading">
                <Loader2 size={20} className="spinner" />
                <span>Loading history...</span>
              </div>
            ) : history.length === 0 ? (
              <div className="history-empty">
                <p>No query history yet.</p>
                <p className="history-empty-subtitle">Your queries will appear here after you send them.</p>
              </div>
            ) : (
              <div className="history-list">
                {history.map((item) => (
                  <div 
                    key={item.id} 
                    className="history-item"
                    onClick={() => loadHistoryAsMessages(item)}
                  >
                    <div className="history-item-header">
                      <span className="history-agent">{item.agent_name}</span>
                      <button
                        className="history-delete-button"
                        onClick={(e) => deleteHistoryItem(item.id, e)}
                        title="Delete this query"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                    <div className="history-message">{item.message}</div>
                    <div className="history-timestamp">
                      {new Date(item.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className={`messages-container ${showHistory ? 'with-history' : ''}`}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <Bot size={48} className="empty-icon" />
            <h2>Welcome to GCP Billing Agent</h2>
            <p>Select an agent and start chatting!</p>
            {selectedAgentInfo && (
              <p className="agent-description">{selectedAgentInfo.description}</p>
            )}
          </div>
        ) : (
          <div className="messages">
            {messages.map((message, index) => (
              <div key={index} className={`message message-${message.role}`}>
                <div className="message-avatar">
                  {message.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {formatMessageContent(message.content) || (message.role === 'assistant' && isLoading ? (
                      <Loader2 size={16} className="spinner" />
                    ) : '')}
                  </div>
                  <div className="message-timestamp">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
              <div className="message message-assistant">
                <div className="message-avatar">
                  <Bot size={20} />
                </div>
                <div className="message-content">
                  <Loader2 size={16} className="spinner" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-container">
        <form onSubmit={sendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={selectedAgent ? `Message ${selectedAgentInfo?.display_name || selectedAgent}...` : "Select an agent first..."}
            disabled={!selectedAgent || isLoading}
            className="input-field"
          />
          <button
            type="submit"
            disabled={!input.trim() || !selectedAgent || isLoading}
            className="send-button"
          >
            {isLoading ? <Loader2 size={20} className="spinner" /> : <Send size={20} />}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App

