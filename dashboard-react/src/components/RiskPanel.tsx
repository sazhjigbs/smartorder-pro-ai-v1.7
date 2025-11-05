import { Card, CardContent, Typography, Box, LinearProgress, Chip, Grid } from '@mui/material';
import { Security, TrendingUp, TrendingDown } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getRiskStatus, getPnL } from '../services/api';
import type { RiskData, PnLData } from '../types';

export const RiskPanel = () => {
  const [riskData, setRiskData] = useState<RiskData | null>(null);
  const [pnl, setPnl] = useState<PnLData | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [riskRes, pnlRes] = await Promise.all([getRiskStatus(), getPnL()]);
      setRiskData(riskRes.data);
      setPnl(pnlRes.data);
    } catch (error) {
      console.error('Erreur chargement risk/pnl:', error);
    }
  };

  if (!riskData || !pnl) return null;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Security color="warning" />
          <Typography variant="h6">Risk Management</Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Market Reliability
            </Typography>
            <Typography variant="h5" fontWeight={700} color="success.main">
              {riskData.reliability_score}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={riskData.reliability_score}
              color="success"
              sx={{ mt: 1, height: 6, borderRadius: 3 }}
            />
          </Grid>

          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Mode
            </Typography>
            <Chip label={riskData.current_mode} color="warning" sx={{ mt: 0.5 }} />
          </Grid>

          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Drawdown Day
            </Typography>
            <Typography variant="h5" fontWeight={700} color={riskData.drawdown_day_pct > 5 ? 'error.main' : 'text.primary'}>
              {(riskData.drawdown_day_pct || 0).toFixed(2)}%
            </Typography>
          </Grid>

          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Win Rate
            </Typography>
            <Typography variant="h5" fontWeight={700} color="info.main">
              {(riskData.win_rate || 0).toFixed(1)}%
            </Typography>
          </Grid>

          <Grid item xs={6} md={3}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                PnL Daily
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {pnl.daily >= 0 ? <TrendingUp color="success" fontSize="small" /> : <TrendingDown color="error" fontSize="small" />}
                <Typography variant="h6" fontWeight={700} color={(pnl.daily || 0) >= 0 ? 'success.main' : 'error.main'}>
                  ${(pnl.daily || 0).toFixed(2)}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={6} md={3}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                PnL Weekly
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {pnl.weekly >= 0 ? <TrendingUp color="success" fontSize="small" /> : <TrendingDown color="error" fontSize="small" />}
                <Typography variant="h6" fontWeight={700} color={(pnl.weekly || 0) >= 0 ? 'success.main' : 'error.main'}>
                  ${(pnl.weekly || 0).toFixed(2)}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={6} md={3}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                PnL Total
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {pnl.total >= 0 ? <TrendingUp color="success" fontSize="small" /> : <TrendingDown color="error" fontSize="small" />}
                <Typography variant="h6" fontWeight={700} color={(pnl.total || 0) >= 0 ? 'success.main' : 'error.main'}>
                  ${(pnl.total || 0).toFixed(2)}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Trades Today
            </Typography>
            <Typography variant="h6" fontWeight={700}>
              {riskData.trades_today}
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
