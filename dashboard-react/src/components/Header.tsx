import { AppBar, Toolbar, Typography, Box, Button, ButtonGroup, Chip } from '@mui/material';
import { TrendingUp } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getCurrentMode, setMode } from '../services/api';
import type { TradingMode } from '../types';

export const Header = () => {
  const [currentMode, setCurrentMode] = useState<TradingMode>('spot');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCurrentMode();
  }, []);

  const loadCurrentMode = async () => {
    try {
      const { data } = await getCurrentMode();
      setCurrentMode(data.mode);
    } catch (error) {
      console.error('Erreur chargement mode:', error);
    }
  };

  const handleModeChange = async (mode: TradingMode) => {
    setLoading(true);
    try {
      await setMode(mode);
      setCurrentMode(mode);
    } catch (error) {
      console.error('Erreur changement mode:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppBar position="sticky" sx={{ backdropFilter: 'blur(20px)', backgroundColor: 'rgba(30, 35, 41, 0.8)' }}>
      <Toolbar>
        <TrendingUp sx={{ mr: 2, fontSize: 32, color: 'success.main' }} />
        <Typography variant="h5" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
          SmartOrder PRO AI v3.0
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Mode de trading:
          </Typography>
          <ButtonGroup disabled={loading}>
            <Button
              variant={currentMode === 'spot' ? 'contained' : 'outlined'}
              color="primary"
              onClick={() => handleModeChange('spot')}
            >
              Spot
            </Button>
            <Button
              variant={currentMode === 'futures' ? 'contained' : 'outlined'}
              color="warning"
              onClick={() => handleModeChange('futures')}
            >
              Futures
            </Button>
            <Button
              variant={currentMode === 'hybrid' ? 'contained' : 'outlined'}
              color="secondary"
              onClick={() => handleModeChange('hybrid')}
            >
              Hybrid
            </Button>
          </ButtonGroup>
          <Chip
            label={currentMode.toUpperCase()}
            color={currentMode === 'spot' ? 'primary' : currentMode === 'futures' ? 'warning' : 'secondary'}
            size="small"
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
};
