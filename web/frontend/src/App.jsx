import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Loader2, AlertCircle, History, Trash2, X } from 'lucide-react'
import Auth from './Auth'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [user, setUser] = useState(null)
  const [userToken, setUserToken] = useState(null)
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
  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  // Check for existing auth token on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const userId = localStorage.getItem('user_id')
    const userEmail = localStorage.getItem('user_email')
    
    if (token && userId && userEmail) {
      // Verify token is still valid by checking user info
      fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        if (response.ok) {
          return response.json()
        } else {
          // Token invalid, clear storage
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
          setUser({
            user_id: userData.user_id,
            email: userData.email
          })
          setUserToken(token)
        }
      })
      .catch(err => {
        console.error('Error verifying token:', err)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_id')
        localStorage.removeItem('user_email')
        setUser(null)
        setUserToken(null)
      })
    }
  }, [])

  // Load agents and history when user is authenticated
  useEffect(() => {
    if (user && userToken) {
      loadAgents()
      loadHistory()
    }
  }, [user, userToken])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadAgents = async () => {
    if (!userToken) return
    try {
      const response = await fetch(`${API_BASE_URL}/agents`, {
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      })
      if (!response.ok) {
        if (response.status === 401) {
          setError('Authentication failed. Please sign in again.')
          return
        }
        throw new Error('Failed to load agents')
      }
      const data = await response.json()
      setAgents(data)
      
      // Auto-select first available agent
      const available = data.find(a => a.is_available)
      if (available) {
        setSelectedAgent(available.name)
      }
    } catch (err) {
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

      const response = await fetch(`${API_BASE_URL}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({
          agent_name: selectedAgent,
          message: messageWithContext,
          user_id: user.user_id,
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
    return <Auth user={user} onAuthChange={setUser} />
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
            <Auth user={user} onAuthChange={setUser} />
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
                    {message.content || (message.role === 'assistant' && isLoading ? (
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

