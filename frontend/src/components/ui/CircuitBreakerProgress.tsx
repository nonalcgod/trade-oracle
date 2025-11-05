import React from 'react';

export interface CircuitBreakerProgressProps {
  current: number;
  limit: number;
  label: string;
  isPercentage?: boolean;
  className?: string;
}

export const CircuitBreakerProgress: React.FC<CircuitBreakerProgressProps> = ({
  current,
  limit,
  label,
  isPercentage = true,
  className = ''
}) => {
  // Calculate percentage (handle negative values for losses)
  const percentage = Math.abs((current / limit) * 100);
  const clampedPercentage = Math.min(percentage, 100);

  // Color coding: green < 50%, amber 50-80%, red > 80%
  const getProgressColor = () => {
    if (clampedPercentage < 50) return 'bg-emerald';
    if (clampedPercentage < 80) return 'bg-amber';
    return 'bg-rose';
  };

  const formatValue = (value: number) => {
    if (isPercentage) {
      return `${value.toFixed(1)}%`;
    }
    return value.toString();
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-white">{label}</span>
        <span className="text-sm font-mono text-white">
          {formatValue(current)} / {formatValue(limit)}
        </span>
      </div>

      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${getProgressColor()}`}
          style={{ width: `${clampedPercentage}%` }}
        />
      </div>

      <div className="text-xs text-gray-400 text-right">
        {clampedPercentage.toFixed(0)}% of limit
      </div>
    </div>
  );
};
