import React, { useState } from 'react';
import { DashboardScreen, TradeHistoryScreen, SystemStatusScreen } from '../screens';
import { mockPortfolio, mockTrades, mockCircuitBreakers, mockServices } from '../data/mockData';

type Screen = 'dashboard' | 'trades' | 'status';

export const UIDemo: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState<Screen>('dashboard');

  const renderScreen = () => {
    switch (currentScreen) {
      case 'dashboard':
        return (
          <DashboardScreen
            portfolio={mockPortfolio}
            onViewTrades={() => setCurrentScreen('trades')}
          />
        );
      case 'trades':
        return (
          <TradeHistoryScreen
            trades={mockTrades}
            onBack={() => setCurrentScreen('dashboard')}
          />
        );
      case 'status':
        return (
          <SystemStatusScreen
            services={mockServices}
            circuitBreakers={mockCircuitBreakers}
            onBack={() => setCurrentScreen('dashboard')}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="relative">
      {renderScreen()}

      {/* Navigation Helper (Dev Only) */}
      <div className="fixed bottom-4 right-4 bg-black text-white rounded-xl shadow-lg p-3 space-y-2">
        <div className="text-xs font-medium mb-2 text-gray-400 uppercase">
          Dev Nav
        </div>
        <button
          onClick={() => setCurrentScreen('dashboard')}
          className={`block w-full text-left px-3 py-1 rounded text-sm ${
            currentScreen === 'dashboard' ? 'bg-teal' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={() => setCurrentScreen('trades')}
          className={`block w-full text-left px-3 py-1 rounded text-sm ${
            currentScreen === 'trades' ? 'bg-teal' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Trades
        </button>
        <button
          onClick={() => setCurrentScreen('status')}
          className={`block w-full text-left px-3 py-1 rounded text-sm ${
            currentScreen === 'status' ? 'bg-teal' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Status
        </button>
      </div>
    </div>
  );
};
