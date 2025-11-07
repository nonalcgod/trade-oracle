/**
 * App - Main Router Component
 *
 * Routes:
 * - / : Main Dashboard (IV Mean Reversion + Iron Condor)
 * - /scalper : ScalperPro (0DTE Momentum Scalping)
 */

import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ScalperPro from './pages/ScalperPro'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/scalper" element={<ScalperPro />} />
    </Routes>
  )
}

export default App
