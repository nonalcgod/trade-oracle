/**
 * Real-Time Positions Hook
 *
 * Subscribes to Supabase Real-Time channel for instant position updates.
 * Replaces 5-second polling with push-based updates (sub-second latency).
 */

import { useEffect, useState } from 'react';
import { createClient, RealtimeChannel } from '@supabase/supabase-js';
import { Position } from '../api';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Initialize Supabase client (only if credentials provided)
let supabase: ReturnType<typeof createClient> | null = null;

if (SUPABASE_URL && SUPABASE_ANON_KEY) {
  supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
}

interface PositionUpdate {
  position_id: number;
  symbol: string;
  status: string;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  pnl_percent: number;
  opened_at: string;
  closed_at?: string;
  exit_reason?: string;
}

export function useRealtimePositions(initialPositions: Position[] = []) {
  const [positions, setPositions] = useState<Position[]>(initialPositions);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!supabase) {
      console.warn('Supabase not configured - falling back to polling');
      return;
    }

    let channel: RealtimeChannel;

    const setupRealtimeSubscription = async () => {
      // Subscribe to position updates channel
      channel = supabase!.channel('position-updates')
        .on(
          'postgres_changes',
          {
            event: '*', // All events (INSERT, UPDATE, DELETE)
            schema: 'public',
            table: 'positions'
          },
          (payload) => {
            console.log('Position update received:', payload);

            const { eventType, new: newPosition, old: oldPosition } = payload;

            setPositions((current) => {
              switch (eventType) {
                case 'INSERT':
                  // New position opened
                  return [...current, newPosition as Position];

                case 'UPDATE':
                  // Position updated (price change, status change, etc.)
                  return current.map((pos) =>
                    pos.id === newPosition.id ? (newPosition as Position) : pos
                  );

                case 'DELETE':
                  // Position removed (shouldn't happen, but handle it)
                  return current.filter((pos) => pos.id !== oldPosition.id);

                default:
                  return current;
              }
            });

            setLastUpdate(new Date());
          }
        )
        .subscribe((status) => {
          console.log('Realtime subscription status:', status);
          setIsConnected(status === 'SUBSCRIBED');
        });
    };

    setupRealtimeSubscription();

    // Cleanup subscription on unmount
    return () => {
      if (channel) {
        supabase!.removeChannel(channel);
        setIsConnected(false);
      }
    };
  }, []);

  // Update positions when initialPositions change (from initial API fetch)
  useEffect(() => {
    setPositions(initialPositions);
  }, [initialPositions]);

  return {
    positions,
    lastUpdate,
    isConnected,
    isRealtimeEnabled: !!supabase
  };
}
