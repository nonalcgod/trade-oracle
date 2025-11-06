/**
 * Real-Time Trades Hook
 *
 * Subscribes to Supabase Real-Time channel for instant trade execution notifications.
 */

import { useEffect, useState } from 'react';
import { createClient, RealtimeChannel, RealtimePostgresChangesPayload } from '@supabase/supabase-js';
import { Trade } from '../api';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

let supabase: ReturnType<typeof createClient> | null = null;

if (SUPABASE_URL && SUPABASE_ANON_KEY) {
  supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

export function useRealtimeTrades(initialTrades: Trade[] = []) {
  const [trades, setTrades] = useState<Trade[]>(initialTrades);
  const [latestTrade, setLatestTrade] = useState<Trade | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    let channel: RealtimeChannel;

    const setupRealtimeSubscription = async () => {
      channel = supabase!.channel('trade-updates')
        .on(
          'postgres_changes',
          {
            event: 'INSERT', // Only new trades
            schema: 'public',
            table: 'trades'
          },
          (payload: RealtimePostgresChangesPayload<Trade>) => {
            console.log('New trade received:', payload);

            const newTrade = payload.new as Trade;

            // Add new trade to beginning of list
            setTrades((current) => [newTrade, ...current].slice(0, 50)); // Keep last 50

            // Set as latest for notification display
            setLatestTrade(newTrade);

            // Clear latest after 5 seconds
            setTimeout(() => {
              setLatestTrade(null);
            }, 5000);
          }
        )
        .subscribe((status: string) => {
          console.log('Trade subscription status:', status);
          setIsConnected(status === 'SUBSCRIBED');
        });
    };

    setupRealtimeSubscription();

    return () => {
      if (channel) {
        supabase!.removeChannel(channel);
        setIsConnected(false);
      }
    };
  }, []);

  useEffect(() => {
    setTrades(initialTrades);
  }, [initialTrades]);

  return {
    trades,
    latestTrade,
    isConnected,
    isRealtimeEnabled: !!supabase
  };
}
