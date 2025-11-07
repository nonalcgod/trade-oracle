/**
 * useEntryWindow Hook
 *
 * Tracks momentum scalping entry window (9:31am - 11:30am ET)
 * Provides real-time countdown and active status
 *
 * @returns {Object} Entry window state
 * - isActive: boolean - Whether entry window is currently active
 * - timeRemaining: string - Formatted time remaining (e.g., "47 min 23 sec")
 * - currentTimeET: string - Current time in ET timezone (e.g., "9:43:37am")
 * - minutesRemaining: number - Minutes until window closes
 * - secondsRemaining: number - Seconds until window closes
 */

import { useState, useEffect } from 'react';
import { utcToZonedTime, format } from 'date-fns-tz';

interface EntryWindowState {
  isActive: boolean;
  timeRemaining: string;
  currentTimeET: string;
  minutesRemaining: number;
  secondsRemaining: number;
}

const ET_TIMEZONE = 'America/New_York';
const ENTRY_START_HOUR = 9;
const ENTRY_START_MINUTE = 31;
const ENTRY_END_HOUR = 11;
const ENTRY_END_MINUTE = 30;

export const useEntryWindow = (): EntryWindowState => {
  const [state, setState] = useState<EntryWindowState>({
    isActive: false,
    timeRemaining: 'Calculating...',
    currentTimeET: '',
    minutesRemaining: 0,
    secondsRemaining: 0,
  });

  useEffect(() => {
    const calculateEntryWindow = () => {
      // Get current time in ET timezone
      const now = new Date();
      const nowET = utcToZonedTime(now, ET_TIMEZONE);

      // Format current time as "9:43:37am ET"
      const currentTimeET = format(nowET, 'h:mm:ssaaa', { timeZone: ET_TIMEZONE });

      // Get current hour and minute in ET
      const currentHour = nowET.getHours();
      const currentMinute = nowET.getMinutes();
      const currentSecond = nowET.getSeconds();

      // Calculate if we're in the entry window (9:31am - 11:30am)
      const startMinutesFromMidnight = ENTRY_START_HOUR * 60 + ENTRY_START_MINUTE;
      const endMinutesFromMidnight = ENTRY_END_HOUR * 60 + ENTRY_END_MINUTE;
      const currentMinutesFromMidnight = currentHour * 60 + currentMinute;

      const isActive =
        currentMinutesFromMidnight >= startMinutesFromMidnight &&
        currentMinutesFromMidnight < endMinutesFromMidnight;

      // Calculate time remaining until window closes
      let minutesRemaining = 0;
      let secondsRemaining = 0;
      let timeRemaining = 'Window closed';

      if (isActive) {
        // Calculate total seconds until 11:30am
        const endTimeInSeconds = (ENTRY_END_HOUR * 3600) + (ENTRY_END_MINUTE * 60);
        const currentTimeInSeconds = (currentHour * 3600) + (currentMinute * 60) + currentSecond;
        const totalSecondsRemaining = endTimeInSeconds - currentTimeInSeconds;

        minutesRemaining = Math.floor(totalSecondsRemaining / 60);
        secondsRemaining = totalSecondsRemaining % 60;

        // Format as "47 min 23 sec"
        timeRemaining = `${minutesRemaining} min ${secondsRemaining} sec`;
      } else if (currentMinutesFromMidnight < startMinutesFromMidnight) {
        // Before window opens
        const secondsUntilOpen = ((startMinutesFromMidnight - currentMinutesFromMidnight) * 60) - currentSecond;
        const minsUntilOpen = Math.floor(secondsUntilOpen / 60);
        const secsUntilOpen = secondsUntilOpen % 60;
        timeRemaining = `Opens in ${minsUntilOpen} min ${secsUntilOpen} sec`;
      }

      setState({
        isActive,
        timeRemaining,
        currentTimeET,
        minutesRemaining,
        secondsRemaining,
      });
    };

    // Calculate immediately
    calculateEntryWindow();

    // Update every second for countdown accuracy
    const interval = setInterval(calculateEntryWindow, 1000);

    return () => clearInterval(interval);
  }, []);

  return state;
};
