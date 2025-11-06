import { useState, useEffect } from 'react'
import Portfolio from './components/Portfolio'
import Trades from './components/Trades'
import Charts from './components/Charts'
import Positions from './components/Positions'
import { apiService, handleApiError, PortfolioData, Trade, HealthStatus, Position } from './api'
import { useRealtimePositions } from './hooks/useRealtimePositions'
import { useRealtimeTrades } from './hooks/useRealtimeTrades'
import { Activity, Sparkles } from 'lucide-react'
import { PillBadge } from './components/ui/PillBadge'
import { StatusDot } from './components/ui/StatusDot'

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
      <div className="min-h-screen bg-[#F5F1E8] p-8">
        <div className="mx-auto max-w-[1200px]">
          <header className="mb-8">
            <h1 className="text-4xl font-sans font-semibold text-black">Trade Oracle</h1>
            <p className="text-sm text-gray-warm mt-2">IV Mean Reversion Options Strategy</p>
          </header>
          <div className="text-center text-gray-warm py-16">Loading dashboard...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F5F1E8] p-8">
      <div className="mx-auto max-w-[1200px]">
        {/* Header */}
        <header className="mb-8">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <h1 className="text-3xl lg:text-4xl font-sans font-semibold text-black">Trade Oracle</h1>
              <p className="text-sm text-gray-warm mt-2 flex items-center gap-2">
                IV Mean Reversion Options Strategy
                <PillBadge variant="rose">PAPER TRADING</PillBadge>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 sm:gap-4 md:gap-6">
              {/* Backend Status */}
              <div className="flex items-center gap-2">
                <StatusDot status={getBackendStatus()} />
                <span className="text-sm text-black">
                  Backend: {getBackendStatus() === 'connected' ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* Real-time Status */}
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-teal" />
                <span className="text-sm text-black">{getRealtimeStatus().message}</span>
              </div>

              {/* Last Update */}
              {lastUpdate && (
                <div className="text-xs text-gray-warm">
                  Updated {Math.round((Date.now() - lastUpdate.getTime()) / 1000)}s ago
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="space-y-6">
          {error && (
            <div className="bg-rose/10 border-2 border-rose rounded-2xl p-4 flex items-center justify-between">
              <span className="text-rose font-medium">Error: {error}</span>
              <button
                onClick={fetchData}
                className="bg-rose text-white px-4 py-2 rounded-xl font-medium hover:scale-105 transition-transform"
              >
                Retry
              </button>
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

          {/* System Information */}
          <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles size={20} className="text-amber" />
              <h3 className="text-xl font-sans font-medium text-black">System Information</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-1">
                <span className="text-xs uppercase tracking-wide text-gray-warm">Strategy</span>
                <p className="text-sm font-medium text-black">IV Mean Reversion</p>
              </div>
              <div className="space-y-1">
                <span className="text-xs uppercase tracking-wide text-gray-warm">Trading Mode</span>
                <p className="text-sm font-medium text-black">Paper Trading (No Real Money)</p>
              </div>
              <div className="space-y-1">
                <span className="text-xs uppercase tracking-wide text-gray-warm">Data Source</span>
                <p className="text-sm font-medium text-black">
                  {health?.services.alpaca === 'configured' ? 'Alpaca Markets' : 'Disconnected'}
                </p>
              </div>
              <div className="space-y-1">
                <span className="text-xs uppercase tracking-wide text-gray-warm">Database</span>
                <p className="text-sm font-medium text-black">
                  {health?.services.supabase === 'configured' ? 'Supabase Connected' : 'Disconnected'}
                </p>
              </div>
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-gray-300 text-center space-y-2">
          <p className="text-xs text-gray-warm">
            ⚠️ Warning: This is a trading bot. Always review trades manually before execution.
          </p>
          <p className="text-xs text-gray-warm flex items-center justify-center gap-2">
            <Sparkles size={14} className="text-amber" />
            Free tier services: Railway • Vercel • Supabase • Alpaca Paper Trading
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App
