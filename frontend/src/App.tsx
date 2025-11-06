import { useState, useEffect } from 'react'
import Portfolio from './components/Portfolio'
import Trades from './components/Trades'
import Charts from './components/Charts'
import Positions from './components/Positions'
import StrategySelector, { Strategy } from './components/StrategySelector'
import IronCondorEntryWindow from './components/IronCondorEntryWindow'
import IronCondorLegs from './components/IronCondorLegs'
import { apiService, handleApiError, PortfolioData, Trade, HealthStatus, Position, IronCondorBuild } from './api'
import { useRealtimePositions } from './hooks/useRealtimePositions'
import { useRealtimeTrades } from './hooks/useRealtimeTrades'
import { Activity, Sparkles } from 'lucide-react'
import { PillBadge } from './components/ui/PillBadge'
import { StatusDot } from './components/ui/StatusDot'
import { ExecuteTradeButton } from './components/ui/ExecuteTradeButton'

function App() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [initialTrades, setInitialTrades] = useState<Trade[]>([])
  const [initialPositions, setInitialPositions] = useState<Position[]>([])
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // Strategy selection with localStorage persistence
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy>(() => {
    const saved = localStorage.getItem('trade-oracle-strategy')
    return (saved === 'iron-condor' ? 'iron-condor' : 'iv-mean-reversion') as Strategy
  })

  // Iron condor state
  const [ironCondorBuild, setIronCondorBuild] = useState<IronCondorBuild | null>(null)
  const [scoutingSetup, setScoutingSetup] = useState(false)

  // Real-time hooks (will fallback to polling if Supabase not configured)
  const { positions, isConnected: positionsConnected, isRealtimeEnabled: positionsRealtimeEnabled } = useRealtimePositions(initialPositions)
  const { trades, isConnected: tradesConnected, isRealtimeEnabled: tradesRealtimeEnabled } = useRealtimeTrades(initialTrades)

  // Handle strategy change
  const handleStrategyChange = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    localStorage.setItem('trade-oracle-strategy', strategy)
    // Clear iron condor build when switching away
    if (strategy !== 'iron-condor') {
      setIronCondorBuild(null)
    }
  }

  // Scout iron condor setups
  const handleScoutSetups = async () => {
    setScoutingSetup(true)
    try {
      // Generate signal for SPY
      const signal = await apiService.generateIronCondorSignal('SPY')

      // Build iron condor with current SPY price (would normally fetch this)
      const build = await apiService.buildIronCondor(signal, 590) // Example price

      setIronCondorBuild(build)
    } catch (err) {
      const errorMessage = handleApiError(err)
      setError(`Failed to scout iron condor: ${errorMessage}`)
      console.error('Iron Condor Scout Error:', errorMessage)
    } finally {
      setScoutingSetup(false)
    }
  }

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
      <div className="min-h-screen bg-[#F5F1E8]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 md:py-8 lg:py-10">
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
    <div className="min-h-screen bg-[#F5F1E8] flex justify-center">
      <div className="w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-6 md:py-8 lg:py-10">
        {/* Header */}
        <header className="mb-8">
          <div className="flex flex-wrap items-start justify-between gap-4 md:gap-6">
            <div>
              <h1 className="text-3xl lg:text-4xl font-sans font-semibold text-black">Trade Oracle</h1>
              <p className="text-sm text-gray-warm mt-2 flex items-center gap-2">
                {selectedStrategy === 'iron-condor'
                  ? '0DTE Iron Condor Strategy'
                  : 'IV Mean Reversion Options Strategy'}
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
          {/* Strategy Selector */}
          <StrategySelector
            selectedStrategy={selectedStrategy}
            onStrategyChange={handleStrategyChange}
          />

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

              {/* Execute Trade Button */}
              <div className="flex justify-center">
                <div className="w-full max-w-md">
                  <ExecuteTradeButton
                    strategy={selectedStrategy}
                    disabled={!portfolio || getBackendStatus() !== 'connected'}
                    onExecute={fetchData}
                  />
                </div>
              </div>

              {/* Iron Condor Specific Sections */}
              {selectedStrategy === 'iron-condor' && (
                <>
                  <IronCondorEntryWindow onScoutSetups={handleScoutSetups} />

                  {scoutingSetup && (
                    <div className="bg-white rounded-2xl border-2 border-black p-6 text-center shadow-md">
                      <p className="text-sm text-gray-600">Scouting iron condor setups...</p>
                    </div>
                  )}

                  {ironCondorBuild && (
                    <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
                      <h2 className="text-2xl font-sans font-semibold text-black mb-6">
                        Iron Condor Setup
                      </h2>
                      <IronCondorLegs build={ironCondorBuild} />
                    </section>
                  )}
                </>
              )}

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
                <p className="text-sm font-medium text-black">
                  {selectedStrategy === 'iron-condor' ? '0DTE Iron Condor' : 'IV Mean Reversion'}
                </p>
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
