import { Card, CardContent, Typography, Box, Chip, Switch, Stack } from '@mui/material';
import { CheckCircle, Cancel } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getExchangesStatus, toggleExchange } from '../services/api';
import type { Exchange } from '../types';

export const ExchangeSelector = () => {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExchanges();
    const interval = setInterval(loadExchanges, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadExchanges = async () => {
    try {
      const { data } = await getExchangesStatus();
      setExchanges(data.exchanges);
    } catch (error) {
      console.error('Erreur chargement exchanges:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (exchangeId: string, enabled: boolean) => {
    try {
      await toggleExchange(exchangeId, enabled);
      await loadExchanges();
    } catch (error) {
      console.error('Erreur toggle exchange:', error);
    }
  };

  if (loading) return null;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Exchanges
        </Typography>
        <Stack spacing={1.5}>
          {exchanges.map((exchange) => (
            <Box
              key={exchange.id}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                p: 1.5,
                borderRadius: 2,
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                {exchange.status === 'CONNECTED' ? (
                  <CheckCircle color="success" />
                ) : (
                  <Cancel color="error" />
                )}
                <Box>
                  <Typography variant="body1" fontWeight={600}>
                    {exchange.name}
                  </Typography>
                  {exchange.latency_ms && (
                    <Typography variant="caption" color="text.secondary">
                      Latency: {exchange.latency_ms}ms
                    </Typography>
                  )}
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={exchange.status}
                  size="small"
                  color={exchange.status === 'CONNECTED' ? 'success' : 'default'}
                />
                <Switch
                  checked={exchange.enabled}
                  onChange={(e) => handleToggle(exchange.id, e.target.checked)}
                  color="primary"
                  size="small"
                />
              </Box>
            </Box>
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};
