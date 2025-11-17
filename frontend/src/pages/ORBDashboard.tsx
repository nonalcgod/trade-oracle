/**
 * ORB Dashboard - Opening Range Breakout Strategy
 *
 * Real-time dashboard for tracking opening ranges and breakout signals.
 * Features:
 * - 60-minute opening range tracking (9:30-10:30am ET)
 * - Breakout signal detection with volume/RSI confirmation
 * - Entry window monitoring (10:30am - 2:00pm ET)
 * - Win rate: 75-89% historically
 */

import { Link } from 'react-router-dom';
import { ArrowLeft, TrendingUp } from 'lucide-react';
import { PillBadge } from '../components/ui/PillBadge';
import { ORBSignals } from '../components/ORBSignals';

const ORBDashboard = () => {
  return (
    <div className="min-h-screen bg-[#F5F1E8]">
      <div className="mx-auto max-w-[1920px] px-6 lg:px-8 py-6">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/"
                className="text-gray-600 hover:text-black transition-colors"
                aria-label="Back to dashboard"
              >
                <ArrowLeft size={24} />
              </Link>
              <div className="flex items-center gap-3">
                <TrendingUp size={32} className="text-teal-500" />
                <h1 className="text-3xl font-sans font-semibold text-black">
                  Opening Range Breakout
                </h1>
                <PillBadge variant="teal">75-89% WIN RATE</PillBadge>
                <PillBadge variant="rose">PAPER TRADING</PillBadge>
              </div>
            </div>
          </div>
        </header>

        {/* Strategy Info Banner */}
        <div className="mb-6 p-6 bg-white rounded-2xl border-2 border-black shadow-md">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-1">Strategy</p>
              <p className="text-lg font-semibold text-black">Opening Range Breakout</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Range Duration</p>
              <p className="text-lg font-semibold text-black">60 minutes (9:30-10:30am ET)</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Entry Window</p>
              <p className="text-lg font-semibold text-black">10:30am - 2:00pm ET</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Daily Target</p>
              <p className="text-lg font-semibold text-emerald-600">$200-400</p>
            </div>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white rounded-xl border-2 border-black shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">📊</span>
              <h3 className="font-semibold text-black">1. Track Opening Range</h3>
            </div>
            <p className="text-sm text-gray-600">
              Monitor the high/low price range during the first 60 minutes of trading (9:30-10:30am ET).
              The range width indicates volatility potential.
            </p>
          </div>

          <div className="p-4 bg-white rounded-xl border-2 border-black shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">🎯</span>
              <h3 className="font-semibold text-black">2. Detect Breakouts</h3>
            </div>
            <p className="text-sm text-gray-600">
              Wait for price to break above/below the range with volume confirmation (≥1.5x average)
              and RSI confirmation. Breakouts indicate directional momentum.
            </p>
          </div>

          <div className="p-4 bg-white rounded-xl border-2 border-black shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl">💰</span>
              <h3 className="font-semibold text-black">3. Execute & Profit</h3>
            </div>
            <p className="text-sm text-gray-600">
              Target: Range width × 1.5 OR 50% option gain. Stop: Price re-enters range (thesis
              invalidation) OR 40% loss. Force close at 3:00pm ET.
            </p>
          </div>
        </div>

        {/* Main ORB Signals Component */}
        <ORBSignals />

        {/* Strategy Performance Stats */}
        <div className="mt-6 p-6 bg-white rounded-2xl border-2 border-black shadow-md">
          <h2 className="text-xl font-semibold text-black mb-4">Historical Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-4 bg-emerald-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Win Rate</p>
              <p className="text-3xl font-mono font-bold text-emerald-600">75-89%</p>
              <p className="text-xs text-gray-500 mt-1">Option Alpha backtest: 89.4%</p>
            </div>
            <div className="p-4 bg-teal-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Avg Hold Time</p>
              <p className="text-3xl font-mono font-bold text-teal-600">30-180 min</p>
              <p className="text-xs text-gray-500 mt-1">Intraday positions only</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Signals/Day</p>
              <p className="text-3xl font-mono font-bold text-blue-600">0.5-1.5</p>
              <p className="text-xs text-gray-500 mt-1">Not every day has breakout</p>
            </div>
            <div className="p-4 bg-amber-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Profit Factor</p>
              <p className="text-3xl font-mono font-bold text-amber-600">1.8-2.2</p>
              <p className="text-xs text-gray-500 mt-1">Wins are 1.8-2.2x larger than losses</p>
            </div>
          </div>
        </div>

        {/* Risk Warnings */}
        <div className="mt-6 p-4 bg-amber-50 border-l-4 border-amber-500 rounded-lg">
          <h3 className="font-semibold text-amber-800 mb-2">⚠️ Risk Warnings</h3>
          <ul className="text-sm text-amber-700 space-y-1">
            <li>
              • <strong>False Breakouts:</strong> If price re-enters opening range, thesis is
              invalidated → immediate exit
            </li>
            <li>
              • <strong>Gap Days Only:</strong> Strategy works best on gap days (0.5-2% pre-market
              gap) with catalyst
            </li>
            <li>
              • <strong>No Late Entries:</strong> Skip signals after 2:00pm ET (insufficient time to
              reach target)
            </li>
            <li>
              • <strong>Range Quality:</strong> Wider ranges (0.5%+) are better than narrow ranges
              (&lt;0.3%)
            </li>
            <li>
              • <strong>Circuit Breakers:</strong> Respects 2% max risk per trade, -3% daily loss
              limit, 3 consecutive loss rule
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ORBDashboard;
