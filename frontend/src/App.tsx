/**
 * App - Main Router Component
 *
 * Routes:
 * - / : Main Dashboard (IV Mean Reversion + Iron Condor)
 * - /scalper : ScalperPro (0DTE Momentum Scalping)
 * - /auto-trade : Auto-Trade (One-click intelligent trading)
 */

import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ScalperPro from './pages/ScalperPro'
import AutoTrade from './components/AutoTrade'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/scalper" element={<ScalperPro />} />
      <Route path="/auto-trade" element={<AutoTrade />} />
    </Routes>
  )
}

export default App
