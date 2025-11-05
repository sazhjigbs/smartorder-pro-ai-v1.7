import { Card, CardContent, Typography, Box, Switch, Chip, Grid } from '@mui/material';
import { Psychology } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getStrategies, bulkToggleStrategies } from '../services/api';
import type { Strategy } from '../types';

export const StrategiesPanel = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStrategies();
    const interval = setInterval(loadStrategies, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadStrategies = async () => {
    try {
      const { data } = await getStrategies();
      setStrategies(data.strategies);
    } catch (error) {
      console.error('Erreur chargement stratégies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (strategyId: string, enabled: boolean) => {
    try {
      await bulkToggleStrategies([strategyId], enabled);
      await loadStrategies();
    } catch (error) {
      console.error('Erreur toggle stratégie:', error);
    }
  };

  if (loading) return null;

  const spotStrats = strategies.filter((s) => s.type === 'SPOT');
  const futuresStrats = strategies.filter((s) => s.type === 'FUTURES');
  const hybridStrats = strategies.filter((s) => s.type === 'HYBRID');

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Psychology color="secondary" />
          <Typography variant="h6">AI Strategies ({strategies.length})</Typography>
        </Box>

        <Grid container spacing={2}>
          {/* SPOT */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              SPOT ({spotStrats.length})
            </Typography>
            <Grid container spacing={1}>
              {spotStrats.map((strategy) => (
                <Grid item xs={12} sm={6} md={4} key={strategy.id}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      backgroundColor: 'rgba(56, 97, 251, 0.05)',
                      border: '1px solid rgba(56, 97, 251, 0.2)',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {strategy.name}
                      </Typography>
                      <Switch
                        size="small"
                        checked={strategy.enabled}
                        onChange={(e) => handleToggle(strategy.id, e.target.checked)}
                      />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {strategy.score !== undefined && (
                        <Chip label={`Score: ${strategy.score}`} size="small" color="info" />
                      )}
                      {strategy.win_rate !== undefined && (
                        <Chip label={`WR: ${strategy.win_rate}%`} size="small" color="success" />
                      )}
                    </Box>
                    {strategy.last_signal && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        Last: {strategy.last_signal}
                      </Typography>
                    )}
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* FUTURES */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="warning.main" gutterBottom>
              FUTURES ({futuresStrats.length})
            </Typography>
            <Grid container spacing={1}>
              {futuresStrats.map((strategy) => (
                <Grid item xs={12} sm={6} md={4} key={strategy.id}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      backgroundColor: 'rgba(240, 185, 11, 0.05)',
                      border: '1px solid rgba(240, 185, 11, 0.2)',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {strategy.name}
                      </Typography>
                      <Switch
                        size="small"
                        checked={strategy.enabled}
                        onChange={(e) => handleToggle(strategy.id, e.target.checked)}
                        color="warning"
                      />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {strategy.score !== undefined && (
                        <Chip label={`Score: ${strategy.score}`} size="small" color="info" />
                      )}
                      {strategy.win_rate !== undefined && (
                        <Chip label={`WR: ${strategy.win_rate}%`} size="small" color="success" />
                      )}
                    </Box>
                    {strategy.last_signal && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        Last: {strategy.last_signal}
                      </Typography>
                    )}
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* HYBRID */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="secondary.main" gutterBottom>
              HYBRID ({hybridStrats.length})
            </Typography>
            <Grid container spacing={1}>
              {hybridStrats.map((strategy) => (
                <Grid item xs={12} sm={6} key={strategy.id}>
                  <Box
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      backgroundColor: 'rgba(156, 75, 255, 0.05)',
                      border: '1px solid rgba(156, 75, 255, 0.2)',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" fontWeight={600}>
                        {strategy.name}
                      </Typography>
                      <Switch
                        size="small"
                        checked={strategy.enabled}
                        onChange={(e) => handleToggle(strategy.id, e.target.checked)}
                        color="secondary"
                      />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {strategy.score !== undefined && (
                        <Chip label={`Score: ${strategy.score}`} size="small" color="info" />
                      )}
                      {strategy.win_rate !== undefined && (
                        <Chip label={`WR: ${strategy.win_rate}%`} size="small" color="success" />
                      )}
                    </Box>
                    {strategy.last_signal && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        Last: {strategy.last_signal}
                      </Typography>
                    )}
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
