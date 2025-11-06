import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import { apiService, EntryWindow } from '../api';

interface IronCondorEntryWindowProps {
  onScoutSetups?: () => void;
}

export const IronCondorEntryWindow: React.FC<IronCondorEntryWindowProps> = ({ onScoutSetups }) => {
  const [entryWindow, setEntryWindow] = useState<EntryWindow | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkEntryWindow = async () => {
      try {
        const data = await apiService.checkEntryWindow();
        setEntryWindow(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to check entry window:', error);
        setLoading(false);
      }
    };

    // Check immediately
    checkEntryWindow();

    // Poll every 60 seconds
    const interval = setInterval(checkEntryWindow, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border-2 border-black p-6 mb-6 shadow-md">
        <p className="text-sm text-gray-600">Checking entry window...</p>
      </div>
    );
  }

  if (!entryWindow) {
    return null;
  }

  // Calculate remaining time if in window
  const calculateRemainingTime = () => {
    if (!entryWindow.should_enter || !entryWindow.current_time) return null;

    try {
      const currentTime = new Date(entryWindow.current_time);
      const closeTime = new Date(currentTime);
      closeTime.setHours(9, 45, 0, 0); // 9:45am ET

      const diffMinutes = Math.max(0, Math.floor((closeTime.getTime() - currentTime.getTime()) / 60000));
      return diffMinutes;
    } catch {
      return null;
    }
  };

  const remainingMinutes = calculateRemainingTime();

  if (entryWindow.should_enter) {
    return (
      <div className="bg-[#E8F5E9] rounded-2xl border-2 border-black p-6 mb-6 shadow-md">
        <div className="flex items-center gap-3 mb-2">
          <Clock size={24} className="text-emerald" />
          <h3 className="text-lg font-semibold text-black">Entry Window Open</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          9:31-9:45am ET {remainingMinutes !== null && `• ${remainingMinutes} minutes remaining`}
        </p>
        {onScoutSetups && (
          <button
            onClick={onScoutSetups}
            className="bg-black text-white px-6 py-2 rounded-xl font-medium hover:scale-105 transition-transform"
          >
            Scout Iron Condor Setups →
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border-2 border-black p-6 mb-6 shadow-md">
      <div className="flex items-center gap-3 mb-2">
        <Clock size={24} className="text-gray-600" />
        <h3 className="text-lg font-semibold text-black">Entry Window Closed</h3>
      </div>
      <p className="text-sm text-gray-600">{entryWindow.reason}</p>
    </div>
  );
};

export default IronCondorEntryWindow;
