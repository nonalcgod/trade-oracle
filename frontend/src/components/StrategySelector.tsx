import React from 'react';
import { PillBadge } from './ui/PillBadge';

export type Strategy = 'iv-mean-reversion' | 'iron-condor';

interface StrategySelectorProps {
  selectedStrategy: Strategy;
  onStrategyChange: (strategy: Strategy) => void;
}

export const StrategySelector: React.FC<StrategySelectorProps> = ({
  selectedStrategy,
  onStrategyChange,
}) => {
  return (
    <div className="flex items-center gap-2 mb-6">
      <button
        onClick={() => onStrategyChange('iv-mean-reversion')}
        className="hover:scale-105 transition-transform focus:outline-none focus:ring-2 focus:ring-teal rounded-full"
      >
        <PillBadge variant={selectedStrategy === 'iv-mean-reversion' ? 'teal' : 'cream'}>
          IV Mean Reversion
        </PillBadge>
      </button>
      <button
        onClick={() => onStrategyChange('iron-condor')}
        className="hover:scale-105 transition-transform focus:outline-none focus:ring-2 focus:ring-teal rounded-full"
      >
        <PillBadge variant={selectedStrategy === 'iron-condor' ? 'teal' : 'cream'}>
          0DTE Iron Condor
        </PillBadge>
      </button>
    </div>
  );
};

export default StrategySelector;
