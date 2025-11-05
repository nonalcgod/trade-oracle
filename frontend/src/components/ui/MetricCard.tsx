import React from 'react';

export type MetricColor = 'green' | 'red' | 'teal' | 'amber' | 'black' | 'white';

export interface MetricCardProps {
  label: string;
  value: string | number;
  color?: MetricColor;
  icon?: React.ReactNode;
  subtext?: string;
  className?: string;
}

const colorStyles: Record<MetricColor, string> = {
  green: 'text-emerald',
  red: 'text-rose',
  teal: 'text-teal',
  amber: 'text-amber',
  black: 'text-black',
  white: 'text-white',
};

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  color = 'black',
  icon,
  subtext,
  className = ''
}) => {
  return (
    <div className={`flex flex-col ${className}`}>
      <div className="flex items-center gap-2 mb-1">
        {icon && <span className={colorStyles[color]}>{icon}</span>}
        <span className="text-sm text-gray-warm uppercase tracking-wide">
          {label}
        </span>
      </div>
      <div className={`text-xl font-mono font-semibold ${colorStyles[color]}`}>
        {value}
      </div>
      {subtext && (
        <div className="text-xs text-gray-400 mt-1">
          {subtext}
        </div>
      )}
    </div>
  );
};
