import React from 'react';
import { ArrowLeft, Sparkles, CheckCircle, XCircle } from 'lucide-react';
import { CircuitBreakerProgress } from '../components/ui';
import type { ServiceStatus, CircuitBreakers } from '../types/trading';

export interface SystemStatusScreenProps {
  services: ServiceStatus;
  circuitBreakers: CircuitBreakers;
  onBack?: () => void;
}

interface ServiceItemProps {
  name: string;
  isConnected: boolean;
}

const ServiceItem: React.FC<ServiceItemProps> = ({ name, isConnected }) => {
  return (
    <div className="flex items-center justify-between py-3">
      <span className="text-base font-medium text-black">
        {name}
      </span>
      {isConnected ? (
        <CheckCircle className="w-5 h-5 text-teal" />
      ) : (
        <XCircle className="w-5 h-5 text-rose" />
      )}
    </div>
  );
};

export const SystemStatusScreen: React.FC<SystemStatusScreenProps> = ({
  services,
  circuitBreakers,
  onBack
}) => {
  return (
    <div className="min-h-screen bg-cream px-6 py-8 max-w-md mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-black hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="font-medium">System Status</span>
        </button>
        <Sparkles className="w-5 h-5 text-black" />
      </div>

      {/* Service Status Card */}
      <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold text-black mb-4">
          Service Health
        </h3>
        <div className="divide-y divide-gray-100">
          <ServiceItem
            name="Backend API"
            isConnected={services.backendApi}
          />
          <ServiceItem
            name="Alpaca Markets"
            isConnected={services.alpacaMarkets}
          />
          <ServiceItem
            name="Supabase Database"
            isConnected={services.supabaseDatabase}
          />
        </div>
      </div>

      {/* Circuit Breakers Card */}
      <div className="bg-black border-2 border-rose rounded-2xl shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold text-white mb-6">
          Circuit Breakers
        </h3>

        {/* Daily Loss Limit */}
        <div className="mb-6">
          <CircuitBreakerProgress
            current={Math.abs(circuitBreakers.dailyLossPercent)}
            limit={Math.abs(circuitBreakers.dailyLossLimit)}
            label="Daily Loss Limit"
            isPercentage={true}
          />
        </div>

        {/* Consecutive Losses */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-medium text-white">
              Consecutive Losses
            </span>
            <span className="text-sm font-mono text-white">
              {circuitBreakers.consecutiveLosses} / {circuitBreakers.consecutiveLossLimit}
            </span>
          </div>

          <div className="flex gap-3">
            {[1, 2, 3].map((num) => {
              const isActive = num <= circuitBreakers.consecutiveLosses;
              const isCritical = num === circuitBreakers.consecutiveLossLimit;

              let variant: 'teal' | 'amber' | 'rose' = 'teal';
              if (isActive) {
                if (num >= circuitBreakers.consecutiveLossLimit) {
                  variant = 'rose';
                } else if (num >= circuitBreakers.consecutiveLossLimit - 1) {
                  variant = 'amber';
                }
              }

              return (
                <div
                  key={num}
                  className={`
                    flex-1 h-12 rounded-lg flex items-center justify-center
                    font-mono font-semibold text-lg
                    ${isActive
                      ? variant === 'rose' ? 'bg-rose text-white' :
                        variant === 'amber' ? 'bg-amber text-white' :
                        'bg-teal text-white'
                      : 'bg-gray-700 text-gray-400'
                    }
                    ${isCritical ? 'border-2 border-rose' : ''}
                  `}
                >
                  {num}
                </div>
              );
            })}
          </div>
        </div>

        {/* Max Risk Per Trade */}
        <div className="pt-6 border-t border-gray-700">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-white">
              Max Risk Per Trade
            </span>
            <span className="text-lg font-mono font-semibold text-white">
              {circuitBreakers.maxRiskPerTrade.toFixed(1)}%
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Fixed risk limit per position
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 text-sm text-gray-warm mb-2">
          <Sparkles className="w-4 h-4" />
          <span>Free Tier Services:</span>
        </div>
        <p className="text-xs text-gray-500">
          Railway • Vercel • Supabase
        </p>
        <p className="text-xs text-gray-500">
          Alpaca Paper Trading
        </p>
      </div>
    </div>
  );
};
