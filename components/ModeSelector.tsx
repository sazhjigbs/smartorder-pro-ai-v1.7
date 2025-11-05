'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { API_CONFIG } from '@/lib/smartorder-api';
import axios from 'axios';

type TradingMode = 'spot' | 'futures' | 'hybrid';

export function ModeSelector() {
  const [currentMode, setCurrentMode] = useState<TradingMode>('spot');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCurrentMode();
  }, []);

  const fetchCurrentMode = async () => {
    try {
      const { data } = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.MODE_CURRENT}`);
      if (data.mode) setCurrentMode(data.mode);
    } catch (error) {
      console.error('Error fetching mode:', error);
    }
  };

  const handleModeChange = async (mode: TradingMode) => {
    setLoading(true);
    try {
      await axios.post(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.MODE_CURRENT}`, { mode });
      setCurrentMode(mode);
    } catch (error) {
      console.error('Error changing mode:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        variant={currentMode === 'spot' ? 'default' : 'outline'}
        onClick={() => handleModeChange('spot')}
        disabled={loading}
        className="glassmorphism"
      >
        SPOT
      </Button>
      <Button
        variant={currentMode === 'futures' ? 'default' : 'outline'}
        onClick={() => handleModeChange('futures')}
        disabled={loading}
        className="glassmorphism"
      >
        FUTURES
      </Button>
      <Button
        variant={currentMode === 'hybrid' ? 'default' : 'outline'}
        onClick={() => handleModeChange('hybrid')}
        disabled={loading}
        className="glassmorphism"
      >
        HYBRID
      </Button>
    </div>
  );
}
