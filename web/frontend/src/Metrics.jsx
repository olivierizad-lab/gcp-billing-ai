import React, { useState, useEffect } from 'react'
import { BarChart3, Code, GitBranch, TrendingUp, FileText, Users, Calendar, Activity } from 'lucide-react'
import './Metrics.css'

const API_BASE_URL = import.meta.env.VITE_API_URL

function Metrics() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [token, setToken] = useState(null)
  const [days, setDays] = useState(30)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [availableDays, setAvailableDays] = useState([])
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    if (!storedToken) {
      setError('Authentication required. Sign in to view metrics.')
      setLoading(false)
    } else {
      setToken(storedToken)
    }
  }, [])

  useEffect(() => {
    if (token) {
      loadMetrics(token)
    }
  }, [days, token])

  const fetchMetricsData = async (authToken = token) => {
    if (!authToken) {
      throw new Error('Authentication required. Sign in to view metrics.')
    }

    const response = await fetch(`${API_BASE_URL}/metrics?days=${days}`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      const detail = body?.detail ? ` ${body.detail}` : ''
      throw new Error(`Failed to load metrics: ${response.status}${detail}`)
    }

    return response.json()
  }

  const applyMetricsData = (data) => {
    if (!data || !data.metrics) {
      throw new Error('Metrics snapshot not available yet. Please try again later.')
    }

    console.log('Loaded metrics snapshot:', data.snapshot_id, data.metrics)
    setMetrics(data.metrics)
      setGeneratedAt(data.generated_at || data.metrics.generated_at || null)
      setAvailableDays(data.available_days || [])
  }

  const loadMetrics = async (authToken = token) => {
    if (!authToken) {
      setError('Authentication required. Sign in to view metrics.')
      setLoading(false)
      return
    }
    try {
      setLoading(true)
      setError(null)
      const data = await fetchMetricsData(authToken)
      applyMetricsData(data)
    } catch (err) {
      setError(err.message)
      console.error('Error loading metrics:', err)
      setMetrics(null)
      setGeneratedAt(null)
      setAvailableDays([])
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    if (!token) {
      setError('Authentication required. Sign in to refresh metrics.')
      return
    }

    try {
      setRefreshing(true)
      setError(null)

      const response = await fetch(`${API_BASE_URL}/metrics/refresh`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        const detail = body?.detail ? ` ${body.detail}` : ''
        throw new Error(`Failed to trigger refresh: ${response.status}${detail}`)
      }

      const previousGeneratedAt = generatedAt
      const startTime = Date.now()
      const timeoutMs = 2 * 60 * 1000
      const pollIntervalMs = 5000

      while (Date.now() - startTime < timeoutMs) {
        await new Promise((resolve) => setTimeout(resolve, pollIntervalMs))
        try {
          const data = await fetchMetricsData(token)
          const snapshotGeneratedAt = data.generated_at || data.metrics?.generated_at
          if (snapshotGeneratedAt && snapshotGeneratedAt !== previousGeneratedAt) {
            applyMetricsData(data)
            return
          }
        } catch (pollError) {
          console.warn('Polling metrics snapshot failed:', pollError)
        }
      }

      console.warn('Metrics refresh timed out waiting for new snapshot')
    } catch (err) {
      setError(err.message)
      console.error('Error refreshing metrics:', err)
    } finally {
      setRefreshing(false)
    }
  }

  if (loading) {
    return (
      <div className="metrics-container">
        <div className="metrics-loading">
          <Activity size={32} className="spinner" />
          <p>Loading metrics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="metrics-container">
        <div className="metrics-error">
          <p>Error loading metrics: {error}</p>
          <button onClick={() => loadMetrics(token)}>Retry</button>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="metrics-container">
        <div className="metrics-error">
          <p>No metrics available</p>
        </div>
      </div>
    )
  }

  const { repository_summary, commit_statistics, lines_of_code, ai_effectiveness } = metrics

  // Calculate commit statistics by author
  const commitsByAuthor = {}
  metrics.commits?.forEach(commit => {
    const author = commit.author || 'Unknown'
    if (!commitsByAuthor[author]) {
      commitsByAuthor[author] = { commits: 0, insertions: 0, deletions: 0 }
    }
    commitsByAuthor[author].commits += 1
    commitsByAuthor[author].insertions += commit.insertions || 0
    commitsByAuthor[author].deletions += commit.deletions || 0
  })

  // Calculate commits by date
  const commitsByDate = {}
  metrics.commits?.forEach(commit => {
    const date = commit.date?.split(' ')[0] || 'Unknown'
    commitsByDate[date] = (commitsByDate[date] || 0) + 1
  })

  return (
    <div className="metrics-container">
      <div className="metrics-header">
        <div className="metrics-title-section">
          <BarChart3 size={32} />
          <div>
            <h1>Code Metrics & Analytics</h1>
            <p>Repository statistics and AI coding effectiveness</p>
          </div>
        </div>
        <div className="metrics-controls">
          <label>
            Analysis Period:
            <select value={days} onChange={(e) => setDays(parseInt(e.target.value))}>
              {[7, 30, 90, 180, 365].map((option) => (
                <option
                  key={option}
                  value={option}
                  disabled={
                    availableDays.length > 0 &&
                    option !== days &&
                    !availableDays.includes(option)
                  }
                >
                  Last {option} days
                </option>
              ))}
            </select>
          </label>
          <button onClick={handleRefresh} className="refresh-button" disabled={refreshing}>
            <Activity size={16} className={refreshing ? 'spinner' : ''} />
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* AI Effectiveness Metrics */}
      <div className="metrics-section">
        <div className="section-header">
          <TrendingUp size={20} />
          <h2>AI Coding Effectiveness</h2>
        </div>
        <div className="metrics-grid">
          <div className="metric-card primary">
            <div className="metric-icon">
              <Activity size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Productivity Score</div>
              <div className="metric-value large">{ai_effectiveness?.productivity_score || 0}</div>
              <div className="metric-description">Based on commits, files, and code volume</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">
              <GitBranch size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Commits per Day</div>
              <div className="metric-value">{ai_effectiveness?.commits_per_day?.toFixed(2) || 0}</div>
              <div className="metric-description">Average over {ai_effectiveness?.days_analyzed || 0} days</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">
              <FileText size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Avg Files per Commit</div>
              <div className="metric-value">{ai_effectiveness?.avg_files_per_commit?.toFixed(1) || 0}</div>
              <div className="metric-description">Average files changed per commit</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">
              <Code size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Avg Changes per Commit</div>
              <div className="metric-value">{ai_effectiveness?.avg_changes_per_commit?.toFixed(0) || 0}</div>
              <div className="metric-description">Lines added/removed per commit</div>
            </div>
          </div>
        </div>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Total Insertions</div>
              <div className="metric-value">{ai_effectiveness?.total_insertions?.toLocaleString() || 0}</div>
              <div className="metric-description">Lines of code added</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Total Deletions</div>
              <div className="metric-value">{ai_effectiveness?.total_deletions?.toLocaleString() || 0}</div>
              <div className="metric-description">Lines of code removed</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Net Lines</div>
              <div className="metric-value">{ai_effectiveness?.net_lines?.toLocaleString() || 0}</div>
              <div className="metric-description">Net change (insertions - deletions)</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-content">
              <div className="metric-label">Total Commits</div>
              <div className="metric-value">{ai_effectiveness?.total_commits || 0}</div>
              <div className="metric-description">Commits in analysis period</div>
            </div>
          </div>
        </div>
      </div>

      {/* Repository Summary */}
      <div className="metrics-section">
        <div className="section-header">
          <GitBranch size={20} />
          <h2>Repository Summary</h2>
        </div>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon">
              <GitBranch size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Total Commits</div>
              <div className="metric-value">{repository_summary?.total_commits?.toLocaleString() || 0}</div>
              <div className="metric-description">All time commits</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">
              <FileText size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Total Files</div>
              <div className="metric-value">{repository_summary?.total_files?.toLocaleString() || 0}</div>
              <div className="metric-description">Files in repository</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">
              <Users size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">Contributors</div>
              <div className="metric-value">{repository_summary?.contributors?.length || 0}</div>
              <div className="metric-description">Active contributors</div>
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-icon">
              <Calendar size={24} />
            </div>
            <div className="metric-content">
              <div className="metric-label">First Commit</div>
              <div className="metric-value small">
                {repository_summary?.first_commit_date 
                  ? new Date(repository_summary.first_commit_date).toLocaleDateString()
                  : 'N/A'}
              </div>
              <div className="metric-description">Repository creation date</div>
            </div>
          </div>
        </div>

        {/* Top Contributors */}
        {repository_summary?.contributors && repository_summary.contributors.length > 0 && (
          <div className="contributors-section">
            <h3>Top Contributors</h3>
            <div className="contributors-list">
              {repository_summary.contributors.slice(0, 10).map((contributor, index) => (
                <div key={index} className="contributor-item">
                  <span className="contributor-rank">#{index + 1}</span>
                  <span className="contributor-name">{contributor.name}</span>
                  <span className="contributor-commits">{contributor.commits} commits</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Lines of Code by Module */}
      <div className="metrics-section">
        <div className="section-header">
          <Code size={20} />
          <h2>Lines of Code by Module</h2>
        </div>
        <div className="loc-summary">
          <div className="loc-summary-card">
            <div className="loc-label">Total Files</div>
            <div className="loc-value">{lines_of_code?.summary?.total_files?.toLocaleString() || 0}</div>
          </div>
          <div className="loc-summary-card">
            <div className="loc-label">Total Lines</div>
            <div className="loc-value">{lines_of_code?.summary?.total_lines?.toLocaleString() || 0}</div>
          </div>
          <div className="loc-summary-card">
            <div className="loc-label">Code Lines</div>
            <div className="loc-value">{lines_of_code?.summary?.code_lines?.toLocaleString() || 0}</div>
          </div>
        </div>
        
        <div className="modules-grid">
          {Object.entries(lines_of_code?.by_module || {}).map(([module, data]) => (
            <div key={module} className="module-card">
              <div className="module-header">
                <h3>{module.charAt(0).toUpperCase() + module.slice(1)}</h3>
              </div>
              <div className="module-stats">
                <div className="module-stat">
                  <span className="stat-label">Files:</span>
                  <span className="stat-value">{data.total_files}</span>
                </div>
                <div className="module-stat">
                  <span className="stat-label">Total Lines:</span>
                  <span className="stat-value">{data.total_lines.toLocaleString()}</span>
                </div>
                <div className="module-stat">
                  <span className="stat-label">Code Lines:</span>
                  <span className="stat-value">{data.code_lines.toLocaleString()}</span>
                </div>
              </div>
              {Object.keys(data.by_language || {}).length > 0 && (
                <div className="module-languages">
                  <h4>By Language:</h4>
                  {Object.entries(data.by_language).map(([lang, langData]) => (
                    <div key={lang} className="language-item">
                      <span className="language-name">{lang}</span>
                      <span className="language-stats">
                        {langData.files} files, {langData.code_lines.toLocaleString()} lines
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Commits */}
      {metrics.commits && metrics.commits.length > 0 && (
        <div className="metrics-section">
          <div className="section-header">
            <GitBranch size={20} />
            <h2>Recent Commits</h2>
          </div>
          <div className="commits-list">
            {metrics.commits.slice(0, 20).map((commit, index) => (
              <div key={index} className="commit-item">
                <div className="commit-header">
                  <span className="commit-hash">{commit.hash}</span>
                  <span className="commit-author">{commit.author}</span>
                  <span className="commit-date">
                    {commit.date ? new Date(commit.date).toLocaleString() : 'N/A'}
                  </span>
                </div>
                <div className="commit-message">{commit.message}</div>
                <div className="commit-stats">
                  <span className="commit-stat">
                    {commit.files_changed} file{commit.files_changed !== 1 ? 's' : ''} changed
                  </span>
                  <span className="commit-stat additions">
                    +{commit.insertions} additions
                  </span>
                  <span className="commit-stat deletions">
                    -{commit.deletions} deletions
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="metrics-footer">
        <p>Metrics generated at: {generatedAt ? new Date(generatedAt).toLocaleString() : 'N/A'}</p>
        <p>Analysis period: Last {metrics.analysis_period_days || days} days</p>
      </div>
    </div>
  )
}

export default Metrics

