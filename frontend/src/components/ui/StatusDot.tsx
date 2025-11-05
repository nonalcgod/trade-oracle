import React from 'react';

export type StatusType = 'connected' | 'disconnected' | 'warning';

export interface StatusDotProps {
  status: StatusType;
  label?: string;
  showPulse?: boolean;
  className?: string;
}

const statusColors: Record<StatusType, string> = {
  connected: 'bg-emerald',
  disconnected: 'bg-rose',
  warning: 'bg-amber',
};

export const StatusDot: React.FC<StatusDotProps> = ({
  status,
  label,
  showPulse = true,
  className = ''
}) => {
  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <div className="relative">
        <div
          className={`
            w-2 h-2 rounded-full
            ${statusColors[status]}
            ${showPulse && status === 'connected' ? 'pulse-dot' : ''}
          `}
        />
        {showPulse && status === 'connected' && (
          <div
            className={`
              absolute inset-0 w-2 h-2 rounded-full
              ${statusColors[status]}
              opacity-75 animate-ping
            `}
          />
        )}
      </div>
      {label && (
        <span className="text-sm font-medium text-gray-warm">
          {label}
        </span>
      )}
    </div>
  );
};
