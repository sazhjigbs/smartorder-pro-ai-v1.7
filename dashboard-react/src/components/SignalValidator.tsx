import { Card, CardContent, Typography, Box, Chip, Grid, LinearProgress, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getRealtimeSignal } from '../services/api';
import type { Signal } from '../types';

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d'];

export const SignalValidator = () => {
  const [signal, setSignal] = useState<Signal | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('15m');

  useEffect(() => {
    loadSignal();
    const interval = setInterval(loadSignal, 3000);
    return () => clearInterval(interval);
  }, [selectedSymbol, selectedTimeframe]);

  const loadSignal = async () => {
    try {
      const { data } = await getRealtimeSignal(selectedSymbol, selectedTimeframe);
      setSignal(data);
    } catch (error) {
      console.error('Erreur signal validator:', error);
    }
  };

  if (!signal) return null;

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A':
        return 'success';
      case 'B':
        return 'info';
      case 'C':
        return 'warning';
      case 'D':
      case 'F':
        return 'error';
      default:
        return 'default';
    }
  };

  const getRegimeIcon = (regime: string) => {
    switch (regime) {
      case 'BULLISH':
        return <TrendingUp color="success" />;
      case 'BEARISH':
        return <TrendingDown color="error" />;
      default:
        return <TrendingFlat color="action" />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Signal Validator</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Symbol</InputLabel>
              <Select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)} label="Symbol">
                <MenuItem value="BTCUSDT">BTC/USDT</MenuItem>
                <MenuItem value="ETHUSDT">ETH/USDT</MenuItem>
                <MenuItem value="SOLUSDT">SOL/USDT</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>TF</InputLabel>
              <Select value={selectedTimeframe} onChange={(e) => setSelectedTimeframe(e.target.value)} label="TF">
                {TIMEFRAMES.map((tf) => (
                  <MenuItem key={tf} value={tf}>
                    {tf}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        <Grid container spacing={2}>
          {/* Score Global */}
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, backgroundColor: 'rgba(56, 97, 251, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="text.secondary">
                GLOBAL SCORE
              </Typography>
              <Typography variant="h2" fontWeight={700} color={`${getGradeColor(signal.grade)}.main`}>
                {signal.score}
              </Typography>
              <Chip label={`Grade ${signal.grade}`} color={getGradeColor(signal.grade)} sx={{ mt: 1 }} />
              <LinearProgress variant="determinate" value={signal.score} color={getGradeColor(signal.grade) as any} sx={{ mt: 2, height: 8, borderRadius: 4 }} />
            </Box>
          </Grid>

          {/* Indicators */}
          <Grid item xs={12} md={8}>
            <Grid container spacing={1.5}>
              <Grid item xs={6} sm={4}>
                <Box sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    RSI
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {signal.indicators.rsi.toFixed(2)}
                  </Typography>
                  <Chip label={signal.indicators.rsi_signal} size="small" color={signal.indicators.rsi_signal === 'BULLISH' ? 'success' : signal.indicators.rsi_signal === 'BEARISH' ? 'error' : 'default'} />
                </Box>
              </Grid>

              <Grid item xs={6} sm={4}>
                <Box sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    MACD
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {signal.indicators.macd.toFixed(2)}
                  </Typography>
                  <Chip label={signal.indicators.macd_signal} size="small" color={signal.indicators.macd_signal === 'BULLISH' ? 'success' : signal.indicators.macd_signal === 'BEARISH' ? 'error' : 'default'} />
                </Box>
              </Grid>

              <Grid item xs={6} sm={4}>
                <Box sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Volume Ratio
                  </Typography>
                  <Typography variant="h6" fontWeight={600}>
                    {signal.indicators.volume_ratio.toFixed(2)}x
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ${(signal.indicators.volume / 1000).toFixed(0)}K
                  </Typography>
                </Box>
              </Grid>

              <Grid item xs={6} sm={4}>
                <Box sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Market Regime
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                    {getRegimeIcon(signal.regime)}
                    <Typography variant="body2" fontWeight={600}>
                      {signal.regime}
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={6} sm={4}>
                <Box sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Volatility
                  </Typography>
                  <Chip label={signal.volatility} size="small" color={signal.volatility === 'HIGH' ? 'error' : signal.volatility === 'MEDIUM' ? 'warning' : 'success'} sx={{ mt: 0.5 }} />
                </Box>
              </Grid>

              <Grid item xs={6} sm={4}>
                <Box sx={{ p: 1.5, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    AI Confidence
                  </Typography>
                  <Typography variant="h6" fontWeight={600} color="secondary.main">
                    {(signal.ai_confidence * 100).toFixed(0)}%
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
