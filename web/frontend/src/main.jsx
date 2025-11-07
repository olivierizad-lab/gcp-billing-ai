import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import Metrics from './Metrics.jsx'
import './index.css'

const isMetricsRoute = window.location.pathname.startsWith('/metrics')

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isMetricsRoute ? <Metrics /> : <App />}
  </React.StrictMode>,
)

