import { useState, useEffect } from 'react'
import './App.css'
import Portfolio from './components/Portfolio'
import Trades from './components/Trades'
import Charts from './components/Charts'
import Positions from './components/Positions'
import { apiService, handleApiError, PortfolioData, Trade, HealthStatus, Position } from './api'
import { useRealtimePositions } from './hooks/useRealtimePositions'
import { useRealtimeTrades } from './hooks/useRealtimeTrades'

function App() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [initialTrades, setInitialTrades] = useState<Trade[]>([])
  const [initialPositions, setInitialPositions] = useState<Position[]>([])
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // Real-time hooks (will fallback to polling if Supabase not configured)
  const { positions, isConnected: positionsConnected, isRealtimeEnabled: positionsRealtimeEnabled } = useRealtimePositions(initialPositions)
  const { trades, isConnected: tradesConnected, isRealtimeEnabled: tradesRealtimeEnabled } = useRealtimeTrades(initialTrades)

  // Fetch data from API
  const fetchData = async () => {
    try {
      setError(null)
      const [portfolioData, tradesData, positionsData, healthData] = await Promise.all([
        apiService.getPortfolio(),
        apiService.getTrades(50),
        apiService.getPositions(),
        apiService.getHealth(),
      ])

      setPortfolio(portfolioData)
      setInitialTrades(tradesData)
      setInitialPositions(positionsData)
      setHealth(healthData)
      setLastUpdate(new Date())
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(errorMessage)
      console.error('API Error:', errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchData()
  }, [])

  // Poll for updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  const getBackendStatus = () => {
    if (!health) return 'disconnected'
    if (health.services.alpaca === 'configured') return 'connected'
    return 'warning'
  }

  const getRealtimeStatus = () => {
    if (!positionsRealtimeEnabled && !tradesRealtimeEnabled) {
      return { status: 'polling', message: 'Polling (5s)' }
    }
    if (positionsConnected && tradesConnected) {
      return { status: 'connected', message: 'Real-time' }
    }
    if (positionsConnected || tradesConnected) {
      return { status: 'partial', message: 'Partial real-time' }
    }
    return { status: 'connecting', message: 'Connecting...' }
  }

  if (loading && !portfolio) {
    return (
      <div className="container">
        <header>
          <h1>Trade Oracle</h1>
          <p className="subtitle">IV Mean Reversion Options Strategy</p>
        </header>
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="container">
      <header>
        <div className="header-content">
          <h1>Trade Oracle</h1>
          <p className="subtitle">IV Mean Reversion Options Strategy • Paper Trading Only</p>
        </div>
        <div className="header-status">
          <div className="status-indicator">
            <span className={`status-dot ${getBackendStatus()}`}></span>
            <span>Backend: {getBackendStatus() === 'connected' ? 'Connected' : 'Disconnected'}</span>
          </div>
          <div className="status-indicator">
            <span className={`status-dot ${getRealtimeStatus().status === 'connected' ? 'connected' : 'warning'}`}></span>
            <span>{getRealtimeStatus().message}</span>
          </div>
          {lastUpdate && (
            <div className="last-update">
              Updated {Math.round((Date.now() - lastUpdate.getTime()) / 1000)}s ago
            </div>
          )}
        </div>
      </header>

      <main>
        {error && (
          <div className="error-banner">
            <span>Error: {error}</span>
            <button onClick={fetchData}>Retry</button>
          </div>
        )}

        {portfolio && (
          <>
            <Portfolio portfolio={portfolio} />
            <Positions positions={positions} loading={loading} />
            <Charts trades={trades} />
            <Trades trades={trades} loading={loading} />
          </>
        )}

        <section className="card system-info">
          <h3>System Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="info-label">Strategy:</span>
              <span className="info-value">IV Mean Reversion</span>
            </div>
            <div className="info-item">
              <span className="info-label">Trading Mode:</span>
              <span className="info-value">Paper Trading (No Real Money)</span>
            </div>
            <div className="info-item">
              <span className="info-label">Data Source:</span>
              <span className="info-value">{health?.services.alpaca === 'configured' ? 'Alpaca Markets' : 'Disconnected'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Database:</span>
              <span className="info-value">{health?.services.supabase === 'configured' ? 'Supabase Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </section>
      </main>

      <footer>
        <p>Warning: This is a trading bot. Always review trades manually before execution.</p>
        <p>Free tier services: Railway • Vercel • Supabase • Alpaca Paper Trading</p>
      </footer>
    </div>
  )
}

export default App

