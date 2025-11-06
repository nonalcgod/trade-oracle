import { Position } from '../api';
import { PillBadge } from './ui/PillBadge';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface PositionsProps {
  positions: Position[];
  loading: boolean;
}

function Positions({ positions, loading }: PositionsProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  if (loading) {
    return (
      <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
        <h2 className="text-2xl font-sans font-semibold text-black mb-4">Active Positions</h2>
        <div className="text-center text-gray-warm py-8">Loading positions...</div>
      </section>
    );
  }

  if (positions.length === 0) {
    return (
      <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
        <h2 className="text-2xl font-sans font-semibold text-black mb-4">Active Positions</h2>
        <div className="text-center text-gray-warm py-8">
          <p className="mb-2">No open positions</p>
          <p className="text-sm">
            The monitor will automatically open positions when IV signals are detected
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="bg-white rounded-2xl border-2 border-black p-8 shadow-md">
      <h2 className="text-2xl font-sans font-semibold text-black mb-6">
        Active Positions ({positions.length})
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5 lg:gap-6">
        {positions.map((position) => {
          const pnlPercent = position.entry_price
            ? ((position.current_price - position.entry_price) / position.entry_price) * 100
            : 0;
          const isProfitable = pnlPercent > 0;

          // Calculate progress toward exit conditions
          const profitProgress = Math.min((pnlPercent / 50) * 100, 100); // 50% profit target
          const lossProgress = Math.min((Math.abs(pnlPercent) / 75) * 100, 100); // 75% stop loss

          // Calculate days to expiration (simplified)
          const daysToExp = position.symbol ? parseInt(position.symbol.substring(8, 10)) || 45 : 45;
          const dteProgress = ((45 - daysToExp) / (45 - 21)) * 100; // From 45 DTE to 21 DTE

          // Check if this is an iron condor (multi-leg position)
          // In the future, this will check for position.legs && position.legs.length === 4
          const isIronCondor = false; // Placeholder

          return (
            <div key={position.id} className="bg-white border-2 border-black rounded-2xl p-6 shadow-md transition-all hover:shadow-lg">
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-mono text-black mb-2 truncate">{position.symbol}</h3>
                  <div className="flex items-center gap-2">
                    <PillBadge variant="cream">{position.strategy}</PillBadge>
                    {isIronCondor && <PillBadge variant="teal">Iron Condor</PillBadge>}
                    <PillBadge variant={position.position_type === 'long' ? 'emerald' : 'rose'}>
                      {position.position_type.toUpperCase()}
                    </PillBadge>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`flex items-center gap-1 text-xl font-mono font-bold ${
                    isProfitable ? 'text-emerald' : 'text-rose'
                  }`}>
                    {isProfitable ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                    {formatCurrency(position.unrealized_pnl)}
                  </div>
                  <div className={`text-sm font-mono ${isProfitable ? 'text-emerald' : 'text-rose'}`}>
                    {pnlPercent > 0 ? '+' : ''}{pnlPercent.toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Position Details */}
              <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                <div className="space-y-1">
                  <span className="text-gray-warm">Quantity:</span>
                  <p className="font-mono text-black">{position.quantity} contracts</p>
                </div>
                <div className="space-y-1">
                  <span className="text-gray-warm">Entry:</span>
                  <p className="font-mono text-black">{formatCurrency(position.entry_price)}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-gray-warm">Current:</span>
                  <p className="font-mono text-black">{formatCurrency(position.current_price)}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-gray-warm">Opened:</span>
                  <p className="text-xs text-black">
                    {new Date(position.opened_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Exit Conditions */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-black">Exit Conditions</h4>

                {/* Profit Target */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-warm truncate">💰 Profit (50%)</span>
                    <span className={`font-mono ${profitProgress >= 100 ? 'text-emerald font-bold' : 'text-black'}`}>
                      {pnlPercent > 0 ? `${pnlPercent.toFixed(1)}%` : '0%'} / 50%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(profitProgress, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Stop Loss */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-warm truncate">🛑 Stop (75%)</span>
                    <span className={`font-mono ${lossProgress >= 100 ? 'text-rose font-bold' : 'text-black'}`}>
                      {pnlPercent < 0 ? `${Math.abs(pnlPercent).toFixed(1)}%` : '0%'} / 75%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-rose rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(lossProgress, 100)}%` }}
                    />
                  </div>
                </div>

                {/* DTE Threshold */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-warm truncate">⏰ DTE (21d)</span>
                    <span className={`font-mono ${dteProgress >= 100 ? 'text-amber font-bold' : 'text-black'}`}>
                      {daysToExp} DTE
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(Math.max(dteProgress, 0), 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="mt-4 pt-3 border-t border-gray-200 text-xs text-gray-warm text-center">
                🔄 Monitored every 60 seconds
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default Positions;
